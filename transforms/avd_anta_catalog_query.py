from __future__ import annotations

from pydantic import BaseModel, Field


class AvdAntaCatalogQuery(BaseModel):
    # `target` is the requested device (filtered by name); `dcim_device` is every
    # device, used to gather fabric-wide structured configs for the catalog.
    target: DeviceList = Field(alias="target")
    dcim_device: DeviceList = Field(alias="DcimDevice")


class DeviceList(BaseModel):
    edges: list[DeviceEdge]


class DeviceEdge(BaseModel):
    node: DeviceNode | None


class DeviceNode(BaseModel):
    id: str
    name: StrValue | None = None
    pod: Pod | None = None
    avd_artifact: AvdArtifact | None = None


class Pod(BaseModel):
    node: PodNode | None


class PodNode(BaseModel):
    id: str
    parent: Parent | None = None


class Parent(BaseModel):
    node: ParentNode | None


class ParentNode(BaseModel):
    id: str
    typename: str | None = Field(default=None, alias="__typename")
    name: StrValue | None = None
    anta_enabled: BoolValue | None = None


class AvdArtifact(BaseModel):
    node: AvdArtifactNode | None


class AvdArtifactNode(BaseModel):
    id: str
    structured_config_file: StructuredConfigFile


class StructuredConfigFile(BaseModel):
    node: StructuredConfigFileNode | None


class StructuredConfigFileNode(BaseModel):
    id: str


class StrValue(BaseModel):
    value: str | None


class BoolValue(BaseModel):
    value: bool | None


AvdAntaCatalogQuery.model_rebuild()
DeviceList.model_rebuild()
DeviceEdge.model_rebuild()
DeviceNode.model_rebuild()
Pod.model_rebuild()
PodNode.model_rebuild()
Parent.model_rebuild()
ParentNode.model_rebuild()
AvdArtifact.model_rebuild()
AvdArtifactNode.model_rebuild()
StructuredConfigFile.model_rebuild()
StructuredConfigFileNode.model_rebuild()
