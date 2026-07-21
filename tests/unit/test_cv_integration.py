from __future__ import annotations

import inspect
import time
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, Self, cast

import pytest
from infrahub_sdk.exceptions import NodeNotFoundError, SchemaNotFoundError

from checks import cv_config_check
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


def _fabric_node(cloudvision_managed: bool | None = True) -> dict[str, Any]:
    return {
        "id": "fabric-1",
        "name": {"value": "Fabric-DC1"},
        "cloudvision_managed": {"value": cloudvision_managed},
    }


def _device_node(
    *,
    obj_id: str,
    name: str,
    serial: str | None,
    fabric_id: str | None = "fabric-1",
    structured_config_id: str | None = None,
) -> dict[str, Any]:
    pod: dict[str, Any] = {"node": None}
    if fabric_id is not None:
        pod = {
            "node": {
                "id": f"pod-{fabric_id}",
                "parent": {"node": {"__typename": "NetworkFabric", "id": fabric_id}},
            }
        }
    avd_artifact: dict[str, Any] = {"node": None}
    if structured_config_id is not None:
        avd_artifact = {
            "node": {"id": f"artifact-{obj_id}", "structured_config_file": {"node": {"id": structured_config_id}}}
        }
    return {
        "id": obj_id,
        "name": {"value": name},
        "serial": {"value": serial},
        "pod": pod,
        "avd_artifact": avd_artifact,
    }


