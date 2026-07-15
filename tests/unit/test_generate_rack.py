from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.generate_rack import RackGenerator, is_mlag_enabled


def _leaf(leaf_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=leaf_id,
        name=SimpleNamespace(value=name),
        bgp_asn=SimpleNamespace(value=None),
        save=AsyncMock(),
    )


def _make_generator() -> RackGenerator:
    gen = RackGenerator.__new__(RackGenerator)
    gen.client = MagicMock()
    gen.client.create = AsyncMock()
    gen.client.get = AsyncMock(return_value=SimpleNamespace(bgp_asn=SimpleNamespace(value=65100)))
    gen.logger = MagicMock()
    gen.pod_id = "pod-1"
    gen.rack_name = "DC1_BORDER"
    gen.rack_amount_of_leafs = 2
    gen.rack_index = 1
    gen.rack_id = "rack-1"
    gen.rack_leaf_switch_template = "leaf-template"
    gen.pod_name = "pod-a"
    gen.loopback_pool = object()
    gen.asn_pool = object()
    gen.node_id_pool = object()
    gen.mgmt_pool = object()
    gen.leaf_switches = [_leaf("leaf-a", "leaf-a"), _leaf("leaf-b", "leaf-b")]
    return gen


@pytest.mark.parametrize("value", [False, "false", "False", "0", "no", "off"])
def test_is_mlag_enabled_handles_false_values(value: object) -> None:
    assert is_mlag_enabled(value) is False


@pytest.mark.parametrize("value", [None, True, "true", "1", "yes", "on"])
def test_is_mlag_enabled_defaults_to_enabled(value: object) -> None:
    assert is_mlag_enabled(value) is True


@pytest.mark.asyncio
async def test_create_mlag_pairs_skips_when_rack_mlag_false() -> None:
    gen = _make_generator()
    gen.rack_mlag = False

    await gen.create_mlag_pairs()

    gen.client.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_mlag_pairs_defaults_to_enabled_for_two_leaf_racks() -> None:
    gen = _make_generator()
    gen.rack_mlag = True
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="DC1_BORDER",
        bgp_asn=gen.asn_pool,
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )
    mlag_domain.save.assert_awaited_once_with(allow_upsert=True)
    assert [leaf.bgp_asn.value for leaf in gen.leaf_switches] == [65100, 65100]


@pytest.mark.asyncio
async def test_mlag_enabled_leafs_do_not_allocate_device_asns() -> None:
    gen = _make_generator()
    gen.rack_mlag_enabled = True
    leaf1 = _leaf("leaf-1", "leaf-pod-a-1-1")
    leaf2 = _leaf("leaf-2", "leaf-pod-a-1-2")
    gen.create_avd_device = AsyncMock(side_effect=[leaf1, leaf2])  # type: ignore[method-assign]
    gen.leaf_switches = []

    await gen.create_leaf_switches()

    assert [call.kwargs["asn_pool"] for call in gen.create_avd_device.await_args_list] == [None, None]
    assert gen.leaf_switches == [leaf1, leaf2]


@pytest.mark.asyncio
async def test_mlag_disabled_leafs_allocate_device_asns() -> None:
    gen = _make_generator()
    gen.rack_mlag_enabled = False
    leaf1 = _leaf("leaf-1", "leaf-pod-a-1-1")
    leaf2 = _leaf("leaf-2", "leaf-pod-a-1-2")
    gen.create_avd_device = AsyncMock(side_effect=[leaf1, leaf2])  # type: ignore[method-assign]
    gen.leaf_switches = []

    await gen.create_leaf_switches()

    assert [call.kwargs["asn_pool"] for call in gen.create_avd_device.await_args_list] == [
        gen.asn_pool,
        gen.asn_pool,
    ]
