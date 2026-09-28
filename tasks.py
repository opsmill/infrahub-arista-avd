import json
import os
import secrets
import shlex
import shutil
import sys
import time
from pathlib import Path
from time import sleep
from uuid import uuid4

import httpx
from dotenv import dotenv_values, load_dotenv, set_key, unset_key
from invoke import Context, task
from invoke.exceptions import Exit

CURRENT_DIRECTORY = Path(__file__).resolve()
MAIN_DIRECTORY_PATH = Path(__file__).parent
ENV_FILE_PATH = MAIN_DIRECTORY_PATH / ".env"


def _load_environment(env_path: Path) -> None:
    """Load an environment file without replacing exported shell values."""
    load_dotenv(env_path, override=False)


_load_environment(ENV_FILE_PATH)

# If no version is indicated, we will take the latest
VERSION = os.getenv("INFRAHUB_IMAGE_VER", None)

COMPOSE_FILES = "-f docker-compose.yml -f docker-compose.override.yml"
INFRAHUB_ADDRESS = os.getenv("INFRAHUB_ADDRESS", "http://localhost:8000")
COMPOSE_REQUIRED_SECRET_NAMES = (
    "INFRAHUB_INITIAL_ADMIN_PASSWORD",
    "INFRAHUB_API_TOKEN",
    "INFRAHUB_SECURITY_SECRET_KEY",
    "SEMAPHORE_ADMIN_PASSWORD",
)
COMPOSE_LIFECYCLE_PLACEHOLDER = "unused-for-compose-lifecycle"

os.environ.setdefault("INFRAHUB_USERNAME", "admin")
if admin_password := os.getenv("INFRAHUB_INITIAL_ADMIN_PASSWORD"):
    os.environ.setdefault("INFRAHUB_PASSWORD", admin_password)
os.environ.setdefault("INFRAHUB_ADDRESS", INFRAHUB_ADDRESS)

SEMAPHORE_URL = "http://localhost:3000"
SEMAPHORE_ADMIN = "admin"
SEMAPHORE_ADMIN_PASSWORD = os.getenv("SEMAPHORE_ADMIN_PASSWORD")
SEMAPHORE_PLAYBOOK_PATH = "/opt/semaphore/playbooks"
# Host path bind-mounted into the Semaphore container as the ContainerLab
# staging directory, so files deploy_clab.yml pulls are reachable from the host.
CLAB_STAGING_DIR = "lab/clab-staging"
ANTA_WORKSPACE_DIR = "anta"
ANTA_CONTAINER_WORKSPACE = "/opt/semaphore/anta"

# Markdown authored by this project. Vendored agent content (.agents, .claude,
# .specify), spec-kit process artifacts (specs/), and PyAVD-rendered output
# (lab/avd) are excluded in [tool.rumdl]; these paths are what remains.
# CLAUDE.md is omitted because it symlinks to AGENTS.md.
MARKDOWN_PATHS = "README.md AGENTS.md docs/ lab/README.md schemas/"

# Prose linting covers the published documentation tree only.
PROSE_PATHS = "docs/docs"

# Pinned so local runs match the CI job. Vale ships as a Go binary with no PyPI
# distribution, so it cannot be a uv dev dependency like the other linters.
VALE_VERSION = "3.17.1"


def _initialize_secrets(env_path: Path) -> tuple[str, ...]:
    """Generate missing local credentials while preserving existing assignments."""
    existing = dotenv_values(env_path) if env_path.exists() else {}
    legacy_initial_token = existing.get("INFRAHUB_INITIAL_ADMIN_TOKEN")
    api_token = existing.get("INFRAHUB_API_TOKEN") or legacy_initial_token or str(uuid4())

    required_values = {
        "INFRAHUB_INITIAL_ADMIN_PASSWORD": lambda: secrets.token_urlsafe(32),
        "INFRAHUB_API_TOKEN": lambda: api_token,
        "INFRAHUB_SECURITY_SECRET_KEY": lambda: str(uuid4()),
        "SEMAPHORE_ADMIN_PASSWORD": lambda: secrets.token_urlsafe(32),
    }
    missing = tuple(name for name in required_values if not existing.get(name))

    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        env_path.touch(mode=0o600)
    for name in missing:
        set_key(env_path, name, required_values[name](), quote_mode="never")
    if "INFRAHUB_INITIAL_ADMIN_TOKEN" in existing:
        unset_key(env_path, "INFRAHUB_INITIAL_ADMIN_TOKEN", quote_mode="never")
    env_path.chmod(0o600)
    _load_environment(env_path)
    return missing


