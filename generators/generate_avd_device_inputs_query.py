from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class GenerateAvdDeviceInputsQuery(BaseModel):
    dcim_device: "GenerateAvdDeviceInputsQueryDcimDevice" = Field(alias="DcimDevice")
    network_link: "GenerateAvdDeviceInputsQueryNetworkLink" = Field(alias="NetworkLink")


class GenerateAvdDeviceInputsQueryDcimDevice(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryDcimDeviceEdges"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdges(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeName"]
    role: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeRole"]
    evpn_gateway_group: (
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroup"
    )
    asn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAsn"
    node_id: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeNodeId"]
    avd_custom_hostvars: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeAvdCustomHostvars"
    ]
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroup(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNode(BaseModel):
    id: str
    display_label: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeName"
    ]
    resiliency_model: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeResiliencyModel"
    ]
    evpn_l_2_enabled: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL2Enabled"
    ] = Field(alias="evpn_l2_enabled")
    evpn_l_3_enabled: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL3Enabled"
    ] = Field(alias="evpn_l3_enabled")
    evpn_l_3_inter_domain: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL3InterDomain"
    ] = Field(alias="evpn_l3_inter_domain")
    d_path_enabled: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeDPathEnabled"
    ]
    all_active_multihoming_enabled: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeAllActiveMultihomingEnabled"
    ]
    ethernet_segment_identifier: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEthernetSegmentIdentifier"
    ]
    ethernet_segment_rt_import: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEthernetSegmentRtImport"
    ]
    local_domain: (
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomain"
    )
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePod"
    members: (
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembers"
    )
    remote_domain: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomain"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeResiliencyModel(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL2Enabled(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL3Enabled(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEvpnL3InterDomain(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeDPathEnabled(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeAllActiveMultihomingEnabled(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEthernetSegmentIdentifier(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeEthernetSegmentRtImport(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomain(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeDomainId"
    ]
    fabric: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabric"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeDomainId(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabric(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabricNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabricNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePod(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeName"
    ]
    evpn_domain: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomain"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomain(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeDomainId"
    ]
    fabric: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabric"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeDomainId(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabric(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabricNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabricNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodeName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodeRole"
    ]
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePod"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePod(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePodNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePodNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePodNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePodNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomain(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeDomainId"
    ]
    fabric: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabric"
    remote_gateway_groups: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroups"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeDomainId(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabric(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabricNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabricNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroups(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeName"
    ]
    local_domain: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomain"
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePod"
    members: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembers"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomain(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeDomainId"
    ]
    fabric: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabric"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeDomainId(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabric(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabricNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabricNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePod(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeName"
    ]
    evpn_domain: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomain"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomain(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNode(
    BaseModel
):
    id: str
    display_label: Optional[str]
    domain_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeDomainId"
    ]
    fabric: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabric"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeDomainId(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabric(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabricNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabricNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabricNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabricNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembers(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodeName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodeRole"
    ]
    pod: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePod"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePod(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePodNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePodNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePodNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePodNodeName(
    BaseModel
):
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
    avd_custom_hostvars: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeAvdCustomHostvars"
    ]
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
    children: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildren"
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
    evpn_vlan_aware_bundles: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricEvpnVlanAwareBundles"
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
    spanning_tree_priorities: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriorities"
    bgp_evpn_overlay_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpEvpnOverlayPassword"
    ]
    bgp_underlay_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpUnderlayPassword"
    ]
    bgp_mlag_password: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricBgpMlagPassword"
    ]
    avd_custom_hostvars: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdCustomHostvars"
    ]
    dns_servers: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricDnsServers"
    ntp_servers: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricNtpServers"
    local_users: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricLocalUsers"
    avd_evpn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildren(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkBuildingBlock",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPod",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPod(
    BaseModel
):
    typename__: Literal["NetworkPod"] = Field(alias="__typename")
    id: str
    devices: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevices"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevices(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeRole"
    ]
    node_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeNodeId"
    ]
    interfaces: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeNodeId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole"
    ]
    connector: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]
    connected_endpoints: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint", "InterfacePhysical"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName"
    ]
    device: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = (
        Field(alias="__typename")
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName(
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricEvpnVlanAwareBundles(
    BaseModel
):
    value: Optional[bool]


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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePriorities(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNode(
    BaseModel
):
    role: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNodeRole"
    ]
    priority: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNodePriority"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricSpanningTreePrioritiesEdgesNodePriority(
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdCustomHostvars(
    BaseModel
):
    value: Optional[Any]


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
    tagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlan"


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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus(
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
    lag: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLag"


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
    tagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan"
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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus(
    BaseModel
):
    value: Optional[str]


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
    tagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan"


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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNodeStatus(
    BaseModel
):
    value: Optional[str]


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


class GenerateAvdDeviceInputsQueryNetworkLink(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryNetworkLinkEdges"]


class GenerateAvdDeviceInputsQueryNetworkLinkEdges(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryNetworkLinkEdgesNode"]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNode(BaseModel):
    id: str
    display_label: Optional[str]
    name: Optional["GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeName"]
    role: Optional["GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeRole"]
    include_in_underlay_protocol: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeIncludeInUnderlayProtocol"
    ]
    connected_endpoints: (
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpoints"
    )


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeRole(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeIncludeInUnderlayProtocol(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpoints(BaseModel):
    edges: Optional[
        list["GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges"]
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalRole"
    ]
    device: "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice",
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimGenericDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole"
    ]
    asn: "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsn"
    pod: "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePod"


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsn(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsnNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsnNode(
    BaseModel
):
    asn: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsnNodeAsn"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsnNodeAsn(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePod(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNode(
    BaseModel
):
    parent: "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParent"


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParent(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkBuildingBlock",
                "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabric(
    BaseModel
):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricName"
    ]
    dci_pool: "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPool"


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPool(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNodeName"
    ]
    default_prefix_length: Optional[
        "GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNodeDefaultPrefixLength"
    ]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNodeDefaultPrefixLength(
    BaseModel
):
    value: Optional[Any]


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroup.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeLocalDomainNodeFabricNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodePodNodeEvpnDomainNodeFabricNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeMembersEdgesNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeFabricNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroups.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeLocalDomainNodeFabricNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomain.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabric.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodePodNodeEvpnDomainNodeFabricNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembers.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeEvpnGatewayGroupNodeRemoteDomainNodeRemoteGatewayGroupsEdgesNodeMembersEdgesNodePodNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildren.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPod.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevices.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterface.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode.model_rebuild()
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
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeUntaggedVlanNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalUntaggedVlanNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalLagNodeLagMembersEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLink.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpoints.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsn.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDeviceAsnNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePod.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParent.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabric.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPool.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeDcimDevicePodNodeParentNodeNetworkFabricDciPoolNode.model_rebuild()
