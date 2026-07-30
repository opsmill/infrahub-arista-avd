# Tasks: ContainerLab Topology for the Multi-Domain Fabric

**Feature dir**: `specs/008-containerlab-multi-domain`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Parity contract**: [contracts/parity-matrix.md](./contracts/parity-matrix.md)

**Tech**: Python 3.12, `infrahub-sdk` 1.22.0, Jinja2, pytest. Deploy: `opsmill.infrahub` 1.8.3,
`containerlab` 0.77.0.

Tests are included because the spec requires them (FR-039…FR-043) and the constitution mandates
them before merge.

---

## Phase 1: Setup

- [x] T001 Create working branch and confirm Infrahub reachability by running `uv run infrahubctl info` and `uv run infrahubctl branch create clab-multi-domain` from the repo root
- [x] T002 [P] Record the current baseline output for comparison by rendering the existing artifact to `/tmp/baseline-topology.clab.yml` via `COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-Multi-Domain`, confirming it currently omits border leaves and DCI links
- [x] T003 [P] Install the deploy-side collection with `ansible-galaxy collection install -r ansible/requirements.yml`, since `opsmill.infrahub` is absent from this host and blocks Phase 6

---

## Phase 2: Foundational (blocks US2 and US4)

**Schema and object data. Nothing that reads these attributes can be written until they exist.**

- [x] T004 Add the `containerlab_image` attribute (`kind: Text`, `optional: true`, `order_weight: 1950`) to the `DcimPlatform` node in `schemas/base/dcim.yml`, immediately after the existing `containerlab_os`
- [x] T005 Add the `containerlab_interface_mapping` attribute (`kind: Text`, `optional: true`, `order_weight: 1700`) to the `DcimDeviceType` node in `schemas/base/dcim.yml`
- [x] T006 Validate the schema with `uv run infrahubctl schema check schemas/ --branch clab-multi-domain` and fix any reported errors before loading
- [x] T007 Load the schema with `uv run infrahubctl schema load schemas --branch clab-multi-domain`
- [x] T008 Regenerate protocols with `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py` and commit the regenerated file; do not hand-edit it
- [x] T009 [P] Set `containerlab_image: arista/ceos:4.36.0.1F` on the `EOS` platform in `objects/03_device_type.yml`
- [x] T010 [P] Add a new `Linux` `DcimPlatform` with `containerlab_os: linux` and `containerlab_image: lab-server` to `objects/03_device_type.yml`
- [x] T011 [P] Set `containerlab_interface_mapping: DCS-7050CX3-32S.json` on `Arista 7050CX3-32C` and `DCS-7050SX3-48YC8.json` on `Arista 7050SX3-48YC8C` in `objects/03_device_type.yml`, keeping the filenames exactly as they appear in `lab/configs/eos-intf-mapping/` rather than matching the part numbers
- [x] T012 Assign the `Linux` platform to the server templates in `objects/11b_l3ls_multi_domain_server_templates.yml` so future servers inherit it
- [x] T013 Load object data with `uv run infrahubctl object load objects/ --branch clab-multi-domain` then `uv run infrahubctl object load manual_objects/ --branch clab-multi-domain`, and verify the attributes carry values via `uv run infrahubctl object get DcimPlatform --branch clab-multi-domain -o csv`

**Checkpoint**: schema check passes, protocols regenerated, all four attribute values readable.

---

## Phase 3: User Story 1 — Every multi-domain node and link appears (P1) 🎯 MVP

**Goal**: The 4 border leaves and all 4 DCI links plus 8 uplinks stop being silently dropped.

**Independent test**: Render the artifact and assert 12 switch nodes and 4 links whose
`NetworkLink.role` is `dci`. Delivers value with no other story implemented.

