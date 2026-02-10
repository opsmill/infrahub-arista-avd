"""Backfill Structured Config Generator.

Reads AVD structured config per-device and backfills IpamIPPrefix,
IpamIPAddress, NetworkInterface.mtu, BGP peer groups/neighbors,
prefix lists, route maps, and static routes into the Infrahub data model.
"""

from __future__ import annotations

import ipaddress
import json
import logging
from typing import Any

from infrahub_sdk.exceptions import NodeNotFoundError
from infrahub_sdk.generator import InfrahubGenerator
from infrahub_sdk.node import NodeProperty

from solution_ai_dc.protocols import (
    CoreAccountGroup,
    IpamIPAddress,
    IpamIPPrefix,
    NetworkInterface,
    RoutingBGPNeighbor,
    RoutingBGPPeerGroup,
    RoutingPrefixList,
    RoutingPrefixListEntry,
    RoutingRouteMap,
    RoutingRouteMapEntry,
    RoutingStaticRoute,
)

from .backfill_structured_config_query import (
    BackfillStructuredConfigQuery,
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode,
)

INTERFACE_SECTIONS = ["ethernet_interfaces", "loopback_interfaces", "management_interfaces"]

ROUTING_SECTIONS = ["router_bgp", "prefix_lists", "route_maps", "static_routes"]

UNMODELED_SECTIONS = [
    "ip_routing",
    "service_routing_protocols_model",
    "spanning_tree",
    "vlan_internal_order",
    "ip_name_servers",
    "ntp",
    "management_api_http",
]


