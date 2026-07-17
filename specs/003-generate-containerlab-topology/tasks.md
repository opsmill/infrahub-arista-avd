---
description: "Task list for ContainerLab Topology Generation"
---

# Tasks: ContainerLab Topology Generation

**Input**: Design documents from `/specs/003-generate-containerlab-topology/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — the repo Constitution (Principle IV, Test-Required Quality) mandates tests for
all transforms. Unit tests + a YAML-driven transform render test are required before merge.

**Organization**: Tasks are grouped by user story (P1 → P2 → P3) so each story is an independently
testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 / US2 / US3 (setup, foundational, and polish tasks carry no story label)

## Path Conventions

Single-project Infrahub repo. All paths are relative to repo root
(`/home/ubuntu/dev/infrahub-arista-avd/.emdash/worktrees/infrahub-arista-avd/atg/flat-pans-peel/`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create file skeletons and confirm dependencies so later phases have a place to land.

- [X] T001 Create transform skeletons: empty `transforms/containerlab_topology.gql`, `transforms/containerlab_topology_query.py`, `transforms/containerlab_topology.py` (with `class ContainerLabTopology(InfrahubTransform): query = "containerlab_topology"` and a stub `transform`), and `transforms/templates/containerlab_topology.j2`
- [X] T002 [P] Confirm `PyYAML` is available for import (it ships transitively with `infrahub-sdk[all]`); if `import yaml` fails, add it to `pyproject.toml` dependencies and `uv sync --all-packages`
- [X] T003 [P] Create the interface-mapping resource directory `lab/configs/eos-intf-mapping/` and the Ansible directory `lab/playbooks/` (empty placeholders committed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Query, typed models, and registration that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Write the GraphQL query in `transforms/containerlab_topology.gql` per `contracts/graphql-query.md`: `NetworkFabric(name__value: $name)` → `children` (NetworkPod) → `devices` + `racks.devices`, selecting per `DcimDevice`: `name.value`, `role.value`, `device_type.node.name.value`, `mgmt_ip.node { ... on IpamIPAddress { address { value } } }`, and `interfaces` with `name.value` + `... on DcimEndpoint { connector { node { id } } }`
- [X] T005 Register the query in `.infrahub.yml` under `queries` (`name: containerlab_topology`, `file_path: ./transforms/containerlab_topology.gql`)
- [X] T006 Validate the query executes against a seeded fabric: `uv run infrahubctl query containerlab_topology --variable name=Fabric-A` (or via the GraphQL sandbox) and confirm all required fields resolve
- [X] T007 [P] Implement Pydantic response models in `transforms/containerlab_topology_query.py` mirroring the query shape (fabric → pods → devices/racks → interfaces/connectors), typed so `transform()` never touches raw dicts (Constitution III)
- [X] T008 Register the transform in `.infrahub.yml` under `python_transforms` (`name: containerlab_topology`, `class_name: ContainerLabTopology`, `file_path: ./transforms/containerlab_topology.py`) and add the `artifact_definitions` entry (`name: containerlab_topology`, `artifact_name: "ContainerLab Topology"`, `parameters.name: name__value`, `content_type: application/yaml`, `targets: fabrics`, `transformation: containerlab_topology`) per `contracts/artifact-output.md`

**Checkpoint**: Query returns typed data and the transform/artifact are registered — story work can begin.

---

## Phase 3: User Story 1 - Generate a deployable ContainerLab topology from a fabric (Priority: P1) 🎯 MVP

**Goal**: Render a structurally valid `topology.clab.yml` for a fabric — one cEOS node per network
device (with `mgmt-ipv4`), one `links` entry per connection, plus `name`, `mgmt`, and `kinds`.

**Independent Test**: `uv run infrahubctl transform containerlab_topology --name Fabric-A` produces
YAML that `yaml.safe_load` parses and `containerlab validate` accepts, with correct node/link counts.

### Tests for User Story 1 ⚠️ (write first, ensure they FAIL)

- [X] T009 [P] [US1] In `tests/unit/test_containerlab_topology.py`, add tests over a fixture query response: output parses as YAML; one node per network device; one `links` entry per unique link (bidirectional stored link appears once); device with a mgmt IP gets matching `mgmt-ipv4`; device without a mgmt IP omits `mgmt-ipv4`; empty fabric yields a valid file
- [X] T010 [P] [US1] Add a YAML-driven transform render test (Resources Testing Framework) that renders the transform for a seeded fabric and asserts the output is valid ContainerLab YAML

### Implementation for User Story 1

- [X] T011 [US1] In `transforms/containerlab_topology.py`, implement fabric traversal (mirroring `transforms/cabling_plan.py`): walk pods → `devices` + `racks.devices`, collecting devices and unique `NetworkLink` ids from interface `connector`s
- [X] T012 [US1] Implement link-endpoint resolution (inline from the query if available, else a batched `NetworkLink(ids: [...])` fetch like `CablingPlan`) yielding, per link, two `(device_name, interface_name)` endpoints; dedupe by link id (FR-009)
- [X] T013 [US1] Build the intermediate `ClabTopology` model (per `data-model.md` §B): `name` from fabric; `nodes` (one per network device, `kind: arista_ceos`, `mgmt-ipv4` when present); `links` (endpoints as `"<node>:<interface>"` using the raw interface name for now — translation added in US2); sort nodes and links deterministically (FR-012)
- [X] T014 [US1] Derive the `mgmt` block: `network: clab-<fabric>-mgmt` and `ipv4-subnet` from the covering management prefix of the devices' `mgmt_ip` addresses (strip masks to bare host addresses on nodes) per research R2
- [X] T015 [US1] Define the `topology.kinds` block (`arista_ceos` with default image `arista/ceos:4.36.0.1F`, `startup-config` path using `__clabNodeName__`) per research R3
- [X] T016 [US1] Implement rendering in `transforms/templates/containerlab_topology.j2` (or `yaml.safe_dump` of the built dict) producing `name`/`mgmt`/`topology.{kinds,nodes,links}`; `transform()` returns the rendered string
- [X] T017 [US1] Handle US1 edge cases: empty fabric (empty/absent nodes+links, no exception); link endpoint missing an interface name → skip with a warning
- [X] T018 [US1] Run the independent test: `uv run infrahubctl transform containerlab_topology --name Fabric-A > /tmp/topology.clab.yml`, confirm `yaml.safe_load` parses it and node/link counts match the fabric

**Checkpoint**: A fabric renders to a structurally valid ContainerLab file (MVP). Links carry raw
EOS interface names — made deploy-correct in US2.

---

## Phase 4: User Story 2 - Interface-mapping-aware links and binds (Priority: P2)

> **Status update (design pivot):** Investigation showed devices use plain `Ethernet<N>` interfaces
> and have no `device_type`. The algorithmic translation (`Ethernet<N>` → `eth<N>`, T024) *is* cEOS's
> default mapping, so **no `EosIntfMapping.json` bind is needed** for the current data. Per user
> direction, the authoritative mapping will live as a `CoreFileObject` on `DcimDeviceType` and is
> **deferred to a dedicated schema-first `/speckit.specify` cycle** (schema + device_type-populating
> generator + upload generator + transform rewire). The interim "generate per-role mapping files +
> binds" approach was built and then removed. T024 (algorithmic translation) shipped; T021–T023,
> T025–T026 (device-type binds) move to the schema cycle.

**Goal (revised)**: Link endpoints use ContainerLab short names via algorithmic translation. Per
-device-type `EosIntfMapping.json` binds are handled in the follow-up schema cycle.

**Independent Test**: For a fabric with ≥2 device types, each node binds the mapping file matching
its device type, and a spine↔leaf link's endpoints are the mapped short names (which the mapping
files translate back to the EOS interfaces in Infrahub); an unmapped device type fails loudly.

### Tests for User Story 2 ⚠️ (write first, ensure they FAIL)

- [X] T019 [P] [US2] In `tests/unit/test_containerlab_topology.py`, add tests: device-type → correct mapping-file bind path; `Ethernet1/1` (per fixture model) translated to the model's short name on BOTH ends of a link; server endpoint rendered as `linux` with no EOS translation; unmapped device type raises a named error; interface absent from the mapping raises a named error
- [X] T020 [P] [US2] Add a fixture pair of interface-mapping JSON files under `tests/` (or fixtures dir) covering two models so translation can be tested without touching `lab/`

### Implementation for User Story 2

- [X] T021 [P] [US2] Author the real interface-mapping files in `lab/configs/eos-intf-mapping/` for every device-type model on the seeded fabrics — currently `PowerSwitch Z9864F-ON` and `PowerSwitch S5232F-ON` — mapping ContainerLab short names to the models' Infrahub `Ethernet1/N` names, per `contracts/interface-mapping.md`. Decide and document the model→filename scheme (exact string vs slug)
- [X] T022 [US2] In `transforms/containerlab_topology.py`, implement the mapping loader: read `lab/configs/eos-intf-mapping/<model>.json`, parse `EthernetIntf`, and build the inverse map (EOS name → ContainerLab short name); cache per model
- [X] T023 [US2] Resolve each device's mapping file from `device_type.node.name.value` and add the per-node `binds` entry `configs/eos-intf-mapping/<model>.json:/mnt/flash/EosIntfMapping.json:ro` (FR-007); raise a named error if the file is missing (FR-014)
- [X] T024 [US2] Replace the raw endpoint naming from US1: translate each endpoint's EOS interface name to its ContainerLab short name via that endpoint device's inverse mapping (FR-008); raise a named error if an interface has no mapping entry
- [X] T025 [US2] Render server endpoints as `linux` nodes with their raw short interface names and NO EOS translation (FR-010); add the `linux` kind to `topology.kinds` only when servers are present
- [X] T026 [US2] Run the independent test: render a fabric spanning both device types and confirm per-node binds are correct and 0 untranslated EOS names remain in `links` (grep the output for `Ethernet`)

**Checkpoint**: The rendered topology is deploy-correct — interfaces and binds line up with cEOS.

---

## Phase 5: User Story 3 - Ansible pulls the topology and deploys the lab (Priority: P3)

**Goal**: One Ansible command pulls the topology artifact (+ referenced files) from Infrahub and
deploys the lab with ContainerLab.

**Independent Test**: With a fabric's artifacts generated, the playbook fetches the topology,
stages the interface-mapping files and per-device configs, and `containerlab deploy` brings the
cEOS nodes to a running state.

### Implementation for User Story 3

- [ ] T027 [US3] Confirm the `opsmill.infrahub` artifact-retrieval mechanism against the installed collection (`uv run ansible-galaxy collection list opsmill.infrahub`; check module/lookup docs) — do not guess module names (research R6)
- [X] T028 [US3] Write `lab/playbooks/deploy_clab.yml`: use `opsmill.infrahub` to fetch the fabric's "ContainerLab Topology" artifact and write it to the lab directory (FR-019)
- [X] T029 [US3] In the playbook, stage the files the topology references — the repo-bundled interface-mapping files at `configs/eos-intf-mapping/` and the per-device AVD EOS config artifacts (fetched from Infrahub) at the `startup-config` paths — before deploy (FR-020)
- [X] T030 [US3] Add the `containerlab deploy` invocation and success/failure reporting to the playbook (FR-021); wire an ergonomic entry point (e.g. a `lab/` Make target or documented `ansible-playbook` command)
- [ ] T031 [US3] Run the independent test: `cd lab && uv run ansible-playbook -i avd/inventory.yml playbooks/deploy_clab.yml` against a seeded fabric with a ContainerLab-capable host, confirming nodes reach running state (SC-007)

**Checkpoint**: End-to-end — fabric in Infrahub to running virtual lab with no manual file copying.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T032 [P] Run `inv lint` (ruff + mypy + yamllint) and fix all findings; keep `transform()` and helpers under ruff C901 max-complexity=17 (split methods as needed) — Constitution IV
- [X] T033 [P] Render the artifact for BOTH seeded fabrics (`Fabric-A`, `Fabric-B`) and validate each with `containerlab validate` (SC-006)
- [X] T034 [P] Document the transform and lab workflow: add a row to the transforms table in `CLAUDE.md` and a short usage note (rendering + Ansible deploy) referencing `quickstart.md`
- [X] T035 Run the full `quickstart.md` validation end to end (render → test → lint → deploy) and confirm all Success Criteria SC-001…SC-007

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational.
  - US1 (P1) is the MVP and should land first.
  - US2 (P2) depends on US1 (it replaces US1's raw endpoint naming and adds binds).
  - US3 (P3) depends on US1/US2 producing a correct artifact.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: After Foundational. No dependency on other stories. Independently testable.
- **US2 (P2)**: After US1 (extends the same transform's link/node rendering). Independently testable
  via multi-device-type render + bind/translation assertions.
- **US3 (P3)**: After US2 (needs a deploy-correct artifact). Independently testable via the playbook.

### Within Each User Story

- Tests written first and failing before implementation (Constitution IV).
- Data traversal/model before rendering; rendering before edge-case hardening.

### Parallel Opportunities

- Setup: T002, T003 in parallel.
- Foundational: T007 can proceed in parallel with `.infrahub.yml` edits once the query (T004) exists.
- US1 tests T009, T010 in parallel. US2 tests T019, T020 in parallel; mapping-file authoring T021 is
  independent of the loader/resolver code and can run alongside test writing.
- Polish: T032, T033, T034 in parallel.

---

## Parallel Example: User Story 1

```bash
# Write both US1 test tasks together (they touch different concerns):
Task: "T009 Unit tests for node/link/dedup/mgmt behavior in tests/unit/test_containerlab_topology.py"
Task: "T010 YAML-driven transform render test for a seeded fabric"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 → **STOP & VALIDATE**: a fabric renders
to a structurally valid ContainerLab file. Demo the MVP.

### Incremental Delivery

1. Setup + Foundational → foundation ready.
2. US1 → structurally valid topology (MVP).
3. US2 → deploy-correct topology (binds + interface translation).
4. US3 → one-command Ansible pull + ContainerLab deploy.

### MVP Scope

**User Story 1** — rendering a valid `topology.clab.yml` from a fabric — is the recommended MVP.

---

## Notes

- [P] = different files, no incomplete dependencies. [Story] label maps each task to its user story.
- Fail loudly: unmapped device type or interface must raise a clear, named error — never emit a
  silently wrong file (SC-004/SC-005).
- Deterministic output: sort nodes and links before rendering so unchanged inputs produce identical
  YAML (FR-012).
- Ansible assets under `lab/` stay outside the Python lint/test targets; US3 acceptance is functional.
- Commit after each task or logical group.
