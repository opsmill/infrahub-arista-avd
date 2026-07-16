"""Unit tests for the AVD hostvar generator's tenant/EVPN payload."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pyavd import get_avd_facts, validate_inputs

from generators.generate_avd_device_hostvar import GenerateAVDDeviceHostvar


def _attr(value: object) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _rel(peers: list[object]) -> SimpleNamespace:
    return SimpleNamespace(fetch=AsyncMock(), peers=[SimpleNamespace(peer=p) for p in peers])


def _make_generator() -> GenerateAVDDeviceHostvar:
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)
    gen.client = AsyncMock()
    return gen


def _base_hostvars(
    tenants_data: list[dict],
    *,
    rack_info: dict | None = None,
    mlag_info: dict | None = None,
) -> dict:
    """Minimal leaf hostvars wrapping the tenant payload, mirroring generate()."""
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname="leaf1",
        role="leaf",
        bgp_asn=65001,
        node_id=3,
        loopback_ip="10.0.0.3",
        mgmt_ip="192.168.0.3",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priority=4096,
        loopback_ipv4_offset=None,
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "vtep_loopback_ipv4_pool": "10.2.0.0/24",
            "loopback_ipv4_pool": "10.0.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info=rack_info or {"name": "DC1_BORDER", "mlag": False, "leaf_names": ["leaf1"]},
        mlag_info=mlag_info or {"domain_id": None, "bgp_asn": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=tenants_data,
        connected_endpoints=[],
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
        mgmt_ip=f"192.168.0.{node_id}",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priority=4096,
        loopback_ipv4_offset=None,
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "vtep_loopback_ipv4_pool": "10.2.0.0/24",
            "loopback_ipv4_pool": "10.0.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        rack_info=rack_info,
        mlag_info=mlag_info,
        tenants_data=[],
        connected_endpoints=[],
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
        mgmt_ip=f"192.168.0.{node_id}/24",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priority=4096,
        loopback_ipv4_offset=None,
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "vtep_loopback_ipv4_pool": "10.2.0.0/24",
            "loopback_ipv4_pool": "10.0.0.0/24",
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
    )


def test_mlag_peer_facts_use_shared_node_group_bgp_as() -> None:
    hostvars = {
        "leaf1": _mlag_peer_hostvars(hostname="leaf1", node_id=1, device_asn=65099),
        "leaf2": _mlag_peer_hostvars(hostname="leaf2", node_id=2, device_asn=65098),
    }

    facts = get_avd_facts(hostvars)

    assert facts["leaf1"]._as_dict()["bgp_as"] == "65100"
    assert facts["leaf2"]._as_dict()["bgp_as"] == "65100"


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


@pytest.mark.anyio
async def test_tenants_hostvars_validate_against_pyavd():
    """EVPN tenant payload (incl. l2vlan vni_override) must pass pyAVD validation.

    Regression guard for the AVD 6.2 upgrade, which renamed the l2vlan key to
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
    # get_avd_facts is where the invalid key surfaced as a hard KeyError pre-fix.
    get_avd_facts({"leaf1": hostvars})


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
        mgmt_ip="192.168.0.3",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac=None,
        underlay_routing_protocol=None,
        overlay_routing_protocol=None,
        p2p_uplinks_mtu=p2p_uplinks_mtu,
        spanning_tree_mode=None,
        spanning_tree_priority=None,
        loopback_ipv4_offset=None,
        bgp_passwords={"evpn_overlay": None, "underlay": None, "mlag": None},
        management={},
        pools={
            "uplink_ipv4_pool": "10.1.0.0/24",
            "vtep_loopback_ipv4_pool": "10.2.0.0/24",
            "loopback_ipv4_pool": "10.0.0.0/24",
            "mlag_peer_ipv4_pool": None,
            "mlag_peer_l3_ipv4_pool": None,
        },
        uplinks={"uplink_interfaces": [], "uplink_switches": [], "uplink_switch_interfaces": []},
        mlag_info={"domain_id": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=[],
        connected_endpoints=[],
    )

    assert hostvars["p2p_uplinks_mtu"] == 1500
