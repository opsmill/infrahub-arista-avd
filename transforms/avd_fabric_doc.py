"""AVD Fabric Documentation Transform.

Generates fabric documentation from stored structured configs.
"""

import copy
from typing import Any

import pyavd
from infrahub_sdk.transforms import InfrahubTransform


class AvdFabricDocTransform(InfrahubTransform):
    """Generates fabric documentation from stored structured configs."""

    query = "avd_fabric_devices"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform fabric data to documentation."""
        # Get fabric info
        fabric_edges = data.get("NetworkFabric", {}).get("edges", [])
        if not fabric_edges:
            return "# No fabric found"

        fabric_node = fabric_edges[0]["node"]
        fabric_name = fabric_node["name"]["value"]
        fabric_id = fabric_node["id"]

        # Get all devices and filter by fabric
        device_edges = data.get("NetworkDevice", {}).get("edges", [])
        all_hostvars: dict[str, dict[str, Any]] = {}
        structured_configs: dict[str, dict[str, Any]] = {}

        for edge in device_edges:
            device = edge["node"]
            # Check if device belongs to this fabric
            pod = device.get("pod", {}).get("node")
            if not pod:
                continue
            parent = pod.get("parent", {}).get("node")
            if not parent or parent.get("id") != fabric_id:
                continue

            hostname = device["hostname"]["value"]

            avd_inputs = device.get("avd_inputs", {})
            avd_inputs_value = avd_inputs.get("value") if avd_inputs else None

            avd_structured = device.get("avd_structured_config", {})
            avd_structured_value = avd_structured.get("value") if avd_structured else None

            if avd_inputs_value:
                all_hostvars[hostname] = avd_inputs_value
            if avd_structured_value:
                structured_configs[hostname] = avd_structured_value

        if not all_hostvars or not structured_configs:
            return f"# {fabric_name}\n\nNo AVD data available for this fabric."

        # Generate AVD facts
        hostvars_copy = copy.deepcopy(all_hostvars)
        avd_facts = pyavd.get_avd_facts(hostvars_copy)

        # Generate fabric documentation
        fabric_doc = pyavd.get_fabric_documentation(
            avd_facts,
            structured_configs,
            fabric_name,
        )

        return fabric_doc.content