- [x] T014 [US1] Extend the accepted-role set in `transforms/containerlab_topology.py` to include `border_leaf`, `l2spine`, and `l3spine` alongside the existing `super_spine`, `spine`, `leaf`, `l2leaf`, deliberately leaving out `p`, `pe`, `rr` per research R-003
- [x] T015 [US1] Add a module-level logger to `transforms/containerlab_topology.py` and emit one warning per device excluded by role filtering, naming the device and its role, so exclusions are diagnosable
- [x] T016 [P] [US1] Add `role { value }` to the `NetworkLink` selection in `transforms/containerlab_topology.gql` so DCI links are distinguishable, and add the matching field to `transforms/containerlab_topology_query.py`
- [x] T017 [P] [US1] Add unit tests to `tests/unit/test_containerlab_topology.py` asserting a `border_leaf` device is included, that links between two border leaves survive, and that an unsupported role is excluded and warned about
- [x] T018 [US1] Dry-run against loaded data with `COLUMNS=500 uv run infrahubctl transform containerlab_topology name=Fabric-L3LS-Multi-Domain --branch clab-multi-domain` and diff against `/tmp/baseline-topology.clab.yml` to confirm 4 more nodes and 12 more links appear

**Checkpoint**: 12 switch nodes, 20 switch-to-switch links, 4 of them DCI.

---

## Phase 4: User Story 2 — Kind, image, and interface mapping from the graph (P1)

**Goal**: No node kind, container image, or mapping filename originates in Python.

**Independent test**: Render and assert `kinds` carries the image from
`DcimPlatform.containerlab_image`, and each spine binds `DCS-7050CX3-32S.json` while each leaf
binds `DCS-7050SX3-48YC8.json`.

- [x] T019 [US2] Extend `transforms/containerlab_topology.gql` to traverse `device_type { node { platform { node { containerlab_os { value } containerlab_image { value } } } containerlab_interface_mapping { value } } }`, using nested `node` wrappers for each cardinality-one hop
- [x] T020 [US2] Add the corresponding nested models to `transforms/containerlab_topology_query.py` for the platform and device-type fields
- [x] T021 [US2] Implement platform resolution in `transforms/containerlab_topology.py` that tries `device_type.platform` first then falls back to the device's own `platform`, warning and excluding the node when neither yields a `containerlab_os`
- [x] T022 [US2] Replace the hardcoded `CEOS_KIND` and `CEOS_IMAGE` use in `transforms/containerlab_topology.py` with graph-derived values, and build the kind-to-image grouping in Python rather than deferring it to Jinja2 per research R-009
- [x] T023 [US2] Emit a per-node interface-mapping bind in `transforms/containerlab_topology.py` as `configs/eos-intf-mapping/<filename>:/mnt/flash/EosIntfMapping.json:ro`, omitting it when the attribute is unset
- [x] T024 [US2] Rewrite `transforms/templates/containerlab_topology.j2` to render one `kinds` entry per distinct kind with its own image, and per-node `binds` lists, omitting the `binds` key entirely when a node has none
- [x] T025 [US2] Change the kind-level `startup-config` in `transforms/templates/containerlab_topology.j2` to `configs/__clabNodeName__.cfg` per research R-006, so it matches where the playbook writes fetched configs
- [x] T026 [P] [US2] Replace the obsolete `assert "binds" not in ...` assertion in `tests/unit/test_containerlab_topology.py` with assertions that binds ARE emitted, rather than deleting it silently
- [x] T027 [P] [US2] Add unit tests to `tests/unit/test_containerlab_topology.py` for kind/image derivation, mapping-bind emission, absence of a bind when the attribute is unset, and multi-kind grouping
- [x] T028 [US2] Dry-run the render and confirm no container image, kind, or mapping filename remains as a literal in `transforms/containerlab_topology.py`

**Checkpoint**: all 12 switches carry the correct mapping bind; images come from data.

---

## Phase 5: User Story 4 — Servers present (P2)

**Depends on**: US2 (server kind resolves through the same platform path).

**Goal**: Two `linux` nodes with mgmt IPs, netplan binds, and their 4 links to access leaves.

**Independent test**: Render and assert two `linux`-kind nodes each with two links to distinct
access leaves.

