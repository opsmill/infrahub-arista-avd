"""AVD Fabric Documentation Transform.

Generates fabric documentation from stored structured configs.
"""

import copy
import json
from typing import Any

import pyavd
from infrahub_sdk.transforms import InfrahubTransform

from .avd_fabric_devices_query import AvdFabricDevicesQuery


class AvdFabricDocTransform(InfrahubTransform):
    """Generates fabric documentation from stored structured configs."""

    query = "avd_fabric_devices"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform fabric data to documentation."""
        data: AvdFabricDevicesQuery = AvdFabricDevicesQuery(**data)

        # Get fabric info
        fabric_edges = data.network_fabric.edges
        if not fabric_edges:
            return "# No fabric found"

        fabric_node = fabric_edges[0].node
        fabric_name = fabric_node.name.value
        fabric_id = fabric_node.id

        # Get all devices and filter by fabric
        device_edges = data.dcim_device.edges
        all_hostvars: dict[str, dict[str, Any]] = {}
        structured_configs: dict[str, dict[str, Any]] = {}

        for edge in device_edges:
            device = edge.node
            # Check if device belongs to this fabric
            if not device.pod or not device.pod.node:
                continue
            pod_node = device.pod.node
            if not pod_node.parent or not pod_node.parent.node:
                continue
            if pod_node.parent.node.id != fabric_id:
                continue

            hostname = device.name.value

            # Fetch AVD data from object store via avd_artifact relationship
            if not device.avd_artifact or not device.avd_artifact.node:
                continue

            artifact_node = device.avd_artifact.node

            hostvar_id = artifact_node.hostvar_identifier.value if artifact_node.hostvar_identifier else None
            structured_config_id = (
                artifact_node.structured_config_identifier.value if artifact_node.structured_config_identifier else None
            )

            if hostvar_id:
                hostvar_content = await self.client.object_store.get(identifier=hostvar_id)
                all_hostvars[hostname] = json.loads(hostvar_content)

            if structured_config_id:
                sc_content = await self.client.object_store.get(identifier=structured_config_id)
                structured_configs[hostname] = json.loads(sc_content)

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

        return fabric_doc.fabric_documentation
