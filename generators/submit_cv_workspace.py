"""Post-merge generator that submits CloudVision workspaces.

After a proposed change is merged, this generator finds all Cv.Workspace
nodes in 'built' status for the target fabric and submits them to
CloudVision without creating a change control.
"""

from __future__ import annotations

import logging
from typing import Any

from infrahub_sdk.generator import InfrahubGenerator
from pyavd._cv.client import CVClient
from pyavd._cv.client.exceptions import CVClientException
from pyavd._cv.workflows.models import CVWorkspace

from checks.cv_helpers import get_cloudvision_config

from .submit_cv_workspace_query import SubmitCVWorkspaceQuery

LOGGER = logging.getLogger(__name__)


class SubmitCVWorkspaceGenerator(InfrahubGenerator):
    """Submits built CloudVision workspaces after a proposed change merge."""

    async def generate(self, data: dict[str, Any]) -> None:
        parsed = SubmitCVWorkspaceQuery(**data)

        fabric_edges = parsed.network_fabric.edges
        if not fabric_edges or not fabric_edges[0].node:
            return

        fabric_node = fabric_edges[0].node
        fabric_id = fabric_node.id
        fabric_name = fabric_node.name.value if fabric_node.name else "unknown"

        workspaces_to_submit = []
        for edge in parsed.cv_workspace.edges:
            ws_node = edge.node
            if not ws_node or not ws_node.workspace_id or not ws_node.workspace_id.value:
                continue
            if not ws_node.fabric.node or ws_node.fabric.node.id != fabric_id:
                continue
            workspaces_to_submit.append(ws_node)

        if not workspaces_to_submit:
            LOGGER.info("No built workspaces to submit for fabric %s", fabric_name)
            return

        cv_config = get_cloudvision_config()
        if cv_config is None:
            LOGGER.error("CloudVision credentials not configured, cannot submit workspaces")
            return

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
                for ws_data in workspaces_to_submit:
                    ws_id = ws_data.workspace_id.value
                    ws_display_name = ws_data.name.value if ws_data.name else ws_id
                    await self._submit_workspace(cv_client, ws_id, ws_display_name, ws_data.id)

        except CVClientException:
            LOGGER.exception("CloudVision connection failed during workspace submission")

    async def _submit_workspace(
        self, cv_client: CVClient, ws_id: str, ws_display_name: str, infrahub_node_id: str
    ) -> None:
        """Submit a single workspace and update the Infrahub tracking node."""
        LOGGER.info("Submitting CloudVision workspace %s (%s)", ws_display_name, ws_id)

        workspace = CVWorkspace(name=ws_display_name, id=ws_id, requested_state="submitted")
        workspace.state = "built"

        try:
            workspace_config = await cv_client.submit_workspace(workspace_id=ws_id)
            submit_result, _cv_workspace = await cv_client.wait_for_workspace_response(
                workspace_id=ws_id,
                request_id=workspace_config.request_params.request_id,
            )

            from pyavd._cv.api.arista.workspace.v1 import ResponseStatus

            if submit_result.status == ResponseStatus.SUCCESS:
                LOGGER.info("Workspace %s submitted successfully", ws_display_name)
                await self._update_tracking_node(infrahub_node_id, "submitted")
            else:
                LOGGER.error("Workspace %s submission failed: %s", ws_display_name, submit_result)
        except CVClientException:
            LOGGER.exception("Failed to submit workspace %s", ws_display_name)

    async def _update_tracking_node(self, node_id: str, status: str) -> None:
        """Update the Cv.Workspace tracking node status in Infrahub."""
        try:
            ws_node = await self.client.get(kind="CvWorkspace", id=node_id)
            ws_node.status.value = status
            await ws_node.save()
        except (AttributeError, ValueError, RuntimeError):
            LOGGER.exception("Failed to update workspace tracking node")
