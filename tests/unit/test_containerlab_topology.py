"""Unit tests for the ContainerLab topology transform helpers."""

from __future__ import annotations

import operator
from typing import Any

import yaml

from transforms.containerlab_topology import (
    DeviceInfo,
    build_links,
    clab_interface_name,
    collect_devices,
    collect_link_ids,
    fetch_link_endpoints,
    mgmt_subnet,
    render_topology,
)
from transforms.containerlab_topology_query import ContainerLabTopologyQuery

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _device(
    name: str, role: str, mgmt: str | None, iface_link_ids: list[str], model: str | None = None
) -> dict[str, Any]:
    return {
        "__typename": "DcimDevice",
        "id": name,
        "name": {"value": name},
        "role": {"value": role},
        "device_type": {"node": {"name": {"value": model}}} if model else {"node": None},
        "mgmt_ip": {"node": {"address": {"value": mgmt}}} if mgmt else {"node": None},
        "interfaces": {
            "edges": [
                {"node": {"__typename": "DcimEndpoint", "connector": {"node": {"id": lid}}}} for lid in iface_link_ids
            ]
        },
    }


def _query(
    pod_devices: list[dict[str, Any]], rack_devices: list[dict[str, Any]] | None = None
) -> ContainerLabTopologyQuery:
    pod = {
        "__typename": "NetworkPod",
        "devices": {"edges": [{"node": d} for d in pod_devices]},
        "racks": {"edges": [{"node": {"devices": {"edges": [{"node": d} for d in (rack_devices or [])]}}}]},
    }
    return ContainerLabTopologyQuery(
        NetworkFabric={"edges": [{"node": {"name": {"value": "Fabric-X"}, "children": {"edges": [{"node": pod}]}}}]}
    )


# --------------------------------------------------------------------------
# interface name translation & slugs
# --------------------------------------------------------------------------


def test_clab_interface_name_simple() -> None:
    assert clab_interface_name("Ethernet27") == "eth27"


def test_clab_interface_name_breakout() -> None:
    assert clab_interface_name("Ethernet1/1") == "eth1_1"
    assert clab_interface_name("Ethernet1/1/3") == "eth1_1_3"


# --------------------------------------------------------------------------
# DeviceInfo
# --------------------------------------------------------------------------


def test_device_info_mgmt_ipv4_strips_mask() -> None:
    assert DeviceInfo("d", "leaf", None, "10.255.0.18/24").mgmt_ipv4 == "10.255.0.18"
    assert DeviceInfo("d", "leaf", None, None).mgmt_ipv4 is None


# --------------------------------------------------------------------------
# collection from a query response
# --------------------------------------------------------------------------


def test_collect_devices_dedupes_and_filters_roles() -> None:
    leaf = _device("leaf1", "leaf", "10.0.0.1/24", ["L1"])
    server = _device("srv1", "server", "10.0.0.9/24", ["L2"])  # non-network role -> excluded
    dupe = _device("leaf1", "leaf", "10.0.0.1/24", ["L1"])  # duplicate name -> collapsed
    devices = collect_devices(_query([leaf, dupe], rack_devices=[server]))
    assert set(devices) == {"leaf1"}
    assert devices["leaf1"].role == "leaf"


def test_collect_link_ids_unique_sorted() -> None:
    a = _device("leaf1", "leaf", None, ["L2", "L1"])
    b = _device("spine1", "spine", None, ["L1", "L3"])
    assert collect_link_ids(_query([a, b])) == ["L1", "L2", "L3"]


# --------------------------------------------------------------------------
# links
# --------------------------------------------------------------------------


def _devs(*specs: tuple[str, str]) -> dict[str, DeviceInfo]:
    return {name: DeviceInfo(name, role, None, None) for name, role in specs}


def test_build_links_translates_both_ends_and_orders() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"))
    links = build_links([(("spine1", "Ethernet1"), ("leaf1", "Ethernet49"))], devices)
    assert links == [{"a": "leaf1:eth49", "b": "spine1:eth1"}]


def test_build_links_skips_unknown_device_endpoints() -> None:
    devices = _devs(("leaf1", "leaf"))
    # peer 'srv1' is not a known network device -> link skipped (v1 network-only)
    assert build_links([(("leaf1", "Ethernet1"), ("srv1", "eth1"))], devices) == []


def test_build_links_deterministic_sort() -> None:
    devices = _devs(("spine1", "spine"), ("leaf1", "leaf"), ("leaf2", "leaf"))
    endpoints = [
        (("spine1", "Ethernet2"), ("leaf2", "Ethernet49")),
        (("spine1", "Ethernet1"), ("leaf1", "Ethernet49")),
    ]
    links = build_links(endpoints, devices)
    assert links == sorted(links, key=operator.itemgetter("a", "b"))


# --------------------------------------------------------------------------
# mgmt subnet & mappings
# --------------------------------------------------------------------------


def test_mgmt_subnet_derivation() -> None:
    devices = _devs(("leaf1", "leaf"))
    devices["leaf1"].mgmt = "10.255.0.18/24"
    assert mgmt_subnet(devices) == "10.255.0.0/24"


def test_mgmt_subnet_none_without_mask() -> None:
    assert mgmt_subnet(_devs(("leaf1", "leaf"))) is None


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
    assert doc["topology"]["nodes"]["spine1"]["kind"] == "arista_ceos"
    assert "binds" not in doc["topology"]["nodes"]["leaf1"]  # binds return with the device-type schema cycle
    assert len(doc["topology"]["links"]) == 1


def test_render_topology_device_without_mgmt_ip_omits_field() -> None:
    devices = _devs(("leaf1", "leaf"))  # no mgmt
    doc = yaml.safe_load(render_topology("Fabric-X", devices, []))
    assert "mgmt-ipv4" not in doc["topology"]["nodes"]["leaf1"]
    assert "mgmt" not in doc  # no mgmt block when no subnet derivable


def test_render_topology_empty_fabric_is_valid() -> None:
    doc = yaml.safe_load(render_topology("Empty", {}, []))
    assert doc["name"] == "Empty"
    assert doc["topology"]["nodes"] is None
    assert doc["topology"]["links"] is None


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
