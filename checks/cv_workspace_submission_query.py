from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CVWorkspaceSubmissionQuery(BaseModel):
    cloudvision_workspace: "CVWorkspaceSubmissionQueryCloudvisionWorkspace" = Field(
        alias="CloudvisionWorkspace"
    )


class CVWorkspaceSubmissionQueryCloudvisionWorkspace(BaseModel):
    edges: list["CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdges"]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdges(BaseModel):
    node: Optional["CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNode"]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNode(BaseModel):
    id: str
    name: Optional["CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeName"]
    workspace_id: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeWorkspaceId"
    ]
    proposed_change_id: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeProposedChangeId"
    ]
    status: Optional["CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeStatus"]
    workspace_url: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeWorkspaceUrl"
    ]
    thread_id: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeThreadId"
    ]
    change_control_id: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeChangeControlId"
    ]
    change_control_url: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeChangeControlUrl"
    ]
    fabric: "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabric"


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeName(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeWorkspaceId(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeProposedChangeId(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeStatus(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeWorkspaceUrl(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeThreadId(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeChangeControlId(BaseModel):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeChangeControlUrl(
    BaseModel
):
    value: Optional[str]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabric(BaseModel):
    node: Optional["CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabricNode"]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabricNode(BaseModel):
    id: str
    name: Optional[
        "CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabricNodeName"
    ]


class CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabricNodeName(BaseModel):
    value: Optional[str]


CVWorkspaceSubmissionQuery.model_rebuild()
CVWorkspaceSubmissionQueryCloudvisionWorkspace.model_rebuild()
CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdges.model_rebuild()
CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNode.model_rebuild()
CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabric.model_rebuild()
CVWorkspaceSubmissionQueryCloudvisionWorkspaceEdgesNodeFabricNode.model_rebuild()
