"""Render a ContainerLab topology (``topology.clab.yml``) from a NetworkFabric.

Each network device (super_spine / spine / leaf / l2leaf) becomes an Arista
cEOS node; each device-to-device connection becomes a ContainerLab link.
Interface names are translated to their ContainerLab short form
(``Ethernet27`` -> ``eth27``, ``Ethernet1/1`` -> ``eth1_1``), which is cEOS's
default mapping — so no per-node ``EosIntfMapping.json`` bind is required for the
plain ``Ethernet<N>`` interfaces this fabric uses today.

Per-device-type interface-mapping files (bound into each node) are planned as a
separate schema-first cycle: a ``CoreFileObject`` attached to ``DcimDeviceType``
that the transform reads via ``device.device_type``. Until that lands, link
endpoints use the algorithmic translation below.

The collection/translation helpers are module-level pure functions so they can
be unit-tested without a live Infrahub connection.
"""

from __future__ import annotations

import ipaddress
import operator
import re
from pathlib import Path
from typing import Any, Protocol

import jinja2
from infrahub_sdk.transforms import InfrahubTransform

from .containerlab_topology_query import ContainerLabTopologyQuery, DeviceNode

CEOS_IMAGE = "arista/ceos:4.36.0.1F"
CEOS_KIND = "arista_ceos"
NETWORK_ROLES = {"super_spine", "spine", "leaf", "l2leaf"}

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# One endpoint of a link: (device_name, eos_interface_name).
Endpoint = tuple[str, str]

_LINK_ENDPOINTS_QUERY = """
query($ids: [ID!]) {
    NetworkLink(ids: $ids) {
        edges { node { id connected_endpoints { edges { node {
            __typename
            ... on DcimInterface { name { value } device { node { ... on DcimDevice { name { value } } } } }
            ... on InterfacePhysical { name { value } device { node { ... on DcimDevice { name { value } } } } }
        } } } } }
    }
}
"""


class GraphQLClient(Protocol):
    """Minimal client surface used by :func:`fetch_link_endpoints`."""

    async def execute_graphql(
        self, query: str, variables: dict[str, Any], branch_name: str | None = None
    ) -> dict[str, Any]: ...


def clab_interface_name(eos_name: str) -> str:
    """Translate an EOS interface name to its ContainerLab short form.

    ``Ethernet27`` -> ``eth27``; ``Ethernet1/1`` -> ``eth1_1``. Names that are
    not ``Ethernet*`` are returned with ``/`` -> ``_`` as a best effort
    (management/other interfaces are not used for links).
    """
    match = re.fullmatch(r"Ethernet(.+)", eos_name)
    if match:
        return "eth" + match.group(1).replace("/", "_")
    return eos_name.replace("/", "_")


class DeviceInfo:
    """Flattened view of a network device needed for the topology."""

    def __init__(self, name: str, role: str, model: str | None, mgmt: str | None) -> None:
        self.name = name
        self.role = role
        self.model = model
        self.mgmt = mgmt

    @property
    def mgmt_ipv4(self) -> str | None:
        """Bare host address (mask stripped) for the node's ``mgmt-ipv4``."""
        if not self.mgmt:
            return None
        return self.mgmt.split("/", 1)[0]


def iter_device_nodes(data: ContainerLabTopologyQuery) -> list[DeviceNode]:
    """Yield every device node under the fabric (pod devices + rack devices)."""
    nodes: list[DeviceNode] = []
    fabric_edges = data.network_fabric.edges
    if not fabric_edges or fabric_edges[0].node is None:
        return nodes
    children = fabric_edges[0].node.children
    if children is None:
        return nodes

    for child_edge in children.edges:
        pod = child_edge.node
        if pod is None:
            continue
        if pod.devices is not None:
            nodes.extend(e.node for e in pod.devices.edges if e.node is not None)
        if pod.racks is not None:
            for rack_edge in pod.racks.edges:
                rack = rack_edge.node
                if rack is not None and rack.devices is not None:
                    nodes.extend(e.node for e in rack.devices.edges if e.node is not None)
    return nodes


def _device_model(node: DeviceNode) -> str | None:
    if node.device_type and node.device_type.node and node.device_type.node.name:
        return node.device_type.node.name.value
    return None


def _device_mgmt(node: DeviceNode) -> str | None:
    if node.mgmt_ip and node.mgmt_ip.node and node.mgmt_ip.node.address:
        return node.mgmt_ip.node.address.value
    return None


def collect_devices(data: ContainerLabTopologyQuery) -> dict[str, DeviceInfo]:
    """Build a name -> DeviceInfo map for network devices (deduped)."""
    devices: dict[str, DeviceInfo] = {}
    for node in iter_device_nodes(data):
        if node.typename != "DcimDevice" or node.name is None or not node.name.value:
            continue
        role = node.role.value if node.role else None
        if role not in NETWORK_ROLES:
            continue
        name = node.name.value
        if name in devices:
            continue
        devices[name] = DeviceInfo(name=name, role=role, model=_device_model(node), mgmt=_device_mgmt(node))
    return devices


