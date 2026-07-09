from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CVConfigCheckQuery(BaseModel):
    network_fabric: CVConfigCheckNetworkFabric = Field(alias="NetworkFabric")
    dcim_device: CVConfigCheckDcimDevice = Field(alias="DcimDevice")


class CVConfigCheckNetworkFabric(BaseModel):
    edges: list[CVConfigCheckNetworkFabricEdge]


class CVConfigCheckNetworkFabricEdge(BaseModel):
    node: CVConfigCheckNetworkFabricNode | None


class CVConfigCheckNetworkFabricNode(BaseModel):
    id: str
    name: CVConfigCheckValueField | None


class CVConfigCheckDcimDevice(BaseModel):
    edges: list[CVConfigCheckDcimDeviceEdge]


class CVConfigCheckDcimDeviceEdge(BaseModel):
    node: CVConfigCheckDcimDeviceNode | None


class CVConfigCheckDcimDeviceNode(BaseModel):
    id: str
    name: CVConfigCheckValueField | None
    serial: CVConfigCheckValueField | None
    pod: CVConfigCheckDevicePod | None
    avd_artifact: CVConfigCheckDeviceAvdArtifact | None


class CVConfigCheckValueField(BaseModel):
    value: str | None


class CVConfigCheckDevicePod(BaseModel):
    node: CVConfigCheckDevicePodNode | None


class CVConfigCheckDevicePodNode(BaseModel):
    id: str
    parent: CVConfigCheckDevicePodParent | None


class CVConfigCheckDevicePodParent(BaseModel):
    node: CVConfigCheckDevicePodParentNode | None


class CVConfigCheckDevicePodParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(alias="__typename")
    id: str | None


class CVConfigCheckDeviceAvdArtifact(BaseModel):
    node: CVConfigCheckDeviceAvdArtifactNode | None


class CVConfigCheckDeviceAvdArtifactNode(BaseModel):
    id: str
    structured_config_file: CVConfigCheckDeviceStructuredConfigFile | None


class CVConfigCheckDeviceStructuredConfigFile(BaseModel):
    node: CVConfigCheckDeviceStructuredConfigFileNode | None


class CVConfigCheckDeviceStructuredConfigFileNode(BaseModel):
    id: str


CVConfigCheckQuery.model_rebuild()
CVConfigCheckNetworkFabric.model_rebuild()
CVConfigCheckNetworkFabricEdge.model_rebuild()
CVConfigCheckNetworkFabricNode.model_rebuild()
CVConfigCheckDcimDevice.model_rebuild()
CVConfigCheckDcimDeviceEdge.model_rebuild()
CVConfigCheckDcimDeviceNode.model_rebuild()
CVConfigCheckDevicePod.model_rebuild()
CVConfigCheckDevicePodNode.model_rebuild()
CVConfigCheckDevicePodParent.model_rebuild()
CVConfigCheckDevicePodParentNode.model_rebuild()
CVConfigCheckDeviceAvdArtifact.model_rebuild()
CVConfigCheckDeviceAvdArtifactNode.model_rebuild()
CVConfigCheckDeviceStructuredConfigFile.model_rebuild()
CVConfigCheckDeviceStructuredConfigFileNode.model_rebuild()
