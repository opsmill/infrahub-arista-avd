from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class GenerateAvdDeviceInputsQuery(BaseModel):
    network_device: "GenerateAvdDeviceInputsQueryNetworkDevice" = Field(
        alias="NetworkDevice"
    )


class GenerateAvdDeviceInputsQueryNetworkDevice(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryNetworkDeviceEdges"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdges(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNode"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNode(BaseModel):
    id: str
    hostname: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeHostname"]
    role: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeRole"]
    bgp_asn: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeBgpAsn"]
    node_id: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeNodeId"]
    loopback_ip: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIp"
    mgmt_ip: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIp"
    pod: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePod"
    interfaces: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeHostname(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeRole(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeBgpAsn(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeNodeId(BaseModel):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIp(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIpNode"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIpNode(BaseModel):
    id: str
    address: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIpNodeAddress"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIpNodeAddress(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIp(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIpNode"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIpNode(BaseModel):
    id: str
    address: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIpNodeAddress"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIpNodeAddress(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePod(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNode"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeName"]
    parent: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParent"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParent(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock",
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabric",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkPod"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlockName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabric(
    BaseModel
):
    typename__: Literal["NetworkFabric"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricName"
    ]
    mgmt_gateway: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway"
    ]
    mgmt_routes_1: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes1"
    ] = Field(alias="mgmt_routes1")
    avd_evpn: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes1(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode(
    BaseModel
):
    ebgp_multihop: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop"
    ]
    overlay_bgp_rtc: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeEbgpMultihop(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNodeOverlayBgpRtc(
    BaseModel
):
    value: Optional[bool]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces(BaseModel):
    edges: list["GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdges"]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNode(BaseModel):
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole"
    ]
    tagged_vlan: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlan"
    untagged_vlan: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlan"
    link: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLink"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlan(
    BaseModel
):
    edges: list[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdges"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlan(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNode(
    BaseModel
):
    vlan_id: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNodeVlanId"
    ]
    status: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNodeStatus"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNodeVlanId(
    BaseModel
):
    value: Optional[Any]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNodeStatus(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLink(
    BaseModel
):
    node: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNode"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNode(
    BaseModel
):
    id: str
    endpoints: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpoints"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpoints(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdges"
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkEndpoint",
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkEndpoint(
    BaseModel
):
    typename__: Literal["NetworkEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface(
    BaseModel
):
    typename__: Literal["NetworkInterface"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceName"
    ]
    device: "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice"


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkGenericDevice",
                "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkGenericDevice(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "NetworkGenericDevice"] = Field(
        alias="__typename"
    )
    id: Optional[str]
    hostname: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkGenericDeviceHostname"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkGenericDeviceHostname(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDevice(
    BaseModel
):
    typename__: Literal["NetworkDevice"] = Field(alias="__typename")
    id: str
    hostname: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDeviceHostname"
    ]
    role: Optional[
        "GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDeviceRole"
    ]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDeviceHostname(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDeviceRole(
    BaseModel
):
    value: Optional[str]


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIp.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeLoopbackIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIp.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeMgmtIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePod.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParent.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkBuildingBlock.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabric.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpnNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeTaggedVlanEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlan.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlanNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLink.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNode.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpoints.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdges.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkGenericDevice.model_rebuild()
GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeNetworkDevice.model_rebuild()
