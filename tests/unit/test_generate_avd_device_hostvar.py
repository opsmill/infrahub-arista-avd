"""Unit tests for the AVD hostvar generator's tenant/EVPN payload."""

import logging
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import yaml
from pyavd import validate_inputs

import generators.generate_avd_device_hostvar as hostvar_module
from generators.generate_avd_device_hostvar import (
    GenerateAVDDeviceHostvar,
    _add_switch_lag_adapter,  # noqa: PLC2701 - focused unit coverage for internal conflict validation
    allocate_dci_p2p_prefix_from_pool,
    apply_lag_adapter_config,
    build_dci_l3_edge_p2p_links,
)


def _attr(value: object) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _rel(peers: list[object]) -> SimpleNamespace:
    return SimpleNamespace(fetch=AsyncMock(), peers=[SimpleNamespace(peer=p) for p in peers])


def _custom(value: object) -> SimpleNamespace:
    return SimpleNamespace(avd_custom_hostvars=_attr(value))


def _make_generator() -> GenerateAVDDeviceHostvar:
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)
    gen.client = AsyncMock()
    return gen


def _named_peer(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=_attr(name))


# Sentinel so tests can pass `pool=None` to model a fabric with no DCI pool,
# distinct from "use the default pool".
_NO_POOL = object()


def _pool(pool_id: str = "pool-1") -> SimpleNamespace:
    return SimpleNamespace(id=pool_id, name=_attr("DCI-Pool"))


def _dci_endpoint(
    *,
    endpoint_id: str,
    device_id: str,
    device_name: str,
    interface_name: str,
    role: str = "border_leaf",
    interface_role: str = "peering",
    device_asn: int | None = 65101,
    pool: object = _NO_POOL,
    fabric_name: str = "fabric-l3ls-multipod-a",
    speed: str | None = "100g",
) -> dict:
    pool_node = _pool() if pool is _NO_POOL else pool
    fabric_node = {
        "__typename": "NetworkFabric",
        "name": {"value": fabric_name},
        "dci_pool": {"node": pool_node},
    }
    endpoint = {
        "__typename": "InterfacePhysical",
        "id": endpoint_id,
        "name": {"value": interface_name},
        "role": {"value": interface_role},
        "device": {
            "node": {
                "__typename": "DcimDevice",
                "id": device_id,
                "name": {"value": device_name},
                "role": {"value": role},
                "asn": {"node": {"asn": {"value": device_asn}} if device_asn is not None else None},
                "pod": {"node": {"parent": {"node": fabric_node}}},
            }
        },
    }
    if speed is not None:
        endpoint["speed"] = {"value": speed}
    return endpoint


def _dci_link(
    link_id: str = "dci-1",
    *,
    name: str = "DCI-1",
    endpoint_1: dict | None = None,
    endpoint_2: dict | None = None,
    include_in_underlay_protocol: bool | None = True,
) -> dict:
    link = {
        "__typename": "NetworkLink",
        "id": link_id,
        "display_label": name,
        "name": {"value": name},
        "role": {"value": "dci"},
        "connected_endpoints": {
            "edges": [
                {
                    "node": endpoint_1
                    or _dci_endpoint(
                        endpoint_id="dc1-eth5",
                        device_id="dc1-leaf1",
                        device_name="ih-dc1-leaf1a",
                        interface_name="Ethernet5",
                        device_asn=65101,
                    )
                },
                {
                    "node": endpoint_2
                    or _dci_endpoint(
                        endpoint_id="dc2-eth5",
                        device_id="dc2-leaf1",
                        device_name="ih-dc2-leaf1a",
                        interface_name="Ethernet5",
                        device_asn=65201,
                    )
                },
            ]
        },
    }
    if include_in_underlay_protocol is not None:
        link["include_in_underlay_protocol"] = {"value": include_in_underlay_protocol}
    return link


def _mock_prefix(prefix: str) -> SimpleNamespace:
    return SimpleNamespace(prefix=_attr(prefix))


