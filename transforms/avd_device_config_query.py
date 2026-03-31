from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AvdDeviceConfigQuery(BaseModel):
    dcim_device: "AvdDeviceConfigQueryDcimDevice" = Field(alias="DcimDevice")


class AvdDeviceConfigQueryDcimDevice(BaseModel):
    edges: list["AvdDeviceConfigQueryDcimDeviceEdges"]


class AvdDeviceConfigQueryDcimDeviceEdges(BaseModel):
    node: Optional["AvdDeviceConfigQueryDcimDeviceEdgesNode"]


class AvdDeviceConfigQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: Optional["AvdDeviceConfigQueryDcimDeviceEdgesNodeName"]
    avd_artifact: "AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact"


class AvdDeviceConfigQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: Optional["AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode"]


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    structured_config_identifier: Optional[
        "AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier"
    ]


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier(BaseModel):
    value: Optional[str]


AvdDeviceConfigQuery.model_rebuild()
AvdDeviceConfigQueryDcimDevice.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdges.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNode.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode.model_rebuild()
