from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ContainerlabLinkEndpointsQuery(BaseModel):
    network_link: "ContainerlabLinkEndpointsQueryNetworkLink" = Field(
        alias="NetworkLink"
    )


class ContainerlabLinkEndpointsQueryNetworkLink(BaseModel):
    edges: list["ContainerlabLinkEndpointsQueryNetworkLinkEdges"]


class ContainerlabLinkEndpointsQueryNetworkLinkEdges(BaseModel):
    node: Optional["ContainerlabLinkEndpointsQueryNetworkLinkEdgesNode"]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNode(BaseModel):
    id: str
    connected_endpoints: (
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpoints"
    )


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpoints(BaseModel):
    edges: Optional[
        list[
            "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges"
        ]
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterface",
                "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    name: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceName"
    ]
    device: "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice"


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: Optional[str]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode"
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = (
        Field(alias="__typename")
    )
    name: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName"
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName(
    BaseModel
):
    value: Optional[str]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    name: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    device: "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"
    name: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalName"
    ]
    device: "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice"


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalName(
    BaseModel
):
    value: Optional[str]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice(
    BaseModel
):
    node: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNode"
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = (
        Field(alias="__typename")
    )
    name: Optional[
        "ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeName"
    ]


class ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNodeName(
    BaseModel
):
    value: Optional[str]


ContainerlabLinkEndpointsQuery.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLink.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdges.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNode.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpoints.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdges.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterface.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysical.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDevice.model_rebuild()
ContainerlabLinkEndpointsQueryNetworkLinkEdgesNodeConnectedEndpointsEdgesNodeInterfacePhysicalDeviceNode.model_rebuild()
