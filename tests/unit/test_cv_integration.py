from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from checks.cv_config_check import CVConfigValidationCheck
from checks.cv_config_check_query import CVConfigCheckQuery
from checks.cv_helpers import get_proposed_change_id, get_workspace_id

if TYPE_CHECKING:
    from pathlib import Path


def _cv_query() -> CVConfigCheckQuery:
    return CVConfigCheckQuery.model_validate(
        {
            "NetworkFabric": {"edges": [{"node": {"id": "fabric-1", "name": {"value": "Fabric-DC1"}}}]},
            "DcimDevice": {
                "edges": [
                    {
                        "node": {
                            "id": "leaf-1",
                            "name": {"value": "leaf-1"},
                            "serial": {"value": "SERIAL1"},
                            "pod": {
                                "node": {
                                    "id": "pod-1",
                                    "parent": {"node": {"__typename": "NetworkFabric", "id": "fabric-1"}},
                                }
                            },
                            "avd_artifact": {
                                "node": {"id": "artifact-1", "structured_config_file": {"node": {"id": "sc-1"}}}
                            },
                        }
                    },
                    {
                        "node": {
                            "id": "leaf-2",
                            "name": {"value": "leaf-2"},
                            "serial": {"value": None},
                            "pod": {
                                "node": {
                                    "id": "pod-1",
                                    "parent": {"node": {"__typename": "NetworkFabric", "id": "fabric-1"}},
                                }
                            },
                            "avd_artifact": {
                                "node": {"id": "artifact-2", "structured_config_file": {"node": {"id": "sc-2"}}}
                            },
                        }
                    },
                    {
                        "node": {
                            "id": "other",
                            "name": {"value": "other"},
                            "serial": {"value": "SERIAL2"},
                            "pod": {
                                "node": {
                                    "id": "pod-2",
                                    "parent": {"node": {"__typename": "NetworkFabric", "id": "fabric-2"}},
                                }
                            },
                            "avd_artifact": {
                                "node": {"id": "artifact-3", "structured_config_file": {"node": {"id": "sc-3"}}}
                            },
                        }
                    },
                    {
                        "node": {
                            "id": "server",
                            "name": {"value": "server"},
                            "serial": {"value": "SERIAL3"},
                            "pod": None,
                            "avd_artifact": None,
                        }
                    },
                    {
                        "node": {
                            "id": "leaf-no-config",
                            "name": {"value": "leaf-no-config"},
                            "serial": {"value": "SERIAL4"},
                            "pod": {
                                "node": {
                                    "id": "pod-1",
                                    "parent": {"node": {"__typename": "NetworkFabric", "id": "fabric-1"}},
                                }
                            },
                            "avd_artifact": {"node": {"id": "artifact-4", "structured_config_file": None}},
                        }
                    },
                ]
            },
        }
    )


def test_cv_filter_limits_devices_to_target_fabric_with_structured_configs() -> None:
    parsed = _cv_query()
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)

    devices = check._filter_devices_by_fabric(parsed, "fabric-1")

    assert [device.id for device in devices] == ["leaf-1", "leaf-2"]
    assert [check._device_serial(device) for device in devices] == ["SERIAL1", None]


def test_workspace_id_includes_proposed_change_identity() -> None:
    assert get_proposed_change_id(SimpleNamespace(proposed_change_id="pc-123")) == "pc-123"
    assert get_workspace_id("pc-123", "Fabric-DC1") != get_workspace_id("pc-456", "Fabric-DC1")


@pytest.mark.asyncio
async def test_collect_eos_configs_fetches_structured_config_from_check_branch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    parsed = _cv_query()
    device = parsed.dcim_device.edges[0].node
    assert device is not None

    class FakeStructuredConfigFile:
        async def download_file(self) -> str:
            return "{}"

    class FakeClient:
        def __init__(self) -> None:
            self.calls: list[tuple[Any, dict[str, Any]]] = []

        async def get(self, kind: Any, **kwargs: Any) -> FakeStructuredConfigFile:
            self.calls.append((kind, kwargs))
            return FakeStructuredConfigFile()

    fake_client = FakeClient()
    check = CVConfigValidationCheck(branch="cv-check-test", client=fake_client)

    def fake_get_device_config(structured_config: dict[str, Any]) -> str:
        return "hostname leaf-1\n"

    monkeypatch.setattr("checks.cv_config_check.pyavd.get_device_config", fake_get_device_config)

    eos_configs = await check._collect_eos_configs([device], str(tmp_path))

    assert len(eos_configs) == 1
    assert fake_client.calls[0][1]["id"] == "sc-1"
    assert fake_client.calls[0][1]["branch"] == "cv-check-test"
