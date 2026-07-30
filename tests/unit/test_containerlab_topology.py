"""Unit tests for the ContainerLab topology transform helpers."""

from __future__ import annotations

import operator
import re
from typing import Any

import pytest
import yaml

from transforms.containerlab_topology import (
    DeviceInfo,
    build_kinds,
    build_links,
    clab_interface_name,
    collect_devices,
    collect_link_ids,
    collect_servers,
    fabric_rack_names,
    fetch_link_endpoints,
    link_endpoints_query,
    mgmt_subnet,
    render_topology,
)
from transforms.containerlab_topology_query import ContainerLabTopologyQuery

CEOS_KIND = "arista_ceos"
CEOS_IMAGE = "arista/ceos:4.36.0.1F"
SPINE_MAPPING = "DCS-7050CX3-32S.json"
LEAF_MAPPING = "DCS-7050SX3-48YC8.json"

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _platform(kind: str | None = CEOS_KIND, image: str | None = CEOS_IMAGE) -> dict[str, Any]:
    return {"node": {"containerlab_os": {"value": kind}, "containerlab_image": {"value": image}}}


def _interfaces(link_ids: list[str], role: str | None = None) -> dict[str, Any]:
    return {
        "edges": [
            {
                "node": {
                    "__typename": "DcimEndpoint",
                    "connector": {"node": {"id": lid, "role": {"value": role} if role else None}},
                }
            }
            for lid in link_ids
        ]
    }


def _device(
    name: str,
    role: str,
    mgmt: str | None,
    iface_link_ids: list[str],
    model: str | None = None,
    mapping: str | None = None,
    kind: str | None = CEOS_KIND,
    image: str | None = CEOS_IMAGE,
    link_role: str | None = None,
) -> dict[str, Any]:
    return {
        "__typename": "DcimDevice",
        "id": name,
        "name": {"value": name},
        "role": {"value": role},
        "device_type": {
            "node": {
                "name": {"value": model},
                "containerlab_interface_mapping": {"value": mapping} if mapping else None,
                "platform": _platform(kind, image),
            }
        },
        "platform": _platform(kind, image),
        "mgmt_ip": {"node": {"address": {"value": mgmt}}} if mgmt else {"node": None},
        "interfaces": _interfaces(iface_link_ids, link_role),
    }


def _server(
    name: str,
    rack: str,
    address: str | None = None,
    iface_link_ids: list[str] | None = None,
    kind: str | None = "linux",
    image: str | None = "lab-server",
) -> dict[str, Any]:
    return {
        "__typename": "ComputePhysicalServer",
        "id": name,
        "name": {"value": name},
        "rack": {"node": {"name": {"value": rack}}},
        "platform": _platform(kind, image),
        "primary_address": {"node": {"address": {"value": address}}} if address else {"node": None},
        "interfaces": _interfaces(iface_link_ids or []),
    }


def _query(
    pod_devices: list[dict[str, Any]],
    rack_devices: list[dict[str, Any]] | None = None,
    servers: list[dict[str, Any]] | None = None,
    rack_name: str = "RACK-1",
) -> ContainerLabTopologyQuery:
    pod = {
        "__typename": "NetworkPod",
        "devices": {"edges": [{"node": d} for d in pod_devices]},
        "racks": {
            "edges": [
                {
                    "node": {
                        "name": {"value": rack_name},
                        "devices": {"edges": [{"node": d} for d in (rack_devices or [])]},
                    }
                }
            ]
        },
    }
    return ContainerLabTopologyQuery(
        NetworkFabric={"edges": [{"node": {"name": {"value": "Fabric-X"}, "children": {"edges": [{"node": pod}]}}}]},
        ComputePhysicalServer={"edges": [{"node": s} for s in (servers or [])]},
    )


def _devs(*specs: tuple[str, str]) -> dict[str, DeviceInfo]:
    return {name: DeviceInfo(name=name, role=role, kind=CEOS_KIND, image=CEOS_IMAGE, mgmt=None) for name, role in specs}


# --------------------------------------------------------------------------
# interface name translation
# --------------------------------------------------------------------------


def test_clab_interface_name_simple() -> None:
    assert clab_interface_name("Ethernet27") == "eth27"


