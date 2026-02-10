from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ComputedInterfaceDescriptionQuery(BaseModel):
    network_interface: "ComputedInterfaceDescriptionQueryNetworkInterface" = Field(alias="NetworkInterface")


class ComputedInterfaceDescriptionQueryNetworkInterface(BaseModel):
    edges: list["ComputedInterfaceDescriptionQueryNetworkInterfaceEdges"]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdges(BaseModel):
    node: Optional["ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNode"]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNode(BaseModel):
    id: str
    link: "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLink"


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLink(BaseModel):
    node: Optional["ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNode"]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNode(BaseModel):
    id: str
    endpoints: "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpoints"


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpoints(BaseModel):
    edges: Optional[list["ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdges"]]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkEndpoint",
                "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkEndpoint(BaseModel):
    typename__: Literal["NetworkEndpoint"] = Field(alias="__typename")
    id: Optional[str]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface(BaseModel):
    typename__: Literal["NetworkInterface"] = Field(alias="__typename")
    id: str
    name: Optional[
        "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceName"
    ]
    device: "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice"


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceName(
    BaseModel
):
    value: Optional[str]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice(
    BaseModel
):
    node: Optional[
        "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNode"
    ]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "NetworkDevice", "NetworkGenericDevice"] = Field(alias="__typename")
    hostname: Optional[
        "ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeHostname"
    ]


class ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNodeHostname(
    BaseModel
):
    value: Optional[str]


ComputedInterfaceDescriptionQuery.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterface.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdges.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNode.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLink.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNode.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpoints.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdges.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterface.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDevice.model_rebuild()
ComputedInterfaceDescriptionQueryNetworkInterfaceEdgesNodeLinkNodeEndpointsEdgesNodeNetworkInterfaceDeviceNode.model_rebuild()
