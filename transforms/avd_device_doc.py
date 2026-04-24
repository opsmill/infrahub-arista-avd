"""AVD Device Documentation Transform.

Generates device documentation from stored structured config.
"""

import json
from typing import Any

import pyavd
from infrahub_sdk.transforms import InfrahubTransform

from solution_arista_avd.protocols import AvdStructuredConfigFile

from .avd_device_config_query import AvdDeviceConfigQuery


class AvdDeviceDocTransform(InfrahubTransform):
    """Generates device documentation from stored structured config."""

    query = "avd_device_config"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform structured config to device documentation."""
        data: AvdDeviceConfigQuery = AvdDeviceConfigQuery(**data)
        device_edges = data.dcim_device.edges

        if not device_edges:
            return "# No device found"

        device = device_edges[0].node
        hostname = device.name.value

        artifact_node = device.avd_artifact.node if device.avd_artifact else None
        if not artifact_node or not artifact_node.structured_config_file.node:
            return f"# No structured config available for {hostname}"

        sc_file = await self.client.get(AvdStructuredConfigFile, id=artifact_node.structured_config_file.node.id)
        content = await sc_file.download_file()
        structured_config_value = json.loads(content)

        # Generate device documentation from stored structured config
        return pyavd.get_device_doc(structured_config_value)
