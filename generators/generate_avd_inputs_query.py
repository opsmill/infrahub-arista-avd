from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class GenerateAvdInputsQuery(BaseModel):
    network_fabric: "GenerateAvdInputsQueryNetworkFabric" = Field(alias="NetworkFabric")


class GenerateAvdInputsQueryNetworkFabric(BaseModel):
    edges: list["GenerateAvdInputsQueryNetworkFabricEdges"]


class GenerateAvdInputsQueryNetworkFabricEdges(BaseModel):
    node: Optional["GenerateAvdInputsQueryNetworkFabricEdgesNode"]


class GenerateAvdInputsQueryNetworkFabricEdgesNode(BaseModel):
    id: str
    name: Optional["GenerateAvdInputsQueryNetworkFabricEdgesNodeName"]
    children: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren(BaseModel):
    edges: Optional[list["GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges"]]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock",
                "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod",
            ],
            Field(discriminator="typename__"),
        ]
    ]


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
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks"
    )
    devices: (
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices"
    )


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(
    BaseModel
):
    edges: list[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(
    BaseModel
):
    devices: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(
    BaseModel
):
    edges: Optional[
        list[
            "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges"
        ]
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice",
                "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: Optional[str]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName"
    ]
    avd_artifact: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode(
    BaseModel
):
    hostvar_file: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFile"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFile(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFileNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFileNode(
    BaseModel
):
    id: str


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(
    BaseModel
):
    edges: list[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName"
    ]
    avd_artifact: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode(
    BaseModel
):
    hostvar_file: "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFile"


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFile(
    BaseModel
):
    node: Optional[
        "GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFileNode"
    ]


class GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFileNode(
    BaseModel
):
    id: str


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
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFile.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode.model_rebuild()
GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFile.model_rebuild()