def collect_link_ids(data: ContainerLabTopologyQuery) -> list[str]:
    """Collect the unique NetworkLink ids referenced by device interfaces."""
    link_ids: set[str] = set()
    for node in iter_device_nodes(data):
        if node.interfaces is None:
            continue
        for iface_edge in node.interfaces.edges:
            iface = iface_edge.node
            if iface and iface.connector and iface.connector.node and iface.connector.node.id:
                link_ids.add(iface.connector.node.id)
    return sorted(link_ids)


def _parse_endpoint(node: dict[str, Any]) -> Endpoint | None:
    iface = (node.get("name") or {}).get("value")
    device = ((node.get("device") or {}).get("node") or {}).get("name", {}).get("value")
    if iface and device:
        return (device, iface)
    return None


async def fetch_link_endpoints(
    client: GraphQLClient, link_ids: list[str], branch: str | None = None
) -> list[tuple[Endpoint, Endpoint]]:
    """Fetch both endpoints (device name + interface name) for each link.

    ``branch`` scopes the query to the render branch — essential for artifact
    generation, where the devices/links live on a branch, not ``main``.
    """
    pairs: list[tuple[Endpoint, Endpoint]] = []
    batch_size = 50
    for i in range(0, len(link_ids), batch_size):
        batch = link_ids[i : i + batch_size]
        result = await client.execute_graphql(
            query=_LINK_ENDPOINTS_QUERY, variables={"ids": batch}, branch_name=branch
        )
        for edge in result.get("NetworkLink", {}).get("edges", []):
            endpoints = edge.get("node", {}).get("connected_endpoints", {}).get("edges", [])
            if len(endpoints) != 2:
                continue
            first = _parse_endpoint(endpoints[0].get("node") or {})
            second = _parse_endpoint(endpoints[1].get("node") or {})
            if first and second:
                pairs.append((first, second))
    return pairs


def build_links(endpoints: list[tuple[Endpoint, Endpoint]], devices: dict[str, DeviceInfo]) -> list[dict[str, str]]:
    """Build sorted, network-only ContainerLab links (endpoints translated)."""
    links: list[dict[str, str]] = []
    for (dev_a, if_a), (dev_b, if_b) in endpoints:
        if dev_a not in devices or dev_b not in devices:
            continue  # v1: network-device links only (skip servers/unknowns)
        a = f"{dev_a}:{clab_interface_name(if_a)}"
        b = f"{dev_b}:{clab_interface_name(if_b)}"
        # Order endpoints within a link for deterministic output.
        links.append({"a": min(a, b), "b": max(a, b)})
    links.sort(key=operator.itemgetter("a", "b"))
    return links


def mgmt_subnet(devices: dict[str, DeviceInfo]) -> str | None:
    """Derive the management IPv4 subnet from the devices' management IPs."""
    for info in devices.values():
        if info.mgmt and "/" in info.mgmt:
            return str(ipaddress.ip_interface(info.mgmt).network)
    return None


def render_topology(fabric_name: str, devices: dict[str, DeviceInfo], links: list[dict[str, str]]) -> str:
    """Render the ContainerLab YAML for a fabric from prepared data."""
    nodes = [
        {"name": info.name, "kind": CEOS_KIND, "mgmt_ipv4": info.mgmt_ipv4}
        for info in sorted(devices.values(), key=lambda d: d.name)
    ]
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        # YAML output, not HTML: escaping would corrupt values. select_autoescape
        # leaves .j2 templates unescaped while satisfying the linter.
        autoescape=jinja2.select_autoescape(),
    )
    return env.get_template("containerlab_topology.j2").render(
        name=fabric_name,
        mgmt_network=f"clab-{fabric_name}-mgmt",
        mgmt_subnet=mgmt_subnet(devices),
        image=CEOS_IMAGE,
        kind=CEOS_KIND,
        nodes=nodes,
        links=links,
    )


class ContainerLabTopology(InfrahubTransform):
    query = "containerlab_topology"

    async def transform(self, data: dict[str, Any]) -> str:
        parsed = ContainerLabTopologyQuery(**data)
        fabric_edges = parsed.network_fabric.edges
        fabric_node = fabric_edges[0].node if fabric_edges else None
        fabric_name = fabric_node.name.value if fabric_node and fabric_node.name and fabric_node.name.value else "fabric"

        devices = collect_devices(parsed)
        link_ids = collect_link_ids(parsed)
        endpoints = await fetch_link_endpoints(self.client, link_ids, branch=self.branch_name)
        links = build_links(endpoints, devices)
        return render_topology(fabric_name, devices, links)
