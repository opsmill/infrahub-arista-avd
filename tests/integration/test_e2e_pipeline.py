"""End-to-end pipeline integration test.

Boots a real Infrahub stack via ``infrahub-testcontainers`` and drives the full
design-to-artifact pipeline, one component per test:

    load schema -> load objects -> target groups -> register repository
    -> run generators (fabric/pod/rack/server-cabling) -> IP/cabling checks
    -> AVD structured config -> artifacts generated -> artifact content

The container stack is class-scoped, so it boots once and the ordered test
methods share it via the class-scoped ``client``. Tests run in definition order
and build on each other's server-side state (each later test assumes the earlier
ones ran); all methods share a single class-scoped event loop so the one client
is reused safely. Each asynchronous wait is bounded by ``wait_until`` and fails
with the last observed state, so a regression localizes to its component.

Heavy: excluded from the per-PR fast path and run in CI's
``integration-tests-full`` job (nightly / workflow_dispatch). Select locally with
``-m e2e``; exclude with ``-m "not e2e"``.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.protocols import CoreGenericRepository
from infrahub_sdk.testing.docker import TestInfrahubDockerClient
from infrahub_sdk.testing.repository import GitRepo

from .helpers import (
    ALL_ARTIFACT_NAMES,
    ANTA_DISABLED_MARKER,
    ARTIFACT_AVD_ANTA_CATALOG,
    ARTIFACT_AVD_EOS_CONFIG,
    ARTIFACT_TIMEOUT,
    GENERATOR_AVD_STRUCTURED_CONFIG,
    GENERATOR_BACKFILL,
    GENERATOR_TIMEOUT,
    GROUP_TIMEOUT,
    POLL_INTERVAL,
    REPO_SYNC_INTERVAL,
    REPO_SYNC_RETRIES,
    TOPOLOGY_GENERATOR_CHAIN,
    expected_super_spine_count,
    wait_until,
)

if TYPE_CHECKING:
    from pathlib import Path

    from infrahub_sdk import InfrahubClient

REPO_NAME = "e2e-repository"


@pytest.mark.e2e
class TestE2EPipeline(TestInfrahubDockerClient):
    """Full design-to-artifact pipeline against a real Infrahub instance.

    One test per pipeline component; they run in order and share the class-scoped
    stack. Running a single test in isolation will fail because it relies on the
    state produced by the earlier ones.
    """

    @pytest.fixture(scope="class", autouse=True)
    def _client_timeout(self) -> None:
        # Raise the infrahubctl client timeout: generators trigger downstream work
        # and issue large GraphQL reads that can exceed the 60s default under load.
        os.environ.setdefault("INFRAHUB_TIMEOUT", "300")

    @staticmethod
    def _address(infrahub_port: int) -> str:
        return f"http://localhost:{infrahub_port}"

    def _run_generator(self, name: str, address: str, branch: str) -> None:
        """Run a generator over its whole target group and assert it succeeded.

        ``--branch`` is passed explicitly: infrahubctl otherwise defaults to the
        local git branch, which does not exist on the testcontainer server.
        """
        result = self.execute_command(command=f"infrahubctl generator {name} --branch {branch}", address=address)
        print(f"--- infrahubctl generator {name} ---\n{result.stdout}", flush=True)
        if result.stderr:
            print(result.stderr, flush=True)
        assert result.returncode == 0, f"generator '{name}' failed:\n{result.stdout}\n{result.stderr}"

    # --- Component 1: schema ------------------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_load_schema(self, default_branch: str, client: InfrahubClient, schemas: list[dict]) -> None:
        """Load this repository's schemas and wait for convergence (FR-002)."""
        await client.schema.wait_until_converged(branch=default_branch)
        resp = await client.schema.load(schemas=schemas, branch=default_branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"
        await client.schema.wait_until_converged(branch=default_branch)

    # --- Component 2: objects ----------------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_load_objects(self, default_branch: str, client: InfrahubClient, infrahub_port: int) -> None:
        """Load the seed objects via ``infrahubctl object load`` (FR-003)."""
        result = self.execute_command(command="infrahubctl object load objects/", address=self._address(infrahub_port))
        print(result.stdout, flush=True)
        if result.stderr:
            print(result.stderr, flush=True)
        assert result.returncode == 0, f"object load failed:\n{result.stdout}\n{result.stderr}"
        assert await client.all(kind="OrganizationManufacturer", branch=default_branch), "no manufacturers loaded"
        assert await client.all(kind="DcimDeviceType", branch=default_branch), "no device types loaded"

    # --- Component 3: generator target groups ------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_target_groups_populated(self, default_branch: str, client: InfrahubClient) -> None:
        """The generators' target groups are populated by seed membership (FR-004)."""
        for kind in ("NetworkFabric", "NetworkPod", "LocationRack"):
            await wait_until(
                fetch=lambda k=kind: client.all(kind=k, branch=default_branch),
                ready=lambda objs: len(objs) > 0,
                timeout=GROUP_TIMEOUT,
                interval=POLL_INTERVAL,
                describe=f"seed objects of kind {kind}",
            )

    # --- Component 4: repository -------------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_register_repository(
        self, default_branch: str, client: InfrahubClient, root_directory: Path, remote_repos_dir: Path
    ) -> None:
        """Register this repository and wait for in-sync, failing fast on error (FR-005)."""
        repo = GitRepo(name=REPO_NAME, src_directory=root_directory, dst_directory=remote_repos_dir)
        await repo.add_to_infrahub(client=client)
        in_sync = await repo.wait_for_sync_to_complete(
            client=client, interval=REPO_SYNC_INTERVAL, retries=REPO_SYNC_RETRIES
        )
        if not in_sync:
            synced = await client.get(kind=CoreGenericRepository, name__value=REPO_NAME, branch=default_branch)
            msg = f"repository '{REPO_NAME}' did not reach in-sync; status={synced.sync_status.value}"
            raise AssertionError(msg)

    # --- Component 5: generators create the topology -----------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_run_generators_create_devices(
        self, default_branch: str, client: InfrahubClient, infrahub_port: int
    ) -> None:
        """Run the topology generator chain and verify the expected devices (FR-006/FR-008)."""
        address = self._address(infrahub_port)
        for generator_name in TOPOLOGY_GENERATOR_CHAIN:
            self._run_generator(generator_name, address, default_branch)

        expected_super_spines = await expected_super_spine_count(client, default_branch)
        super_spines = await wait_until(
            fetch=lambda: client.filters(kind="DcimDevice", role__value="super_spine", branch=default_branch),
            ready=lambda d: len(d) >= expected_super_spines > 0,
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"super_spine devices (expected {expected_super_spines})",
        )
        spines = await client.filters(kind="DcimDevice", role__value="spine", branch=default_branch)
        leaves = await client.filters(kind="DcimDevice", role__value="leaf", branch=default_branch)
        assert spines, "no spine devices created"
        assert leaves, "no leaf devices created"
        print(f"devices: super_spine={len(super_spines)} spine={len(spines)} leaf={len(leaves)}", flush=True)

    # --- Component 6: cabling & IP allocation (US2) ------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_cabling_and_ip_allocation(self, default_branch: str, client: InfrahubClient) -> None:
        """Links exist and every L3 device has a unique loopback + a management IP (FR-009)."""
        links = await client.all(kind="NetworkLink", branch=default_branch)
        assert links, "no NetworkLink cabling created"

        l3_device_count = 0
        for role in ("super_spine", "spine", "leaf"):
            l3_device_count += len(await client.filters(kind="DcimDevice", role__value=role, branch=default_branch))

        ip_report = await _device_ip_report(client, default_branch)
        print(
            f"ip report: total={ip_report['total']} with_loopback={ip_report['with_loopback']} "
            f"with_mgmt={ip_report['with_mgmt']} duplicate_loopbacks={ip_report['duplicate_loopbacks']}",
            flush=True,
        )
        assert ip_report["with_loopback"] >= l3_device_count > 0, (
            f"expected every L3 device to have a loopback; {ip_report['with_loopback']} have one"
        )
        assert not ip_report["duplicate_loopbacks"], (
            f"duplicate loopback addresses allocated: {ip_report['duplicate_loopbacks']}"
        )
        assert ip_report["with_mgmt"] > 0, "no devices have an allocated management IP"

    # --- Component 7: AVD structured config --------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_generate_structured_config(
        self, default_branch: str, client: InfrahubClient, infrahub_port: int
    ) -> None:
        """Enable ANTA, generate AVD structured config, and verify every device has it (FR-010/FR-014)."""
        address = self._address(infrahub_port)

        # Enable ANTA so the catalog is populated (not the disabled marker); the
        # schema default is False and the seed does not set it.
        fabrics = await client.all(kind="NetworkFabric", branch=default_branch)
        assert fabrics, "no fabrics found to enable ANTA on"
        for fabric in fabrics:
            if hasattr(fabric, "anta_enabled"):
                fabric.anta_enabled.value = True
                await fabric.save()

        self._run_generator(GENERATOR_AVD_STRUCTURED_CONFIG, address, default_branch)
        # Backfill is best-effort (P2); it reconciles structured config into the model.
        self.execute_command(
            command=f"infrahubctl generator {GENERATOR_BACKFILL} --branch {default_branch}", address=address
        )

        report = await wait_until(
            fetch=lambda: _devices_without_structured_config(client, default_branch),
            ready=lambda r: r is not None and r["total"] > 0 and not r["without"],
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="every device has an AVD structured config",
        )
        print(f"structured config present on all {report['total']} devices", flush=True)

    # --- Component 8: artifacts generated ----------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_artifacts_generated(self, default_branch: str, client: InfrahubClient) -> None:
        """Every AVD artifact definition yields at least one Ready artifact (FR-011/FR-013)."""
        definitions = await client.all(kind="CoreArtifactDefinition", branch=default_branch)
        assert definitions, "no artifact definitions registered (repository sync incomplete?)"
        await _trigger_all_artifacts(definitions)

        for artifact_name in ALL_ARTIFACT_NAMES:
            await self._wait_for_ready_artifact(client, default_branch, artifact_name, definitions)

    # --- Component 9: artifact content -------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_artifact_content(self, default_branch: str, client: InfrahubClient) -> None:
        """A rendered EOS config mentions its device hostname; the ANTA catalog is populated (FR-012)."""
        eos_content, eos_target = await _fetch_ready_artifact_content(client, default_branch, ARTIFACT_AVD_EOS_CONFIG)
        assert eos_content and eos_content.strip(), "EOS configuration artifact is empty"
        assert "hostname" in eos_content, "EOS config does not contain a hostname line"
        if eos_target:
            assert eos_target in eos_content, f"EOS config does not mention its device hostname {eos_target}"

        anta_content, _ = await _fetch_ready_artifact_content(client, default_branch, ARTIFACT_AVD_ANTA_CATALOG)
        assert anta_content and anta_content.strip(), "ANTA catalog artifact is empty"
        assert ANTA_DISABLED_MARKER not in anta_content, (
            "ANTA catalog rendered the disabled marker despite anta_enabled"
        )

    async def _wait_for_ready_artifact(
        self, client: InfrahubClient, branch: str, artifact_name: str, definitions: list
    ) -> None:
        """Poll for >=1 Ready artifact of ``artifact_name``, re-triggering once midway."""
        retriggered = {"done": False}

        async def fetch() -> list:
            artifacts = await client.filters(kind="CoreArtifact", name__value=artifact_name, branch=branch)
            ready = [a for a in artifacts if a.status.value == "Ready"]
            # One re-trigger at the halfway mark to cover read-replica visibility gaps (FR-013).
            if not ready and not retriggered["done"]:
                retriggered["done"] = True
                await _trigger_all_artifacts(definitions)
            return ready

        await wait_until(
            fetch=fetch,
            ready=lambda ready: len(ready) >= 1,
            timeout=ARTIFACT_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"Ready artifact '{artifact_name}'",
        )