def _compose_lifecycle_environment() -> dict[str, str]:
    """Satisfy Compose interpolation for commands that never consume credentials."""
    return {name: os.environ.get(name) or COMPOSE_LIFECYCLE_PLACEHOLDER for name in COMPOSE_REQUIRED_SECRET_NAMES}


@task(name="init-secrets")
def init_secrets(_context: Context) -> None:
    """Create strong missing credentials in the ignored local .env file."""
    generated = _initialize_secrets(ENV_FILE_PATH)
    if generated:
        print(f"Generated {len(generated)} missing credential assignments in .env.")
    else:
        print("No credentials generated; existing .env values were preserved.")
    print("Protected .env with mode 0600. Credential values were not displayed.")


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
    ctx.run(
        f"docker compose {COMPOSE_FILES} down -v",
        pty=True,
        env=_compose_lifecycle_environment(),
    )


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
        item = self.find_by_name(list_url, name)
        if item is not None:
            rid = int(str(item["id"]))
            print(f"  '{name}' already exists (id={rid}).")
            return rid

        resp = self._client.post(create_url, json=payload)
        resp.raise_for_status()
        rid = int(resp.json()["id"])
        print(f"  '{name}' created (id={rid}).")
        return rid

    def find_by_name(self, list_url: str, name: str) -> dict[str, object] | None:
        """Return one named Semaphore resource, if present."""
        items: list[dict[str, object]] = self._client.get(list_url).json()
        return next((item for item in items if item.get("name") == name), None)

    def list_resources(self, list_url: str) -> list[dict[str, object]]:
        """Return all resources from a Semaphore project endpoint."""
        return self._client.get(list_url).json()

    def update(self, resource_url: str, payload: dict[str, object]) -> None:
        """Replace one Semaphore resource with a reconciled payload."""
        resp = self._client.put(resource_url, json=payload)
        resp.raise_for_status()

    def delete(self, resource_url: str) -> None:
        """Delete one Semaphore resource."""
        resp = self._client.delete(resource_url)
        resp.raise_for_status()


def _anta_environment_payload(project_id: int, workspace: str) -> dict[str, object]:
    """Build the default Semaphore environment used by ANTA runs."""
    return {
        "name": "ANTA",
        "project_id": project_id,
        "json": json.dumps(
            {
                "fabric_name": "",
                "anta_workspace": workspace,
                "anta_user": "admin",
                "anta_password": "",
                "anta_enable": True,
            }
        ),
        "env": "{}",
    }


def _reconcile_anta_environment(api: _SemaphoreClient, project_id: int, workspace: str) -> int:
    """Create or update ANTA defaults while preserving operator overrides."""
    list_url = f"/api/project/{project_id}/environment"
    existing = api.find_by_name(list_url, "ANTA")
    if existing is None:
        return api.find_or_create(list_url, list_url, "ANTA", _anta_environment_payload(project_id, workspace))

    try:
        variables = json.loads(str(existing.get("json") or "{}"))
    except json.JSONDecodeError as error:
        msg = "Semaphore environment 'ANTA' contains invalid JSON"
        raise ValueError(msg) from error
    if not isinstance(variables, dict):
        msg = "Semaphore environment 'ANTA' JSON must be an object"
        raise TypeError(msg)

    variables["anta_workspace"] = workspace
    variables.setdefault("fabric_name", "")
    variables.setdefault("anta_user", "admin")
    variables.setdefault("anta_password", "")
    variables.setdefault("anta_enable", True)

    environment_id = int(str(existing["id"]))
    payload = _anta_environment_payload(project_id, workspace)
    payload["json"] = json.dumps(variables)
    payload["env"] = str(existing.get("env") or "{}")
    api.update(f"{list_url}/{environment_id}", payload)
    print(f"  'ANTA' reconciled (id={environment_id}).")
    return environment_id


def _reconcile_template(
    api: _SemaphoreClient,
    project_id: int,
    name: str,
    payload: dict[str, object],
) -> int:
    """Create a template or update it without discarding unmodelled fields."""
    list_url = f"/api/project/{project_id}/templates"
    existing = api.find_by_name(list_url, name)
    if existing is None:
        return api.find_or_create(list_url, list_url, name, payload)

    template_id = int(str(existing["id"]))
    api.update(f"{list_url}/{template_id}", {**existing, **payload})
    print(f"  '{name}' reconciled (id={template_id}).")
    return template_id


