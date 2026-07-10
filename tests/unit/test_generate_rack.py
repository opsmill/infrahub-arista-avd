from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.generate_rack import RackGenerator, is_mlag_enabled


def _leaf(leaf_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=leaf_id, name=SimpleNamespace(value=name))


def _make_generator() -> RackGenerator:
    gen = RackGenerator.__new__(RackGenerator)
    gen.client = MagicMock()
    gen.client.create = AsyncMock()
    gen.logger = MagicMock()
    gen.pod_id = "pod-1"
    gen.rack_name = "DC1_BORDER"
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
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="mlag-DC1_BORDER",
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )
    mlag_domain.save.assert_awaited_once_with(allow_upsert=True)
