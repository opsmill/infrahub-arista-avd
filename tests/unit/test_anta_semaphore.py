import json
from pathlib import Path

import yaml
from invoke import Context
from pytest import MonkeyPatch

import tasks

ROOT = Path(__file__).parents[2]
PLAYBOOK_PATH = ROOT / "ansible" / "test.yml"
INVENTORY_PATH = ROOT / "ansible" / "inventory.yml"


def _playbook() -> list[dict[str, object]]:
    content = yaml.safe_load(PLAYBOOK_PATH.read_text(encoding="utf-8"))
    assert isinstance(content, list)
    return content


def _named_tasks(play: dict[str, object], section: str) -> dict[str, dict[str, object]]:
    task_list = play[section]
    assert isinstance(task_list, list)
    return {str(task["name"]): task for task in task_list}


def test_fabric_anta_filters_schema_and_example_data_contract() -> None:
    schema = yaml.safe_load((ROOT / "schemas" / "l3ls_extensions.yml").read_text(encoding="utf-8"))
    fabric_extension = next(item for item in schema["extensions"]["nodes"] if item["kind"] == "NetworkFabric")
    attribute = next(item for item in fabric_extension["attributes"] if item["name"] == "avd_catalogs_filters")
    assert attribute["kind"] == "List"
    assert attribute["optional"] is True

    documents = yaml.safe_load_all((ROOT / "objects" / "11_l3ls_multi_domain_fabric.yml").read_text(encoding="utf-8"))
    fabric_document = next(document for document in documents if document["spec"]["kind"] == "NetworkFabric")
    fabric = next(item for item in fabric_document["spec"]["data"] if item.get("name") == "Fabric-L3LS-Multi-Domain")
    assert fabric["avd_catalogs_filters"] == ["VerifyInterfaceDiscards", "VerifyLoggingErrors"]


def test_infrahub_inventory_is_main_only_and_exposes_anta_fields() -> None:
    inventory = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))

    assert inventory["branch"] == "main"
    assert "token" not in inventory
    assert inventory["hostnames"] == ["display_label"]
    includes = inventory["nodes"]["DcimDevice"]["include"]
    assert includes == ["role", "mgmt_ip.address", "pod.parent.name", "status"]
    assert "name" not in includes
    assert "device_type.name" not in includes
    assert "location.name" not in includes
    assert "mgmt_ip.address" in includes
    assert "pod.parent.name" in includes
    assert inventory["compose"]["infrahub_fabric_name"] == "pod.parent.name"
    assert "mgmt_ip.address" in inventory["compose"]["ansible_host"]


def test_playbook_requires_exact_fabric_scope_and_valid_target_inventory() -> None:
    selection_play = _playbook()[0]
    tasks_by_name = _named_tasks(selection_play, "tasks")

    require_fabric = tasks_by_name["Require a fabric name"]["ansible.builtin.assert"]
    assert require_fabric["that"] == [
        "fabric_name is defined",
        "fabric_name | string | trim | length > 0",
    ]

    add_hosts = tasks_by_name["Add devices from the requested fabric to the ANTA target group"]
    assert add_hosts["when"] == "hostvars[item].infrahub_fabric_name | default('') == anta_selected_fabric"
    assert add_hosts["ansible.builtin.add_host"]["groups"] == "infrahub_anta_targets"

    require_devices = tasks_by_name["Require matching devices"]["ansible.builtin.assert"]
    assert require_devices["that"] == ["groups['infrahub_anta_targets'] | default([]) | length > 0"]

    require_inventory = tasks_by_name["Require inventory identifiers and management addresses"]
    assert require_inventory["ansible.builtin.assert"]["that"] == [
        "hostvars[item].id is defined",
        "hostvars[item].id | string | length > 0",
        "hostvars[item].ansible_host is defined",
        "hostvars[item].ansible_host | string | length > 0",
    ]


def test_credentials_support_manual_precedence_and_explicit_empty_password() -> None:
    execution_play = _playbook()[1]
    tasks_by_name = _named_tasks(execution_play, "pre_tasks")

    require_credentials = tasks_by_name["Require ANTA credentials from Semaphore or the environment"]
    credential_checks = require_credentials["ansible.builtin.assert"]["that"]
    assert "anta_user is defined" in credential_checks[0]
    assert "ANTA_USER" in credential_checks[0]
    assert "anta_password is defined" in credential_checks[1]
    assert "ANTA_PASSWORD" in credential_checks[1]
    assert "length > 0" not in credential_checks[1]
    assert require_credentials["no_log"] is True

    resolve_credentials = tasks_by_name["Resolve ANTA credentials for each target"]
    facts = resolve_credentials["ansible.builtin.set_fact"]
    assert facts["anta_user"].startswith("{{ anta_user if anta_user is defined")
    assert facts["anta_password"].startswith("{{ anta_password if anta_password is defined")
    assert resolve_credentials["no_log"] is True


