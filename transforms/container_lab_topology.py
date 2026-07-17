from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


class ContainerLabTopology(BaseModel):
    network_fabric: "ContainerLabTopologyNetworkFabric" = Field(alias="NetworkFabric")


class ContainerLabTopologyNetworkFabric(BaseModel):
    edges: list["ContainerLabTopologyNetworkFabricEdges"]


class ContainerLabTopologyNetworkFabricEdges(BaseModel):
    node: Optional["ContainerLabTopologyNetworkFabricEdgesNode"]


class ContainerLabTopologyNetworkFabricEdgesNode(BaseModel):
    name: Optional["ContainerLabTopologyNetworkFabricEdgesNodeName"]
    children: "ContainerLabTopologyNetworkFabricEdgesNodeChildren"


class ContainerLabTopologyNetworkFabricEdgesNodeName(BaseModel):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildren(BaseModel):
    edges: Optional[list["ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdges"]]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdges(BaseModel):
    node: Optional[
        Annotated[
            Union[
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock",
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkBuildingBlock(
    BaseModel
):
    typename__: Literal["NetworkBuildingBlock", "NetworkFabric"] = Field(
        alias="__typename"
    )


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod(BaseModel):
    typename__: Literal["NetworkPod"] = Field(alias="__typename")
    devices: (
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices"
    )
    racks: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(
    BaseModel
):
    edges: list[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(
    BaseModel
):
    id: str
    name: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName"
    ]
    role: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRole"
    ]
    device_type: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceType"
    mgmt_ip: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIp"
    interfaces: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeRole(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceType(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceTypeNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceTypeNode(
    BaseModel
):
    name: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceTypeNodeName"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceTypeNodeName(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIp(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIpNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIpNode(
    BaseModel
):
    address: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIpNodeAddress"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIpNodeAddress(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces(
    BaseModel
):
    edges: Optional[
        list[
            "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges"
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface",
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpoint",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal[
        "DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"
    ] = Field(alias="__typename")


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    connector: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpointConnector"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpointConnector(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpointConnectorNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpointConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(
    BaseModel
):
    edges: list[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(
    BaseModel
):
    devices: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(
    BaseModel
):
    edges: Optional[
        list[
            "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges"
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice",
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimPhysicalDevice(
    BaseModel
):
    typename__: Literal["DcimPhysicalDevice"] = Field(alias="__typename")


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
    BaseModel
):
    typename__: Literal["DcimDevice"] = Field(alias="__typename")
    id: str
    name: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName"
    ]
    role: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRole"
    ]
    device_type: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceType"
    mgmt_ip: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIp"
    interfaces: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceRole(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceType(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceTypeNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceTypeNode(
    BaseModel
):
    name: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceTypeNodeName"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceTypeNodeName(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIp(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIpNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIpNode(
    BaseModel
):
    address: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIpNodeAddress"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIpNodeAddress(
    BaseModel
):
    value: Optional[str]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces(
    BaseModel
):
    edges: Optional[
        list[
            "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges"
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges(
    BaseModel
):
    node: Optional[
        Annotated[
            Union[
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface",
                "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint",
            ],
            Field(discriminator="typename__"),
        ]
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimInterface(
    BaseModel
):
    typename__: Literal[
        "DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"
    ] = Field(alias="__typename")


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint(
    BaseModel
):
    typename__: Literal["DcimEndpoint"] = Field(alias="__typename")
    connector: "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector"


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector(
    BaseModel
):
    node: Optional[
        "ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode"
    ]


class ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnectorNode(
    BaseModel
):
    typename__: Literal["DcimConnector", "NetworkLink"] = Field(alias="__typename")
    id: Optional[str]


ContainerLabTopology.model_rebuild()
ContainerLabTopologyNetworkFabric.model_rebuild()
ContainerLabTopologyNetworkFabricEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildren.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceType.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeDeviceTypeNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIp.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeMgmtIpNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfaces.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpoint.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeInterfacesEdgesNodeDcimEndpointConnector.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceType.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceDeviceTypeNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIp.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceMgmtIpNode.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfaces.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdges.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpoint.model_rebuild()
ContainerLabTopologyNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceInterfacesEdgesNodeDcimEndpointConnector.model_rebuild()
