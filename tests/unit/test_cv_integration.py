from __future__ import annotations

from types import SimpleNamespace

from checks.cv_config_check import CVConfigValidationCheck
from checks.cv_config_check_query import CVConfigCheckQuery
from checks.cv_helpers import get_proposed_change_id, get_workspace_id


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
