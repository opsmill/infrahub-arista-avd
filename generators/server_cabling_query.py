from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ServerCablingQuery(BaseModel):
    compute_physical_server: ServerCablingQueryComputePhysicalServer = Field(
        alias="ComputePhysicalServer"
    )


class ServerCablingQueryComputePhysicalServer(BaseModel):
    edges: list[ServerCablingQueryComputePhysicalServerEdges]


class ServerCablingQueryComputePhysicalServerEdges(BaseModel):
    node: ServerCablingQueryComputePhysicalServerEdgesNode | None


class ServerCablingQueryComputePhysicalServerEdgesNode(BaseModel):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeName | None
    role: ServerCablingQueryComputePhysicalServerEdgesNodeRole | None
    status: ServerCablingQueryComputePhysicalServerEdgesNodeStatus | None
    rack: ServerCablingQueryComputePhysicalServerEdgesNodeRack
    interfaces: ServerCablingQueryComputePhysicalServerEdgesNodeInterfaces


class ServerCablingQueryComputePhysicalServerEdgesNodeName(BaseModel):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeRole(BaseModel):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeStatus(BaseModel):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeRack(BaseModel):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeRackNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeRackNode(BaseModel):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeRackNodeName | None


class ServerCablingQueryComputePhysicalServerEdgesNodeRackNodeName(BaseModel):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfaces(BaseModel):
    edges: list[ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdges] | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdges(BaseModel):
    node: Annotated[ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeDcimInterface | ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysical, Field(discriminator="typename__")] | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceVirtual"] = Field(alias="__typename")
    id: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalName | None
    role: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole | None
    status: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalStatus | None
    connector: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector
    tagged_vlan: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan
    untagged_vlan: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan
    profiles: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfiles


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalStatus(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan(
    BaseModel
):
    edges: list[
        ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdges(
    BaseModel
):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNode(
    BaseModel
):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeName | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlanEdgesNodeName(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan(
    BaseModel
):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNode(
    BaseModel
):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeName | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlanNodeName(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfiles(
    BaseModel
):
    edges: list[ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdges] | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdges(
    BaseModel
):
    node: Annotated[ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeCoreProfile | ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterface, Field(discriminator="typename__")] | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeCoreProfile(
    BaseModel
):
    typename__: Literal[
        "CoreProfile",
        "ProfileAvdArtifact",
        "ProfileAvdEvpn",
        "ProfileBuiltinIPAddress",
        "ProfileBuiltinIPPrefix",
        "ProfileBuiltinTag",
        "ProfileComputeGenericUnit",
        "ProfileComputePhysicalServer",
        "ProfileDcimConnector",
        "ProfileDcimDevice",
        "ProfileDcimDeviceType",
        "ProfileDcimEndpoint",
        "ProfileDcimGenericDevice",
        "ProfileDcimPhysicalDevice",
        "ProfileDcimPlatform",
        "ProfileGeneratorTarget",
        "ProfileInterfaceHasSubInterface",
        "ProfileInterfaceLayer2",
        "ProfileInterfaceLayer3",
        "ProfileInterfacePhysical",
        "ProfileInterfaceVirtual",
        "ProfileIpamIPAddress",
        "ProfileIpamL2Domain",
        "ProfileIpamNamespace",
        "ProfileIpamPrefix",
        "ProfileIpamVLAN",
        "ProfileLocationGeneric",
        "ProfileLocationHall",
        "ProfileLocationHosting",
        "ProfileLocationRack",
        "ProfileNetworkBuildingBlock",
        "ProfileNetworkFabric",
        "ProfileNetworkLink",
        "ProfileNetworkPod",
        "ProfileOrganizationGeneric",
        "ProfileOrganizationManufacturer",
        "ProfileOrganizationProvider",
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
    id: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterface(
    BaseModel
):
    typename__: Literal["ProfileDcimInterface"] = Field(alias="__typename")
    id: str
    profile_name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceProfileName | None
    tagged_vlan: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlan
    untagged_vlan: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlan


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceProfileName(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlan(
    BaseModel
):
    edges: list[
        ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdges
    ]


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdges(
    BaseModel
):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNode(
    BaseModel
):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNodeName | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceTaggedVlanEdgesNodeName(
    BaseModel
):
    value: str | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlan(
    BaseModel
):
    node: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNode | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNode(
    BaseModel
):
    id: str
    name: ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNodeName | None


class ServerCablingQueryComputePhysicalServerEdgesNodeInterfacesEdgesNodeInterfacePhysicalProfilesEdgesNodeProfileDcimInterfaceUntaggedVlanNodeName(
    BaseModel
):
    value: str | None


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