def _remove_empty_environment(api: _SemaphoreClient, project_id: int) -> None:
    """Detach and delete the obsolete Semaphore environment named Empty."""
    environments_url = f"/api/project/{project_id}/environment"
    empty_environment = api.find_by_name(environments_url, "Empty")
    if empty_environment is None:
        return

    empty_id = int(str(empty_environment["id"]))
    templates_url = f"/api/project/{project_id}/templates"
    for template in api.list_resources(templates_url):
        environment_id = template.get("environment_id")
        if environment_id is None or int(str(environment_id)) != empty_id:
            continue
        template_id = int(str(template["id"]))
        api.update(f"{templates_url}/{template_id}", {**template, "environment_id": None})
        print(f"  '{template.get('name', template_id)}' detached from 'Empty'.")

    api.delete(f"{environments_url}/{empty_id}")
    print(f"  'Empty' deleted (id={empty_id}).")


def ensure_clab_staging_dir() -> Path:
    """Create the ContainerLab staging directory the Semaphore container writes to.

    docker-compose.override.yml bind-mounts this into the container, so the files
    deploy_clab.yml pulls land on the host instead of a container layer that is
    discarded on recreate.

    It must exist *before* the container is created, and must be writable by both
    the container's uid and the host user's, which differ. Getting either wrong
    fails without naming the cause:

      - absent at container start: Docker creates it owned by root, and the
        staging write fails with EACCES.
      - mode 0755: the same EACCES, because the container's uid is not the owner.
      - deleted while the container runs: the container keeps a stale mountpoint
        and every path under it fails with ENOENT, which takes a container
        recreate to fix - and that discards Semaphore's sqlite state.

    Called from both `start` and `init-semaphore` so the ordering holds either
    way. Staging inside the lab/ mount instead was tried and does not work: a
    writable bind mount still obeys POSIX permissions, so the container cannot
    mkdir inside a host directory it does not own.
    """
    staging_dir = Path(__file__).parent / CLAB_STAGING_DIR
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_dir.chmod(0o777)
    print(f"Staging directory {CLAB_STAGING_DIR} ready (mode 0777, shared with the Semaphore container).")
    return staging_dir


def ensure_anta_workspace_dir() -> Path:
    """Create the host directory persisted at /opt/semaphore/anta."""
    workspace_dir = Path(__file__).parent / ANTA_WORKSPACE_DIR
    workspace_dir.mkdir(parents=True, exist_ok=True)
    workspace_dir.chmod(0o777)
    print(f"ANTA workspace {ANTA_WORKSPACE_DIR} ready (mode 0777, shared with the Semaphore container).")
    return workspace_dir


def _semaphore_staging_host_path(context: Context, container_path: str) -> str:
    """Host path backing the Semaphore container's staging directory.

    Asks Docker for the real bind source rather than assuming it matches this
    checkout. They diverge whenever the stack was started from a different
    directory — a git worktree being the obvious case — and a wrong path here is
    worse than none, because it sends people to an empty directory that looks
    like a failed run.
    """
    fallback = str((Path(__file__).parent / CLAB_STAGING_DIR).resolve())
    fmt = "{{range .Mounts}}{{if eq .Destination " + f'"{container_path}"' + "}}{{.Source}}{{end}}{{end}}"
    result = context.run(
        f"docker inspect $(docker ps -q --filter name=semaphore | head -1) --format '{fmt}'",
        hide=True,
        warn=True,
    )
    if result and result.ok and result.stdout.strip():
        return str(result.stdout.strip())
    return fallback


