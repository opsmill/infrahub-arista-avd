"""CloudVision proposed-change thread and CustomWebhook workspace lifecycle."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

from infrahub_sdk import InfrahubClient
from infrahub_sdk.exceptions import NodeNotFoundError, SchemaNotFoundError
from pyavd._cv.api.arista.workspace.v1 import ResponseStatus, WorkspaceState
from pyavd._cv.client import CVClient
from pyavd._cv.client.exceptions import CVClientException, CVResourceNotFound, CVWorkspaceFailed

from transforms.cv_workspace_submission_webhook_query import CVWorkspaceSubmissionWebhookQuery

from .cv_helpers import get_change_control_url, get_cloudvision_config, get_workspace_url

LOGGER = logging.getLogger(__name__)

SubmissionStatus = Literal["submitted", "already_submitted", "skipped", "failed"]

SUBMIT_READY_STATUSES = {"built", "submit_failed"}
SUBMITTED_STATES = {WorkspaceState.SUBMITTED.value, "submitted"}
SUBMISSION_THREAD_LABEL = "CloudVision workspace submission"
WORKSPACE_SUBMISSION_QUERY_PATH = Path(__file__).parents[1] / "transforms" / "cv_workspace_submission_webhook.gql"


@dataclass(frozen=True)
class SubmissionResult:
    """Typed result returned by the CloudVision CustomWebhook submission path."""

    status: SubmissionStatus
    proposed_change_id: str
    workspace_id: str | None = None
    fabric_name: str | None = None
    thread_id: str | None = None
    change_control_id: str | None = None
    message: str = ""


@dataclass(frozen=True)
class WorkspaceRecord:
    """Relevant Infrahub workspace tracking state."""

    id: str
    name: str
    workspace_id: str | None
    proposed_change_id: str | None
    status: str | None
    workspace_url: str | None
    thread_id: str | None
    change_control_id: str | None
    change_control_url: str | None
    fabric_id: str | None
    fabric_name: str | None


def workspace_thread_label(workspace_id: str) -> str:
    """Return the deterministic CoreChangeThread label for a workspace."""
    return f"CloudVision workspace {workspace_id}"


def _valid_workspace_url(workspace_url: str | None, workspace_id: str | None) -> str | None:
    if not workspace_url:
        return None
    stripped = workspace_url.strip()
    if not stripped.startswith(("http://", "https://")):
        return None
    if workspace_id and workspace_id not in stripped:
        return None
    return stripped


def workspace_url_comment(
    proposed_change_id: str, workspace_id: str, fabric_name: str | None, workspace_url: str
) -> str:
    """Return the user-visible workspace URL comment body."""
    fabric = fabric_name or "unknown"
    return (
        f"CloudVision workspace for proposed change {proposed_change_id} and fabric {fabric}: "
        f"{workspace_url} (workspace {workspace_id})"
    )


async def _execute_graphql(
    client: Any, query: str, variables: dict[str, object] | None = None, branch: str | None = None
) -> dict[str, Any]:
    kwargs: dict[str, object] = {"query": query}
    if variables is not None:
        kwargs["variables"] = variables
    if branch is not None:
        kwargs["branch_name"] = branch
    try:
        result = await client.execute_graphql(**kwargs)
    except TypeError:
        if branch is not None:
            kwargs.pop("branch_name", None)
            kwargs["branch"] = branch
        result = await client.execute_graphql(**kwargs)
    return result if isinstance(result, dict) else {}


def _edges(result: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = result.get(key)
    if not isinstance(value, dict):
        return []
    edges = value.get("edges", [])
    return edges if isinstance(edges, list) else []


def _first_node(result: dict[str, Any], key: str) -> dict[str, Any] | None:
    edges = _edges(result, key)
    if not edges:
        return None
    node = edges[0].get("node") if isinstance(edges[0], dict) else None
    return node if isinstance(node, dict) else None


def _attr_value(node: dict[str, Any], name: str) -> Any:
    value = node.get(name)
    if isinstance(value, dict):
        return value.get("value")
    return value


def _comment_texts(thread_node: dict[str, Any]) -> set[str]:
    comments = thread_node.get("comments")
    if not isinstance(comments, dict):
        return set()
    texts: set[str] = set()
    for edge in comments.get("edges", []):
        if not isinstance(edge, dict):
            continue
        node = edge.get("node")
        if isinstance(node, dict):
            text = _attr_value(node, "text")
            if isinstance(text, str):
                texts.add(text)
    return texts


async def _lookup_thread(
    client: Any,
    *,
    proposed_change_id: str,
    workspace_id: str,
    thread_id: str | None,
    branch: str,
    label: str | None = None,
) -> dict[str, Any] | None:
    thread_label = label or workspace_thread_label(workspace_id)
    fields = """
      id
      label { value }
      resolved { value }
      comments {
        edges {
          node {
            id
            text { value }
          }
        }
      }
