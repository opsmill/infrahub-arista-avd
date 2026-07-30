"""Render a ContainerLab topology (``topology.clab.yml``) from a NetworkFabric.

Each network device becomes a ContainerLab node whose kind and container image
come from ``DcimPlatform.containerlab_os`` / ``DcimPlatform.containerlab_image``,
and each device-to-device connection becomes a ContainerLab link. Interface names
are translated to their ContainerLab short form (``Ethernet27`` -> ``eth27``,
``Ethernet49/1`` -> ``eth49_1``).

Breakout names only resolve inside cEOS when the matching
``EosIntfMapping.json`` is mounted, so each node binds the file named by its
device type's ``containerlab_interface_mapping``.

``ComputePhysicalServer`` members render as Linux-kind nodes with a netplan bind
derived from the device name.

The collection/translation helpers are module-level pure functions so they can
be unit-tested without a live Infrahub connection.
"""

from __future__ import annotations

import collections
import ipaddress
import logging
import operator
import re
from pathlib import Path
from typing import Any, Protocol

import jinja2
from infrahub_sdk.transforms import InfrahubTransform

from .containerlab_topology_query import ContainerLabTopologyQuery, DeviceNode, ServerNode

logger = logging.getLogger(__name__)

# Roles with a validated ContainerLab representation. ``p``/``pe``/``rr`` are
# deliberately absent: they belong to the ISIS-LDP fabric, whose interface
# naming has not been validated here. Excluded devices are warned about, not
# dropped silently.
NETWORK_ROLES = frozenset({"super_spine", "spine", "leaf", "l2leaf", "border_leaf", "l2spine", "l3spine"})

INTERFACE_MAPPING_DIR = "configs/eos-intf-mapping"
INTERFACE_MAPPING_TARGET = "/mnt/flash/EosIntfMapping.json"
NETPLAN_DIR = "configs/servers"
NETPLAN_TARGET = "/etc/netplan/netplan.yaml"
STARTUP_CONFIG_DIR = "configs"

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_LINK_ENDPOINTS_QUERY_FILE = Path(__file__).parent / "containerlab_link_endpoints.gql"

# One endpoint of a link: (device_name, eos_interface_name).
Endpoint = tuple[str, str]


