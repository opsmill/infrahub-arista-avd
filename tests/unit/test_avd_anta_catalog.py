"""Unit tests for the AVD ANTA catalog transform."""

import json
from unittest.mock import AsyncMock

import pytest
import yaml

from transforms.avd_anta_catalog import AvdAntaCatalogTransform

FABRIC_ID = "fabric-1"


def _fabric_parent(anta_enabled: bool | None, name: str = "Fabric-A") -> dict:
    return {
        "node": {
            "__typename": "NetworkFabric",
            "id": FABRIC_ID,
            "name": {"value": name},
            "anta_enabled": {"value": anta_enabled},
        }
    }


def _device(hostname: str, dev_id: str, *, with_sc: bool = True, fabric_id: str = FABRIC_ID) -> dict:
    node: dict = {
        "id": dev_id,
        "name": {"value": hostname},
        "pod": {"node": {"id": f"pod-{dev_id}", "parent": {"node": {"id": fabric_id}}}},
        "avd_artifact": None,
    }
    if with_sc:
        node["avd_artifact"] = {
            "node": {"id": f"art-{dev_id}", "structured_config_file": {"node": {"id": f"scf-{dev_id}"}}},
        }
    return node


def _data(*, anta_enabled: bool | None, target_found: bool = True, target_has_sc: bool = True) -> dict:
    target_edges = []
    if target_found:
        target_edges = [
            {
                "node": {
                    "id": "dev-target",
                    "name": {"value": "leaf1"},
                    "pod": {"node": {"id": "pod-t", "parent": _fabric_parent(anta_enabled)}},
                }
            }
        ]
    return {
        "target": {"edges": target_edges},
        "DcimDevice": {"edges": [{"node": _device("leaf1", "dev-target", with_sc=target_has_sc)}]},
    }


def _transform(structured_config: dict | None = None) -> AvdAntaCatalogTransform:
    """Build a transform with a mocked client that returns the given structured config."""
    t = AvdAntaCatalogTransform.__new__(AvdAntaCatalogTransform)
    sc_file = AsyncMock()
    sc_file.download_file = AsyncMock(return_value=json.dumps(structured_config or {"hostname": "leaf1"}))
    client = AsyncMock()
    client.get = AsyncMock(return_value=sc_file)
    t._init_client = client  # `client` is a read-only property backed by _init_client
    return t


async def test_disabled_fabric_returns_marker() -> None:
    result = await _transform().transform(_data(anta_enabled=False))
    assert result.startswith("# ANTA disabled for fabric Fabric-A")


async def test_flag_absent_treated_as_disabled() -> None:
    result = await _transform().transform(_data(anta_enabled=None))
    assert result.startswith("# ANTA disabled")


async def test_device_not_found_returns_marker() -> None:
    result = await _transform().transform(_data(anta_enabled=True, target_found=False))
    assert result.startswith("# ANTA catalog: device not found")


async def test_missing_structured_config_returns_marker() -> None:
    result = await _transform().transform(_data(anta_enabled=True, target_has_sc=False))
    assert result.startswith("# No structured config for leaf1")


async def test_enabled_produces_valid_yaml_catalog() -> None:
    result = await _transform().transform(_data(anta_enabled=True))
    assert not result.startswith("#")
    parsed = yaml.safe_load(result)
    assert isinstance(parsed, dict) and parsed  # non-empty ANTA catalog mapping


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