@task(name="init-semaphore")
def init_semaphore(
    context: Context,
    url: str = SEMAPHORE_URL,
    admin: str = SEMAPHORE_ADMIN,
    password: str | None = SEMAPHORE_ADMIN_PASSWORD,
    playbook_path: str = SEMAPHORE_PLAYBOOK_PATH,
) -> None:
    """Seed Semaphore with the project, repository, inventory, and task template.

    Fully idempotent — each resource is looked up by name before creation.
    Safe to run multiple times; existing resources are reused.
    """
    if not password:
        raise Exit("SEMAPHORE_ADMIN_PASSWORD is required; run 'uv run invoke init-secrets' first.")

    print("=== Semaphore Init ===")
    ensure_clab_staging_dir()
    ensure_anta_workspace_dir()

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

    print("Task template...")
    _reconcile_template(
        api,
        project_id,
        "Deploy",
        {
            "name": "Deploy",
            "project_id": project_id,
            "repository_id": repo_id,
            "inventory_id": inv_id,
            "environment_id": None,
            "playbook": "deploy.yml",
            "type": "task",
            "app": "ansible",
        },
    )

    print("ANTA environment...")
    anta_env_id = _reconcile_anta_environment(api, project_id, ANTA_CONTAINER_WORKSPACE)

    print("ANTA task template...")
    _reconcile_template(
        api,
        project_id,
        "Validate with ANTA",
        {
            "name": "Validate with ANTA",
            "project_id": project_id,
            "repository_id": repo_id,
            "inventory_id": inv_id,
            "environment_id": anta_env_id,
            "playbook": "test.yml",
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
    clab_container_staging = f"{SEMAPHORE_PLAYBOOK_PATH.rsplit('/', 1)[0]}/clab-staging"
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
                    "clab_staging_dir": clab_container_staging,
                    # Reported back by the playbook so a run tells you where the
                    # files are on the Docker host, not just inside the container.
                    "clab_staging_host_dir": _semaphore_staging_host_path(context, clab_container_staging),
                }
            ),
            "env": "{}",
        },
    )

    print("ContainerLab task template...")
    # Runs with --skip-tags deploy, so Semaphore fetches the artifacts, stages
    # every file the topology references, and validates them - but does not run
    # `containerlab deploy`. That step cannot work from here: this container has
    # no containerlab binary and no Docker socket, so an unskipped run always
    # ends on the "containerlab is not on PATH" assertion.
    #
    # To deploy, point clab_hosts (ansible/inventory_clab.yml) at a ContainerLab
    # host reachable over SSH and clear the arguments below, or run
    # `make -C lab deploy-from-infrahub FABRIC=<name>` from a checkout.
    api.find_or_create(
        f"/api/project/{project_id}/templates",
        f"/api/project/{project_id}/templates",
        "Fetch ContainerLab Files",
        {
            "name": "Fetch ContainerLab Files",
            "project_id": project_id,
            "repository_id": repo_id,
            "inventory_id": clab_inv_id,
            "environment_id": clab_env_id,
            "playbook": "deploy_clab.yml",
            "type": "task",
            "app": "ansible",
            "arguments": json.dumps(["--skip-tags", "deploy"]),
            "allow_override_args_in_task": True,
        },
    )

    print("Obsolete environment cleanup...")
    _remove_empty_environment(api, project_id)

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
    ctx.run(
        f"docker compose {COMPOSE_FILES} down",
        pty=True,
        env=_compose_lifecycle_environment(),
    )


@task(help={"component": "Optional name of a specific service to restart."})
def restart(ctx: Context, component: str = "") -> None:
    """
    Restart all services or a specific one using docker-compose.
    """
    if component:
        ctx.run(
            f"docker compose {COMPOSE_FILES} restart {component}",
            pty=True,
            env=_compose_lifecycle_environment(),
        )
        return

    ctx.run(
        f"docker compose {COMPOSE_FILES} restart",
        pty=True,
        env=_compose_lifecycle_environment(),
    )


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


@task
def docs(ctx: Context) -> None:
    """Build the documentation site."""
    print(" - Build the Docusaurus site")
    exec_cmds = ["pnpm install --frozen-lockfile", "pnpm run build"]
    with ctx.cd(MAIN_DIRECTORY_PATH / "docs"):
        for cmd in exec_cmds:
            ctx.run(cmd, pty=True)


@task(name="format")
def format_python(ctx: Context) -> None:
    """Run RUFF to format all Python files."""

    exec_cmds = ["ruff format .", "ruff check . --fix", f"rumdl fmt {MARKDOWN_PATHS}"]
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


@task
def lint_markdown(ctx: Context) -> None:
    """Run Linter to check authored Markdown files."""
    print(" - Check Markdown with rumdl")
    exec_cmd = f"rumdl check {MARKDOWN_PATHS}"
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run(exec_cmd, pty=True)


@task
def lint_prose(ctx: Context) -> None:
    """Run Linter to check documentation prose."""
    print(" - Check prose with Vale")
    if not shutil.which("vale"):
        # Vale is a Go binary with no PyPI distribution, so `uv sync` cannot
        # provide it. Skip rather than fail, so contributors without it can still
        # run the rest of the suite; CI installs it and remains the gate.
        print(
            f"   skipped: vale not found on PATH. Install v{VALE_VERSION} from "
            "https://github.com/errata-ai/vale/releases, then run `vale sync`."
        )
        return
    with ctx.cd(MAIN_DIRECTORY_PATH):
        ctx.run("vale sync", pty=True)
        ctx.run(f"vale {PROSE_PATHS}", pty=True)


@task(name="lint")
def lint_all(ctx: Context) -> None:
    """Run all linters."""
    lint_yaml(ctx)
    lint_ruff(ctx)
    lint_mypy(ctx)
    lint_markdown(ctx)
    lint_prose(ctx)


@task
def start(ctx: Context) -> None:
    """
    Start the services using docker-compose in detached mode.
    """
    # Before compose creates the containers: a bind-mount source that does not
    # exist yet is created by Docker as root, which the Semaphore container then
    # cannot write to.
    ensure_clab_staging_dir()
    ensure_anta_workspace_dir()
    ctx.run(f"docker compose {COMPOSE_FILES} up -d", pty=True)
