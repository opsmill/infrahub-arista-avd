"""AVD Generator.

This generator builds pyAVD hostvars from Infrahub data and generates
structured configurations for all devices in a fabric.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator
from pyavd import get_avd_facts, get_device_structured_config, validate_inputs

from solution_ai_dc.protocols import AvdArtifact, AvdStructuredConfigFile

from .generate_avd_inputs_query import GenerateAvdInputsQuery


class AvdDeviceStructuredConfigGenerator(InfrahubGenerator):
    """Builds AVD inputs and structured config for all devices in a fabric."""

    logger = logging.getLogger("infrahub.tasks")

    def _extract_devices_from_fabric(self, data: GenerateAvdInputsQuery) -> list[dict[str, Any]]:
        """Extract all devices from the nested fabric structure.

        Traverses: NetworkFabric -> children (pods) -> devices + racks -> devices

        Returns:
            List of dicts with hostname, id, and has_hostvar flag
        """
        devices: dict[str, dict[str, Any]] = {}  # Use dict to dedupe by hostname

        fabric_edges = data.network_fabric.edges
        if not fabric_edges:
            return []

        fabric_node = fabric_edges[0].node

        # Traverse children (pods)
        children_edges = fabric_node.children.edges
        for child_edge in children_edges:
            child_node = child_edge.node

            # Get devices directly under pod
            for device_edge in child_node.devices.edges:
                device = device_edge.node
                hostname = device.name.value
                has_hostvar = False

                avd_artifact = device.avd_artifact.node
                if avd_artifact and avd_artifact.hostvar_file.node:
                    has_hostvar = True

                devices[hostname] = {
                    "id": device.id,
                    "hostname": hostname,
                    "has_hostvar": has_hostvar,
                }

            # Get devices from racks
            for rack_edge in child_node.racks.edges:
                rack_node = rack_edge.node
                for device_edge in rack_node.devices.edges:
                    device = device_edge.node
                    hostname = device.name.value
                    has_hostvar = False

                    avd_artifact = device.avd_artifact.node
                    if avd_artifact and avd_artifact.hostvar_file.node:
                        has_hostvar = True

                    devices[hostname] = {
                        "id": device.id,
                        "hostname": hostname,
                        "has_hostvar": has_hostvar,
                    }

        return list(devices.values())

    async def _fetch_hostvars_from_storage(self, devices: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Fetch hostvar content from CoreFileObject for each device.

        Args:
            devices: List of dicts with hostname and has_hostvar flag

        Returns:
            Dict mapping hostname to hostvars content (only devices with artifacts)
        """
        result: dict[str, dict[str, Any]] = {}

        for device in devices:
            hostname = device["hostname"]

            if not device.get("has_hostvar"):
                continue

            try:
                artifact = await self.client.get(AvdArtifact, name__value=hostname)
                await artifact.hostvar_file.fetch()
                hostvar_file = artifact.hostvar_file.peer
                content = await hostvar_file.download_file()
                result[hostname] = json.loads(content)
            except Exception as e:
                self.logger.warning(f"Failed to fetch hostvars for {hostname}: {e}")

        return result

    async def generate(self, data: dict) -> None:
        """Generate AVD inputs and structured config for all devices."""
        data: GenerateAvdInputsQuery = GenerateAvdInputsQuery(**data)
        # Extract all devices from nested fabric structure
        devices = self._extract_devices_from_fabric(data)

        self.logger.info(f"Found {len(devices)} devices in fabric")
        print(f"\nFound {len(devices)} devices:")
        device_mapping: dict[str, str] = {}
        for d in devices:
            status = "✓" if d["has_hostvar"] else "✗"
            device_mapping[d["hostname"]] = d["id"]
            print(f"  {status} {d['hostname']}: {'has hostvar' if d['has_hostvar'] else 'no artifact'}")

        # Fetch hostvars from object storage
        hostvars = await self._fetch_hostvars_from_storage(devices)

        print("\nHostvars:")
        print(json.dumps(hostvars, indent=2))

        for hostname, inputs in hostvars.items():
            validation_result = validate_inputs(inputs)
            if validation_result.failed:
                print(f"  ❌ Validation failed for {hostname}:")
                for error in validation_result.validation_errors:
                    print(f"     - {error}")
                return
            print("  ✓ All inputs validated successfully")

        print("\nStep 3: Generating AVD facts for all devices...")
        try:
            avd_facts = get_avd_facts(hostvars)
            print(f"  ✓ Generated facts for {len(avd_facts)} devices")
        except Exception as e:
            print(f"  ❌ Failed to generate AVD facts: {e}")
            return

        structured_configs = {}
        for hostname, inputs in hostvars.items():
            print(f"\n  Generating structured config for {hostname}...")
            try:
                structured_config = get_device_structured_config(hostname=hostname, inputs=inputs, avd_facts=avd_facts)

                avd_artifact = await self.client.get(AvdArtifact, name__value=hostname)

                sc_file = await self.client.create(
                    AvdStructuredConfigFile,
                    artifact=avd_artifact,
                    member_of_groups=["avd_structured_configs"],
                )
                sc_file.upload_from_bytes(
                    content=json.dumps(structured_config).encode(),
                    name=f"{hostname}-structured-config.json",
                )
                await sc_file.save(allow_upsert=True)
                print(f"    ✓ Generated structured config with {len(structured_config)} top-level keys")
            except Exception as e:
                print(f"    ❌ Failed: {e}")
                continue
