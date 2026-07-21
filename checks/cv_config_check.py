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
from typing import Any, cast

import pyavd
from infrahub_sdk.checks import InfrahubCheck
from infrahub_sdk.exceptions import NodeNotFoundError
from pyavd._cv.api.arista.workspace.v1 import WorkspaceState
from pyavd._cv.client import CVClient
from pyavd._cv.client.exceptions import CVClientException, CVResourceNotFound
from pyavd._cv.workflows.deploy_configs_to_cv import deploy_configs_to_cv
from pyavd._cv.workflows.finalize_workspace_on_cv import finalize_workspace_on_cv
from pyavd._cv.workflows.models import (
    AvdDevice,
    AvdWorkspace,
    CVDevice,
    CVEosConfig,
    CVWorkspace,
    DeployToCvResult,
)
from pyavd._cv.workflows.verify_devices_on_cv import verify_devices_in_cloudvision_inventory, verify_devices_on_cv

from solution_arista_avd.protocols import AvdStructuredConfigFile

from .cv_config_check_query import CVConfigCheckQuery
from .cv_config_check_query import CVConfigCheckQueryDcimDeviceEdgesNode as CVConfigCheckDcimDeviceNode
from .cv_helpers import (
    DEFAULT_WORKSPACE_DESCRIPTION,
    get_cloudvision_config,
    get_proposed_change_context,
    get_workspace_description,
    get_workspace_id,
    get_workspace_name,
    rollback_workspace,
)

LOGGER = logging.getLogger(__name__)


