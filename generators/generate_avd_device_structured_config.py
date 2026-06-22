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

from solution_arista_avd.protocols import AvdArtifact, AvdStructuredConfigFile

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

                avd_artifact = getattr(device, "avd_artifact", None)
                if avd_artifact and avd_artifact.node:
                    hostvar_file = getattr(avd_artifact.node, "hostvar_file", None)
                    if hostvar_file and hostvar_file.node:
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

                    avd_artifact = getattr(device, "avd_artifact", None)
                    if avd_artifact and avd_artifact.node:
                        hostvar_file = getattr(avd_artifact.node, "hostvar_file", None)
                        if hostvar_file and hostvar_file.node:
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
                if not artifact.hostvar_file.id:
                    self.logger.warning(f"No hostvar file for {hostname}, skipping")
                    continue
                await artifact.hostvar_file.fetch()
                hostvar_file = artifact.hostvar_file.peer
                if not hostvar_file:
                    self.logger.warning(f"Hostvar file peer not found for {hostname}, skipping")
                    continue
                content = await hostvar_file.download_file()
                result[hostname] = json.loads(content)
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"Failed to fetch hostvars for {hostname}: {e}")

        return result

    async def generate(self, data: dict) -> None:
        """Generate AVD inputs and structured config for all devices."""
        data: GenerateAvdInputsQuery = GenerateAvdInputsQuery(**data)
        # Extract all devices from nested fabric structure
        devices = self._extract_devices_from_fabric(data)

        self.logger.info(f"Found {len(devices)} devices in fabric")
        device_mapping: dict[str, str] = {}
        for d in devices:
            device_mapping[d["hostname"]] = d["id"]
            self.logger.info("  %s: %s", d["hostname"], "has hostvar" if d["has_hostvar"] else "no artifact")

        # Check all devices have hostvars before proceeding
        devices_without_hostvars = [d["hostname"] for d in devices if not d["has_hostvar"]]
        if devices_without_hostvars:
            self.logger.warning(
                f"Aborting: {len(devices_without_hostvars)} devices missing hostvars: "
                f"{', '.join(devices_without_hostvars[:5])}{'...' if len(devices_without_hostvars) > 5 else ''}"
            )
            return

        # Fetch hostvars from object storage
        hostvars = await self._fetch_hostvars_from_storage(devices)

        validation_errors: list[str] = []
        for hostname, inputs in hostvars.items():
            validated = validate_inputs(inputs)
            if validated.validation_result.violations:
                for violation in validated.validation_result.violations:
                    msg = getattr(violation, "message", str(violation))
                    path = getattr(violation, "path", "")
                    validation_errors.append(f"{hostname}: {msg} (path: {path})")
                self.logger.warning(
                    f"Validation warnings for {hostname}: {len(validated.validation_result.violations)} issues"
                )
            else:
                self.logger.info(f"{hostname} validated successfully")

        if validation_errors:
            for err in validation_errors:
                self.logger.error(f"Validation error: {err}")
            self.logger.error(
                f"pyAVD validation failed for {len(validation_errors)} inputs — aborting structured config generation"
            )
            return

        self.logger.info("Generating AVD facts for all devices...")
        try:
            avd_facts = get_avd_facts(hostvars)
            self.logger.info(f"Generated facts for {len(avd_facts)} devices")
        except (ValueError, KeyError, TypeError):
            self.logger.exception("AVD facts generation failed")
            return

        import hashlib

        success_count = 0
        skipped_count = 0
        failed_devices: list[str] = []
        for hostname, inputs in hostvars.items():
            try:
                structured_config = get_device_structured_config(hostname=hostname, inputs=inputs, avd_facts=avd_facts)
                structured_config_dict = (
                    structured_config._as_dict()  # noqa: SLF001 — pyAVD model exposes its data only via _as_dict()
                    if hasattr(structured_config, "_as_dict")
                    else structured_config
                )

                new_content = json.dumps(structured_config_dict, indent=2).encode()
                new_checksum = hashlib.sha256(new_content).hexdigest()

                avd_artifact = await self.client.get(AvdArtifact, name__value=hostname)

                # Get existing structured config file if it exists
                existing_file = None
                existing_checksum = None
                if avd_artifact.structured_config_file.id:
                    try:
                        await avd_artifact.structured_config_file.fetch()
                        existing_file = avd_artifact.structured_config_file.peer
                        if existing_file:
                            existing_content = await existing_file.download_file()
                            existing_checksum = hashlib.sha256(existing_content).hexdigest()
                    except Exception as exc:  # noqa: BLE001 - treat any fetch/download failure as "no existing file"
                        self.logger.warning(
                            "Could not read existing structured config for %s, forcing re-upload: %s",
                            hostname,
                            exc,
                        )
                        existing_file = None

                # Always upload and save to ensure the file exists on this branch
                if existing_file:
                    existing_file.upload_from_bytes(content=new_content, name=f"{hostname}-structured-config.json")
                    await existing_file.save(allow_upsert=True)
                else:
                    sc_file = await self.client.create(
                        AvdStructuredConfigFile,
                        artifact=avd_artifact,
                        member_of_groups=["avd_structured_configs"],
                    )
                    sc_file.upload_from_bytes(content=new_content, name=f"{hostname}-structured-config.json")
                    await sc_file.save(allow_upsert=True)

                if existing_checksum == new_checksum:
                    skipped_count += 1
                else:
                    success_count += 1
            except (ValueError, KeyError, TypeError, AttributeError) as e:
                self.logger.exception(f"Structured config failed for {hostname}")
                failed_devices.append(f"{hostname}: {e}")

        self.logger.info(
            f"Structured config complete: {success_count} updated, {skipped_count} unchanged, {len(failed_devices)} failed"
        )
        for failure in failed_devices:
            self.logger.error(f"  Failed: {failure}")
