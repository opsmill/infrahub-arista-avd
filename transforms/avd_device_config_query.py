from __future__ import annotations

from pydantic import BaseModel, Field


class AvdDeviceConfigQuery(BaseModel):
    dcim_device: AvdDeviceConfigQueryDcimDevice = Field(alias="DcimDevice")


class AvdDeviceConfigQueryDcimDevice(BaseModel):
    edges: list[AvdDeviceConfigQueryDcimDeviceEdges]


class AvdDeviceConfigQueryDcimDeviceEdges(BaseModel):
    node: AvdDeviceConfigQueryDcimDeviceEdgesNode | None


class AvdDeviceConfigQueryDcimDeviceEdgesNode(BaseModel):
    id: str
    name: AvdDeviceConfigQueryDcimDeviceEdgesNodeName | None
    avd_artifact: AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact


class AvdDeviceConfigQueryDcimDeviceEdgesNodeName(BaseModel):
    value: str | None


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact(BaseModel):
    node: AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode | None


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode(BaseModel):
    id: str
    structured_config_identifier: AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier | None


class AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNodeStructuredConfigIdentifier(
    BaseModel
):
    value: str | None


AvdDeviceConfigQuery.model_rebuild()
AvdDeviceConfigQueryDcimDevice.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdges.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNode.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifact.model_rebuild()
AvdDeviceConfigQueryDcimDeviceEdgesNodeAvdArtifactNode.model_rebuild()