def test_artifacts_are_fetched_from_main_and_rejected_when_not_populated() -> None:
    execution_play = _playbook()[1]
    tasks_by_name = _named_tasks(execution_play, "pre_tasks")

    fetch = tasks_by_name["Fetch the merged ANTA catalog from Infrahub main"]
    module = fetch["opsmill.infrahub.artifact_fetch"]
    assert module["artifact_name"] == "{{ anta_artifact_name }}"
    assert module["target_id"] == "{{ id }}"
    assert module["branch"] == "main"

    require_catalog = tasks_by_name["Require a populated ANTA catalog"]["ansible.builtin.assert"]
    assert require_catalog["that"] == [
        "anta_catalog_artifact.text is defined",
        "(anta_catalog_artifact.text | regex_search('(?m)^anta\\.tests\\.[^:]+:')) is not none",
    ]


def test_anta_role_uses_user_catalogs_and_propagates_all_failures() -> None:
    execution_play = _playbook()[1]
    outer_task = execution_play["tasks"][0]
    role_task = outer_task["block"][0]

    assert role_task["ansible.builtin.import_role"]["name"] == "arista.avd.anta_runner"
    assert role_task["vars"]["avd_catalogs_enabled"] is False
    assert role_task["vars"]["user_catalogs_enabled"] is True
    assert role_task["vars"]["anta_runner_tags"] == "{{ groups['infrahub_anta_targets'] }}"
    assert "ignore_errors" not in role_task
    assert "failed_when" not in role_task
    assert "rescue" not in outer_task

    report_task = outer_task["always"][0]
    report_values = report_task["ansible.builtin.debug"]["msg"]
    assert set(report_values) == {"summary", "json_report", "markdown_report", "csv_report"}


def test_semaphore_environment_and_compose_seed_anta_defaults() -> None:
    payload = tasks._anta_environment_payload(7, "/opt/semaphore/anta")

    assert payload["name"] == "ANTA"
    assert payload["project_id"] == 7
    assert json.loads(str(payload["json"])) == {
        "fabric_name": "",
        "anta_workspace": "/opt/semaphore/anta",
        "anta_user": "admin",
        "anta_password": "",
        "anta_enable": True,
    }

    compose = yaml.safe_load((ROOT / "docker-compose.override.yml").read_text(encoding="utf-8"))
    environment = compose["services"]["semaphore"]["environment"]
    assert "ANTA_USER" in environment and environment["ANTA_USER"] is None
    assert "ANTA_PASSWORD" in environment and environment["ANTA_PASSWORD"] is None
    forwarded = json.loads(environment["SEMAPHORE_FORWARDED_ENV_VARS"])
    assert {"ANTA_USER", "ANTA_PASSWORD"}.issubset(forwarded)
    assert "./anta:/opt/semaphore/anta" in compose["services"]["semaphore"]["volumes"]


class FakeSemaphoreClient:
    def __init__(self, resources: dict[str, list[dict[str, object]]] | None = None) -> None:
        self.resources = resources or {}
        self.created: list[tuple[str, dict[str, object]]] = []
        self.updated: list[tuple[str, dict[str, object]]] = []
        self.deleted: list[str] = []

    def find_by_name(self, list_url: str, name: str) -> dict[str, object] | None:
        return next((item for item in self.resources.get(list_url, []) if item.get("name") == name), None)

    def list_resources(self, list_url: str) -> list[dict[str, object]]:
        return self.resources.get(list_url, [])

    def find_or_create(
        self,
        list_url: str,
        _create_url: str,
        name: str,
        payload: dict[str, object],
    ) -> int:
        existing = self.find_by_name(list_url, name)
        if existing is not None:
            return int(str(existing["id"]))
        resource_id = sum(len(items) for items in self.resources.values()) + 1
        self.resources.setdefault(list_url, []).append({"id": resource_id, **payload})
        self.created.append((name, payload))
        return resource_id

    def update(self, resource_url: str, payload: dict[str, object]) -> None:
        self.updated.append((resource_url, payload))

    def delete(self, resource_url: str) -> None:
        self.deleted.append(resource_url)


