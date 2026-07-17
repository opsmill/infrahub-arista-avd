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
    asn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn"
    node_id: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId"]
    avd_custom_hostvars: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars"]
    loopback_ip: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp"
    mgmt_ip: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp"
    mlag_domain: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain"
    rack: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRack"
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod"
    interfaces: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNode(BaseModel):
    asn: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNodeAsn"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNodeAsn(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars(BaseModel):
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode(BaseModel):
    id: str
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId"
    ]
    asn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsn"
    virtual_router_mac: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac"
    ]
    peers: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsn(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNode(BaseModel):
    asn: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNodeAsn"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNodeAsn(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers(BaseModel):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRack(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeName"]
    mlag: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeMlag"]
    devices: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevices"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeMlag(BaseModel):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevices(BaseModel):
    edges: Optional[
        list["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdges"]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimPhysicalDevice",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceRole"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName"]
    mlag_peer_pool: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool"
    mlag_l_3_pool: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool" = Field(
        alias="mlag_l3_pool"
    )
    loopback_ipv_4_offset: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeLoopbackIpv4Offset"
    ] = Field(alias="loopback_ipv4_offset")
    avd_custom_hostvars: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars"]
    parent: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode(BaseModel):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode(BaseModel):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeLoopbackIpv4Offset(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars(
    BaseModel
):
    value: Optional[Any]


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
    virtual_router_mac: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVirtualRouterMac"
    ]
    underlay_routing_protocol: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol"
    ]
    overlay_routing_protocol: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricOverlayRoutingProtocol"
    ]
    p_2_p_uplinks_mtu: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricP2PUplinksMtu"
    ] = Field(alias="p2p_uplinks_mtu")
    uplink_pool: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool"
    vtep_pool: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool"
    loopback_pool: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool"
    spanning_tree_mode: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreeMode"
    ]
    spanning_tree_priority: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriority"
    ]
    bgp_evpn_overlay_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpEvpnOverlayPassword"
    ]
    bgp_underlay_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpUnderlayPassword"
    ]
    bgp_mlag_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpMlagPassword"
    ]
    dns_servers: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers"
    ntp_servers: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers"
    local_users: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers"
    avd_evpn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn"
    avd_custom_hostvars: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdCustomHostvars"
    ]


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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdCustomHostvars(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVirtualRouterMac(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricOverlayRoutingProtocol(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricP2PUplinksMtu(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeName"
    ]
    default_prefix_length: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeDefaultPrefixLength"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeName"
    ]
    default_prefix_length: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeDefaultPrefixLength"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeName"
    ]
    default_prefix_length: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeDefaultPrefixLength"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreeMode(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriority(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpEvpnOverlayPassword(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpUnderlayPassword(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpMlagPassword(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNode(
    BaseModel
):
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeName"
    ]
    ip_address: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeIpAddress"
    ]
    vrf: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeVrf"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeIpAddress(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeVrf(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNode(
    BaseModel
):
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeName"
    ]
    server_vrf: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeServerVrf"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeServerVrf(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNode(
    BaseModel
):
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeName"
    ]
    privilege: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePrivilege"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeRole"
    ]
    password_type: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePasswordType"
    ]
    password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePassword"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePrivilege(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePasswordType(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePassword(
    BaseModel
):
    value: Optional[str]


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
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
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
    lag: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLag"
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLag(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeName"
    ]
    channel_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeChannelId"
    ]
    lacp_mode: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeLacpMode"
    ]
    evpn_ethernet_segment: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeChannelId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeLacpMode(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment(
    BaseModel
):
    value: Optional[bool]


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
    lag: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag"
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName"
    ]
    channel_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeChannelId"
    ]
    lacp_mode: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode"
    ]
    evpn_ethernet_segment: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment"
    ]
    lag_members: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembers"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeChannelId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeName"
    ]
    connector: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnector"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnector(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]
    connected_endpoints: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpoints"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpoints(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalRole"
    ]
    lag: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag"
    tagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlan"
    device: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName"
    ]
    channel_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeChannelId"
    ]
    lacp_mode: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode"
    ]
    evpn_ethernet_segment: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeChannelId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeEvpnEthernetSegment(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsn.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRack.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevices.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdCustomHostvars.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriorities.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLag.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnector.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpoints.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice.model_rebuild()
