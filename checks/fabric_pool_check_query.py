from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class FabricPoolCheckQuery(BaseModel):
    network_fabric: "FabricPoolCheckQueryNetworkFabric" = Field(alias="NetworkFabric")
    network_link: "FabricPoolCheckQueryNetworkLink" = Field(alias="NetworkLink")
    network_pod: "FabricPoolCheckQueryNetworkPod" = Field(alias="NetworkPod")


class FabricPoolCheckQueryNetworkFabric(BaseModel):
    edges: list["FabricPoolCheckQueryNetworkFabricEdges"]


class FabricPoolCheckQueryNetworkFabricEdges(BaseModel):
    node: Optional["FabricPoolCheckQueryNetworkFabricEdgesNode"]


class FabricPoolCheckQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["FabricPoolCheckQueryNetworkFabricEdgesNodeName"]
    underlay_routing_protocol: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol"
    ]
    overlay_routing_protocol: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeOverlayRoutingProtocol"
    ]
    fabric_ip_pools: "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPools"


class FabricPoolCheckQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeUnderlayRoutingProtocol(BaseModel):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeOverlayRoutingProtocol(BaseModel):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPools(BaseModel):
    edges: Optional[
        list["FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdges"]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreResourcePool",
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool",
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreResourcePool(
    BaseModel
):
    typename__: Literal["CoreNumberPool", "CoreResourcePool"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    display_label: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool(
    BaseModel
):
    typename__: Literal["CoreIPAddressPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources"


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool(
    BaseModel
):
    typename__: Literal["CoreIPPrefixPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources"


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkLink(BaseModel):
    edges: list["FabricPoolCheckQueryNetworkLinkEdges"]


class FabricPoolCheckQueryNetworkLinkEdges(BaseModel):
    node: Optional["FabricPoolCheckQueryNetworkLinkEdgesNode"]


class FabricPoolCheckQueryNetworkLinkEdgesNode(BaseModel):
    id: str


class FabricPoolCheckQueryNetworkPod(BaseModel):
    edges: list["FabricPoolCheckQueryNetworkPodEdges"]


class FabricPoolCheckQueryNetworkPodEdges(BaseModel):
    node: Optional["FabricPoolCheckQueryNetworkPodEdgesNode"]


class FabricPoolCheckQueryNetworkPodEdgesNode(BaseModel):
    id: str
    name: Optional["FabricPoolCheckQueryNetworkPodEdgesNodeName"]
    parent: "FabricPoolCheckQueryNetworkPodEdgesNodeParent"
    pod_ip_pools: "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPools"


class FabricPoolCheckQueryNetworkPodEdgesNodeName(BaseModel):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlock",
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkBuildingBlock(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabric(BaseModel):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional["FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricName"]
    fabric_ip_pools: (
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPools"
    )


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricName(BaseModel):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPools(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreResourcePool",
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPool",
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPool",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreResourcePool(
    BaseModel
):
    typename__: Literal["CoreNumberPool", "CoreResourcePool"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    display_label: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPool(
    BaseModel
):
    typename__: Literal["CoreIPAddressPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResources"


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPool(
    BaseModel
):
    typename__: Literal["CoreIPPrefixPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources"


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPools(BaseModel):
    edges: Optional[list["FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdges"]]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreResourcePool",
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPool",
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPool",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreResourcePool(
    BaseModel
):
    typename__: Literal["CoreNumberPool", "CoreResourcePool"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    display_label: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPool(
    BaseModel
):
    typename__: Literal["CoreIPAddressPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResources"


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPool(
    BaseModel
):
    typename__: Literal["CoreIPPrefixPool"] = Field(alias="__typename")
    id: str
    display_label: Optional[str]
    name: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolName"
    ]
    resources: "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResources"


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolName(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResources(
    BaseModel
):
    edges: Optional[
        list[
            "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges"
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix",
                "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeBuiltinIPPrefix(
    BaseModel
):
    typename__: Literal["BuiltinIPPrefix", "InternalIPPrefixAvailable"] = Field(
        alias="__typename"
    )


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix(
    BaseModel
):
    typename__: Literal["IpamPrefix"] = Field(alias="__typename")
    prefix: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix"
    ]
    role: Optional[
        "FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole"
    ]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixPrefix(
    BaseModel
):
    value: Optional[str]


class FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefixRole(
    BaseModel
):
    value: Optional[str]


FabricPoolCheckQuery.model_rebuild()
FabricPoolCheckQueryNetworkFabric.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdges.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNode.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPools.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdges.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPool.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPool.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkFabricEdgesNodeFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricPoolCheckQueryNetworkLink.model_rebuild()
FabricPoolCheckQueryNetworkLinkEdges.model_rebuild()
FabricPoolCheckQueryNetworkPod.model_rebuild()
FabricPoolCheckQueryNetworkPodEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNode.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParent.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabric.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPools.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPool.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPool.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodeParentNodeNetworkFabricFabricIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPools.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPool.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPAddressPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPool.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResources.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdges.model_rebuild()
FabricPoolCheckQueryNetworkPodEdgesNodePodIpPoolsEdgesNodeCoreIPPrefixPoolResourcesEdgesNodeIpamPrefix.model_rebuild()
