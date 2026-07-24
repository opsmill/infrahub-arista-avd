from __future__ import annotations

import importlib
import inspect
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Self, cast

import pytest
from infrahub_sdk.exceptions import NodeNotFoundError, SchemaNotFoundError

from checks import cv_config_check
from checks.cv_config_check import CVConfigValidationCheck
from checks.cv_config_check_query import CVConfigCheckQuery
from checks.cv_helpers import (
    DEFAULT_WORKSPACE_DESCRIPTION,
    get_change_control_url,
    get_cloudvision_config,
    get_proposed_change_context,
    get_proposed_change_id,
    get_workspace_description,
    get_workspace_id,
    get_workspace_name,
    get_workspace_url,
)
from checks.cv_workspace_lifecycle import (
    SubmissionResult,
    ensure_workspace_thread_and_url_comment,
    submit_linked_workspace_for_custom_webhook,
    submit_linked_workspace_for_proposed_change,
)
from transforms.cv_workspace_submission_webhook import CVWorkspaceSubmissionWebhookPayload
from transforms.cv_workspace_submission_webhook_query import CVWorkspaceSubmissionWebhookQuery


def test_cv_workspace_lifecycle_imports_from_check_import_context(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = Path(__file__).parents[2]
    checks_path = str(repo_root / "checks")
    module_names = (
        "checks.cv_workspace_lifecycle",
        "transforms",
        "transforms.cv_workspace_submission_webhook_query",
    )
    original_modules = {module_name: sys.modules.get(module_name) for module_name in module_names}
    checks_package = sys.modules.get("checks")
    original_lifecycle_attr = getattr(checks_package, "cv_workspace_lifecycle", None)

    for module_name in module_names:
        sys.modules.pop(module_name, None)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", [checks_path, *[path for path in sys.path if path not in ("", str(repo_root))]])

    try:
        importlib.import_module("checks.cv_workspace_lifecycle")
    finally:
        for module_name, module in original_modules.items():
            if module is None:
                sys.modules.pop(module_name, None)
            else:
                sys.modules[module_name] = module
        if checks_package is not None:
            if original_lifecycle_attr is None:
                if hasattr(checks_package, "cv_workspace_lifecycle"):
                    del checks_package.cv_workspace_lifecycle
            else:
                checks_package.cv_workspace_lifecycle = original_lifecycle_attr


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


def test_cv_query_parsing_tolerates_absent_optional_relationship_keys() -> None:
    data = _cv_query().model_dump(by_alias=True)
    device_nodes = [edge["node"] for edge in data["DcimDevice"]["edges"]]
    device_nodes[0].pop("pod")
    device_nodes[1]["pod"]["node"].pop("parent")
    device_nodes[2].pop("avd_artifact")
    device_nodes[4]["avd_artifact"] = {"node": {"id": "artifact-without-structured-config"}}

    parsed = CVConfigCheckQuery.model_validate(cv_config_check._normalize_optional_relationships(data))
    check = CVConfigValidationCheck.__new__(CVConfigValidationCheck)

    devices = check._devices_in_fabric(parsed, "fabric-1")

    assert [check._device_name(device) for device in devices] == ["leaf-no-config"]
    assert [check._structured_config_file_id(device) for device in devices] == [None]


@pytest.mark.asyncio
async def test_unmanaged_validation_tolerates_absent_optional_relationship_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CLOUDVISION_SERVERS", raising=False)
    data = _cv_query(cloudvision_managed=False).model_dump(by_alias=True)
    device_nodes = [edge["node"] for edge in data["DcimDevice"]["edges"]]
    device_nodes[0].pop("pod")
    device_nodes[1]["pod"]["node"].pop("parent")
    device_nodes[2].pop("avd_artifact")
    device_nodes[4]["avd_artifact"] = {"node": {"id": "artifact-without-structured-config"}}
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", SimpleNamespace()))

    await check.validate(data)

    assert check.errors == []
    assert "disabled" in check.logs[0]["message"]


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


def test_cloudvision_workspace_and_change_control_url_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    monkeypatch.setenv("CLOUDVISION_CHANGE_CONTROL_URL_TEMPLATE", "https://cv.example.com/cc/{change_control_id}")

    config = get_cloudvision_config()

    assert config is not None
    assert get_workspace_url(config, "ws-1") == "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"
    assert get_change_control_url(config, "cc-1") == "https://cv.example.com/cc/cc-1"


def test_repository_objects_register_one_placeholder_cloudvision_webhook() -> None:
    repository_text = "\n".join(
        Path(path).read_text(encoding="utf-8") for path in ["triggers.yml", "repository_checks.yml", ".infrahub.yml"]
    )

    assert repository_text.count("kind: CoreCustomWebhook") == 1
    assert repository_text.count("cloudvision-workspace-submission") == 2
    assert "https://placeholder.invalid/cloudvision-workspace-submission" in repository_text
    assert "cv-workspace-submission-webhook-payload" in repository_text
    assert "cv_workspace_submission_webhook_payload" in repository_text
    assert "CVWorkspaceSubmissionWebhookPayload" in repository_text
    webhook_block = repository_text.split("kind: CoreCustomWebhook", maxsplit=1)[1]
    assert "node_kind:" not in webhook_block
    assert "CoreStandardWebhook" not in repository_text


def test_cloudvision_docs_describe_placeholder_custom_webhook() -> None:
    docs = Path("docs/docs/cloudvision.md").read_text(encoding="utf-8")

    assert "cloudvision-workspace-submission" in docs
    assert "https://placeholder.invalid/cloudvision-workspace-submission" in docs
    assert "placeholder" in docs.lower()
    assert "no real external automation receiver is required" in docs.lower()


def test_cloudvision_docs_describe_custom_webhook_submission_and_manual_retry() -> None:
    docs = Path("docs/docs/cloudvision.md").read_text(encoding="utf-8")

    assert "submit_linked_workspace_for_proposed_change()" in docs
    assert "submit_linked_workspace_for_custom_webhook()" in docs
    assert "CustomWebhook" in docs
    assert "uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main" in docs
    assert "fallback" in docs
    assert "unresolved failure comment" in docs
    assert "CloudVision change-control management and Semaphore Ansible playbooks are out of scope" in docs


def test_custom_webhook_quickstart_lists_validation_and_retry_paths() -> None:
    quickstart = Path("specs/004-cv-config-validation/quickstart.md").read_text(encoding="utf-8")

    assert "uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main" in quickstart
    assert "uv run pytest tests/unit/test_cv_integration.py" in quickstart
    assert "uv run invoke lint" in quickstart
    assert "$infrahub-run-integration-tests" in quickstart
    assert "Exactly one intended CloudVision workspace submission `CoreCustomWebhook`" in quickstart


class _FakeWorkspaceNode:
    def __init__(
        self,
        *,
        obj_id: str = "workspace-node-1",
        workspace_id: str = "ws-1",
        status: str = "built",
        thread_id: str | None = None,
        workspace_url: str | None = "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1",
    ) -> None:
        self.id = obj_id
        self.name = SimpleNamespace(value="Workspace")
        self.workspace_id = SimpleNamespace(value=workspace_id)
        self.proposed_change_id = SimpleNamespace(value="pc-1")
        self.status = SimpleNamespace(value=status)
        self.workspace_url = SimpleNamespace(value=workspace_url)
        self.thread_id = SimpleNamespace(value=thread_id)
        self.change_control_id = SimpleNamespace(value=None)
        self.change_control_url = SimpleNamespace(value=None)
        self.last_submission_error = SimpleNamespace(value=None)
        self.last_submission_attempt_at = SimpleNamespace(value=None)
        self.submitted_at = SimpleNamespace(value=None)
        self.saved = 0

    async def save(self) -> None:
        self.saved += 1


class _FakeLifecycleClient:
    def __init__(
        self,
        workspaces: list[_FakeWorkspaceNode] | None = None,
        *,
        fail_comment_write: bool = False,
        fail_thread_resolve: bool = False,
    ) -> None:
        self.workspaces = workspaces if workspaces is not None else [_FakeWorkspaceNode()]
        self.threads: dict[str, dict[str, Any]] = {}
        self.comments: list[dict[str, str]] = []
        self.resolved: list[tuple[str, bool]] = []
        self.fail_comment_write = fail_comment_write
        self.fail_thread_resolve = fail_thread_resolve
        self.workspace_submission_query = Path("transforms/cv_workspace_submission_webhook.gql").read_text(
            encoding="utf-8"
        )

    async def get(self, **kwargs: Any) -> _FakeWorkspaceNode:
        obj_id = kwargs.get("id")
        workspace_id = kwargs.get("workspace_id__value")
        for workspace in self.workspaces:
            if obj_id == workspace.id or workspace_id == workspace.workspace_id.value:
                return workspace
        raise NodeNotFoundError({"workspace": ["not-found"]})

    async def create(self, **kwargs: Any) -> _FakeWorkspaceNode:
        data = kwargs["data"]
        node = _FakeWorkspaceNode(
            obj_id="workspace-node-created",
            workspace_id=data["workspace_id"],
            status=data["status"],
        )
        node.workspace_url.value = data.get("workspace_url")
        self.workspaces.append(node)
        return node

    async def execute_graphql(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs["query"]
        variables = kwargs.get("variables", {})
        if "CVWorkspaceSubmission" in query:
            assert query == self.workspace_submission_query
            return {
                "CloudvisionWorkspace": {
                    "edges": [
                        {
                            "node": {
                                "id": workspace.id,
                                "name": {"value": workspace.name.value},
                                "workspace_id": {"value": workspace.workspace_id.value},
                                "proposed_change_id": {"value": workspace.proposed_change_id.value},
                                "status": {"value": workspace.status.value},
                                "workspace_url": {"value": workspace.workspace_url.value},
                                "thread_id": {"value": workspace.thread_id.value},
                                "change_control_id": {"value": workspace.change_control_id.value},
                                "change_control_url": {"value": workspace.change_control_url.value},
                                "fabric": {"node": {"id": "fabric-1", "name": {"value": "Fabric-DC1"}}},
                            }
                        }
                        for workspace in self.workspaces
                    ]
                }
            }
        if "GetCloudVisionWorkspaceThreadById" in query:
            thread_id = variables["ids"][0]
            thread = self.threads.get(thread_id)
            return {"CoreChangeThread": {"edges": [{"node": thread}] if thread else []}}
        if "GetCloudVisionWorkspaceThread" in query:
            label = variables["label"]
            thread = next((thread for thread in self.threads.values() if thread["label"]["value"] == label), None)
            return {"CoreChangeThread": {"edges": [{"node": thread}] if thread else []}}
        if "CreateCloudVisionWorkspaceThread" in query:
            thread_id = f"thread-{len(self.threads) + 1}"
            thread = {
                "id": thread_id,
                "label": {"value": variables["label"]},
                "resolved": {"value": False},
                "comments": {"edges": []},
            }
            self.threads[thread_id] = thread
            return {"CoreChangeThreadCreate": {"ok": True, "object": thread}}
        if "AddCloudVisionWorkspaceThreadComment" in query:
            if self.fail_comment_write:
                raise RuntimeError("comment write failed")
            thread_id = variables["thread"]["id"]
            text = variables["text"]
            comment = {"id": f"comment-{len(self.comments) + 1}", "text": text, "thread_id": thread_id}
            self.comments.append(comment)
            self.threads[thread_id]["comments"]["edges"].append(
                {"node": {"id": comment["id"], "text": {"value": text}}}
            )
            return {"CoreThreadCommentCreate": {"ok": True, "object": {"id": comment["id"], "text": {"value": text}}}}
        if "ResolveCloudVisionWorkspaceThread" in query:
            if self.fail_thread_resolve:
                raise RuntimeError("resolve failed")
            thread_id = variables["id"]
            resolved = variables["resolved"]
            self.threads[thread_id]["resolved"]["value"] = resolved
            self.resolved.append((thread_id, resolved))
            return {"CoreChangeThreadUpdate": {"ok": True, "object": self.threads[thread_id]}}
        raise AssertionError(f"Unexpected GraphQL query: {query}")


def test_workspace_submission_runtime_query_and_generated_model_stay_aligned() -> None:
    query = Path("transforms/cv_workspace_submission_webhook.gql").read_text(encoding="utf-8")
    parsed = CVWorkspaceSubmissionWebhookQuery.model_validate(
        {
            "CloudvisionWorkspace": {
                "edges": [
                    {
                        "node": {
                            "id": "workspace-node-1",
                            "name": {"value": "Workspace"},
                            "workspace_id": {"value": "ws-1"},
                            "proposed_change_id": {"value": "pc-1"},
                            "status": {"value": "built"},
                            "workspace_url": {"value": "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"},
                            "thread_id": {"value": "thread-1"},
                            "change_control_id": {"value": "cc-1"},
                            "change_control_url": {"value": "https://www.cv.example.com/cc/cc-1"},
                            "fabric": {"node": {"id": "fabric-1", "name": {"value": "Fabric-DC1"}}},
                        }
                    }
                ]
            }
        }
    )

    assert all(
        field in query
        for field in (
            "workspace_id",
            "proposed_change_id",
            "status",
            "workspace_url",
            "thread_id",
            "change_control_id",
            "change_control_url",
            "fabric",
        )
    )
    node = parsed.cloudvision_workspace.edges[0].node
    assert node is not None
    assert node.workspace_id is not None
    assert node.workspace_id.value == "ws-1"
    assert node.fabric.node is not None
    assert node.fabric.node.name is not None
    assert node.fabric.node.name.value == "Fabric-DC1"
    assert node.change_control_id is not None
    assert node.change_control_id.value == "cc-1"


@pytest.mark.asyncio
async def test_workspace_thread_creation_adds_exact_url_comment_once() -> None:
    client = _FakeLifecycleClient(workspaces=[])
    workspace_url = "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"

    first_thread_id = await ensure_workspace_thread_and_url_comment(
        client,
        proposed_change_id="pc-1",
        workspace_id="ws-1",
        fabric_name="Fabric-DC1",
        workspace_url=workspace_url,
        branch="branch-1",
    )
    second_thread_id = await ensure_workspace_thread_and_url_comment(
        client,
        proposed_change_id="pc-1",
        workspace_id="ws-1",
        fabric_name="Fabric-DC1",
        workspace_url=workspace_url,
        branch="branch-1",
        thread_id=first_thread_id,
    )

    assert first_thread_id == second_thread_id
    assert list(client.threads) == ["thread-1"]
    assert len(client.comments) == 1
    assert workspace_url in client.comments[0]["text"]


@pytest.mark.asyncio
async def test_workspace_tracking_persists_workspace_url_and_thread_id() -> None:
    node = _FakeWorkspaceNode()
    client = _FakeLifecycleClient([node])
    check = CVConfigValidationCheck(branch="cv-check-test", client=cast("Any", client))

    await check._track_workspace(
        "ws-1",
        "Workspace",
        "fabric-1",
        "pc-1",
        "built",
        workspace_url="https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1",
        fabric_name="Fabric-DC1",
    )

    assert node.workspace_url.value.endswith("ws=ws-1")
    assert node.thread_id.value == "thread-1"
    assert len(client.comments) == 1


@pytest.mark.asyncio
async def test_submit_linked_workspace_success_updates_workspace_comments_and_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    monkeypatch.setenv("CLOUDVISION_CHANGE_CONTROL_URL_TEMPLATE", "https://www.cv.example.com/cc/{change_control_id}")
    client = _FakeLifecycleClient([_FakeWorkspaceNode()])

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="built")

        async def submit_workspace(self, workspace_id: str, force: bool = False) -> SimpleNamespace:
            assert workspace_id == "ws-1"
            assert force is False
            return SimpleNamespace(request_params=SimpleNamespace(request_id="req-1"))

        async def wait_for_workspace_response(self, **kwargs: Any) -> tuple[SimpleNamespace, SimpleNamespace]:
            assert kwargs == {"workspace_id": "ws-1", "request_id": "req-1", "timeout": 600.0}
            return SimpleNamespace(status="success"), SimpleNamespace(change_control_id="cc-1")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.CVClient", FakeCVClient)

    result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    workspace = client.workspaces[0]
    assert result == SubmissionResult(
        status="submitted",
        proposed_change_id="pc-1",
        workspace_id="ws-1",
        fabric_name="Fabric-DC1",
        thread_id="thread-1",
        change_control_id="cc-1",
        message=(
            "CloudVision workspace ws-1 submitted successfully. "
            "Workspace: https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"
        ),
    )
    assert workspace.status.value == "submitted"
    assert workspace.change_control_id.value == "cc-1"
    assert workspace.change_control_url.value == "https://www.cv.example.com/cc/cc-1"
    assert client.resolved[-1] == ("thread-1", True)


@pytest.mark.asyncio
async def test_submit_linked_workspace_failure_records_unresolved_comment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    client = _FakeLifecycleClient([_FakeWorkspaceNode()])

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="built")

        async def submit_workspace(self, workspace_id: str, force: bool = False) -> SimpleNamespace:
            raise RuntimeError("rejected by CloudVision")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.CVClient", FakeCVClient)

    result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    workspace = client.workspaces[0]
    assert result.status == "failed"
    assert result.workspace_id == "ws-1"
    assert workspace.status.value == "submit_failed"
    assert "rejected by CloudVision" in workspace.last_submission_error.value
    assert client.resolved[-1] == ("thread-1", False)
    assert any("Infrahub proposed change pc-1 was submitted" in comment["text"] for comment in client.comments)


