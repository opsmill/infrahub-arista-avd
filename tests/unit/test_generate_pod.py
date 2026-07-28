"""Unit tests for the pod generator."""

from __future__ import annotations

import re
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import generators.generate_pod as generate_pod_module
from generators.generate_pod import PodGenerator


def _make_generator() -> PodGenerator:
    gen = PodGenerator.__new__(PodGenerator)
    gen.client = MagicMock()
    gen.logger = MagicMock()
    gen.pod_id = "pod-1"
    gen.calculate_checksum = MagicMock(return_value="new-checksum")  # type: ignore[method-assign]
    return gen


@pytest.mark.asyncio
async def test_update_checksum_schedules_unchanged_racks(monkeypatch: pytest.MonkeyPatch) -> None:
    gen = _make_generator()
    unchanged_rack = MagicMock()
    unchanged_rack.id = "rack-1"
    unchanged_rack.name.value = "rack-1"
    unchanged_rack.checksum.value = "new-checksum"
    unchanged_rack.save = AsyncMock()
    gen.client.filters = AsyncMock(return_value=[unchanged_rack])
    trigger_rack_generation = AsyncMock()
    monkeypatch.setattr(generate_pod_module, "trigger_rack_generation", trigger_rack_generation)

    await gen.update_checksum()

    unchanged_rack.save.assert_not_awaited()
    trigger_rack_generation.assert_awaited_once_with(gen.client, node_ids=["rack-1"])


@pytest.mark.asyncio
async def test_update_checksum_changed_racks_rely_on_checksum_trigger(monkeypatch: pytest.MonkeyPatch) -> None:
    gen = _make_generator()
    changed_rack = MagicMock()
    changed_rack.id = "rack-1"
    changed_rack.name.value = "rack-1"
    changed_rack.checksum.value = "old-checksum"
    changed_rack.save = AsyncMock()
    gen.client.filters = AsyncMock(return_value=[changed_rack])
    trigger_rack_generation = AsyncMock()
    monkeypatch.setattr(generate_pod_module, "trigger_rack_generation", trigger_rack_generation)

    await gen.update_checksum()

    changed_rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    trigger_rack_generation.assert_not_awaited()


# --- l2spine MLAG pair creation (feature 002) ---------------------------------


def _iface(name: str, role: str) -> SimpleNamespace:
    # Mirror the schema's computed `index` attribute (zero-padded interface number).
    match = re.search(r"\d+", name)
    index_value = f"{int(match.group()):03d}" if match else "000"
    return SimpleNamespace(
        name=SimpleNamespace(value=name),
        role=SimpleNamespace(value=role),
        index=SimpleNamespace(value=index_value),
        save=AsyncMock(),
    )


def _spine(device_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=SimpleNamespace(value=name))


def _make_mlag_generator() -> PodGenerator:
    gen = PodGenerator.__new__(PodGenerator)
    gen.client = AsyncMock()
    return gen


def _spine_interfaces() -> list[SimpleNamespace]:
    # arista-7050cx3-32c spine: Ethernet1-27 are leaf-facing (role leaf, used),
    # Ethernet28-32 are super-spine-facing (role super_spine, free in L2LS).
    return [
        _iface("Ethernet1", "leaf"),
        _iface("Ethernet27", "leaf"),
        _iface("Ethernet31", "super_spine"),
        _iface("Ethernet32", "super_spine"),
    ]


@pytest.mark.asyncio
async def test_create_spine_mlag_pair_carves_super_spine_ports() -> None:
    """An l2spine pod forms one MLAG domain and carves the peer-link from the
    highest free super-spine-facing ports (never the leaf-facing downlinks)."""
    gen = _make_mlag_generator()
    gen.spine_role = "l2spine"
    gen.pod_id = "pod-1"
    gen.pod_name = "l2ls-pod1"
    spine_a = _spine("spine-a", "spine-l2ls-pod1-1")
    spine_b = _spine("spine-b", "spine-l2ls-pod1-2")
    gen.spine_switches = [spine_a, spine_b]

    ifaces_by_device = {"spine-a": _spine_interfaces(), "spine-b": _spine_interfaces()}

    async def filters_side_effect(*_args: object, **kwargs: object) -> list[SimpleNamespace]:
        device_ids = kwargs.get("device__ids") or [None]
        return ifaces_by_device[device_ids[0]]

    gen.client.filters = AsyncMock(side_effect=filters_side_effect)
    gen.client.create = AsyncMock(return_value=SimpleNamespace(save=AsyncMock()))

    await gen.create_spine_mlag_pair()

    # One MLAG domain created for the spine pair.
    gen.client.create.assert_awaited_once()
    _, kwargs = gen.client.create.call_args
    assert kwargs["domain_id"] == "l2ls-pod1-spine"
    assert kwargs["peers"] == [{"id": "spine-a"}, {"id": "spine-b"}]
    assert kwargs["pod"] == {"id": "pod-1"}
    assert "asn" not in kwargs  # pure Layer-2: no BGP ASN on the domain

    # Highest two super-spine ports on each spine converted to the peer-link.
    for ifaces in ifaces_by_device.values():
        converted = {i.name.value for i in ifaces if i.role.value == "mlag_peer"}
        assert converted == {"Ethernet31", "Ethernet32"}
        for i in ifaces:
            if i.name.value in {"Ethernet31", "Ethernet32"}:
                i.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
            else:
                i.save.assert_not_awaited()  # leaf downlinks untouched


@pytest.mark.asyncio
async def test_create_spine_mlag_pair_skips_routed_spine() -> None:
    """A routed L3LS spine tier is never MLAG'd by this path."""
    gen = _make_mlag_generator()
    gen.spine_role = "spine"
    gen.pod_id = "pod-1"
    gen.pod_name = "pod1"
    gen.spine_switches = [_spine("s1", "spine-1"), _spine("s2", "spine-2")]
    gen.client.create = AsyncMock()

    await gen.create_spine_mlag_pair()

    gen.client.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_spine_mlag_pair_skips_single_spine() -> None:
    """A single spine cannot form an MLAG pair."""
    gen = _make_mlag_generator()
    gen.spine_role = "l2spine"
    gen.pod_id = "pod-1"
    gen.pod_name = "l2ls-pod1"
    gen.spine_switches = [_spine("s1", "spine-1")]
    gen.client.create = AsyncMock()

    await gen.create_spine_mlag_pair()

    gen.client.create.assert_not_awaited()