class CVConfigValidationCheck(InfrahubCheck):
    """Validates EOS configurations by deploying them to CloudVision."""

    query = "cv_config_check"
    timeout = 600

    async def validate(self, data: dict[str, Any]) -> None:  # type: ignore[override]
        parsed = CVConfigCheckQuery(**data)

        fabric_edges = parsed.network_fabric.edges
        if not fabric_edges or not fabric_edges[0].node:
            self.log_info(message="No fabric found")
            return

        fabric_node = fabric_edges[0].node
        fabric_id = fabric_node.id
        fabric_name = fabric_node.name.value if fabric_node.name and fabric_node.name.value else "unknown"
        if not (fabric_node.cloudvision_managed and fabric_node.cloudvision_managed.value):
            self.log_info(message=f"CloudVision validation disabled for fabric {fabric_name}; skipping")
            return

        cv_config = get_cloudvision_config()
        if cv_config is None:
            self.log_error(
                message=(
                    "CloudVision credentials not configured. Set CLOUDVISION_SERVERS plus CLOUDVISION_TOKEN, "
                    "or CLOUDVISION_SERVERS plus CLOUDVISION_USERNAME and CLOUDVISION_PASSWORD."
                )
            )
            return

        fabric_devices = self._devices_in_fabric(parsed, fabric_id)
        missing_serials = [self._device_name(device) for device in fabric_devices if not self._device_serial(device)]
        if missing_serials:
            self.log_error(
                message=f"CloudVision-managed devices in fabric {fabric_name} are missing serial numbers: "
                f"{', '.join(missing_serials)}"
            )
            return

        proposed_change = await get_proposed_change_context(self.client, self.initializer, self.branch_name)
        ws_id = get_workspace_id(proposed_change.id, fabric_name)
        ws_name = get_workspace_name(proposed_change.name, fabric_name)
        proposed_change_description = (
            None if proposed_change.description == DEFAULT_WORKSPACE_DESCRIPTION else proposed_change.description
        )
        ws_description = get_workspace_description(proposed_change_description, proposed_change.id, fabric_name)

        serial_devices = [device for device in fabric_devices if self._device_serial(device)]
        try:
            inventory_devices = await self._verify_inventory(
                cv_config=cv_config,
                devices=serial_devices,
            )
        except CVClientException as exc:
            self.log_error(
                message=f"CloudVision connection or inventory validation failed for fabric {fabric_name}: {exc}"
            )
            return

        if not fabric_devices:
            self.log_info(
                message=f"No devices found for CloudVision-managed fabric {fabric_name}; skipping workspace validation"
            )
            return

        deploy_devices = [device for device in fabric_devices if self._structured_config_file_id(device)]
        if not deploy_devices:
            self.log_info(message=f"No generated EOS configurations available for fabric {fabric_name}")
            return

        with tempfile.TemporaryDirectory(prefix="infrahub_cv_") as tmp_dir:
            eos_configs = await self._collect_eos_configs(deploy_devices, tmp_dir)
            if self.errors:
                return

            await self._deploy_and_build(
                cv_config,
                ws_id,
                ws_name,
                ws_description,
                proposed_change.id,
                eos_configs,
                fabric_name,
                fabric_id,
                inventory_devices=inventory_devices,
            )

    def _devices_in_fabric(self, parsed: CVConfigCheckQuery, fabric_id: str) -> list[CVConfigCheckDcimDeviceNode]:
        """Filter devices confirmed to belong to the target fabric."""
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
            devices.append(device)
        return devices

    def _filter_devices_by_fabric(
        self, parsed: CVConfigCheckQuery, fabric_id: str
    ) -> list[CVConfigCheckDcimDeviceNode]:
        """Filter target-fabric devices that have structured configs."""
        return [
            device for device in self._devices_in_fabric(parsed, fabric_id) if self._structured_config_file_id(device)
        ]

    @staticmethod
    def _device_name(device: CVConfigCheckDcimDeviceNode) -> str:
        return device.name.value if device.name and device.name.value else "unknown"

    @staticmethod
    def _device_serial(device: CVConfigCheckDcimDeviceNode) -> str | None:
        return device.serial.value if device.serial and device.serial.value else None

    @staticmethod
    def _structured_config_file_id(device: CVConfigCheckDcimDeviceNode) -> str | None:
        avd_artifact = device.avd_artifact
        if (
            not avd_artifact
            or not avd_artifact.node
            or not avd_artifact.node.structured_config_file
            or not avd_artifact.node.structured_config_file.node
        ):
            return None
        return avd_artifact.node.structured_config_file.node.id

    @classmethod
    def _cv_device(cls, device: CVConfigCheckDcimDeviceNode) -> CVDevice:
        return CVDevice(
            avd_device=AvdDevice(hostname=cls._device_name(device)),
            serial_number=cls._device_serial(device),
        )

    async def _verify_inventory(self, cv_config: Any, devices: list[CVConfigCheckDcimDeviceNode]) -> list[CVDevice]:
        """Verify every serial-numbered managed-fabric device exists in CloudVision inventory."""
        cv_devices = [self._cv_device(device) for device in devices]
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
            return await verify_devices_in_cloudvision_inventory(
                devices=cv_devices,
                skip_missing_devices=False,
                warnings=[],
                cv_client=cv_client,
            )

    async def _collect_eos_configs(self, devices: list[CVConfigCheckDcimDeviceNode], tmp_dir: str) -> list[CVEosConfig]:
        """Download structured configs and generate EOS CLI configs."""
        eos_configs: list[CVEosConfig] = []
        for device in devices:
            hostname = self._device_name(device)
            serial = self._device_serial(device)
            avd_artifact = device.avd_artifact
            if (
                not avd_artifact
                or not avd_artifact.node
                or not avd_artifact.node.structured_config_file
                or not avd_artifact.node.structured_config_file.node
            ):
                self.log_info(message=f"WARNING: Structured config relationship missing for {hostname}")
                continue
            sc_file_id = self._structured_config_file_id(device)
            if not sc_file_id:
                continue

            try:
                sc_file = await self.client.get(AvdStructuredConfigFile, id=sc_file_id, branch=self.branch_name)
                content = await sc_file.download_file()
                structured_config = json.loads(content)
                eos_config_str = pyavd.get_device_config(structured_config)
            except (NodeNotFoundError, json.JSONDecodeError, OSError, ValueError, AttributeError, TypeError) as exc:
                self.log_error(message=f"Could not render structured config for device {hostname}: {exc}")
                continue

            config_path = Path(tmp_dir) / f"{hostname}.cfg"
            config_path.write_text(eos_config_str)

            cv_device = CVDevice(avd_device=AvdDevice(hostname=hostname), serial_number=serial)
            eos_configs.append(
                CVEosConfig(file=str(config_path), device=cv_device, configlet_name=f"Infrahub_{hostname}")
            )

        return eos_configs

    async def _deploy_and_build(
        self,
        cv_config: Any,
        ws_id: str,
        ws_name: str,
        ws_description: str,
        proposed_change_id: str,
        eos_configs: list[CVEosConfig],
        fabric_name: str,
        fabric_id: str,
        inventory_devices: list[CVDevice],
    ) -> None:
        """Connect to CloudVision, deploy configs, and build the workspace."""
        workspace = CVWorkspace(
            avd_workspace=AvdWorkspace(name=ws_name, description=ws_description, id=ws_id, requested_state="built")
        )
        result = DeployToCvResult(workspace=workspace)
        devices = [config.device for config in eos_configs]
        inactive_devices = self._inactive_cv_device_names(inventory_devices)

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
                await self._ensure_workspace_pending(cv_client, workspace, ws_description)

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

        await self._track_workspace(
            ws_id,
            ws_name,
            fabric_id,
            proposed_change_id,
            "built" if not result.failed and not inactive_devices else "abandoned",
        )
        self._report_results(result, cv_config, fabric_name, len(inventory_devices))
        if inactive_devices:
            self.log_error(
                message=(
                    f"CloudVision devices inactive for fabric {fabric_name}: {', '.join(inactive_devices)}. "
                    "The workspace build completed, but inactive targeted devices make validation unsafe."
                )
            )

    @staticmethod
    def _inactive_cv_device_names(devices: list[CVDevice]) -> list[str]:
        """Return sorted unique device names whose CloudVision inventory state is inactive."""
        return sorted({device.hostname for device in devices if device.streaming is False})

    async def _ensure_workspace_pending(
        self, cv_client: CVClient, workspace: CVWorkspace, workspace_description: str
    ) -> None:
        """Create/update the workspace or rollback to pending if already built."""
        try:
            existing = await cv_client.get_workspace(workspace_id=workspace.id)
            existing_state = getattr(existing.state, "value", existing.state)
            if existing_state in (
                WorkspaceState.PENDING.value,
                WorkspaceState.ROLLED_BACK.value,
                "pending",
                "rolled_back",
            ):
                workspace.state = "pending"
            else:
                await rollback_workspace(cv_client, workspace.id)
                await cv_client.wait_for_workspace_state(workspace_id=workspace.id, state="pending")
                workspace.state = "pending"
        except CVResourceNotFound:
            await cv_client.create_workspace(
                workspace_id=workspace.id,
                display_name=workspace.name,
                description=workspace_description,
            )

        workspace.state = "pending"
        await cv_client.wait_for_workspace_state(workspace_id=workspace.id, state="pending")

    async def _track_workspace(
        self, ws_id: str, ws_name: str, fabric_id: str, proposed_change_id: str, status: str
    ) -> None:
        """Create or update the Cv.Workspace tracking node in Infrahub."""
        from infrahub_sdk.exceptions import NodeNotFoundError, SchemaNotFoundError

        try:
            try:
                ws_node = cast(
                    "Any",
                    await self.client.get(
                        kind="CloudvisionWorkspace", branch=self.branch_name, workspace_id__value=ws_id
                    ),
                )
                ws_node.status.value = status
                if hasattr(ws_node, "proposed_change_id"):
                    ws_node.proposed_change_id.value = proposed_change_id
                await ws_node.save()
            except NodeNotFoundError:
                ws_node = cast(
                    "Any",
                    await self.client.create(
                        kind="CloudvisionWorkspace",
                        branch=self.branch_name,
                        data={
                            "name": ws_name,
                            "workspace_id": ws_id,
                            "proposed_change_id": proposed_change_id,
                            "status": status,
                            "fabric": fabric_id,
                        },
                    ),
                )
                await ws_node.save()
        except SchemaNotFoundError:
            LOGGER.warning("CloudvisionWorkspace schema not loaded in Infrahub — skipping workspace tracking")
        except (AttributeError, ValueError, RuntimeError):
            LOGGER.exception("Failed to track workspace in Infrahub")

    def _report_results(self, result: DeployToCvResult, cv_config: Any, fabric_name: str, inventory_count: int) -> None:
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
        self.log_info(
            message=(
                f"Deployed {deployed_count} device configs, skipped {skipped_count}; "
                f"confirmed {inventory_count} devices in CloudVision inventory"
            )
        )

        if result.deployed_configs:
            device_names = ", ".join(c.device.hostname for c in result.deployed_configs)
            self.log_info(message=f"Devices with configs deployed: {device_names}")

        if result.skipped_configs:
            skipped_names = ", ".join(c.device.hostname for c in result.skipped_configs)
            self.log_info(message=f"WARNING: Devices skipped (not found on CloudVision): {skipped_names}")

        for warning in result.warnings:
            self.log_info(message=f"WARNING: {warning}")
