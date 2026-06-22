from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class FabricCablingPlanQuery(BaseModel):
    network_fabric: FabricCablingPlanQueryNetworkFabric = Field(alias="NetworkFabric")


class FabricCablingPlanQueryNetworkFabric(BaseModel):
    edges: list[FabricCablingPlanQueryNetworkFabricEdges]


class FabricCablingPlanQueryNetworkFabricEdges(BaseModel):
    node: FabricCablingPlanQueryNetworkFabricEdgesNode | None


class FabricCablingPlanQueryNetworkFabricEdgesNode(BaseModel):
    children: FabricCablingPlanQueryNetworkFabricEdgesNodeChildren


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildren(BaseModel):
    edges: list[FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges] | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges(BaseModel):
    node: (
        Annotated[
            FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock
            | FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod,
            Field(discriminator="typename__"),
        ]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock(BaseModel):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric"] = Field(alias="__typename")
    id: str | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod(BaseModel):
    typename__: Literal["NetworkPod"] = Field(alias="__typename")
    id: str
    devices: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices
    racks: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(BaseModel):
    edges: list[FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(BaseModel):
    node: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(BaseModel):
    id: str
    rack: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack
    interfaces: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack(BaseModel):
    node: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRackNode | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRackNode(BaseModel):
    id: str


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces(BaseModel):
    edges: (
        list[FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges(BaseModel):
    node: (
        Annotated[
            FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface
            | FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical,
            Field(discriminator="typename__"),
        ]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(alias="__typename")
    id: str | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    connector: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: (
        FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: str | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(BaseModel):
    edges: list[FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(BaseModel):
    node: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(BaseModel):
    id: str
    devices: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(BaseModel):
    edges: (
        list[FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges] | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(BaseModel):
    node: (
        Annotated[
            FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice
            | FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice,
            Field(discriminator="typename__"),
        ]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: str | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    rack: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack
    interfaces: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack(
    BaseModel
):
    node: (
        FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRackNode
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRackNode(
    BaseModel
):
    id: str


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces(
    BaseModel
):
    edges: (
        list[
            FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges
        ]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges(
    BaseModel
):
    node: (
        Annotated[
            FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface
            | FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint,
            Field(discriminator="typename__"),
        ]
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
    id: str | None


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: str | None
    connector: FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector(
    BaseModel
):
    node: (
        FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode
        | None
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: str | None


FabricCablingPlanQuery.model_rebuild()
FabricCablingPlanQueryNetworkFabric.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildren.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector.model_rebuild()
