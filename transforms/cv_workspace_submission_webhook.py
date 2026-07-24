"""CustomWebhook payload transform for CloudVision workspace submission."""

from __future__ import annotations

from typing import Any

from infrahub_sdk.transforms import InfrahubTransform

from .cv_workspace_submission_webhook_query import CVWorkspaceSubmissionWebhookQuery


class CVWorkspaceSubmissionWebhookPayload(InfrahubTransform):
    """Return a compact JSON payload for CloudVision workspace submission."""

    query = "cv_workspace_submission_webhook"

    async def transform(self, data: dict[str, Any]) -> dict[str, Any]:
        parsed = CVWorkspaceSubmissionWebhookQuery(**data)
        workspaces: list[dict[str, str | None]] = []
        proposed_change_id: str | None = None

        for edge in parsed.cloudvision_workspace.edges:
            node = edge.node
            if node is None:
                continue
            fabric = node.fabric.node if node.fabric else None
            current_proposed_change_id = node.proposed_change_id.value if node.proposed_change_id else None
            proposed_change_id = proposed_change_id or current_proposed_change_id
            workspaces.append(
                {
                    "workspace_id": node.workspace_id.value if node.workspace_id else None,
                    "proposed_change_id": current_proposed_change_id,
                    "status": node.status.value if node.status else None,
                    "workspace_url": node.workspace_url.value if node.workspace_url else None,
                    "fabric_name": fabric.name.value if fabric and fabric.name else None,
                }
            )

        return {
            "check_name": "cv-config-validation",
            "proposed_change_id": proposed_change_id,
            "workspaces": workspaces,
        }
