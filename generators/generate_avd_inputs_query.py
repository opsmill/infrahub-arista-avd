from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class GenerateAvdInputsQuery(BaseModel):
    network_fabric: GenerateAvdInputsQueryNetworkFabric = Field(alias="NetworkFabric")


class GenerateAvdInputsQueryNetworkFabric(BaseModel):
    edges: list[GenerateAvdInputsQueryNetworkFabricEdges]


class GenerateAvdInputsQueryNetworkFabricEdges(BaseModel):
    node: GenerateAvdInputsQueryNetworkFabricEdgesNode | None


class GenerateAvdInputsQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: GenerateAvdInputsQueryNetworkFabricEdgesNodeName | None
    children: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren


class GenerateAvdInputsQueryNetworkFabricEdgesNodeName(BaseModel):
    value: str | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren(BaseModel):
    edges: list[GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges] | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges(BaseModel):
    node: Annotated[GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock | GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod, Field(discriminator="typename__")] | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric"] = Field(
        alias="__typename"
    )


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod(
    BaseModel
):
    typename__: Literal["NetworkPod"] = Field(alias="__typename")
    racks: (
        GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks
    )
    devices: (
        GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices
    )


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(
    BaseModel
):
    edges: list[
        GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(
    BaseModel
):
    node: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(
    BaseModel
):
    devices: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(
    BaseModel
):
    edges: list[GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges] | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(
    BaseModel
):
    node: Annotated[GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice | GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice, Field(discriminator="typename__")] | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: str | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName | None
    avd_artifact: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName(
    BaseModel
):
    value: str | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact(
    BaseModel
):
    node: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode(
    BaseModel
):
    hostvar_identifier: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarIdentifier | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarIdentifier(
    BaseModel
):
    value: str | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(
    BaseModel
):
    edges: list[
        GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(
    BaseModel
):
    node: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(
    BaseModel
):
    id: str
    name: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName | None
    avd_artifact: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName(
    BaseModel
):
    value: str | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact(
    BaseModel
):
    node: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode(
    BaseModel
):
    hostvar_identifier: GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarIdentifier | None


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarIdentifier(
    BaseModel
):
    value: str | None


GenerateAvdInputsQuery.model_rebuild()
GenerateAvdInputsQueryNetworkFabric.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode.model_rebuild()
