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


class PlatformNode(BaseModel):
    """``DcimPlatform`` — supplies the ContainerLab node kind and image."""

    containerlab_os: Value | None = None
    containerlab_image: Value | None = None


class PlatformRelation(BaseModel):
    node: PlatformNode | None = None


class DeviceTypeNode(BaseModel):
    """``DcimDeviceType`` — supplies the interface-mapping filename."""

    name: Value | None = None
    containerlab_interface_mapping: Value | None = None
    platform: PlatformRelation | None = None


class DeviceTypeRelation(BaseModel):
    node: DeviceTypeNode | None = None


class ConnectorNode(BaseModel):
    id: str | None = None
    # Present only on NetworkLink (via inline fragment); ``dci`` marks
    # inter-domain links.
    role: Value | None = None


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
    device_type: DeviceTypeRelation | None = None
    platform: PlatformRelation | None = None
    mgmt_ip: AddressRelation | None = None
    interfaces: Interfaces | None = None


class DeviceEdge(BaseModel):
    node: DeviceNode | None = None


class Devices(BaseModel):
    edges: list[DeviceEdge] = Field(default_factory=list)


class RackNode(BaseModel):
    name: Value | None = None
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


class ServerNode(BaseModel):
    """``ComputePhysicalServer`` — rendered as a Linux-kind ContainerLab node.

    Servers have no ``mgmt_ip``: that relationship is a ``DcimDevice``-only
    extension, so the inherited ``primary_address`` is used instead.
    """

    typename: str | None = Field(default=None, alias="__typename")
    id: str | None = None
    name: Value | None = None
    rack: NameRelation | None = None
    platform: PlatformRelation | None = None
    primary_address: AddressRelation | None = None
    interfaces: Interfaces | None = None


class ServerEdge(BaseModel):
    node: ServerNode | None = None


class Servers(BaseModel):
    edges: list[ServerEdge] = Field(default_factory=list)


class ContainerLabTopologyQuery(BaseModel):
    """Root model for the ``containerlab_topology`` query response."""

    network_fabric: Fabric = Field(alias="NetworkFabric")
    # Unfiltered: LocationRack declares no inverse to ComputePhysicalServer, so
    # servers are filtered to the fabric's racks in Python.
    compute_physical_server: Servers = Field(default_factory=Servers, alias="ComputePhysicalServer")
