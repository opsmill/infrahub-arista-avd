from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BackfillStructuredConfigQuery(BaseModel):
    avd_artifact: BackfillStructuredConfigQueryAvdArtifact = Field(alias="AvdArtifact")


class BackfillStructuredConfigQueryAvdArtifact(BaseModel):
    edges: list[BackfillStructuredConfigQueryAvdArtifactEdges]


class BackfillStructuredConfigQueryAvdArtifactEdges(BaseModel):
    node: BackfillStructuredConfigQueryAvdArtifactEdgesNode | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNode(BaseModel):
    id: str
    structured_config_file: BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigFile
    device: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigFile(BaseModel):
    node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigFileNode | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigFileNode(BaseModel):
    id: str


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice(BaseModel):
    node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode(BaseModel):
    id: str
    name: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeName | None
    role: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeRole | None
    interfaces: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeName(BaseModel):
    value: str | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeRole(BaseModel):
    value: str | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces(BaseModel):
    edges: list[BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges] | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges(BaseModel):
    node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode(BaseModel):
    typename__: Literal["DcimInterface", "InterfacePhysical", "InterfaceVirtual"] = Field(alias="__typename")
    id: str | None
    name: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeName | None
    role: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeRole | None
    mtu: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeMtu | None
    ip_address: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeName(BaseModel):
    value: str | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeRole(BaseModel):
    value: str | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeMtu(BaseModel):
    value: Any | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress(BaseModel):
    node: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode(BaseModel):
    id: str
    address: BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNodeAddress | None


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNodeAddress(BaseModel):
    value: str | None


BackfillStructuredConfigQuery.model_rebuild()
BackfillStructuredConfigQueryAvdArtifact.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdges.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigFile.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode.model_rebuild()
