from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CVConfigCheckQuery(BaseModel):
    network_fabric: CVConfigCheckQueryNetworkFabric = Field(alias="NetworkFabric")
    dcim_device: CVConfigCheckQueryDcimDevice = Field(alias="DcimDevice")


class CVConfigCheckQueryNetworkFabric(BaseModel):
    edges: list[CVConfigCheckQueryNetworkFabricEdges]


class CVConfigCheckQueryNetworkFabricEdges(BaseModel):
    node: CVConfigCheckQueryNetworkFabricEdgesNode | None


class CVConfigCheckQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: CVConfigCheckQueryNetworkFabricEdgesNodeName | None
    cloudvision_managed: CVConfigCheckQueryNetworkFabricEdgesNodeCloudvisionManaged | None


class CVConfigCheckQueryNetworkFabricEdgesNodeName(BaseModel):
    value: str | None


class CVConfigCheckQueryNetworkFabricEdgesNodeCloudvisionManaged(BaseModel):
    value: bool | None


class CVConfigCheckQueryDcimDevice(BaseModel):
    edges: list[CVConfigCheckQueryDcimDeviceEdges]


class CVConfigCheckQueryDcimDeviceEdges(BaseModel):
    node: CVConfigCheckQueryDcimDeviceEdgesNode | None


class CVConfigCheckQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: CVConfigCheckQueryDcimDeviceEdgesNodeName | None
    serial: CVConfigCheckQueryDcimDeviceEdgesNodeSerial | None
    pod: CVConfigCheckQueryDcimDeviceEdgesNodePod
    avd_artifact: CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifact


class CVConfigCheckQueryDcimDeviceEdgesNodeName(BaseModel):
    value: str | None


class CVConfigCheckQueryDcimDeviceEdgesNodeSerial(BaseModel):
    value: str | None


class CVConfigCheckQueryDcimDeviceEdgesNodePod(BaseModel):
    node: CVConfigCheckQueryDcimDeviceEdgesNodePodNode | None


class CVConfigCheckQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParent


class CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParentNode | None


class CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: str | None


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNode | None


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    structured_config_file: (
        CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile
    )


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile(
    BaseModel
):
    node: CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode | None


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode(
    BaseModel
):
    id: str


CVConfigCheckQuery.model_rebuild()
CVConfigCheckQueryNetworkFabric.model_rebuild()
CVConfigCheckQueryNetworkFabricEdges.model_rebuild()
CVConfigCheckQueryNetworkFabricEdgesNode.model_rebuild()
CVConfigCheckQueryDcimDevice.model_rebuild()
CVConfigCheckQueryDcimDeviceEdges.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNode.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodePod.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodePodNode.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifact.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNode.model_rebuild()
CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile.model_rebuild()
