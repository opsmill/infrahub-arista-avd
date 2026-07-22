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

import json
import os
from operator import itemgetter
from typing import TYPE_CHECKING

import pytest
import yaml
from infrahub_sdk.protocols import CoreGenericRepository
from infrahub_sdk.testing.docker import TestInfrahubDockerClient
from infrahub_sdk.testing.repository import GitRepo

from .helpers import (
    ALL_ARTIFACT_NAMES,
    ANTA_DISABLED_MARKER,
    ARISTA_DEVICE_TYPES,
    ARISTA_TEMPLATE_INTERFACE_COUNTS,
    ARTIFACT_AVD_ANTA_CATALOG,
    ARTIFACT_AVD_EOS_CONFIG,
    ARTIFACT_CONTAINERLAB_TOPOLOGY,
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
GENERATOR_AVD_HOSTVAR = "generate-avd-device-hostvar"
SERVER_CABLING_RACK = "Rack-B2-1"
SERVER_CABLING_SERVER = "e2e-server-b2-1"
SERVER_CABLING_TEMPLATE = "compute-server-dual"
DCI_POOL_PREFIX = "10.253.253.0/24"
DCI_POOL_NAME = "E2E-DCI-Pool"
DCI_LINK_NAME = "e2e-dci-link"
DCI_INTERFACE_NAME = "Ethernet999"


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
        device_types = {dt.name.value for dt in await client.all(kind="DcimDeviceType", branch=default_branch)}
        assert device_types, "no device types loaded"
        # Issue #70: Arista device types + object templates with the right port layout.
        missing_types = set(ARISTA_DEVICE_TYPES) - device_types
        assert not missing_types, f"Arista device types not loaded: {missing_types}"
        template_counts = await _template_interface_counts(
            client, default_branch, list(ARISTA_TEMPLATE_INTERFACE_COUNTS)
        )
        assert template_counts == ARISTA_TEMPLATE_INTERFACE_COUNTS, (
            f"Arista object templates wrong/absent: expected {ARISTA_TEMPLATE_INTERFACE_COUNTS}, got {template_counts}"
        )

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
        fabrics = await client.all(kind="NetworkFabric", branch=PIPELINE_BRANCH)
        fabric_ids = [fabric.id for fabric in fabrics]
        assert fabric_ids, "no fabrics found on the pipeline branch"
        await client.execute_graphql(
            query="""
            mutation RunGenerator($id: String!, $nodes: [String!]!) {
                CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                    ok
                }
            }
            """,
            variables={"id": gen_def.id, "nodes": fabric_ids},
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
            ready=lambda r: (
                len(r["asns"]) > 0
                and all(d["asn_node_id"] for d in r["devices"] if d["role"] in ("super_spine", "spine", "leaf"))
            ),
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
        report = await wait_until(
            fetch=lambda: _cabling_and_ip_report(client, PIPELINE_BRANCH),
            ready=lambda r: (
                r["network_link_count"] > 0
                and r["with_loopback"] >= r["l3_device_count"] > 0
                and not r["duplicate_loopbacks"]
                and r["with_mgmt"] > 0
            ),
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="NetworkLink cabling and device IP allocation",
        )
        print(
            f"cabling/ip report: links={report['network_link_count']} l3_devices={report['l3_device_count']} "
            f"total={report['total']} with_loopback={report['with_loopback']} "
            f"with_mgmt={report['with_mgmt']} duplicate_loopbacks={report['duplicate_loopbacks']}",
            flush=True,
        )
        assert report["network_link_count"] > 0, "no NetworkLink cabling created"
        assert report["with_loopback"] >= report["l3_device_count"] > 0, (
            f"expected every L3 device to have a loopback; {report['with_loopback']} have one"
        )
        assert not report["duplicate_loopbacks"], (
            f"duplicate loopback addresses allocated: {report['duplicate_loopbacks']}"
        )
        assert report["with_mgmt"] > 0, "no devices have an allocated management IP"

    # --- Component 10b: server cabling trigger -----------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_server_cabling_trigger_creates_links_and_lags(self, client: InfrahubClient) -> None:
        """Creating a server in the servers group triggers server cabling and creates links/LAGs."""
        await wait_until(
            fetch=lambda: _server_cabling_prerequisites(client, PIPELINE_BRANCH),
            ready=lambda r: (
                r["rack_complete"]
                and r["leaf_count"] == 2
                and r["leaf1_server_ports"] > 0
                and r["leaf2_server_ports"] > 0
            ),
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"{SERVER_CABLING_RACK} leaves and server-role ports",
        )

        rack = await client.get(kind="LocationRack", name__value=SERVER_CABLING_RACK, branch=PIPELINE_BRANCH)
        template = await client.get(
            kind="TemplateComputePhysicalServer",
            template_name__value=SERVER_CABLING_TEMPLATE,
            branch=PIPELINE_BRANCH,
        )
        server = await client.create(
            kind="ComputePhysicalServer",
            branch=PIPELINE_BRANCH,
            name=SERVER_CABLING_SERVER,
            rack={"id": rack.id},
            object_template={"id": template.id},
            status="provisioning",
            member_of_groups=["servers"],
        )
        await server.save(allow_upsert=True)

        report = await wait_until(
            fetch=lambda: _server_cabling_report(client, PIPELINE_BRANCH, SERVER_CABLING_SERVER),
            ready=lambda r: (
                r["server_link_count"] == 2
                and r["server_physical_count"] == 2
                and r["server_connected_count"] == 2
                and r["server_bond_count"] == 1
                and r["leaf_port_channel_count"] == 2
                and r["leaf_port_channel_member_count"] == 2
            ),
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"server cabling output for {SERVER_CABLING_SERVER}",
        )

        assert report["server_physical_lags"] == {"Ethernet1": "Bond1", "Ethernet2": "Bond1"}
        assert report["server_bond_members"] == ["Ethernet1", "Ethernet2"]
        assert report["server_link_count"] == 2
        assert report["leaf_port_channel_count"] == 2
        assert report["leaf_port_channel_member_count"] == 2
        assert report["leaf_port_channel_ids"] == [1117, 1117]
        print(f"server cabling report: {report}", flush=True)

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

    # --- Component 11b: DCI link hostvars ----------------------------------
    @pytest.mark.asyncio(loop_scope="class")
    async def test_dci_link_generates_l3_edge_hostvars(self, client: InfrahubClient) -> None:
        """A NetworkLink with role dci between Border Leafs generates stored l3_edge hostvars."""
        setup = await _create_dci_link_scenario(client, PIPELINE_BRANCH)
        await _run_generator_for_nodes(client, PIPELINE_BRANCH, GENERATOR_AVD_HOSTVAR, setup["device_ids"])

        report = await wait_until(
            fetch=lambda: _dci_hostvars_report(client, PIPELINE_BRANCH, setup["device_names"]),
            ready=lambda r: r["ready"] and len(r["unique_matching_links"]) == 1,
            timeout=GENERATOR_TIMEOUT,
            interval=POLL_INTERVAL,
            describe=f"DCI l3_edge hostvars for {DCI_LINK_NAME}",
        )

        link = report["unique_matching_links"][0]
        assert link["nodes"] == setup["device_names"]
        assert link["interfaces"] == setup["interface_names"]
        assert link["as"] == setup["expected_as"]
        assert link["ip"] == ["10.253.253.0/31", "10.253.253.1/31"]
        assert link["include_in_underlay_protocol"] is True
        assert "profile" not in link
        assert all("p2p_links_profiles" not in hostvars.get("l3_edge", {}) for hostvars in report["hostvars"].values())
        print(f"dci hostvars report: {report}", flush=True)

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

        # ContainerLab Topology is fabric-scoped and, unlike the device-scoped
        # EOS/ANTA artifacts, does not auto-cascade on the branch — so generate it
        # explicitly for each fabric target on the branch, then read a populated
        # render (this also proves the transform renders server-side on a branch).
        definitions = await client.all(kind="CoreArtifactDefinition", branch=PIPELINE_BRANCH)
        clab_def = next((d for d in definitions if d.artifact_name.value == ARTIFACT_CONTAINERLAB_TOPOLOGY), None)
        assert clab_def, "ContainerLab Topology artifact definition not registered"
        for fabric in await client.all(kind="NetworkFabric", branch=PIPELINE_BRANCH):
            resp = await client._post(
                f"{client.address}/api/artifact/generate/{clab_def.id}?branch={PIPELINE_BRANCH}",
                payload={"nodes": [fabric.id]},
            )
            resp.raise_for_status()

        def _has_populated_topology(contents: list[str]) -> bool:
            return any((yaml.safe_load(c).get("topology") or {}).get("nodes") for c in contents if c and c.strip())

        clab_contents = await wait_until(
            fetch=lambda: _fetch_ready_artifact_contents(client, PIPELINE_BRANCH, ARTIFACT_CONTAINERLAB_TOPOLOGY),
            ready=_has_populated_topology,
            timeout=ARTIFACT_TIMEOUT,
            interval=POLL_INTERVAL,
            describe="a populated ContainerLab topology artifact on the branch",
        )
        topos = [yaml.safe_load(c) for c in clab_contents if c and c.strip()]
        populated = [t for t in topos if (t.get("topology") or {}).get("nodes")]
        topo = max(populated, key=lambda t: len(t["topology"]["nodes"]))
        assert topo.get("name"), "ContainerLab topology has no fabric name"
        nodes = topo["topology"]["nodes"]
        links = topo["topology"]["links"]
        assert links, "ContainerLab topology has no links"
        assert all(n["kind"] == "arista_ceos" for n in nodes.values()), "non-cEOS node in topology"
        # Interface names must be ContainerLab short form, never raw EOS names.
        untranslated = [ep for link in links for ep in link["endpoints"] if "Ethernet" in ep]
        assert not untranslated, f"untranslated EOS interface names in links: {untranslated[:5]}"

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


async def _template_interface_counts(client: InfrahubClient, branch: str, template_names: list[str]) -> dict[str, int]:
    """Return {template_name: interface_count} for the given object templates (issue #70)."""
    resp = await client.execute_graphql(
        query="""
        query($names: [String!]) {
          TemplateDcimDevice(template_name__values: $names) {
            edges { node { template_name { value } interfaces { count } } }
          }
        }
        """,
        variables={"names": template_names},
        branch_name=branch,
    )
    return {
        edge["node"]["template_name"]["value"]: edge["node"]["interfaces"]["count"]
        for edge in resp["TemplateDcimDevice"]["edges"]
    }


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
        asns.append(
            {"id": node["id"], "value": (node.get("asn") or {}).get("value"), "fabric_id": (fabric or {}).get("id")}
        )

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


async def _cabling_and_ip_report(client: InfrahubClient, branch: str) -> dict:
    ip_report = await _device_ip_report(client, branch)
    links = await client.all(kind="NetworkLink", branch=branch)
    l3_device_count = 0
    for role in ("super_spine", "spine", "leaf", "border_leaf"):
        l3_device_count += len(await client.filters(kind="DcimDevice", role__value=role, branch=branch))
    return {
        **ip_report,
        "network_link_count": len(links),
        "l3_device_count": l3_device_count,
    }


async def _server_cabling_prerequisites(client: InfrahubClient, branch: str) -> dict:
    """Report whether Rack-B2-1 is ready for server-cabling validation."""
    query = """
    query ServerCablingPrerequisites($rack: String!) {
      LocationRack(name__value: $rack) {
        edges {
          node {
            generation_complete { value }
          }
        }
      }
      DcimDevice(role__value: "leaf") {
        edges {
          node {
            name { value }
            rack { node { name { value } } }
            interfaces(role__value: "server") {
              edges {
                node {
                  __typename
                  ... on InterfacePhysical {
                    name { value }
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, variables={"rack": SERVER_CABLING_RACK}, branch_name=branch)
    rack_edges = resp["LocationRack"]["edges"]
    rack_complete = bool(rack_edges and rack_edges[0]["node"]["generation_complete"]["value"])
    leaves = [
        edge["node"]
        for edge in resp["DcimDevice"]["edges"]
        if edge["node"].get("rack", {}).get("node", {}).get("name", {}).get("value") == SERVER_CABLING_RACK
    ]
    ports_by_leaf = {
        leaf["name"]["value"]: len(
            [
                iface_edge
                for iface_edge in leaf["interfaces"]["edges"]
                if iface_edge["node"].get("__typename") == "InterfacePhysical"
            ]
        )
        for leaf in leaves
    }
    return {
        "rack_complete": rack_complete,
        "leaf_count": len(leaves),
        "leaf1_server_ports": ports_by_leaf.get("leaf-pod-b2-1-1", 0),
        "leaf2_server_ports": ports_by_leaf.get("leaf-pod-b2-1-2", 0),
    }


async def _server_cabling_report(client: InfrahubClient, branch: str, server_name: str) -> dict:
    """Summarize server-cabling links, server Bond1, and switch-side Port-Channels."""
    query = """
    query ServerCablingReport($server: String!) {
      ComputePhysicalServer(name__value: $server) {
        edges {
          node {
            interfaces {
              edges {
                node {
                  __typename
                  ... on InterfacePhysical {
                    name { value }
                    connector { node { name { value } } }
                    lag { node { name { value } } }
                  }
                  ... on InterfaceLag {
                    name { value }
                    lag_members {
                      edges {
                        node {
                          name { value }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      NetworkLink {
        edges {
          node {
            name { value }
          }
        }
      }
      InterfaceLag {
        edges {
          node {
            name { value }
            channel_id { value }
            device { node { name { value } } }
            lag_members {
              edges {
                node {
                  name { value }
                  device { node { name { value } } }
                }
              }
            }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, variables={"server": server_name}, branch_name=branch)

    server_edges = resp["ComputePhysicalServer"]["edges"]
    if not server_edges:
        return {
            "server_link_count": 0,
            "server_physical_count": 0,
            "server_connected_count": 0,
            "server_physical_lags": {},
            "server_bond_count": 0,
            "server_bond_members": [],
            "leaf_port_channel_count": 0,
            "leaf_port_channel_member_count": 0,
            "leaf_port_channel_ids": [],
        }

    physical_interfaces = []
    server_bonds = []
    for edge in server_edges[0]["node"]["interfaces"]["edges"]:
        node = edge["node"]
        if node["__typename"] == "InterfacePhysical":
            physical_interfaces.append(node)
        elif node["__typename"] == "InterfaceLag" and node["name"]["value"] == "Bond1":
            server_bonds.append(node)

    server_links = [
        edge["node"]["name"]["value"]
        for edge in resp["NetworkLink"]["edges"]
        if server_name in edge["node"]["name"]["value"]
    ]
    server_physical_lags = {}
    server_connected_count = 0
    for iface in physical_interfaces:
        lag_node = (iface.get("lag") or {}).get("node") or {}
        connector_node = (iface.get("connector") or {}).get("node") or {}
        server_physical_lags[iface["name"]["value"]] = (lag_node.get("name") or {}).get("value")
        if connector_node:
            server_connected_count += 1
    server_bond_members = sorted(
        member_edge["node"]["name"]["value"] for bond in server_bonds for member_edge in bond["lag_members"]["edges"]
    )

    leaf_port_channels = []
    for edge in resp["InterfaceLag"]["edges"]:
        node = edge["node"]
        if node["name"]["value"] != "Port-Channel1117":
            continue
        device_name = node.get("device", {}).get("node", {}).get("name", {}).get("value")
        if device_name in {"leaf-pod-b2-1-1", "leaf-pod-b2-1-2"}:
            leaf_port_channels.append(node)

    return {
        "server_link_count": len(server_links),
        "server_physical_count": len(physical_interfaces),
        "server_connected_count": server_connected_count,
        "server_physical_lags": server_physical_lags,
        "server_bond_count": len(server_bonds),
        "server_bond_members": server_bond_members,
        "leaf_port_channel_count": len(leaf_port_channels),
        "leaf_port_channel_member_count": sum(len(lag["lag_members"]["edges"]) for lag in leaf_port_channels),
        "leaf_port_channel_ids": sorted(lag["channel_id"]["value"] for lag in leaf_port_channels),
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


async def _create_dci_link_scenario(client: InfrahubClient, branch: str) -> dict:
    """Create one complete DCI link using the shared connector workflow."""
    candidates = await _dci_leaf_candidates(client, branch)
    assert len(candidates) >= 2, f"expected two leaves with spare physical interfaces, got {candidates}"
    left, right = candidates[:2]

    await _ensure_dci_pool(client, branch, left["fabric_id"])

    for device_id in (left["device_id"], right["device_id"]):
        device = await client.get(kind="DcimDevice", id=device_id, branch=branch)
        device.role.value = "border_leaf"
        await device.save(allow_upsert=True)

    dci_link = await client.create(
        kind="NetworkLink",
        branch=branch,
        name=DCI_LINK_NAME,
        medium="smf",
        role="dci",
        include_in_underlay_protocol=True,
    )
    await dci_link.save(allow_upsert=True)

    for endpoint in (left, right):
        dci_interface = await client.create(
            kind="InterfacePhysical",
            branch=branch,
            name=DCI_INTERFACE_NAME,
            device={"id": endpoint["device_id"]},
        )
        await dci_interface.save(allow_upsert=True)
        iface = await client.get(kind="InterfacePhysical", id=dci_interface.id, branch=branch, include=["connector"])
        iface.connector = dci_link
        iface.status.value = "active"
        await iface.save(allow_upsert=True)
        endpoint["interface_id"] = dci_interface.id
        endpoint["interface_name"] = DCI_INTERFACE_NAME

    return {
        "device_ids": [left["device_id"], right["device_id"]],
        "device_names": [left["device_name"], right["device_name"]],
        "interface_names": [left["interface_name"], right["interface_name"]],
        # Candidates are sorted by device name, matching the generator's endpoint
        # ordering, so the AS list follows the same order.
        "expected_as": [left["device_asn"], right["device_asn"]],
    }


async def _dci_leaf_candidates(client: InfrahubClient, branch: str) -> list[dict]:
    query = """
    query DciLeafCandidates {
      DcimDevice(role__value: "leaf") {
        edges {
          node {
            id
            name { value }
            asn { node { asn { value } } }
            pod { node { parent { node { id name { value } } } } }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, branch_name=branch)
    candidates = []
    seen_fabric_id = None
    for edge in resp["DcimDevice"]["edges"]:
        device = edge["node"]
        fabric = device.get("pod", {}).get("node", {}).get("parent", {}).get("node")
        if not fabric:
            continue
        asn_node = (device.get("asn") or {}).get("node")
        device_asn = asn_node["asn"]["value"] if asn_node and asn_node.get("asn") else None
        if device_asn is None:
            continue
        if seen_fabric_id is None:
            seen_fabric_id = fabric["id"]
        if fabric["id"] != seen_fabric_id:
            continue
        candidates.append(
            {
                "device_id": device["id"],
                "device_name": device["name"]["value"],
                "device_asn": int(device_asn),
                "fabric_id": fabric["id"],
                "fabric_name": fabric["name"]["value"],
                "interface_id": None,
                "interface_name": DCI_INTERFACE_NAME,
            }
        )
    return sorted(candidates, key=itemgetter("device_name"))


async def _ensure_dci_pool(client: InfrahubClient, branch: str, fabric_id: str) -> None:
    prefix = await client.create(kind="IpamPrefix", branch=branch, prefix=DCI_POOL_PREFIX, role="technical")
    await prefix.save(allow_upsert=True)
    pool = await client.create(
        kind="CoreIPPrefixPool",
        branch=branch,
        name=DCI_POOL_NAME,
        default_member_type="prefix",
        default_prefix_type="IpamPrefix",
        default_prefix_length=31,
        ip_namespace="default",
        resources=[DCI_POOL_PREFIX],
    )
    await pool.save(allow_upsert=True)

    fabric = await client.get(kind="NetworkFabric", id=fabric_id, branch=branch, include=["dci_pool"])
    fabric.dci_pool = pool
    await fabric.save(allow_upsert=True)


async def _run_generator_for_nodes(
    client: InfrahubClient, branch: str, generator_name: str, node_ids: list[str]
) -> None:
    gen_def = await client.get(kind="CoreGeneratorDefinition", name__value=generator_name, branch=branch)
    for node_id in node_ids:
        await client.execute_graphql(
            query="""
            mutation RunGenerator($id: String!, $nodes: [String!]!) {
                CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                    ok
                }
            }
            """,
            variables={"id": gen_def.id, "nodes": [node_id]},
            branch_name=branch,
        )


async def _dci_hostvars_report(client: InfrahubClient, branch: str, device_names: list[str]) -> dict:
    query = """
    query DciHostvars($names: [String!]) {
      DcimDevice(name__values: $names) {
        edges {
          node {
            name { value }
            avd_artifact {
              node {
                hostvar_file { node { storage_id { value } } }
              }
            }
          }
        }
      }
    }
    """
    resp = await client.execute_graphql(query=query, variables={"names": device_names}, branch_name=branch)
    hostvars = {}
    for edge in resp["DcimDevice"]["edges"]:
        node = edge["node"]
        storage_id = (
            node.get("avd_artifact", {})
            .get("node", {})
            .get("hostvar_file", {})
            .get("node", {})
            .get("storage_id", {})
            .get("value")
        )
        if not storage_id:
            continue
        hostvars[node["name"]["value"]] = json.loads(await client.object_store.get(identifier=storage_id))

    matching_links = []
    for device_hostvars in hostvars.values():
        matching_links.extend(
            link
            for link in device_hostvars.get("l3_edge", {}).get("p2p_links", [])
            if link.get("nodes") == device_names or link.get("nodes") == list(reversed(device_names))
        )

    unique_matching_links = list(
        {
            (
                tuple(link.get("nodes", [])),
                tuple(link.get("interfaces", [])),
                tuple(link.get("as", [])),
                tuple(link.get("ip", [])),
                link.get("include_in_underlay_protocol"),
                link.get("speed"),
            ): link
            for link in matching_links
        }.values()
    )

    return {
        "ready": set(hostvars) == set(device_names),
        "hostvars": hostvars,
        "matching_links": matching_links,
        "unique_matching_links": unique_matching_links,
    }


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


async def _fetch_ready_artifact_contents(client: InfrahubClient, branch: str, artifact_name: str) -> list[str]:
    """Return the content of every Ready artifact of ``artifact_name`` on ``branch``.

    Used for fabric-scoped artifacts where several targets (and possibly an early
    empty render) share one name, so the caller can pick a populated one.
    """
    query = (
        "query {\n"
        f'  CoreArtifact(name__value: "{artifact_name}") {{\n'
        "    edges { node { status { value } storage_id { value } } }\n"
        "  }\n"
        "}"
    )
    resp = await client.execute_graphql(query=query, branch_name=branch)
    contents: list[str] = []
    for edge in resp["CoreArtifact"]["edges"]:
        node = edge["node"]
        if node.get("status", {}).get("value") != "Ready":
            continue
        storage_id = node.get("storage_id", {}).get("value")
        if storage_id:
            contents.append(await client.object_store.get(identifier=storage_id))
    return contents


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
