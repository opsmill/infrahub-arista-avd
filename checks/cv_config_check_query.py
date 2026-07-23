from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CVConfigCheckQuery(BaseModel):
    network_fabric: "CVConfigCheckQueryNetworkFabric" = Field(alias="NetworkFabric")
    dcim_device: "CVConfigCheckQueryDcimDevice" = Field(alias="DcimDevice")


class CVConfigCheckQueryNetworkFabric(BaseModel):
    edges: list["CVConfigCheckQueryNetworkFabricEdges"]


class CVConfigCheckQueryNetworkFabricEdges(BaseModel):
    node: Optional["CVConfigCheckQueryNetworkFabricEdgesNode"]


class CVConfigCheckQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["CVConfigCheckQueryNetworkFabricEdgesNodeName"]
    cloudvision_managed: Optional[
        "CVConfigCheckQueryNetworkFabricEdgesNodeCloudvisionManaged"
    ]


class CVConfigCheckQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class CVConfigCheckQueryNetworkFabricEdgesNodeCloudvisionManaged(BaseModel):
    value: Optional[bool]


class CVConfigCheckQueryDcimDevice(BaseModel):
    edges: list["CVConfigCheckQueryDcimDeviceEdges"]


class CVConfigCheckQueryDcimDeviceEdges(BaseModel):
    node: Optional["CVConfigCheckQueryDcimDeviceEdgesNode"]


class CVConfigCheckQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["CVConfigCheckQueryDcimDeviceEdgesNodeName"]
    serial: Optional["CVConfigCheckQueryDcimDeviceEdgesNodeSerial"]
    pod: "CVConfigCheckQueryDcimDeviceEdgesNodePod"
    avd_artifact: "CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifact"


class CVConfigCheckQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class CVConfigCheckQueryDcimDeviceEdgesNodeSerial(BaseModel):
    value: Optional[str]


class CVConfigCheckQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["CVConfigCheckQueryDcimDeviceEdgesNodePodNode"]


class CVConfigCheckQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: "CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParent"


class CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional["CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParentNode"]


class CVConfigCheckQueryDcimDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNode"]


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    structured_config_file: (
        "CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile"
    )


class CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile(
    BaseModel
):
    node: Optional[
        "CVConfigCheckQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode"
    ]


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
