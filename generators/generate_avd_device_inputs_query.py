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


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePod(BaseModel):
    node: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode"]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNode(BaseModel):
    id: str
    name: Optional["GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeName"]
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
    mgmt_routes_1: Optional[
        "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes1"
    ] = Field(alias="mgmt_routes1")
    avd_evpn: "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricAvdEvpn"


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtGateway(
    BaseModel
):
    value: Optional[str]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodePodNodeParentNodeNetworkFabricMgmtRoutes1(
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
    typename__: Literal["DcimInterface", "InterfaceVirtual"] = Field(alias="__typename")
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
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint", "InterfacePhysical"] = Field(alias="__typename")
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


GenerateAvdDeviceInputsQuery.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDevice.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdges.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeLoopbackIpNode.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIp.model_rebuild()
GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeMgmtIpNode.model_rebuild()
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
