from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class StartupConfigQuery(BaseModel):
    dcim_device: "StartupConfigQueryDcimDevice" = Field(alias="DcimDevice")


class StartupConfigQueryDcimDevice(BaseModel):
    edges: list["StartupConfigQueryDcimDeviceEdges"]


class StartupConfigQueryDcimDeviceEdges(BaseModel):
    node: Optional["StartupConfigQueryDcimDeviceEdgesNode"]


class StartupConfigQueryDcimDeviceEdgesNode(BaseModel):
    name: Optional["StartupConfigQueryDcimDeviceEdgesNodeName"]
    loopback_ip: "StartupConfigQueryDcimDeviceEdgesNodeLoopbackIp"
    interfaces: "StartupConfigQueryDcimDeviceEdgesNodeInterfaces"


class StartupConfigQueryDcimDeviceEdgesNodeName(BaseModel):
    value: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIp(BaseModel):
    node: Optional["StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNode"]


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNode(BaseModel):
    address: Optional["StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress"]


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress(BaseModel):
    ip: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeInterfaces(BaseModel):
    edges: Optional[list["StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdges"]]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: Optional["StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNode"]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNode(BaseModel):
    typename__: Literal[
        "DcimInterface", "InterfaceLag", "InterfacePhysical", "InterfaceVirtual"
    ] = Field(alias="__typename")
    name: Optional["StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeName"]
    description: Optional[
        "StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDescription"
    ]
    role: Optional["StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeRole"]
    status: Optional["StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeStatus"]
    ip_address: "StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddress"


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeName(BaseModel):
    value: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDescription(BaseModel):
    value: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeRole(BaseModel):
    value: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeStatus(BaseModel):
    value: Optional[str]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddress(BaseModel):
    node: Optional[
        "StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode"
    ]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode(BaseModel):
    address: Optional[
        "StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress"
    ]


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress(
    BaseModel
):
    value: Optional[str]


StartupConfigQuery.model_rebuild()
StartupConfigQueryDcimDevice.model_rebuild()
StartupConfigQueryDcimDeviceEdges.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNode.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeLoopbackIp.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNode.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeInterfaces.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdges.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNode.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddress.model_rebuild()
StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode.model_rebuild()
