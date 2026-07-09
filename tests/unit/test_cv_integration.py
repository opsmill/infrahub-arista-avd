from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest

from checks.cv_config_check import CVConfigValidationCheck
from checks.cv_config_check_query import CVConfigCheckQuery
from checks.cv_helpers import (
    DEFAULT_WORKSPACE_DESCRIPTION,
    get_cloudvision_config,
    get_proposed_change_context,
    get_proposed_change_id,
    get_workspace_description,
    get_workspace_id,
    get_workspace_name,
)

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


def test_workspace_name_and_description_use_proposed_change_metadata() -> None:
    assert get_workspace_name("Add Tenant", "Fabric-DC1") == (
        "Infrahub Proposed Changes Add Tenant - Fabric Fabric-DC1"
    )
    assert get_workspace_description("  Review EOS changes  ") == "Review EOS changes"
    assert get_workspace_description("") == DEFAULT_WORKSPACE_DESCRIPTION


@pytest.mark.asyncio
async def test_proposed_change_context_fetches_name_and_description() -> None:
    class FakeClient:
        async def execute_graphql(self, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["variables"] == {"ids": ["pc-123"]}
            return {
                "CoreProposedChange": {
                    "edges": [
                        {
                            "node": {
                                "id": "pc-123",
                                "name": {"value": "Update Fabric"},
                                "description": {"value": "Validate changed EOS config"},
                            }
                        }
                    ]
                }
            }

    context = await get_proposed_change_context(FakeClient(), SimpleNamespace(proposed_change_id="pc-123"))

    assert context.id == "pc-123"
    assert context.name == "Update Fabric"
    assert context.description == "Validate changed EOS config"


@pytest.mark.asyncio
async def test_proposed_change_context_uses_safe_description_fallback() -> None:
    class FakeClient:
        async def execute_graphql(self, **kwargs: Any) -> dict[str, Any]:
            return {
                "CoreProposedChange": {
                    "edges": [
                        {
                            "node": {
                                "id": "pc-123",
                                "name": {"value": "Update Fabric"},
                                "description": {"value": ""},
                            }
                        }
                    ]
                }
            }

    context = await get_proposed_change_context(FakeClient(), SimpleNamespace(proposed_change_id="pc-123"))

    assert context.name == "Update Fabric"
    assert context.description == DEFAULT_WORKSPACE_DESCRIPTION


@pytest.mark.asyncio
async def test_proposed_change_context_falls_back_to_source_branch_lookup() -> None:
    class FakeClient:
        async def execute_graphql(self, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["variables"] == {"sourceBranch": "cv-config-check"}
            return {
                "CoreProposedChange": {
                    "edges": [
                        {
                            "node": {
                                "id": "pc-from-branch",
                                "name": {"value": "Branch Proposed Change"},
                                "description": {"value": "Found by source branch"},
                            }
                        }
                    ]
                }
            }

    context = await get_proposed_change_context(FakeClient(), SimpleNamespace(), "cv-config-check")

    assert context.id == "pc-from-branch"
    assert context.name == "Branch Proposed Change"
    assert context.description == "Found by source branch"


def test_cloudvision_config_ignores_blank_proxy_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    monkeypatch.setenv("CLOUDVISION_USERNAME", "")
    monkeypatch.setenv("CLOUDVISION_PASSWORD", "")
    monkeypatch.setenv("CLOUDVISION_PROXY_HOST", "")
    monkeypatch.setenv("CLOUDVISION_PROXY_PORT", "")
    monkeypatch.setenv("CLOUDVISION_PROXY_USERNAME", "")
    monkeypatch.setenv("CLOUDVISION_PROXY_PASSWORD", "")

    config = get_cloudvision_config()

    assert config is not None
    assert config.servers == ["www.cv.example.com"]
    assert config.proxy_host is None
    assert config.proxy_port is None
    assert config.proxy_username is None
    assert config.proxy_password is None


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
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", fake_client))

    def fake_get_device_config(structured_config: dict[str, Any]) -> str:
        return "hostname leaf-1\n"

    monkeypatch.setattr("checks.cv_config_check.pyavd.get_device_config", fake_get_device_config)

    eos_configs = await check._collect_eos_configs([device], str(tmp_path))

    assert len(eos_configs) == 1
    assert fake_client.calls[0][1]["id"] == "sc-1"
    assert fake_client.calls[0][1]["branch"] == "cv-check-test"
