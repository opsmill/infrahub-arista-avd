from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class GenerateAvdDeviceInputsQuery(BaseModel):
    dcim_device: GenerateAvdDeviceInputsQueryDcimDevice = Field(alias="DcimDevice")


class GenerateAvdDeviceInputsQueryDcimDevice(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName | None
    role: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole | None
    asn: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn | None
    node_id: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId | None
    avd_custom_hostvars: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars | None
    loopback_ip: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp
    mgmt_ip: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp
    mlag_domain: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain
    rack: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRack
    pod: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod
    interfaces: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNode(BaseModel):
    asn: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNodeAsn | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsnNodeAsn(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode(BaseModel):
    id: str
    address: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode(BaseModel):
    id: str
    address: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNodeAddress | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNodeAddress(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomain(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNode(BaseModel):
    id: str
    domain_id: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId | None
    asn: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsn | None
    virtual_router_mac: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac | None
    peers: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeDomainId(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsn(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNode(BaseModel):
    asn: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNodeAsn | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeAsnNodeAsn(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodeVirtualRouterMac(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeers(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMlagDomainNodePeersEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRack(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeName | None
    mlag: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeMlag | None
    devices: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevices


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeMlag(BaseModel):
    value: bool | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevices(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdges] | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdges(BaseModel):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimPhysicalDevice
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDevice,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimPhysicalDevice(BaseModel):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDevice(BaseModel):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceName | None
    role: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceRole | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRackNodeDevicesEdgesNodeDcimDeviceRole(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName | None
    mlag_peer_pool: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool
    mlag_l_3_pool: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool = Field(alias="mlag_l3_pool")
    loopback_ipv_4_offset: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeLoopbackIpv4Offset | None = Field(
        alias="loopback_ipv4_offset"
    )
    avd_custom_hostvars: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars | None
    parent: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNodeName | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNodeName | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeLoopbackIpv4Offset(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent(BaseModel):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(alias="__typename")
    id: str | None
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric(BaseModel):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName | None
    mgmt_gateway: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway | None
    mgmt_routes: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes | None
    virtual_router_mac: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVirtualRouterMac | None
    )
    underlay_routing_protocol: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol | None
    )
    overlay_routing_protocol: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricOverlayRoutingProtocol | None
    )
    p_2_p_uplinks_mtu: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricP2PUplinksMtu | None
    ) = Field(alias="p2p_uplinks_mtu")
    uplink_pool: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool
    vtep_pool: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool
    loopback_pool: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool
    spanning_tree_mode: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreeMode | None
    )
    spanning_tree_priority: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriority | None
    )
    bgp_evpn_overlay_password: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpEvpnOverlayPassword | None
    )
    bgp_underlay_password: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpUnderlayPassword | None
    )
    bgp_mlag_password: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpMlagPassword | None
    )
    dns_servers: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers
    ntp_servers: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers
    local_users: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers
    avd_evpn: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVirtualRouterMac(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUnderlayRoutingProtocol(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricOverlayRoutingProtocol(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricP2PUplinksMtu(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeName | None
    default_prefix_length: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeDefaultPrefixLength
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeName | None
    default_prefix_length: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeDefaultPrefixLength
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode(BaseModel):
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeName | None
    default_prefix_length: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeDefaultPrefixLength
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreeMode(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriority(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpEvpnOverlayPassword(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpUnderlayPassword(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpMlagPassword(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNode(BaseModel):
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeName | None
    ip_address: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeIpAddress | None
    )
    vrf: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeVrf | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeIpAddress(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServersEdgesNodeVrf(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNode(BaseModel):
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeName | None
    server_vrf: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeServerVrf | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServersEdgesNodeServerVrf(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNode(BaseModel):
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeName | None
    privilege: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePrivilege | None
    )
    role: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeRole | None
    password_type: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePasswordType
        | None
    )
    password: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePassword | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePrivilege(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodeRole(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePasswordType(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsersEdgesNodePassword(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode(BaseModel):
    ebgp_multihop: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop | None
    )
    overlay_bgp_rtc: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop(BaseModel):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc(BaseModel):
    value: bool | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfaces(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges] | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDcimInterface
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDcimInterface(BaseModel):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(alias="__typename")
    id: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical(BaseModel):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalName | None
    role: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole | None
    tagged_vlan: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan
    untagged_vlan: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan
    connector: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalName(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole(BaseModel):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan(BaseModel):
    edges: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode(BaseModel):
    vlan_id: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId
        | None
    )
    status: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode(BaseModel):
    vlan_id: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId | None
    )
    status: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Any | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeStatus(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(BaseModel):
    node: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(BaseModel):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: str | None
    connected_endpoints: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints(
    BaseModel
):
    edges: (
        list[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: str | None
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName
        | None
    )
    device: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDevice
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDevice,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(alias="__typename")
    id: str | None
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDeviceName
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceName
        | None
    )
    role: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceRole
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName
        | None
    )
    device: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice
    lag: GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice(
    BaseModel
):
    node: (
        Annotated[
            GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice
            | GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice,
            Field(discriminator="typename__"),
        ]
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(alias="__typename")
    id: str | None
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName
        | None
    )
    role: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag(
    BaseModel
):
    node: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNode(
    BaseModel
):
    id: str
    name: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName
        | None
    )
    lacp_mode: (
        GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode
        | None
    )


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeName(
    BaseModel
):
    value: str | None


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLacpMode(
    BaseModel
):
    value: str | None


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagPeerPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3Pool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeMlagL3PoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParent.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricUplinkPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricVtepPoolNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPool.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLoopbackPoolNode.model_rebuild()
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