"""
    if thread_id:
        result = await _execute_graphql(
            client,
            f"query GetCloudVisionWorkspaceThreadById($ids: [ID]) {{ CoreChangeThread(ids: $ids, limit: 1) {{ edges {{ node {{ {fields} }} }} }} }}",
            {"ids": [thread_id]},
            branch,
        )
        node = _first_node(result, "CoreChangeThread")
        if node:
            return node

    result = await _execute_graphql(
        client,
        f"""
query GetCloudVisionWorkspaceThread($changeIds: [ID], $label: String) {{
  CoreChangeThread(change__ids: $changeIds, label__value: $label, limit: 1) {{
    edges {{
      node {{
        {fields}
      }}
    }}
  }}
}}
""",
        {"changeIds": [proposed_change_id], "label": thread_label},
        branch,
    )
    return _first_node(result, "CoreChangeThread")


async def _create_thread(
    client: Any, *, proposed_change_id: str, workspace_id: str, branch: str, label: str | None = None
) -> dict[str, Any]:
    thread_label = label or workspace_thread_label(workspace_id)
    result = await _execute_graphql(
        client,
        """
mutation CreateCloudVisionWorkspaceThread($change: RelatedNodeInput!, $label: String!) {
  CoreChangeThreadCreate(
    data: {
      change: $change
      label: { value: $label }
      resolved: { value: false }
    }
  ) {
    ok
    object {
      id
      label { value }
      resolved { value }
      comments {
        edges {
          node {
            id
            text { value }
          }
        }
      }
    }
  }
}
""",
        {"change": {"id": proposed_change_id}, "label": thread_label},
        branch,
    )
    created = result.get("CoreChangeThreadCreate")
    node = created.get("object") if isinstance(created, dict) else None
    if not isinstance(node, dict) or not node.get("id"):
        msg = f"Unable to create CloudVision workspace thread for proposed change {proposed_change_id}"
        raise RuntimeError(msg)
    return node


async def _add_comment(client: Any, *, thread_id: str, text: str, branch: str) -> str:
    result = await _execute_graphql(
        client,
        """
mutation AddCloudVisionWorkspaceThreadComment($thread: RelatedNodeInput!, $text: String!) {
  CoreThreadCommentCreate(
    data: {
      thread: $thread
      text: { value: $text }
    }
  ) {
    ok
    object {
      id
      text { value }
    }
  }
}
""",
        {"thread": {"id": thread_id}, "text": text},
        branch,
    )
    created = result.get("CoreThreadCommentCreate")
    node = created.get("object") if isinstance(created, dict) else None
    if not isinstance(node, dict) or not node.get("id"):
        msg = f"Unable to add CloudVision workspace comment to thread {thread_id}"
        raise RuntimeError(msg)
    return cast("str", node["id"])


async def _add_comment_once(client: Any, *, thread: dict[str, Any], thread_id: str, text: str, branch: str) -> None:
    if text not in _comment_texts(thread):
        await _add_comment(client, thread_id=thread_id, text=text, branch=branch)


async def _resolve_thread(client: Any, *, thread_id: str, resolved: bool, branch: str) -> None:
    await _execute_graphql(
        client,
        """