@pytest.mark.asyncio
async def test_submit_linked_workspace_already_submitted_does_not_submit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    client = _FakeLifecycleClient([_FakeWorkspaceNode(status="submitted")])

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def submit_workspace(self, workspace_id: str, force: bool = False) -> None:
            pytest.fail("already-submitted workspace should not be submitted")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.CVClient", FakeCVClient)

    result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    assert result.status == "already_submitted"
    assert client.resolved[-1] == ("thread-1", True)


@pytest.mark.asyncio
async def test_submit_linked_workspace_missing_or_ambiguous_linkage_skips_or_fails() -> None:
    skipped_client = _FakeLifecycleClient([])
    skipped = await submit_linked_workspace_for_proposed_change(skipped_client, "pc-1", branch="main")
    ambiguous_client = _FakeLifecycleClient(
        [_FakeWorkspaceNode(workspace_id="ws-1"), _FakeWorkspaceNode(workspace_id="ws-2")]
    )
    failed = await submit_linked_workspace_for_proposed_change(
        ambiguous_client,
        "pc-1",
        branch="main",
    )

    assert skipped.status == "skipped"
    assert skipped.thread_id == "thread-1"
    assert skipped_client.threads["thread-1"]["label"]["value"] == "CloudVision workspace submission"
    assert "No linked CloudVision workspace found" in skipped_client.comments[0]["text"]
    assert skipped_client.resolved[-1] == ("thread-1", True)
    assert failed.status == "failed"
    assert failed.thread_id == "thread-1"
    assert "Multiple CloudVision workspaces" in failed.message
    assert "Multiple CloudVision workspaces" in ambiguous_client.comments[0]["text"]
    assert ambiguous_client.resolved[-1] == ("thread-1", False)


