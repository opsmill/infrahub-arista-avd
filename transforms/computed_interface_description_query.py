from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ComputedInterfaceDescriptionQuery(BaseModel):
    dcim_interface: ComputedInterfaceDescriptionQueryDcimInterface = Field(alias="DcimInterface")


class ComputedInterfaceDescriptionQueryDcimInterface(BaseModel):
    edges: list[ComputedInterfaceDescriptionQueryDcimInterfaceEdges]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdges(BaseModel):
    node: (
        Annotated[
            ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimInterface
            | ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpoint,
            Field(discriminator="typename__"),
        ]
        | None
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimInterface(BaseModel):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
    id: str | None


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpoint(BaseModel):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: str | None
    connector: ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnector


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnector(BaseModel):
    node: ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNode | None


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNode(BaseModel):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: str | None
    connected_endpoints: (
        ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpoints
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpoints(BaseModel):
    edges: (
        list[ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdges]
        | None
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: (
        Annotated[
            ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint
            | ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterface,
            Field(discriminator="typename__"),
        ]
        | None
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint", "InterfacePhysical"] = Field(alias="__typename")
    id: str | None


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: str | None
    name: (
        ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName
        | None
    )
    device: ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: str | None


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: (
        ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode
        | None
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = Field(alias="__typename")
    name: (
        ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName
        | None
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName(
    BaseModel
):
    value: str | None


ComputedInterfaceDescriptionQuery.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterface.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdges.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpoint.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnector.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNode.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpoints.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdges.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterface.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode.model_rebuild()
