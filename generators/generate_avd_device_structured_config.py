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

from solution_arista_avd.generator import save_file_if_changed
from solution_arista_avd.protocols import AvdArtifact, AvdStructuredConfigFile

from .generate_avd_inputs_query import GenerateAvdInputsQuery

try:  # pyAVD's error base is not part of its public API; import defensively.
    from pyavd._errors import AristaAvdError  # noqa: PLC2701 - intentional private import, guarded above

    _AVD_ERROR_BASES: tuple[type[BaseException], ...] = (AristaAvdError,)
except ImportError:  # pragma: no cover - private module path may change across pyAVD versions
    _AVD_ERROR_BASES = ()

# Invalid per-fabric AVD inputs (e.g. a bad MLAG/EVPN payload on one device) surface
# as AristaAvdError subclasses or as the standard value/lookup/type errors. Catching
# this tuple isolates a broken fabric without also swallowing genuine programming
# bugs (AttributeError, NameError, ...), which should still propagate.
AVD_INPUT_ERRORS: tuple[type[BaseException], ...] = (*_AVD_ERROR_BASES, ValueError, KeyError, TypeError)


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
                artifact = await self.client.get(AvdArtifact, name__value=hostname, include=["hostvar_file"])
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

    @staticmethod
    def _missing_evpn_gateway_remote_peers(hostvars: dict[str, dict[str, Any]]) -> list[str]:
        """Return hostname-only EVPN Gateway peers missing from the aggregated AVD inputs."""
        missing: list[str] = []
        available_hostnames = set(hostvars)
        for hostname, inputs in hostvars.items():
            node_type = inputs.get("type")
            if not isinstance(node_type, str):
                continue
            node_type_inputs = inputs.get(node_type)
            if not isinstance(node_type_inputs, dict):
                continue
            nodes = node_type_inputs.get("nodes")
            if not isinstance(nodes, list):
                continue
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                evpn_gateway = node.get("evpn_gateway")
                if not isinstance(evpn_gateway, dict):
                    continue
                remote_peers = evpn_gateway.get("remote_peers") or []
                for peer in remote_peers:
                    if not isinstance(peer, dict) or peer.get("ip_address") or peer.get("bgp_as"):
                        continue
                    peer_hostname = peer.get("hostname")
                    if isinstance(peer_hostname, str) and peer_hostname not in available_hostnames:
                        missing.append(f"{hostname} -> {peer_hostname}")
        return sorted(missing)

    @staticmethod
    def _collect_input_validation_errors(hostvars: dict[str, dict[str, Any]]) -> list[str]:
        """Validate all pyAVD inputs and return formatted violation messages."""
        validation_errors: list[str] = []
        for hostname, inputs in hostvars.items():
            validated = validate_inputs(inputs)
            if not validated.validation_result.violations:
                AvdDeviceStructuredConfigGenerator.logger.info(f"{hostname} validated successfully")
                continue

            for violation in validated.validation_result.violations:
                msg = getattr(violation, "message", str(violation))
                path = getattr(violation, "path", "")
                validation_errors.append(f"{hostname}: {msg} (path: {path})")
            AvdDeviceStructuredConfigGenerator.logger.warning(
                f"Validation warnings for {hostname}: {len(validated.validation_result.violations)} issues"
            )
        return validation_errors

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
        missing_remote_peers = self._missing_evpn_gateway_remote_peers(hostvars)
        if missing_remote_peers:
            self.logger.error(
                "Hostname-only EVPN Gateway remote peer hostvars are missing; generate hostvars for these peers "
                "before structured config generation: %s",
                ", ".join(missing_remote_peers),
            )
            return

        validation_errors = self._collect_input_validation_errors(hostvars)
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
        except AVD_INPUT_ERRORS:
            # Invalid inputs for this fabric (e.g. one device with a bad MLAG/EVPN
            # payload) fail this fabric alone instead of propagating and aborting
            # every other fabric's structured-config run. Genuine bugs still raise.
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

                avd_artifact = await self.client.get(
                    AvdArtifact, name__value=hostname, include=["structured_config_file"]
                )

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

                uploaded = await save_file_if_changed(
                    existing_file=existing_file,
                    existing_checksum=existing_checksum,
                    new_checksum=new_checksum,
                    new_content=new_content,
                    filename=f"{hostname}-structured-config.json",
                    create_file=lambda avd_artifact=avd_artifact: self.client.create(
                        AvdStructuredConfigFile,
                        artifact=avd_artifact,
                        member_of_groups=["avd_structured_configs"],
                    ),
                )

                if not uploaded:
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