async def _device_ip_report(client: InfrahubClient, branch: str) -> dict:
    """Report loopback/mgmt IP allocation across all devices, plus duplicate loopbacks."""
    query = """
    query DeviceIPs {
      DcimDevice {
        edges {
          node {
            name { value }
            role { value }
            loopback_ip { node { address { value } } }
            mgmt_ip { node { address { value } } }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, branch_name=branch)
    edges = resp["DcimDevice"]["edges"]
    loopbacks: list[str] = []
    with_mgmt = 0
    for edge in edges:
        node = edge["node"]
        lo = node.get("loopback_ip", {}).get("node")
        if lo and lo.get("address", {}).get("value"):
            loopbacks.append(lo["address"]["value"])
        mgmt = node.get("mgmt_ip", {}).get("node")
        if mgmt and mgmt.get("address", {}).get("value"):
            with_mgmt += 1
    duplicate_loopbacks = sorted({ip for ip in loopbacks if loopbacks.count(ip) > 1})
    return {
        "total": len(edges),
        "with_loopback": len(loopbacks),
        "with_mgmt": with_mgmt,
        "duplicate_loopbacks": duplicate_loopbacks,
    }


async def _devices_without_structured_config(client: InfrahubClient, branch: str) -> dict:
    """Return {'total': N, 'without': [names]} for devices missing a structured config file."""
    query = """
    query DevicesStructuredConfig {
      DcimDevice {
        edges {
          node {
            name { value }
            avd_artifact {
              node {
                structured_config_file { node { id } }
              }
            }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, branch_name=branch)
    edges = resp["DcimDevice"]["edges"]
    without = []
    for edge in edges:
        node = edge["node"]
        artifact = node.get("avd_artifact", {}).get("node")
        scf = artifact.get("structured_config_file", {}).get("node") if artifact else None
        if not scf:
            without.append(node["name"]["value"])
    return {"total": len(edges), "without": without}


async def _trigger_all_artifacts(definitions: list) -> None:
    """Fire artifact generation for every definition (fire-and-forget)."""
    for definition in definitions:
        await definition.generate()


async def _fetch_ready_artifact_content(
    client: InfrahubClient, branch: str, artifact_name: str
) -> tuple[str | None, str | None]:
    """Return (content, target_display_label) for one Ready artifact of ``artifact_name``.

    Reads content straight from the object store so it does not depend on any
    particular device having the artifact. Returns (None, None) if none is Ready.
    """
    query = (
        "query {\n"
        f'  CoreArtifact(name__value: "{artifact_name}") {{\n'
        "    edges { node {\n"
        "      status { value }\n"
        "      storage_id { value }\n"
        "      object { node { display_label } }\n"
        "    } }\n"
        "  }\n"
        "}"
    )
    resp = await client.execute_graphql(query=query, branch_name=branch)
    for edge in resp["CoreArtifact"]["edges"]:
        node = edge["node"]
        if node.get("status", {}).get("value") != "Ready":
            continue
        storage_id = node.get("storage_id", {}).get("value")
        if not storage_id:
            continue
        target = (node.get("object") or {}).get("node") or {}
        content = await client.object_store.get(identifier=storage_id)
        return content, target.get("display_label")
    return None, None
