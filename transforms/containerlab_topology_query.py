"""Typed models for the ``containerlab_topology`` GraphQL response.

Lean by design: Pydantic v2 ignores unknown fields, so only the attributes the
transform actually traverses are modelled. Classes are declared bottom-up so no
forward references are required.
"""

from pydantic import BaseModel, Field


class Value(BaseModel):
    """A scalar attribute wrapper (``{ "value": ... }``)."""

    value: str | None = None


class NamedNode(BaseModel):
    name: Value | None = None


class NameRelation(BaseModel):
    node: NamedNode | None = None


class AddressNode(BaseModel):
    address: Value | None = None


class AddressRelation(BaseModel):
    node: AddressNode | None = None


class ConnectorNode(BaseModel):
    id: str | None = None


class Connector(BaseModel):
    node: ConnectorNode | None = None


class InterfaceNode(BaseModel):
    connector: Connector | None = None


class InterfaceEdge(BaseModel):
    node: InterfaceNode | None = None


class Interfaces(BaseModel):
    edges: list[InterfaceEdge] = Field(default_factory=list)


class DeviceNode(BaseModel):
    typename: str | None = Field(default=None, alias="__typename")
    id: str | None = None
    name: Value | None = None
    role: Value | None = None
    device_type: NameRelation | None = None
    mgmt_ip: AddressRelation | None = None
    interfaces: Interfaces | None = None


class DeviceEdge(BaseModel):
    node: DeviceNode | None = None


class Devices(BaseModel):
    edges: list[DeviceEdge] = Field(default_factory=list)


class RackNode(BaseModel):
    devices: Devices | None = None


class RackEdge(BaseModel):
    node: RackNode | None = None


class Racks(BaseModel):
    edges: list[RackEdge] = Field(default_factory=list)


class ChildNode(BaseModel):
    typename: str | None = Field(default=None, alias="__typename")
    devices: Devices | None = None
    racks: Racks | None = None


class ChildEdge(BaseModel):
    node: ChildNode | None = None


class Children(BaseModel):
    edges: list[ChildEdge] = Field(default_factory=list)


class FabricNode(BaseModel):
    name: Value | None = None
    children: Children | None = None


class FabricEdge(BaseModel):
    node: FabricNode | None = None


class Fabric(BaseModel):
    edges: list[FabricEdge] = Field(default_factory=list)


class ContainerLabTopologyQuery(BaseModel):
    """Root model for the ``containerlab_topology`` query response."""

    network_fabric: Fabric = Field(alias="NetworkFabric")
