from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AvdFabricDevicesQuery(BaseModel):
    network_fabric: "AvdFabricDevicesQueryNetworkFabric" = Field(alias="NetworkFabric")
    dcim_device: "AvdFabricDevicesQueryDcimDevice" = Field(alias="DcimDevice")


class AvdFabricDevicesQueryNetworkFabric(BaseModel):
    edges: list["AvdFabricDevicesQueryNetworkFabricEdges"]


class AvdFabricDevicesQueryNetworkFabricEdges(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkFabricEdgesNode"]


class AvdFabricDevicesQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["AvdFabricDevicesQueryNetworkFabricEdgesNodeName"]


class AvdFabricDevicesQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdFabricDevicesQueryDcimDevice(BaseModel):
    edges: list["AvdFabricDevicesQueryDcimDeviceEdges"]


class AvdFabricDevicesQueryDcimDeviceEdges(BaseModel):
    node: Optional["AvdFabricDevicesQueryDcimDeviceEdgesNode"]


class AvdFabricDevicesQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["AvdFabricDevicesQueryDcimDeviceEdgesNodeName"]
    pod: "AvdFabricDevicesQueryDcimDeviceEdgesNodePod"
    avd_artifact: "AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifact"


class AvdFabricDevicesQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdFabricDevicesQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["AvdFabricDevicesQueryDcimDeviceEdgesNodePodNode"]


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: "AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParent"


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional["AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParentNode"]


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNode"]


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    hostvar_file: "AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeHostvarFile"
    structured_config_file: (
        "AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile"
    )


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeHostvarFile(BaseModel):
    node: Optional[
        "AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeHostvarFileNode"
    ]


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeHostvarFileNode(BaseModel):
    id: str


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile(
    BaseModel
):
    node: Optional[
        "AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode"
    ]


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode(
    BaseModel
):
    id: str


AvdFabricDevicesQuery.model_rebuild()
AvdFabricDevicesQueryNetworkFabric.model_rebuild()
AvdFabricDevicesQueryNetworkFabricEdges.model_rebuild()
AvdFabricDevicesQueryNetworkFabricEdgesNode.model_rebuild()
AvdFabricDevicesQueryDcimDevice.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdges.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNode.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodePod.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodePodNode.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNode.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeHostvarFile.model_rebuild()
AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile.model_rebuild()
