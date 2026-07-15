"""Unit tests for schema-driven IP pool extraction in the AVD hostvar generator.

These tests pin the behavior introduced when the hardcoded fallback prefixes
(10.250.0.0/16, 10.251.0.0/24, 10.255.0.0/24) were replaced by mandatory
fabric pool relationships: the three fabric pools must resolve from data, a
missing/empty one fails loudly, and the MLAG pools stay optional.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from generators.generate_avd_device_hostvar import GenerateAVDDeviceHostvar


def _attr(value: object) -> SimpleNamespace:
    """Mimic an Infrahub attribute node exposing `.value`."""
    return SimpleNamespace(value=value)


def _make_generator(prefix_map: dict[int, str | None]) -> GenerateAVDDeviceHostvar:
    """Build a generator with `_extract_pool_prefix` stubbed.

    `prefix_map` maps a pool-ref sentinel's id() to the prefix it resolves to
    (or None to simulate an unset or linked-but-empty pool).
    """
    gen = GenerateAVDDeviceHostvar.__new__(GenerateAVDDeviceHostvar)

    async def fake_extract(pool_ref: object, pool_kind: str) -> str | None:
        return prefix_map.get(id(pool_ref)) if pool_ref is not None else None

    gen._extract_pool_prefix = fake_extract  # type: ignore[method-assign]
    return gen


async def test_extract_l3ls_pools_returns_all_pools() -> None:
    """All five pyAVD pools resolve from the data model, including loopback."""
    uplink, vtep, loopback, mlag_peer, mlag_l3 = (object() for _ in range(5))
    fabric = SimpleNamespace(name=_attr("Fabric-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback)
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
    assert pools["vtep_loopback_ipv4_pool"] == "10.2.0.0/24"
    assert pools["loopback_ipv4_pool"] == "10.3.0.0/24"
    assert pools["mlag_peer_ipv4_pool"] == "10.4.0.0/24"
    assert pools["mlag_peer_l3_ipv4_pool"] == "10.5.0.0/24"


async def test_extract_l3ls_pools_no_hardcoded_fallback() -> None:
    """The removed literals never reappear as fallbacks."""
    uplink, vtep, loopback = (object() for _ in range(3))
    fabric = SimpleNamespace(name=_attr("Fabric-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback)
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l3_pool=None)
    gen = _make_generator({id(uplink): "172.16.0.0/16", id(vtep): "172.17.0.0/24", id(loopback): "172.18.0.0/24"})

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert "10.250.0.0/16" not in pools.values()
    assert "10.251.0.0/24" not in pools.values()
    assert "10.255.0.0/24" not in pools.values()


@pytest.mark.parametrize("missing", ["uplink_pool", "vtep_pool", "loopback_pool"])
async def test_extract_l3ls_pools_raises_when_required_pool_empty(missing: str) -> None:
    """A linked-but-empty (or unset) mandatory pool fails loudly, naming the pool."""
    refs = {"uplink_pool": object(), "vtep_pool": object(), "loopback_pool": object()}
    fabric = SimpleNamespace(name=_attr("Fabric-A"), **refs)
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l3_pool=None)
    prefix_map = {id(ref): "10.0.0.0/24" for ref in refs.values()}
    prefix_map[id(refs[missing])] = None  # simulate empty/unset pool

    gen = _make_generator(prefix_map)

    with pytest.raises(ValueError, match=f"Fabric 'Fabric-A'.*{missing}"):
        await gen._extract_l3ls_pools(fabric, pod)


async def test_extract_l3ls_pools_mlag_optional() -> None:
    """MLAG pools remain optional: absent pods yield None, not an error."""
    uplink, vtep, loopback = (object() for _ in range(3))
    fabric = SimpleNamespace(name=_attr("Fabric-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback)
    pod = SimpleNamespace(mlag_peer_pool=None, mlag_l3_pool=None)
    gen = _make_generator({id(uplink): "10.1.0.0/16", id(vtep): "10.2.0.0/24", id(loopback): "10.3.0.0/24"})

    pools = await gen._extract_l3ls_pools(fabric, pod)

    assert pools["mlag_peer_ipv4_pool"] is None
    assert pools["mlag_peer_l3_ipv4_pool"] is None
    assert pools["loopback_ipv4_pool"] == "10.3.0.0/24"


async def test_extract_l3ls_pools_uses_generated_mlag_l3_pool_alias() -> None:
    """The generated Pydantic field name resolves the optional MLAG L3 pool."""
    uplink, vtep, loopback, mlag_l3 = (object() for _ in range(4))
    fabric = SimpleNamespace(name=_attr("Fabric-A"), uplink_pool=uplink, vtep_pool=vtep, loopback_pool=loopback)
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
