from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StartupConfigQuery(BaseModel):
    dcim_device: StartupConfigQueryDcimDevice = Field(alias="DcimDevice")


class StartupConfigQueryDcimDevice(BaseModel):
    edges: list[StartupConfigQueryDcimDeviceEdges]


class StartupConfigQueryDcimDeviceEdges(BaseModel):
    node: StartupConfigQueryDcimDeviceEdgesNode | None


class StartupConfigQueryDcimDeviceEdgesNode(BaseModel):
    name: StartupConfigQueryDcimDeviceEdgesNodeName | None
    loopback_ip: StartupConfigQueryDcimDeviceEdgesNodeLoopbackIp
    interfaces: StartupConfigQueryDcimDeviceEdgesNodeInterfaces


class StartupConfigQueryDcimDeviceEdgesNodeName(BaseModel):
    value: str | None


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIp(BaseModel):
    node: StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNode | None


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNode(BaseModel):
    address: StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress | None


class StartupConfigQueryDcimDeviceEdgesNodeLoopbackIpNodeAddress(BaseModel):
    ip: str | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfaces(BaseModel):
    edges: list[StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdges] | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdges(BaseModel):
    node: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNode | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNode(BaseModel):
    typename__: Literal["DcimInterface", "InterfacePhysical", "InterfaceVirtual"] = Field(alias="__typename")
    name: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeName | None
    description: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDescription | None
    role: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeRole | None
    status: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeStatus | None
    ip_address: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddress


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeName(BaseModel):
    value: str | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeDescription(BaseModel):
    value: str | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeRole(BaseModel):
    value: str | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeStatus(BaseModel):
    value: str | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddress(BaseModel):
    node: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNode(BaseModel):
    address: StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress | None


class StartupConfigQueryDcimDeviceEdgesNodeInterfacesEdgesNodeIpAddressNodeAddress(BaseModel):
    value: str | None


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
