from __future__ import annotations

import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator

from solution_ai_dc.generator import set_fabric_avd_hostvars_ready, trigger_hostvar_generation
from solution_ai_dc.protocols import DcimConnector, DcimDevice, DcimInterface, LocationRack, NetworkPod


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

        # Find leaf switches in the same rack
        leaf_switches = await self._get_rack_leaf_switches(rack_id)
        if not leaf_switches:
            self.logger.warning("No leaf switches found in rack %s for server %s", rack_name, server_hostname)
            return

        # Get all server/storage-role interfaces on leaf switches
        leaf_interfaces = await self._get_leaf_interfaces(leaf_switches)
        if not leaf_interfaces:
            self.logger.warning(
                "No server-role interfaces on leaf switches in rack %s for server %s",
                rack_name,
                server_hostname,
            )
            return

        # Warn if insufficient but proceed with what we have
        if len(leaf_interfaces) < len(server_interfaces):
            self.logger.warning(
                "Insufficient leaf interfaces in rack %s: need %d, have %d for server %s",
                rack_name,
                len(server_interfaces),
                len(leaf_interfaces),
                server_hostname,
            )

        # Distribute server interfaces across leaves (round-robin, deterministic by index)
        pairings = self._distribute_interfaces(server_interfaces, leaf_interfaces, leaf_switches)

        if len(leaf_switches) == 1 and len(server_interfaces) > 1:
            self.logger.info(
                "Only one leaf switch in rack %s; connecting all %d server interfaces to %s",
                rack_name,
                len(server_interfaces),
                leaf_switches[0].name.value,
            )

        # Upsert links and assign VLANs
        for server_iface, leaf_iface_id in pairings:
            await self._cable_interface(server_hostname, server_iface, leaf_iface_id)

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
        """Extract server interfaces with their VLANs."""
        interfaces = []
        for edge in server_node.get("interfaces", {}).get("edges", []):
            node = edge["node"]
            vlans = self._extract_vlans(node)
            interfaces.append({
                "id": node["id"],
                "name": node["name"]["value"],
                "tagged_vlan_ids": vlans["tagged"],
                "untagged_vlan_id": vlans["untagged"],
            })
        return interfaces

    def _extract_vlans(self, interface_node: dict) -> dict[str, Any]:
        """Extract VLAN IDs from interface and its profiles."""
        tagged: list[str] = []
        untagged: str | None = None

        # Collect from interface directly
        self._collect_vlans(interface_node, tagged)
        untagged_rel = interface_node.get("untagged_vlan")
        if untagged_rel and untagged_rel.get("node"):
            untagged = untagged_rel["node"]["id"]

        # Collect from profiles
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

    async def _get_rack_leaf_switches(self, rack_id: str) -> list[DcimDevice]:
        """Find all leaf switches in the given rack."""
        return await self.client.filters(kind=DcimDevice, rack__ids=[rack_id], role__value="leaf")

    async def _get_leaf_interfaces(self, leaf_switches: list[DcimDevice]) -> list[dict[str, Any]]:
        """Get all server/storage-role interfaces from leaf switches."""
        result: list[dict[str, Any]] = []
        for leaf in leaf_switches:
            interfaces = await self.client.filters(
                kind=DcimInterface,
                device__ids=[leaf.id],
                role__values=["server", "storage"],
            )
            for iface in interfaces:
                result.append({
                    "id": iface.id,
                    "leaf_id": leaf.id,
                    "leaf_hostname": leaf.name.value,
                    "name": iface.name.value,
                })
        return result

    def _distribute_interfaces(
        self,
        server_interfaces: list[dict[str, Any]],
        available_leaf_interfaces: list[dict[str, Any]],
        leaf_switches: list[DcimDevice],
    ) -> list[tuple[dict[str, Any], str]]:
        """Pair server interfaces with leaf interfaces using round-robin across leaves."""
        if len(leaf_switches) <= 1:
            # Single leaf: just pair sequentially
            return list(zip(server_interfaces, [li["id"] for li in available_leaf_interfaces], strict=False))

        # Multiple leaves: round-robin by leaf
        leaf_ids = [leaf.id for leaf in leaf_switches]
        interfaces_by_leaf: dict[str, list[dict[str, Any]]] = {lid: [] for lid in leaf_ids}
        for li in available_leaf_interfaces:
            interfaces_by_leaf[li["leaf_id"]].append(li)

        pairings: list[tuple[dict[str, Any], str]] = []
        leaf_index = 0
        for server_iface in server_interfaces:
            # Find the next leaf with available interfaces
            for _ in range(len(leaf_ids)):
                current_leaf = leaf_ids[leaf_index % len(leaf_ids)]
                if interfaces_by_leaf[current_leaf]:
                    leaf_iface = interfaces_by_leaf[current_leaf].pop(0)
                    pairings.append((server_iface, leaf_iface["id"]))
                    leaf_index += 1
                    break
                leaf_index += 1

        return pairings

    async def _cable_interface(
        self,
        server_hostname: str,
        server_iface: dict[str, Any],
        leaf_iface_id: str,
    ) -> None:
        """Create a network link between server and leaf interfaces and assign VLANs."""
        # Re-fetch interfaces for proper SDK objects
        server_interface = await self.client.get(DcimInterface, id=server_iface["id"])
        leaf_interface = await self.client.get(DcimInterface, id=leaf_iface_id, include=["connector"])

        # Create the network link
        link_name = f"{server_hostname}-{server_iface['name']}__{leaf_interface.device.display_label}-{leaf_interface.name.value}"
        network_link = await self.client.create(
            DcimConnector,
            name=link_name,
            medium="copper",
            connected_endpoints=[server_interface, leaf_interface],
        )
        await network_link.save(allow_upsert=True)

        # Re-fetch interfaces after link creation to get updated link relationship
        server_interface = await self.client.get(DcimInterface, id=server_iface["id"], include=["connector"])
        leaf_interface = await self.client.get(
            DcimInterface, id=leaf_iface_id, include=["connector", "tagged_vlan", "untagged_vlan"],
        )

        # Set interfaces to active
        server_interface.status.value = "active"
        await server_interface.save(allow_upsert=True)

        leaf_interface.status.value = "active"

        # Assign VLANs from server interface to leaf interface
        if server_iface["tagged_vlan_ids"]:
            await leaf_interface.tagged_vlan.fetch()  # type: ignore[union-attr]
            leaf_interface.tagged_vlan.extend(server_iface["tagged_vlan_ids"])  # type: ignore[union-attr]
        if server_iface["untagged_vlan_id"]:
            await leaf_interface.untagged_vlan.fetch()  # type: ignore[union-attr]
            leaf_interface.untagged_vlan.add(server_iface["untagged_vlan_id"])  # type: ignore[union-attr]

        await leaf_interface.save(allow_upsert=True)

        self.logger.info("Cabled %s %s → %s", server_hostname, server_iface["name"], leaf_interface.name.value)
