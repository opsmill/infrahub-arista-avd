from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class AvdAntaCatalogQuery(BaseModel):
    anta_fabrics: "AvdAntaCatalogQueryAntaFabrics"
    target: "AvdAntaCatalogQueryTarget"
    dcim_device: "AvdAntaCatalogQueryDcimDevice" = Field(alias="DcimDevice")


class AvdAntaCatalogQueryAntaFabrics(BaseModel):
    edges: list["AvdAntaCatalogQueryAntaFabricsEdges"]


class AvdAntaCatalogQueryAntaFabricsEdges(BaseModel):
    node: Optional["AvdAntaCatalogQueryAntaFabricsEdgesNode"]


class AvdAntaCatalogQueryAntaFabricsEdgesNode(BaseModel):
    id: str
    anta_enabled: Optional["AvdAntaCatalogQueryAntaFabricsEdgesNodeAntaEnabled"]
    avd_catalogs_filters: Optional[
        "AvdAntaCatalogQueryAntaFabricsEdgesNodeAvdCatalogsFilters"
    ]


class AvdAntaCatalogQueryAntaFabricsEdgesNodeAntaEnabled(BaseModel):
    value: Optional[bool]


class AvdAntaCatalogQueryAntaFabricsEdgesNodeAvdCatalogsFilters(BaseModel):
    value: Optional[Any]


class AvdAntaCatalogQueryTarget(BaseModel):
    edges: list["AvdAntaCatalogQueryTargetEdges"]


class AvdAntaCatalogQueryTargetEdges(BaseModel):
    node: Optional["AvdAntaCatalogQueryTargetEdgesNode"]


class AvdAntaCatalogQueryTargetEdgesNode(BaseModel):
    id: str
    name: Optional["AvdAntaCatalogQueryTargetEdgesNodeName"]
    pod: "AvdAntaCatalogQueryTargetEdgesNodePod"


class AvdAntaCatalogQueryTargetEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdAntaCatalogQueryTargetEdgesNodePod(BaseModel):
    node: Optional["AvdAntaCatalogQueryTargetEdgesNodePodNode"]


class AvdAntaCatalogQueryTargetEdgesNodePodNode(BaseModel):
    id: str
    parent: "AvdAntaCatalogQueryTargetEdgesNodePodNodeParent"


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkBuildingBlock",
                "AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabric(BaseModel):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional[
        "AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricName"
    ]
    anta_enabled: Optional[
        "AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricAntaEnabled"
    ]
    avd_catalogs_filters: Optional[
        "AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricAvdCatalogsFilters"
    ]


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricName(BaseModel):
    value: Optional[str]


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricAntaEnabled(
    BaseModel
):
    value: Optional[bool]


class AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabricAvdCatalogsFilters(
    BaseModel
):
    value: Optional[Any]


class AvdAntaCatalogQueryDcimDevice(BaseModel):
    edges: list["AvdAntaCatalogQueryDcimDeviceEdges"]


class AvdAntaCatalogQueryDcimDeviceEdges(BaseModel):
    node: Optional["AvdAntaCatalogQueryDcimDeviceEdgesNode"]


class AvdAntaCatalogQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["AvdAntaCatalogQueryDcimDeviceEdgesNodeName"]
    pod: "AvdAntaCatalogQueryDcimDeviceEdgesNodePod"
    avd_artifact: "AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifact"


class AvdAntaCatalogQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdAntaCatalogQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["AvdAntaCatalogQueryDcimDeviceEdgesNodePodNode"]


class AvdAntaCatalogQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    parent: "AvdAntaCatalogQueryDcimDeviceEdgesNodePodNodeParent"


class AvdAntaCatalogQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional["AvdAntaCatalogQueryDcimDeviceEdgesNodePodNodeParentNode"]


class AvdAntaCatalogQueryDcimDeviceEdgesNodePodNodeParentNode(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNode"]


class AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    structured_config_file: (
        "AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile"
    )


class AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile(
    BaseModel
):
    node: Optional[
        "AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode"
    ]


class AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFileNode(
    BaseModel
):
    id: str


AvdAntaCatalogQuery.model_rebuild()
AvdAntaCatalogQueryAntaFabrics.model_rebuild()
AvdAntaCatalogQueryAntaFabricsEdges.model_rebuild()
AvdAntaCatalogQueryAntaFabricsEdgesNode.model_rebuild()
AvdAntaCatalogQueryTarget.model_rebuild()
AvdAntaCatalogQueryTargetEdges.model_rebuild()
AvdAntaCatalogQueryTargetEdgesNode.model_rebuild()
AvdAntaCatalogQueryTargetEdgesNodePod.model_rebuild()
AvdAntaCatalogQueryTargetEdgesNodePodNode.model_rebuild()
AvdAntaCatalogQueryTargetEdgesNodePodNodeParent.model_rebuild()
AvdAntaCatalogQueryTargetEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
AvdAntaCatalogQueryDcimDevice.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdges.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNode.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodePod.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodePodNode.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNode.model_rebuild()
AvdAntaCatalogQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigFile.model_rebuild()
