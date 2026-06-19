---
description: "Task list for Schema-Driven AVD IP Pools"
---

# Tasks: Schema-Driven AVD IP Pools

**Input**: Design documents from `/specs/015-schema-driven-ip-pools/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/schema-extension.md, quickstart.md

**Tests**: No automated test tasks are included — the spec requests no TDD, and validation for a schema change is via `infrahubctl schema check` + `inv load` + enforcement check (see quickstart.md). Generator behavior tests belong to the follow-up generator cycle.

**Organization**: Tasks are grouped by the three user stories from spec.md. Note the corrected scope from research.md (R1): the four `uplink_pool`/`vtep_pool`/`mlag_peer_pool`/`mlag_l3_pool` relationships already exist in `schemas/l3ls_extensions.yml`; only `loopback_pool` is new, and the work is "add new relationship + flip optionality + backfill seed data."

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 from spec.md

## Path Conventions

Single-project Infrahub solution. Schema YAML in `schemas/`, seed data in `objects/`, generated protocols in `src/solution_arista_avd/`. Paths are relative to repo root `/Users/alex/dev/opsmill/infrahub-arista-avd`.

⚠️ **Cross-story file sharing**: US1 and US3 both edit `objects/04a_l3ls_pools.yml` and `objects/10_fabric.yml`, and US3 re-edits `schemas/l3ls_extensions.yml`. These two stories therefore cannot be fully parallelized — sequence US1 → US3 (or assign both to one person).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the working environment before editing declarative artifacts

- [X] T001 Confirm branch `015-schema-driven-ip-pools` is checked out and Infrahub is reachable via `uv run infrahubctl info` (Address shows ✅)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Introduce the one genuinely new model element so every story can build on it. Added as **optional first** (migration rule) so nothing breaks until seed data is populated in US1/US3.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Add the new `loopback_pool` relationship to the `- kind: NetworkFabric` entry in `schemas/l3ls_extensions.yml` under `relationships:` — `peer: CoreIPPrefixPool`, `kind: Attribute`, `cardinality: one`, `optional: true` (tightened to false later in T011), `branch: aware`, `identifier: "fabric__loopback_pool"`, `label: "Loopback IP Pool"`, `description: "IP prefix pool for device loopback (loopback0) addressing"`, `order_weight: 10600`. See contracts/schema-extension.md §1.
- [X] T003 Validate the edit: `uv run infrahubctl schema check schemas/` — expect zero errors (a duplicate-identifier error means `fabric__loopback_pool` collided)
- [X] T004 Regenerate protocols: `infrahubctl protocols --out src/solution_arista_avd/protocols.py`; confirm the `NetworkFabric` protocol now exposes `loopback_pool`

**Checkpoint**: New `loopback_pool` relationship exists (optional), schema validates, protocols typed — stories can proceed.

---

## Phase 3: User Story 1 - Model fabric-level underlay/overlay IP pools (Priority: P1) 🎯 MVP

**Goal**: The fabric device-loopback pool is modeled and Fabric-A is fully pool-linked (uplink + vtep already set; loopback added), replacing the `10.255.0.0/24` literal that collided with the management subnet.

**Independent Test**: `infrahubctl schema check schemas/` passes and a load of schema + objects leaves Fabric-A resolving `uplink_pool`, `vtep_pool`, and `loopback_pool` over GraphQL (each pool's first resource prefix retrievable per the `_extract_pool_prefix` pattern). Non-breaking: all relationships still optional at this point.

### Implementation for User Story 1

- [X] T005 [P] [US1] In `objects/04a_l3ls_pools.yml`, append an `IpamPrefix` for `10.255.2.0/24` (role e.g. `pod_loopback`) and a `CoreIPPrefixPool` named `Fabric-A-Loopback-Pool` (`default_member_type: prefix`, `default_prefix_type: IpamPrefix`, `default_prefix_length: 32`, `ip_namespace: default`, `resources: ["10.255.2.0/24"]`), mirroring the existing `Fabric-A-VTEP-Pool` document shape. Prefix MUST NOT overlap mgmt `10.255.0.0/24`.
- [X] T006 [US1] In `objects/10_fabric.yml`, add `loopback_pool: "Fabric-A-Loopback-Pool"` to the Fabric-A `data` entry (alongside its existing `uplink_pool` / `vtep_pool`).
- [X] T007 [US1] Validate: `uv run infrahubctl schema check schemas/` passes, then `inv load` (or `inv load-schema` + object load) succeeds; verify via GraphQL that Fabric-A's `uplink_pool`, `vtep_pool`, and `loopback_pool` each resolve to a pool with a retrievable resource prefix.

**Checkpoint**: Fabric-A is fully pool-linked and the device-loopback pool is no longer a hidden literal. Repo still loads cleanly (relationships optional).

---

## Phase 4: User Story 2 - Model pod-level MLAG IP pools (Priority: P2)

**Goal**: Confirm the pod MLAG pools behave correctly — they already exist in the schema as optional (research R1), and not every pod uses them.

**Independent Test**: A pod with MLAG pools (Pod-A2/A3) resolves both relationships; a pod without them (Pod-A1/Pod-B*) loads successfully.

### Implementation for User Story 2

- [X] T008 [US2] Verify (no schema change) in `schemas/l3ls_extensions.yml` that `mlag_peer_pool` (`pod__mlag_peer_pool`) and `mlag_l3_pool` (`pod__mlag_l3_pool`) on `- kind: NetworkPod` are `peer: CoreIPAddressPool`, `cardinality: one`, `optional: true`; confirm via GraphQL that Pod-A2/Pod-A3 resolve both pools and that Pod-A1 (no MLAG pools) loads without error. Do NOT rename `mlag_l3_pool` (research R4 — the generator's `mlag_l_3_pool`/`mlag_l3_pool` getattr handling stays).

**Checkpoint**: MLAG pool modeling validated; remains optional per FR-021.

---

## Phase 5: User Story 3 - Seed data and existing fabrics carry valid pools (Priority: P3)

**Goal**: Complete the migration — backfill Fabric-B's missing pools, then flip the three fabric pools to mandatory so the platform enforces them (SC-003). This is the step that makes "fail loudly when unset" real.

**Independent Test**: After backfill + flip, `infrahubctl schema check schemas/` passes, a full `inv load` of both fabrics succeeds with zero missing-mandatory-relationship errors, and attempting to save a `NetworkFabric` without `loopback_pool` (or uplink/vtep) is rejected by the platform.

### Implementation for User Story 3

- [X] T009 [US3] In `objects/04a_l3ls_pools.yml`, append the Fabric-B pools (each `CoreIPPrefixPool` with its supporting `IpamPrefix`, non-overlapping with Fabric-A allocations): `Fabric-B-Uplink-Pool` (resource `10.254.252.0/22`, `default_prefix_length: 31`), `Fabric-B-VTEP-Pool` (resource `10.254.1.0/27`, `default_prefix_length: 32`), `Fabric-B-Loopback-Pool` (resource `10.255.3.0/24`, `default_prefix_length: 32`). _Edits the same file as T005 — sequence after it._
- [X] T010 [US3] In `objects/10_fabric.yml`, add `uplink_pool: "Fabric-B-Uplink-Pool"`, `vtep_pool: "Fabric-B-VTEP-Pool"`, and `loopback_pool: "Fabric-B-Loopback-Pool"` to the Fabric-B `data` entry. _Edits the same file as T006 — sequence after it._
- [X] T011 [US3] In `schemas/l3ls_extensions.yml`, change `optional` from `true` to `false` on the `NetworkFabric` relationships `uplink_pool`, `vtep_pool`, and `loopback_pool` (per contracts/schema-extension.md §1). _Re-edits the file from T002._
- [X] T012 [US3] Validate the migration: `uv run infrahubctl schema check schemas/` passes; full `inv load` completes with both fabrics fully pool-linked (SC-005); attempt to create/save a `NetworkFabric` without `loopback_pool` and confirm the platform rejects it (SC-003); confirm a `NetworkPod` still saves without MLAG pools (FR-021).

**Checkpoint**: All five pyAVD pools are traceable to a schema relationship (SC-004); the model enforces the three fabric pools; no fabric depends on a literal.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] Run `inv lint-yaml` over the edited schema and object YAML; fix any findings
- [X] T014 Run the full quickstart.md "Done when" checklist end-to-end (SC-001 → SC-006), confirming loopback prefixes `10.255.2.0/24` / `10.255.3.0/24` do not overlap mgmt `10.255.0.0/24`
- [X] T015 Record the follow-up generator-cycle work (out of scope here): remove the `10.250.0.0/16` / `10.251.0.0/24` literals at `generators/generate_avd_device_hostvar.py:383-384`, replace the `10.255.0.0/24` literal at line 523 by reading `fabric.loopback_pool`, and raise a clear error when a required pool is linked-but-empty. Capture as a tracked note / next `/speckit.specify` for the generator artifact.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies
- **Foundational (Phase 2)**: depends on Setup; **BLOCKS all stories** (adds the `loopback_pool` model element + protocols)
- **US1 (Phase 3)**: depends on Foundational
- **US2 (Phase 4)**: depends on Foundational; independent of US1/US3 (verification only)
- **US3 (Phase 5)**: depends on Foundational AND on US1 completing first — shares `objects/04a_l3ls_pools.yml` (T009 after T005) and `objects/10_fabric.yml` (T010 after T006), and re-edits the schema from T002 (T011). The mandatory flip (T011) requires Fabric-A's loopback pool (US1) and Fabric-B's backfill (T009/T010) to already be in place, else the load breaks.
- **Polish (Phase 6)**: depends on US1 + US3 (US2 optional)

### Within Each User Story

- US1: T005 (pool object) before T006 (reference) before T007 (load/verify)
- US3: T009 + T010 (backfill) before T011 (flip mandatory) before T012 (validate enforcement)

### Parallel Opportunities

- Limited by design: T005 [P] and T013 [P] are the only safely-parallel tasks (distinct files, no incomplete dependencies). US1 and US3 cannot run in parallel because they share two object files and the schema file.

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup (T001) → Foundational (T002–T004) → US1 (T005–T007).
2. **STOP and VALIDATE**: Fabric-A fully pool-linked, loopback literal eliminated for Fabric-A, repo still loads (relationships optional). Deployable as a non-breaking increment.

### Incremental Delivery

1. Foundational → US1 (MVP, non-breaking).
2. US2 verification (no change; confirms FR-021).
3. US3 (backfill Fabric-B + flip to mandatory) → enforcement live. This is the breaking/migration step and must land as one unit (T009→T012).
4. Polish + record generator-cycle follow-up.

---

## Notes

- The spec (FR-010/FR-011/FR-013/FR-014) predates the discovery that these relationships already exist — research.md R1 reconciles it. Tasks here implement the *corrected* scope.
- No Python is edited this cycle except generated `src/solution_arista_avd/protocols.py` (T004).
- Removing the generator literals is intentionally deferred (T015) to keep this a clean schema-only cycle.
- Commit after each phase; the US3 flip-to-mandatory is the point of no return for partially-populated live data.