def _cv_query(cloudvision_managed: bool | None = True) -> CVConfigCheckQuery:
    return CVConfigCheckQuery.model_validate(
        {
            "NetworkFabric": {"edges": [{"node": _fabric_node(cloudvision_managed)}]},
            "DcimDevice": {
                "edges": [
                    {
                        "node": _device_node(
                            obj_id="leaf-1", name="leaf-1", serial="SERIAL1", structured_config_id="sc-1"
                        )
                    },
                    {"node": _device_node(obj_id="leaf-2", name="leaf-2", serial=None, structured_config_id="sc-2")},
                    {
                        "node": _device_node(
                            obj_id="other",
                            name="other",
                            serial="SERIAL2",
                            fabric_id="fabric-2",
                            structured_config_id="sc-3",
                        )
                    },
                    {"node": _device_node(obj_id="server", name="server", serial="SERIAL3", fabric_id=None)},
                    {"node": _device_node(obj_id="leaf-no-config", name="leaf-no-config", serial="SERIAL4")},
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


def test_cv_devices_in_fabric_includes_devices_without_structured_configs() -> None:
    parsed = _cv_query()
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)

    devices = check._devices_in_fabric(parsed, "fabric-1")

    assert [device.id for device in devices] == ["leaf-1", "leaf-2", "leaf-no-config"]


def test_workspace_id_includes_proposed_change_identity() -> None:
    assert get_proposed_change_id(SimpleNamespace(proposed_change_id="pc-123")) == "pc-123"
    assert get_workspace_id("pc-123", "Fabric-DC1") != get_workspace_id("pc-456", "Fabric-DC1")


def test_workspace_name_and_description_use_proposed_change_metadata() -> None:
    assert get_workspace_name("Add Tenant", "Fabric-DC1") == (
        "Infrahub Proposed Changes Add Tenant - Fabric Fabric-DC1"
    )
    assert get_workspace_description("  Review EOS changes  ") == "Review EOS changes"
    assert get_workspace_description("", "pc-123", "Fabric-DC1") == (
        "Infrahub CloudVision validation for proposed change pc-123 on fabric Fabric-DC1"
    )
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
            assert kwargs["variables"] == {"sourceBranches": ["cv-config-check"]}
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


@pytest.mark.asyncio
async def test_proposed_change_context_falls_back_to_short_feature_branch_name() -> None:
    class FakeClient:
        async def execute_graphql(self, **kwargs: Any) -> dict[str, Any]:
            assert kwargs["variables"] == {"sourceBranches": ["feat/cv-config-check", "cv-config-check"]}
            return {
                "CoreProposedChange": {
                    "edges": [
                        {
                            "node": {
                                "id": "pc-from-short-branch",
                                "name": {"value": "Short Branch Proposed Change"},
                                "description": {"value": "Found by short source branch"},
                            }
                        }
                    ]
                }
            }

    context = await get_proposed_change_context(FakeClient(), SimpleNamespace(), "feat/cv-config-check")

    assert context.id == "pc-from-short-branch"
    assert context.name == "Short Branch Proposed Change"
    assert context.description == "Found by short source branch"


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


def test_cloudvision_config_supports_username_password_and_invalid_proxy_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password_value = "cv-" + "pass"
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.delenv("CLOUDVISION_TOKEN", raising=False)
    monkeypatch.setenv("CLOUDVISION_USERNAME", "cv-user")
    monkeypatch.setenv("CLOUDVISION_PASSWORD", password_value)
    monkeypatch.setenv("CLOUDVISION_VERIFY_CERTS", "false")
    monkeypatch.setenv("CLOUDVISION_PROXY_PORT", "not-a-port")

    config = get_cloudvision_config()

    assert config is not None
    assert config.username == "cv-user"
    assert config.password == password_value
    assert config.verify_certs is False
    assert config.proxy_port is None


@pytest.mark.asyncio
async def test_unmanaged_fabric_skips_before_cloudvision_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUDVISION_SERVERS", raising=False)
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    await check.validate(_cv_query(cloudvision_managed=False).model_dump(by_alias=True))

    assert check.errors == []
    assert check.logs[0]["level"] == "INFO"
    assert "disabled" in check.logs[0]["message"]


@pytest.mark.asyncio
async def test_missing_cloudvision_managed_defaults_to_unmanaged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUDVISION_SERVERS", raising=False)
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    await check.validate(_cv_query(cloudvision_managed=None).model_dump(by_alias=True))

    assert check.errors == []
    assert "disabled" in check.logs[0]["message"]


@pytest.mark.asyncio
async def test_managed_fabric_missing_credentials_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOUDVISION_SERVERS", raising=False)
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    await check.validate(_cv_query().model_dump(by_alias=True))

    assert len(check.errors) == 1
    assert "CloudVision credentials not configured" in check.errors[0]["message"]


@pytest.mark.asyncio
async def test_missing_serials_fail_before_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    async def fail_if_called(**kwargs: Any) -> list[Any]:
        pytest.fail("inventory verification should not run when serial numbers are missing")

    monkeypatch.setattr(check, "_verify_inventory", fail_if_called)

    await check.validate(_cv_query().model_dump(by_alias=True))

    assert len(check.errors) == 1
    assert "leaf-2" in check.errors[0]["message"]


@pytest.mark.asyncio
async def test_no_generated_configs_skips_after_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    data = {
        "NetworkFabric": {"edges": [{"node": _fabric_node(True)}]},
        "DcimDevice": {
            "edges": [
                {"node": _device_node(obj_id="leaf-1", name="leaf-1", serial="SERIAL1")},
            ]
        },
    }
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    async def verify_inventory(**kwargs: Any) -> list[Any]:
        return [SimpleNamespace()]

    monkeypatch.setattr(check, "_verify_inventory", verify_inventory)

    await check.validate(data)

    assert check.errors == []
    assert "No generated EOS configurations" in check.logs[-1]["message"]


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
    assert eos_configs[0].device.hostname == "leaf-1"


@pytest.mark.asyncio
async def test_collect_eos_configs_blocks_json_decode_failure(tmp_path: Path) -> None:
    parsed = _cv_query()
    device = parsed.dcim_device.edges[0].node
    assert device is not None

    class FakeStructuredConfigFile:
        async def download_file(self) -> str:
            return "{"

    class FakeClient:
        async def get(self, kind: Any, **kwargs: Any) -> FakeStructuredConfigFile:
            return FakeStructuredConfigFile()

    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", FakeClient()))

    eos_configs = await check._collect_eos_configs([device], str(tmp_path))

    assert eos_configs == []
    assert len(check.errors) == 1
    assert "leaf-1" in check.errors[0]["message"]


@pytest.mark.asyncio
async def test_collect_eos_configs_blocks_pyavd_render_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    parsed = _cv_query()
    device = parsed.dcim_device.edges[0].node
    assert device is not None

    class FakeStructuredConfigFile:
        async def download_file(self) -> str:
            return "{}"

    class FakeClient:
        async def get(self, kind: Any, **kwargs: Any) -> FakeStructuredConfigFile:
            return FakeStructuredConfigFile()

    def raise_render_error(structured_config: dict[str, Any]) -> str:
        raise ValueError("render failed")

    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", FakeClient()))
    monkeypatch.setattr("checks.cv_config_check.pyavd.get_device_config", raise_render_error)

    eos_configs = await check._collect_eos_configs([device], str(tmp_path))

    assert eos_configs == []
    assert len(check.errors) == 1
    assert "render failed" in check.errors[0]["message"]


@pytest.mark.asyncio
async def test_existing_pending_workspace_is_reused_without_recreate() -> None:
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)
    workspace = SimpleNamespace(id="ws-1", name="Workspace", state=None)

    class FakeCVClient:
        def __init__(self) -> None:
            self.created = False
            self.waits: list[tuple[str, str]] = []

        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="pending")

        async def create_workspace(self, **kwargs: Any) -> None:
            self.created = True

        async def wait_for_workspace_state(self, *, workspace_id: str, state: str) -> None:
            self.waits.append((workspace_id, state))

    client = FakeCVClient()

    await check._ensure_workspace_pending(cast("Any", client), cast("Any", workspace), "description")

    assert client.created is False
    assert client.waits == [("ws-1", "pending")]


@pytest.mark.asyncio
async def test_existing_built_workspace_is_rolled_back(monkeypatch: pytest.MonkeyPatch) -> None:
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)
    workspace = SimpleNamespace(id="ws-1", name="Workspace", state=None)
    rolled_back: list[str] = []

    class FakeCVClient:
        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="built")

        async def create_workspace(self, **kwargs: Any) -> None:
            pytest.fail("existing workspace should not be recreated")

        async def wait_for_workspace_state(self, *, workspace_id: str, state: str) -> None:
            assert (workspace_id, state) == ("ws-1", "pending")

    async def fake_rollback(cv_client: Any, workspace_id: str) -> None:
        rolled_back.append(workspace_id)

    monkeypatch.setattr("checks.cv_config_check.rollback_workspace", fake_rollback)

    await check._ensure_workspace_pending(cast("Any", FakeCVClient()), cast("Any", workspace), "description")

    assert rolled_back == ["ws-1"]