mutation ResolveCloudVisionWorkspaceThread($id: String!, $resolved: Boolean!) {
  CoreChangeThreadUpdate(
    data: {
      id: $id
      resolved: { value: $resolved }
    }
  ) {
    ok
    object {
      id
      resolved { value }
    }
  }
}
""",
        {"id": thread_id, "resolved": resolved},
        branch,
    )


async def ensure_workspace_thread_and_url_comment(
    client: Any,
    *,
    proposed_change_id: str,
    workspace_id: str,
    fabric_name: str | None,
    workspace_url: str,
    branch: str,
    thread_id: str | None = None,
) -> str:
    """Create/reuse the workspace thread and ensure one URL comment exists."""
    thread = await _lookup_thread(
        client,
        proposed_change_id=proposed_change_id,
        workspace_id=workspace_id,
        thread_id=thread_id,
        branch=branch,
    )
    if thread is None:
        thread = await _create_thread(
            client, proposed_change_id=proposed_change_id, workspace_id=workspace_id, branch=branch
        )

    current_thread_id = cast("str", thread["id"])
    comment = workspace_url_comment(proposed_change_id, workspace_id, fabric_name, workspace_url)
    if comment not in _comment_texts(thread):
        await _add_comment(client, thread_id=current_thread_id, text=comment, branch=branch)
    return current_thread_id


async def _ensure_change_thread(
    client: Any,
    *,
    proposed_change_id: str,
    label: str,
    branch: str,
    thread_id: str | None = None,
) -> dict[str, Any]:
    thread = await _lookup_thread(
        client,
        proposed_change_id=proposed_change_id,
        workspace_id=label,
        thread_id=thread_id,
        branch=branch,
        label=label,
    )
    if thread is None:
        thread = await _create_thread(
            client,
            proposed_change_id=proposed_change_id,
            workspace_id=label,
            branch=branch,
            label=label,
        )
    return thread


async def _record_change_outcome(
    client: Any,
    *,
    proposed_change_id: str,
    branch: str,
    text: str,
    resolved: bool,
) -> str | None:
    thread = await _ensure_change_thread(
        client,
        proposed_change_id=proposed_change_id,
        label=SUBMISSION_THREAD_LABEL,
        branch=branch,
    )
    thread_id = cast("str", thread["id"])
    await _add_comment_once(client, thread=thread, thread_id=thread_id, text=text, branch=branch)
    await _resolve_thread(client, thread_id=thread_id, resolved=resolved, branch=branch)
    return thread_id


def _workspace_from_query(data: CVWorkspaceSubmissionWebhookQuery) -> list[WorkspaceRecord]:
    records: list[WorkspaceRecord] = []
    for edge in data.cloudvision_workspace.edges:
        node = edge.node
        if node is None:
            continue
        fabric = node.fabric.node if node.fabric else None
        records.append(
            WorkspaceRecord(
                id=node.id,
                name=node.name.value if node.name and node.name.value else "",
                workspace_id=node.workspace_id.value if node.workspace_id else None,
                proposed_change_id=node.proposed_change_id.value if node.proposed_change_id else None,
                status=node.status.value if node.status else None,
                workspace_url=node.workspace_url.value if node.workspace_url else None,
                thread_id=node.thread_id.value if node.thread_id else None,
                change_control_id=node.change_control_id.value if node.change_control_id else None,
                change_control_url=node.change_control_url.value if node.change_control_url else None,
                fabric_id=fabric.id if fabric else None,
                fabric_name=fabric.name.value if fabric and fabric.name else None,
            )
        )
    return records


@lru_cache(maxsize=1)
def _workspace_submission_query() -> str:
    return WORKSPACE_SUBMISSION_QUERY_PATH.read_text(encoding="utf-8")


async def _get_linked_workspaces(client: Any, proposed_change_id: str, branch: str) -> list[WorkspaceRecord]:
    result = await _execute_graphql(
        client, _workspace_submission_query(), {"proposed_change_id": proposed_change_id}, branch
    )
    return _workspace_from_query(CVWorkspaceSubmissionWebhookQuery(**result))


def _set_optional_attr(node: Any, name: str, value: str | None) -> None:
    if not hasattr(node, name) or value is None:
        return
    getattr(node, name).value = value


async def _save_workspace_success(
    client: Any,
    *,
    record: WorkspaceRecord,
    branch: str,
    change_control_id: str | None,
    change_control_url: str | None,
    submitted_at: str,
    workspace_url: str | None,
) -> None:
    node = await client.get(kind="CloudvisionWorkspace", branch=branch, id=record.id)
    node.status.value = "submitted"
    _set_optional_attr(node, "workspace_url", workspace_url)
    _set_optional_attr(node, "change_control_id", change_control_id)
    _set_optional_attr(node, "change_control_url", change_control_url)
    _set_optional_attr(node, "submitted_at", submitted_at)
    _set_optional_attr(node, "last_submission_error", "")
    await node.save()


async def _save_workspace_failure(
    client: Any, *, record: WorkspaceRecord, branch: str, reason: str, attempted_at: str
) -> None:
    node = await client.get(kind="CloudvisionWorkspace", branch=branch, id=record.id)
    node.status.value = "submit_failed"
    _set_optional_attr(node, "last_submission_error", reason)
    _set_optional_attr(node, "last_submission_attempt_at", attempted_at)
    await node.save()


def _workspace_state_value(workspace: Any) -> str | None:
    state = getattr(workspace, "state", None)
    value = getattr(state, "value", state)
    return str(value) if value is not None else None


def _request_id(submit_response: Any) -> str | None:
    request_params = getattr(submit_response, "request_params", None)
    request_id = getattr(request_params, "request_id", None)
    return str(request_id) if request_id else None


def _change_control_id(workspace: Any) -> str | None:
    direct = getattr(workspace, "change_control_id", None)
    if direct:
        return str(direct)
    cc_ids = getattr(workspace, "cc_ids", None)
    values = getattr(cc_ids, "values", None)
    if values:
        first = next(iter(values), None)
        return str(first) if first else None
    return None


def _success_comment(workspace_id: str, workspace_url: str | None) -> str:
    if workspace_url:
        return f"CloudVision workspace {workspace_id} submitted successfully. Workspace: {workspace_url}"
    return f"CloudVision workspace {workspace_id} submitted successfully."


def _failure_comment(proposed_change_id: str, workspace_id: str | None, fabric_name: str | None, reason: str) -> str:
    workspace = workspace_id or "unknown"
    fabric = fabric_name or "unknown"
    return (
        f"Infrahub proposed change {proposed_change_id} was submitted, but CloudVision workspace {workspace} "
        f"was not submitted for fabric {fabric}: {reason}"
    )


def _thread_workspace_url(record: WorkspaceRecord, cv_config: Any | None = None) -> str | None:
    valid = _valid_workspace_url(record.workspace_url, record.workspace_id)
    if valid or not cv_config or not record.workspace_id:
        return valid
    return get_workspace_url(cv_config, record.workspace_id)


def _log_outcome_fallback(result: SubmissionResult) -> None:
    LOGGER.error(
        "CloudVision submission outcome could not be written to the proposed-change thread; "
        "fallback outcome: status=%s proposed_change_id=%s workspace_id=%s fabric=%s change_control_id=%s message=%s",
        result.status,
        result.proposed_change_id,
        result.workspace_id,
        result.fabric_name,
        result.change_control_id,
        result.message,
    )


async def _append_outcome_comment(
    client: Any,
    *,
    record: WorkspaceRecord,
    proposed_change_id: str,
    branch: str,
    text: str,
    resolved: bool,
    workspace_url: str | None = None,
) -> str | None:
    if not record.workspace_id:
        return await _record_change_outcome(
            client,
            proposed_change_id=proposed_change_id,
            branch=branch,
            text=text,
            resolved=resolved,
        )

    valid_url = _valid_workspace_url(workspace_url or record.workspace_url, record.workspace_id)
    if valid_url:
        thread_id = await ensure_workspace_thread_and_url_comment(
            client,
            proposed_change_id=proposed_change_id,
            workspace_id=record.workspace_id,
            fabric_name=record.fabric_name,
            workspace_url=valid_url,
            branch=branch,
            thread_id=record.thread_id,
        )
    else:
        thread = await _lookup_thread(
            client,
            proposed_change_id=proposed_change_id,
            workspace_id=record.workspace_id,
            thread_id=record.thread_id,
            branch=branch,
        )
        if thread is None:
            thread = await _create_thread(
                client,
                proposed_change_id=proposed_change_id,
                workspace_id=record.workspace_id,
                branch=branch,
            )
        thread_id = cast("str", thread["id"])

    thread = await _lookup_thread(
        client,
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        thread_id=thread_id,
        branch=branch,
    )
    if thread is None:
        thread = {"comments": {"edges": []}}
    await _add_comment_once(client, thread=thread, thread_id=thread_id, text=text, branch=branch)
    await _resolve_thread(client, thread_id=thread_id, resolved=resolved, branch=branch)
    return thread_id


async def _fail_workspace(
    client: Any,
    *,
    record: WorkspaceRecord,
    proposed_change_id: str,
    branch: str,
    reason: str,
    workspace_url: str | None = None,
) -> SubmissionResult:
    attempted_at = datetime.now(UTC).isoformat()
    try:
        await _save_workspace_failure(client, record=record, branch=branch, reason=reason, attempted_at=attempted_at)
    except Exception:
        LOGGER.exception("Failed to persist CloudVision submission failure for workspace %s", record.workspace_id)
    thread_id: str | None = None
    try:
        thread_id = await _append_outcome_comment(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            text=_failure_comment(proposed_change_id, record.workspace_id, record.fabric_name, reason),
            resolved=False,
            workspace_url=workspace_url,
        )
    except Exception:
        LOGGER.exception(
            "Failed to record CloudVision submission failure comment for workspace %s; "
            "fallback outcome: status=failed proposed_change_id=%s fabric=%s message=%s",
            record.workspace_id,
            proposed_change_id,
            record.fabric_name,
            reason,
        )
    return SubmissionResult(
        status="failed",
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        fabric_name=record.fabric_name,
        thread_id=thread_id or record.thread_id,
        message=reason,
    )


async def _submit_workspace(
    client: Any, *, record: WorkspaceRecord, proposed_change_id: str, branch: str
) -> SubmissionResult:
    if not record.workspace_id:
        return await _fail_workspace(
            client, record=record, proposed_change_id=proposed_change_id, branch=branch, reason="Missing workspace ID"
        )
    if record.status == "submitted":
        return await _already_submitted(client, record=record, proposed_change_id=proposed_change_id, branch=branch)

    cv_config = get_cloudvision_config()
    thread_workspace_url = _thread_workspace_url(record, cv_config)
    if cv_config is None:
        return await _fail_workspace(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            reason=(
                "CloudVision credentials not configured. Set CLOUDVISION_SERVERS plus CLOUDVISION_TOKEN, "
                "or CLOUDVISION_SERVERS plus CLOUDVISION_USERNAME and CLOUDVISION_PASSWORD."
            ),
            workspace_url=thread_workspace_url,
        )
    if record.status not in SUBMIT_READY_STATUSES:
        return await _fail_workspace(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            reason=f"Workspace is not submit-ready: status={record.status or 'unknown'}",
            workspace_url=thread_workspace_url,
        )

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
            existing = await cv_client.get_workspace(workspace_id=record.workspace_id)
            if _workspace_state_value(existing) in SUBMITTED_STATES:
                return await _already_submitted(
                    client, record=record, proposed_change_id=proposed_change_id, branch=branch
                )
            submitted = await cv_client.submit_workspace(record.workspace_id, force=False)
            request_id = _request_id(submitted)
            if request_id is None:
                return await _fail_workspace(
                    client,
                    record=record,
                    proposed_change_id=proposed_change_id,
                    branch=branch,
                    workspace_url=thread_workspace_url,
                    reason="CloudVision did not return a submission request ID",
                )
            response, workspace = await cv_client.wait_for_workspace_response(
                workspace_id=record.workspace_id, request_id=request_id, timeout=600.0
            )
    except (
        CVClientException,
        CVResourceNotFound,
        CVWorkspaceFailed,
        TimeoutError,
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        return await _fail_workspace(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            reason=str(exc),
            workspace_url=thread_workspace_url,
        )

    status = getattr(response, "status", None)
    if status == ResponseStatus.FAIL or str(status).lower().endswith("fail"):
        reason = getattr(response, "message", None) or "CloudVision rejected workspace submission"
        return await _fail_workspace(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            reason=str(reason),
            workspace_url=thread_workspace_url,
        )

    change_control_id = _change_control_id(workspace)
    change_control_url = get_change_control_url(cv_config, change_control_id)
    submitted_at = datetime.now(UTC).isoformat()
    await _save_workspace_success(
        client,
        record=record,
        branch=branch,
        change_control_id=change_control_id,
        change_control_url=change_control_url,
        submitted_at=submitted_at,
        workspace_url=thread_workspace_url,
    )
    text = _success_comment(record.workspace_id, thread_workspace_url)
    thread_id = record.thread_id
    result = SubmissionResult(
        status="submitted",
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        fabric_name=record.fabric_name,
        thread_id=thread_id,
        change_control_id=change_control_id,
        message=text,
    )
    try:
        thread_id = await _append_outcome_comment(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            text=text,
            resolved=True,
            workspace_url=thread_workspace_url,
        )
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        _log_outcome_fallback(result)
    return SubmissionResult(
        status="submitted",
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        fabric_name=record.fabric_name,
        thread_id=thread_id or record.thread_id,
        change_control_id=change_control_id,
        message=text,
    )


async def _already_submitted(
    client: Any, *, record: WorkspaceRecord, proposed_change_id: str, branch: str
) -> SubmissionResult:
    text = f"CloudVision workspace {record.workspace_id} was already submitted; no additional submission was needed."
    try:
        node = await client.get(kind="CloudvisionWorkspace", branch=branch, id=record.id)
        node.status.value = "submitted"
        await node.save()
    except Exception:
        LOGGER.exception("Failed to persist already-submitted status for workspace %s", record.workspace_id)
    thread_id = record.thread_id
    result = SubmissionResult(
        status="already_submitted",
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        fabric_name=record.fabric_name,
        thread_id=thread_id,
        change_control_id=record.change_control_id,
        message=text,
    )
    try:
        thread_id = await _append_outcome_comment(
            client,
            record=record,
            proposed_change_id=proposed_change_id,
            branch=branch,
            text=text,
            resolved=True,
            workspace_url=_thread_workspace_url(record),
        )
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        _log_outcome_fallback(result)
    return SubmissionResult(
        status="already_submitted",
        proposed_change_id=proposed_change_id,
        workspace_id=record.workspace_id,
        fabric_name=record.fabric_name,
        thread_id=thread_id or record.thread_id,
        change_control_id=record.change_control_id,
        message=text,
    )


def _event_value(event: Mapping[str, Any], key: str) -> Any:
    value = event.get(key)
    if value is not None:
        return value
    payload = event.get("payload")
    if isinstance(payload, Mapping):
        return payload.get(key)
    return None


def _node_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, Mapping):
        return None
    node_id = value.get("id") or value.get("node_id")
    return str(node_id) if node_id else None


def _proposed_change_id_from_event(event: Mapping[str, Any]) -> str | None:
    direct = _event_value(event, "proposed_change_id") or _event_value(event, "proposed_change")
    proposed_change_id = _node_id(direct)
    if proposed_change_id:
        return proposed_change_id
    payload = event.get("payload")
    if isinstance(payload, Mapping):
        proposed_change_id = _node_id(payload.get("primary_node") or payload.get("node"))
        if proposed_change_id:
            return proposed_change_id
    return _node_id(event.get("primary_node"))


def _branch_from_event(event: Mapping[str, Any], fallback: str) -> str:
    branch = _event_value(event, "destination_branch") or _event_value(event, "branch")
    return branch if isinstance(branch, str) and branch.strip() else fallback


async def submit_linked_workspace_for_merged_event(
    client: Any,
    event: Mapping[str, Any],
    *,
    branch: str = "main",
) -> SubmissionResult:
    """Backward-compatible adapter for legacy merged proposed-change events."""
    proposed_change_id = _proposed_change_id_from_event(event)
    if not proposed_change_id:
        message = "Unable to resolve proposed change ID from merged proposed-change event"
        LOGGER.error(message)
        return SubmissionResult(status="failed", proposed_change_id="", message=message)
    return await submit_linked_workspace_for_proposed_change(
        client,
        proposed_change_id,
        branch=_branch_from_event(event, branch),
    )


def _check_name_from_event(event: Mapping[str, Any]) -> str | None:
    value = _event_value(event, "check_name") or _event_value(event, "check")
    if isinstance(value, Mapping):
        name = value.get("name") or value.get("display_label")
        return str(name) if name else None
    return str(value) if value else None


async def submit_linked_workspace_for_custom_webhook(
    client: Any,
    event: Mapping[str, Any],
    *,
    branch: str = "main",
) -> SubmissionResult:
    """Adapter for the proposed-change submitted CustomWebhook payload."""
    check_name = _check_name_from_event(event)
    if check_name and check_name != "cv-config-validation":
        message = f"Ignoring CustomWebhook event for check {check_name}"
        LOGGER.info(message)
        return SubmissionResult(status="skipped", proposed_change_id="", message=message)

    proposed_change_id = _proposed_change_id_from_event(event)
    if not proposed_change_id:
        message = "Unable to resolve proposed change ID from CustomWebhook event"
        LOGGER.error(message)
        return SubmissionResult(status="failed", proposed_change_id="", message=message)

    return await submit_linked_workspace_for_proposed_change(
        client,
        proposed_change_id,
        branch=_branch_from_event(event, branch),
    )


async def submit_linked_workspace_for_proposed_change(
    client: Any,
    proposed_change_id: str,
    *,
    branch: str = "main",
) -> SubmissionResult:
    """Submit the exact CloudVision workspace linked to a submitted proposed change."""
    try:
        records = await _get_linked_workspaces(client, proposed_change_id, branch)
    except (SchemaNotFoundError, NodeNotFoundError) as exc:
        message = f"Unable to resolve linked CloudVision workspace: {exc}"
        LOGGER.exception(message)
        return SubmissionResult(status="failed", proposed_change_id=proposed_change_id, message=message)

    if not records:
        message = f"No linked CloudVision workspace found for proposed change {proposed_change_id}; skipping submission"
        LOGGER.info(message)
        thread_id: str | None = None
        try:
            thread_id = await _record_change_outcome(
                client,
                proposed_change_id=proposed_change_id,
                branch=branch,
                text=message,
                resolved=True,
            )
        except Exception:
            LOGGER.exception(
                "Failed to record CloudVision no-workspace outcome; "
                "fallback outcome: status=skipped proposed_change_id=%s message=%s",
                proposed_change_id,
                message,
            )
        return SubmissionResult(
            status="skipped", proposed_change_id=proposed_change_id, thread_id=thread_id, message=message
        )
    if len(records) > 1:
        workspace_ids = ", ".join(record.workspace_id or record.id for record in records)
        message = f"Multiple CloudVision workspaces linked to proposed change {proposed_change_id}: {workspace_ids}"
        LOGGER.error(message)
        thread_id = None
        try:
            thread_id = await _record_change_outcome(
                client,
                proposed_change_id=proposed_change_id,
                branch=branch,
                text=message,
                resolved=False,
            )
        except Exception:
            LOGGER.exception(
                "Failed to record CloudVision ambiguous-workspace outcome; "
                "fallback outcome: status=failed proposed_change_id=%s message=%s",
                proposed_change_id,
                message,
            )
        return SubmissionResult(
            status="failed", proposed_change_id=proposed_change_id, thread_id=thread_id, message=message
        )
    return await _submit_workspace(client, record=records[0], proposed_change_id=proposed_change_id, branch=branch)


async def _run_manual_submission(proposed_change_id: str, branch: str) -> SubmissionResult:
    address = os.environ.get("INFRAHUB_ADDRESS", "")
    token = os.environ.get("INFRAHUB_API_TOKEN")
    config: dict[str, str] = {}
    if token:
        config["api_token"] = token
    client = InfrahubClient(address=address, config=config or None)
    return await submit_linked_workspace_for_proposed_change(client, proposed_change_id, branch=branch)


def main() -> None:
    """CLI entry point for manual CustomWebhook submission retries."""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Submit a linked CloudVision workspace for a proposed change.")
    parser.add_argument("proposed_change_id")
    parser.add_argument("--branch", default="main")
    args = parser.parse_args()
    result = asyncio.run(_run_manual_submission(args.proposed_change_id, args.branch))
    print(f"{result.status}: {result.message}")


if __name__ == "__main__":
    main()
