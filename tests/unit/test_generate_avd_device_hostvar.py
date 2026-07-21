"""Unit tests for the AVD hostvar generator's tenant/EVPN payload."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import yaml
from pyavd import get_avd_facts, validate_inputs

from generators.generate_avd_device_hostvar import (
    GenerateAVDDeviceHostvar,
    _add_switch_lag_adapter,  # noqa: PLC2701 - focused unit coverage for internal conflict validation
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


def _pool(pool_id: str = "pool-1") -> SimpleNamespace:
    return SimpleNamespace(id=pool_id, name=_attr("DCI-Pool"))


def _fabric_with_dci_pool() -> dict:
    return {"dci_pool": {"node": _pool()}}


def _fabric_with_dci_pool_dict() -> dict:
    return {"dci_pool": {"node": {"id": "pool-1", "name": {"value": "DCI-Pool"}}}}


def _dci_endpoint(
    *,
    endpoint_id: str,
    device_id: str,
    device_name: str,
    interface_name: str,
    role: str = "border_leaf",
    speed: str | None = "100g",
) -> dict:
    endpoint = {
        "__typename": "InterfacePhysical",
        "id": endpoint_id,
        "name": {"value": interface_name},
        "device": {
            "node": {
                "__typename": "DcimDevice",
                "id": device_id,
                "name": {"value": device_name},
                "role": {"value": role},
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
    asn_1: int | None = 65101,
    asn_2: int | None = 65201,
    include_in_underlay_protocol: bool | None = True,
) -> dict:
    link = {
        "__typename": "NetworkDciLink",
        "id": link_id,
        "display_label": name,
        "name": {"value": name},
        "endpoint_1_bgp_asn": {"value": asn_1},
        "endpoint_2_bgp_asn": {"value": asn_2},
        "connected_endpoints": {
            "edges": [
                {
                    "node": endpoint_1
                    or _dci_endpoint(
                        endpoint_id="dc1-eth5",
                        device_id="dc1-leaf1",
                        device_name="ih-dc1-leaf1a",
                        interface_name="Ethernet5",
                    )
                },
                {
                    "node": endpoint_2
                    or _dci_endpoint(
                        endpoint_id="dc2-eth5",
                        device_id="dc2-leaf1",
                        device_name="ih-dc2-leaf1a",
                        interface_name="Ethernet5",
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
) -> dict:
    """Minimal leaf hostvars wrapping the tenant payload, mirroring generate()."""
    return GenerateAVDDeviceHostvar._build_hostvars(
        hostname="leaf1",
        role=role,
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
        spanning_tree_priorities={"leaf": 8192},
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
        connected_endpoints=connected_endpoints or [],
        dci_l3_edge_p2p_links=dci_l3_edge_p2p_links,
        custom_hostvars=custom_hostvars or {},
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


def test_border_leaf_builds_l3leaf_hostvars() -> None:
    hostvars = _base_hostvars([], role="border_leaf")

    assert hostvars["type"] == "l3leaf"
    assert hostvars["l3leaf"]["nodes"][0]["name"] == "leaf1"
    assert hostvars["l3leaf"]["node_groups"][0]["nodes"] == [{"name": "leaf1"}]
    assert not validate_inputs(hostvars).validation_result.violations


@pytest.mark.anyio
async def test_dci_l3_edge_p2p_link_output_with_resolved_speed() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        fabric=_fabric_with_dci_pool(),
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
        fabric=_fabric_with_dci_pool(),
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

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        fabric=_fabric_with_dci_pool_dict(),
        dci_links=[_dci_link()],
        hostname="ih-dc1-leaf1a",
    )

    gen.client.get.assert_awaited_once_with(kind="CoreIPPrefixPool", id="pool-1")
    allocation_kwargs = gen.client.allocate_next_ip_prefix.await_args.kwargs
    assert allocation_kwargs["resource_pool"] is hydrated_pool
    assert allocation_kwargs["member_type"] == "prefix"
    assert allocation_kwargs["data"] == {"role": "technical"}
    assert p2p_links[0]["ip"] == ["172.16.0.0/31", "172.16.0.1/31"]


@pytest.mark.anyio
async def test_dci_l3_edge_uses_default_underlay_when_unset() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    p2p_links = await build_dci_l3_edge_p2p_links(
        gen.client,
        fabric=_fabric_with_dci_pool(),
        dci_links=[_dci_link(include_in_underlay_protocol=None)],
        hostname="ih-dc1-leaf1a",
    )

    assert p2p_links[0]["include_in_underlay_protocol"] is True


@pytest.mark.anyio
async def test_invalid_dci_link_reports_non_border_leaf_context() -> None:
    gen = _make_generator()

    with pytest.raises(ValueError, match="both endpoints must be Border Leaf"):
        await build_dci_l3_edge_p2p_links(
            gen.client,
            fabric=_fabric_with_dci_pool(),
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


@pytest.mark.anyio
async def test_duplicate_dci_endpoint_pairs_are_rejected_before_allocation() -> None:
    gen = _make_generator()
    gen.client.allocate_next_ip_prefix = AsyncMock(return_value=_mock_prefix("172.16.0.0/31"))

    with pytest.raises(ValueError, match="duplicate endpoint-interface pair"):
        await build_dci_l3_edge_p2p_links(
            gen.client,
            fabric=_fabric_with_dci_pool(),
            dci_links=[_dci_link("dci-1", name="DCI-1"), _dci_link("dci-2", name="DCI-2")],
            hostname="ih-dc1-leaf1a",
        )

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
        (_dci_link(asn_1=None), "both endpoint BGP ASN"),
    ],
)
async def test_invalid_dci_links_report_actionable_context(link: dict, match: str) -> None:
    gen = _make_generator()

    with pytest.raises(ValueError, match=match):
        await build_dci_l3_edge_p2p_links(
            gen.client,
            fabric=_fabric_with_dci_pool(),
            dci_links=[link],
            hostname="ih-dc1-leaf1a",
        )


@pytest.mark.anyio
async def test_dci_link_requires_fabric_dci_pool() -> None:
    gen = _make_generator()

    with pytest.raises(ValueError, match="missing dci_pool"):
        await build_dci_l3_edge_p2p_links(
            gen.client,
            fabric={"dci_pool": {"node": None}},
            dci_links=[_dci_link()],
            hostname="ih-dc1-leaf1a",
        )


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
        fabric=_fabric_with_dci_pool(),
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
        mgmt_ip=f"192.168.0.{node_id}",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={"leaf": 8192},
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
        mgmt_ip=f"192.168.0.{node_id}/24",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac="00:1c:73:00:00:99",
        underlay_routing_protocol="ebgp",
        overlay_routing_protocol="ebgp",
        p2p_uplinks_mtu=9000,
        spanning_tree_mode="mstp",
        spanning_tree_priorities={"leaf": 8192},
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
        custom_hostvars={},
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
            "nodes": [{"name": "custom-leaf", "id": 999}],
        },
        "servers": [{"name": "custom-server"}],
    }

    hostvars = _base_hostvars([], custom_hostvars=custom_hostvars)

    assert hostvars["fabric_name"] == "Fabric-A"
    assert hostvars["custom_only"] == {"enabled": True}
    assert hostvars["l3leaf"]["defaults"] == {"platform": "custom-platform", "spanning_tree_priority": 8192}
    assert hostvars["l3leaf"]["nodes"][0]["name"] == "leaf1"
    assert hostvars["l3leaf"]["nodes"][0]["id"] == 3
    assert hostvars["l3leaf"]["nodes"][0]["bgp_as"] == "65001"
    assert hostvars["l3leaf"]["nodes"][0]["loopback_ipv4_address"] == "10.0.0.3"
    assert hostvars["l3leaf"]["nodes"][0]["mgmt_ip"] == "192.168.0.3"
    assert hostvars["servers"] == [{"name": "custom-server"}]
    assert custom_hostvars["l3leaf"]["nodes"] == [{"name": "custom-leaf", "id": 999}]


def _lag(
    lacp_mode: str = "active",
    evpn_ethernet_segment: bool = False,
    *,
    name: str | None = None,
    channel_id: int | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=_attr(name) if name else None,
        channel_id=_attr(channel_id) if channel_id is not None else None,
        lacp_mode=_attr(lacp_mode),
        evpn_ethernet_segment=_attr(evpn_ethernet_segment),
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
    # get_avd_facts is where the invalid key surfaced as a hard KeyError pre-fix.
    get_avd_facts({"leaf1": hostvars})


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
        mgmt_ip="192.168.0.3",
        fabric_name="Fabric-A",
        mgmt_gateway=None,
        virtual_router_mac=None,
        underlay_routing_protocol=None,
        overlay_routing_protocol=None,
        p2p_uplinks_mtu=p2p_uplinks_mtu,
        spanning_tree_mode=None,
        spanning_tree_priorities={},
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


def test_server_lag_evpn_hostvars_validate_against_pyavd() -> None:
    adapter = _multi_switch_adapter()
    apply_lag_adapter_config(adapter, _lag(name="Port-Channel1117", evpn_ethernet_segment=True), mlag_active=False)

    hostvars = _base_hostvars(
        tenants_data=[],
        connected_endpoints=[{"name": "server1", "adapters": [adapter]}],
    )

    assert not validate_inputs(hostvars).validation_result.violations
