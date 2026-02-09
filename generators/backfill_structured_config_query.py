from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class BackfillStructuredConfigQuery(BaseModel):
    network_device: "BackfillStructuredConfigQueryNetworkDevice" = Field(
        alias="NetworkDevice"
    )


class BackfillStructuredConfigQueryNetworkDevice(BaseModel):
    edges: list["BackfillStructuredConfigQueryNetworkDeviceEdges"]


class BackfillStructuredConfigQueryNetworkDeviceEdges(BaseModel):
    node: Optional["BackfillStructuredConfigQueryNetworkDeviceEdgesNode"]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNode(BaseModel):
    id: str
    hostname: Optional["BackfillStructuredConfigQueryNetworkDeviceEdgesNodeHostname"]
    role: Optional["BackfillStructuredConfigQueryNetworkDeviceEdgesNodeRole"]
    avd_artifact: "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifact"
    interfaces: "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfaces"


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeHostname(BaseModel):
    value: Optional[str]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeRole(BaseModel):
    value: Optional[str]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode"]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    structured_config_identifier: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier"
    ]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfaces(BaseModel):
    edges: list["BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdges"]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode"
    ]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode(BaseModel):
    id: str
    name: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName"
    ]
    role: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole"
    ]
    mtu: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeMtu"
    ]
    ip_address: "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress"


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeMtu(
    BaseModel
):
    value: Optional[Any]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress(
    BaseModel
):
    node: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode"
    ]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode(
    BaseModel
):
    id: str
    address: Optional[
        "BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress"
    ]


class BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress(
    BaseModel
):
    value: Optional[str]


BackfillStructuredConfigQuery.model_rebuild()
BackfillStructuredConfigQueryNetworkDevice.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdges.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNode.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifact.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfaces.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdges.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress.model_rebuild()
BackfillStructuredConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode.model_rebuild()
