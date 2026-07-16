from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.generate_rack import RackGenerator, is_mlag_enabled
from solution_arista_avd.generator import trigger_hostvar_generation

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


def _leaf(leaf_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=leaf_id,
        name=SimpleNamespace(value=name),
        save=AsyncMock(),
    )


def _pool(start: int = 65100, end: int = 65199) -> SimpleNamespace:
    return SimpleNamespace(start_range=SimpleNamespace(value=start), end_range=SimpleNamespace(value=end))


def _domain(domain_id: str, *, domain_uuid: str | None = None, asn_node_id: str | None = None) -> SimpleNamespace:
    """Mock MlagDomain whose ``asn`` relationship points at the given RoutingAsn node id."""
    return SimpleNamespace(
        id=domain_uuid or domain_id,
        domain_id=SimpleNamespace(value=domain_id),
        asn=SimpleNamespace(id=asn_node_id),
    )


def _named_device(device_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=SimpleNamespace(value=name))


def _filters_side_effect(
    *,
    domains: list[SimpleNamespace] | None = None,
) -> Callable[..., Coroutine[Any, Any, list[SimpleNamespace]]]:
    async def side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))

        if kind_name == "MlagDomain" and kwargs.get("domain_id__value") == "DC1_BORDER":
            return domains or []
        return []

    return side_effect


def _make_generator() -> RackGenerator:
    gen = RackGenerator.__new__(RackGenerator)
    gen.client = MagicMock()
    gen.client.create = AsyncMock()
    gen.client.get = AsyncMock()
    gen.client.filters = AsyncMock(side_effect=_filters_side_effect())
    gen.client.execute_graphql = AsyncMock()
    gen.logger = MagicMock()
    gen.fabric = SimpleNamespace(id="fabric-1")
    gen.pod_id = "pod-1"
    gen.rack_name = "DC1_BORDER"
    gen.rack_amount_of_leafs = 2
    gen.rack_mlag = True
    gen.rack_mlag_enabled = True
    gen.rack_index = 1
    gen.rack_id = "rack-1"
    gen.rack_leaf_switch_template = "leaf-template"
    gen.pod_name = "pod-a"
    gen.loopback_pool = object()
    gen.asn_pool = _pool()
    gen.node_id_pool = object()
    gen.mgmt_pool = object()
    gen.leaf_switches = [_leaf("leaf-a", "leaf-a"), _leaf("leaf-b", "leaf-b")]
    gen.l2leaf_switches = []
    gen.spine_switches = [_named_device("spine-a", "spine-a"), _named_device("spine-b", "spine-b")]
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
    gen.rack_mlag_enabled = False

    await gen.create_mlag_pairs()

    gen.client.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_mlag_pairs_allocates_shared_asn_node() -> None:
    gen = _make_generator()
    gen.rack_mlag = True
    gen.allocate_routing_asn = AsyncMock(return_value=SimpleNamespace(id="asn-node-1"))  # type: ignore[method-assign]
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    # A single shared RoutingAsn is allocated from the fabric pool and linked to the domain.
    gen.allocate_routing_asn.assert_awaited_once_with(gen.asn_pool, gen.fabric.id)
    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="DC1_BORDER",
        asn={"id": "asn-node-1"},
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )
    mlag_domain.save.assert_awaited_once_with(allow_upsert=True)
    # Both leaves are linked to that same shared ASN node via a targeted mutation.
    assert gen.client.execute_graphql.await_count == 2
    linked_asn_ids = {call.kwargs["variables"]["asn_id"] for call in gen.client.execute_graphql.await_args_list}
    assert linked_asn_ids == {"asn-node-1"}


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
async def test_create_mlag_pairs_reuses_existing_domain_asn() -> None:
    """A re-run must reuse the pair's existing shared RoutingAsn, not allocate a new one (FR-007)."""
    gen = _make_generator()
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(domains=[_domain("DC1_BORDER", asn_node_id="asn-existing")])
    )
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    gen.allocate_routing_asn.assert_not_awaited()
    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="DC1_BORDER",
        asn={"id": "asn-existing"},
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )


@pytest.mark.asyncio
async def test_get_or_allocate_mlag_asn_allocates_when_no_existing_domain() -> None:
    gen = _make_generator()
    gen.allocate_routing_asn = AsyncMock(return_value=SimpleNamespace(id="asn-new"))  # type: ignore[method-assign]

    asn_id = await gen._get_or_allocate_mlag_asn("DC1_BORDER")

    assert asn_id == "asn-new"
    gen.allocate_routing_asn.assert_awaited_once_with(gen.asn_pool, gen.fabric.id)


@pytest.mark.asyncio
async def test_get_or_allocate_mlag_asn_reuses_existing_domain_link() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(domains=[_domain("DC1_BORDER", asn_node_id="asn-existing")])
    )
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]

    asn_id = await gen._get_or_allocate_mlag_asn("DC1_BORDER")

    assert asn_id == "asn-existing"
    gen.allocate_routing_asn.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_stale_mlag_domains_only_deletes_current_rack_domains() -> None:
    gen = _make_generator()
    stale_primary = _domain("DC1_BORDER")
    stale_pair = _domain("DC1_BORDER-2")
    other_domain = _domain("DC1_OTHER")
    for domain in [stale_primary, stale_pair, other_domain]:
        domain.delete = AsyncMock()
    gen.client.filters = AsyncMock(return_value=[stale_primary, stale_pair, other_domain])

    await gen.delete_stale_mlag_domains()

    stale_primary.delete.assert_awaited_once()
    stale_pair.delete.assert_awaited_once()
    other_domain.delete.assert_not_awaited()


def test_hostvar_target_device_ids_deduplicates_rack_and_spine_devices() -> None:
    gen = _make_generator()
    gen.leaf_switches = [_named_device("leaf-a", "leaf-a"), _named_device("leaf-b", "leaf-b")]
    gen.l2leaf_switches = [_named_device("l2leaf-a", "l2leaf-a")]
    gen.spine_switches = [_named_device("spine-a", "spine-a"), _named_device("leaf-a", "leaf-a")]

    assert gen.hostvar_target_device_ids() == ["leaf-a", "leaf-b", "l2leaf-a", "spine-a"]


@pytest.mark.asyncio
async def test_invalidate_hostvars_deletes_target_hostvar_files() -> None:
    gen = _make_generator()
    hostvar_file = SimpleNamespace(delete=AsyncMock())
    hostvar_rel = SimpleNamespace(id="hostvar-file-1", fetch=AsyncMock(), peer=hostvar_file)
    artifact = SimpleNamespace(hostvar_file=hostvar_rel)

    async def filters_side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))
        if kind_name == "DcimDevice":
            return [_named_device("leaf-a", "leaf-a")]
        if kind_name == "AvdArtifact":
            return [artifact]
        return []

    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    await gen.invalidate_hostvars(["leaf-a"])

    hostvar_rel.fetch.assert_awaited_once()
    hostvar_file.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_limits_nodes() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock()

    await trigger_hostvar_generation(client, node_ids=["leaf-a", "spine-a"])

    client.execute_graphql.assert_awaited_once()
    assert client.execute_graphql.await_args.kwargs["variables"] == {
        "id": "generator-1",
        "nodes": ["leaf-a", "spine-a"],
    }
