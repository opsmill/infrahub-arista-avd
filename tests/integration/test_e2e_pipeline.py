"""End-to-end pipeline integration test (trigger-driven).

Boots a real Infrahub stack via ``infrahub-testcontainers`` and exercises the
pipeline the way it actually runs in production: the ``triggers.yml`` event rules
are loaded, work happens on a branch, and only the **fabric** generator is
invoked explicitly. Everything downstream cascades via ``CoreNodeTriggerRule``:

    generate-fabric  (updates each pod's checksum)
      -> trigger-pod-generator      -> spines created (+ racks bumped)
      -> trigger-rack-generator     -> leaves created (+ hostvars generated)
      -> avd_hostvars_ready True    -> AVD structured config generated
      -> structured-config created  -> backfill runs

The trigger rules are ``branch_scope: "other_branches"``, so the cascade only
fires off ``main`` — hence a dedicated branch. Base data (schema, objects,
triggers, repository) is loaded on ``main``; the generator cascade runs on the
branch, mirroring the real change/proposed-change workflow.

The container stack is class-scoped, so it boots once and the ordered component
tests share it. Each downstream test simply waits (bounded) for the stage's
output to appear — it does not run that generator itself. All methods share one
class-scoped event loop so the single ``client`` is reused safely.

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
    GENERATOR_FABRIC,
    GENERATOR_TIMEOUT,
    GROUP_TIMEOUT,
    POLL_INTERVAL,
    REPO_SYNC_INTERVAL,
    REPO_SYNC_RETRIES,
    expected_super_spine_count,
    wait_until,
)

if TYPE_CHECKING:
    from pathlib import Path

    from infrahub_sdk import InfrahubClient

REPO_NAME = "e2e-repository"
# The cascade runs on this branch; trigger rules only fire off `main`.
PIPELINE_BRANCH = "e2e-pipeline"


@pytest.mark.e2e
class TestE2EPipeline(TestInfrahubDockerClient):
    """Trigger-driven design-to-artifact pipeline against a real Infrahub instance.

    One test per pipeline component; they run in order and share the class-scoped
    stack. Downstream components appear via ``triggers.yml`` event rules after the
    fabric generator runs — the tests observe each stage, they do not drive it.
    Running a single test in isolation will fail because it relies on the state
    produced by the earlier ones.
    """

    @pytest.fixture(scope="class", autouse=True)
    def _client_timeout(self) -> None:
        # Raise the infrahubctl client timeout: the fabric generator issues large
        # GraphQL reads/writes that can exceed the 60s default under load.
        os.environ.setdefault("INFRAHUB_TIMEOUT", "300")

    @staticmethod
    def _address(infrahub_port: int) -> str:
        return f"http://localhost:{infrahub_port}"

    # --- Component 1: schema (main) ----------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_load_schema(self, default_branch: str, client: InfrahubClient, schemas: list[dict]) -> None:
        """Load this repository's schemas and wait for convergence (FR-002)."""
        await client.schema.wait_until_converged(branch=default_branch)
        resp = await client.schema.load(schemas=schemas, branch=default_branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"
        await client.schema.wait_until_converged(branch=default_branch)

    # --- Component 2: objects (main) ---------------------------------------
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

    # --- Component 3: target groups (main) ---------------------------------
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

    # --- Component 4: repository (main) ------------------------------------
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

    # --- Component 5: trigger rules (main, after repo sync) ----------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_load_triggers(self, infrahub_port: int) -> None:
        """Load the generator event-trigger rules so the cascade can fire on a branch.

        Loaded *after* the repository sync: the ``CoreGeneratorAction`` objects
        reference generators by name (generate-pod, generate-rack, ...) which only
        exist once the repository has registered its generator definitions. This
        mirrors the `inv load` order (objects -> repository -> wait -> triggers).
        """
        result = self.execute_command(
            command="infrahubctl object load triggers.yml", address=self._address(infrahub_port)
        )
        print(result.stdout, flush=True)
        if result.stderr:
            print(result.stderr, flush=True)
        assert result.returncode == 0, f"trigger load failed:\n{result.stdout}\n{result.stderr}"

    # --- Component 6: branch + enable ANTA ---------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_create_branch_and_enable_anta(self, client: InfrahubClient) -> None:
        """Create the working branch (triggers fire off `main`) and enable ANTA before the cascade."""
        await client.branch.create(branch_name=PIPELINE_BRANCH, sync_with_git=False)
        # Enable ANTA on the branch fabrics so the catalog is populated (not the
        # disabled marker) once the cascade reaches structured-config generation.
        fabrics = await client.all(kind="NetworkFabric", branch=PIPELINE_BRANCH)
        assert fabrics, "no fabrics found on the pipeline branch"
        for fabric in fabrics:
            if hasattr(fabric, "anta_enabled"):
                fabric.anta_enabled.value = True
                await fabric.save()

    # --- Component 7: fabric generator (the only explicit kick-off) --------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_fabric_generator_creates_super_spines(self, client: InfrahubClient) -> None:
        """Kick off ONLY the fabric generator via the API; assert super-spines appear (FR-006/FR-008).

        Uses the ``CoreGeneratorDefinitionRun`` mutation — the same server-side
        mechanism the repo's own generators use to chain (see ``_trigger_generator``
        in ``src/solution_arista_avd/generator.py``) and how the triggered pod/rack
        generators run. No infrahubctl subprocess; it runs in the task-worker against
        the synced repo. Fire-and-forget, so success is confirmed by polling for the
        produced devices, which also proves the trigger cascade started.
        """
        gen_def = await client.get(kind="CoreGeneratorDefinition", name__value=GENERATOR_FABRIC, branch=PIPELINE_BRANCH)
        await client.execute_graphql(
            query="""
            mutation RunGenerator($id: String!) {
                CoreGeneratorDefinitionRun(data: { id: $id }) {
                    ok
                }
            }
            """,
            variables={"id": gen_def.id},
            branch_name=PIPELINE_BRANCH,
        )

        expected = await expected_super_spine_count(client, PIPELINE_BRANCH)
        super_spines = await wait_until(
            fetch=lambda: client.filters(kind="DcimDevice", role__value="super_spine", branch=PIPELINE_BRANCH),
            ready=lambda d: len(d) >= expected > 0,
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"super_spine devices (expected {expected})",
        )
        print(f"super_spine devices: {len(super_spines)}", flush=True)

    # --- Component 8: pod trigger cascade ----------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_pod_trigger_creates_spines(self, client: InfrahubClient) -> None:
        """The fabric generator bumped the pods, firing the pod generator via triggers."""
        spines = await wait_until(
            fetch=lambda: client.filters(kind="DcimDevice", role__value="spine", branch=PIPELINE_BRANCH),
            ready=lambda d: len(d) > 0,
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="spine devices (pod generator fired via trigger)",
        )
        print(f"spine devices: {len(spines)}", flush=True)

    # --- Component 9: rack trigger cascade ---------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_rack_trigger_creates_leaves(self, client: InfrahubClient) -> None:
        """The pod generator bumped the racks, firing the rack generator via triggers."""
        leaves = await wait_until(
            fetch=lambda: client.filters(kind="DcimDevice", role__value="leaf", branch=PIPELINE_BRANCH),
            ready=lambda d: len(d) > 0,
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="leaf devices (rack generator fired via trigger)",
        )
        print(f"leaf devices: {len(leaves)}", flush=True)

    # --- Component 9b: BGP ASN nodes (regression 002) ----------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_asn_nodes_created_and_linked(self, client: InfrahubClient) -> None:
        """RoutingAsn nodes are created, fabric-owned, and linked to every L3 device (C1);
        each MLAG pair shares one ASN node across both leaves and the domain (C2).

        This is the regression guard for feature 002: before the fix, fabric
        generation produced zero Routing.Asn nodes.
        """
        report = await wait_until(
            fetch=lambda: _asn_report(client, PIPELINE_BRANCH),
            ready=lambda r: len(r["asns"]) > 0
            and all(d["asn_node_id"] for d in r["devices"] if d["role"] in ("super_spine", "spine", "leaf")),
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="RoutingAsn nodes created and linked to every L3 device",
        )

        # SC-001 / C1: nodes exist and every one is owned by a fabric.
        assert report["asns"], "no RoutingAsn nodes created by fabric generation"
        assert all(a["fabric_id"] for a in report["asns"]), "a RoutingAsn node has no owning fabric"

        # SC-002: every L3 device (super-spine/spine/leaf) resolves an ASN node.
        l3 = [d for d in report["devices"] if d["role"] in ("super_spine", "spine", "leaf")]
        assert l3, "no L3 devices found"
        unlinked = [d["name"] for d in l3 if not d["asn_node_id"]]
        assert not unlinked, f"L3 devices without an ASN node: {unlinked}"

        # C2 / SC-004: each MLAG domain shares one ASN node with both of its peers.
        asn_by_device = {d["id"]: d["asn_node_id"] for d in report["devices"]}
        for dom in report["domains"]:
            dom_asn = dom["asn_node_id"]
            assert dom_asn, f"MLAG domain {dom['domain_id']} has no ASN node"
            peer_asns = {asn_by_device.get(pid) for pid in dom["peer_ids"]}
            assert peer_asns == {dom_asn}, (
                f"MLAG domain {dom['domain_id']} does not share one ASN node with its peers: "
                f"domain={dom_asn} peers={peer_asns}"
            )
        print(
            f"asn report: routing_asns={len(report['asns'])} l3_devices={len(l3)} mlag_domains={len(report['domains'])}",
            flush=True,
        )

    # --- Component 10: cabling & IP allocation (US2) -----------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_cabling_and_ip_allocation(self, client: InfrahubClient) -> None:
        """Links exist and every L3 device has a unique loopback + a management IP (FR-009)."""
        links = await client.all(kind="NetworkLink", branch=PIPELINE_BRANCH)
        assert links, "no NetworkLink cabling created"

        l3_device_count = 0
        for role in ("super_spine", "spine", "leaf"):
            l3_device_count += len(await client.filters(kind="DcimDevice", role__value=role, branch=PIPELINE_BRANCH))

        ip_report = await _device_ip_report(client, PIPELINE_BRANCH)
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

    # --- Component 11: AVD structured config (via trigger cascade) ---------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_structured_config_cascade(self, client: InfrahubClient) -> None:
        """Rack completion set avd_hostvars_ready, cascading into AVD structured config (FR-010)."""
        report = await wait_until(
            fetch=lambda: _devices_without_structured_config(client, PIPELINE_BRANCH),
            ready=lambda r: r is not None and r["total"] > 0 and not r["without"],
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="every device has an AVD structured config",
        )
        print(f"structured config present on all {report['total']} devices", flush=True)

    # --- Component 12: artifacts generated ---------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_artifacts_generated(self, client: InfrahubClient) -> None:
        """Every AVD artifact definition yields at least one Ready artifact on the branch (FR-011/FR-013)."""
        definitions = await client.all(kind="CoreArtifactDefinition", branch=PIPELINE_BRANCH)
        assert definitions, "no artifact definitions registered (repository sync incomplete?)"
        await _trigger_all_artifacts(client, PIPELINE_BRANCH, definitions)

        for artifact_name in ALL_ARTIFACT_NAMES:
            await self._wait_for_ready_artifact(client, PIPELINE_BRANCH, artifact_name, definitions)

    # --- Component 13: artifact content ------------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_artifact_content(self, client: InfrahubClient) -> None:
        """A rendered EOS config mentions its device hostname; the ANTA catalog is populated (FR-012)."""
        eos_content, eos_target = await _fetch_ready_artifact_content(client, PIPELINE_BRANCH, ARTIFACT_AVD_EOS_CONFIG)
        assert eos_content and eos_content.strip(), "EOS configuration artifact is empty"
        assert "hostname" in eos_content, "EOS config does not contain a hostname line"
        if eos_target:
            assert eos_target in eos_content, f"EOS config does not mention its device hostname {eos_target}"

        anta_content, _ = await _fetch_ready_artifact_content(client, PIPELINE_BRANCH, ARTIFACT_AVD_ANTA_CATALOG)
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
                await _trigger_all_artifacts(client, branch, definitions)
            return ready

        await wait_until(
            fetch=fetch,
            ready=lambda ready: len(ready) >= 1,
            timeout=ARTIFACT_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"Ready artifact '{artifact_name}'",
        )


async def _asn_report(client: InfrahubClient, branch: str) -> dict:
    """Report Routing.Asn nodes and every device's / MLAG domain's linked ASN node.

    Returns:
        asns: [{id, value, fabric_id}] — the allocated ASN nodes.
        devices: [{id, name, role, asn_node_id}] — each device's linked ASN node id (or None).
        domains: [{domain_id, asn_node_id, peer_ids}] — MLAG domains and their peers.
    """
    query = """
    query AsnReport {
      RoutingAsn { edges { node { id asn { value } fabric { node { id } } } } }
      DcimDevice { edges { node { id name { value } role { value } asn { node { id } } } } }
      MlagDomain { edges { node { domain_id { value } asn { node { id } } peers { edges { node { id } } } } } }
    }
    """
    resp = await client.execute_graphql(query=query, branch_name=branch)

    asns = []
    for edge in resp["RoutingAsn"]["edges"]:
        node = edge["node"]
        fabric = (node.get("fabric") or {}).get("node")
        asns.append({"id": node["id"], "value": (node.get("asn") or {}).get("value"), "fabric_id": (fabric or {}).get("id")})

    devices = []
    for edge in resp["DcimDevice"]["edges"]:
        node = edge["node"]
        asn_node = (node.get("asn") or {}).get("node")
        devices.append(
            {
                "id": node["id"],
                "name": node["name"]["value"],
                "role": node["role"]["value"],
                "asn_node_id": (asn_node or {}).get("id"),
            }
        )

    domains = []
    for edge in resp["MlagDomain"]["edges"]:
        node = edge["node"]
        asn_node = (node.get("asn") or {}).get("node")
        peer_ids = [p["node"]["id"] for p in node.get("peers", {}).get("edges", []) if p.get("node")]
        domains.append(
            {
                "domain_id": node["domain_id"]["value"],
                "asn_node_id": (asn_node or {}).get("id"),
                "peer_ids": peer_ids,
            }
        )

    return {"asns": asns, "devices": devices, "domains": domains}


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


async def _trigger_all_artifacts(client: InfrahubClient, branch: str, definitions: list) -> None:
    """Fire artifact generation for every definition on ``branch`` (fire-and-forget).

    The node ``.generate()`` helper posts without a branch (targets main, which has
    no devices in this flow), so hit the branch-aware endpoint directly.
    """
    for definition in definitions:
        resp = await client._post(
            f"{client.address}/api/artifact/generate/{definition.id}?branch={branch}",
            payload={"nodes": []},
        )
        resp.raise_for_status()


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
