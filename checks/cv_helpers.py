"""CloudVision helper utilities shared between checks and generators."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING
from uuid import NAMESPACE_DNS, uuid4, uuid5

from pyavd._cv.api.arista.workspace.v1 import (
    Request,
    RequestParams,
    WorkspaceConfig,
    WorkspaceConfigServiceStub,
    WorkspaceConfigSetRequest,
    WorkspaceKey,
)
from pyavd._cv.workflows.models import CloudVision

if TYPE_CHECKING:
    from pyavd._cv.client import CVClient

LOGGER = logging.getLogger(__name__)

INFRAHUB_CV_NAMESPACE = uuid5(NAMESPACE_DNS, "infrahub.cloudvision")


def get_cloudvision_config() -> CloudVision | None:
    """Build a CloudVision connection config from environment variables.

    Returns None if required variables are missing.
    """
    servers_raw = os.environ.get("CLOUDVISION_SERVERS")
    if not servers_raw:
        return None

    servers = [s.strip() for s in servers_raw.split(",") if s.strip()]
    token = os.environ.get("CLOUDVISION_TOKEN")
    username = os.environ.get("CLOUDVISION_USERNAME")
    password = os.environ.get("CLOUDVISION_PASSWORD")
    verify_certs = os.environ.get("CLOUDVISION_VERIFY_CERTS", "true").lower() != "false"

    if not token and not (username and password):
        return None

    return CloudVision(
        servers=servers,
        token=token,
        username=username,
        password=password,
        verify_certs=verify_certs,
        proxy_host=os.environ.get("CLOUDVISION_PROXY_HOST"),
        proxy_port=int(os.environ.get("CLOUDVISION_PROXY_PORT", "8080"))
        if os.environ.get("CLOUDVISION_PROXY_PORT")
        else None,
        proxy_username=os.environ.get("CLOUDVISION_PROXY_USERNAME"),
        proxy_password=os.environ.get("CLOUDVISION_PROXY_PASSWORD"),
    )


def get_workspace_id(proposed_change_id: str, fabric_name: str) -> str:
    """Generate a deterministic workspace ID from proposed change and fabric name."""
    return f"ws-{uuid5(INFRAHUB_CV_NAMESPACE, f'{proposed_change_id}-{fabric_name}')}"


def get_workspace_name(proposed_change_id: str, fabric_name: str) -> str:
    """Generate a human-readable workspace name."""
    return f"Infrahub - {fabric_name} - {proposed_change_id[:8]}"


async def rollback_workspace(cv_client: CVClient, workspace_id: str) -> WorkspaceConfig:
    """Rollback a built workspace to pending state.

    Uses the same pattern as CVClient.build_workspace() and
    CVClient.abandon_workspace() but with Request.ROLLBACK.
    """
    LOGGER.info("rollback_workspace: Rolling back workspace %s to pending", workspace_id)
    request = WorkspaceConfigSetRequest(
        WorkspaceConfig(
            key=WorkspaceKey(workspace_id=workspace_id),
            request=Request.ROLLBACK,
            request_params=RequestParams(
                request_id=f"req-{uuid4()}",
            ),
        ),
    )
    client = WorkspaceConfigServiceStub(cv_client._channel)
    response = await client.set(request, metadata=cv_client._metadata, timeout=120.0)
    return response.value
