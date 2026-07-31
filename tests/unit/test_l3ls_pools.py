"""Unit tests for schema-driven IP pool extraction in the AVD hostvar generator.

These tests pin the behavior introduced when the hardcoded fallback prefixes
(10.250.0.0/16, 10.251.0.0/24, 10.255.0.0/24) were replaced by data-model
relationships: hostvars still require the uplink pool, loopback/VTEP addresses
come from device relationships, and the MLAG pools stay optional.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.generate_avd_device_hostvar import GenerateAVDDeviceHostvar
from solution_arista_avd.pool_roles import ResourceRole


def _attr(value: object) -> SimpleNamespace:
    """Mimic an Infrahub attribute node exposing `.value`."""
    return SimpleNamespace(value=value)


def _edge(node: object) -> dict:
    return {"node": node}


def _pool_node(name: str, role: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"id-{name}",
        name=_attr(name),
        resources=SimpleNamespace(edges=[SimpleNamespace(node=SimpleNamespace(id=f"prefix-{name}", role=_attr(role)))]),
    )


def _uplink_interface(name: str, role: str, uplink_switch: str, remote_interface: str) -> dict:
    return {
        "__typename": "InterfacePhysical",
        "id": f"if-{name}-{uplink_switch}-{remote_interface}",
        "name": {"value": name},
        "role": {"value": role},
        "connector": {
            "node": {
                "__typename": "NetworkLink",
                "id": f"link-{name}-{uplink_switch}-{remote_interface}",
                "connected_endpoints": {
                    "edges": [
                        _edge(
                            {
                                "__typename": "DcimInterface",
                                "id": f"remote-{uplink_switch}-{remote_interface}",
                                "name": {"value": remote_interface},
                                "device": {
                                    "node": {
                                        "__typename": "DcimDevice",
                                        "id": f"dev-{uplink_switch}",
                                        "name": {"value": uplink_switch},
                                    }
                                },
                            }
                        )
                    ]
                },
            }
        },
    }


def _fabric_device(name: str, role: str, node_id: int | None, uplinks: list[tuple[str, str, str]]) -> dict:
    uplink_role = "super_spine" if role == "spine" else "spine"
    return {
        "__typename": "DcimDevice",
        "id": f"dev-{name}",
        "name": {"value": name},
        "role": {"value": role},
        "node_id": {"value": node_id} if node_id is not None else None,
        "interfaces": {
            "edges": [
                _edge(_uplink_interface(interface_name, uplink_role, uplink_switch, remote_interface))
                for interface_name, uplink_switch, remote_interface in uplinks
            ]
        },
    }


def _fabric_with_devices(devices: list[dict]) -> dict:
    return {
        "__typename": "NetworkFabric",
        "id": "fabric-l3ls-multipod-a",
        "name": {"value": "Fabric-L3LS-MultiPod-A"},
        "devices": {"edges": [_edge(device) for device in devices]},
    }


def _make_generator(prefix_map: dict[int, str | None]) -> GenerateAVDDeviceHostvar:
    """Build a generator with `_extract_pool_prefix` stubbed.

    `prefix_map` maps a pool-ref sentinel's id() to the prefix it resolves to
    (or None to simulate an unset or linked-but-empty pool).
    """
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)

    async def fake_extract(pool_ref: object, pool_kind: str) -> str | None:
        return prefix_map.get(id(pool_ref)) if pool_ref is not None else None

    async def fake_default(role: ResourceRole) -> str:
        return {
            ResourceRole.MLAG: "169.254.0.0/31",
            ResourceRole.MLAG_PEERING: "192.0.0.0/31",
        }[role]

    gen._extract_pool_prefix = fake_extract  # type: ignore[method-assign]
    gen._ensure_default_mlag_pool_prefix = fake_default  # type: ignore[method-assign]
    return gen


async def test_extract_l3ls_pools_returns_all_pools() -> None:
    """Only pyAVD pools still required by hostvars resolve from the data model."""
    uplink, vtep, loopback, mlag_peer, mlag_l3 = (object() for _ in range(5))
    fabric = SimpleNamespace(
        name=_attr("Fabric-L3LS-MultiPod-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback
    )
    pod = SimpleNamespace(mlag_peer_pool=mlag_peer, mlag_l3_pool=mlag_l3)
    gen = _make_generator(
        {
            id(uplink): "10.1.0.0/16",
            id(vtep): "10.2.0.0/24",
            id(loopback): "10.3.0.0/24",
            id(mlag_peer): "10.4.0.0/24",
            id(mlag_l3): "10.5.0.0/24",
        }
    )

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["uplink_ipv4_pool"] == "10.1.0.0/16"
    assert pools["mlag_peer_ipv4_pool"] == "10.4.0.0/24"
    assert pools["mlag_peer_l3_ipv4_pool"] == "10.5.0.0/24"
    assert "vtep_loopback_ipv4_pool" not in pools
    assert "loopback_ipv4_pool" not in pools


async def test_extract_l3ls_pools_prefers_fabric_ip_pools_for_uplink_pool() -> None:
    legacy_uplink, mlag_peer, mlag_l3 = (object() for _ in range(3))
    collection_uplink = _pool_node("collection-uplink", "fabric_point_to_point")
    fabric = SimpleNamespace(
        name=_attr("Fabric-A"),
        uplink_pool=legacy_uplink,
        fabric_ip_pools=SimpleNamespace(edges=[SimpleNamespace(node=collection_uplink)]),
    )
    pod = SimpleNamespace(mlag_peer_pool=mlag_peer, mlag_l3_pool=mlag_l3)
    gen = _make_generator(
        {
            id(collection_uplink): "10.100.0.0/24",
            id(legacy_uplink): "10.1.0.0/16",
            id(mlag_peer): "10.4.0.0/24",
            id(mlag_l3): "10.5.0.0/24",
        }
    )

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["uplink_ipv4_pool"] == "10.100.0.0/24"


async def test_extract_l3ls_pools_prefers_pod_ip_pools_for_uplink_pool() -> None:
    legacy_uplink, mlag_peer, mlag_l3 = (object() for _ in range(3))
    fabric_uplink = _pool_node("fabric-uplink", "fabric_point_to_point")
    pod_uplink = _pool_node("pod-uplink", "fabric_point_to_point")
    fabric = SimpleNamespace(
        name=_attr("Fabric-A"),
        uplink_pool=legacy_uplink,
        fabric_ip_pools=SimpleNamespace(edges=[SimpleNamespace(node=fabric_uplink)]),
    )
    pod = SimpleNamespace(
        pod_ip_pools=SimpleNamespace(edges=[SimpleNamespace(node=pod_uplink)]),
        mlag_peer_pool=mlag_peer,
        mlag_l3_pool=mlag_l3,
    )
    gen = _make_generator(
        {
            id(pod_uplink): "10.200.0.0/24",
            id(fabric_uplink): "10.100.0.0/24",
            id(legacy_uplink): "10.1.0.0/16",
            id(mlag_peer): "10.4.0.0/24",
            id(mlag_l3): "10.5.0.0/24",
        }
    )

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["uplink_ipv4_pool"] == "10.200.0.0/24"


async def test_extract_l3ls_pools_no_hardcoded_fallback() -> None:
    """The removed literals never reappear as fallbacks."""
    uplink, vtep, loopback = (object() for _ in range(3))
    fabric = SimpleNamespace(
        name=_attr("Fabric-L3LS-MultiPod-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback
    )
    pod = SimpleNamespace(
        mlag_peer_pool=None,
        mlag_l3_pool=None,
        racks=SimpleNamespace(edges=[SimpleNamespace(node=SimpleNamespace(mlag=_attr(True)))]),
    )
    gen = _make_generator({id(uplink): "172.16.0.0/16", id(vtep): "172.17.0.0/24", id(loopback): "172.18.0.0/24"})

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert "10.250.0.0/16" not in pools.values()
    assert "10.251.0.0/24" not in pools.values()
    assert "10.255.0.0/24" not in pools.values()


@pytest.mark.parametrize("missing", ["uplink_pool"])
async def test_extract_l3ls_pools_raises_when_required_pool_empty(missing: str) -> None:
    """A linked-but-empty (or unset) mandatory pool fails loudly, naming the pool."""
    refs = {"uplink_pool": object(), "vtep_pool": object(), "loopback_pool": object()}
    fabric = SimpleNamespace(name=_attr("Fabric-L3LS-MultiPod-A"), **refs)
    pod = SimpleNamespace(
        mlag_peer_pool=None,
        mlag_l3_pool=None,
        racks=SimpleNamespace(edges=[SimpleNamespace(node=SimpleNamespace(mlag=_attr(True)))]),
    )
    prefix_map = {id(ref): "10.0.0.0/24" for ref in refs.values()}
    prefix_map[id(refs[missing])] = None  # simulate empty/unset pool

    gen = _make_generator(prefix_map)

    with pytest.raises(ValueError, match=f"Fabric 'Fabric-L3LS-MultiPod-A'.*{missing}"):
        await gen._extract_l3ls_pools(fabric, pod)


async def test_extract_l3ls_pools_uses_default_mlag_pools_when_missing() -> None:
    """Missing MLAG pools resolve to deterministic default /31 pool intents."""
    uplink, vtep, loopback = (object() for _ in range(3))
    fabric = SimpleNamespace(
        name=_attr("Fabric-L3LS-MultiPod-A"),
        underlay_routing_protocol=_attr("ebgp"),
        uplink_pool=uplink,
        vtep_pool=vtep,
        loopback_pool=loopback,
    )
    pod = SimpleNamespace(
        mlag_peer_pool=None,
        mlag_l3_pool=None,
        racks=SimpleNamespace(edges=[SimpleNamespace(node=SimpleNamespace(mlag=_attr(True)))]),
    )
    gen = _make_generator({id(uplink): "10.1.0.0/16", id(vtep): "10.2.0.0/24", id(loopback): "10.3.0.0/24"})

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["mlag_peer_ipv4_pool"] == "169.254.0.0/31"
    assert pools["mlag_peer_l3_ipv4_pool"] == "192.0.0.0/31"


async def test_extract_l3ls_pools_does_not_create_mlag_defaults_when_not_required() -> None:
    uplink = object()
    fabric = SimpleNamespace(
        name=_attr("Fabric-A"),
        underlay_routing_protocol=_attr("ebgp"),
        uplink_pool=uplink,
    )
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l3_pool=None, racks=SimpleNamespace(edges=[]))
    gen = _make_generator({id(uplink): "10.1.0.0/16"})
    gen._ensure_default_mlag_pool_prefix = AsyncMock(side_effect=AssertionError("MLAG default not required"))  # type: ignore[method-assign]

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["mlag_peer_ipv4_pool"] is None
    assert pools["mlag_peer_l3_ipv4_pool"] is None


async def test_extract_l3ls_pools_creates_required_mlag_defaults_for_mlag_rack() -> None:
    uplink = object()
    fabric = SimpleNamespace(
        name=_attr("Fabric-A"),
        underlay_routing_protocol=_attr("ebgp"),
        uplink_pool=uplink,
    )
    pod = SimpleNamespace(
        mlag_peer_pool=None,
        mlag_l3_pool=None,
        racks=SimpleNamespace(edges=[SimpleNamespace(node=SimpleNamespace(mlag=_attr(True)))]),
    )
    gen = _make_generator({id(uplink): "10.1.0.0/16"})

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["mlag_peer_ipv4_pool"] == "169.254.0.0/31"
    assert pools["mlag_peer_l3_ipv4_pool"] == "192.0.0.0/31"


async def test_extract_l3ls_pools_uses_fabric_supernet_fallback_for_missing_uplink_pool() -> None:
    supernet_pool = _pool_node("supernet", "fabric_supernet")
    fallback_pool = object()
    fabric = SimpleNamespace(
        name=_attr("Fabric-A"),
        underlay_routing_protocol=_attr("ebgp"),
        uplink_pool=None,
        fabric_ip_pools=SimpleNamespace(edges=[SimpleNamespace(node=supernet_pool)]),
    )
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l3_pool=None, racks=SimpleNamespace(edges=[]))
    gen = _make_generator({id(fallback_pool): "10.0.0.0/24"})
    gen._ensure_fabric_supernet_fallback_pool = AsyncMock(return_value=fallback_pool)  # type: ignore[method-assign]

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["uplink_ipv4_pool"] == "10.0.0.0/24"
    gen._ensure_fabric_supernet_fallback_pool.assert_awaited_once_with(  # type: ignore[attr-defined]
        fabric=fabric,
        role=ResourceRole.FABRIC_POINT_TO_POINT,
        fabric_pool_refs={ResourceRole.FABRIC_SUPERNET: supernet_pool},
    )


async def test_extract_l3ls_pools_uses_generated_mlag_l3_pool_alias() -> None:
    """The generated Pydantic field name resolves the optional MLAG L3 pool."""
    uplink, vtep, loopback, mlag_l3 = (object() for _ in range(4))
    fabric = SimpleNamespace(
        name=_attr("Fabric-L3LS-MultiPod-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback
    )
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l_3_pool=mlag_l3)
    gen = _make_generator(
        {
            id(uplink): "10.1.0.0/16",
            id(vtep): "10.2.0.0/24",
            id(loopback): "10.3.0.0/24",
            id(mlag_l3): "10.5.0.0/24",
        }
    )

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["mlag_peer_l3_ipv4_pool"] == "10.5.0.0/24"


async def test_default_mlag_pool_creation_uses_stable_pool_name_and_prefix() -> None:
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)
    prefix = SimpleNamespace(id="prefix-mlag", save=AsyncMock())
    pool = SimpleNamespace(save=AsyncMock())
    gen.client = MagicMock()
    gen.client.filters = AsyncMock(return_value=[])
    gen.client.create = AsyncMock(side_effect=[prefix, pool])

    result = await gen._ensure_default_mlag_pool_prefix(ResourceRole.MLAG)

    assert result == "169.254.0.0/31"
    gen.client.create.assert_any_await(
        kind="IpamPrefix",
        prefix="169.254.0.0/31",
        role="mlag",
        ip_namespace={"hfid": ["default"]},
    )
    gen.client.create.assert_any_await(
        kind="CoreIPAddressPool",
        name="MLAG-Peer-Subnet",
        default_address_type="IpamIPAddress",
        default_prefix_length=31,
        ip_namespace={"hfid": ["default"]},
        resources=[{"id": "prefix-mlag"}],
    )
    prefix.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    pool.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)


async def test_default_mlag_pool_reuses_existing_pool_by_stable_name() -> None:
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)
    existing_pool = SimpleNamespace(id="existing-mlag")
    gen.client = MagicMock()
    gen.client.filters = AsyncMock(return_value=[existing_pool])
    gen.client.create = AsyncMock()

    async def fake_extract(pool_ref: object, pool_kind: str) -> str | None:
        assert pool_ref is existing_pool
        assert pool_kind == "CoreIPAddressPool"
        return "169.254.0.0/31"

    gen._extract_pool_prefix = fake_extract  # type: ignore[method-assign]

    result = await gen._ensure_default_mlag_pool_prefix(ResourceRole.MLAG)

    assert result == "169.254.0.0/31"
    gen.client.create.assert_not_awaited()


def test_derive_uplink_pool_reservation_uses_widest_fabric_fanout() -> None:
    fabric = _fabric_with_devices(
        [
            _fabric_device("super-spine1", "super_spine", 1, []),
            _fabric_device(
                "spine1",
                "spine",
                2,
                [("Ethernet1", "super-spine1", "Ethernet1"), ("Ethernet2", "super-spine2", "Ethernet1")],
            ),
            _fabric_device(
                "leaf1",
                "leaf",
                3,
                [("Ethernet1", "spine1", "Ethernet3"), ("Ethernet2", "spine2", "Ethernet3")],
            ),
            _fabric_device(
                "leaf2",
                "leaf",
                4,
                [
                    ("Ethernet1", "spine1", "Ethernet4"),
                    ("Ethernet2", "spine2", "Ethernet4"),
                    ("Ethernet3", "spine3", "Ethernet4"),
                    ("Ethernet4", "spine4", "Ethernet4"),
                ],
            ),
        ]
    )

    assert GenerateAVDDeviceHostvar._derive_uplink_pool_reservation(fabric, fabric_underlay="ebgp") == {
        "max_uplink_switches": 4,
        "max_parallel_uplinks": None,
    }


def test_derive_uplink_pool_reservation_detects_parallel_uplinks() -> None:
    fabric = _fabric_with_devices(
        [
            _fabric_device(
                "leaf1",
                "leaf",
                3,
                [
                    ("Ethernet1", "spine1", "Ethernet3"),
                    ("Ethernet2", "spine1", "Ethernet4"),
                    ("Ethernet3", "spine2", "Ethernet3"),
                    ("Ethernet4", "spine2", "Ethernet4"),
                ],
            )
        ]
    )

    assert GenerateAVDDeviceHostvar._derive_uplink_pool_reservation(fabric, fabric_underlay="ebgp") == {
        "max_uplink_switches": 2,
        "max_parallel_uplinks": 2,
    }


def test_derive_uplink_pool_reservation_ignores_no_uplink_devices() -> None:
    fabric = _fabric_with_devices([_fabric_device("super-spine1", "super_spine", None, [])])

    assert GenerateAVDDeviceHostvar._derive_uplink_pool_reservation(fabric, fabric_underlay="ebgp") is None


def test_derive_uplink_pool_reservation_requires_node_id() -> None:
    fabric = _fabric_with_devices([_fabric_device("leaf1", "leaf", None, [("Ethernet1", "spine1", "Ethernet3")])])

    with pytest.raises(ValueError, match=r"leaf1.*no node_id"):
        GenerateAVDDeviceHostvar._derive_uplink_pool_reservation(fabric, fabric_underlay="ebgp")


def test_derive_uplink_pool_reservation_rejects_duplicate_node_ids() -> None:
    fabric = _fabric_with_devices(
        [
            _fabric_device("leaf1", "leaf", 3, [("Ethernet1", "spine1", "Ethernet3")]),
            _fabric_device("leaf2", "leaf", 3, [("Ethernet1", "spine1", "Ethernet4")]),
        ]
    )

    with pytest.raises(ValueError, match=r"leaf1.*leaf2.*node_id 3"):
        GenerateAVDDeviceHostvar._derive_uplink_pool_reservation(fabric, fabric_underlay="ebgp")
