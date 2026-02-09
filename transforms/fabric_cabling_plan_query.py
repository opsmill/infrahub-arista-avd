from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class FabricCablingPlanQuery(BaseModel):
    network_fabric: "FabricCablingPlanQueryNetworkFabric" = Field(alias="NetworkFabric")


class FabricCablingPlanQueryNetworkFabric(BaseModel):
    edges: list["FabricCablingPlanQueryNetworkFabricEdges"]


class FabricCablingPlanQueryNetworkFabricEdges(BaseModel):
    node: Optional["FabricCablingPlanQueryNetworkFabricEdgesNode"]


class FabricCablingPlanQueryNetworkFabricEdgesNode(BaseModel):
    children: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildren"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildren(BaseModel):
    edges: Optional[list["FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges"]]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock",
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod(
    BaseModel
):
    typename__: Literal["NetworkPod"] = Field(alias="__typename")
    id: str
    devices: (
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices"
    )


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(
    BaseModel
):
    edges: list[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(
    BaseModel
):
    id: str
    rack: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack"
    interfaces: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRackNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRackNode(
    BaseModel
):
    id: str


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces(
    BaseModel
):
    edges: list[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNode(
    BaseModel
):
    id: str
    link: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeLink"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeLink(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeLinkNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeLinkNode(
    BaseModel
):
    id: str


FabricCablingPlanQuery.model_rebuild()
FabricCablingPlanQueryNetworkFabric.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildren.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRack.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeLink.model_rebuild()