def test_existing_anta_environment_is_reconciled_without_overwriting_operator_values() -> None:
    url = "/api/project/7/environment"
    api = FakeSemaphoreClient(
        {
            url: [
                {
                    "id": "42",
                    "name": "ANTA",
                    "json": json.dumps({"fabric_name": "Fabric-A", "anta_user": "operator"}),
                    "env": '{"EXISTING":"value"}',
                }
            ]
        }
    )

    assert tasks._reconcile_anta_environment(api, 7, "/opt/semaphore/anta") == 42

    resource_url, payload = api.updated[0]
    assert resource_url == f"{url}/42"
    assert payload["env"] == '{"EXISTING":"value"}'
    assert json.loads(str(payload["json"])) == {
        "fabric_name": "Fabric-A",
        "anta_workspace": "/opt/semaphore/anta",
        "anta_user": "operator",
        "anta_password": "",
        "anta_enable": True,
    }


def test_empty_environment_is_detached_and_deleted_idempotently() -> None:
    environment_url = "/api/project/7/environment"
    templates_url = "/api/project/7/templates"
    api = FakeSemaphoreClient(
        {
            environment_url: [{"id": 12, "name": "Empty"}],
            templates_url: [
                {"id": 21, "name": "Deploy", "environment_id": "12"},
                {"id": 22, "name": "Validate", "environment_id": 9},
            ],
        }
    )

    tasks._remove_empty_environment(api, 7)

    assert api.updated == [(f"{templates_url}/21", {"id": 21, "name": "Deploy", "environment_id": None})]
    assert api.deleted == [f"{environment_url}/12"]

    absent_api = FakeSemaphoreClient()
    tasks._remove_empty_environment(absent_api, 7)
    assert not absent_api.updated
    assert not absent_api.deleted


def test_init_semaphore_registers_anta_with_the_infrahub_inventory(monkeypatch: MonkeyPatch) -> None:
    api = FakeSemaphoreClient()

    class InitializableFakeSemaphoreClient(FakeSemaphoreClient):
        def __init__(self, _base_url: str) -> None:
            self.__dict__ = api.__dict__

        def wait_until_ready(self) -> None:
            pass

        def login(self, _admin: str, _password: str) -> None:
            pass

    monkeypatch.setattr(tasks, "_SemaphoreClient", InitializableFakeSemaphoreClient)
    monkeypatch.setattr(tasks, "ensure_clab_staging_dir", lambda: ROOT / "lab" / "clab-staging")
    monkeypatch.setattr(tasks, "ensure_anta_workspace_dir", lambda: ROOT / "anta")
    monkeypatch.setattr(tasks, "_semaphore_staging_host_path", lambda *_args: "/host/clab-staging")

    fake_admin_password = object()
    tasks.init_semaphore.body(Context(), password=fake_admin_password)

    resources = dict(api.created)
    resource_ids = {str(item["name"]): int(str(item["id"])) for items in api.resources.values() for item in items}
    assert "Empty" not in resources
    anta_environment = resources["ANTA"]
    assert json.loads(str(anta_environment["json"]))["anta_user"] == "admin"
    assert not json.loads(str(anta_environment["json"]))["anta_password"]

    anta_template = resources["Validate with ANTA"]
    assert anta_template["playbook"] == "test.yml"
    assert anta_template["inventory_id"] == resource_ids["Infrahub"]
    assert anta_template["environment_id"] == resource_ids["ANTA"]
    deploy_template = resources["Deploy"]
    assert deploy_template["environment_id"] is None


def test_workspace_directories_are_world_writable(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(tasks, "__file__", str(tmp_path / "tasks.py"))
    monkeypatch.setattr(tasks, "CLAB_STAGING_DIR", "clab")
    monkeypatch.setattr(tasks, "ANTA_WORKSPACE_DIR", "anta")

    staging = tasks.ensure_clab_staging_dir()
    workspace = tasks.ensure_anta_workspace_dir()

    assert staging == tmp_path / "clab"
    assert workspace == tmp_path / "anta"
    assert staging.stat().st_mode & 0o777 == 0o777
    assert workspace.stat().st_mode & 0o777 == 0o777


def test_anta_dependencies_are_pinned_to_avd_630() -> None:
    requirements = yaml.safe_load((ROOT / "ansible" / "galaxy-requirements.yml").read_text(encoding="utf-8"))
    versions = {item["name"]: str(item["version"]) for item in requirements["collections"]}

    assert versions["opsmill.infrahub"] == "1.9.0"
    assert versions["arista.avd"] == "6.3.0"
    dockerfile = (ROOT / "semaphore" / "Dockerfile").read_text(encoding="utf-8")
    assert "pip3 uninstall --yes ansible" in dockerfile
    assert '"ansible-core==2.19.13"' in dockerfile
    assert '"pyavd[ansible]==6.3.0"' in dockerfile
    assert "pip3 check" in dockerfile
    assert "ANSIBLE_COLLECTIONS_PATH=/opt/semaphore/collections:/usr/share/ansible/collections" in dockerfile
    assert "arista.avd:6.3.0" in dockerfile
