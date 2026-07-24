from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CVWorkspaceSubmissionWebhookQuery(BaseModel):
    cloudvision_workspace: "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspace" = (
        Field(alias="CloudvisionWorkspace")
    )


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspace(BaseModel):
    edges: list["CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdges"]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdges(BaseModel):
    node: Optional["CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNode"]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNode(BaseModel):
    id: str
    name: Optional["CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeName"]
    workspace_id: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeWorkspaceId"
    ]
    proposed_change_id: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeProposedChangeId"
    ]
    status: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeStatus"
    ]
    workspace_url: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeWorkspaceUrl"
    ]
    thread_id: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeThreadId"
    ]
    change_control_id: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeChangeControlId"
    ]
    change_control_url: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeChangeControlUrl"
    ]
    fabric: "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabric"


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeName(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeWorkspaceId(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeProposedChangeId(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeStatus(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeWorkspaceUrl(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeThreadId(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeChangeControlId(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeChangeControlUrl(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabric(BaseModel):
    node: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabricNode"
    ]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabricNodeName"
    ]


class CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


CVWorkspaceSubmissionWebhookQuery.model_rebuild()
CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspace.model_rebuild()
CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdges.model_rebuild()
CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNode.model_rebuild()
CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabric.model_rebuild()
CVWorkspaceSubmissionWebhookQueryCloudvisionWorkspaceEdgesNodeFabricNode.model_rebuild()
