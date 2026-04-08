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
    racks: (
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks"
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
    edges: Optional[
        list[
            "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges"
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface",
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal["DcimInterface", "InterfaceLag", "InterfaceVirtual"] = Field(
        alias="__typename"
    )
    id: Optional[str]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical(
    BaseModel
):
    typename__: Literal["InterfacePhysical"] = Field(alias="__typename")
    id: str
    connector: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(
    BaseModel
):
    edges: list[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(
    BaseModel
):
    id: str
    devices: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(
    BaseModel
):
    edges: Optional[
        list[
            "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges"
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice",
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")
    id: Optional[str]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    rack: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack"
    interfaces: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRackNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRackNode(
    BaseModel
):
    id: str


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces(
    BaseModel
):
    edges: Optional[
        list[
            "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges"
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface",
                "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal[
        "DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"
    ] = Field(alias="__typename")
    id: Optional[str]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    id: Optional[str]
    connector: "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector"


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector(
    BaseModel
):
    node: Optional[
        "FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode"
    ]


class FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]


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
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysical.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRack.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint.model_rebuild()
FabricCablingPlanQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector.model_rebuild()
