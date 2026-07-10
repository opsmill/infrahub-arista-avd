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
        mlag_info=mlag_info or {"domain_id": None, "virtual_router_mac": None, "peer_names": []},
        tenants_data=tenants_data,
        connected_endpoints=[],
    )


def test_non_mlag_leaf_sets_avd_mlag_false_on_rack_node_group() -> None:
    """Leaf hostvars without an MLAG domain must explicitly disable MLAG on the rack node group."""
    hostvars = _base_hostvars([])

    node_group = hostvars["l3leaf"]["node_groups"][0]
    assert node_group["group"] == "DC1_BORDER"
    assert node_group["nodes"] == [{"name": "leaf1"}]
    assert node_group["mlag"] is False
    assert "mlag" not in hostvars["l3leaf"].get("defaults", {})
    assert not validate_inputs(hostvars).validation_result.violations


def test_mlag_leaf_uses_rack_node_group_and_domain_id() -> None:
    """MLAG leaf hostvars must use the rack name for group and explicit mlag_domain_id."""
    hostvars = _base_hostvars(
        [],
        rack_info={"name": "DC1_BORDER", "mlag": True, "leaf_names": ["leaf2", "leaf1"]},
        mlag_info={
            "domain_id": "DC1_BORDER",
            "virtual_router_mac": None,
            "peer_names": ["leaf1", "leaf2"],
            "mlag_peer_interfaces": ["Ethernet3", "Ethernet4"],
        },
    )

    node_group = hostvars["l3leaf"]["node_groups"][0]
    assert node_group["group"] == "DC1_BORDER"
    assert node_group["mlag_domain_id"] == "DC1_BORDER"
    assert node_group["nodes"] == [{"name": "leaf1"}, {"name": "leaf2"}]
    assert hostvars["l3leaf"]["nodes"][0]["mlag_interfaces"] == ["Ethernet3", "Ethernet4"]
    assert "mlag" not in hostvars["l3leaf"].get("defaults", {})
    assert not validate_inputs(hostvars).validation_result.violations


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
