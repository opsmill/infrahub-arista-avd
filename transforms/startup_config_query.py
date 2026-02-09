from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StartupConfigQuery(BaseModel):
    network_device: "StartupConfigQueryNetworkDevice" = Field(alias="NetworkDevice")


class StartupConfigQueryNetworkDevice(BaseModel):
    edges: list["StartupConfigQueryNetworkDeviceEdges"]


class StartupConfigQueryNetworkDeviceEdges(BaseModel):
    node: Optional["StartupConfigQueryNetworkDeviceEdgesNode"]


class StartupConfigQueryNetworkDeviceEdgesNode(BaseModel):
    hostname: Optional["StartupConfigQueryNetworkDeviceEdgesNodeHostname"]
    loopback_ip: "StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIp"
    interfaces: "StartupConfigQueryNetworkDeviceEdgesNodeInterfaces"


class StartupConfigQueryNetworkDeviceEdgesNodeHostname(BaseModel):
    value: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIp(BaseModel):
    node: Optional["StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIpNode"]


class StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIpNode(BaseModel):
    address: Optional["StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIpNodeAddress"]


class StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIpNodeAddress(BaseModel):
    ip: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfaces(BaseModel):
    edges: list["StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdges"]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: Optional["StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode"]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode(BaseModel):
    name: Optional["StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName"]
    description: Optional[
        "StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeDescription"
    ]
    role: Optional["StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole"]
    status: Optional[
        "StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeStatus"
    ]
    ip_address: "StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress"


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeName(BaseModel):
    value: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeDescription(BaseModel):
    value: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeRole(BaseModel):
    value: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeStatus(BaseModel):
    value: Optional[str]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress(BaseModel):
    node: Optional[
        "StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode"
    ]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode(
    BaseModel
):
    address: Optional[
        "StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress"
    ]


class StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress(
    BaseModel
):
    value: Optional[str]


StartupConfigQuery.model_rebuild()
StartupConfigQueryNetworkDevice.model_rebuild()
StartupConfigQueryNetworkDeviceEdges.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNode.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIp.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeLoopbackIpNode.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeInterfaces.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdges.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNode.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddress.model_rebuild()
StartupConfigQueryNetworkDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode.model_rebuild()