@pytest.mark.asyncio
async def test_workspace_tracking_updates_existing_node() -> None:
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))
    saved: list[str] = []
    node = SimpleNamespace(status=SimpleNamespace(value="pending"), proposed_change_id=SimpleNamespace(value="old"))

    async def save() -> None:
        saved.append("saved")

    node.save = save

    class FakeClient:
        async def get(self, **kwargs: Any) -> SimpleNamespace:
            assert kwargs["workspace_id__value"] == "ws-1"
            return node

    check.client = cast("Any", FakeClient())

    await check._track_workspace("ws-1", "Workspace", "fabric-1", "pc-1", "built")

    assert node.status.value == "built"
    assert node.proposed_change_id.value == "pc-1"
    assert saved == ["saved"]


@pytest.mark.asyncio
async def test_workspace_tracking_creates_missing_node() -> None:
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))
    created: list[dict[str, Any]] = []

    class FakeNode:
        async def save(self) -> None:
            created.append({"saved": True})

    class FakeClient:
        async def get(self, **kwargs: Any) -> SimpleNamespace:
            raise NodeNotFoundError({"workspace_id": ["ws-1"]})

        async def create(self, **kwargs: Any) -> FakeNode:
            created.append(kwargs["data"])
            return FakeNode()

    check.client = cast("Any", FakeClient())

    await check._track_workspace("ws-1", "Workspace", "fabric-1", "pc-1", "built")

    assert created[0]["workspace_id"] == "ws-1"
    assert created[0]["fabric"] == "fabric-1"
    assert created[1] == {"saved": True}


@pytest.mark.asyncio
async def test_workspace_tracking_schema_absence_does_not_fail() -> None:
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    class FakeClient:
        async def get(self, **kwargs: Any) -> SimpleNamespace:
            raise SchemaNotFoundError("CloudvisionWorkspace")

    check.client = cast("Any", FakeClient())

    await check._track_workspace("ws-1", "Workspace", "fabric-1", "pc-1", "built")


