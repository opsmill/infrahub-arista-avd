import json
import os
import shlex
import sys
import time
from pathlib import Path
from time import sleep

import httpx
from invoke import Context, task

# If no version is indicated, we will take the latest
VERSION = os.getenv("INFRAHUB_IMAGE_VER", None)
CURRENT_DIRECTORY = Path(__file__).resolve()
MAIN_DIRECTORY_PATH = Path(__file__).parent

COMPOSE_FILES = "-f docker-compose.yml -f docker-compose.override.yml"
INFRAHUB_ADDRESS = os.getenv("INFRAHUB_ADDRESS", "http://localhost:8000")

os.environ.setdefault("INFRAHUB_USERNAME", "admin")
os.environ.setdefault("INFRAHUB_PASSWORD", "infrahub")
os.environ.setdefault("INFRAHUB_ADDRESS", INFRAHUB_ADDRESS)

SEMAPHORE_URL = "http://localhost:3000"
SEMAPHORE_ADMIN = "admin"
SEMAPHORE_ADMIN_PASSWORD = "semaphore"  # noqa: S105
SEMAPHORE_PLAYBOOK_PATH = "/opt/semaphore/playbooks"


@task
def build(ctx: Context, cache: bool = True) -> None:
    """
    Build the docker image.
    """
    compose_cmd = f"docker compose {COMPOSE_FILES} build"
    if not cache:
        compose_cmd += " --no-cache"
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run(compose_cmd, pty=True)


@task
def destroy(ctx: Context) -> None:
    """
    Stop and remove containers, networks, and volumes.
    """
    ctx.run(f"docker compose {COMPOSE_FILES} down -v", pty=True)


