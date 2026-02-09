"""Backfill Structured Config Generator.

Reads AVD structured config per-device and backfills IpamIPPrefix,
IpamIPAddress, and NetworkInterface.mtu into the Infrahub data model.
"""

from __future__ import annotations

import ipaddress
import json
import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator

from solution_ai_dc.protocols import NetworkInterface

from .backfill_structured_config_query import (
    BackfillStructuredConfigQuery,
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode,
)

INTERFACE_SECTIONS = ["ethernet_interfaces", "loopback_interfaces", "management_interfaces"]

UNMODELED_SECTIONS = [
    "router_bgp",
    "prefix_lists",
    "route_maps",
    "ip_routing",
    "static_routes",
    "service_routing_protocols_model",
    "spanning_tree",
    "vlan_internal_order",
    "ip_name_servers",
    "ntp",
    "management_api_http",
]


class BackfillStructuredConfigGenerator(InfrahubGenerator):
    """Backfills IP addresses and MTU from AVD structured config into the data model."""

    logger = logging.getLogger("infrahub.tasks")

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
            kind="IpamIPPrefix",
            prefix=prefix_str,
            role="backfill",
        )
        await prefix.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Ensured prefix {prefix_str}")

        ip_address = await self.client.create(
            kind="IpamIPAddress",
            address=str(ip_iface),
            ip_prefix=prefix,
        )
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
    ) -> None:
        """Update interface MTU if it differs from current value."""
        iface_name = interface_node.name.value if interface_node.name else "unknown"
        current_mtu = interface_node.mtu.value if interface_node.mtu else None

        if current_mtu == mtu:
            return

        interface = await self.client.get(NetworkInterface, id=interface_node.id)
        interface.mtu.value = mtu
        await interface.save(allow_upsert=True)
        self.logger.info(f"[{hostname}] Updated MTU on {iface_name}: {current_mtu} -> {mtu}")

    async def generate(self, data: dict) -> None:
        """Backfill IPs and MTU from structured config into the data model."""
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
                    await self._backfill_ip(gql_iface, ip_str, hostname)

                # MTU update
                mtu = iface_config.get("mtu")
                if mtu is not None:
                    await self._update_mtu(gql_iface, mtu, hostname)

        # Log unmodeled sections
        unmodeled_present = [s for s in UNMODELED_SECTIONS if s in structured_config]
        if unmodeled_present:
            self.logger.info(f"[{hostname}] Unmodeled sections in structured config: {', '.join(unmodeled_present)}")