- [x] T029 [US4] Add `ComputePhysicalServer` as a separate top-level field in `transforms/containerlab_topology.gql` — not an inline fragment, per research R-009 — selecting `id`, `name`, `mgmt_ip`, `platform`, and `interfaces`
- [x] T030 [US4] Add the server models to `transforms/containerlab_topology_query.py`
- [x] T031 [US4] Collect servers as nodes in `transforms/containerlab_topology.py`, resolving kind and image from `device.platform` since `ComputePhysicalServer` has no `device_type`
- [x] T032 [US4] Emit the netplan bind as `configs/servers/<device-name>-netplan.yaml:/etc/netplan/netplan.yaml` in `transforms/containerlab_topology.py`
- [x] T033 [US4] Stop dropping server links in `transforms/containerlab_topology.py` by including servers in the known-device set that `build_links` filters against
- [x] T034 [P] [US4] Rename `lab/configs/servers/dc1-server1-netplan.yaml` to `dc1-server-netplan.yaml` and `dc2-server1-netplan.yaml` to `dc2-server-netplan.yaml` with `git mv`, and update the referencing binds in `lab/topology.clab.yml`
- [x] T035 [P] [US4] Add unit tests to `tests/unit/test_containerlab_topology.py` for server node emission, netplan bind path, and server-to-leaf link retention

**Checkpoint**: 14 nodes, 24 links — full parity counts per `contracts/parity-matrix.md`.

---

## Phase 6: User Story 3 — Ansible pulls and deploys (P1)

**Independently developable** (disjoint files), but end-to-end validation needs US1–US4 rendering
correctly. Requires T003.

**Goal**: One command brings the lab up from Infrahub with no manual file editing.

- [x] T036 [US3] Fix `target_id` in `lab/playbooks/deploy_clab.yml` to pass a node **UUID** rather than a name, for both the fabric artifact fetch and the per-device config fetch
- [x] T037 [US3] Change `variables:` to `graph_variables:` and `.results` to `.response` in the `query_graphql` task in `lab/playbooks/deploy_clab.yml`, and add `id` to the device-discovery query selection
- [x] T038 [US3] Replace every `item.text | default(item.content)` with `item.text` in `lab/playbooks/deploy_clab.yml`, since `.content` does not exist and the `default()` never fires
- [x] T039 [US3] Write fetched device configs to the directory the topology's `startup-config` references in `lab/playbooks/deploy_clab.yml`, keeping it consistent with T025
- [x] T040 [US3] Add tasks to `lab/playbooks/deploy_clab.yml` that stage every bind source — interface-mapping files into `configs/eos-intf-mapping/` and netplan files into `configs/servers/` — before ContainerLab runs
- [x] T041 [US3] Add explicit existence assertions in `lab/playbooks/deploy_clab.yml` that fail with the device or filename named when an artifact or bind source is missing, so a missing bind fails at deploy rather than as a ContainerLab-created directory at boot
- [x] T042 [US3] Add a target to `lab/Makefile` that runs the playbook with a `FABRIC` variable, following the existing target naming
- [x] T043 [US3] Document in `lab/playbooks/deploy_clab.yml` header comments that `infrahub-sdk` must be importable by the Ansible controller's Python and that `lab/pyproject.toml`'s `ansible` bundle does not ship `opsmill.infrahub`

**Checkpoint**: `make <target> FABRIC=Fabric-L3LS-Multi-Domain` brings up 14 containers.

---

## Phase 7: User Story 5 — Determinism and typed queries (P3)

- [x] T044 [US5] Replace the non-deterministic subnet derivation in `transforms/containerlab_topology.py` with most-common-subnet selection, ties broken by lowest network address
- [x] T045 [US5] Create `transforms/containerlab_link_endpoints.gql` containing the query currently inlined as `_LINK_ENDPOINTS_QUERY`, keeping the `... on DcimInterface` / `... on InterfacePhysical` fragments and declaring `$ids: [ID!]`
- [x] T046 [US5] Register the new query under `queries:` in `.infrahub.yml`
- [x] T047 [US5] Generate return types with `uv run infrahubctl graphql generate-return-types transforms/containerlab_link_endpoints.gql` and commit the generated `transforms/containerlab_link_endpoints_query.py`
- [x] T048 [US5] Replace the inline string literal in `transforms/containerlab_topology.py` with the registered query file read from disk, validating the response through the generated model
- [x] T049 [P] [US5] Add a determinism test to `tests/unit/test_containerlab_topology.py` asserting two renders of identical input are byte-identical
- [x] T050 [P] [US5] Add unit tests to `tests/unit/test_containerlab_topology.py` for the subnet tiebreak rules, including the stray-device case and the no-masked-address case

