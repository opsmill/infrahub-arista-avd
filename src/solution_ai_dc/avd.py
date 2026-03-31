"""AVD (Arista Validated Design) utilities for Infrahub integration.

This module provides utilities for transforming Infrahub network data
into pyAVD-compatible hostvars structures.
"""

from __future__ import annotations

from typing import Any

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
        device_name: str,  # noqa: ARG002 - kept for API completeness
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
            device_name: Device name
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
