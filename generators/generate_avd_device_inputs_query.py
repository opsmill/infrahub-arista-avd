from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class GenerateAvdDeviceInputsQuery(BaseModel):
    dcim_device: "GenerateAvdDeviceInputsQueryDcimDevice" = Field(alias="DcimDevice")


class GenerateAvdDeviceInputsQueryDcimDevice(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryDcimDeviceEdges"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdges(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName"]
    role: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole"]
    bgp_asn: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeBgpAsn"]
    node_id: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId"]
    loopback_ip: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp"
    mgmt_ip: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp"
    mlag_domain: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain"] = None
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod"
    interfaces: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeBgpAsn(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode(BaseModel):
    id: str
    address: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode(BaseModel):
    id: str
    address: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNodeAddress"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNodeAddress(BaseModel):
    value: Optional[str]


# --- MLAG Domain models ---


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode"] = None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode(BaseModel):
    id: str
    domain_id: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId"] = None
    virtual_router_mac: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac"] = None
    peers: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers"] = None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode"] = None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName"] = None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName(BaseModel):
    value: Optional[str]


# --- Pod models ---


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode"]


class _OptionalNodeRef(BaseModel):
    """Reusable model for optional { node { id, name { value } } } refs."""
    node: Optional["_OptionalNodeRefNode"] = None


class _OptionalNodeRefNode(BaseModel):
    id: str
    name: Optional["_OptionalNodeRefNodeName"] = None


class _OptionalNodeRefNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName"]
    mlag_peer_pool: Optional[_OptionalNodeRef] = None
    mlag_l3_pool: Optional[_OptionalNodeRef] = None
    loopback_ipv4_offset: Optional[_SimpleValue] = None
    parent: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName(
    BaseModel
):
    value: Optional[str]


class _SimpleValue(BaseModel):
    value: Optional[Any]


class _GenericNode(BaseModel):
    """Generic node that accepts any fields from GraphQL."""
    model_config = {"extra": "allow"}


class _GenericNodeEdge(BaseModel):
    node: Optional[_GenericNode] = None


class _EdgesListSimple(BaseModel):
    edges: list[_GenericNodeEdge] = []


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric(
    BaseModel
):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName"
    ]
    mgmt_gateway: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway"
    ]
    mgmt_routes: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes"
    ]
    virtual_router_mac: Optional[_SimpleValue] = None
    underlay_routing_protocol: Optional[_SimpleValue] = None
    overlay_routing_protocol: Optional[_SimpleValue] = None
    p2p_uplinks_mtu: Optional[_SimpleValue] = None
    spanning_tree_mode: Optional[_SimpleValue] = None
    spanning_tree_priority: Optional[_SimpleValue] = None
    bgp_evpn_overlay_password: Optional[_SimpleValue] = None
    bgp_underlay_password: Optional[_SimpleValue] = None
    bgp_mlag_password: Optional[_SimpleValue] = None
    uplink_pool: Optional[_OptionalNodeRef] = None
    vtep_pool: Optional[_OptionalNodeRef] = None
    dns_servers: Optional["_EdgesListSimple"] = None
    ntp_servers: Optional["_EdgesListSimple"] = None
    local_users: Optional["_EdgesListSimple"] = None
    avd_evpn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode(
    BaseModel
):
    ebgp_multihop: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop"
    ]
    overlay_bgp_rtc: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces(BaseModel):
    edges: Optional[
        list["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges"]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDcimInterface",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceVirtual", "InterfaceLag", "MlagInterface"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole"
    ]
    tagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan"
    connector: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]
    connected_endpoints: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName"
    ]
    device: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDevice",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDeviceName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceRole"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    device: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    device: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode.model_rebuild()
_OptionalNodeRef.model_rebuild()
_OptionalNodeRefNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice.model_rebuild()