class BackfillStructuredConfigGenerator(InfrahubGenerator):
    """Backfills structured config data into the Infrahub data model."""

    logger = logging.getLogger("infrahub.tasks")

    async def _get_avd_source(self) -> str | None:
        """Look up the 'AVD' CoreAccountGroup and return its ID for source attribution.

        Returns None with a warning log if the group cannot be found.
        """
        try:
            group = await self.client.get(CoreAccountGroup, name__value="AVD")
        except NodeNotFoundError:
            self.logger.warning("CoreAccountGroup 'AVD' not found; skipping source attribution")
            return None
        else:
            return group.id

    @staticmethod
    def _set_source(node: Any, source_id: str | None) -> None:  # noqa: ANN401
        """Set the source property on all attributes of a node.

        No-op when *source_id* is ``None``.
        """
        if not source_id:
            return
        prop = NodeProperty(source_id)
        for attr_name in node._attributes:  # noqa: SLF001
            attr = getattr(node, attr_name, None)
            if attr is not None and hasattr(attr, "source"):
                attr.source = prop

    def _build_interface_map(
        self,
        interfaces: list[BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode],
    ) -> dict[str, BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode]:
        """Build a dict mapping interface name -> GraphQL interface node."""
        result: dict[str, BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode] = {}
        for iface in interfaces:
            if iface.name and iface.name.value:
                result[iface.name.value] = iface
        return result

    async def _backfill_ip(
        self,
        interface_node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode,
        ip_str: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Create IpamIPPrefix and IpamIPAddress, assign to interface."""
        iface_name = interface_node.name.value if interface_node.name else "unknown"

        try:
            ip_iface = ipaddress.ip_interface(ip_str)
        except ValueError:
            self.logger.warning(f"[{hostname}] Invalid IP format '{ip_str}' on {iface_name}, skipping")
            return

        network = ip_iface.network
        prefix_str = str(network)

        prefix = await self.client.create(
            IpamIPPrefix,
            prefix=prefix_str,
            role="backfill",
        )
        self._set_source(prefix, avd_source)
        await prefix.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Ensured prefix {prefix_str}")

        ip_address = await self.client.create(
            IpamIPAddress,
            address=str(ip_iface),
            ip_prefix=prefix,
        )
        self._set_source(ip_address, avd_source)
        await ip_address.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Ensured IP address {ip_iface}")

        interface = await self.client.get(NetworkInterface, id=interface_node.id, include=["link"])
        interface.ip_address = ip_address
        await interface.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Assigned {ip_iface} to {iface_name}")

    async def _update_mtu(
        self,
        interface_node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode,
        mtu: int,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Update interface MTU if it differs from current value."""
        iface_name = interface_node.name.value if interface_node.name else "unknown"
        current_mtu = interface_node.mtu.value if interface_node.mtu else None

        if current_mtu == mtu:
            return

        interface = await self.client.get(NetworkInterface, id=interface_node.id)
        interface.mtu.value = mtu
        if avd_source and hasattr(interface.mtu, "source"):
            interface.mtu.source = NodeProperty(avd_source)
        await interface.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Updated MTU on {iface_name}: {current_mtu} -> {mtu}")

    # --- BGP backfill ---

    @staticmethod
    def _extract_optional(
        config: dict[str, Any], keys: list[str], stringify: list[str] | None = None
    ) -> dict[str, Any]:
        """Extract optional fields from a config dict, only including non-None/non-empty values."""
        result: dict[str, Any] = {}
        stringify = stringify or []
        for key in keys:
            val = config.get(key)
            if val is not None and (val or isinstance(val, (bool, int))):
                result[key] = str(val) if key in stringify else val
        return result

    async def _backfill_bgp_peer_groups(
        self,
        bgp_config: dict[str, Any],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> dict[str, Any]:
        """Backfill BGP peer groups, return a map of name -> saved peer group object."""
        peer_group_map: dict[str, Any] = {}
        pg_fields = [
            "type",
            "remote_as",
            "local_as",
            "description",
            "send_community",
            "maximum_routes",
            "bfd",
            "ebgp_multihop",
            "update_source",
            "route_map_in",
            "route_map_out",
        ]
        for pg_config in bgp_config.get("peer_groups", []):
            pg_name = pg_config.get("name")
            if not pg_name:
                continue

            pg_attrs: dict[str, Any] = {"name": pg_name, "device": device_id}
            pg_attrs.update(self._extract_optional(pg_config, pg_fields, stringify=["remote_as", "local_as"]))

            peer_group = await self.client.create(RoutingBGPPeerGroup, **pg_attrs)
            self._set_source(peer_group, avd_source)
            await peer_group.save(allow_upsert=True)
            peer_group_map[pg_name] = peer_group
            self.logger.info(f"[{hostname}] Ensured BGP peer group '{pg_name}'")

        return peer_group_map

    async def _backfill_bgp_neighbors(
        self,
        bgp_config: dict[str, Any],
        device_id: str,
        hostname: str,
        peer_group_map: dict[str, Any],
        avd_source: str | None = None,
    ) -> None:
        """Backfill BGP neighbors from router_bgp config."""
        nb_fields = ["remote_as", "description", "shutdown", "bfd", "ebgp_multihop", "send_community"]
        for nb_config in bgp_config.get("neighbors", []):
            nb_addr = nb_config.get("ip_address")
            if not nb_addr:
                continue

            nb_attrs: dict[str, Any] = {"peer_address": nb_addr, "device": device_id}
            nb_attrs.update(self._extract_optional(nb_config, nb_fields, stringify=["remote_as"]))

            pg_name = nb_config.get("peer_group")
            if pg_name and pg_name in peer_group_map:
                nb_attrs["peer_group"] = peer_group_map[pg_name]

            neighbor = await self.client.create(RoutingBGPNeighbor, **nb_attrs)
            self._set_source(neighbor, avd_source)
            await neighbor.save(allow_upsert=True)
            self.logger.info(f"[{hostname}] Ensured BGP neighbor {nb_addr}")

    async def _backfill_bgp(
        self,
        bgp_config: dict[str, Any],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Backfill BGP peer groups and neighbors from router_bgp config."""
        peer_group_map = await self._backfill_bgp_peer_groups(bgp_config, device_id, hostname, avd_source)
        await self._backfill_bgp_neighbors(bgp_config, device_id, hostname, peer_group_map, avd_source)

    # --- Prefix list backfill ---

    async def _backfill_prefix_lists(
        self,
        prefix_lists: list[dict[str, Any]],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Backfill prefix list entries from structured config."""
        for pl_config in prefix_lists:
            pl_name = pl_config.get("name")
            if not pl_name:
                continue

            pl = await self.client.create(
                RoutingPrefixList,
                name=pl_name,
                device=device_id,
            )
            self._set_source(pl, avd_source)
            await pl.save(allow_upsert=True)
            self.logger.info(f"[{hostname}] Ensured prefix list '{pl_name}'")

            for seq_config in pl_config.get("sequence_numbers", []):
                seq = seq_config.get("sequence")
                action = seq_config.get("action")
                if seq is None or not action:
                    continue

                existing = await self.client.filters(
                    kind=RoutingPrefixListEntry,
                    prefix_list__ids=[pl.id],
                    sequence__value=seq,
                )
                if existing:
                    entry = existing[0]
                    entry.action.value = action  # type: ignore[union-attr]
                else:
                    entry = await self.client.create(
                        RoutingPrefixListEntry,
                        sequence=seq,
                        action=action,
                        prefix_list=pl,
                    )
                self._set_source(entry, avd_source)
                await entry.save(allow_upsert=True)
                self.logger.info(f"[{hostname}] Ensured prefix list entry {pl_name} seq {seq}")

    # --- Route map backfill ---

    async def _backfill_route_maps(
        self,
        route_maps: list[dict[str, Any]],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Backfill route map entries from structured config."""
        for rm_config in route_maps:
            rm_name = rm_config.get("name")
            if not rm_name:
                continue

            rm = await self.client.create(
                RoutingRouteMap,
                name=rm_name,
                device=device_id,
            )
            self._set_source(rm, avd_source)
            await rm.save(allow_upsert=True)
            self.logger.info(f"[{hostname}] Ensured route map '{rm_name}'")

            for seq_config in rm_config.get("sequence_numbers", []):
                seq = seq_config.get("sequence")
                seq_type = seq_config.get("type")
                if seq is None or not seq_type:
                    continue

                existing = await self.client.filters(
                    kind=RoutingRouteMapEntry,
                    route_map__ids=[rm.id],
                    sequence__value=seq,
                )
                if existing:
                    entry = existing[0]
                    entry.type.value = seq_type  # type: ignore[union-attr]
                    if seq_config.get("description"):
                        entry.description.value = seq_config["description"]  # type: ignore[union-attr]
                    if seq_config.get("match"):
                        entry.match.value = seq_config["match"]  # type: ignore[union-attr]
                    if seq_config.get("set"):
                        entry.set.value = seq_config["set"]  # type: ignore[union-attr]
                else:
                    entry_attrs: dict[str, Any] = {
                        "sequence": seq,
                        "type": seq_type,
                        "route_map": rm,
                    }
                    if seq_config.get("description"):
                        entry_attrs["description"] = seq_config["description"]
                    if seq_config.get("match"):
                        entry_attrs["match"] = seq_config["match"]
                    if seq_config.get("set"):
                        entry_attrs["set"] = seq_config["set"]
                    entry = await self.client.create(RoutingRouteMapEntry, **entry_attrs)

                self._set_source(entry, avd_source)
                await entry.save(allow_upsert=True)
                self.logger.info(f"[{hostname}] Ensured route map entry {rm_name} seq {seq}")

    # --- Static route backfill ---

    async def _backfill_static_routes(
        self,
        static_routes: list[dict[str, Any]],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Backfill static routes from structured config."""
        for sr_config in static_routes:
            prefix = sr_config.get("destination_address_prefix") or sr_config.get("prefix")
            if not prefix:
                continue

            sr_attrs: dict[str, Any] = {
                "prefix": prefix,
                "device": device_id,
            }
            if sr_config.get("gateway"):
                sr_attrs["gateway"] = sr_config["gateway"]
            if sr_config.get("next_hop"):
                sr_attrs["next_hop"] = sr_config["next_hop"]
            if sr_config.get("interface"):
                sr_attrs["interface"] = sr_config["interface"]
            if sr_config.get("distance") is not None:
                sr_attrs["distance"] = sr_config["distance"]
            if sr_config.get("tag") is not None:
                sr_attrs["tag"] = sr_config["tag"]
            if sr_config.get("name"):
                sr_attrs["route_name"] = sr_config["name"]
            vrf = sr_config.get("vrf", "default")
            sr_attrs["vrf"] = vrf or "default"

            route = await self.client.create(RoutingStaticRoute, **sr_attrs)
            self._set_source(route, avd_source)
            await route.save(allow_upsert=True)
            self.logger.info(f"[{hostname}] Ensured static route {prefix} (vrf={vrf})")

    # --- Routing section dispatch ---

    async def _process_routing_sections(
        self,
        structured_config: dict[str, Any],
        device_id: str,
        hostname: str,
        avd_source: str | None = None,
    ) -> None:
        """Process all routing sections from structured config."""
        bgp_config = structured_config.get("router_bgp")
        if bgp_config:
            self.logger.info(f"[{hostname}] Processing router_bgp")
            await self._backfill_bgp(bgp_config, device_id, hostname, avd_source)

        prefix_lists = structured_config.get("prefix_lists")
        if prefix_lists:
            self.logger.info(f"[{hostname}] Processing prefix_lists: {len(prefix_lists)} lists")
            await self._backfill_prefix_lists(prefix_lists, device_id, hostname, avd_source)

        route_maps = structured_config.get("route_maps")
        if route_maps:
            self.logger.info(f"[{hostname}] Processing route_maps: {len(route_maps)} maps")
            await self._backfill_route_maps(route_maps, device_id, hostname, avd_source)

        static_routes = structured_config.get("static_routes")
        if static_routes:
            self.logger.info(f"[{hostname}] Processing static_routes: {len(static_routes)} routes")
            await self._backfill_static_routes(static_routes, device_id, hostname, avd_source)

    # --- Main generate ---

    async def generate(self, data: dict) -> None:
        """Backfill IPs, MTU, and routing config from structured config into the data model."""
        data: BackfillStructuredConfigQuery = BackfillStructuredConfigQuery(**data)
        artifact = data.avd_artifact.edges[0].node

        # Get structured config identifier
        if not artifact.structured_config_identifier:
            self.logger.warning("No structured config identifier on artifact, skipping")
            return

        identifier = artifact.structured_config_identifier.value
        if not identifier:
            self.logger.warning("Empty structured config identifier, skipping")
            return

        # Get device info via relationship
        device = artifact.device.node
        if not device:
            self.logger.warning("No device linked to artifact, skipping")
            return

        hostname = device.hostname.value if device.hostname else "unknown"
        device_id = device.id

        # Fetch structured config from object storage
        try:
            content = await self.client.object_store.get(identifier=identifier)
        except (OSError, ValueError) as e:
            self.logger.warning(f"[{hostname}] Failed to fetch structured config: {e}")
            return

        try:
            structured_config: dict[str, Any] = json.loads(content)
        except json.JSONDecodeError as e:
            self.logger.warning(f"[{hostname}] Invalid JSON in structured config: {e}")
            return

        self.logger.info(f"[{hostname}] Loaded structured config with {len(structured_config)} top-level keys")

        # Look up AVD source for data lineage attribution
        avd_source = await self._get_avd_source()

        # Build interface map from GraphQL data
        interfaces = [edge.node for edge in device.interfaces.edges if edge.node]
        interface_map = self._build_interface_map(interfaces)

        # Process each interface section
        for section in INTERFACE_SECTIONS:
            section_data = structured_config.get(section, [])
            if not section_data:
                continue

            self.logger.info(f"[{hostname}] Processing {section}: {len(section_data)} interfaces")

            for iface_config in section_data:
                iface_name = iface_config.get("name")
                if not iface_name:
                    continue

                # Find matching interface in data model
                gql_iface = interface_map.get(iface_name)
                if not gql_iface:
                    self.logger.debug(f"[{hostname}] Interface {iface_name} not in data model, skipping")
                    continue

                # IP backfill (gap-fill only)
                ip_str = iface_config.get("ip_address")
                if ip_str and not (gql_iface.ip_address.node):
                    await self._backfill_ip(gql_iface, ip_str, hostname, avd_source)

                # MTU update
                mtu = iface_config.get("mtu")
                if mtu is not None:
                    await self._update_mtu(gql_iface, mtu, hostname, avd_source)

        # Process routing sections
        await self._process_routing_sections(structured_config, device_id, hostname, avd_source)

        # Log remaining unmodeled sections
        unmodeled_present = [s for s in UNMODELED_SECTIONS if s in structured_config]
        if unmodeled_present:
            self.logger.info(f"[{hostname}] Unmodeled sections in structured config: {', '.join(unmodeled_present)}")
