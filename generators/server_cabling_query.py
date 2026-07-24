from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ServerCablingQuery(BaseModel):
    compute_physical_server: "ServerCablingQueryComputePhysicalServer" = Field(
        alias="ComputePhysicalServer"
    )


class ServerCablingQueryComputePhysicalServer(BaseModel):
    edges: list["ServerCablingQueryComputePhysicalServerEdges"]


class ServerCablingQueryComputePhysicalServerEdges(BaseModel):
    node: Optional["ServerCablingQueryComputePhysicalServerEdgesNode"]


class ServerCablingQueryComputePhysicalServerEdgesNode(BaseModel):
    id: str
    name: Optional["ServerCablingQueryComputePhysicalServerEdgesNodeName"]
    role: Optional["ServerCablingQueryComputePhysicalServerEdgesNodeRole"]
    status: Optional["ServerCablingQueryComputePhysicalServerEdgesNodeStatus"]
    rack: "ServerCablingQueryComputePhysicalServerEdgesNodeRack"
    interfaces: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfaces"


class ServerCablingQueryComputePhysicalServerEdgesNodeName(BaseModel):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeRole(BaseModel):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeStatus(BaseModel):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeRack(BaseModel):
    node: Optional["ServerCablingQueryComputePhysicalServerEdgesNodeRackNode"]


class ServerCablingQueryComputePhysicalServerEdgesNodeRackNode(BaseModel):
    id: str
    name: Optional["ServerCablingQueryComputePhysicalServerEdgesNodeRackNodeName"]


class ServerCablingQueryComputePhysicalServerEdgesNodeRackNodeName(BaseModel):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfaces(BaseModel):
    edges: Optional[
        list["ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdges"]
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeDcimInterface",
                "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalName"
    ]
    role: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole"
    ]
    status: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalStatus"
    ]
    connector: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector"
    tagged_vlan: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan"
    untagged_vlan: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan"
    profiles: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfiles"


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalStatus(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan(
    BaseModel
):
    edges: list[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeName"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan(
    BaseModel
):
    node: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode(
    BaseModel
):
    id: str
    name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeName"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeName(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfiles(
    BaseModel
):
    edges: Optional[
        list[
            "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdges"
        ]
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeCoreProfile",
                "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeCoreProfile(
    BaseModel
):
    typename__: Literal[
        "CoreProfile",
        "ProfileAvdArtifact",
        "ProfileAvdEvpn",
        "ProfileAvdHostvarFile",
        "ProfileAvdStructuredConfigFile",
        "ProfileAvdTag",
        "ProfileBuiltinIPAddress",
        "ProfileBuiltinIPPrefix",
        "ProfileBuiltinTag",
        "ProfileCloudvisionWorkspace",
        "ProfileComputeGenericUnit",
        "ProfileComputePhysicalServer",
        "ProfileDcimConnector",
        "ProfileDcimDevice",
        "ProfileDcimDeviceType",
        "ProfileDcimEndpoint",
        "ProfileDcimGenericDevice",
        "ProfileDcimPhysicalDevice",
        "ProfileDcimPlatform",
        "ProfileEvpnDomain",
        "ProfileEvpnGatewayGroup",
        "ProfileEvpnL2Vlan",
        "ProfileEvpnSvi",
        "ProfileEvpnTenant",
        "ProfileGeneratorTarget",
        "ProfileGenericInterfaceBundle",
        "ProfileGenericMlagDomain",
        "ProfileInterfaceHasSubInterface",
        "ProfileInterfaceLag",
        "ProfileInterfaceLayer2",
        "ProfileInterfaceLayer3",
        "ProfileInterfacePhysical",
        "ProfileInterfaceVirtual",
        "ProfileIpamIPAddress",
        "ProfileIpamL2Domain",
        "ProfileIpamNamespace",
        "ProfileIpamPrefix",
        "ProfileIpamRouteTarget",
        "ProfileIpamVLAN",
        "ProfileIpamVRF",
        "ProfileLocationGeneric",
        "ProfileLocationHall",
        "ProfileLocationHosting",
        "ProfileLocationRack",
        "ProfileMlagDomain",
        "ProfileMlagInterface",
        "ProfileNetworkBuildingBlock",
        "ProfileNetworkDnsServer",
        "ProfileNetworkFabric",
        "ProfileNetworkLink",
        "ProfileNetworkLocalUser",
        "ProfileNetworkNtpServer",
        "ProfileNetworkPod",
        "ProfileNetworkSpanningTreePriority",
        "ProfileOrganizationGeneric",
        "ProfileOrganizationManufacturer",
        "ProfileOrganizationProvider",
        "ProfileRoutingAsn",
        "ProfileRoutingBGPNeighbor",
        "ProfileRoutingBGPPeerGroup",
        "ProfileRoutingPrefixList",
        "ProfileRoutingPrefixListEntry",
        "ProfileRoutingRouteMap",
        "ProfileRoutingRouteMapEntry",
        "ProfileRoutingStaticRoute",
        "ProfileVirtualizationHostVirtualMachine",
        "ProfileVirtualizationVirtualMachine",
    ] = Field(alias="__typename")
    id: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterface(
    BaseModel
):
    typename__: Literal["ProfileDcimInterface"] = Field(alias="__typename")
    id: str
    profile_name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceProfileName"
    ]
    tagged_vlan: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlan"
    untagged_vlan: "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlan"


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceProfileName(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlan(
    BaseModel
):
    edges: list[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdges"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdges(
    BaseModel
):
    node: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNode"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNodeName"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlan(
    BaseModel
):
    node: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNode"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNode(
    BaseModel
):
    id: str
    name: Optional[
        "ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNodeName"
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNodeName(
    BaseModel
):
    value: Optional[str]


ServerCablingQuery.model_rebuild()
ServerCablingQueryComputePhysicalServer.model_rebuild()
ServerCablingQueryComputePhysicalServerEdges.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNode.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeRack.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeRackNode.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfaces.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdges.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysical.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfiles.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdges.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterface.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlan.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdges.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNode.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlan.model_rebuild()
ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNode.model_rebuild()
