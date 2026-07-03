"""CloudVision Configuration Validation Check.

Deploys EOS configurations to a CloudVision workspace during proposed change
validation. Creates/updates configlets in Static Configuration Studio, builds
the workspace, and reports build results back to Infrahub.
"""

from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import pyavd
from infrahub_sdk.checks import InfrahubCheck
from pyavd._cv.api.arista.workspace.v1 import WorkspaceState
from pyavd._cv.client import CVClient
from pyavd._cv.client.exceptions import CVClientException, CVResourceNotFound
from pyavd._cv.workflows.deploy_configs_to_cv import deploy_configs_to_cv
from pyavd._cv.workflows.finalize_workspace_on_cv import finalize_workspace_on_cv
from pyavd._cv.workflows.models import CVDevice, CVEosConfig, CVWorkspace, DeployToCvResult
from pyavd._cv.workflows.verify_devices_on_cv import verify_devices_on_cv

from solution_arista_avd.protocols import AvdStructuredConfigFile

from .cv_config_check_query import CVConfigCheckDcimDeviceNode, CVConfigCheckQuery
from .cv_helpers import get_cloudvision_config, get_workspace_id, get_workspace_name, rollback_workspace

LOGGER = logging.getLogger(__name__)


class CVConfigValidationCheck(InfrahubCheck):
    """Validates EOS configurations by deploying them to CloudVision."""

    query = "cv_config_check"
    timeout = 600

    async def validate(self, data: dict[str, Any]) -> None:
        parsed = CVConfigCheckQuery(**data)

        fabric_edges = parsed.network_fabric.edges
        if not fabric_edges or not fabric_edges[0].node:
            self.log_info(message="No fabric found")
            return

        fabric_node = fabric_edges[0].node
        fabric_id = fabric_node.id
        fabric_name = fabric_node.name.value if fabric_node.name else "unknown"

        cv_config = get_cloudvision_config()
        if cv_config is None:
            self.log_error(
                message="CloudVision credentials not configured. Set CLOUDVISION_SERVERS and CLOUDVISION_TOKEN environment variables."
            )
            return

        fabric_devices = self._filter_devices_by_fabric(parsed, fabric_id)
        if not fabric_devices:
            self.log_info(message=f"No devices with EOS configs found for fabric {fabric_name}")
            return

        proposed_change_id = getattr(self.initializer, "proposed_change_id", "") or "local"
        ws_id = get_workspace_id(proposed_change_id, fabric_name)
        ws_name = get_workspace_name(proposed_change_id, fabric_name)

        with tempfile.TemporaryDirectory(prefix="infrahub_cv_") as tmp_dir:
            eos_configs = await self._collect_eos_configs(fabric_devices, tmp_dir)
            if not eos_configs:
                self.log_info(message=f"No EOS configurations available for fabric {fabric_name}")
                return

            await self._deploy_and_build(cv_config, ws_id, ws_name, eos_configs, fabric_name, fabric_id)

    def _filter_devices_by_fabric(
        self, parsed: CVConfigCheckQuery, fabric_id: str
    ) -> list[CVConfigCheckDcimDeviceNode]:
        """Filter devices that belong to the target fabric and have structured configs."""
        devices = []
        for edge in parsed.dcim_device.edges:
            device = edge.node
            if not device:
                continue
            if not device.pod or not device.pod.node:
                continue
            pod_node = device.pod.node
            if not pod_node.parent or not pod_node.parent.node:
                continue
            if pod_node.parent.node.id != fabric_id:
                continue
            if not device.avd_artifact or not device.avd_artifact.node:
                continue
            if not device.avd_artifact.node.structured_config_file.node:
                continue
            devices.append(device)
        return devices

    async def _collect_eos_configs(self, devices: list[CVConfigCheckDcimDeviceNode], tmp_dir: str) -> list[CVEosConfig]:
        """Download structured configs and generate EOS CLI configs."""
        eos_configs: list[CVEosConfig] = []
        for device in devices:
            hostname = device.name.value if device.name else "unknown"
            serial = device.serial.value if device.serial else None
            sc_file_id = device.avd_artifact.node.structured_config_file.node.id

            try:
                sc_file = await self.client.get(AvdStructuredConfigFile, id=sc_file_id)
                content = await sc_file.download_file()
                structured_config = json.loads(content)
            except (json.JSONDecodeError, OSError, ValueError, AttributeError) as exc:
                self.log_info(message=f"WARNING: Could not fetch structured config for {hostname}: {exc}")
                continue

            eos_config_str = pyavd.get_device_config(structured_config)

            config_path = Path(tmp_dir) / f"{hostname}.cfg"
            config_path.write_text(eos_config_str)

            cv_device = CVDevice(hostname=hostname, serial_number=serial)
            eos_configs.append(
                CVEosConfig(file=str(config_path), device=cv_device, configlet_name=f"Infrahub_{hostname}")
            )

        return eos_configs

    async def _deploy_and_build(
        self,
        cv_config: Any,
        ws_id: str,
        ws_name: str,
        eos_configs: list[CVEosConfig],
        fabric_name: str,
        fabric_id: str,
    ) -> None:
        """Connect to CloudVision, deploy configs, and build the workspace."""
        workspace = CVWorkspace(name=ws_name, id=ws_id, requested_state="built")
        result = DeployToCvResult(workspace=workspace)
        devices = [config.device for config in eos_configs]

        try:
            async with CVClient(
                servers=cv_config.servers,
                token=cv_config.token,
                username=cv_config.username,
                password=cv_config.password,
                verify_certs=cv_config.verify_certs,
                proxy_host=cv_config.proxy_host,
                proxy_port=cv_config.proxy_port,
                proxy_username=cv_config.proxy_username,
                proxy_password=cv_config.proxy_password,
            ) as cv_client:
                await self._ensure_workspace_pending(cv_client, workspace)

                await verify_devices_on_cv(
                    devices=devices,
                    workspace_id=workspace.id,
                    skip_missing_devices=True,
                    warnings=result.warnings,
                    cv_client=cv_client,
                )

                await deploy_configs_to_cv(configs=eos_configs, result=result, cv_client=cv_client)

                try:
                    await finalize_workspace_on_cv(
                        workspace=workspace, cv_client=cv_client, devices=devices, warnings=result.warnings
                    )
                except CVClientException as build_exc:
                    result.failed = True
                    result.errors.append(build_exc)

        except CVClientException as exc:
            self.log_error(message=f"CloudVision connection failed: {exc}")
            return

        await self._track_workspace(ws_id, ws_name, fabric_id, "built" if not result.failed else "abandoned")
        self._report_results(result, cv_config, fabric_name)

    async def _ensure_workspace_pending(self, cv_client: CVClient, workspace: CVWorkspace) -> None:
        """Create the workspace or rollback to pending if already built."""
        try:
            existing = await cv_client.get_workspace(workspace_id=workspace.id)
            if existing.state in (WorkspaceState.PENDING, WorkspaceState.ROLLED_BACK):
                workspace.state = "pending"
            else:
                await rollback_workspace(cv_client, workspace.id)
                await cv_client.wait_for_workspace_state(workspace_id=workspace.id, state="pending")
                workspace.state = "pending"
        except CVResourceNotFound:
            await cv_client.create_workspace(
                workspace_id=workspace.id,
                display_name=workspace.name,
                description="Infrahub proposed change validation",
            )
            await cv_client.wait_for_workspace_state(workspace_id=workspace.id, state="pending")
            workspace.state = "pending"

    async def _track_workspace(self, ws_id: str, ws_name: str, fabric_id: str, status: str) -> None:
        """Create or update the Cv.Workspace tracking node in Infrahub."""
        try:
            from infrahub_sdk import NodeNotFoundError

            try:
                ws_node = await self.client.get(kind="CvWorkspace", workspace_id__value=ws_id)
                ws_node.status.value = status
                await ws_node.save()
            except NodeNotFoundError:
                ws_node = await self.client.create(
                    kind="CvWorkspace",
                    data={
                        "name": ws_name,
                        "workspace_id": ws_id,
                        "status": status,
                        "fabric": fabric_id,
                    },
                )
                await ws_node.save()
        except (AttributeError, ValueError, RuntimeError):
            LOGGER.exception("Failed to track workspace in Infrahub")

    def _report_results(self, result: DeployToCvResult, cv_config: Any, fabric_name: str) -> None:
        """Report deployment results via check log methods."""
        server = cv_config.servers[0] if isinstance(cv_config.servers, list) else cv_config.servers
        ws_url = f"https://{server}/cv/provisioning/workspaces?ws={result.workspace.id}"

        if result.failed:
            error_msgs = "; ".join(str(e) for e in result.errors)
            self.log_error(
                message=f"CloudVision workspace build failed for fabric {fabric_name}: {error_msgs}. "
                f"See workspace: {ws_url}"
            )
            return

        self.log_info(message=f"CloudVision workspace built successfully for fabric {fabric_name}: {ws_url}")

        deployed_count = len(result.deployed_configs)
        skipped_count = len(result.skipped_configs)
        self.log_info(message=f"Deployed {deployed_count} device configs, skipped {skipped_count}")

        if result.deployed_configs:
            device_names = ", ".join(c.device.hostname for c in result.deployed_configs)
            self.log_info(message=f"Devices with configs deployed: {device_names}")

        if result.skipped_configs:
            skipped_names = ", ".join(c.device.hostname for c in result.skipped_configs)
            self.log_info(message=f"WARNING: Devices skipped (not found on CloudVision): {skipped_names}")

        for warning in result.warnings:
            self.log_info(message=f"WARNING: {warning}")
