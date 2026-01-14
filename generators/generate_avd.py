"""AVD Generator.

This generator builds pyAVD hostvars from Infrahub data and generates
structured configurations for all devices in a fabric.
"""

from __future__ import annotations

import copy
import logging
from typing import Any
import json

import pyavd
from infrahub_sdk.generator import InfrahubGenerator

from solution_ai_dc.avd import ROLE_TO_AVD_TYPE


class AvdGenerator(InfrahubGenerator):
    """Builds AVD inputs and structured config for all devices in a fabric."""

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        """Generate AVD inputs and structured config for all devices."""
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

        self.logger.info(f"Building AVD config for fabric: {fabric_name}")

        # Get all devices and filter by fabric
        device_edges = data.get("NetworkDevice", {}).get("edges", [])
        fabric_devices: list[dict[str, Any]] = []


        # First pass: collect devices with pods in this fabric
        devices_by_role: dict[str, list[dict[str, Any]]] = {"super_spine": [], "spine": [], "leaf": []}
        referenced_super_spines: set[str] = set()

        for edge in device_edges:
            device = edge["node"]
            hostname = device.get("hostname", {}).get("value", "unknown")
            role = device.get("role", {}).get("value", "unknown")

            # Check if device belongs to this fabric via pod relationship
            pod = device.get("pod", {}).get("node")
            if pod:
                parent = pod.get("parent", {}).get("node")
                if parent and parent.get("id") == fabric_id:
                    fabric_devices.append(device)
                    if role in devices_by_role:
                        devices_by_role[role].append(device)
                    continue

            # Super-spines may not have pod set - collect them separately
            if role == "super_spine":
                devices_by_role["super_spine"].append(device)

        # Collect super-spine references from spines' uplink_switches
        for spine in devices_by_role["spine"]:
            uplinks = self._extract_uplinks(spine, "spine")
            for switch in uplinks["uplink_switches"]:
                referenced_super_spines.add(switch)

        # Add super-spines that are referenced by spines in this fabric
        for ss in devices_by_role["super_spine"]:
            hostname = ss.get("hostname", {}).get("value", "unknown")
            if hostname in referenced_super_spines and ss not in fabric_devices:
                self.logger.info(f"Including super-spine {hostname} (referenced by fabric spines)")
                fabric_devices.append(ss)

        self.logger.info(f"Found {len(fabric_devices)} devices in fabric {fabric_name}")

        if not fabric_devices:
            self.logger.warning("No devices found in fabric")
            return

        # Build fabric-wide node type configurations
        node_type_configs = self._build_node_type_configs(fabric_devices, fabric_name, mgmt_gateway_value)

        # Build hostvars for all devices (includes node type configs)
        all_hostvars: dict[str, dict[str, Any]] = {}
        device_map: dict[str, str] = {}  # hostname -> device_id

        for device in fabric_devices:
            hostname = device["hostname"]["value"]
            role = device["role"]["value"]
            avd_type = ROLE_TO_AVD_TYPE.get(role, role)

            # Each device's hostvars includes the full node type configs
            hostvars: dict[str, Any] = {
                "type": avd_type,
                "fabric_name": fabric_name,
                # Required for pyAVD to select correct default node_type_keys
                "design": {"type": "l3ls-evpn"},
            }

            # Add management gateway if available
            if mgmt_gateway_value:
                hostvars["mgmt_gateway"] = mgmt_gateway_value

            # Add node type configurations (required by pyAVD)
            hostvars.update(node_type_configs)

            all_hostvars[hostname] = hostvars
            device_map[hostname] = device["id"]

        self.logger.info(f"Built hostvars for {len(all_hostvars)} devices")

        # Generate AVD facts (requires all devices)
        # Make a deep copy since pyAVD modifies input data in-place
        hostvars_copy = copy.deepcopy(all_hostvars)
        avd_facts = pyavd.get_avd_facts(hostvars_copy)

        # Generate and store both avd_inputs and avd_structured_config per device
        for hostname, device_id in device_map.items():
            hostvars = all_hostvars[hostname]

            # Generate structured config for this device
            # Make a copy of this device's hostvars since pyAVD modifies data in-place
            device_inputs = copy.deepcopy(hostvars)

            structured_config = pyavd.get_device_structured_config(
                hostname,
                device_inputs,
                avd_facts,
            )

            # Store both avd_inputs and avd_structured_config
            device_obj = await self.client.get(kind="NetworkDevice", id=device_id)
            device_obj.avd_inputs.value = {}
            response = await self.client.object_store.upload(content=json.dumps(structured_config))
            device_obj.avd_file_identifier = response['identifier']
            device_obj.avd_file_checksum = response['checksum']
            await device_obj.save()

            self.logger.info(f"Stored AVD config for device: {hostname}")

    def _build_node_type_configs(
        self,
        devices: list[dict[str, Any]],
        fabric_name: str,
        mgmt_gateway: str | None,
    ) -> dict[str, Any]:
        """Build node type configurations for the fabric.

        AVD requires node type keys (spine, l3leaf, super-spine) with their
        defaults and nodes lists.
        """
        # Group devices by role/type
        super_spines: list[dict[str, Any]] = []
        spines: list[dict[str, Any]] = []
        leaves: list[dict[str, Any]] = []

        for device in devices:
            role = device["role"]["value"]
            hostname = device["hostname"]["value"]
            node_id = device.get("node_id", {})
            node_id_value = node_id.get("value") if node_id else None
            bgp_asn = device.get("bgp_asn", {})
            bgp_asn_value = bgp_asn.get("value") if bgp_asn else None

            # Get loopback IP
            loopback_ip = None
            loopback_ip_data = device.get("loopback_ip", {}).get("node")
            if loopback_ip_data and loopback_ip_data.get("address", {}).get("value"):
                address = loopback_ip_data["address"]["value"]
                loopback_ip = address.split("/")[0]

            # Get management IP
            mgmt_ip = None
            mgmt_ip_data = device.get("mgmt_ip", {}).get("node")
            if mgmt_ip_data and mgmt_ip_data.get("address", {}).get("value"):
                address = mgmt_ip_data["address"]["value"]
                mgmt_ip = address.split("/")[0]

            node_config: dict[str, Any] = {"name": hostname}

            if node_id_value is not None:
                node_config["id"] = node_id_value

            if bgp_asn_value is not None:
                node_config["bgp_as"] = str(bgp_asn_value)

            if loopback_ip:
                node_config["loopback_ipv4_address"] = loopback_ip

            if mgmt_ip:
                node_config["mgmt_ip"] = mgmt_ip

            # Get uplink information for spine and leaf devices
            uplinks = self._extract_uplinks(device, role)
            if uplinks["uplink_interfaces"]:
                node_config["uplink_interfaces"] = uplinks["uplink_interfaces"]
                node_config["uplink_switches"] = uplinks["uplink_switches"]
                node_config["uplink_switch_interfaces"] = uplinks["uplink_switch_interfaces"]

            if role == "super_spine":
                super_spines.append(node_config)
            elif role == "spine":
                spines.append(node_config)
            elif role == "leaf":
                leaves.append(node_config)

        # Build the node type configuration structure
        # Note: AVD uses hyphenated keys for node types
        config: dict[str, Any] = {}

        if super_spines:
            # Note: AVD uses underscore for super_spine key, but hyphen for type value
            config["super_spine"] = {
                "defaults": {
                    "platform": "vEOS-lab",
                    # Placeholder pools - individual IPs are set per node
                    "loopback_ipv4_pool": "10.255.0.0/24",
                },
                "nodes": super_spines,
            }

        if spines:
            config["spine"] = {
                "defaults": {
                    "platform": "vEOS-lab",
                    # Placeholder pools - individual IPs are set per node
                    "loopback_ipv4_pool": "10.255.1.0/24",
                    "uplink_ipv4_pool": "10.254.0.0/16",
                },
                "nodes": spines,
            }

        if leaves:
            config["l3leaf"] = {
                "defaults": {
                    "platform": "vEOS-lab",
                    # Placeholder pools - individual IPs are set per node
                    "loopback_ipv4_pool": "10.255.2.0/24",
                    "vtep_loopback_ipv4_pool": "10.255.3.0/24",
                    "uplink_ipv4_pool": "10.253.0.0/16",
                },
                "nodes": leaves,
            }

        return config

    def _extract_uplinks(
        self,
        device: dict[str, Any],
        role: str,
    ) -> dict[str, list[str]]:
        """Extract uplink information from device interfaces."""
        uplink_interfaces: list[str] = []
        uplink_switches: list[str] = []
        uplink_switch_interfaces: list[str] = []

        # Determine uplink role based on device role
        uplink_role = None
        if role == "spine":
            uplink_role = "super_spine"
        elif role == "leaf":
            uplink_role = "spine"

        if not uplink_role:
            return {
                "uplink_interfaces": uplink_interfaces,
                "uplink_switches": uplink_switches,
                "uplink_switch_interfaces": uplink_switch_interfaces,
            }

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
                    endpoint = ep_edge.get("node")
                    # Skip null endpoints or this interface
                    if not endpoint:
                        continue
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
