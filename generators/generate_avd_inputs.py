"""AVD Input Builder Generator.

This generator builds and stores pyAVD hostvars for all devices in a fabric.
The hostvars are stored in each device's avd_inputs JSON attribute.
"""

from __future__ import annotations

import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator

from solution_ai_dc.avd import ROLE_TO_AVD_TYPE


class AvdInputsGenerator(InfrahubGenerator):
    """Builds and stores pyAVD hostvars for all devices in a fabric."""

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        """Generate AVD inputs for all devices in the fabric."""
        # Get fabric info
        fabric_edges = data.get("NetworkFabric", {}).get("edges", [])
        if not fabric_edges:
            self.logger.warning("No fabric found in query results")
            return

        fabric_node = fabric_edges[0]["node"]
        fabric_name = fabric_node["name"]["value"]
        fabric_id = fabric_node["id"]
        mgmt_gateway = fabric_node.get("mgmt_gateway", {})
        mgmt_gateway_value = mgmt_gateway.get("value") if mgmt_gateway else None

        self.logger.info(f"Building AVD inputs for fabric: {fabric_name}")

        # Get all devices and filter by fabric
        device_edges = data.get("NetworkDevice", {}).get("edges", [])
        fabric_devices = []

        for edge in device_edges:
            device = edge["node"]
            # Check if device belongs to this fabric
            pod = device.get("pod", {}).get("node")
            if not pod:
                continue
            parent = pod.get("parent", {}).get("node")
            if not parent or parent.get("id") != fabric_id:
                continue
            fabric_devices.append(device)

        self.logger.info(f"Found {len(fabric_devices)} devices in fabric {fabric_name}")

        # Build and store hostvars for each device
        for device in fabric_devices:
            hostname = device["hostname"]["value"]
            hostvars = self._build_device_hostvars(device, fabric_name, mgmt_gateway_value)

            # Store hostvars in device's avd_inputs attribute
            device_obj = await self.client.get(kind="NetworkDevice", id=device["id"])
            device_obj.avd_inputs.value = hostvars
            await device_obj.save()

            self.logger.info(f"Stored AVD inputs for device: {hostname}")

    def _build_device_hostvars(
        self,
        device: dict[str, Any],
        fabric_name: str,
        mgmt_gateway: str | None,
    ) -> dict[str, Any]:
        """Build hostvars dict for a single device."""
        role = device["role"]["value"]

        # Get AVD type from role
        avd_type = ROLE_TO_AVD_TYPE.get(role, role)

        # Get BGP ASN and Node ID
        bgp_asn = device.get("bgp_asn", {})
        bgp_asn_value = bgp_asn.get("value") if bgp_asn else None

        node_id = device.get("node_id", {})
        node_id_value = node_id.get("value") if node_id else None

        hostvars: dict[str, Any] = {
            "type": avd_type,
            "fabric_name": fabric_name,
        }

        if bgp_asn_value is not None:
            hostvars["bgp_as"] = str(bgp_asn_value)

        if node_id_value is not None:
            hostvars["id"] = node_id_value

        # Get loopback IP
        loopback_ip = device.get("loopback_ip", {}).get("node")
        if loopback_ip and loopback_ip.get("address", {}).get("value"):
            address = loopback_ip["address"]["value"]
            # Strip prefix length if present
            hostvars["loopback_ipv4_address"] = address.split("/")[0]

        # Get management IP
        mgmt_ip = device.get("mgmt_ip", {}).get("node")
        if mgmt_ip and mgmt_ip.get("address", {}).get("value"):
            address = mgmt_ip["address"]["value"]
            hostvars["mgmt_ip"] = address.split("/")[0]

        if mgmt_gateway:
            hostvars["mgmt_gateway"] = mgmt_gateway

        # Get uplink information for spine and leaf devices
        uplink_role = None
        if role == "spine":
            uplink_role = "super_spine"
        elif role == "leaf":
            uplink_role = "spine"

        if uplink_role:
            uplinks = self._extract_uplinks(device, uplink_role)
            if uplinks["uplink_interfaces"]:
                hostvars["uplink_interfaces"] = uplinks["uplink_interfaces"]
                hostvars["uplink_switches"] = uplinks["uplink_switches"]
                hostvars["uplink_switch_interfaces"] = uplinks["uplink_switch_interfaces"]

        return hostvars

    def _extract_uplinks(
        self,
        device: dict[str, Any],
        uplink_role: str,
    ) -> dict[str, list[str]]:
        """Extract uplink information from device interfaces."""
        uplink_interfaces: list[str] = []
        uplink_switches: list[str] = []
        uplink_switch_interfaces: list[str] = []

        interfaces = device.get("interfaces", {}).get("edges", [])

        for edge in interfaces:
            interface = edge["node"]
            iface_role = interface.get("role", {})
            if not iface_role or iface_role.get("value") != uplink_role:
                continue

            uplink_interfaces.append(interface["name"]["value"])

            # Get the remote endpoint from the link
            link = interface.get("link", {}).get("node")
            if link:
                endpoints = link.get("endpoints", {}).get("edges", [])
                for ep_edge in endpoints:
                    endpoint = ep_edge["node"]
                    # Skip this interface, find the remote one
                    if endpoint.get("id") != interface["id"]:
                        remote_device = endpoint.get("device", {}).get("node")
                        if remote_device:
                            uplink_switches.append(remote_device["hostname"]["value"])
                            uplink_switch_interfaces.append(endpoint["name"]["value"])

        return {
            "uplink_interfaces": uplink_interfaces,
            "uplink_switches": uplink_switches,
            "uplink_switch_interfaces": uplink_switch_interfaces,
        }
