from __future__ import annotations

import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator

from solution_ai_dc.cabling import build_server_cabling_plan, connect_interface_maps
from solution_ai_dc.generator import set_fabric_avd_hostvars_ready, trigger_hostvar_generation
from solution_ai_dc.protocols import DcimDevice, DcimInterface, InterfacePhysical, LocationRack, NetworkPod
from solution_ai_dc.sorting import create_sorted_device_interface_map


class ServerCablingGenerator(InfrahubGenerator):
    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        servers = data.get("ComputePhysicalServer", {}).get("edges", [])
        if not servers:
            self.logger.warning("No server found in query response")
            return

        server_node = servers[0]["node"]
        server_hostname: str = server_node["name"]["value"]

        # Get rack info
        rack_rel = server_node.get("rack")
        if not rack_rel or not rack_rel.get("node"):
            self.logger.warning("Server %s has no rack assigned", server_hostname)
            return

        rack_id: str = rack_rel["node"]["id"]
        rack_name: str = rack_rel["node"]["name"]["value"]

        # Get all server interfaces
        server_interfaces = self._get_server_interfaces(server_node)
        if not server_interfaces:
            self.logger.warning("Server %s has no interfaces", server_hostname)
            return

        # Skip if server is already fully cabled
        if await self._is_server_cabled(server_interfaces):
            self.logger.info("Server %s is already cabled, skipping", server_hostname)
            return

        # Find leaf switches in the same rack
        leaf_switches = await self.client.filters(kind=DcimDevice, rack__ids=[rack_id], role__value="leaf")
        if not leaf_switches:
            self.logger.warning("No leaf switches found in rack %s for server %s", rack_name, server_hostname)
            return

        # Build sorted interface maps (same pattern as pod/rack generators)
        server_iface_objects = await self.client.filters(
            kind=DcimInterface, device__name__value=server_hostname
        )
        server_interface_map = create_sorted_device_interface_map(server_iface_objects)

        leaf_interfaces = await self.client.filters(
            kind=InterfacePhysical,
            device__ids=[leaf.id for leaf in leaf_switches],
            role__values=["server", "storage"],
        )
        leaf_interface_map = create_sorted_device_interface_map(leaf_interfaces)

        if not leaf_interface_map:
            self.logger.warning(
                "No server-role interfaces on leaf switches in rack %s for server %s",
                rack_name,
                server_hostname,
            )
            return

        # Find the next available index (first unused slot across all leaves)
        server_index = self._find_next_available_index(leaf_interface_map)

        # Build cabling plan and connect (same pattern as connect_leafs_to_spine)
        cabling_plan = build_server_cabling_plan(
            server_index=server_index,
            src_interface_map=server_interface_map,
            dst_interface_map=leaf_interface_map,
        )

        await connect_interface_maps(client=self.client, logger=self.logger, cabling_plan=cabling_plan)

        # Assign VLANs from server interfaces to their paired leaf interfaces
        await self._assign_vlans(cabling_plan, server_interfaces)

        # Trigger AVD hostvar regeneration cascade
        await self._trigger_avd_cascade(rack_id, server_hostname)

    async def _trigger_avd_cascade(self, rack_id: str, server_hostname: str) -> None:
        """Navigate from rack to fabric and trigger AVD hostvar regeneration."""
        rack = await self.client.get(LocationRack, id=rack_id)
        await rack.pod.fetch()  # type: ignore[union-attr]
        pod = await self.client.get(NetworkPod, id=rack.pod.peer.id)  # type: ignore[union-attr]
        await pod.parent.fetch()  # type: ignore[union-attr]
        fabric = pod.parent.peer  # type: ignore[union-attr]

        self.logger.info(
            "Server %s cabled — triggering AVD cascade for fabric %s",
            server_hostname,
            fabric.name.value,
        )
        await set_fabric_avd_hostvars_ready(self.client, fabric.id, False)
        await trigger_hostvar_generation(self.client)

    def _get_server_interfaces(self, server_node: dict) -> list[dict[str, Any]]:
        """Extract server interfaces with their VLANs from the GQL response."""
        interfaces = []
        for edge in server_node.get("interfaces", {}).get("edges", []):
            node = edge["node"]
            vlans = self._extract_vlans(node)
            interfaces.append(
                {
                    "id": node["id"],
                    "name": node["name"]["value"],
                    "tagged_vlan_ids": vlans["tagged"],
                    "untagged_vlan_id": vlans["untagged"],
                }
            )
        return interfaces

    async def _is_server_cabled(self, server_interfaces: list[dict[str, Any]]) -> bool:
        """Check if all server interfaces already have connectors."""
        for iface_data in server_interfaces:
            iface = await self.client.get(InterfacePhysical, id=iface_data["id"])
            if not iface.connector.id:
                return False
        return True

    def _extract_vlans(self, interface_node: dict) -> dict[str, Any]:
        """Extract VLAN IDs from interface and its profiles."""
        tagged: list[str] = []
        untagged: str | None = None

        self._collect_vlans(interface_node, tagged)
        untagged_rel = interface_node.get("untagged_vlan")
        if untagged_rel and untagged_rel.get("node"):
            untagged = untagged_rel["node"]["id"]

        for profile_edge in interface_node.get("profiles", {}).get("edges", []):
            profile = profile_edge["node"]
            self._collect_vlans(profile, tagged)
            if not untagged:
                profile_untagged = profile.get("untagged_vlan")
                if profile_untagged and profile_untagged.get("node"):
                    untagged = profile_untagged["node"]["id"]

        return {"tagged": tagged, "untagged": untagged}

    @staticmethod
    def _collect_vlans(node: dict, tagged: list[str]) -> None:
        """Append tagged VLAN IDs from a node's tagged_vlan edges."""
        for vlan_edge in node.get("tagged_vlan", {}).get("edges", []):
            vlan_id = vlan_edge["node"]["id"]
            if vlan_id not in tagged:
                tagged.append(vlan_id)

    @staticmethod
    def _find_next_available_index(
        leaf_interface_map: dict[DcimDevice, list[DcimInterface]],
    ) -> int:
        """Find the first index where all leaves have an uncabled interface."""
        max_len = max(len(ifaces) for ifaces in leaf_interface_map.values())
        for idx in range(max_len):
            all_available = all(
                idx < len(ifaces) and not ifaces[idx].connector.id
                for ifaces in leaf_interface_map.values()
            )
            if all_available:
                return idx
        return max_len

    async def _assign_vlans(
        self,
        cabling_plan: list[tuple[DcimInterface, DcimInterface]],
        server_interfaces: list[dict[str, Any]],
    ) -> None:
        """Assign VLANs from server interfaces to their paired leaf interfaces."""
        for (_, leaf_iface), server_iface in zip(cabling_plan, server_interfaces, strict=False):
            if not server_iface["tagged_vlan_ids"] and not server_iface["untagged_vlan_id"]:
                continue

            leaf_interface = await self.client.get(
                InterfacePhysical,
                id=leaf_iface.id,
                include=["tagged_vlan", "untagged_vlan"],
            )

            if server_iface["tagged_vlan_ids"]:
                await leaf_interface.tagged_vlan.fetch()  # type: ignore[union-attr]
                leaf_interface.tagged_vlan.extend(server_iface["tagged_vlan_ids"])  # type: ignore[union-attr]
            if server_iface["untagged_vlan_id"]:
                await leaf_interface.untagged_vlan.fetch()  # type: ignore[union-attr]
                leaf_interface.untagged_vlan.add(server_iface["untagged_vlan_id"])  # type: ignore[union-attr]

            await leaf_interface.save(allow_upsert=True)
