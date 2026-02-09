from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AvdDeviceConfigQuery(BaseModel):
    network_device: "AvdDeviceConfigQueryNetworkDevice" = Field(alias="NetworkDevice")


class AvdDeviceConfigQueryNetworkDevice(BaseModel):
    edges: list["AvdDeviceConfigQueryNetworkDeviceEdges"]


class AvdDeviceConfigQueryNetworkDeviceEdges(BaseModel):
    node: Optional["AvdDeviceConfigQueryNetworkDeviceEdgesNode"]


class AvdDeviceConfigQueryNetworkDeviceEdgesNode(BaseModel):
    id: str
    hostname: Optional["AvdDeviceConfigQueryNetworkDeviceEdgesNodeHostname"]
    avd_artifact: "AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifact"


class AvdDeviceConfigQueryNetworkDeviceEdgesNodeHostname(BaseModel):
    value: Optional[str]


class AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode"]


class AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode(BaseModel):
    structured_config_identifier: Optional[
        "AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier"
    ]


class AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier(
    BaseModel
):
    value: Optional[str]


AvdDeviceConfigQuery.model_rebuild()
AvdDeviceConfigQueryNetworkDevice.model_rebuild()
AvdDeviceConfigQueryNetworkDeviceEdges.model_rebuild()
AvdDeviceConfigQueryNetworkDeviceEdgesNode.model_rebuild()
AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdDeviceConfigQueryNetworkDeviceEdgesNodeAvdArtifactNode.model_rebuild()
