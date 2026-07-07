from __future__ import annotations

from pydantic import BaseModel, Field


class SubmitCVWorkspaceQuery(BaseModel):
    network_fabric: SubmitCVWorkspaceNetworkFabric = Field(alias="NetworkFabric")
    cv_workspace: SubmitCVWorkspaceCvWorkspace = Field(alias="CloudvisionWorkspace")


class SubmitCVWorkspaceNetworkFabric(BaseModel):
    edges: list[SubmitCVWorkspaceNetworkFabricEdge]


class SubmitCVWorkspaceNetworkFabricEdge(BaseModel):
    node: SubmitCVWorkspaceNetworkFabricNode | None


class SubmitCVWorkspaceNetworkFabricNode(BaseModel):
    id: str
    name: SubmitCVWorkspaceValueField | None


class SubmitCVWorkspaceValueField(BaseModel):
    value: str | None


class SubmitCVWorkspaceCvWorkspace(BaseModel):
    edges: list[SubmitCVWorkspaceCvWorkspaceEdge]


class SubmitCVWorkspaceCvWorkspaceEdge(BaseModel):
    node: SubmitCVWorkspaceCvWorkspaceNode | None


class SubmitCVWorkspaceCvWorkspaceNode(BaseModel):
    id: str
    workspace_id: SubmitCVWorkspaceValueField | None
    proposed_change_id: SubmitCVWorkspaceValueField | None
    name: SubmitCVWorkspaceValueField | None
    status: SubmitCVWorkspaceValueField | None
    fabric: SubmitCVWorkspaceCvWorkspaceFabric


class SubmitCVWorkspaceCvWorkspaceFabric(BaseModel):
    node: SubmitCVWorkspaceCvWorkspaceFabricNode | None


class SubmitCVWorkspaceCvWorkspaceFabricNode(BaseModel):
    id: str
    name: SubmitCVWorkspaceValueField | None


SubmitCVWorkspaceQuery.model_rebuild()
SubmitCVWorkspaceNetworkFabric.model_rebuild()
SubmitCVWorkspaceNetworkFabricEdge.model_rebuild()
SubmitCVWorkspaceNetworkFabricNode.model_rebuild()
SubmitCVWorkspaceCvWorkspace.model_rebuild()
SubmitCVWorkspaceCvWorkspaceEdge.model_rebuild()
SubmitCVWorkspaceCvWorkspaceNode.model_rebuild()
SubmitCVWorkspaceCvWorkspaceFabric.model_rebuild()
SubmitCVWorkspaceCvWorkspaceFabricNode.model_rebuild()