def link_endpoints_query() -> str:
    """The registered ``containerlab_link_endpoints`` query, read from disk.

    Kept in a ``.gql`` file rather than a string literal so the executed text
    and the file registered in ``.infrahub.yml`` cannot drift.
    """
    return _LINK_ENDPOINTS_QUERY_FILE.read_text()


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
    """Flattened view of a node needed for the topology."""

    def __init__(
        self,
        name: str,
        role: str | None,
        kind: str | None,
        image: str | None,
        mgmt: str | None,
        binds: list[str] | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.kind = kind
        self.image = image
        self.mgmt = mgmt
        self.binds = binds or []

    @property
    def mgmt_ipv4(self) -> str | None:
        """Bare host address (mask stripped) for the node's ``mgmt-ipv4``."""
        if not self.mgmt:
            return None
        return self.mgmt.split("/", 1)[0]


def iter_device_nodes(data: ContainerLabTopologyQuery) -> list[DeviceNode]:
    """Yield every device node under the fabric (pod devices + rack devices)."""
    nodes: list[DeviceNode] = []
    for pod in _iter_pods(data):
        if pod.devices is not None:
            nodes.extend(e.node for e in pod.devices.edges if e.node is not None)
        if pod.racks is not None:
            for rack_edge in pod.racks.edges:
                rack = rack_edge.node
                if rack is not None and rack.devices is not None:
                    nodes.extend(e.node for e in rack.devices.edges if e.node is not None)
    return nodes


def _iter_pods(data: ContainerLabTopologyQuery) -> list[Any]:
    fabric_edges = data.network_fabric.edges
    if not fabric_edges or fabric_edges[0].node is None:
        return []
    children = fabric_edges[0].node.children
    if children is None:
        return []
    return [e.node for e in children.edges if e.node is not None]


def fabric_rack_names(data: ContainerLabTopologyQuery) -> set[str]:
    """Names of every rack under the fabric.

    Used to scope servers, because ``LocationRack`` declares no inverse
    relationship to ``ComputePhysicalServer`` — so the server query cannot be
    filtered server-side.
    """
    names: set[str] = set()
    for pod in _iter_pods(data):
        if pod.racks is None:
            continue
        for rack_edge in pod.racks.edges:
            rack = rack_edge.node
            if rack is not None and rack.name and rack.name.value:
                names.add(rack.name.value)
    return names


def _platform(node: DeviceNode | ServerNode) -> tuple[str | None, str | None]:
    """Resolve ``(kind, image)`` for a node.

    Switches carry their platform through ``device_type``; servers have no
    ``device_type``, so the device's own ``platform`` is the fallback.
    """
    device_type = getattr(node, "device_type", None)
    if device_type is not None and device_type.node is not None and device_type.node.platform is not None:
        platform = device_type.node.platform.node
        if platform is not None:
            kind = platform.containerlab_os.value if platform.containerlab_os else None
            image = platform.containerlab_image.value if platform.containerlab_image else None
            if kind:
                return kind, image
    if node.platform is not None and node.platform.node is not None:
        platform = node.platform.node
        kind = platform.containerlab_os.value if platform.containerlab_os else None
        image = platform.containerlab_image.value if platform.containerlab_image else None
        return kind, image
    return None, None


def _interface_mapping(node: DeviceNode) -> str | None:
    device_type = node.device_type
    if device_type is not None and device_type.node is not None:
        mapping = device_type.node.containerlab_interface_mapping
        if mapping and mapping.value:
            return mapping.value
    return None


def _device_mgmt(node: DeviceNode) -> str | None:
    if node.mgmt_ip and node.mgmt_ip.node and node.mgmt_ip.node.address:
        return node.mgmt_ip.node.address.value
    return None


def _server_mgmt(node: ServerNode) -> str | None:
    if node.primary_address and node.primary_address.node and node.primary_address.node.address:
        return node.primary_address.node.address.value
    return None


def collect_devices(data: ContainerLabTopologyQuery) -> dict[str, DeviceInfo]:
    """Build a name -> DeviceInfo map for network devices (deduped)."""
    devices: dict[str, DeviceInfo] = {}
    for node in iter_device_nodes(data):
        if node.typename != "DcimDevice" or node.name is None or not node.name.value:
            continue
        name = node.name.value
        role = node.role.value if node.role else None
        if role not in NETWORK_ROLES:
            logger.warning("excluding device %s: role %r has no ContainerLab representation", name, role)
            continue
        if name in devices:
            continue
        kind, image = _platform(node)
        if not kind:
            logger.warning("excluding device %s: no containerlab_os on its platform", name)
            continue
        binds = []
        mapping = _interface_mapping(node)
        if mapping:
            binds.append(f"{INTERFACE_MAPPING_DIR}/{mapping}:{INTERFACE_MAPPING_TARGET}:ro")
        devices[name] = DeviceInfo(name=name, role=role, kind=kind, image=image, mgmt=_device_mgmt(node), binds=binds)
    return devices


def collect_servers(data: ContainerLabTopologyQuery) -> dict[str, DeviceInfo]:
    """Build a name -> DeviceInfo map for the fabric's servers."""
    rack_names = fabric_rack_names(data)
    servers: dict[str, DeviceInfo] = {}
    for edge in data.compute_physical_server.edges:
        node = edge.node
        if node is None or node.name is None or not node.name.value:
            continue
        name = node.name.value
        rack = node.rack.node.name.value if node.rack and node.rack.node and node.rack.node.name else None
        if rack not in rack_names:
            continue  # server belongs to a different fabric
        if name in servers:
            continue
        kind, image = _platform(node)
        if not kind:
            logger.warning("excluding server %s: no containerlab_os on its platform", name)
            continue
        servers[name] = DeviceInfo(
            name=name,
            role=None,
            kind=kind,
            image=image,
            mgmt=_server_mgmt(node),
            binds=[f"{NETPLAN_DIR}/{name}-netplan.yaml:{NETPLAN_TARGET}"],
        )
    return servers


def collect_link_ids(data: ContainerLabTopologyQuery) -> list[str]:
    """Collect the unique NetworkLink ids referenced by device interfaces."""
    return sorted(_link_roles(data))


def _link_roles(data: ContainerLabTopologyQuery) -> dict[str, str | None]:
    """Map link id -> role for every link reachable from a node's interfaces."""
    roles: dict[str, str | None] = {}
    nodes: list[Any] = list(iter_device_nodes(data))
    nodes.extend(e.node for e in data.compute_physical_server.edges if e.node is not None)
    for node in nodes:
        if node.interfaces is None:
            continue
        for iface_edge in node.interfaces.edges:
            iface = iface_edge.node
            if iface and iface.connector and iface.connector.node and iface.connector.node.id:
                connector = iface.connector.node
                role = connector.role.value if connector.role else None
                # Keep a non-null role if any endpoint reported one.
                if connector.id not in roles or roles[connector.id] is None:
                    roles[connector.id] = role
    return roles


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
    query = link_endpoints_query()
    batch_size = 50
    for i in range(0, len(link_ids), batch_size):
        batch = link_ids[i : i + batch_size]
        result = await client.execute_graphql(query=query, variables={"ids": batch}, branch_name=branch)
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
    """Build sorted ContainerLab links (endpoints translated).

    ``devices`` must contain every emitted node — switches and servers — so
    server-facing links are retained.
    """
    links: list[dict[str, str]] = []
    for (dev_a, if_a), (dev_b, if_b) in endpoints:
        if dev_a not in devices or dev_b not in devices:
            continue  # an endpoint was excluded; drop the dangling link
        a = f"{dev_a}:{clab_interface_name(if_a)}"
        b = f"{dev_b}:{clab_interface_name(if_b)}"
        # Order endpoints within a link for deterministic output.
        links.append({"a": min(a, b), "b": max(a, b)})
    links.sort(key=operator.itemgetter("a", "b"))
    return links


def mgmt_subnet(devices: dict[str, DeviceInfo]) -> str | None:
    """Derive the management IPv4 subnet from the devices' management IPs.

    Picks the most common subnet, breaking ties by lowest network address, so
    one mis-addressed device cannot displace the real management range and the
    result never depends on dict iteration order.
    """
    counts: collections.Counter[ipaddress.IPv4Network | ipaddress.IPv6Network] = collections.Counter()
    for info in devices.values():
        if info.mgmt and "/" in info.mgmt:
            counts[ipaddress.ip_interface(info.mgmt).network] += 1
    if not counts:
        return None
    best = min(counts.items(), key=lambda item: (-item[1], item[0].network_address.packed))
    return str(best[0])


def build_kinds(devices: dict[str, DeviceInfo]) -> list[dict[str, Any]]:
    """One entry per distinct node kind, with its image, sorted by kind.

    Grouped in Python rather than the template: the template stays free of
    aggregation filters, which are unavailable to pure-Jinja2 transforms.

    ``startup_config`` is set for kinds whose nodes are network devices (they
    have a role). Servers have no role and boot from their netplan bind, so
    pointing them at an EOS startup-config would be wrong.
    """
    images: dict[str, str | None] = {}
    needs_config: dict[str, bool] = {}
    for info in sorted(devices.values(), key=lambda d: d.name):
        if not info.kind:
            continue
        if info.kind not in images:
            images[info.kind] = info.image
            needs_config[info.kind] = False
        if info.role is not None:
            needs_config[info.kind] = True
    return [{"name": kind, "image": images[kind], "startup_config": needs_config[kind]} for kind in sorted(images)]


def render_topology(fabric_name: str, devices: dict[str, DeviceInfo], links: list[dict[str, str]]) -> str:
    """Render the ContainerLab YAML for a fabric from prepared data."""
    nodes = [
        {"name": info.name, "kind": info.kind, "mgmt_ipv4": info.mgmt_ipv4, "binds": info.binds}
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
        kinds=build_kinds(devices),
        startup_config_dir=STARTUP_CONFIG_DIR,
        nodes=nodes,
        links=links,
    )


class ContainerLabTopology(InfrahubTransform):
    query = "containerlab_topology"

    async def transform(self, data: dict[str, Any]) -> str:
        parsed = ContainerLabTopologyQuery(**data)
        fabric_edges = parsed.network_fabric.edges
        fabric_node = fabric_edges[0].node if fabric_edges else None
        fabric_name = (
            fabric_node.name.value if fabric_node and fabric_node.name and fabric_node.name.value else "fabric"
        )

        nodes = collect_devices(parsed)
        nodes.update(collect_servers(parsed))
        link_ids = collect_link_ids(parsed)
        endpoints = await fetch_link_endpoints(self.client, link_ids, branch=self.branch_name)
        links = build_links(endpoints, nodes)
        return render_topology(fabric_name, nodes, links)
