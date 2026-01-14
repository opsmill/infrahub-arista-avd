"""AVD (Arista Validated Design) utilities for Infrahub integration.

This module provides utilities for transforming Infrahub network data
into pyAVD-compatible hostvars structures.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

# Mapping from Infrahub device roles to AVD types
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
}


def get_avd_type(role: str) -> str:
    """Convert Infrahub device role to AVD device type.

    Args:
        role: The Infrahub device role (super_spine, spine, leaf)

    Returns:
        The corresponding AVD device type

    Raises:
        ValueError: If the role is not recognized
    """
    if role not in ROLE_TO_AVD_TYPE:
        msg = f"Unknown device role: {role}"
        raise ValueError(msg)
    return ROLE_TO_AVD_TYPE[role]


def extract_uplink_info(
    device_interfaces: Sequence[Any],
    uplink_role: str,
) -> tuple[list[str], list[str], list[str]]:
    """Extract uplink information from device interfaces.

    Args:
        device_interfaces: List of interface objects with link and name attributes
        uplink_role: The interface role to filter for uplinks (e.g., "super_spine", "spine")

    Returns:
        Tuple of (uplink_interfaces, uplink_switches, uplink_switch_interfaces)
    """
    uplink_interfaces: list[str] = []
    uplink_switches: list[str] = []
    uplink_switch_interfaces: list[str] = []

    for interface in device_interfaces:
        if interface.role.value != uplink_role:
            continue

        uplink_interfaces.append(interface.name.value)

        # Get the remote endpoint from the link
        if interface.link.node:
            link = interface.link.node
            for endpoint in link.endpoints.peers:
                # Skip this interface, find the remote one
                if endpoint.id != interface.id:
                    remote_device = endpoint.device.node
                    uplink_switches.append(remote_device.hostname.value)
                    uplink_switch_interfaces.append(endpoint.name.value)

    return uplink_interfaces, uplink_switches, uplink_switch_interfaces


class AvdInputsBuilder:
    """Builder for constructing pyAVD hostvars from Infrahub data."""

    def __init__(self, fabric_name: str, mgmt_gateway: str | None = None) -> None:
        """Initialize the builder.

        Args:
            fabric_name: Name of the network fabric
            mgmt_gateway: Default gateway for management network
        """
        self.fabric_name = fabric_name
        self.mgmt_gateway = mgmt_gateway

    def build_device_hostvars(
        self,
        hostname: str,  # noqa: ARG002 - kept for API completeness
        role: str,
        bgp_asn: int,
        node_id: int,
        loopback_ip: str | None = None,
        mgmt_ip: str | None = None,
        uplink_interfaces: list[str] | None = None,
        uplink_switches: list[str] | None = None,
        uplink_switch_interfaces: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build hostvars dict for a single device.

        Args:
            hostname: Device hostname
            role: Device role (super_spine, spine, leaf)
            bgp_asn: BGP autonomous system number
            node_id: Unique node ID within the fabric
            loopback_ip: Loopback IP address (optional)
            mgmt_ip: Management IP address (optional)
            uplink_interfaces: List of local uplink interface names
            uplink_switches: List of upstream switch hostnames
            uplink_switch_interfaces: List of upstream switch interface names

        Returns:
            Dictionary of hostvars for pyAVD
        """
        avd_type = get_avd_type(role)

        hostvars: dict[str, Any] = {
            "type": avd_type,
            "id": node_id,
            "bgp_as": str(bgp_asn),
            "fabric_name": self.fabric_name,
        }

        if loopback_ip:
            hostvars["loopback_ipv4_address"] = loopback_ip

        if mgmt_ip:
            hostvars["mgmt_ip"] = mgmt_ip

        if self.mgmt_gateway:
            hostvars["mgmt_gateway"] = self.mgmt_gateway

        # Add uplink configuration for spine and leaf devices
        if role in ("spine", "leaf") and uplink_interfaces:
            hostvars["uplink_interfaces"] = uplink_interfaces
            if uplink_switches:
                hostvars["uplink_switches"] = uplink_switches
            if uplink_switch_interfaces:
                hostvars["uplink_switch_interfaces"] = uplink_switch_interfaces

        return hostvars

    def build_fabric_hostvars(
        self,
        devices: Sequence[Any],
    ) -> dict[str, dict[str, Any]]:
        """Build hostvars for all devices in a fabric.

        Args:
            devices: Sequence of device objects from Infrahub

        Returns:
            Dictionary mapping hostname to hostvars
        """
        all_hostvars: dict[str, dict[str, Any]] = {}

        for device in devices:
            hostname = device.hostname.value
            role = device.role.value
            bgp_asn = device.bgp_asn.value if hasattr(device, "bgp_asn") and device.bgp_asn.value else 0
            node_id = device.node_id.value if hasattr(device, "node_id") and device.node_id.value else 0

            loopback_ip = None
            if hasattr(device, "loopback_ip") and device.loopback_ip.node:
                loopback_ip = str(device.loopback_ip.node.address.value).split("/")[0]

            mgmt_ip = None
            if hasattr(device, "mgmt_ip") and device.mgmt_ip.node:
                mgmt_ip = str(device.mgmt_ip.node.address.value).split("/")[0]

            # Determine uplink role based on device role
            uplink_role = None
            if role == "spine":
                uplink_role = "super_spine"
            elif role == "leaf":
                uplink_role = "spine"

            uplink_interfaces: list[str] = []
            uplink_switches: list[str] = []
            uplink_switch_interfaces: list[str] = []

            if uplink_role and hasattr(device, "interfaces"):
                uplink_interfaces, uplink_switches, uplink_switch_interfaces = extract_uplink_info(
                    device.interfaces.peers,
                    uplink_role,
                )

            hostvars = self.build_device_hostvars(
                hostname=hostname,
                role=role,
                bgp_asn=bgp_asn,
                node_id=node_id,
                loopback_ip=loopback_ip,
                mgmt_ip=mgmt_ip,
                uplink_interfaces=uplink_interfaces,
                uplink_switches=uplink_switches,
                uplink_switch_interfaces=uplink_switch_interfaces,
            )

            all_hostvars[hostname] = hostvars

        return all_hostvars