def test_clab_interface_name_breakout() -> None:
    assert clab_interface_name("Ethernet1/1") == "eth1_1"
    assert clab_interface_name("Ethernet1/1/3") == "eth1_1_3"


def test_clab_interface_name_matches_lab_forms() -> None:
    """The four interface forms used in lab/topology.clab.yml."""
    assert clab_interface_name("Ethernet1/1") == "eth1_1"  # spine downlink
    assert clab_interface_name("Ethernet49/1") == "eth49_1"  # leaf uplink
    assert clab_interface_name("Ethernet5") == "eth5"  # DCI
    assert clab_interface_name("Ethernet1") == "eth1"  # server-facing


# --------------------------------------------------------------------------
# DeviceInfo
# --------------------------------------------------------------------------


def test_device_info_mgmt_ipv4_strips_mask() -> None:
    assert DeviceInfo("d", "leaf", CEOS_KIND, CEOS_IMAGE, "10.255.0.18/24").mgmt_ipv4 == "10.255.0.18"
    assert DeviceInfo("d", "leaf", CEOS_KIND, CEOS_IMAGE, None).mgmt_ipv4 is None


# --------------------------------------------------------------------------
# role filtering
# --------------------------------------------------------------------------


def test_collect_devices_dedupes_and_filters_roles() -> None:
    leaf = _device("leaf1", "leaf", "10.0.0.1/24", ["L1"])
    unsupported = _device("pe1", "pe", "10.0.0.9/24", ["L2"])  # excluded role
    dupe = _device("leaf1", "leaf", "10.0.0.1/24", ["L1"])  # duplicate name -> collapsed
    devices = collect_devices(_query([leaf, dupe], rack_devices=[unsupported]))
    assert set(devices) == {"leaf1"}
    assert devices["leaf1"].role == "leaf"


def test_collect_devices_includes_border_leaf() -> None:
    """border_leaf was silently dropped, taking the DCI links with it."""
    border = _device("leaf1a", "border_leaf", "10.0.6.13/24", ["DCI1"], link_role="dci")
    devices = collect_devices(_query([border]))
    assert set(devices) == {"leaf1a"}
    assert devices["leaf1a"].role == "border_leaf"


@pytest.mark.parametrize("role", ["super_spine", "spine", "leaf", "l2leaf", "border_leaf", "l2spine", "l3spine"])
def test_collect_devices_accepts_all_supported_roles(role: str) -> None:
    assert set(collect_devices(_query([_device("d1", role, None, [])]))) == {"d1"}


@pytest.mark.parametrize("role", ["p", "pe", "rr", "server", "unknown"])
def test_collect_devices_rejects_unsupported_roles(role: str) -> None:
    assert collect_devices(_query([_device("d1", role, None, [])])) == {}