class _SemaphoreClient:
    """Thin wrapper around httpx.Client for Semaphore API calls."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=10)

    def wait_until_ready(self) -> None:
        delay = 2
        for attempt in range(1, 9):
            try:
                self._client.get("/api/ping")
                print("Semaphore is reachable.")
                return
            except httpx.HTTPError:
                print(f"Waiting for Semaphore (attempt {attempt}/8, retry in {delay}s)...")
                time.sleep(delay)
                delay = min(delay * 2, 60)
        print("ERROR: Semaphore not reachable after 8 attempts.")
        sys.exit(1)

    def login(self, admin: str, password: str) -> None:
        resp = self._client.post("/api/auth/login", json={"auth": admin, "password": password})
        if resp.status_code not in {200, 204}:
            print(f"ERROR: Login failed (status={resp.status_code}).")
            sys.exit(1)
        print("Authenticated successfully.")

    def find_or_create(
        self,
        list_url: str,
        create_url: str,
        name: str,
        payload: dict[str, object],
    ) -> int:
        """Find an existing resource by name or create it. Returns the resource id."""
        items: list[dict[str, object]] = self._client.get(list_url).json()
        for item in items:
            if item.get("name") == name:
                rid = int(str(item["id"]))
                print(f"  '{name}' already exists (id={rid}).")
                return rid

        resp = self._client.post(create_url, json=payload)
        resp.raise_for_status()
        rid = int(resp.json()["id"])
        print(f"  '{name}' created (id={rid}).")
        return rid


@task(name="init-semaphore")
def init_semaphore(
    context: Context,  # noqa: ARG001
    url: str = SEMAPHORE_URL,
    admin: str = SEMAPHORE_ADMIN,
    password: str = SEMAPHORE_ADMIN_PASSWORD,
    playbook_path: str = SEMAPHORE_PLAYBOOK_PATH,
) -> None:
    """Seed Semaphore with the project, repository, inventory, and task template.

    Fully idempotent — each resource is looked up by name before creation.
    Safe to run multiple times; existing resources are reused.
    """
    print("=== Semaphore Init ===")
    api = _SemaphoreClient(url)
    api.wait_until_ready()
    api.login(admin, password)

    print("Project...")
    project_id = api.find_or_create(
        "/api/projects",
        "/api/projects",
        "Service Catalog",
        {"name": "Service Catalog", "alert": False, "max_parallel_tasks": 0},
    )

    print("Key store...")
    key_id = api.find_or_create(
        f"/api/project/{project_id}/keys",
        f"/api/project/{project_id}/keys",
        "None",
        {"name": "None", "type": "none", "project_id": project_id},
    )

    print("Repository...")
    repo_id = api.find_or_create(
        f"/api/project/{project_id}/repositories",
        f"/api/project/{project_id}/repositories",
        "Local",
        {
            "name": "Local",
            "project_id": project_id,
            "git_url": playbook_path,
            "git_branch": "",
            "ssh_key_id": key_id,
        },
    )

    print("Inventory...")
    inv_id = api.find_or_create(
        f"/api/project/{project_id}/inventory",
        f"/api/project/{project_id}/inventory",
        "Infrahub",
        {
            "name": "Infrahub",
            "project_id": project_id,
            "inventory": "inventory.yml",
            "type": "file",
            "ssh_key_id": key_id,
        },
    )

    print("Environment...")
    env_id = api.find_or_create(
        f"/api/project/{project_id}/environment",
        f"/api/project/{project_id}/environment",
        "Empty",
        {"name": "Empty", "project_id": project_id, "json": "{}", "env": "{}"},
    )

    print("Task template...")
    api.find_or_create(
        f"/api/project/{project_id}/templates",
        f"/api/project/{project_id}/templates",
        "Deploy",
        {
            "name": "Deploy",
            "project_id": project_id,
            "repository_id": repo_id,
            "inventory_id": inv_id,
            "environment_id": env_id,
            "playbook": "deploy.yml",
            "type": "task",
            "app": "ansible",
        },
    )

    print("ContainerLab inventory...")
    # deploy_clab.yml targets localhost plus the `clab_hosts` group, not the
    # Infrahub dynamic inventory of DcimDevice objects.
    clab_inv_id = api.find_or_create(
        f"/api/project/{project_id}/inventory",
        f"/api/project/{project_id}/inventory",
        "ContainerLab",
        {
            "name": "ContainerLab",
            "project_id": project_id,
            "inventory": "inventory_clab.yml",
            "type": "file",
            "ssh_key_id": key_id,
        },
    )

    print("ContainerLab environment...")
    # The variables deploy_clab.yml needs must live in the environment, NOT in
    # survey_vars. Verified against Semaphore v2.17.12: a declared survey var is
    # recorded on the task's `params` but is never forwarded to ansible-playbook
    # as an extra var, so the playbook fails with "fabric is undefined" — with or
    # without an explicit `type` on the survey var. Only the environment's JSON
    # reaches the playbook. Override per run in the task's Environment field.
    #
    # clab_staging_dir is deliberately not the playbook's /opt/containerlab
    # default: with clab_hosts resolving to localhost, that localhost is this
    # container, which cannot write to /opt. This path is owned by the semaphore
    # user. A real deployment points clab_hosts at a ContainerLab host and
    # overrides this.
    clab_env_id = api.find_or_create(
        f"/api/project/{project_id}/environment",
        f"/api/project/{project_id}/environment",
        "ContainerLab",
        {
            "name": "ContainerLab",
            "project_id": project_id,
            "json": json.dumps(
                {
                    "fabric": "Fabric-L3LS-Multi-Domain",
                    "clab_staging_dir": f"{SEMAPHORE_PLAYBOOK_PATH.rsplit('/', 1)[0]}/clab-staging",
                }
            ),
            "env": "{}",
        },
    )

    print("ContainerLab task template...")
    api.find_or_create(
        f"/api/project/{project_id}/templates",
        f"/api/project/{project_id}/templates",
        "Deploy ContainerLab",
        {
            "name": "Deploy ContainerLab",
            "project_id": project_id,
            "repository_id": repo_id,
            "inventory_id": clab_inv_id,
            "environment_id": clab_env_id,
            "playbook": "deploy_clab.yml",
            "type": "task",
            "app": "ansible",
        },
    )

    print("=== Semaphore init complete ===")


def get_repository_sync_status(name: str) -> str | None:
    query = """
    query CheckRepoSync($name: String!) {
      CoreRepository(name__value: $name) {
        edges {
          node {
            sync_status { value }
          }
        }
      }
    }
    """
    resp = httpx.post(
        f"{INFRAHUB_ADDRESS}/graphql",
        json={"query": query, "variables": {"name": name}},
        timeout=10,
    )
    data = resp.json()
    edges = data.get("data", {}).get("CoreRepository", {}).get("edges", [])
    if not edges:
        return None
    return str(edges[0]["node"]["sync_status"]["value"])


def wait_for_repository_sync(name: str, timeout: int = 300, interval: int = 5) -> None:
    """Poll Infrahub until the named repository reaches 'in_sync' status."""
    elapsed = 0
    while elapsed < timeout:
        try:
            status = get_repository_sync_status(name)
            if status:
                print(f"Repository '{name}' sync_status: {status}")
                if status == "in-sync":
                    return
        except httpx.HTTPError as exc:
            print(f"Waiting for Infrahub API ({exc})")
        sleep(interval)
        elapsed += interval

    msg = f"Repository '{name}' did not reach 'in_sync' within {timeout}s"
    raise TimeoutError(msg)


@task(pre=[init_semaphore])
def load(ctx: Context) -> None:
    load_schema(ctx)
    load_menu(ctx)
    sleep(5)
    ctx.run("infrahubctl object load objects/")
    ctx.run("infrahubctl object load repository.yml")
    wait_for_repository_sync("test-repository")
    ctx.run("infrahubctl object load repository_checks.yml")
    ctx.run("infrahubctl object load triggers.yml")


@task
def stop(ctx: Context) -> None:
    """
    Stop containers and remove networks.
    """
    ctx.run(f"docker compose {COMPOSE_FILES} down", pty=True)


@task(help={"component": "Optional name of a specific service to restart."})
def restart(ctx: Context, component: str = "") -> None:
    """
    Restart all services or a specific one using docker-compose.
    """
    if component:
        ctx.run(f"docker compose {COMPOSE_FILES} restart {component}", pty=True)
        return

    ctx.run(f"docker compose {COMPOSE_FILES} restart", pty=True)


@task
def load_menu(ctx: Context) -> None:
    """
    Load schemas into InfraHub using infrahubctl.
    """
    ctx.run("infrahubctl menu load menus/", pty=True)


@task
def load_schema(ctx: Context) -> None:
    """
    Load schemas into InfraHub using infrahubctl.
    """
    ctx.run("infrahubctl schema load schemas", pty=True)


@task
def test(ctx: Context) -> None:
    """
    Run tests using pytest.
    """
    ctx.run("pytest tests", pty=True)


@task(
    help={
        "proposed_change_id": "Submitted proposed change ID.",
        "branch": "Destination branch containing workspace tracking.",
    }
)
def submit_cv_workspace(ctx: Context, proposed_change_id: str, branch: str = "main") -> None:
    """Manually retry CloudVision submission for a linked submitted proposed change."""
    command = (
        f"python -m checks.cv_workspace_lifecycle {shlex.quote(proposed_change_id)} --branch {shlex.quote(branch)}"
    )
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run(command, pty=True)


@task(help={"override": "Redownload the compose file even if it already exists."})
def download_compose_file(ctx: Context, override: bool = False) -> Path:  # noqa: ARG001
    """
    Download docker-compose.yml from InfraHub if missing or override is True.
    """
    compose_file = Path("./docker-compose.yml")

    if compose_file.exists() and not override:
        return compose_file

    response = httpx.get("https://infrahub.opsmill.io")
    response.raise_for_status()

    compose_file.write_text(response.content.decode(), encoding="utf-8")

    return compose_file


@task(name="format")
def format_python(ctx: Context) -> None:
    """Run RUFF to format all Python files."""

    exec_cmds = ["ruff format .", "ruff check . --fix"]
    with ctx.cd(MAIN_DIRECTORY_PATH):
        for cmd in exec_cmds:
            ctx.run(cmd, pty=True)


@task
def lint_yaml(ctx: Context) -> None:
    """Run Linter to check all Python files."""
    print(" - Check code with yamllint")
    exec_cmd = "yamllint ."
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run(exec_cmd, pty=True)


@task
def lint_mypy(ctx: Context) -> None:
    """Run Linter to check all Python files."""
    print(" - Check code with mypy")
    exec_cmd = "mypy --show-error-codes src/solution_arista_avd"
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run(exec_cmd, pty=True)


@task
def lint_ruff(ctx: Context) -> None:
    """Run Ruff lint and format checks for all Python files."""
    exec_cmds = [
        (" - Check code with ruff", "ruff check ."),
        (" - Check code formatting with ruff", "ruff format --check ."),
    ]
    with ctx.cd(MAIN_DIRECTORY_PATH):
        for message, cmd in exec_cmds:
            print(message)
            ctx.run(cmd, pty=True)


@task(name="lint")
def lint_all(ctx: Context) -> None:
    """Run all linters."""
    lint_yaml(ctx)
    lint_ruff(ctx)
    lint_mypy(ctx)


@task
def start(ctx: Context) -> None:
    """
    Start the services using docker-compose in detached mode.
    """
    ctx.run(f"docker compose {COMPOSE_FILES} up -d", pty=True)
