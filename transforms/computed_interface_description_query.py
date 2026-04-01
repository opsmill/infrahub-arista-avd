from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ComputedInterfaceDescriptionQuery(BaseModel):
    dcim_interface: "ComputedInterfaceDescriptionQueryDcimInterface" = Field(
        alias="DcimInterface"
    )


class ComputedInterfaceDescriptionQueryDcimInterface(BaseModel):
    edges: list["ComputedInterfaceDescriptionQueryDcimInterfaceEdges"]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimInterface",
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpoint",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimInterface(BaseModel):
    typename__: Literal["DcimInterface", "InterfacePhysical", "InterfaceVirtual"] = (
        Field(alias="__typename")
    )
    id: Optional[str]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpoint(BaseModel):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]
    connector: (
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnector"
    )


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnector(
    BaseModel
):
    node: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNode"
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]
    connected_endpoints: "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpoints"


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpoints(
    BaseModel
):
    edges: Optional[
        list[
            "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdges"
        ]
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint",
                "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterface",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint", "InterfacePhysical"] = Field(alias="__typename")
    id: Optional[str]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface"] = Field(alias="__typename")
    id: Optional[str]
    name: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName"
    ]
    device: "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice"


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceName(
    BaseModel
):
    value: Optional[str]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDevice(
    BaseModel
):
    node: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode"
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNode(
    BaseModel
):
    typename__: Literal["ComputePhysicalServer", "DcimDevice", "DcimGenericDevice"] = (
        Field(alias="__typename")
    )
    name: Optional[
        "ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName"
    ]


class ComputedInterfaceDescriptionQueryDcimInterfaceEdgesNodeDcimEndpointConnectorNodeConnectedEndpointsEdgesNodeDcimInterfaceDeviceNodeName(
    BaseModel
):
    value: Optional[str]


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