def test_collect_devices_warns_on_excluded_role(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        collect_devices(_query([_device("pe1", "pe", None, [])]))
    assert "pe1" in caplog.text
    assert "'pe'" in caplog.text or "pe" in caplog.text


def test_collect_devices_excludes_device_without_containerlab_os(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("WARNING"):
        devices = collect_devices(_query([_device("leaf1", "leaf", None, [], kind=None, image=None)]))
    assert devices == {}
    assert "leaf1" in caplog.text


# --------------------------------------------------------------------------
# kind / image / interface mapping from the graph
# --------------------------------------------------------------------------


def test_collect_devices_reads_kind_and_image_from_platform() -> None:
    devices = collect_devices(_query([_device("leaf1", "leaf", None, [], kind="arista_ceos", image="custom:1.0")]))
    assert devices["leaf1"].kind == "arista_ceos"
    assert devices["leaf1"].image == "custom:1.0"


def test_collect_devices_emits_interface_mapping_bind() -> None:
    devices = collect_devices(_query([_device("spine1", "spine", None, [], mapping=SPINE_MAPPING)]))
    assert devices["spine1"].binds == [f"configs/eos-intf-mapping/{SPINE_MAPPING}:/mnt/flash/EosIntfMapping.json:ro"]


def test_collect_devices_omits_bind_without_mapping() -> None:
    devices = collect_devices(_query([_device("spine1", "spine", None, [])]))
    assert devices["spine1"].binds == []


def test_build_kinds_groups_by_kind_with_images() -> None:
    devices = {
        "spine1": DeviceInfo("spine1", "spine", CEOS_KIND, CEOS_IMAGE, None),
        "leaf1": DeviceInfo("leaf1", "leaf", CEOS_KIND, CEOS_IMAGE, None),
        "srv1": DeviceInfo("srv1", None, "linux", "lab-server", None),
    }
    kinds = build_kinds(devices)
    assert kinds == [
        {"name": "arista_ceos", "image": CEOS_IMAGE, "startup_config": True},
        {"name": "linux", "image": "lab-server", "startup_config": False},
    ]


def test_build_kinds_is_sorted_and_deduped() -> None:
    devices = _devs(("z1", "leaf"), ("a1", "spine"))
    assert [k["name"] for k in build_kinds(devices)] == ["arista_ceos"]


# --------------------------------------------------------------------------
# servers
# --------------------------------------------------------------------------


def test_fabric_rack_names() -> None:
    assert fabric_rack_names(_query([], rack_name="DC1_ACCESS")) == {"DC1_ACCESS"}


def test_collect_servers_emits_linux_node_with_netplan_bind() -> None:
    query = _query([], servers=[_server("dc1-server", "DC1_ACCESS", "10.0.6.100/24")], rack_name="DC1_ACCESS")
    servers = collect_servers(query)
    assert set(servers) == {"dc1-server"}
    assert servers["dc1-server"].kind == "linux"
    assert servers["dc1-server"].image == "lab-server"
    assert servers["dc1-server"].mgmt_ipv4 == "10.0.6.100"
    assert servers["dc1-server"].binds == ["configs/servers/dc1-server-netplan.yaml:/etc/netplan/netplan.yaml"]


def test_collect_servers_without_address_omits_mgmt() -> None:
    """ComputePhysicalServer has no mgmt_ip and the seed data sets no address."""
    query = _query([], servers=[_server("dc1-server", "DC1_ACCESS")], rack_name="DC1_ACCESS")
    assert collect_servers(query)["dc1-server"].mgmt_ipv4 is None


def test_collect_servers_scopes_to_fabric_racks() -> None:
    """The server query is unfiltered, so out-of-fabric servers must be dropped."""
    query = _query([], servers=[_server("other-server", "OTHER_RACK")], rack_name="DC1_ACCESS")
    assert collect_servers(query) == {}


def test_collect_servers_excludes_server_without_platform(caplog: pytest.LogCaptureFixture) -> None:
    query = _query([], servers=[_server("s1", "R1", kind=None, image=None)], rack_name="R1")
    with caplog.at_level("WARNING"):
        assert collect_servers(query) == {}
    assert "s1" in caplog.text


# --------------------------------------------------------------------------
# links
# --------------------------------------------------------------------------


def test_collect_link_ids_unique_sorted() -> None:
    a = _device("leaf1", "leaf", None, ["L2", "L1"])
    b = _device("spine1", "spine", None, ["L1", "L3"])
    assert collect_link_ids(_query([a, b])) == ["L1", "L2", "L3"]


def test_collect_link_ids_includes_server_links() -> None:
    leaf = _device("leaf1", "leaf", None, ["L1"])
    srv = _server("dc1-server", "RACK-1", iface_link_ids=["L2"])
    assert collect_link_ids(_query([leaf], servers=[srv])) == ["L1", "L2"]


def test_build_links_translates_both_ends_and_orders() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"))
    links = build_links([(("spine1", "Ethernet1"), ("leaf1", "Ethernet49"))], devices)
    assert links == [{"a": "leaf1:eth49", "b": "spine1:eth1"}]


def test_build_links_skips_unknown_device_endpoints() -> None:
    devices = _devs(("leaf1", "leaf"))
    assert build_links([(("leaf1", "Ethernet1"), ("ghost", "eth1"))], devices) == []


def test_build_links_retains_server_links() -> None:
    """Server-facing links used to be dropped; servers are now emitted nodes."""
    devices = _devs(("leaf2a", "leaf"))
    devices["dc1-server"] = DeviceInfo("dc1-server", None, "linux", "lab-server", None)
    links = build_links([(("dc1-server", "Ethernet1"), ("leaf2a", "Ethernet1"))], devices)
    assert links == [{"a": "dc1-server:eth1", "b": "leaf2a:eth1"}]


def test_build_links_deterministic_sort() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"), ("leaf2", "leaf"))
    endpoints = [
        (("spine1", "Ethernet2"), ("leaf2", "Ethernet49")),
        (("spine1", "Ethernet1"), ("leaf1", "Ethernet49")),
    ]
    links = build_links(endpoints, devices)
    assert links == sorted(links, key=operator.itemgetter("a", "b"))


# --------------------------------------------------------------------------
# mgmt subnet
# --------------------------------------------------------------------------


def test_mgmt_subnet_derivation() -> None:
    devices = _devs(("leaf1", "leaf"))
    devices["leaf1"].mgmt = "10.255.0.18/24"
    assert mgmt_subnet(devices) == "10.255.0.0/24"


def test_mgmt_subnet_none_without_mask() -> None:
    assert mgmt_subnet(_devs(("leaf1", "leaf"))) is None


def test_mgmt_subnet_prefers_most_common() -> None:
    """A single stray device must not displace the real management range."""
    devices = _devs(("a", "leaf"), ("b", "leaf"), ("c", "leaf"), ("stray", "leaf"))
    for name in ("a", "b", "c"):
        devices[name].mgmt = f"10.0.6.{ord(name[0])}/24"
    devices["stray"].mgmt = "10.0.1.5/24"  # numerically lower, single occurrence
    assert mgmt_subnet(devices) == "10.0.6.0/24"


def test_mgmt_subnet_tie_broken_by_lowest_address() -> None:
    devices = _devs(("a", "leaf"), ("b", "leaf"))
    devices["a"].mgmt = "10.0.6.1/24"
    devices["b"].mgmt = "10.0.1.1/24"
    assert mgmt_subnet(devices) == "10.0.1.0/24"


def test_mgmt_subnet_is_order_independent() -> None:
    forward = _devs(("a", "leaf"), ("b", "leaf"))
    forward["a"].mgmt = "10.0.6.1/24"
    forward["b"].mgmt = "10.0.1.1/24"
    reverse = {k: forward[k] for k in reversed(list(forward))}
    assert mgmt_subnet(forward) == mgmt_subnet(reverse)


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def test_render_topology_valid_yaml_with_nodes_and_links() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"))
    devices["spine1"].mgmt = "10.0.0.1/24"
    devices["leaf1"].mgmt = "10.0.0.2/24"
    links = build_links([(("spine1", "Ethernet1"), ("leaf1", "Ethernet49"))], devices)
    doc = yaml.safe_load(render_topology("Fabric-X", devices, links))
    assert doc["name"] == "Fabric-X"
    assert doc["mgmt"]["ipv4-subnet"] == "10.0.0.0/24"
    assert set(doc["topology"]["nodes"]) == {"spine1", "leaf1"}
    assert doc["topology"]["nodes"]["spine1"]["mgmt-ipv4"] == "10.0.0.1"
    assert doc["topology"]["nodes"]["spine1"]["kind"] == CEOS_KIND
    assert doc["topology"]["kinds"][CEOS_KIND]["image"] == CEOS_IMAGE
    assert len(doc["topology"]["links"]) == 1


def test_render_topology_emits_binds_when_present() -> None:
    """Replaces the former assertion that binds were absent."""
    devices = _devs(("spine1", "spine"))
    devices["spine1"].binds = [f"configs/eos-intf-mapping/{SPINE_MAPPING}:/mnt/flash/EosIntfMapping.json:ro"]
    doc = yaml.safe_load(render_topology("Fabric-X", devices, []))
    assert doc["topology"]["nodes"]["spine1"]["binds"] == devices["spine1"].binds


def test_render_topology_omits_binds_key_when_empty() -> None:
    devices = _devs(("spine1", "spine"))
    doc = yaml.safe_load(render_topology("Fabric-X", devices, []))
    assert "binds" not in doc["topology"]["nodes"]["spine1"]


def test_render_topology_multiple_kinds_each_with_image() -> None:
    devices = _devs(("leaf1", "leaf"))
    devices["srv1"] = DeviceInfo("srv1", None, "linux", "lab-server", None)
    doc = yaml.safe_load(render_topology("Fabric-X", devices, []))
    kinds = doc["topology"]["kinds"]
    assert set(kinds) == {CEOS_KIND, "linux"}
    assert kinds[CEOS_KIND]["image"] == CEOS_IMAGE
    assert kinds["linux"]["image"] == "lab-server"


def test_render_topology_startup_config_only_for_network_kinds() -> None:
    """A Linux server must not be pointed at an EOS startup-config."""
    devices = _devs(("leaf1", "leaf"))
    devices["srv1"] = DeviceInfo("srv1", None, "linux", "lab-server", None)
    kinds = yaml.safe_load(render_topology("Fabric-X", devices, []))["topology"]["kinds"]
    assert kinds[CEOS_KIND]["startup-config"] == "configs/__clabNodeName__.cfg"
    assert "startup-config" not in kinds["linux"]


def test_render_topology_device_without_mgmt_ip_omits_field() -> None:
    devices = _devs(("leaf1", "leaf"))
    doc = yaml.safe_load(render_topology("Fabric-X", devices, []))
    assert "mgmt-ipv4" not in doc["topology"]["nodes"]["leaf1"]
    assert "mgmt" not in doc


def test_render_topology_empty_fabric_is_valid() -> None:
    doc = yaml.safe_load(render_topology("Empty", {}, []))
    assert doc["name"] == "Empty"
    assert doc["topology"]["nodes"] is None
    assert doc["topology"]["links"] is None


def test_render_topology_is_deterministic() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"))
    devices["spine1"].mgmt = "10.0.6.11/24"
    devices["leaf1"].mgmt = "10.0.6.13/24"
    links = build_links([(("spine1", "Ethernet1/1"), ("leaf1", "Ethernet49/1"))], devices)
    assert render_topology("F", devices, links) == render_topology("F", devices, links)


# --------------------------------------------------------------------------
# parity with lab/topology.clab.yml (contracts/parity-matrix.md)
# --------------------------------------------------------------------------


def _parity_fixture() -> ContainerLabTopologyQuery:
    """A two-domain fabric shaped like lab/topology.clab.yml."""
    devices: list[dict[str, Any]] = []
    servers: list[dict[str, Any]] = []
    for dc, base in (("dc1", 10), ("dc2", 20)):
        devices.extend(
            _device(
                f"spine-{dc}-{idx}",
                "spine",
                f"10.0.6.{base + idx}/24",
                [f"{dc}-sl-{idx}"],
                mapping=SPINE_MAPPING,
            )
            for idx in (1, 2)
        )
        for rack, role in ((1, "border_leaf"), (2, "leaf")):
            devices.extend(
                _device(
                    f"leaf-{dc}-{rack}-{idx}",
                    role,
                    f"10.0.6.{base + 2 + rack * 2 + idx}/24",
                    [f"{dc}-l-{rack}{idx}"],
                    mapping=LEAF_MAPPING,
                )
                for idx in (1, 2)
            )
        servers.append(_server(f"{dc}-server", "RACK-1", iface_link_ids=[f"{dc}-srv"]))
    return _query(devices, servers=servers)


def test_parity_node_and_kind_counts() -> None:
    query = _parity_fixture()
    nodes = collect_devices(query)
    nodes.update(collect_servers(query))
    kinds = {info.kind for info in nodes.values()}
    assert len(nodes) == 14, "12 switches + 2 servers per contracts/parity-matrix.md"
    assert sum(1 for i in nodes.values() if i.kind == CEOS_KIND) == 12
    assert sum(1 for i in nodes.values() if i.kind == "linux") == 2
    assert kinds == {CEOS_KIND, "linux"}


def test_parity_every_switch_has_a_mapping_bind() -> None:
    nodes = collect_devices(_parity_fixture())
    assert all(any("EosIntfMapping.json" in b for b in info.binds) for info in nodes.values()), (
        "each cEOS node needs its device-type mapping bind or breakout names will not resolve"
    )


def test_parity_mgmt_subnet() -> None:
    query = _parity_fixture()
    nodes = collect_devices(query)
    nodes.update(collect_servers(query))
    assert mgmt_subnet(nodes) == "10.0.6.0/24"


def test_parity_rendered_document_is_valid_and_closed() -> None:
    query = _parity_fixture()
    nodes = collect_devices(query)
    nodes.update(collect_servers(query))
    endpoints = [
        (("spine-dc1-1", "Ethernet1/1"), ("leaf-dc1-1-1", "Ethernet49/1")),
        (("leaf-dc1-1-1", "Ethernet5"), ("leaf-dc2-1-1", "Ethernet5")),
        (("dc1-server", "Ethernet1"), ("leaf-dc1-2-1", "Ethernet1")),
    ]
    links = build_links(endpoints, nodes)
    doc = yaml.safe_load(render_topology("Fabric-L3LS-Multi-Domain", nodes, links))
    rendered = set(doc["topology"]["nodes"])
    for link in doc["topology"]["links"]:
        for endpoint in link["endpoints"]:
            assert endpoint.split(":")[0] in rendered, "link references a node absent from nodes"
            assert "Ethernet" not in endpoint, "untranslated EOS interface name"


# --------------------------------------------------------------------------
# secondary link-endpoint fetch (async, fake client)
# --------------------------------------------------------------------------


class _FakeClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self.calls: list[list[str]] = []

    async def execute_graphql(
        self, query: str, variables: dict[str, Any], branch_name: str | None = None
    ) -> dict[str, Any]:
        self.calls.append(variables["ids"])
        return self._payload


async def test_fetch_link_endpoints_parses_pairs() -> None:
    def ep(dev: str, iface: str) -> dict[str, Any]:
        return {"node": {"name": {"value": iface}, "device": {"node": {"name": {"value": dev}}}}}

    payload = {
        "NetworkLink": {
            "edges": [
                {
                    "node": {
                        "id": "L1",
                        "connected_endpoints": {"edges": [ep("spine1", "Ethernet1"), ep("leaf1", "Ethernet49")]},
                    }
                },
                {
                    "node": {"id": "L2", "connected_endpoints": {"edges": [ep("spine1", "Ethernet2")]}}
                },  # 1 endpoint -> skipped
            ]
        }
    }
    client = _FakeClient(payload)
    pairs = await fetch_link_endpoints(client, ["L1", "L2"])
    assert pairs == [(("spine1", "Ethernet1"), ("leaf1", "Ethernet49"))]
    assert client.calls == [["L1", "L2"]]


async def test_fetch_link_endpoints_batches_above_fifty() -> None:
    client = _FakeClient({"NetworkLink": {"edges": []}})
    await fetch_link_endpoints(client, [f"L{i}" for i in range(120)])
    assert [len(c) for c in client.calls] == [50, 50, 20]


async def test_fetch_link_endpoints_resolves_server_endpoints() -> None:
    """A server endpoint must resolve, not be silently dropped.

    ``DcimInterface.device`` peers the ``DcimGenericDevice`` generic. Narrowing
    it to ``... on DcimDevice`` returns no name for a ComputePhysicalServer, so
    every server-facing link disappears.
    """

    def ep(dev: str, iface: str) -> dict[str, Any]:
        return {"node": {"name": {"value": iface}, "device": {"node": {"name": {"value": dev}}}}}

    payload = {
        "NetworkLink": {
            "edges": [
                {
                    "node": {
                        "id": "S1",
                        "connected_endpoints": {"edges": [ep("dc1-server", "Ethernet1"), ep("leaf2a", "Ethernet1")]},
                    }
                }
            ]
        }
    }
    pairs = await fetch_link_endpoints(_FakeClient(payload), ["S1"])
    assert pairs == [(("dc1-server", "Ethernet1"), ("leaf2a", "Ethernet1"))]


def test_link_endpoints_query_selects_name_on_the_generic() -> None:
    """Guard against reintroducing the DcimDevice-only endpoint fragment.

    The bug is invisible to the Python unit tests because it lives in the
    ``.gql`` selection, so assert on the query text itself.
    """
    query = link_endpoints_query()
    assert "$ids: [ID!]" in query
    device_selections = re.findall(r"device\s*\{\s*node\s*\{\s*([^}]*)", query)
    assert device_selections, "query must resolve each endpoint's owning device"
    for selection in device_selections:
        assert "on DcimDevice" not in selection, (
            "narrowing `device` to DcimDevice drops ComputePhysicalServer endpoints"
        )
        assert "name" in selection