@pytest.mark.asyncio
async def test_submit_linked_workspace_event_adapter_passes_event_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []

    async def submit_for_pc(client: Any, proposed_change_id: str, *, branch: str = "main") -> SubmissionResult:
        calls.append((proposed_change_id, branch))
        return SubmissionResult(status="skipped", proposed_change_id=proposed_change_id, message="done")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.submit_linked_workspace_for_proposed_change", submit_for_pc)

    result = await submit_linked_workspace_for_custom_webhook(
        SimpleNamespace(),
        {
            "event": "infrahub.proposed_change.submitted",
            "branch": "main",
            "payload": {"proposed_change_id": "pc-submitted", "check_name": "cv-config-validation"},
        },
        branch="fallback",
    )

    assert result.status == "skipped"
    assert calls == [("pc-submitted", "main")]


@pytest.mark.asyncio
async def test_custom_webhook_adapter_ignores_other_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    async def submit_for_pc(client: Any, proposed_change_id: str, *, branch: str = "main") -> SubmissionResult:
        pytest.fail("unrelated check should not submit a CloudVision workspace")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.submit_linked_workspace_for_proposed_change", submit_for_pc)

    result = await submit_linked_workspace_for_custom_webhook(
        SimpleNamespace(),
        {"payload": {"proposed_change_id": "pc-1", "check_name": "other-check"}},
    )

    assert result.status == "skipped"
    assert "other-check" in result.message