---

## Phase 8: Polish & Cross-Cutting

- [x] T051 [P] Delete the dead generated orphan `transforms/container_lab_topology.py` and remove its entry from `pyproject.toml`
- [x] T052 [P] Narrow the `**/*_query.py` lint exclusion in `pyproject.toml` so the hand-written `transforms/containerlab_topology_query.py` is linted, and fix anything that surfaces
- [x] T053 [P] Add a parity test to `tests/unit/test_containerlab_topology.py` asserting the full matrix from `contracts/parity-matrix.md`: node count by kind, link count by category, and the set of translated interface-name forms
- [x] T054 Split any function in `transforms/containerlab_topology.py` that exceeds ruff C901 max-complexity 17 into smaller helpers
- [ ] T055 [P] Extend `tests/integration/test_e2e_pipeline.py` to assert the multi-domain artifact contains border leaves and DCI links
- [ ] T056 [P] Add a `graphql-query-smoke` test definition for the new query to guard the silent `error-import` sync failure mode described in research R-009
- [x] T057 [P] Update `lab/README.md` to remove the "Planned: interface mappings from the schema" section as implemented, and document the new Makefile target and required environment
- [x] T058 [P] Add a ContainerLab page under `docs/docs/`, updating `docs/sidebars.ts` if navigation changes, since the docs tree currently has zero ContainerLab coverage
- [x] T059 [P] Update `docs/docs/viewing-artifacts.md` to describe the ContainerLab Topology artifact alongside the existing artifacts
- [x] T060 Run the full gate: `uv run pytest tests/unit` then `uv run invoke lint` (ruff, mypy, yamllint), and resolve every finding
- [x] T061 Regression-check the other five fabrics per quickstart Stage 3, confirming none render empty and that ISIS-LDP's excluded roles appear as warnings
- [ ] T062 Record the integration-test exception from plan.md Complexity Tracking in the pull request description, since `$infrahub-run-integration-tests` is unavailable in this environment

---

## Dependencies

```text
Phase 1 (Setup)
   ↓
Phase 2 (Schema + Objects) ──────┐
   ↓                             │
Phase 3 (US1: roles) ← MVP, only needs manual_objects loaded
   ↓                             │
Phase 4 (US2: kind/image) ←──────┘
   ↓
Phase 5 (US4: servers)  ← needs US2's platform resolution
   ↓
Phase 6 (US3: Ansible)  ← needs T003; validation needs US1–US4
   ↓
Phase 7 (US5: determinism + typed queries)
   ↓
Phase 8 (Polish)
```

**Story independence**: US1 is fully independent and is the MVP. US2 needs Phase 2. US4 needs US2.
US3 touches disjoint files (`lab/`) and can be developed in parallel with US1/US2/US4, but its
end-to-end check needs them landed. US5 is orthogonal and could be done at any point after US2.

## Parallel opportunities

- **Phase 1**: T002, T003 together
- **Phase 2**: T009, T010, T011 together (same file — coordinate edits), then T012
- **Phase 3**: T016 and T017 alongside T014/T015
- **Phase 4**: T026, T027 alongside the implementation tasks
- **Phase 5**: T034, T035 alongside T029–T033
- **Phase 7**: T049, T050 together
- **Phase 8**: T051, T052, T053, T055, T056, T057, T058, T059 all parallel; T060, T061 must follow

## Implementation strategy

**MVP = Phase 1 + Phase 3 (US1).** The border-leaf fix alone converts the multi-domain artifact
from misleading (two disconnected islands) to structurally truthful, and needs no schema change.

