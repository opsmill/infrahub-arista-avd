"""CloudVision helper utilities shared between checks and generators."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
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
LOCAL_PROPOSED_CHANGE_ID = "local"
DEFAULT_WORKSPACE_DESCRIPTION = "Infrahub proposed change validation"


@dataclass(frozen=True)
class ProposedChangeContext:
    """Metadata used to identify the CloudVision validation workspace."""

    id: str
    name: str
    description: str


def _env_value(name: str) -> str | None:
    """Return a stripped environment variable value or None when unset/blank."""
    value = os.environ.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def get_cloudvision_config() -> CloudVision | None:
    """Build a CloudVision connection config from environment variables.

    Returns None if required variables are missing.
    """
    servers_raw = _env_value("CLOUDVISION_SERVERS")
    if not servers_raw:
        return None

    servers = [s.strip() for s in servers_raw.split(",") if s.strip()]
    token = _env_value("CLOUDVISION_TOKEN")
    username = _env_value("CLOUDVISION_USERNAME")
    password = _env_value("CLOUDVISION_PASSWORD")
    verify_certs = os.environ.get("CLOUDVISION_VERIFY_CERTS", "true").lower() != "false"
    proxy_port = _env_value("CLOUDVISION_PROXY_PORT")

    if not token and not (username and password):
        return None

    return CloudVision(
        servers=servers,
        token=token,
        username=username,
        password=password,
        verify_certs=verify_certs,
        proxy_host=_env_value("CLOUDVISION_PROXY_HOST"),
        proxy_port=int(proxy_port) if proxy_port else None,
        proxy_username=_env_value("CLOUDVISION_PROXY_USERNAME"),
        proxy_password=_env_value("CLOUDVISION_PROXY_PASSWORD"),
    )


def get_workspace_id(proposed_change_id: str, fabric_name: str) -> str:
    """Generate a deterministic workspace ID from proposed change and fabric name."""
    return f"ws-{uuid5(INFRAHUB_CV_NAMESPACE, f'{proposed_change_id}-{fabric_name}')}"


def get_workspace_name(proposed_change_name: str, fabric_name: str) -> str:
    """Generate a human-readable workspace name."""
    return f"Infrahub Proposed Changes {proposed_change_name} - Fabric {fabric_name}"


def get_workspace_description(proposed_change_description: str | None) -> str:
    """Return a CloudVision workspace description with a safe fallback."""
    if proposed_change_description:
        stripped = proposed_change_description.strip()
        if stripped:
            return stripped
    return DEFAULT_WORKSPACE_DESCRIPTION


def _string_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _attribute_value(value: object | None) -> str | None:
    """Extract a string from Infrahub-style attribute values or plain values."""
    direct = _string_or_none(value)
    if direct:
        return direct
    nested_value = getattr(value, "value", None)
    return _string_or_none(nested_value)


def _mapping_attribute_value(data: object, name: str) -> str | None:
    if not isinstance(data, dict):
        return None
    value = data.get(name)
    if isinstance(value, dict):
        return _string_or_none(value.get("value"))
    return _attribute_value(value)


def _nested_proposed_change(initializer: object | None) -> object | None:
    if initializer is None:
        return None
    return getattr(initializer, "proposed_change", None)


def get_proposed_change_id(initializer: object | None) -> str:
    """Return the proposed-change identifier exposed by Infrahub task context."""
    if initializer is None:
        return LOCAL_PROPOSED_CHANGE_ID

    proposed_change = _nested_proposed_change(initializer)
    return (
        _attribute_value(getattr(initializer, "proposed_change_id", None))
        or _mapping_attribute_value(proposed_change, "id")
        or _attribute_value(getattr(proposed_change, "id", None))
        or _attribute_value(proposed_change)
        or _attribute_value(getattr(initializer, "proposed_change_name", None))
        or LOCAL_PROPOSED_CHANGE_ID
    )


def get_proposed_change_name(initializer: object | None, fallback: str) -> str:
    """Return the proposed-change name from task context, falling back safely."""
    if initializer is None:
        return fallback

    proposed_change = _nested_proposed_change(initializer)
    return (
        _attribute_value(getattr(initializer, "proposed_change_name", None))
        or _mapping_attribute_value(proposed_change, "name")
        or _attribute_value(getattr(proposed_change, "name", None))
        or _attribute_value(proposed_change)
        or fallback
    )


def get_proposed_change_description(initializer: object | None) -> str:
    """Return the proposed-change description from task context, falling back safely."""
    if initializer is None:
        return DEFAULT_WORKSPACE_DESCRIPTION

    proposed_change = _nested_proposed_change(initializer)
    return get_workspace_description(
        _attribute_value(getattr(initializer, "proposed_change_description", None))
        or _mapping_attribute_value(proposed_change, "description")
        or _attribute_value(getattr(proposed_change, "description", None))
    )


def _proposed_change_context_from_node(
    node: dict[str, object], current: ProposedChangeContext
) -> ProposedChangeContext:
    proposed_change_id = _mapping_attribute_value(node, "id") or current.id
    name = _mapping_attribute_value(node, "name") or current.name
    description = get_workspace_description(_mapping_attribute_value(node, "description") or current.description)
    return ProposedChangeContext(id=proposed_change_id, name=name, description=description)


def _proposed_change_query(proposed_change_id: str, branch_name: str | None) -> tuple[str, dict[str, object]] | None:
    if proposed_change_id != LOCAL_PROPOSED_CHANGE_ID:
        return (
            """
query GetProposedChangeMetadata($ids: [ID]) {
  CoreProposedChange(ids: $ids, limit: 1) {
    edges {
      node {
        id
        name {
          value
        }
        description {
          value
        }
      }
    }
  }
}
""",
            {"ids": [proposed_change_id]},
        )
    if branch_name:
        return (
            """
query GetProposedChangeMetadata($sourceBranch: String!) {
  CoreProposedChange(source_branch__value: $sourceBranch, state__value: "open", limit: 1) {
    edges {
      node {
        id
        name {
          value
        }
        description {
          value
        }
      }
    }
  }
}
""",
            {"sourceBranch": branch_name},
        )
    return None


async def get_proposed_change_context(
    client: Any, initializer: object | None, branch_name: str | None = None
) -> ProposedChangeContext:
    """Return proposed-change metadata from task context and, when possible, Infrahub.

    Infrahub's check initializer only guarantees the proposed-change ID. The
    CloudVision workspace name and description need the user-facing name and
    description, so this function enriches the initializer data with a
    CoreProposedChange lookup. Metadata lookup failures must not prevent
    configuration validation, so they fall back to deterministic local values.
    """
    proposed_change_id = get_proposed_change_id(initializer)
    current = ProposedChangeContext(
        id=proposed_change_id,
        name=get_proposed_change_name(initializer, proposed_change_id),
        description=get_proposed_change_description(initializer),
    )
    query = _proposed_change_query(proposed_change_id, branch_name)
    if query is None:
        return current

    try:
        gql_query, variables = query
        result = await client.execute_graphql(
            query=gql_query,
            variables=variables,
        )
    except Exception:
        LOGGER.warning("Unable to fetch proposed-change metadata for CloudVision workspace", exc_info=True)
        return current

    proposed_change_result = result.get("CoreProposedChange") if isinstance(result, dict) else None
    edges = proposed_change_result.get("edges", []) if isinstance(proposed_change_result, dict) else []
    if not edges:
        return current
    node = edges[0].get("node") if isinstance(edges[0], dict) else None
    if not isinstance(node, dict):
        return current
    return _proposed_change_context_from_node(node, current)


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