@pytest.mark.asyncio
async def test_submit_linked_workspace_derives_missing_workspace_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    client = _FakeLifecycleClient([_FakeWorkspaceNode(workspace_url=None)])

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="built")

        async def submit_workspace(self, workspace_id: str, force: bool = False) -> SimpleNamespace:
            return SimpleNamespace(request_params=SimpleNamespace(request_id="req-1"))

        async def wait_for_workspace_response(self, **kwargs: Any) -> tuple[SimpleNamespace, SimpleNamespace]:
            return SimpleNamespace(status="success"), SimpleNamespace(change_control_id="cc-1")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.CVClient", FakeCVClient)

    result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    assert result.status == "submitted"
    assert client.workspaces[0].workspace_url.value == "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"
    assert "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1" in client.comments[0]["text"]


@pytest.mark.asyncio
async def test_custom_webhook_payload_transform_returns_submission_payload() -> None:
    transform = CVWorkspaceSubmissionWebhookPayload.__new__(CVWorkspaceSubmissionWebhookPayload)
    payload = await transform.transform(
        {
            "CloudvisionWorkspace": {
                "edges": [
                    {
                        "node": {
                            "id": "workspace-node-1",
                            "name": {"value": "Workspace"},
                            "workspace_id": {"value": "ws-1"},
                            "proposed_change_id": {"value": "pc-1"},
                            "status": {"value": "built"},
                            "workspace_url": {"value": "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1"},
                            "thread_id": {"value": "thread-1"},
                            "change_control_id": {"value": None},
                            "change_control_url": {"value": None},
                            "fabric": {"node": {"id": "fabric-1", "name": {"value": "Fabric-DC1"}}},
                        }
                    }
                ]
            }
        }
    )

    assert payload == {
        "check_name": "cv-config-validation",
        "proposed_change_id": "pc-1",
        "workspaces": [
            {
                "workspace_id": "ws-1",
                "proposed_change_id": "pc-1",
                "status": "built",
                "workspace_url": "https://www.cv.example.com/cv/provisioning/workspaces?ws=ws-1",
                "fabric_name": "Fabric-DC1",
            }
        ],
    }


