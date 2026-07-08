"""AVD ANTA Catalog Transform.

Generates a per-device ANTA test catalog (YAML) from the stored AVD structured
config. Gated by the fabric-level ``anta_enabled`` flag: when a device's fabric
has ANTA disabled the transform returns a short marker instead of a catalog.

Unlike EOS config generation, ANTA catalog generation needs fabric-wide data, so
every sibling device's structured config in the same fabric is gathered to build
a single ``AVDFabricData`` instance.
"""

import json
from typing import Any

from infrahub_sdk.transforms import InfrahubTransform
from pyavd import get_device_test_catalog, validate_structured_config
from pyavd.api.anta import AVDFabricData

from solution_arista_avd.protocols import AvdStructuredConfigFile

from .avd_anta_catalog_query import AvdAntaCatalogQuery, DeviceNode, ParentNode


class AvdAntaCatalogTransform(InfrahubTransform):
    """Render an ANTA test catalog for a single device."""

    query = "avd_anta_catalog"

    async def transform(self, data: dict[str, Any]) -> str:
        """Transform stored structured config into an ANTA YAML catalog."""
        parsed = AvdAntaCatalogQuery(**data)

        target = parsed.target.edges[0].node if parsed.target.edges else None
        hostname = target.name.value if target and target.name else None
        if not target or not hostname:
            return "# ANTA catalog: device not found"

        fabric = self._fabric_of(target)
        if fabric is None:
            return f"# ANTA catalog: no fabric for {hostname}"
        fabric_name = fabric.name.value if fabric.name else fabric.id

        if not (fabric.anta_enabled and fabric.anta_enabled.value):
            return f"# ANTA disabled for fabric {fabric_name}"

        configs = await self._fabric_structured_configs(parsed, fabric.id)
        target_sc = configs.get(hostname)
        if target_sc is None:
            return f"# No structured config for {hostname}"

        fabric_data = AVDFabricData.from_structured_configs(configs)
        catalog = get_device_test_catalog(hostname, target_sc, fabric_data)
        return catalog.dump().yaml()

    @staticmethod
    def _fabric_of(device: DeviceNode) -> ParentNode | None:
        """Return the device's fabric node (``pod.parent``), or None."""
        pod = device.pod.node if device.pod else None
        return pod.parent.node if pod and pod.parent else None

    async def _fabric_structured_configs(
        self, parsed: AvdAntaCatalogQuery, fabric_id: str
    ) -> dict[str, dict[str, Any]]:
        """Download validated structured config for every device in the fabric."""
        configs: dict[str, dict[str, Any]] = {}
        for edge in parsed.dcim_device.edges:
            device = edge.node
            if not device or not device.name or not device.name.value:
                continue
            fabric = self._fabric_of(device)
            if fabric is None or fabric.id != fabric_id:
                continue
            sc = await self._download_structured_config(device)
            if sc is not None:
                configs[device.name.value] = sc
        return configs

    async def _download_structured_config(self, device: DeviceNode) -> dict[str, Any] | None:
        """Download and validate a device's structured config, or None if absent/invalid."""
        artifact = device.avd_artifact.node if device.avd_artifact else None
        sc_node = artifact.structured_config_file.node if artifact else None
        if not sc_node:
            return None
        sc_file = await self.client.get(AvdStructuredConfigFile, id=sc_node.id)
        content = await sc_file.download_file()
        return validate_structured_config(json.loads(content)).validated_data
