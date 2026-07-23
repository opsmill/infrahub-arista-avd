from __future__ import annotations

import logging
import re
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator
from netutils.interface import sort_interface_list

from solution_arista_avd.cabling import build_server_cabling_plan, connect_interface_maps
from solution_arista_avd.generator import set_fabric_avd_hostvars_ready, trigger_hostvar_generation
from solution_arista_avd.protocols import DcimDevice, DcimInterface, InterfacePhysical, LocationRack, NetworkPod
from solution_arista_avd.sorting import create_sorted_device_interface_map


class ServerCablingGenerator(InfrahubGenerator):
    logger = logging.getLogger("infrahub.tasks")
    PORT_CHANNEL_RE = re.compile(r"\d+")

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

        server_already_cabled = await self._is_server_cabled(server_interfaces)

        # Find leaf switches in the same rack
        leaf_switches = await self.client.filters(kind=DcimDevice, rack__ids=[rack_id], role__values=["leaf", "l2leaf"])
        if not leaf_switches:
            self.logger.warning("No leaf switches found in rack %s for server %s", rack_name, server_hostname)
            return

        # Build sorted interface maps (same pattern as pod/rack generators)
        server_iface_objects = await self.client.filters(kind=InterfacePhysical, device__name__value=server_hostname)

        # Populate the SDK store with the server device using its actual typename
        # (e.g. ComputePhysicalServer, not DcimDevice) so interface.device.peer resolves
        if server_iface_objects:
            device_rel = server_iface_objects[0].device
            await self.client.get(kind=device_rel.typename, id=device_rel.id)

        server_interface_map = create_sorted_device_interface_map(server_iface_objects)

        leaf_interfaces = await self.client.filters(
            kind=InterfacePhysical,
            device__ids=[leaf.id for leaf in leaf_switches],
            role__value="server",
        )
        leaf_interface_map = create_sorted_device_interface_map(leaf_interfaces)

        if not leaf_interface_map:
            self.logger.warning(
                "No server-role interfaces on leaf switches in rack %s for server %s",
                rack_name,
                server_hostname,
            )
            return

        if server_already_cabled:
            cabling_plan = await self._existing_cabling_plan(server_interfaces)
            if not cabling_plan:
                self.logger.warning("Server %s appears cabled but no leaf links were found", server_hostname)
                return
            self.logger.info("Server %s already cabled — reconciling VLANs and LAGs", server_hostname)
        else:
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

        # For dual-homed servers (connected to 2+ leaf switches), create server
        # and switch-side LAGs.
        await self._create_server_port_channel(server_hostname, cabling_plan)

        # Trigger AVD hostvar regeneration for the leaves connected to this server.
        hostvar_target_ids = self._connected_leaf_device_ids(cabling_plan)
        await self._trigger_avd_cascade(rack_id, server_hostname, hostvar_target_ids)

    async def _create_server_port_channel(
        self,
        server_hostname: str,
        cabling_plan: list[tuple[DcimInterface, DcimInterface]],
    ) -> None:
        """Create server and switch LAGs for dual-homed servers.

        Switch-side LAGs own the EOS Port-Channel ID used by AVD. The server-side
        Bond1 remains useful as the endpoint port-channel description source.
        """
        if len(cabling_plan) < 2:
            return

        # Check if connections go to multiple leaf switches (dual-homed)
        connected_leaf_ids: set[str] = set()
        server_iface_ids = []
        leaf_iface_ids = []
        for server_iface, leaf_iface in self._sort_cabling_plan_by_leaf_port(cabling_plan):
            server_iface_ids.append(server_iface.id)
            leaf_iface_ids.append(leaf_iface.id)
            connected_leaf_ids.add(leaf_iface.device.peer.id)

        if len(connected_leaf_ids) < 2:
            return

        channel_id = self._derive_channel_id(cabling_plan)
        lag_name = f"Port-Channel{channel_id}"
        evpn_ethernet_segment = not self._is_mlag_backed(cabling_plan)

        self.logger.info("Creating LAGs for dual-homed server %s using %s", server_hostname, lag_name)

        # Get the server device to find its ID
        server_iface = await self.client.get(InterfacePhysical, id=server_iface_ids[0])
        server_device_id = server_iface.device.id

        # Create LAG on the server (represents a server-side bond, not a switch Port-Channel)
        lag = await self.client.create(
            "InterfaceLag",
            name="Bond1",
            device={"id": server_device_id},
            lacp_mode="active",
            lacp_rate="fast",
            status="active",
            role="server",
        )
        await lag.save(allow_upsert=True)

        # Assign server physical interfaces as LAG members
        for iface_id in server_iface_ids:
            iface = await self.client.get(InterfacePhysical, id=iface_id)
            iface.lag = {"id": lag.id}  # type: ignore[attr-defined]
            await iface.save(allow_upsert=True)

        for _, leaf_iface in self._sort_cabling_plan_by_leaf_port(cabling_plan):
            leaf_lag = await self.client.create(
                "InterfaceLag",
                name=lag_name,
                device={"id": leaf_iface.device.id},
                channel_id=channel_id,
                lacp_mode="active",
                lacp_rate="fast",
                status="active",
                role="server",
                evpn_ethernet_segment=evpn_ethernet_segment,
            )
            await leaf_lag.save(allow_upsert=True)

            iface = await self.client.get(InterfacePhysical, id=leaf_iface.id)
            iface.lag = {"id": leaf_lag.id}  # type: ignore[attr-defined]
            await iface.save(allow_upsert=True)

        self.logger.info(
            "  Bond1 and %s created for %s with %d members",
            lag_name,
            server_hostname,
            len(server_iface_ids),
        )

    async def _existing_cabling_plan(
        self, server_interfaces: list[dict[str, Any]]
    ) -> list[tuple[DcimInterface, DcimInterface]]:
        cabling_plan: list[tuple[DcimInterface, DcimInterface]] = []
        for iface_data in server_interfaces:
            server_iface = await self.client.get(InterfacePhysical, id=iface_data["id"], include=["connector"])
            connector = getattr(server_iface, "connector", None)
            if not connector or not connector.id:
                continue
            await connector.fetch()
            link = connector.peer
            await link.connected_endpoints.fetch()
            for endpoint_peer in link.connected_endpoints.peers:
                endpoint = endpoint_peer.peer
                if endpoint.id == server_iface.id:
                    continue
                if getattr(endpoint, "device", None) and endpoint.device.id != server_iface.device.id:
                    cabling_plan.append((server_iface, endpoint))
                    break
        return cabling_plan

    @classmethod
    def _sort_cabling_plan_by_leaf_port(
        cls, cabling_plan: list[tuple[DcimInterface, DcimInterface]]
    ) -> list[tuple[DcimInterface, DcimInterface]]:
        return sorted(
            cabling_plan,
            key=lambda item: (
                item[1].device.display_label,
                sort_interface_list([item[1].name.value])[0],
                item[0].name.value,
            ),
        )

    @classmethod
    def _derive_channel_id(cls, cabling_plan: list[tuple[DcimInterface, DcimInterface]]) -> int:
        first_leaf_port = cls._sort_cabling_plan_by_leaf_port(cabling_plan)[0][1].name.value
        digits = "".join(cls.PORT_CHANNEL_RE.findall(first_leaf_port))
        if not digits:
            raise ValueError(f"Cannot derive Port-Channel ID from switch port '{first_leaf_port}'")
        return int(digits)

    @staticmethod
    def _is_mlag_backed(cabling_plan: list[tuple[DcimInterface, DcimInterface]]) -> bool:
        mlag_domain_ids = {
            getattr(getattr(leaf_iface.device.peer, "mlag_domain", None), "id", None)
            or getattr(getattr(leaf_iface.device, "peer", None), "mlag_domain_id", None)
            for _, leaf_iface in cabling_plan
        }
        mlag_domain_ids.discard(None)
        return bool(mlag_domain_ids)

    @classmethod
    def _connected_leaf_device_ids(cls, cabling_plan: list[tuple[DcimInterface, DcimInterface]]) -> list[str]:
        leaf_ids: list[str] = []
        for _, leaf_iface in cls._sort_cabling_plan_by_leaf_port(cabling_plan):
            device_rel = getattr(leaf_iface, "device", None)
            leaf_id = getattr(device_rel, "id", None)
            if not isinstance(leaf_id, str):
                leaf_id = getattr(getattr(device_rel, "peer", None), "id", None)
            if isinstance(leaf_id, str) and leaf_id not in leaf_ids:
                leaf_ids.append(leaf_id)
        return leaf_ids

    async def _trigger_avd_cascade(self, rack_id: str, server_hostname: str, hostvar_target_ids: list[str]) -> None:
        """Navigate from rack to fabric and trigger AVD hostvar regeneration."""
        rack = await self.client.get(LocationRack, id=rack_id)
        await rack.pod.fetch()  # type: ignore[union-attr]
        pod = await self.client.get(NetworkPod, id=rack.pod.peer.id)  # type: ignore[union-attr]
        await pod.parent.fetch()  # type: ignore[union-attr]
        fabric = pod.parent.peer  # type: ignore[union-attr]

        self.logger.info(
            "Server %s cabled — triggering AVD cascade for fabric %s and %d leaf target(s)",
            server_hostname,
            fabric.name.value,
            len(hostvar_target_ids),
        )
        await set_fabric_avd_hostvars_ready(self.client, fabric.id, False)
        if not hostvar_target_ids:
            self.logger.warning(
                "Server %s cabled but no connected leaf target IDs were found; skipping hostvar generation",
                server_hostname,
            )
            return
        await trigger_hostvar_generation(self.client, node_ids=hostvar_target_ids)

    def _get_server_interfaces(self, server_node: dict) -> list[dict[str, Any]]:
        """Extract server interfaces with their VLANs from the GQL response."""
        interfaces = []
        for edge in server_node.get("interfaces", {}).get("edges", []):
            node = edge["node"]
            if node.get("__typename") != "InterfacePhysical":
                continue
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
                idx < len(ifaces) and not ifaces[idx].connector.id for ifaces in leaf_interface_map.values()
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
                include=["tagged_vlan", "untagged_vlan", "connector"],
            )

            if server_iface["tagged_vlan_ids"]:
                await leaf_interface.tagged_vlan.fetch()  # type: ignore[union-attr]
                leaf_interface.tagged_vlan.extend(server_iface["tagged_vlan_ids"])  # type: ignore[union-attr]
            if server_iface["untagged_vlan_id"]:
                await leaf_interface.untagged_vlan.fetch()  # type: ignore[union-attr]
                leaf_interface.untagged_vlan.add(server_iface["untagged_vlan_id"])  # type: ignore[union-attr]

            await leaf_interface.save(allow_upsert=True)