@pytest.mark.asyncio
async def test_submit_linked_workspace_malformed_workspace_url_does_not_create_empty_url_comment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeLifecycleClient([_FakeWorkspaceNode(status="submitted", workspace_url="not-a-url")])

    result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    assert result.status == "already_submitted"
    assert len(client.comments) == 1
    assert "not-a-url" not in client.comments[0]["text"]
    assert "already submitted" in client.comments[0]["text"]


@pytest.mark.asyncio
async def test_successful_submission_logs_fallback_when_thread_comment_fails(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("CLOUDVISION_SERVERS", "www.cv.example.com")
    monkeypatch.setenv("CLOUDVISION_TOKEN", "token")
    client = _FakeLifecycleClient([_FakeWorkspaceNode()], fail_comment_write=True)

    class FakeCVClient:
        def __init__(self, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def get_workspace(self, workspace_id: str) -> SimpleNamespace:
            return SimpleNamespace(state="built")

        async def submit_workspace(self, workspace_id: str, force: bool = False) -> SimpleNamespace:
            return SimpleNamespace(request_params=SimpleNamespace(request_id="req-1"))

        async def wait_for_workspace_response(self, **kwargs: Any) -> tuple[SimpleNamespace, SimpleNamespace]:
            return SimpleNamespace(status="success"), SimpleNamespace(change_control_id="cc-1")

    monkeypatch.setattr("checks.cv_workspace_lifecycle.CVClient", FakeCVClient)

    with caplog.at_level("ERROR", logger="checks.cv_workspace_lifecycle"):
        result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    assert result.status == "submitted"
    assert client.workspaces[0].status.value == "submitted"
    assert "fallback outcome: status=submitted proposed_change_id=pc-1 workspace_id=ws-1" in caplog.text


@pytest.mark.asyncio
async def test_already_submitted_logs_fallback_when_thread_resolve_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = _FakeLifecycleClient([_FakeWorkspaceNode(status="submitted")], fail_thread_resolve=True)

    with caplog.at_level("ERROR", logger="checks.cv_workspace_lifecycle"):
        result = await submit_linked_workspace_for_proposed_change(client, "pc-1", branch="main")

    assert result.status == "already_submitted"
    assert "fallback outcome: status=already_submitted proposed_change_id=pc-1 workspace_id=ws-1" in caplog.text


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

    async def track_workspace(
        ws_id: str,
        ws_name: str,
        fabric_id: str,
        proposed_change_id: str,
        status: str,
        **kwargs: Any,
    ) -> None:
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
    assert any(log["message"] == "Confirmed 2 devices in CloudVision inventory, skipped 0" for log in check.logs)
    assert any(log["message"] == "Devices with validated configurations: leaf-1" for log in check.logs)
    assert not any("Deployed" in log["message"] for log in check.logs)
    assert not any("Devices with configs deployed" in log["message"] for log in check.logs)


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