@pytest.mark.asyncio
async def test_deploy_and_build_blocks_inactive_inventory_device_after_successful_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))
    tracked_statuses: list[str] = []

    config_path = tmp_path / "leaf-1.cfg"
    config_path.write_text("hostname leaf-1\n")
    eos_config = cv_config_check.CVEosConfig(
        file=str(config_path),
        device=cv_config_check.CVDevice(
            avd_device=cv_config_check.AvdDevice(hostname="leaf-1"), serial_number="SERIAL1"
        ),
        configlet_name="Infrahub_leaf-1",
    )
    inventory_devices = [
        cv_config_check.CVDevice(
            avd_device=cv_config_check.AvdDevice(hostname="leaf-1"), serial_number="SERIAL1", streaming=True
        ),
        cv_config_check.CVDevice(
            avd_device=cv_config_check.AvdDevice(hostname="leaf-2"), serial_number="SERIAL2", streaming=False
        ),
    ]

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

    async def ensure_workspace_pending(*args: Any, **kwargs: Any) -> None:
        return None

    async def verify_devices(*args: Any, **kwargs: Any) -> None:
        return None

    async def deploy_configs(*, configs: list[cv_config_check.CVEosConfig], result: Any, cv_client: Any) -> None:
        result.deployed_configs.extend(configs)

    async def finalize_workspace(*args: Any, **kwargs: Any) -> None:
        return None

    async def track_workspace(ws_id: str, ws_name: str, fabric_id: str, proposed_change_id: str, status: str) -> None:
        tracked_statuses.append(status)

    token_value = "cv-" + "token"
    monkeypatch.setattr("checks.cv_config_check.CVClient", FakeCVClient)
    monkeypatch.setattr(check, "_ensure_workspace_pending", ensure_workspace_pending)
    monkeypatch.setattr("checks.cv_config_check.verify_devices_on_cv", verify_devices)
    monkeypatch.setattr("checks.cv_config_check.deploy_configs_to_cv", deploy_configs)
    monkeypatch.setattr("checks.cv_config_check.finalize_workspace_on_cv", finalize_workspace)
    monkeypatch.setattr(check, "_track_workspace", track_workspace)

    await check._deploy_and_build(
        cv_config=SimpleNamespace(
            servers=["www.cv.example.com"],
            token=token_value,
            username=None,
            password=None,
            verify_certs=True,
            proxy_host=None,
            proxy_port=None,
            proxy_username=None,
            proxy_password=None,
        ),
        ws_id="ws-1",
        ws_name="Workspace",
        ws_description="description",
        proposed_change_id="pc-1",
        eos_configs=[eos_config],
        fabric_name="Fabric-DC1",
        fabric_id="fabric-1",
        inventory_devices=inventory_devices,
    )

    assert tracked_statuses == ["abandoned"]
    assert any("inactive" in error["message"] and "leaf-2" in error["message"] for error in check.errors)
    assert any("workspace built successfully" in log["message"] for log in check.logs)


def test_check_does_not_submit_or_register_lifecycle_hooks() -> None:
    source = inspect.getsource(CVConfigValidationCheck)

    assert ".submit" not in source
    assert "submit_workspace" not in source
    assert "abandon_workspace" not in source
    assert "proposed-change deletion" not in source


def test_50_device_local_selection_path_completes_within_documented_threshold() -> None:
    data = {
        "NetworkFabric": {"edges": [{"node": _fabric_node(True)}]},
        "DcimDevice": {
            "edges": [
                {
                    "node": _device_node(
                        obj_id=f"leaf-{index}",
                        name=f"leaf-{index}",
                        serial=f"SERIAL{index}",
                        structured_config_id=f"sc-{index}",
                    )
                }
                for index in range(50)
            ]
        },
    }
    parsed = CVConfigCheckQuery.model_validate(data)
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)

    start = time.perf_counter()
    devices = check._devices_in_fabric(parsed, "fabric-1")
    deploy_devices = check._filter_devices_by_fabric(parsed, "fabric-1")
    elapsed = time.perf_counter() - start

    assert len(devices) == 50
    assert len(deploy_devices) == 50
    assert elapsed < 1.0
