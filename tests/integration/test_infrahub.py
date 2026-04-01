from pathlib import Path

import pytest
from infrahub_sdk import InfrahubClient
from infrahub_sdk.protocols import CoreGenericRepository
from infrahub_sdk.testing.docker import TestInfrahubDockerClient
from infrahub_sdk.testing.repository import GitRepo


class TestInfrahub(TestInfrahubDockerClient):
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

        repo = GitRepo(
            name="local-repository",
            src_directory=root_directory,
            dst_directory=remote_repos_dir,
        )
        await repo.add_to_infrahub(client=client)
        in_sync = await repo.wait_for_sync_to_complete(client=client)
        assert in_sync

        repos = await client.all(kind=CoreGenericRepository)

        # A breakpoint can be added to pause the tests from running and keep the test containers active
        # breakpoint()

        assert repos
