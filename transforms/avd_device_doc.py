"""AVD Device Documentation Transform.

Generates device documentation from stored structured config.
"""

import json
from typing import Any

import pyavd
from infrahub_sdk.transforms import InfrahubTransform

from .avd_device_config_query import AvdDeviceConfigQuery


class AvdDeviceDocTransform(InfrahubTransform):
    """Generates device documentation from stored structured config."""

    query = "avd_device_config"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform structured config to device documentation."""
        data: AvdDeviceConfigQuery = AvdDeviceConfigQuery(**data)
        device_edges = data.network_device.edges

        if not device_edges:
            return "# No device found"

        device = device_edges[0].node
        hostname = device.hostname.value
        structured_config_peer = device.avd_artifact.node.structured_config_identifier
        structured_config_id = structured_config_peer.value if structured_config_peer else None

        structured_config = (
            await self.client.object_store.get(identifier=structured_config_id) if structured_config_id else None
        )
        if not structured_config:
            return f"# No structured config available for {hostname}"

        structured_config_value = json.loads(structured_config)

        # Generate device documentation from stored structured config
        return pyavd.get_device_doc(structured_config_value)