def _base_hostvars(
    tenants_data: list[dict],
    *,
    rack_info: dict | None = None,
    mlag_info: dict | None = None,
    connected_endpoints: list[dict] | None = None,
    custom_hostvars: dict | None = None,
    role: str = "leaf",
    dci_l3_edge_p2p_links: list[dict] | None = None,
    evpn_gateway: dict | None = None,
    evpn_vlan_aware_bundles: bool | None = None,
    underlay_routing_protocol: str = "ebgp",
    mlag_capable: bool = False,
    pools: dict | None = None,
    uplinks: dict | None = None,
    uplink_pool_reservation: dict | None = None,
    loopback_ipv4_pool: str | None = "10.0.0.0/24",
    vtep_loopback_ipv4_pool: str | None = "10.2.0.0/24",
) -> dict:
    """Minimal leaf hostvars wrapping the tenant payload, mirroring generate()."""
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname="leaf1",
        role=role,
        bgp_asn=65001,
        node_id=3,
        loopback_ip="10.0.0.3",
        loopback_ipv4_pool=loopback_ipv4_pool,
        vtep_loopback_ip="10.2.0.3",
        vtep_loopback_ipv4_pool=vtep_loopback_ipv4_pool,
        mgmt_ip="192.168.0.3",
        fabric_name="Fabric-L3LS-MultiPod-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol=underlay_routing_protocol,
        overlay_routing_protocol="ebgp",
        evpn_vlan_aware_bundles=evpn_vlan_aware_bundles,
        mlag_capable=mlag_capable,
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={"leaf": 8192},
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools=pools
        or {
            "uplink_ipv4_pool": "10.1.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks=uplinks or {"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info=rack_info or {"name": "DC1_BORDER", "mlag": False, "leaf_names": ["leaf1"]},
        mlag_info=mlag_info or {"domain_id": None, "bgp_asn": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=tenants_data,
        connected_endpoints=connected_endpoints or [],
        dci_l3_edge_p2p_links=dci_l3_edge_p2p_links,
        evpn_gateway=evpn_gateway,
        custom_hostvars=custom_hostvars or {},
        uplink_pool_reservation=uplink_pool_reservation,
    )


def _underlay_hostvars(
    *,
    hostname: str,
    role: str,
    node_id: int,
    uplinks: dict | None = None,
    uplink_pool_reservation: dict | None = None,
) -> dict:
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname=hostname,
        role=role,
        bgp_asn=65000 + node_id,
        node_id=node_id,
        loopback_ip=f"10.0.0.{node_id}",
        loopback_ipv4_pool="10.0.0.0/24",
        vtep_loopback_ip="10.2.0.3",
        vtep_loopback_ipv4_pool="10.2.0.0/24",
        mgmt_ip=f"192.168.0.{node_id}",
        fabric_name="Fabric-L3LS-MultiPod-A",
        mgmt_gateway=None,
        virtual_router_mac=None,
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={},
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks=uplinks or {"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info={"name": f"{hostname}-rack", "mlag": False, "leaf_names": [hostname], "avd_tags": []},
        mlag_info={"domain_id": None, "bgp_asn": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=[],
        connected_endpoints=[],
        custom_hostvars={},
        uplink_pool_reservation=uplink_pool_reservation,
    )


def test_extract_mlag_info_reads_bgp_asn_from_routing_asn_relationship() -> None:
    """The MLAG ASN is now sourced from the shared Routing.Asn node via the ``asn`` relationship."""
    mlag_domain = SimpleNamespace(
        domain_id=_attr("DC1_BORDER"),
        asn=SimpleNamespace(node=SimpleNamespace(asn=_attr(65100))),
        virtual_router_mac=_attr(None),
        peers=SimpleNamespace(
            edges=[
                SimpleNamespace(node=SimpleNamespace(name=_attr("leaf1"))),
                SimpleNamespace(node=SimpleNamespace(name=_attr("leaf2"))),
            ]
        ),
    )
    device = SimpleNamespace(mlag_domain=SimpleNamespace(node=mlag_domain))

    info = GenerateAVDDeviceHostvar._extract_mlag_info(device)

    assert info["bgp_asn"] == 65100
    assert info["domain_id"] == "DC1_BORDER"
    assert info["peer_names"] == ["leaf1", "leaf2"]


def test_extract_mlag_info_handles_unlinked_asn() -> None:
    """A domain with no ASN node linked yet resolves bgp_asn to None (no crash)."""
    mlag_domain = SimpleNamespace(
        domain_id=_attr("DC1_BORDER"),
        asn=SimpleNamespace(node=None),
        virtual_router_mac=_attr(None),
        peers=SimpleNamespace(edges=[]),
    )
    device = SimpleNamespace(mlag_domain=SimpleNamespace(node=mlag_domain))

    info = GenerateAVDDeviceHostvar._extract_mlag_info(device)

    assert info["bgp_asn"] is None


def test_non_mlag_leaf_sets_avd_mlag_false_on_rack_node_group() -> None:
    """Leaf hostvars without an MLAG domain must explicitly disable MLAG on the rack node group."""
    hostvars = _base_hostvars([])

    node_group = hostvars["l3leaf"]["node_groups"][0]
    assert node_group["group"] == "DC1_BORDER"
    assert node_group["nodes"] == [{"name": "leaf1"}]
    assert node_group["mlag"] is False
    assert hostvars["l3leaf"]["nodes"][0]["bgp_as"] == "65001"
    assert "mlag" not in hostvars["l3leaf"].get("defaults", {})
    assert not validate_inputs(hostvars).validation_result.violations


def test_uplink_pool_and_reservation_emit_only_with_routed_uplinks() -> None:
    no_uplink_hostvars = _base_hostvars([])
    assert "uplink_ipv4_pool" not in no_uplink_hostvars["l3leaf"]["nodes"][0]
    assert "max_uplink_switches" not in no_uplink_hostvars["l3leaf"]["nodes"][0]

    routed_hostvars = _base_hostvars(
        [],
        uplinks={
            "uplink_interfaces": ["Ethernet1", "Ethernet2", "Ethernet3", "Ethernet4"],
            "uplink_switches": ["spine1", "spine1", "spine2", "spine2"],
            "uplink_switch_interfaces": ["Ethernet1", "Ethernet2", "Ethernet1", "Ethernet2"],
        },
        uplink_pool_reservation={"max_uplink_switches": 2, "max_parallel_uplinks": 2},
    )

    node = routed_hostvars["l3leaf"]["nodes"][0]
    assert node["uplink_ipv4_pool"] == "10.1.0.0/24"
    assert node["max_uplink_switches"] == 2
    assert node["max_parallel_uplinks"] == 2
    assert not validate_inputs(routed_hostvars).validation_result.violations


def test_five_stage_shared_uplink_pool_has_unique_structured_config_interface_ips() -> None:
    reservation = {"max_uplink_switches": 4, "max_parallel_uplinks": None}
    hostvars = {
        "super-spine1": _underlay_hostvars(hostname="super-spine1", role="super_spine", node_id=1),
        "super-spine2": _underlay_hostvars(hostname="super-spine2", role="super_spine", node_id=2),
        "spine1": _underlay_hostvars(
            hostname="spine1",
            role="spine",
            node_id=1,
            uplinks={
                "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                "uplink_switches": ["super-spine1", "super-spine2"],
                "uplink_switch_interfaces": ["Ethernet1", "Ethernet1"],
            },
            uplink_pool_reservation=reservation,
        ),
        "spine2": _underlay_hostvars(
            hostname="spine2",
            role="spine",
            node_id=2,
            uplinks={
                "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                "uplink_switches": ["super-spine1", "super-spine2"],
                "uplink_switch_interfaces": ["Ethernet2", "Ethernet2"],
            },
            uplink_pool_reservation=reservation,
        ),
        "leaf1": _underlay_hostvars(
            hostname="leaf1",
            role="leaf",
            node_id=3,
            uplinks={
                "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                "uplink_switches": ["spine1", "spine2"],
                "uplink_switch_interfaces": ["Ethernet3", "Ethernet3"],
            },
            uplink_pool_reservation=reservation,
        ),
        "leaf2": _underlay_hostvars(
            hostname="leaf2",
            role="leaf",
            node_id=4,
            uplinks={
                "uplink_interfaces": ["Ethernet1", "Ethernet2"],
                "uplink_switches": ["spine1", "spine2"],
                "uplink_switch_interfaces": ["Ethernet4", "Ethernet4"],
            },
            uplink_pool_reservation=reservation,
        ),
    }
    for inputs in hostvars.values():
        assert not validate_inputs(inputs).validation_result.violations
        node_type = "super_spine" if inputs["type"] == "super-spine" else inputs["type"]
        node = inputs[node_type]["nodes"][0]
        assert "loopback_ipv4_address" in node
        assert node["loopback_ipv4_pool"] == "10.0.0.0/24"
        if inputs["type"] == "l3leaf":
            assert node["vtep_loopback_ipv4_pool"] == "10.2.0.0/24"
        else:
            assert "vtep_loopback_ipv4_pool" not in node


def test_l2leaf_main_tier_renders_mlag_node_group() -> None:
    """A standalone L2LS/campus l2leaf pair is the main tier and must render its
    MLAG domain (node-group + mlag_domain_id + peer-link), with no bgp_as since a
    pure-L2 MLAG tier runs no BGP. Regression for the MLAG-rendering gap."""
    mlag_info = {
        "domain_id": "L2LS_RACK1",
        "bgp_asn": None,
        "virtual_router_mac": None,
        "peer_names": ["leaf1", "leaf2"],
        "mlag_peer_interfaces": ["Ethernet47", "Ethernet48"],
    }
    hostvars = _base_hostvars(
        [],
        role="l2leaf",
        underlay_routing_protocol="none",
        mlag_capable=True,
        mlag_info=mlag_info,
        rack_info={"name": "L2LS_RACK1", "mlag": True, "leaf_names": [], "avd_tags": []},
    )

    node_group = hostvars["l2leaf"]["node_groups"][0]
    assert node_group["group"] == "L2LS_RACK1"
    assert node_group["mlag_domain_id"] == "L2LS_RACK1"
    assert node_group["nodes"] == [{"name": "leaf1"}, {"name": "leaf2"}]
    assert "bgp_as" not in node_group
    assert hostvars["l2leaf"]["nodes"][0]["mlag_interfaces"] == ["Ethernet47", "Ethernet48"]
    assert not validate_inputs(hostvars).validation_result.violations


def test_l2spine_main_tier_renders_mlag_node_group() -> None:
    """The L2LS spine tier (l2spine) also forms an MLAG pair and must render it."""
    mlag_info = {
        "domain_id": "L2LS_SPINE",
        "bgp_asn": None,
        "virtual_router_mac": None,
        "peer_names": ["leaf1", "leaf2"],
        "mlag_peer_interfaces": ["Ethernet1", "Ethernet2"],
    }
    hostvars = _base_hostvars(
        [],
        role="l2spine",
        underlay_routing_protocol="none",
        mlag_capable=True,
        mlag_info=mlag_info,
        rack_info={"name": "L2LS_SPINE", "mlag": True, "leaf_names": [], "avd_tags": []},
    )

    node_group = hostvars["l2spine"]["node_groups"][0]
    assert node_group["mlag_domain_id"] == "L2LS_SPINE"
    assert node_group["nodes"] == [{"name": "leaf1"}, {"name": "leaf2"}]
    assert not validate_inputs(hostvars).validation_result.violations


def test_l2leaf_access_tier_under_l3ls_renders_no_mlag() -> None:
    """Regression guard: the L3LS access-tier l2leaf (not mlag_capable) must keep
    its pure-access behavior and render no MLAG node group."""
    mlag_info = {
        "domain_id": "ACCESS_RACK",
        "bgp_asn": None,
        "virtual_router_mac": None,
        "peer_names": ["l2leaf1", "l2leaf2"],
    }
    hostvars = _base_hostvars(
        [],
        role="l2leaf",
        underlay_routing_protocol="ebgp",
        mlag_capable=False,
        mlag_info=mlag_info,
    )
    assert "node_groups" not in hostvars.get("l2leaf", {})
    assert "mlag_interfaces" not in hostvars["l2leaf"]["nodes"][0]


def test_l2leaf_main_tier_emits_mlag_peer_pool_only() -> None:
    """A main-tier l2leaf MLAG pair needs the pod's MLAG peer-link pool at node
    level, but must not emit the L3 uplink/vtep/loopback/mlag-L3 pools (it runs no
    L3 underlay). Regression for the 'mlag_interfaces not set' crash, whose root
    cause included the peer pool being nulled for every l2leaf."""
    mlag_info = {
        "domain_id": "L2LS_RACK1",
        "bgp_asn": None,
        "virtual_router_mac": None,
        "peer_names": ["leaf1", "leaf2"],
        "mlag_peer_interfaces": ["Ethernet47", "Ethernet48"],
    }
    hostvars = _base_hostvars(
        [],
        role="l2leaf",
        underlay_routing_protocol="none",
        mlag_capable=True,
        mlag_info=mlag_info,
        rack_info={"name": "L2LS_RACK1", "mlag": True, "leaf_names": [], "avd_tags": []},
        loopback_ipv4_pool=None,
        vtep_loopback_ipv4_pool=None,
        pools={
            "uplink_ipv4_pool": None,
            "vtep_loopback_ipv4_pool": None,
            "loopback_ipv4_pool": None,
            "mlag_peer_ipv4_pool": "10.60.4.0/24",
            "mlag_peer_l3_ipv4_pool": None,
        },
    )

    node = hostvars["l2leaf"]["nodes"][0]
    assert node["mlag_peer_ipv4_pool"] == "10.60.4.0/24"
    assert node["mlag_interfaces"] == ["Ethernet47", "Ethernet48"]
    assert "uplink_ipv4_pool" not in node
    assert "vtep_loopback_ipv4_pool" not in node
    assert "loopback_ipv4_pool" not in node
    assert "mlag_peer_l3_ipv4_pool" not in node
    assert not validate_inputs(hostvars).validation_result.violations


def test_switch_lag_member_links_retains_l2leaf_switch_endpoints() -> None:
    """When the current device is itself a main-tier l2leaf, a dual-homed server's
    port-channel legs land on sibling l2leaf switches and must be retained. The
    default (L3-leaf) behaviour still drops l2leaf downlink endpoints.

    Regression for the empty-adapter bug where a dual-homed L2LS/campus server
    rendered a port_channel with no switches/switch_ports/endpoint_ports.
    """
    switch_lag = _lag(name="Port-Channel1", channel_id=1)

    def _server_lag_member(member_name: str, switch_name: str, switch_port: str) -> SimpleNamespace:
        switch_endpoint = SimpleNamespace(
            id=f"{switch_name}:{switch_port}",
            typename__="InterfacePhysical",
            name=_attr(switch_port),
            device=SimpleNamespace(node=SimpleNamespace(name=_attr(switch_name), role=_attr("l2leaf"))),
            lag=SimpleNamespace(node=switch_lag),
            tagged_vlan=SimpleNamespace(edges=[]),
            untagged_vlan=SimpleNamespace(node=None),
        )
        connector = SimpleNamespace(
            node=SimpleNamespace(connected_endpoints=SimpleNamespace(edges=[SimpleNamespace(node=switch_endpoint)]))
        )
        return SimpleNamespace(id=f"srv:{member_name}", name=_attr(member_name), connector=connector)

    server_lag = SimpleNamespace(
        lag_members=SimpleNamespace(
            edges=[
                SimpleNamespace(node=_server_lag_member("Ethernet1", "leaf-l2ls-pod1-1-1", "Ethernet1")),
                SimpleNamespace(node=_server_lag_member("Ethernet2", "leaf-l2ls-pod1-1-2", "Ethernet1")),
            ]
        )
    )
    fallback_local = SimpleNamespace(
        name=_attr("Ethernet1"), tagged_vlan=SimpleNamespace(edges=[]), untagged_vlan=SimpleNamespace(node=None)
    )
    fallback_endpoint = SimpleNamespace(name=_attr("Ethernet1"))

    kept = hostvar_module._switch_lag_member_links(
        server_lag_node=server_lag,
        fallback_switch_lag_node=switch_lag,
        fallback_local_interface=fallback_local,
        fallback_endpoint=fallback_endpoint,
        hostname="leaf-l2ls-pod1-1-1",
        skip_l2leaf_endpoints=False,
    )
    assert sorted((link["switch"], link["switch_port"]) for link in kept) == [
        ("leaf-l2ls-pod1-1-1", "Ethernet1"),
        ("leaf-l2ls-pod1-1-2", "Ethernet1"),
    ]

    dropped = hostvar_module._switch_lag_member_links(
        server_lag_node=server_lag,
        fallback_switch_lag_node=switch_lag,
        fallback_local_interface=fallback_local,
        fallback_endpoint=fallback_endpoint,
        hostname="leaf-l2ls-pod1-1-1",
        skip_l2leaf_endpoints=True,
    )
    assert dropped == []


def test_border_leaf_builds_l3leaf_hostvars() -> None:
    hostvars = _base_hostvars([], role="border_leaf")

    assert hostvars["type"] == "l3leaf"
    assert hostvars["l3leaf"]["nodes"][0]["name"] == "leaf1"
    assert hostvars["l3leaf"]["node_groups"][0]["nodes"] == [{"name": "leaf1"}]
    assert not validate_inputs(hostvars).validation_result.violations


def test_super_spine_renders_evpn_route_server() -> None:
    """Super-spines act as EVPN route servers in the 5-stage Clos design."""
    hostvars = _base_hostvars([], role="super_spine")

    assert hostvars["type"] == "super-spine"
    assert hostvars["super_spine"]["nodes"][0]["evpn_role"] == "server"


def test_non_super_spine_has_no_evpn_route_server_role() -> None:
    """Only super-spines derive evpn_role: server; leaves must not."""
    hostvars = _base_hostvars([], role="leaf")

    assert hostvars["l3leaf"]["nodes"][0].get("evpn_role") != "server"


def test_hostvars_never_emit_design_type() -> None:
    """pyAVD 6.3 has no design.type; the generator must never emit it (research R1)."""
    for role in ("leaf", "border_leaf", "spine", "super_spine"):
        hostvars = _base_hostvars([], role=role)
        assert "design" not in hostvars


def test_underlay_none_omits_underlay_routing_protocol() -> None:
    """Standalone L2LS (underlay 'none') must not emit an underlay_routing_protocol."""
    hostvars = _base_hostvars([], underlay_routing_protocol="none")
    assert "underlay_routing_protocol" not in hostvars

    ebgp = _base_hostvars([], underlay_routing_protocol="ebgp")
    assert ebgp["underlay_routing_protocol"] == "ebgp"


def test_evpn_vlan_aware_bundles_rendered_when_enabled() -> None:
    """The 5-stage Clos design renders tenants as vlan-aware bundles when enabled."""
    enabled = _base_hostvars([], evpn_vlan_aware_bundles=True)
    assert enabled["evpn_vlan_aware_bundles"] is True

    default = _base_hostvars([])
    assert "evpn_vlan_aware_bundles" not in default


@pytest.mark.parametrize(("role", "node_type_key"), [("spine", "spine"), ("super_spine", "super_spine")])
def test_l3ls_transit_roles_omit_node_virtual_router_mac_address(role: str, node_type_key: str) -> None:
    """Routed L3LS spines/super-spines carry a fabric virtual_router_mac but render no
    anycast SVIs, so they must NOT get a node-level virtual_router_mac_address — even
    with tenant data present. Regression guard for the SVI-role gating (issue: the
    node-level mac guard must stay off the pure-L3 transit tier)."""
    hostvars = _base_hostvars([{"name": "TENANT_A"}], role=role)

    node = hostvars[node_type_key]["nodes"][0]
    assert "virtual_router_mac_address" not in node


@pytest.mark.parametrize(("role", "node_type_key"), [("leaf", "l3leaf"), ("l3spine", "l3spine"), ("pe", "pe")])
def test_svi_rendering_roles_keep_node_virtual_router_mac_address(role: str, node_type_key: str) -> None:
    """Devices that render anycast SVIs (L3 leaf, campus l3spine core, MPLS PE) keep the
    node-level virtual_router_mac_address when tenant SVIs are present."""
    hostvars = _base_hostvars([{"name": "TENANT_A"}], role=role)

    node = hostvars[node_type_key]["nodes"][0]
    assert node["virtual_router_mac_address"] == "00:1c:73:00:00:99"


def test_border_leaf_mapping_is_available_to_repository_loaded_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repository-loaded generators may run beside an older installed package."""

    def reject_border_leaf(role: str) -> str:
        if role == "border_leaf":
            msg = f"Unknown device role: {role}"
            raise ValueError(msg)
        return role

    monkeypatch.setattr(hostvar_module, "_get_package_avd_type", reject_border_leaf)

    hostvars = _base_hostvars([], role="border_leaf")

    assert hostvars["type"] == "l3leaf"
    assert hostvars["l3leaf"]["nodes"][0]["name"] == "leaf1"
    assert not validate_inputs(hostvars).validation_result.violations


def _rel_node(node: object | None) -> SimpleNamespace:
    return SimpleNamespace(node=node)


def _rel_edges(nodes: list[object]) -> SimpleNamespace:
    return SimpleNamespace(edges=[SimpleNamespace(node=node) for node in nodes])


def _gateway_device(device_id: str, name: str, role: str, pod: object) -> SimpleNamespace:
    return SimpleNamespace(
        id=device_id,
        name=_attr(name),
        role=_attr(role),
        pod=_rel_node(pod),
    )


def _fabric(fabric_id: str = "fabric-l3ls-multipod-a") -> SimpleNamespace:
    return SimpleNamespace(id=fabric_id, name=_attr(fabric_id))


def _domain(domain_id: str, fabric: object, *, obj_id: str = "domain") -> SimpleNamespace:
    return SimpleNamespace(
        id=obj_id,
        display_label=f"{fabric.name.value} / {domain_id}",
        domain_id=_attr(domain_id),
        fabric=_rel_node(fabric),
        remote_gateway_groups=_rel_edges([]),
    )


def _pod(pod_id: str, name: str, evpn_domain: object | None) -> SimpleNamespace:
    return SimpleNamespace(id=pod_id, name=_attr(name), evpn_domain=_rel_node(evpn_domain))


def _gateway_group(
    group_id: str,
    name: str,
    local_domain: object | None,
    pod: object | None,
    remote_domain: object | None,
    members: list[object],
) -> SimpleNamespace:
    return SimpleNamespace(
        id=group_id,
        display_label=name,
        name=_attr(name),
        resiliency_model=_attr("all_active_multihoming"),
        evpn_l2_enabled=_attr(True),
        evpn_l3_enabled=_attr(True),
        evpn_l3_inter_domain=_attr(True),
        d_path_enabled=_attr(True),
        all_active_multihoming_enabled=_attr(True),
        ethernet_segment_identifier=_attr("0000:0000:0000:0001:0001"),
        ethernet_segment_rt_import=_attr("00:00:00:00:00:01"),
        local_domain=_rel_node(local_domain),
        pod=_rel_node(pod),
        remote_domain=_rel_node(remote_domain),
        members=_rel_edges(members),
    )


def _gateway_group_topology(
    *, target_role: str = "border_leaf", peer_names: tuple[str, ...] = ("leaf3", "leaf2")
) -> tuple[SimpleNamespace, SimpleNamespace]:
    fabric = _fabric()
    local_domain = _domain("65100:1", fabric, obj_id="domain-a")
    peer_domain = _domain("65200:1", fabric, obj_id="domain-b")
    core_domain = _domain("65300:1", fabric, obj_id="domain-core")
    local_pod = _pod("pod-a", "pod-a", local_domain)
    peer_pod = _pod("pod-b", "pod-b", peer_domain)
    target = _gateway_device("device-a", "leaf1", target_role, local_pod)
    peer_members = [
        _gateway_device(f"device-peer-{index}", peer_name, "border_leaf", peer_pod)
        for index, peer_name in enumerate(peer_names)
    ]
    local_group = _gateway_group("gateway-group-a", "gateway-group-a", local_domain, local_pod, core_domain, [target])
    peer_group = _gateway_group("gateway-group-b", "gateway-group-b", peer_domain, peer_pod, core_domain, peer_members)
    core_domain.remote_gateway_groups = _rel_edges([local_group, peer_group])
    target.evpn_gateway_group = _rel_node(local_group)
    return target, local_group


def test_gateway_group_border_leaf_emits_evpn_gateway_payload() -> None:
    target, _gateway_node = _gateway_group_topology()

    payload = GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf")
    hostvars = _base_hostvars([], role="border_leaf", evpn_gateway=payload)

    gateway = hostvars["l3leaf"]["nodes"][0]["evpn_gateway"]
    assert gateway == {
        "remote_peers": [{"hostname": "leaf2"}, {"hostname": "leaf3"}],
        "evpn_l2": {"enabled": True},
        "evpn_l3": {"enabled": True, "inter_domain": True},
        "d_path": {"enabled": True, "local_domain_id": "65100:1", "remote_domain_id": "65300:1"},
        "all_active_multihoming": {
            "enabled": True,
            "evpn_ethernet_segment": {
                "identifier": "0000:0000:0000:0001:0001",
                "rt_import": "00:00:00:00:00:01",
            },
        },
    }
    assert "enable_d_path" not in gateway["all_active_multihoming"]
    assert "evpn_domain_id_local" not in gateway["all_active_multihoming"]
    assert "evpn_domain_id_remote" not in gateway["all_active_multihoming"]
    assert not validate_inputs(hostvars).validation_result.violations


def test_gateway_group_generated_query_alias_booleans_are_preserved() -> None:
    target, gateway_node = _gateway_group_topology()
    for graphql_name, generated_name in (
        ("evpn_l2_enabled", "evpn_l_2_enabled"),
        ("evpn_l3_enabled", "evpn_l_3_enabled"),
        ("evpn_l3_inter_domain", "evpn_l_3_inter_domain"),
    ):
        setattr(gateway_node, generated_name, getattr(gateway_node, graphql_name))
        delattr(gateway_node, graphql_name)

    payload = GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf")

    assert payload is not None
    assert payload["evpn_l2"]["enabled"] is True
    assert payload["evpn_l3"]["enabled"] is True
    assert payload["evpn_l3"]["inter_domain"] is True


def test_gateway_query_model_exposes_domain_owned_relationships() -> None:
    query_text = Path("generators/avd_device_hostvar.gql").read_text(encoding="utf-8")
    model_text = Path("generators/generate_avd_device_inputs_query.py").read_text(encoding="utf-8")

    assert "local_domain" in query_text
    assert "remote_gateway_groups" in query_text
    assert "NodeLocalDomain" in model_text
    assert "RemoteGatewayGroupsEdgesNodeLocalDomain" in model_text


@pytest.mark.parametrize("role", ["leaf", "l2leaf", "spine", "super_spine"])
def test_ungrouped_non_gateway_roles_omit_evpn_gateway_payload(role: str) -> None:
    target, _gateway_node = _gateway_group_topology(target_role=role)
    target.evpn_gateway_group = _rel_node(None)

    assert GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role=role) is None


@pytest.mark.parametrize("role", ["leaf", "l2leaf", "spine", "super_spine"])
def test_grouped_non_gateway_roles_raise_actionable_error(role: str) -> None:
    target, _gateway_node = _gateway_group_topology(target_role=role)

    with pytest.raises(ValueError, match="target device role"):
        GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role=role)


def test_unlinked_border_leaf_omits_evpn_gateway_payload() -> None:
    target, _gateway_node = _gateway_group_topology()
    target.evpn_gateway_group = _rel_node(None)

    assert GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf") is None


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("resiliency_model", _attr("mlag"), "resiliency_model"),
        ("ethernet_segment_identifier", _attr(""), "ethernet_segment_identifier"),
        ("ethernet_segment_rt_import", _attr(""), "ethernet_segment_rt_import"),
    ],
)
def test_gateway_group_field_validation_errors_are_actionable(field: str, value: object, match: str) -> None:
    target, gateway = _gateway_group_topology()
    setattr(gateway, field, value)

    with pytest.raises(ValueError, match=match):
        GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf")


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda _target, gateway: setattr(gateway, "local_domain", _rel_node(None)), "local_domain"),
        (
            lambda _target, gateway: setattr(
                gateway,
                "local_domain",
                _rel_node(_domain("65100:99", _fabric(), obj_id="domain-unmatched")),
            ),
            "must match gateway group local_domain",
        ),
        (lambda _target, gateway: setattr(gateway.pod.node, "evpn_domain", _rel_node(None)), "evpn_domain"),
        (lambda _target, gateway: setattr(gateway, "pod", _rel_node(None)), "relationship 'pod'"),
        (lambda _target, gateway: setattr(gateway, "remote_domain", _rel_node(None)), "remote_domain"),
        (
            lambda _target, gateway: setattr(gateway, "remote_domain", _rel_node(gateway.local_domain.node)),
            "must differ",
        ),
        (lambda _target, gateway: setattr(gateway, "members", _rel_edges([])), "at least one"),
        (lambda _target, gateway: setattr(gateway.members.edges[0].node, "role", _attr("leaf")), "border_leaf"),
        (
            lambda _target, gateway: setattr(
                gateway.members.edges[0].node, "pod", _rel_node(_pod("pod-x", "pod-x", None))
            ),
            "gateway group's pod",
        ),
    ],
)
def test_gateway_group_relationship_validation_errors_are_actionable(
    mutator: Callable[[SimpleNamespace, SimpleNamespace], None], match: str
) -> None:
    target, gateway = _gateway_group_topology()
    mutator(target, gateway)

    with pytest.raises(ValueError, match=match):
        GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf")


def test_gateway_group_without_remote_peers_emits_empty_peer_list() -> None:
    target, gateway = _gateway_group_topology(peer_names=())
    gateway.remote_domain.node.remote_gateway_groups = _rel_edges([gateway])

    payload = GenerateAVDDeviceHostvar._extract_evpn_gateway_payload(target, hostname="leaf1", role="border_leaf")

    assert payload is not None
    assert payload["remote_peers"] == []


@pytest.mark.anyio
async def test_dci_l3_edge_p2p_link_output_with_resolved_speed() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[_dci_link()],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == [
        {
            "nodes": ["ih-dc1-leaf1a", "ih-dc2-leaf1a"],
            "interfaces": ["Ethernet5", "Ethernet5"],
            "as": [65101, 65201],
            "ip": ["172.16.0.0/31", "172.16.0.1/31"],
            "include_in_underlay_protocol": True,
            "speed": "100g",
        }
    ]
    gen.client.allocate_next_ip_prefix.assert_awaited_once()

    hostvars = _base_hostvars([], dci_l3_edge_p2p_links=p2p_links)
    assert "p2p_links_profiles" not in hostvars["l3_edge"]
    assert "profile" not in hostvars["l3_edge"]["p2p_links"][0]
    assert not validate_inputs(hostvars).validation_result.violations


@pytest.mark.anyio
async def test_dci_l3_edge_omits_speed_when_unresolved() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    speed=None,
                ),
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    speed=None,
                ),
            )
        ],
        hostname="ih-dc1-leaf1a",
    )

    assert "speed" not in p2p_links[0]
    assert not validate_inputs(_base_hostvars([], dci_l3_edge_p2p_links=p2p_links)).validation_result.violations


@pytest.mark.anyio
async def test_dci_l3_edge_hydrates_graphql_pool_before_allocation() -> None:
    gen = _make_generator()
    hydrated_pool = SimpleNamespace(id="pool-1", get_kind=lambda: "CoreIPPrefixPool")
    gen.client.get = AsyncMock(return_value=hydrated_pool)
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    graphql_pool = {"id": "pool-1", "name": {"value": "DCI-Pool"}}
    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=65101,
                    pool=graphql_pool,
                ),
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=65201,
                    pool=graphql_pool,
                ),
            )
        ],
        hostname="ih-dc1-leaf1a",
    )

    gen.client.get.assert_awaited_once_with(kind="CoreIPPrefixPool", id="pool-1")
    allocation_kwargs = gen.client.allocate_next_ip_prefix.await_args.kwargs
    assert allocation_kwargs["resource_pool"] is hydrated_pool
    assert allocation_kwargs["member_type"] == "prefix"
    assert allocation_kwargs["data"] == {"role": "technical"}
    assert p2p_links[0]["ip"] == ["172.16.0.0/31", "172.16.0.1/31"]


@pytest.mark.anyio
@pytest.mark.parametrize("hostname", ["ih-dc1-leaf1a", "ih-dc2-leaf1a"])
async def test_dci_cross_fabric_uses_single_deterministic_pool(hostname: str) -> None:
    """Both border leafs must allocate the DCI /31 from the same pool.

    The two endpoints can live in different fabrics with different DCI pools, yet
    each device generates its hostvars independently. The pool is chosen from the
    sorted-first endpoint's fabric, so both sides allocate the same prefix under
    the shared link identifier — otherwise the two ends would get mismatched IPs.
    """
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))
    pool_dc1 = _pool("pool-dc1")
    pool_dc2 = _pool("pool-dc2")
    link = _dci_link(
        endpoint_1=_dci_endpoint(
            endpoint_id="dc1-eth5",
            device_id="dc1-leaf1",
            device_name="ih-dc1-leaf1a",
            interface_name="Ethernet5",
            device_asn=65101,
            pool=pool_dc1,
            fabric_name="fabric-dc1",
        ),
        endpoint_2=_dci_endpoint(
            endpoint_id="dc2-eth5",
            device_id="dc2-leaf1",
            device_name="ih-dc2-leaf1a",
            interface_name="Ethernet5",
            device_asn=65201,
            pool=pool_dc2,
            fabric_name="fabric-dc2",
        ),
    )

    p2p_links = await build_dci_l3_edge_p2p_links(gen.client, dci_links=[link], hostname=hostname)

    assert p2p_links[0]["ip"] == ["172.16.0.0/31", "172.16.0.1/31"]
    assert p2p_links[0]["as"] == [65101, 65201]
    allocation_kwargs = gen.client.allocate_next_ip_prefix.await_args.kwargs
    # sorted-first endpoint (dc1) owns the allocation regardless of the generating device
    assert allocation_kwargs["resource_pool"] is pool_dc1
    assert allocation_kwargs["identifier"] == "dci-link:dci-1"


@pytest.mark.anyio
async def test_dci_pool_falls_back_to_peer_endpoint_when_first_fabric_has_none() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))
    pool_dc2 = _pool("pool-dc2")
    link = _dci_link(
        endpoint_1=_dci_endpoint(
            endpoint_id="dc1-eth5",
            device_id="dc1-leaf1",
            device_name="ih-dc1-leaf1a",
            interface_name="Ethernet5",
            device_asn=65101,
            pool=None,
        ),
        endpoint_2=_dci_endpoint(
            endpoint_id="dc2-eth5",
            device_id="dc2-leaf1",
            device_name="ih-dc2-leaf1a",
            interface_name="Ethernet5",
            device_asn=65201,
            pool=pool_dc2,
        ),
    )

    p2p_links = await build_dci_l3_edge_p2p_links(gen.client, dci_links=[link], hostname="ih-dc1-leaf1a")

    assert len(p2p_links) == 1
    assert gen.client.allocate_next_ip_prefix.await_args.kwargs["resource_pool"] is pool_dc2


@pytest.mark.anyio
async def test_dci_ospf_underlay_omits_as_and_relaxes_asn_requirement() -> None:
    """With a non-eBGP underlay, the DCI link is emitted without `as`.

    Endpoint devices are not required to carry a BGP ASN when the underlay
    routing protocol is OSPF; the link is still generated for reachability.
    """
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=None,
                ),
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=None,
                ),
            )
        ],
        hostname="ih-dc1-leaf1a",
        underlay_routing_protocol="ospf",
    )

    assert len(p2p_links) == 1
    assert "as" not in p2p_links[0]
    assert p2p_links[0]["ip"] == ["172.16.0.0/31", "172.16.0.1/31"]
    assert not validate_inputs(_base_hostvars([], dci_l3_edge_p2p_links=p2p_links)).validation_result.violations


@pytest.mark.anyio
async def test_dci_ebgp_underlay_requires_asn(caplog: pytest.LogCaptureFixture) -> None:
    """With an eBGP underlay, a missing endpoint device ASN skips the link."""
    gen = _make_generator()
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=None,
                ),
            )
        ],
        hostname="ih-dc1-leaf1a",
        underlay_routing_protocol="ebgp",
    )

    assert p2p_links == []
    assert "must have a BGP ASN when the underlay routing protocol is eBGP" in caplog.text


@pytest.mark.anyio
async def test_dci_l3_edge_uses_default_underlay_when_unset() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[_dci_link(include_in_underlay_protocol=None)],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links[0]["include_in_underlay_protocol"] is True


@pytest.mark.anyio
async def test_invalid_dci_link_reports_non_border_leaf_context(caplog: pytest.LogCaptureFixture) -> None:
    gen = _make_generator()
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    role="leaf",
                )
            )
        ],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == []
    assert "both endpoints must be Border Leaf" in caplog.text


@pytest.mark.anyio
async def test_dci_link_requires_peering_endpoint_interfaces(caplog: pytest.LogCaptureFixture) -> None:
    gen = _make_generator()
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    interface_role="server",
                )
            )
        ],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == []
    assert "endpoint interfaces must use role=peering" in caplog.text
    assert "ih-dc2-leaf1a Ethernet5" in caplog.text


@pytest.mark.anyio
async def test_duplicate_dci_endpoint_pairs_are_reported_without_reallocating(
    caplog: pytest.LogCaptureFixture,
) -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[_dci_link("dci-1", name="DCI-1"), _dci_link("dci-2", name="DCI-2")],
        hostname="ih-dc1-leaf1a",
    )

    assert len(p2p_links) == 1
    assert "duplicate endpoint-interface pair" in caplog.text
    gen.client.allocate_next_ip_prefix.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("link", "match"),
    [
        (
            {
                **_dci_link(),
                "connected_endpoints": {
                    "edges": [
                        {
                            "node": _dci_endpoint(
                                endpoint_id="a", device_id="a", device_name="a", interface_name="Ethernet1"
                            )
                        }
                    ]
                },
            },
            "exactly two",
        ),
        (
            {**_dci_link(), "connected_endpoints": {"edges": [{"node": {"__typename": "DcimInterface", "id": "bad"}}]}},
            "not a physical",
        ),
        (
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="a", device_id="same", device_name="same-a", interface_name="Ethernet1"
                ),
                endpoint_2=_dci_endpoint(
                    endpoint_id="b", device_id="same", device_name="same-b", interface_name="Ethernet2"
                ),
            ),
            "different devices",
        ),
        (
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=None,
                ),
            ),
            "both endpoint devices must have a BGP ASN",
        ),
    ],
)
async def test_invalid_dci_links_report_actionable_context(
    link: dict,
    match: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gen = _make_generator()
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[link],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == []
    assert match in caplog.text


@pytest.mark.anyio
async def test_dci_link_requires_fabric_dci_pool(caplog: pytest.LogCaptureFixture) -> None:
    gen = _make_generator()
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[
            _dci_link(
                endpoint_1=_dci_endpoint(
                    endpoint_id="dc1-eth5",
                    device_id="dc1-leaf1",
                    device_name="ih-dc1-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=65101,
                    pool=None,
                ),
                endpoint_2=_dci_endpoint(
                    endpoint_id="dc2-eth5",
                    device_id="dc2-leaf1",
                    device_name="ih-dc2-leaf1a",
                    interface_name="Ethernet5",
                    device_asn=65201,
                    pool=None,
                ),
            )
        ],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == []
    assert "neither endpoint fabric defines a dci_pool" in caplog.text


@pytest.mark.anyio
async def test_mixed_valid_and_invalid_dci_links_emit_valid_and_report_invalid(
    caplog: pytest.LogCaptureFixture,
) -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    valid = _dci_link("dci-valid", name="DCI-Valid")
    invalid = _dci_link(
        "dci-invalid",
        name="DCI-Invalid",
        endpoint_2=_dci_endpoint(
            endpoint_id="dc2-eth6",
            device_id="dc2-leaf2",
            device_name="ih-dc2-leaf2a",
            interface_name="Ethernet6",
            role="leaf",
        ),
    )

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[invalid, valid],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == [
        {
            "nodes": ["ih-dc1-leaf1a", "ih-dc2-leaf1a"],
            "interfaces": ["Ethernet5", "Ethernet5"],
            "as": [65101, 65201],
            "ip": ["172.16.0.0/31", "172.16.0.1/31"],
            "include_in_underlay_protocol": True,
            "speed": "100g",
        }
    ]
    assert "DCI-Invalid" in caplog.text
    assert "both endpoints must be Border Leaf" in caplog.text


@pytest.mark.anyio
async def test_dci_allocation_failure_reports_link_and_continues(caplog: pytest.LogCaptureFixture) -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(side_effect=ValueError("pool exhausted"))
    caplog.set_level(logging.WARNING, logger="infrahub.tasks")

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=[_dci_link()],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links == []
    assert "pool exhausted" in caplog.text


def test_dci_allocation_helper_documents_repository_loaded_generator_exception() -> None:
    assert allocate_dci_p2p_prefix_from_pool.__doc__
    assert "repository-loaded generator" in allocate_dci_p2p_prefix_from_pool.__doc__
    assert "task-worker image" in allocate_dci_p2p_prefix_from_pool.__doc__


@pytest.mark.anyio
@pytest.mark.parametrize("count", [10, 100, 250])
async def test_dci_link_scale_ordering_and_no_duplicate_entries(count: int) -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(
        side_effect=[_mock_prefix(f"172.16.{index // 128}.{(index % 128) * 2}/31") for index in range(count)]
    )
    links = [
        _dci_link(
            f"dci-{index:03}",
            name=f"DCI-{index:03}",
            endpoint_1=_dci_endpoint(
                endpoint_id=f"dc1-eth{index}",
                device_id="dc1-leaf1",
                device_name="ih-dc1-leaf1a",
                interface_name=f"Ethernet{index + 1}",
                speed=None,
            ),
            endpoint_2=_dci_endpoint(
                endpoint_id=f"dc2-eth{index}",
                device_id=f"dc2-leaf{index}",
                device_name=f"ih-dc2-leaf{index:03}",
                interface_name=f"Ethernet{index + 1}",
                speed=None,
            ),
        )
        for index in reversed(range(count))
    ]

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        dci_links=links,
        hostname="ih-dc1-leaf1a",
    )

    assert len(p2p_links) == count
    assert p2p_links[0]["nodes"] == ["ih-dc1-leaf1a", "ih-dc2-leaf000"]
    assert p2p_links[-1]["nodes"] == ["ih-dc1-leaf1a", f"ih-dc2-leaf{count - 1:03}"]
    assert len({tuple(link["nodes"] + link["interfaces"]) for link in p2p_links}) == count


def test_mlag_leaf_uses_rack_node_group_and_domain_id() -> None:
    """MLAG leaf hostvars must use the rack name for group and explicit mlag_domain_id."""
    hostvars = _base_hostvars(
        [],
        rack_info={"name": "DC1_BORDER", "mlag": True, "leaf_names": ["leaf2", "leaf1"]},
        mlag_info={
            "domain_id": "DC1_BORDER",
            "bgp_asn": 65100,
            "virtual_router_mac": None,
            "peer_names": ["leaf1", "leaf2"],
            "mlag_peer_interfaces": ["Ethernet3", "Ethernet4"],
        },
    )

    node_group = hostvars["l3leaf"]["node_groups"][0]
    assert node_group["group"] == "DC1_BORDER"
    assert node_group["mlag_domain_id"] == "DC1_BORDER"
    assert node_group["bgp_as"] == "65100"
    assert node_group["nodes"] == [{"name": "leaf1"}, {"name": "leaf2"}]
    assert "bgp_as" not in hostvars["l3leaf"]["nodes"][0]
    assert hostvars["l3leaf"]["nodes"][0]["mlag_interfaces"] == ["Ethernet3", "Ethernet4"]
    assert "mlag" not in hostvars["l3leaf"].get("defaults", {})
    assert not validate_inputs(hostvars).validation_result.violations


def _leaf_hostvars(
    *,
    hostname: str,
    node_id: int,
    rack_info: dict,
    mlag_info: dict,
) -> dict:
    """Build leaf hostvars with an arbitrary hostname / rack / MLAG context."""
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname=hostname,
        role="leaf",
        bgp_asn=65000 + node_id,
        node_id=node_id,
        loopback_ip=f"10.0.0.{node_id}",
        loopback_ipv4_pool="10.0.0.0/24",
        vtep_loopback_ip="10.2.0.3",
        vtep_loopback_ipv4_pool="10.2.0.0/24",
        mgmt_ip=f"192.168.0.{node_id}",
        fabric_name="Fabric-L3LS-MultiPod-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={"leaf": 8192},
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info=rack_info,
        mlag_info=mlag_info,
        tenants_data=[],
        connected_endpoints=[],
        custom_hostvars={},
    )


def test_multi_pair_rack_keeps_mlag_pairs_in_separate_node_groups() -> None:
    """A rack with two MLAG pairs (4 leafs) must not collapse into one node group.

    Each leaf is grouped by its own pair-unique MLAG domain and lists only its
    peer pair — never all four rack leafs under a single group/domain.
    """
    rack_leaf_names = ["leaf1", "leaf2", "leaf3", "leaf4"]

    def mlag(domain_id: str, peers: list[str], asn: int) -> dict:
        return {"domain_id": domain_id, "bgp_asn": asn, "virtual_router_mac": None, "peer_names": peers}

    def rack() -> dict:
        return {"name": "Rack-X", "mlag": True, "leaf_names": rack_leaf_names}

    leaf1 = _leaf_hostvars(
        hostname="leaf1", node_id=1, rack_info=rack(), mlag_info=mlag("Rack-X", ["leaf1", "leaf2"], 65010)
    )
    leaf3 = _leaf_hostvars(
        hostname="leaf3", node_id=3, rack_info=rack(), mlag_info=mlag("Rack-X-2", ["leaf3", "leaf4"], 65011)
    )

    group1 = leaf1["l3leaf"]["node_groups"][0]
    group3 = leaf3["l3leaf"]["node_groups"][0]

    assert group1["group"] == "Rack-X"
    assert group1["mlag_domain_id"] == "Rack-X"
    assert group1["bgp_as"] == "65010"
    assert group1["nodes"] == [{"name": "leaf1"}, {"name": "leaf2"}]

    assert group3["group"] == "Rack-X-2"
    assert group3["mlag_domain_id"] == "Rack-X-2"
    assert group3["bgp_as"] == "65011"
    assert group3["nodes"] == [{"name": "leaf3"}, {"name": "leaf4"}]

    # The two pairs must remain distinct groups with distinct ASNs.
    assert group1["group"] != group3["group"]
    assert group1["bgp_as"] != group3["bgp_as"]


def _mlag_peer_hostvars(*, hostname: str, node_id: int, device_asn: int) -> dict:
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname=hostname,
        role="leaf",
        bgp_asn=device_asn,
        node_id=node_id,
        loopback_ip=f"10.0.0.{node_id}",
        loopback_ipv4_pool="10.0.0.0/24",
        vtep_loopback_ip="10.2.0.3",
        vtep_loopback_ipv4_pool="10.2.0.0/24",
        mgmt_ip=f"192.168.0.{node_id}/24",
        fabric_name="Fabric-L3LS-MultiPod-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={"leaf": 8192},
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "mlag_peer_ipv4_pool": "10.3.0.0/31",
            "mlag_peer_l3_ipv4_pool": "10.4.0.0/31",
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info={"name": "DC1_BORDER", "mlag": True, "leaf_names": ["leaf1", "leaf2"]},
        mlag_info={
            "domain_id": "DC1_BORDER",
            "bgp_asn": 65100,
            "virtual_router_mac": None,
            "peer_names": ["leaf1", "leaf2"],
            "mlag_peer_interfaces": ["Ethernet3", "Ethernet4"],
        },
        tenants_data=[],
        connected_endpoints=[],
        custom_hostvars={},
    )


def test_mlag_peer_facts_use_shared_node_group_bgp_as() -> None:
    hostvars = {
        "leaf1": _mlag_peer_hostvars(hostname="leaf1", node_id=1, device_asn=65099),
        "leaf2": _mlag_peer_hostvars(hostname="leaf2", node_id=2, device_asn=65098),
    }

    assert hostvars["leaf1"]["l3leaf"]["node_groups"][0]["bgp_as"] == "65100"
    assert hostvars["leaf2"]["l3leaf"]["node_groups"][0]["bgp_as"] == "65100"
    assert not validate_inputs(hostvars["leaf1"]).validation_result.violations
    assert not validate_inputs(hostvars["leaf2"]).validation_result.violations


def test_mlag_leaf_without_domain_asn_fails() -> None:
    with pytest.raises(ValueError, match="has no BGP ASN"):
        _base_hostvars(
            [],
            rack_info={"name": "DC1_BORDER", "mlag": True, "leaf_names": ["leaf1", "leaf2"]},
            mlag_info={
                "domain_id": "DC1_BORDER",
                "bgp_asn": None,
                "virtual_router_mac": None,
                "peer_names": ["leaf1", "leaf2"],
            },
        )


@pytest.mark.parametrize("value", [None, "", {}, []])
def test_extract_custom_hostvars_ignores_empty_values(value: object) -> None:
    assert GenerateAVDDeviceHostvar._extract_custom_hostvars(_custom(value)) == {}


def test_extract_custom_hostvars_parses_yaml_string() -> None:
    hostvars = GenerateAVDDeviceHostvar._extract_custom_hostvars(
        _custom(
            """
            custom_structured_configuration_prefix:
              - custom
            nested:
              enabled: true
            """
        )
    )

    assert hostvars == {
        "custom_structured_configuration_prefix": ["custom"],
        "nested": {"enabled": True},
    }


@pytest.mark.parametrize("value", [["invalid"], "invalid"])
def test_extract_custom_hostvars_rejects_non_mapping_values(value: object) -> None:
    with pytest.raises(TypeError, match="avd_custom_hostvars must be a mapping"):
        GenerateAVDDeviceHostvar._extract_custom_hostvars(_custom(value))


def test_extract_custom_hostvars_rejects_malformed_yaml_string() -> None:
    with pytest.raises(yaml.YAMLError):
        GenerateAVDDeviceHostvar._extract_custom_hostvars(_custom("not: [closed"))


def test_merge_custom_hostvars_scope_precedence_and_replacement() -> None:
    merged = GenerateAVDDeviceHostvar._merge_custom_hostvars(
        {
            "fabric_only": True,
            "scope": "fabric",
            "nested": {"fabric": True, "winner": "fabric"},
            "servers": [{"name": "fabric-server"}],
        },
        {
            "pod_only": True,
            "scope": "pod",
            "nested": {"pod": True, "winner": "pod"},
            "servers": [{"name": "pod-server"}],
        },
        {
            "device_only": True,
            "scope": "device",
            "nested": {"device": True, "winner": "device"},
        },
    )

    assert merged == {
        "fabric_only": True,
        "pod_only": True,
        "device_only": True,
        "scope": "device",
        "nested": {"fabric": True, "pod": True, "device": True, "winner": "device"},
        "servers": [{"name": "pod-server"}],
    }


def test_deep_merge_does_not_mutate_inputs() -> None:
    base = {"nested": {"keep": True, "replace": "base"}, "items": ["base"]}
    overlay = {"nested": {"replace": "overlay"}, "items": ["overlay"]}

    merged = GenerateAVDDeviceHostvar._deep_merge(base, overlay)

    assert merged == {"nested": {"keep": True, "replace": "overlay"}, "items": ["overlay"]}
    assert base == {"nested": {"keep": True, "replace": "base"}, "items": ["base"]}
    assert overlay == {"nested": {"replace": "overlay"}, "items": ["overlay"]}


def test_generated_hostvars_take_precedence_over_custom_hostvars() -> None:
    custom_hostvars = {
        "fabric_name": "custom-fabric",
        "custom_only": {"enabled": True},
        "l3leaf": {
            "defaults": {"platform": "custom-platform"},
            "nodes": [
                {
                    "name": "custom-leaf",
                    "id": 999,
                    "loopback_ipv4_pool": "192.0.2.0/24",
                    "vtep_loopback_ipv4_pool": "198.51.100.0/24",
                }
            ],
        },
        "servers": [{"name": "custom-server"}],
    }

    hostvars = _base_hostvars([], custom_hostvars=custom_hostvars)

    assert hostvars["fabric_name"] == "Fabric-L3LS-MultiPod-A"
    assert hostvars["custom_only"] == {"enabled": True}
    assert hostvars["l3leaf"]["defaults"] == {"platform": "custom-platform", "spanning_tree_priority": 8192}
    assert hostvars["l3leaf"]["nodes"][0]["name"] == "leaf1"
    assert hostvars["l3leaf"]["nodes"][0]["id"] == 3
    assert hostvars["l3leaf"]["nodes"][0]["bgp_as"] == "65001"
    assert hostvars["l3leaf"]["nodes"][0]["loopback_ipv4_address"] == "10.0.0.3"
    assert hostvars["l3leaf"]["nodes"][0]["vtep_loopback_ipv4_address"] == "10.2.0.3"
    assert hostvars["l3leaf"]["nodes"][0]["loopback_ipv4_pool"] == "10.0.0.0/24"
    assert hostvars["l3leaf"]["nodes"][0]["vtep_loopback_ipv4_pool"] == "10.2.0.0/24"
    assert hostvars["l3leaf"]["nodes"][0]["mgmt_ip"] == "192.168.0.3"
    assert hostvars["servers"] == [{"name": "custom-server"}]
    assert custom_hostvars["l3leaf"]["nodes"] == [
        {
            "name": "custom-leaf",
            "id": 999,
            "loopback_ipv4_pool": "192.0.2.0/24",
            "vtep_loopback_ipv4_pool": "198.51.100.0/24",
        }
    ]


def _lag(
    lacp_mode: str = "active",
    evpn_ethernet_segment: bool = False,
    *,
    name: str | None = None,
    channel_id: int | None = None,
    tagged_vlans: list[int] | None = None,
    untagged_vlan: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=_attr(name) if name else None,
        channel_id=_attr(channel_id) if channel_id is not None else None,
        lacp_mode=_attr(lacp_mode),
        evpn_ethernet_segment=_attr(evpn_ethernet_segment),
        tagged_vlan=SimpleNamespace(
            edges=[
                SimpleNamespace(node=SimpleNamespace(vlan_id=_attr(vlan_id), status=_attr("active")))
                for vlan_id in tagged_vlans or []
            ]
        ),
        untagged_vlan=SimpleNamespace(
            node=SimpleNamespace(vlan_id=_attr(untagged_vlan), status=_attr("active")) if untagged_vlan else None
        ),
    )


def _multi_switch_adapter() -> dict:
    return {
        "switches": ["leaf1", "leaf2"],
        "switch_ports": ["Ethernet1", "Ethernet1"],
        "endpoint_ports": ["eth1", "eth2"],
        "mode": "trunk",
        "vlans": "11,19",
        "spanning_tree_portfast": "edge",
    }


def _evpn_hostvar_objects(*, tenant_id: str | None = None, vrf_id: str | None = None) -> tuple:
    svi = SimpleNamespace(
        id="svi-1",
        svi_id=_attr(100),
        name=_attr("web"),
        enabled=_attr(True),
        ip_address_virtual=_attr("10.10.10.1/24"),
        rack_tags=_rel([]),
        avd_tags=_rel([]),
    )
    vrf = SimpleNamespace(
        id=vrf_id,
        name=_attr("VRF1"),
        vrf_vni=_attr(10),
        vtep_diagnostic_loopback=_attr(None),
        vtep_diagnostic_loopback_ip_range=_attr(None),
        svis=_rel([svi]),
    )
    l2vlan = SimpleNamespace(id="l2vlan-1", vlan_id=_attr(200), name=_attr("l2"), vni_override=_attr(20200))
    tenant = SimpleNamespace(
        id=tenant_id,
        name=_attr("T1"),
        mac_vrf_vni_base=_attr(10000),
        vrfs=_rel([vrf]),
        l2vlans=_rel([l2vlan]),
    )
    return tenant, vrf, svi, l2vlan


@pytest.mark.anyio
async def test_tenants_hostvars_returns_empty_when_tenant_lookup_is_empty() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[])

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data == []
    gen.client.filters.assert_awaited_once_with(kind="EvpnTenant", fabrics__ids=["fabric-1"])


@pytest.mark.anyio
async def test_tenants_hostvars_prefers_child_side_filters() -> None:
    tenant, vrf, svi, l2vlan = _evpn_hostvar_objects(tenant_id="tenant-1", vrf_id="vrf-1")
    tenant.vrfs = _rel([SimpleNamespace(name=_attr("WRONG"))])
    tenant.l2vlans = _rel([SimpleNamespace(vlan_id=_attr(999), name=_attr("WRONG"))])
    vrf.svis = _rel([SimpleNamespace(svi_id=_attr(999), name=_attr("WRONG"))])

    async def filters_side_effect(*, kind: str, **kwargs: object) -> list[object]:
        match kind:
            case "EvpnTenant":
                assert kwargs == {"fabrics__ids": ["fabric-1"]}
                return [tenant]
            case "IpamVRF":
                assert kwargs == {"tenant__ids": ["tenant-1"]}
                return [vrf]
            case "EvpnSvi":
                assert kwargs == {"vrf__ids": ["vrf-1"]}
                return [svi]
            case "EvpnL2Vlan":
                assert kwargs == {"tenant__ids": ["tenant-1"]}
                return [l2vlan]
        pytest.fail(f"unexpected filter kind {kind}")

    gen = _make_generator()
    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data == [
        {
            "name": "T1",
            "mac_vrf_vni_base": 10000,
            "vrfs": [
                {
                    "name": "VRF1",
                    "vrf_vni": 10,
                    "svis": [{"id": 100, "name": "web", "enabled": True, "ip_address_virtual": "10.10.10.1/24"}],
                }
            ],
            "l2vlans": [{"id": 200, "name": "l2", "vni_override": 20200}],
        }
    ]
    gen.client.filters.assert_any_await(kind="IpamVRF", tenant__ids=["tenant-1"])
    gen.client.filters.assert_any_await(kind="EvpnSvi", vrf__ids=["vrf-1"])
    gen.client.filters.assert_any_await(kind="EvpnL2Vlan", tenant__ids=["tenant-1"])
    tenant.vrfs.fetch.assert_not_awaited()
    vrf.svis.fetch.assert_not_awaited()
    tenant.l2vlans.fetch.assert_not_awaited()


@pytest.mark.anyio
async def test_tenants_hostvars_falls_back_when_child_side_filters_return_empty() -> None:
    tenant, vrf, _svi, _l2vlan = _evpn_hostvar_objects(tenant_id="tenant-1", vrf_id="vrf-1")

    async def filters_side_effect(*, kind: str, **kwargs: object) -> list[object]:
        if kind == "EvpnTenant":
            return [tenant]
        return []

    gen = _make_generator()
    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data[0]["vrfs"][0]["name"] == "VRF1"
    assert tenants_data[0]["vrfs"][0]["svis"][0]["name"] == "web"
    assert tenants_data[0]["l2vlans"][0]["vni_override"] == 20200
    tenant.vrfs.fetch.assert_awaited_once()
    vrf.svis.fetch.assert_awaited_once()
    tenant.l2vlans.fetch.assert_awaited_once()


@pytest.mark.anyio
@pytest.mark.parametrize("exception_type", [AttributeError, KeyError])
async def test_tenants_hostvars_falls_back_when_child_side_filters_raise(exception_type: type[Exception]) -> None:
    tenant, vrf, _svi, _l2vlan = _evpn_hostvar_objects(tenant_id="tenant-1", vrf_id="vrf-1")

    async def filters_side_effect(*, kind: str, **kwargs: object) -> list[object]:
        if kind == "EvpnTenant":
            return [tenant]
        raise exception_type

    gen = _make_generator()
    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data[0]["vrfs"][0]["name"] == "VRF1"
    assert tenants_data[0]["vrfs"][0]["svis"][0]["name"] == "web"
    assert tenants_data[0]["l2vlans"][0]["vni_override"] == 20200
    tenant.vrfs.fetch.assert_awaited_once()
    vrf.svis.fetch.assert_awaited_once()
    tenant.l2vlans.fetch.assert_awaited_once()


@pytest.mark.anyio
async def test_tenants_hostvars_validate_against_pyavd():
    """EVPN tenant payload (incl. l2vlan vni_override) must pass pyAVD validation.

    Regression guard for the AVD 6.3 target, which expects the l2vlan key to be
    `vni_override` and rejects the old `vni` key with an invalid-key error.
    """
    svi = SimpleNamespace(
        svi_id=_attr(100),
        name=_attr("web"),
        enabled=_attr(True),
        ip_address_virtual=_attr("10.10.10.1/24"),
    )
    vrf = SimpleNamespace(
        name=_attr("VRF1"),
        vrf_vni=_attr(10),
        vtep_diagnostic_loopback=_attr(None),
        vtep_diagnostic_loopback_ip_range=_attr(None),
        svis=_rel([svi]),
    )
    l2vlan = SimpleNamespace(vlan_id=_attr(200), name=_attr("l2"), vni_override=_attr(20200))
    tenant = SimpleNamespace(
        name=_attr("T1"),
        mac_vrf_vni_base=_attr(10000),
        vrfs=_rel([vrf]),
        l2vlans=_rel([l2vlan]),
    )

    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[tenant])

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    # The bug site: the l2vlan must use `vni_override`, not `vni`.
    assert tenants_data[0]["l2vlans"][0]["vni_override"] == 20200

    hostvars = _base_hostvars(tenants_data)
    assert not validate_inputs(hostvars).validation_result.violations
    assert hostvars["tenants"][0]["l2vlans"][0]["vni_override"] == 20200


@pytest.mark.anyio
async def test_svi_rack_tags_emit_rack_names() -> None:
    svi = SimpleNamespace(
        svi_id=_attr(100),
        name=_attr("web"),
        enabled=_attr(True),
        ip_address_virtual=_attr("10.10.10.1/24"),
        rack_tags=_rel([_named_peer("Rack-B"), _named_peer("Rack-A")]),
        avd_tags=_rel([]),
    )
    vrf = SimpleNamespace(
        name=_attr("VRF1"),
        vrf_vni=_attr(None),
        vtep_diagnostic_loopback=_attr(None),
        vtep_diagnostic_loopback_ip_range=_attr(None),
        svis=_rel([svi]),
    )
    tenant = SimpleNamespace(name=_attr("T1"), mac_vrf_vni_base=_attr(10000), vrfs=_rel([vrf]), l2vlans=_rel([]))
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[tenant])

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data[0]["vrfs"][0]["svis"][0]["tags"] == ["Rack-A", "Rack-B"]
    assert not validate_inputs(_base_hostvars(tenants_data)).validation_result.violations


@pytest.mark.anyio
async def test_svi_avd_tags_emit_tag_names() -> None:
    svi = SimpleNamespace(
        svi_id=_attr(100),
        name=_attr("web"),
        enabled=_attr(True),
        ip_address_virtual=_attr("10.10.10.1/24"),
        rack_tags=_rel([]),
        avd_tags=_rel([_named_peer("storage"), _named_peer("compute")]),
    )
    vrf = SimpleNamespace(
        name=_attr("VRF1"),
        vrf_vni=_attr(None),
        vtep_diagnostic_loopback=_attr(None),
        vtep_diagnostic_loopback_ip_range=_attr(None),
        svis=_rel([svi]),
    )
    tenant = SimpleNamespace(name=_attr("T1"), mac_vrf_vni_base=_attr(10000), vrfs=_rel([vrf]), l2vlans=_rel([]))
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[tenant])

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert tenants_data[0]["vrfs"][0]["svis"][0]["tags"] == ["compute", "storage"]
    assert not validate_inputs(_base_hostvars(tenants_data)).validation_result.violations


def test_mixed_svi_tags_are_deduplicated_with_rack_names_first() -> None:
    tags = GenerateAVDDeviceHostvar._build_svi_tags(
        [_named_peer("shared"), _named_peer("Rack-A"), _named_peer("shared")],
        [_named_peer("blue"), _named_peer("shared"), _named_peer("blue")],
    )

    assert tags == ["Rack-A", "shared", "blue"]


@pytest.mark.anyio
async def test_empty_svi_tag_relationships_omit_tags() -> None:
    svi = SimpleNamespace(
        svi_id=_attr(100),
        name=_attr("web"),
        enabled=_attr(True),
        ip_address_virtual=_attr("10.10.10.1/24"),
        rack_tags=_rel([]),
        avd_tags=_rel([]),
    )
    vrf = SimpleNamespace(
        name=_attr("VRF1"),
        vrf_vni=_attr(None),
        vtep_diagnostic_loopback=_attr(None),
        vtep_diagnostic_loopback_ip_range=_attr(None),
        svis=_rel([svi]),
    )
    tenant = SimpleNamespace(name=_attr("T1"), mac_vrf_vni_base=_attr(10000), vrfs=_rel([vrf]), l2vlans=_rel([]))
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[tenant])

    tenants_data = await gen._build_tenants_hostvars("fabric-1")

    assert "tags" not in tenants_data[0]["vrfs"][0]["svis"][0]
    assert not validate_inputs(_base_hostvars(tenants_data)).validation_result.violations


def test_rack_avd_tags_emit_node_group_filter_tags() -> None:
    hostvars = _base_hostvars(
        [],
        rack_info={"name": "DC1_BORDER", "mlag": False, "leaf_names": ["leaf1"], "avd_tags": ["storage", "compute"]},
    )

    node_group = hostvars["l3leaf"]["node_groups"][0]
    assert node_group["filter"] == {"tags": ["compute", "storage"]}
    assert not validate_inputs(hostvars).validation_result.violations


@pytest.mark.anyio
async def test_rack_avd_tags_are_fetched_by_rack_id() -> None:
    gen = _make_generator()
    rack = SimpleNamespace(avd_tags=_rel([_named_peer("storage"), _named_peer("compute")]))
    gen.client.get = AsyncMock(return_value=rack)

    tags = await gen._fetch_rack_avd_tags("rack-1")

    assert tags == ["compute", "storage"]
    gen.client.get.assert_awaited_once_with(kind="LocationRack", id="rack-1", include=["avd_tags"])


def test_generated_only_p2p_mtu_resolves() -> None:
    fabric = SimpleNamespace(p_2_p_uplinks_mtu=_attr(1500))

    assert GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu") == 1500


def test_schema_name_only_p2p_mtu_resolves() -> None:
    fabric = SimpleNamespace(p2p_uplinks_mtu=_attr(9000))

    assert GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu") == 9000


def test_generated_p2p_mtu_preferred_when_both_names_exist() -> None:
    fabric = SimpleNamespace(p_2_p_uplinks_mtu=_attr(1500), p2p_uplinks_mtu=_attr(9000))

    assert GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu") == 1500


def test_generated_p2p_mtu_none_falls_back_to_schema_name() -> None:
    fabric = SimpleNamespace(p_2_p_uplinks_mtu=_attr(None), p2p_uplinks_mtu=_attr(9000))

    assert GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu") == 9000


def test_generated_p2p_mtu_zero_does_not_fall_back() -> None:
    fabric = SimpleNamespace(p_2_p_uplinks_mtu=_attr(0), p2p_uplinks_mtu=_attr(9000))

    assert GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu") == 0


def test_hostvars_include_p2p_mtu_from_generated_alias() -> None:
    fabric = SimpleNamespace(p_2_p_uplinks_mtu=_attr(1500))
    p2p_uplinks_mtu = GenerateAVDDeviceHostvar._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu")

    hostvars = GenerateAVDDeviceHostvar._build_hostvars(
        hostname="leaf1",
        role="leaf",
        bgp_asn=65001,
        node_id=3,
        loopback_ip="10.0.0.3",
        loopback_ipv4_pool="10.0.0.0/24",
        vtep_loopback_ip="10.2.0.3",
        vtep_loopback_ipv4_pool="10.2.0.0/24",
        mgmt_ip="192.168.0.3",
        fabric_name="Fabric-L3LS-MultiPod-A",
        mgmt_gateway=None,
        virtual_router_mac=None,
        underlay_routing_protocol=None,
        overlay_routing_protocol=None,
        p2p_uplinks_mtu=p2p_uplinks_mtu,
        spanning_tree_mode=None,
        spanning_tree_priorities={},
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info={"name": "DC1_BORDER", "mlag": False, "leaf_names": ["leaf1"]},
        mlag_info={"domain_id": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=[],
        connected_endpoints=[],
        custom_hostvars={},
    )

    assert hostvars["p2p_uplinks_mtu"] == 1500


def test_lag_without_evpn_knob_preserves_port_channel_only() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(evpn_ethernet_segment=False), mlag_active=False)

    assert adapter["port_channel"] == {"mode": "active"}
    assert "ethernet_segment" not in adapter


def test_evpn_lag_multi_switch_non_mlag_emits_ethernet_segment() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(evpn_ethernet_segment=True), mlag_active=False)

    assert adapter["ethernet_segment"] == {"short_esi": "auto"}


def test_evpn_lag_with_mlag_active_does_not_emit_ethernet_segment() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(evpn_ethernet_segment=True), mlag_active=True)

    assert "ethernet_segment" not in adapter


def test_evpn_lag_single_switch_does_not_emit_ethernet_segment() -> None:
    adapter = _multi_switch_adapter()
    adapter["switches"] = ["leaf1"]
    adapter["switch_ports"] = ["Ethernet1"]
    adapter["endpoint_ports"] = ["eth1"]

    apply_lag_adapter_config(adapter, _lag(evpn_ethernet_segment=True), mlag_active=False)

    assert "ethernet_segment" not in adapter


def test_disabled_lacp_mode_maps_to_pyavd_on() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(lacp_mode="disabled"), mlag_active=False)

    assert adapter["port_channel"] == {"mode": "on"}


def test_switch_lag_channel_id_is_emitted() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(name="Port-Channel1117", channel_id=1117), mlag_active=False)

    assert adapter["port_channel"] == {"mode": "active", "channel_id": 1117}


def test_switch_lag_name_only_channel_id_is_parsed() -> None:
    adapter = _multi_switch_adapter()

    apply_lag_adapter_config(adapter, _lag(name="Port-Channel1117"), mlag_active=False)

    assert adapter["port_channel"] == {"mode": "active", "channel_id": 1117}


def test_switch_lag_channel_id_name_mismatch_fails() -> None:
    adapter = _multi_switch_adapter()

    with pytest.raises(ValueError, match="implies channel ID 1117, but channel_id is 42"):
        apply_lag_adapter_config(adapter, _lag(name="Port-Channel1117", channel_id=42), mlag_active=False)


def test_conflicting_switch_lag_ids_fail() -> None:
    server = {"name": "server1", "adapters": []}
    groups: dict[tuple[str, int], dict] = {}

    with pytest.raises(ValueError, match="Conflicting switch LAG channel ID"):
        _add_switch_lag_adapter(
            server,
            groups,
            server_name="server1",
            switch_lag_node=_lag(name="Port-Channel1117", channel_id=1117),
            endpoint_lag_node=None,
            links=[
                {
                    "endpoint_port": "Ethernet1",
                    "switch_port": "Ethernet1/1/17",
                    "switch": "leaf1",
                    "switch_lag": _lag(name="Port-Channel42", channel_id=42),
                    "vlan": ((11,), None),
                }
            ],
        )


def test_conflicting_switch_lag_vlans_fail() -> None:
    server = {"name": "server1", "adapters": []}
    groups: dict[tuple[str, int], dict] = {}

    with pytest.raises(ValueError, match="Conflicting VLANs"):
        _add_switch_lag_adapter(
            server,
            groups,
            server_name="server1",
            switch_lag_node=_lag(name="Port-Channel1117", channel_id=1117),
            endpoint_lag_node=None,
            links=[
                {
                    "endpoint_port": "Ethernet1",
                    "switch_port": "Ethernet1/1/17",
                    "switch": "leaf1",
                    "switch_lag": _lag(name="Port-Channel1117", channel_id=1117),
                    "vlan": ((11,), None),
                },
                {
                    "endpoint_port": "Ethernet2",
                    "switch_port": "Ethernet1/1/17",
                    "switch": "leaf2",
                    "switch_lag": _lag(name="Port-Channel1117", channel_id=1117),
                    "vlan": ((12,), None),
                },
            ],
        )


def test_server_bond_vlans_drive_switch_lag_adapter_without_member_vlans() -> None:
    server = {"name": "server1", "adapters": []}
    groups: dict[tuple[str, int], dict] = {}
    server_bond = _lag(name="Bond1", tagged_vlans=[300, 400], untagged_vlan=100)
    switch_lag = _lag(name="Port-Channel1117", channel_id=1117)
    fallback_local = SimpleNamespace(
        name=_attr("Ethernet1/1/17"),
        tagged_vlan=SimpleNamespace(edges=[]),
        untagged_vlan=SimpleNamespace(node=None),
    )
    fallback_endpoint = SimpleNamespace(name=_attr("Ethernet1"))

    links = hostvar_module._switch_lag_member_links(
        server_lag_node=server_bond,
        fallback_switch_lag_node=switch_lag,
        fallback_local_interface=fallback_local,
        fallback_endpoint=fallback_endpoint,
        hostname="leaf1",
    )
    _add_switch_lag_adapter(
        server,
        groups,
        server_name="server1",
        switch_lag_node=switch_lag,
        endpoint_lag_node=server_bond,
        links=links,
    )
    hostvar_module._flush_switch_lag_groups(groups, mlag_active=False)

    assert server["adapters"] == [
        {
            "endpoint_ports": ["Ethernet1"],
            "switch_ports": ["Ethernet1/1/17"],
            "switches": ["leaf1"],
            "port_channel": {"mode": "active", "channel_id": 1117, "endpoint_port_channel": "Bond1"},
            "spanning_tree_portfast": "edge",
            "mode": "trunk",
            "vlans": "300,400",
            "native_vlan": 100,
        }
    ]
    assert not validate_inputs(_base_hostvars([], connected_endpoints=[server])).validation_result.violations


def test_switch_lag_vlans_are_used_when_server_bond_has_no_vlan_relationships() -> None:
    server = {"name": "server1", "adapters": []}
    groups: dict[tuple[str, int], dict] = {}
    server_bond = _lag(name="Bond1")
    switch_lag = _lag(name="Port-Channel1117", channel_id=1117, tagged_vlans=[300, 400])
    fallback_local = SimpleNamespace(
        name=_attr("Ethernet1/1/17"),
        tagged_vlan=SimpleNamespace(edges=[]),
        untagged_vlan=SimpleNamespace(node=None),
    )
    fallback_endpoint = SimpleNamespace(name=_attr("Ethernet1"))

    links = hostvar_module._switch_lag_member_links(
        server_lag_node=server_bond,
        fallback_switch_lag_node=switch_lag,
        fallback_local_interface=fallback_local,
        fallback_endpoint=fallback_endpoint,
        hostname="leaf1",
    )
    _add_switch_lag_adapter(
        server,
        groups,
        server_name="server1",
        switch_lag_node=switch_lag,
        endpoint_lag_node=server_bond,
        links=links,
    )
    hostvar_module._flush_switch_lag_groups(groups, mlag_active=False)

    assert server["adapters"][0]["mode"] == "trunk"
    assert server["adapters"][0]["vlans"] == "300,400"


def test_server_lag_evpn_hostvars_validate_against_pyavd() -> None:
    adapter = _multi_switch_adapter()
    apply_lag_adapter_config(adapter, _lag(name="Port-Channel1117", evpn_ethernet_segment=True), mlag_active=False)

    hostvars = _base_hostvars(
        tenants_data=[],
        connected_endpoints=[{"name": "server1", "adapters": [adapter]}],
    )

    assert not validate_inputs(hostvars).validation_result.violations
