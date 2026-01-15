from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class PodGeneratorQuery(BaseModel):
    network_pod: "PodGeneratorQueryNetworkPod" = Field(alias="NetworkPod")


class PodGeneratorQueryNetworkPod(BaseModel):
    edges: list["PodGeneratorQueryNetworkPodEdges"]


class PodGeneratorQueryNetworkPodEdges(BaseModel):
    node: Optional["PodGeneratorQueryNetworkPodEdgesNode"]


class PodGeneratorQueryNetworkPodEdgesNode(BaseModel):
    id: str
    amount_of_spines: Optional["PodGeneratorQueryNetworkPodEdgesNodeAmountOfSpines"]
    name: Optional["PodGeneratorQueryNetworkPodEdgesNodeName"]
    checksum: Optional["PodGeneratorQueryNetworkPodEdgesNodeChecksum"]
    index: Optional["PodGeneratorQueryNetworkPodEdgesNodeIndex"]
    role: Optional["PodGeneratorQueryNetworkPodEdgesNodeRole"]
    spine_switch_template: "PodGeneratorQueryNetworkPodEdgesNodeSpineSwitchTemplate"
    parent: "PodGeneratorQueryNetworkPodEdgesNodeParent"


class PodGeneratorQueryNetworkPodEdgesNodeAmountOfSpines(BaseModel):
    value: Optional[Any]


class PodGeneratorQueryNetworkPodEdgesNodeName(BaseModel):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeChecksum(BaseModel):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeIndex(BaseModel):
    value: Optional[Any]


class PodGeneratorQueryNetworkPodEdgesNodeRole(BaseModel):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeSpineSwitchTemplate(BaseModel):
    node: Optional["PodGeneratorQueryNetworkPodEdgesNodeSpineSwitchTemplateNode"]


class PodGeneratorQueryNetworkPodEdgesNodeSpineSwitchTemplateNode(BaseModel):
    typename__: Literal["CoreObjectTemplate", "TemplateNetworkDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlock",
                "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlock(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlockName"
    ]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlockName(BaseModel):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabric(BaseModel):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional["PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricName"]
    amount_of_super_spines: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAmountOfSuperSpines"
    ]
    fabric_interface_sorting_method: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricInterfaceSortingMethod"
    ]
    spine_interface_sorting_method: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricSpineInterfaceSortingMethod"
    ]
    asn_pool: "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAsnPool"
    node_id_pool: (
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricNodeIdPool"
    )
    mgmt_pool: "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricMgmtPool"


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricName(BaseModel):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAmountOfSuperSpines(
    BaseModel
):
    value: Optional[Any]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricInterfaceSortingMethod(
    BaseModel
):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricSpineInterfaceSortingMethod(
    BaseModel
):
    value: Optional[str]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAsnPool(BaseModel):
    node: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAsnPoolNode"
    ]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAsnPoolNode(BaseModel):
    id: str


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricNodeIdPool(BaseModel):
    node: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricNodeIdPoolNode"
    ]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricNodeIdPoolNode(
    BaseModel
):
    id: str


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricMgmtPool(BaseModel):
    node: Optional[
        "PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricMgmtPoolNode"
    ]


class PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricMgmtPoolNode(
    BaseModel
):
    id: str


PodGeneratorQuery.model_rebuild()
PodGeneratorQueryNetworkPod.model_rebuild()
PodGeneratorQueryNetworkPodEdges.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNode.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeSpineSwitchTemplate.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParent.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlock.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabric.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricAsnPool.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricNodeIdPool.model_rebuild()
PodGeneratorQueryNetworkPodEdgesNodeParentNodeNetworkFabricMgmtPool.model_rebuild()
