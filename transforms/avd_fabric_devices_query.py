from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AvdFabricDevicesQuery(BaseModel):
    network_fabric: AvdFabricDevicesQueryNetworkFabric = Field(alias="NetworkFabric")
    dcim_device: AvdFabricDevicesQueryDcimDevice = Field(alias="DcimDevice")


class AvdFabricDevicesQueryNetworkFabric(BaseModel):
    edges: list[AvdFabricDevicesQueryNetworkFabricEdges]


class AvdFabricDevicesQueryNetworkFabricEdges(BaseModel):
    node: AvdFabricDevicesQueryNetworkFabricEdgesNode | None


class AvdFabricDevicesQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: AvdFabricDevicesQueryNetworkFabricEdgesNodeName | None


class AvdFabricDevicesQueryNetworkFabricEdgesNodeName(BaseModel):
    value: str | None


class AvdFabricDevicesQueryDcimDevice(BaseModel):
    edges: list[AvdFabricDevicesQueryDcimDeviceEdges]


class AvdFabricDevicesQueryDcimDeviceEdges(BaseModel):
    node: AvdFabricDevicesQueryDcimDeviceEdgesNode | None


class AvdFabricDevicesQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: AvdFabricDevicesQueryDcimDeviceEdgesNodeName | None
    pod: AvdFabricDevicesQueryDcimDeviceEdgesNodePod
    avd_artifact: AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifact


class AvdFabricDevicesQueryDcimDeviceEdgesNodeName(BaseModel):
    value: str | None


class AvdFabricDevicesQueryDcimDeviceEdgesNodePod(BaseModel):
    node: AvdFabricDevicesQueryDcimDeviceEdgesNodePodNode | None


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParent


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParentNode | None


class AvdFabricDevicesQueryDcimDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(alias="__typename")
    id: str | None


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNode | None


class AvdFabricDevicesQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    hostvar_file: AvdFabricDevicesQueryFileRef
    structured_config_file: AvdFabricDevicesQueryFileRef


class AvdFabricDevicesQueryFileRef(BaseModel):
    node: AvdFabricDevicesQueryFileRefNode | None


class AvdFabricDevicesQueryFileRefNode(BaseModel):
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
AvdFabricDevicesQueryFileRef.model_rebuild()
