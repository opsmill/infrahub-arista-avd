from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class BackfillStructuredConfigQuery(BaseModel):
    avd_artifact: "BackfillStructuredConfigQueryAvdArtifact" = Field(
        alias="AvdArtifact"
    )


class BackfillStructuredConfigQueryAvdArtifact(BaseModel):
    edges: list["BackfillStructuredConfigQueryAvdArtifactEdges"]


class BackfillStructuredConfigQueryAvdArtifactEdges(BaseModel):
    node: Optional["BackfillStructuredConfigQueryAvdArtifactEdgesNode"]


class BackfillStructuredConfigQueryAvdArtifactEdgesNode(BaseModel):
    id: str
    structured_config_identifier: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigIdentifier"
    ]
    device: "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice"


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeStructuredConfigIdentifier(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice(BaseModel):
    node: Optional["BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode"]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode(BaseModel):
    id: str
    name: Optional["BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeName"]
    role: Optional["BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeRole"]
    interfaces: "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces"


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeName(BaseModel):
    value: Optional[str]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeRole(BaseModel):
    value: Optional[str]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces(BaseModel):
    edges: Optional[
        list[
            "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges"
        ]
    ]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges(
    BaseModel
):
    node: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode"
    ]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfacePhysical", "InterfaceVirtual"] = (
        Field(alias="__typename")
    )
    id: Optional[str]
    name: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeName"
    ]
    role: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeRole"
    ]
    mtu: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeMtu"
    ]
    ip_address: "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress"


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeMtu(
    BaseModel
):
    value: Optional[Any]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress(
    BaseModel
):
    node: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode"
    ]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode(
    BaseModel
):
    id: str
    address: Optional[
        "BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNodeAddress"
    ]


class BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNodeAddress(
    BaseModel
):
    value: Optional[str]


BackfillStructuredConfigQuery.model_rebuild()
BackfillStructuredConfigQueryAvdArtifact.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdges.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDevice.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfaces.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdges.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress.model_rebuild()
BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode.model_rebuild()
