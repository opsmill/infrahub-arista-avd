import os
import subprocess  # noqa: S404
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from infrahub_sdk import InfrahubClient
from infrahub_sdk.protocols import CoreGenericRepository
from infrahub_sdk.testing.docker import TestInfrahubDockerClient
from infrahub_sdk.testing.repository import GitRepo
from infrahub_testcontainers.helpers import InfrahubDockerCompose

TEST_IMAGE = "opsmill/infrahub-solution-arista-avd-integration-test"
COMPOSE_START_TIMEOUT = 300


def _run_command(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=check)  # noqa: S603


def _image_exists(image: str) -> bool:
    result = _run_command(["docker", "image", "inspect", image], check=False)
    return result.returncode == 0


def _ensure_project_image(root_directory: Path, infrahub_version: str) -> str:
    """Build a local Infrahub image that includes this repository's runtime dependencies."""
    base_version = os.environ.get("INFRAHUB_BASE_VERSION") or (
        "1.10.1" if infrahub_version == "local" else infrahub_version
    )
    image = f"{TEST_IMAGE}:{base_version}"
    if _image_exists(image):
        return image

    _run_command(
        [
            "docker",
            "build",
            "--build-arg",
            f"INFRAHUB_BASE_VERSION={base_version}",
            "--tag",
            image,
            ".",
        ],
        cwd=root_directory,
    )
    return image


def _disable_cadvisor_healthcheck(compose_file: Path) -> None:
    """Disable cAdvisor's inherited image healthcheck in the generated test compose file."""
    content = compose_file.read_text(encoding="utf-8")
    cadvisor_start = content.find("  cadvisor:\n")
    if cadvisor_start == -1:
        return

    next_service = content.find("\n  scraper:\n", cadvisor_start)
    if next_service == -1:
        return

    cadvisor_section = content[cadvisor_start:next_service]
    if "healthcheck:" in cadvisor_section:
        return

    cadvisor_section = cadvisor_section.replace(
        '    ports:\n      - "${INFRAHUB_TESTING_CADVISOR_PORT:-0}:8080"\n',
        '    ports:\n      - "${INFRAHUB_TESTING_CADVISOR_PORT:-0}:8080"\n    healthcheck:\n      disable: true\n',
    )
    compose_file.write_text(content[:cadvisor_start] + cadvisor_section + content[next_service:], encoding="utf-8")


