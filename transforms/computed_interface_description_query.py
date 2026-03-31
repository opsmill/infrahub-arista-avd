from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ComputedInterfaceDescriptionQuery(BaseModel):
    dcim_interface: "ComputedInterfaceDescriptionQueryDcimInterface" = Field(alias="DcimInterface")


class ComputedInterfaceDescriptionQueryDcimInterface(BaseModel):
    edges: list["ComputedInterfaceDescriptionQueryDcimInterfaceEdges"]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdges(BaseModel):
    node: Optional["ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNode"]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNode(BaseModel):
    id: str
    connector: "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnector"


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnector(BaseModel):
    node: Optional["ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNode"]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNode(BaseModel):
    id: str
    connected_endpoints: "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpoints"


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpoints(BaseModel):
    edges: Optional[list["ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdges"]]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(BaseModel):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(BaseModel):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: str
    name: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName"
    ]
    device: "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice"


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: Optional[str]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode"
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = Field(alias="__typename")
    name: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName"
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName(
    BaseModel
):
    value: Optional[str]


ComputedInterfaceDescriptionQuery.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterface.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdges.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNode.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnector.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNode.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpoints.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdges.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterface.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice.model_rebuild()
ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode.model_rebuild()