Then Phase 2 + Phase 4 (US2) for interfaces and images — the specific thing the request called out.
Then Phase 5 (US4) for full parity counts, Phase 6 (US3) for deployability, and Phase 7–8 for
determinism, typed queries, and docs.

Every checkpoint is independently verifiable via `uv run infrahubctl transform`, so progress can be
confirmed without completing the whole feature.

---

## Deferred with rationale

- **T048** — swap `fetch_link_endpoints` onto the generated model. Types are generated and committed
  (T047), but the model's `__typename` discriminator covers only three endpoint kinds and raises on
  any other, turning a skipped endpoint into a failed artifact. See research R-011.
- **T055** — extend `tests/integration/test_e2e_pipeline.py`. Requires the testcontainer stack.
- **T056** — `graphql-query-smoke` definition. The repo has no `test_*.yml` files; adding the first
  one is a convention change worth its own review.
- **T062** — record the integration-test exception in the PR description. Belongs to the PR, not the
  tree.

## Validated against live Infrahub (branch `clab-multi-domain`)

| Check | Result |
|---|---|
| Nodes | 14 — 12 `arista_ceos` + 2 `linux` |
| Links | 24 — 16 spine↔leaf, 4 DCI, 4 server |
| Kinds/images | `arista/ceos:4.36.0.1F`, `lab-server`, both from the graph |
| Mapping binds | present on all 12 switches |
| Interface translation | no untranslated `Ethernet*` names |
| Management subnet | `10.0.6.0/24` |
| Determinism | two renders byte-identical |
| Gates | 562 unit tests, ruff, ruff-format, mypy, yamllint all clean |

Not validated: the other five fabrics have zero generated devices in this environment, so the
`l2spine`/`l3spine` additions and `p`/`pe`/`rr` exclusions are unexercised against real data.

## Relocation to `ansible/` (post-tasks change)

T036–T043 were written against `lab/playbooks/deploy_clab.yml`. The playbook now lives at
`ansible/deploy_clab.yml`, because `docker-compose.override.yml` mounts only `./ansible` into the
Semaphore container — that directory *is* the Semaphore playbook repository, so a playbook under
`lab/playbooks/` can never be run from Semaphore. All the T036–T043 correctness work carried over
unchanged; only the location and play structure changed.

It is now two plays, because the controller is not necessarily the ContainerLab host:

- Play 1 (`localhost`) — Infrahub work: fabric→UUID, fetch topology + per-device config artifacts,
  assert bodies returned. Writes nothing to the controller's filesystem.
- Play 2 (`clab_hosts`) — stage topology, configs and bind sources onto the lab host, assert every
  bind and `startup-config` path exists **there**, then `containerlab deploy`.

Added: `ansible/inventory_clab.yml` (`clab_hosts`, defaults to local), a second Semaphore template
`Deploy ContainerLab` in `tasks.py` with `fabric` as a survey var, `infrahub-sdk` in
`lab/pyproject.toml`, and `/lab/.venv` to `.yamllint.yml`.

### Verified independently

`ok=24 changed=4 failed=0` with `--skip-tags deploy`: 12 configs staged under Infrahub device names
(`leaf-infrahub-dc1-1-1.cfg` …), plus `configs/{ceos-config,eos-intf-mapping,servers}/`.

### Known gaps

- **`containerlab deploy` itself is unexecuted.** Every run used `--skip-tags deploy` or `--check`.
- **SSH transport unverified** — no second host here, so `clab_hosts` resolved to local.
- **The staged topology is the stale artifact** (12 nodes / 16 links / no binds). Infrahub syncs its
  repository from git, so the new transform output only reaches Ansible after the change is
  committed, the repository re-syncs, and the artifact is regenerated.
- **Semaphore cannot supply bind sources** — `lab/` is not mounted into that container, so
  `clab_dir` must be passed explicitly or the sources pre-staged on the lab host.
- **`--check` is a weak test**: the topology write is skipped, so bind assertions read whatever
  topology already exists. Use `--skip-tags deploy` instead.
