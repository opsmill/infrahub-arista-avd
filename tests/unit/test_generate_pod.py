from __future__ import annotations

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
