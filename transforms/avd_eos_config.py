"""AVD EOS Config Transform.

Generates EOS CLI configuration from stored structured config.
"""

from typing import Any

import pyavd
from infrahub_sdk.transforms import InfrahubTransform


class AvdEosConfigTransform(InfrahubTransform):
    """Generates EOS CLI config from stored structured config."""

    query = "avd_device_config"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform structured config to EOS CLI configuration."""
        device_edges = data.get("NetworkDevice", {}).get("edges", [])

        if not device_edges:
            return "! No device found"

        device = device_edges[0]["node"]
        hostname = device["hostname"]["value"]
        structured_config = device.get("avd_structured_config", {})
        structured_config_value = structured_config.get("value") if structured_config else None

        if not structured_config_value:
            return f"! No structured config available for {hostname}"

        # Ensure hostname is set in structured config
        structured_config_value["hostname"] = hostname

        # Generate EOS CLI from stored structured config
        return pyavd.get_device_config(structured_config_value)
