from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AvdFabricDevicesQuery(BaseModel):
    network_fabric: "AvdFabricDevicesQueryNetworkFabric" = Field(alias="NetworkFabric")
    network_device: "AvdFabricDevicesQueryNetworkDevice" = Field(alias="NetworkDevice")


class AvdFabricDevicesQueryNetworkFabric(BaseModel):
    edges: list["AvdFabricDevicesQueryNetworkFabricEdges"]


class AvdFabricDevicesQueryNetworkFabricEdges(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkFabricEdgesNode"]


class AvdFabricDevicesQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["AvdFabricDevicesQueryNetworkFabricEdgesNodeName"]


class AvdFabricDevicesQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdFabricDevicesQueryNetworkDevice(BaseModel):
    edges: list["AvdFabricDevicesQueryNetworkDeviceEdges"]


class AvdFabricDevicesQueryNetworkDeviceEdges(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNode"]


class AvdFabricDevicesQueryNetworkDeviceEdgesNode(BaseModel):
    id: str
    hostname: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNodeHostname"]
    pod: "AvdFabricDevicesQueryNetworkDeviceEdgesNodePod"
    avd_artifact: "AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifact"


class AvdFabricDevicesQueryNetworkDeviceEdgesNodeHostname(BaseModel):
    value: Optional[str]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodePod(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNode"]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: "AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNodeParent"


class AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNodeParentNode"]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(alias="__typename")
    id: Optional[str]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNode"]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNode(BaseModel):
    hostvar_identifier: Optional["AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNodeHostvarIdentifier"]
    structured_config_identifier: Optional[
        "AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier"
    ]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNodeHostvarIdentifier(BaseModel):
    value: Optional[str]


class AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier(BaseModel):
    value: Optional[str]


AvdFabricDevicesQuery.model_rebuild()
AvdFabricDevicesQueryNetworkFabric.model_rebuild()
AvdFabricDevicesQueryNetworkFabricEdges.model_rebuild()
AvdFabricDevicesQueryNetworkFabricEdgesNode.model_rebuild()
AvdFabricDevicesQueryNetworkDevice.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdges.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNode.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNodePod.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNode.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNodePodNodeParent.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNode.model_rebuild()