def _compose_container_ids(project_name: str) -> list[str]:
    result = _run_command(
        [
            "docker",
            "ps",
            "--all",
            "--quiet",
            "--filter",
            f"label=com.docker.compose.project={project_name}",
        ]
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _inspect_containers(container_ids: list[str]) -> list[dict]:
    if not container_ids:
        return []
    result = _run_command(["docker", "inspect", *container_ids])
    import json

    return json.loads(result.stdout)


def _container_status(containers: list[dict]) -> str:
    lines = []
    for container in containers:
        labels = container.get("Config", {}).get("Labels") or {}
        state = container.get("State", {})
        service = labels.get("com.docker.compose.service", container.get("Name", "").lstrip("/"))
        status = state.get("Status", "unknown")
        health = state.get("Health", {}).get("Status", "no-health")
        lines.append(f"{service}: state={status} health={health}")
    return "\n".join(sorted(lines))


def _container_logs(containers: list[dict], tail: int = 80) -> str:
    logs = []
    for container in containers:
        container_id = container.get("Id")
        labels = container.get("Config", {}).get("Labels") or {}
        service = labels.get("com.docker.compose.service", container.get("Name", "").lstrip("/"))
        if not container_id:
            continue
        result = _run_command(["docker", "logs", "--tail", str(tail), container_id], check=False)
        logs.append(f"--- {service} ---\n{result.stdout}{result.stderr}")
    return "\n".join(logs)


def _wait_for_compose_project(project_name: str, timeout: int = COMPOSE_START_TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    latest_containers: list[dict] = []

    while time.monotonic() < deadline:
        container_ids = _compose_container_ids(project_name)
        if not container_ids:
            time.sleep(2)
            continue

        latest_containers = _inspect_containers(container_ids)
        bad = []
        pending = []
        for container in latest_containers:
            state = container.get("State", {})
            status = state.get("Status", "unknown")
            health = state.get("Health", {}).get("Status", "no-health")

            if status in {"dead", "exited", "removing"} or health == "unhealthy":
                bad.append(container)
            elif status != "running" or health not in {"healthy", "no-health"}:
                pending.append(container)

        if bad:
            raise RuntimeError(
                "Docker Compose project failed while starting:\n"
                f"{_container_status(latest_containers)}\n\n"
                f"{_container_logs(bad)}"
            )
        if not pending:
            return
        time.sleep(5)

    raise TimeoutError(
        "Timed out waiting for Docker Compose project to become healthy:\n"
        f"{_container_status(latest_containers)}\n\n"
        f"{_container_logs(latest_containers)}"
    )


def _start_compose(compose: InfrahubDockerCompose) -> None:
    base_cmd = compose.compose_command_property[:]
    if compose.pull:
        compose._run_command(cmd=[*base_cmd, "pull"])

    up_cmd = [*base_cmd, "up"]
    if compose.build:
        up_cmd.append("--build")
    up_cmd.extend(["--wait", "--wait-timeout", str(COMPOSE_START_TIMEOUT)])
    if compose.services:
        up_cmd.extend(compose.services)

    try:
        compose._run_command(cmd=up_cmd)
    except subprocess.CalledProcessError:
        _wait_for_compose_project(project_name=compose.project_name or "", timeout=COMPOSE_START_TIMEOUT)


class TestInfrahub(TestInfrahubDockerClient):
    @pytest.fixture(scope="class")
    def infrahub_compose(
        self,
        tmp_directory: Path,
        remote_repos_dir: Path,  # initialize repository before docker compose to fix permissions issues
        remote_backups_dir: Path,
        infrahub_version: str,
        deployment_type: str | None,
    ) -> InfrahubDockerCompose:
        root_directory = Path(__file__).parent.parent.parent
        image = _ensure_project_image(root_directory=root_directory, infrahub_version=infrahub_version)
        image_name, image_version = image.rsplit(":", maxsplit=1)

        previous_env = {
            key: os.environ.get(key)
            for key in [
                "INFRAHUB_TESTING_DOCKER_IMAGE",
                "INFRAHUB_TESTING_IMAGE_VER",
                "INFRAHUB_TESTING_DOCKER_PULL",
            ]
        }
        os.environ["INFRAHUB_TESTING_DOCKER_IMAGE"] = image_name
        os.environ["INFRAHUB_TESTING_IMAGE_VER"] = image_version
        os.environ["INFRAHUB_TESTING_DOCKER_PULL"] = "false"
        try:
            compose = InfrahubDockerCompose.init(
                directory=tmp_directory,
                version=image_version,
                deployment_type=deployment_type,
            )
        finally:
            for key, value in previous_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        _disable_cadvisor_healthcheck(Path(compose.context) / "docker-compose.yml")
        return compose

    @pytest.fixture(scope="class")
    def infrahub_app(
        self, request: pytest.FixtureRequest, infrahub_compose: InfrahubDockerCompose
    ) -> Generator[dict[str, int], None, None]:
        tests_failed_before_class = request.session.testsfailed

        try:
            _start_compose(infrahub_compose)
        except Exception as exc:
            stdout, stderr = infrahub_compose.get_logs()
            raise RuntimeError(f"Failed to start docker compose:\nStdout:\n{stdout}\nStderr:\n{stderr}") from exc

        yield infrahub_compose.get_services_port()

        tests_failed_during_class = request.session.testsfailed - tests_failed_before_class
        if tests_failed_during_class > 0:
            stdout, stderr = infrahub_compose.get_logs("infrahub-server", "task-worker")
            import warnings

            warnings.warn(
                f"Container logs:\nStdout:\n{stdout}\nStderr:\n{stderr}",
                stacklevel=2,
            )
        infrahub_compose.stop()

    @pytest.mark.asyncio
    async def test_load_schema(self, default_branch: str, client: InfrahubClient, schemas: list[dict]) -> None:
        await client.schema.wait_until_converged(branch=default_branch)

        resp = await client.schema.load(schemas=schemas, branch=default_branch, wait_until_converged=True)
        await client.schema.wait_until_converged(branch=default_branch)
        assert resp.errors == {}

    @pytest.mark.asyncio
    async def test_load_objects(
        self,
        default_branch: str,
        client: InfrahubClient,
        schemas: list[dict],
        infrahub_port: int,
    ) -> None:
        """Load schemas then load all object files via infrahubctl object load."""
        await client.schema.wait_until_converged(branch=default_branch)

        resp = await client.schema.load(schemas=schemas, branch=default_branch, wait_until_converged=True)
        assert resp.errors == {}, f"Schema load errors: {resp.errors}"
        await client.schema.wait_until_converged(branch=default_branch)

        infrahub_address = f"http://localhost:{infrahub_port}"
        result = self.execute_command(
            address=infrahub_address,
            command="infrahubctl object load objects/",
        )
        print(result.stdout, flush=True)
        if result.stderr:
            print(result.stderr, flush=True)
        assert result.returncode == 0, f"infrahubctl object load failed:\n{result.stdout}\n{result.stderr}"

        # Verify key objects were created with the new kind names
        manufacturers = await client.all(kind="OrganizationManufacturer")
        assert len(manufacturers) > 0, "No manufacturers loaded"

        device_types = await client.all(kind="DcimDeviceType")
        assert len(device_types) > 0, "No device types loaded"

    @pytest.mark.asyncio
    async def test_load_repository(
        self,
        client: InfrahubClient,
        remote_repos_dir: Path,
        root_directory: Path,
    ) -> None:
        """Add the local directory as a repository in Infrahub and wait for the import to be complete"""
        git_config_global = remote_repos_dir.parent / "gitconfig"
        git_config_global.write_text("[commit]\n\tgpgSign = false\n[tag]\n\tgpgSign = false\n", encoding="utf-8")
        previous_git_config_global = os.environ.get("GIT_CONFIG_GLOBAL")
        os.environ["GIT_CONFIG_GLOBAL"] = str(git_config_global)

        try:
            repo = GitRepo(
                name="local-repository",
                src_directory=root_directory,
                dst_directory=remote_repos_dir,
            )
            await repo.add_to_infrahub(client=client)
            in_sync = await repo.wait_for_sync_to_complete(client=client)
        finally:
            if previous_git_config_global is None:
                os.environ.pop("GIT_CONFIG_GLOBAL", None)
            else:
                os.environ["GIT_CONFIG_GLOBAL"] = previous_git_config_global
        assert in_sync

        repos = await client.all(kind=CoreGenericRepository)

        # A breakpoint can be added to pause the tests from running and keep the test containers active
        # breakpoint()

        assert repos
