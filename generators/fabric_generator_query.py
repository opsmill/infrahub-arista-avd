from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class FabricGeneratorQuery(BaseModel):
    network_fabric: "FabricGeneratorQueryNetworkFabric" = Field(alias="NetworkFabric")


class FabricGeneratorQueryNetworkFabric(BaseModel):
    edges: list["FabricGeneratorQueryNetworkFabricEdges"]


class FabricGeneratorQueryNetworkFabricEdges(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNode"]


class FabricGeneratorQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeName"]
    underlay_routing_protocol: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol"
    ]
    device_designs: "FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesigns"
    mgmt_gateway: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway"]
    asn_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool"
    node_id_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool"
    mgmt_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool"
    fabric_ip_pools: "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPools"
    vtep_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool"
    loopback_pool: "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool"


class FabricGeneratorQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesigns(BaseModel):
    edges: list["FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdges"]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdges(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNode(BaseModel):
    role: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeRole"
    ]
    device_quantity: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceQuantity"
    ]
    device_template: (
        "FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate"
    )


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeRole(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceQuantity(
    BaseModel
):
    value: Optional[Any]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate(
    BaseModel
):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceTemplateNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceTemplateNode(
    BaseModel
):
    typename__: Literal[
        "CoreObjectTemplate", "TemplateComputePhysicalServer", "TemplateDcimDevice"
    ] = Field(alias="__typename")
    id: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtGateway(BaseModel):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeAsnPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPoolNode(BaseModel):
    id: str


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPools(BaseModel):
    edges: Optional[
        list["FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdges"]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreResourcePool",
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool",
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreResourcePool(
    BaseModel
):
    typename__: Literal["CoreNumberPool", "CoreResourcePool"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool(
    BaseModel
):
    typename__: Literal["CoreIPAddressPool"] = Field(alias="__typename")
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges"
        ]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    role: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool(
    BaseModel
):
    typename__: Literal["CoreIPPrefixPool"] = Field(alias="__typename")
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges"
        ]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    role: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode(BaseModel):
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources(BaseModel):
    edges: Optional[
        list["FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges"]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges(BaseModel):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdgesNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool(BaseModel):
    node: Optional["FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode"]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode(BaseModel):
    id: str
    resources: "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources"


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources(BaseModel):
    edges: Optional[
        list["FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges"]
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges(
    BaseModel
):
    node: Optional[
        "FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdgesNode"
    ]


class FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdgesNode(
    BaseModel
):
    typename__: Literal[
        "BuiltinIPPrefix", "InternalIPPrefixAvailable", "IpamPrefix"
    ] = Field(alias="__typename")
    id: Optional[str]


FabricGeneratorQuery.model_rebuild()
FabricGeneratorQueryNetworkFabric.model_rebuild()
FabricGeneratorQueryNetworkFabricEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesigns.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeDeviceDesignsEdgesNodeDeviceTemplate.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeAsnPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeNodeIdPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeMgmtPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPools.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeVtepPoolNodeResourcesEdges.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPool.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNode.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResources.model_rebuild()
FabricGeneratorQueryNetworkFabricEdgesNodeLoopbackPoolNodeResourcesEdges.model_rebuild()
