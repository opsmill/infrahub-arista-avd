from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.generate_rack import RackGenerator, is_mlag_enabled

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


def _leaf(leaf_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=leaf_id,
        name=SimpleNamespace(value=name),
        bgp_asn=SimpleNamespace(value=None),
        save=AsyncMock(),
    )


def _pool(start: int = 65100, end: int = 65199) -> SimpleNamespace:
    return SimpleNamespace(start_range=SimpleNamespace(value=start), end_range=SimpleNamespace(value=end))


def _device(device_id: str, asn: int | None) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, bgp_asn=SimpleNamespace(value=asn))


def _domain(domain_id: str, *, domain_uuid: str | None = None, asn: int | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=domain_uuid or domain_id,
        domain_id=SimpleNamespace(value=domain_id),
        bgp_asn=SimpleNamespace(value=asn),
    )


def _filters_side_effect(
    *,
    desired_domains: list[SimpleNamespace] | None = None,
    legacy_domains: list[SimpleNamespace] | None = None,
    used_devices: list[SimpleNamespace] | None = None,
    used_domains: list[SimpleNamespace] | None = None,
) -> Callable[..., Coroutine[Any, Any, list[SimpleNamespace]]]:
    async def side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))

        if kind_name == "MlagDomain" and kwargs.get("domain_id__value") == "DC1_BORDER":
            return desired_domains or []
        if kind_name == "MlagDomain" and kwargs.get("domain_id__value") == "mlag-DC1_BORDER":
            return legacy_domains or []
        if kind_name == "NetworkPod":
            return [SimpleNamespace(id="pod-1")]
        if kind_name == "DcimDevice":
            return used_devices or []
        if kind_name == "MlagDomain" and "pod__ids" in kwargs:
            return used_domains or []
        return []

    return side_effect


def _make_generator() -> RackGenerator:
    gen = RackGenerator.__new__(RackGenerator)
    gen.client = MagicMock()
    gen.client.create = AsyncMock()
    gen.client.get = AsyncMock(return_value=SimpleNamespace(bgp_asn=SimpleNamespace(value=65100)))
    gen.client.filters = AsyncMock(side_effect=_filters_side_effect())
    gen.client.execute_graphql = AsyncMock()
    gen.logger = MagicMock()
    gen.fabric = SimpleNamespace(id="fabric-1")
    gen.pod_id = "pod-1"
    gen.rack_name = "DC1_BORDER"
    gen.rack_amount_of_leafs = 2
    gen.rack_index = 1
    gen.rack_id = "rack-1"
    gen.rack_leaf_switch_template = "leaf-template"
    gen.pod_name = "pod-a"
    gen.loopback_pool = object()
    gen.asn_pool = _pool()
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
        bgp_asn=65100,
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


@pytest.mark.asyncio
async def test_create_mlag_pairs_migrates_legacy_domain_and_reuses_peer_asn() -> None:
    gen = _make_generator()
    gen.leaf_switches[0].bgp_asn.value = 65114
    gen.leaf_switches[1].bgp_asn.value = 65116
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(legacy_domains=[_domain("mlag-DC1_BORDER", domain_uuid="legacy-id")])
    )
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain
    gen.client.get = AsyncMock(return_value=SimpleNamespace(bgp_asn=SimpleNamespace(value=65114)))

    await gen.create_mlag_pairs()

    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        id="legacy-id",
        domain_id="DC1_BORDER",
        bgp_asn=65114,
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )
    assert [leaf.bgp_asn.value for leaf in gen.leaf_switches] == [65114, 65114]


@pytest.mark.asyncio
async def test_get_or_allocate_mlag_domain_asn_skips_used_fabric_asns() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(
            used_devices=[_device("spine-1", 65100)],
            used_domains=[_domain("Rack-OTHER", asn=65101)],
        )
    )

    asn = await gen._get_or_allocate_mlag_domain_asn(
        domain_id="DC1_BORDER",
        existing_domains=[],
        leaf_a=gen.leaf_switches[0],
        leaf_b=gen.leaf_switches[1],
    )

    assert asn == 65102
