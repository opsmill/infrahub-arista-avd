from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class RackGeneratorQuery(BaseModel):
    location_rack: "RackGeneratorQueryLocationRack" = Field(alias="LocationRack")


class RackGeneratorQueryLocationRack(BaseModel):
    edges: list["RackGeneratorQueryLocationRackEdges"]


class RackGeneratorQueryLocationRackEdges(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNode"]


class RackGeneratorQueryLocationRackEdgesNode(BaseModel):
    id: str
    name: Optional["RackGeneratorQueryLocationRackEdgesNodeName"]
    checksum: Optional["RackGeneratorQueryLocationRackEdgesNodeChecksum"]
    index: Optional["RackGeneratorQueryLocationRackEdgesNodeIndex"]
    rack_type: Optional["RackGeneratorQueryLocationRackEdgesNodeRackType"]
    amount_of_leafs: Optional["RackGeneratorQueryLocationRackEdgesNodeAmountOfLeafs"]
    leaf_switch_template: "RackGeneratorQueryLocationRackEdgesNodeLeafSwitchTemplate"
    amount_of_l_2_leafs: Optional[
        "RackGeneratorQueryLocationRackEdgesNodeAmountOfL2Leafs"
    ] = Field(alias="amount_of_l2leafs")
    l_2_leaf_switch_template: "RackGeneratorQueryLocationRackEdgesNodeL2LeafSwitchTemplate" = Field(
        alias="l2leaf_switch_template"
    )
    parent: "RackGeneratorQueryLocationRackEdgesNodeParent"
    pod: "RackGeneratorQueryLocationRackEdgesNodePod"


class RackGeneratorQueryLocationRackEdgesNodeName(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeChecksum(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeIndex(BaseModel):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodeRackType(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeAmountOfLeafs(BaseModel):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodeLeafSwitchTemplate(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodeLeafSwitchTemplateNode"]


class RackGeneratorQueryLocationRackEdgesNodeLeafSwitchTemplateNode(BaseModel):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeAmountOfL2Leafs(BaseModel):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodeL2LeafSwitchTemplate(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodeL2LeafSwitchTemplateNode"]


class RackGeneratorQueryLocationRackEdgesNodeL2LeafSwitchTemplateNode(BaseModel):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeParent(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodeParentNode"]


class RackGeneratorQueryLocationRackEdgesNodeParentNode(BaseModel):
    typename__: Literal["LocationGeneric", "LocationHall", "LocationRack"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional["RackGeneratorQueryLocationRackEdgesNodeParentNodeName"]


class RackGeneratorQueryLocationRackEdgesNodeParentNodeName(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePod(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodePodNode"]


class RackGeneratorQueryLocationRackEdgesNodePodNode(BaseModel):
    id: str
    name: Optional["RackGeneratorQueryLocationRackEdgesNodePodNodeName"]
    index: Optional["RackGeneratorQueryLocationRackEdgesNodePodNodeIndex"]
    prefix_pool: "RackGeneratorQueryLocationRackEdgesNodePodNodePrefixPool"
    loopback_pool: "RackGeneratorQueryLocationRackEdgesNodePodNodeLoopbackPool"
    amount_of_spines: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeAmountOfSpines"
    ]
    leaf_interface_sorting_method: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeLeafInterfaceSortingMethod"
    ]
    spine_interface_sorting_method: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeSpineInterfaceSortingMethod"
    ]
    parent: "RackGeneratorQueryLocationRackEdgesNodePodNodeParent"


class RackGeneratorQueryLocationRackEdgesNodePodNodeName(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeIndex(BaseModel):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodePodNodePrefixPool(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodePodNodePrefixPoolNode"]


class RackGeneratorQueryLocationRackEdgesNodePodNodePrefixPoolNode(BaseModel):
    id: str


class RackGeneratorQueryLocationRackEdgesNodePodNodeLoopbackPool(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodePodNodeLoopbackPoolNode"]


class RackGeneratorQueryLocationRackEdgesNodePodNodeLoopbackPoolNode(BaseModel):
    id: str


class RackGeneratorQueryLocationRackEdgesNodePodNodeAmountOfSpines(BaseModel):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodePodNodeLeafInterfaceSortingMethod(
    BaseModel
):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeSpineInterfaceSortingMethod(
    BaseModel
):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkBuildingBlock",
                "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabric(BaseModel):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    asn_pool: (
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPool"
    )
    node_id_pool: "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPool"
    mgmt_pool: (
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPool"
    )


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPool(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPoolNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPoolNode(
    BaseModel
):
    id: str


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPool(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPoolNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPoolNode(
    BaseModel
):
    id: str


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPool(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPoolNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPoolNode(
    BaseModel
):
    id: str


RackGeneratorQuery.model_rebuild()
RackGeneratorQueryLocationRack.model_rebuild()
RackGeneratorQueryLocationRackEdges.model_rebuild()
RackGeneratorQueryLocationRackEdgesNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeLeafSwitchTemplate.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeL2LeafSwitchTemplate.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeParent.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeParentNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePod.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodePrefixPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeLoopbackPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParent.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPool.model_rebuild()
