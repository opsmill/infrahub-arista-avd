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
    mlag: Optional["RackGeneratorQueryLocationRackEdgesNodeMlag"]
    device_designs: "RackGeneratorQueryLocationRackEdgesNodeDeviceDesigns"
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


class RackGeneratorQueryLocationRackEdgesNodeMlag(BaseModel):
    value: Optional[bool]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesigns(BaseModel):
    edges: list["RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdges"]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdges(BaseModel):
    node: Optional["RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNode"]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNode(BaseModel):
    role: Optional["RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeRole"]
    device_quantity: Optional[
        "RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceQuantity"
    ]
    device_template: (
        "RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate"
    )


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeRole(BaseModel):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceQuantity(
    BaseModel
):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceTemplateNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceTemplateNode(
    BaseModel
):
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
    device_designs: "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesigns"
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


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesigns(BaseModel):
    edges: list["RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdges"]


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdges(BaseModel):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNode(BaseModel):
    role: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeRole"
    ]
    device_quantity: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceQuantity"
    ]
    device_template: "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceTemplate"


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceQuantity(
    BaseModel
):
    value: Optional[Any]


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceTemplate(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceTemplateNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceTemplateNode(
    BaseModel
):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: Optional[str]


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
    name: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricName"
    ]
    underlay_routing_protocol: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol"
    ]
    asn_pool: (
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPool"
    )
    node_id_pool: "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPool"
    mgmt_pool: (
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPool"
    )
    vtep_pool: (
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPool"
    )
    loopback_pool: "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool"


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol(
    BaseModel
):
    value: Optional[str]


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


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPool(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode(
    BaseModel
):
    id: str
    resources: "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResources"


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResources(
    BaseModel
):
    edges: Optional[
        list[
            "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResourcesEdges"
        ]
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResourcesEdges(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResourcesEdgesNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode(
    BaseModel
):
    id: str
    resources: "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResources"


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResources(
    BaseModel
):
    edges: Optional[
        list[
            "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResourcesEdges"
        ]
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResourcesEdges(
    BaseModel
):
    node: Optional[
        "RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResourcesEdgesNode"
    ]


class RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


RackGeneratorQuery.model_rebuild()
RackGeneratorQueryLocationRack.model_rebuild()
RackGeneratorQueryLocationRackEdges.model_rebuild()
RackGeneratorQueryLocationRackEdgesNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeDeviceDesigns.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdges.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeParent.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodeParentNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePod.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesigns.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdges.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeDeviceDesignsEdgesNodeDeviceTemplate.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParent.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricAsnPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricNodeIdPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricMgmtPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResources.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeResourcesEdges.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResources.model_rebuild()
RackGeneratorQueryLocationRackEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeResourcesEdges.model_rebuild()
