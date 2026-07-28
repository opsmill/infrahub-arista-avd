---
description: "Task list for Normalized Device Design Entities (schema cycle)"
---

# Tasks: Normalized Device Design Entities

**Input**: Design documents from `/specs/005-device-design-entities/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/schema-contract.md, quickstart.md

**Tests**: Included and treated as REQUIRED — Constitution Principle IV mandates schema-check evidence, integration coverage of the schema migration + repo load, and unit tests for any helper. They are not optional for this repo.

**Scope**: This is a **schema-only** cycle. It delivers the additive schema (Stage 1) as the working increment. Data migration (Stage 2) and old-field removal (Stage 3) are authored here but their **load is gated** behind the follow-on generator and objects cycles (research Decision 8). Generator/object/protocol-consumer edits are separate `/speckit-specify` cycles.

**Format**: `[ID] [P?] [Story?] Description with file path` — `[P]` = parallelizable (different files, no incomplete deps).

**Authoritative skill**: All schema YAML MUST be authored and validated with the `infrahub-managing-schemas` skill.

## Implementation status (2026-07-28)

**Complete — 21/23 tasks done, 2 descoped as N/A.** The staged migration was collapsed:
because the project is pre-production with no populated live instance, `state: absent`
and the backfill helper were unnecessary, so the 8 legacy fields were deleted outright.

Validated on a live local stack:

- Schema loads clean with the legacy fields gone; `protocols.py`, `schema.graphql`, and
  all three generator `*_query.py` models regenerated and confirmed free of all 8 fields.
- Seed objects load and materialize 39 device designs (2 fabric, 10 pod, 27 rack).
- Migration parity: all 44 sizing containers (7 fabrics, 12 pods, 25 racks) match `main`'s
  legacy `(template, count)` values exactly.
- `ruff`, `ruff format`, `mypy`, `yamllint` clean; 501 unit tests pass; the schema-contract
  integration test (`tests/integration/test_device_design_schema.py`) passes.

Convergence (resize / remove / decrease) and repeated-run idempotence were verified
against the pre-rebase tree and are unchanged in intent by the rebase. Note that since
`main` made `_trigger_generator` raise rather than log, a standalone
`infrahubctl generator` chain now aborts partway without a registered `CoreRepository`
(the `generate-avd-device-hostvar` definition is missing), so re-running those two gates
requires the repository-backed path — the nightly full-stack job or
`pytest tests/integration/test_e2e_pipeline.py -m e2e`.

Descoped (recorded, not skipped by omission):

- **T018/T019** (live-instance migration helper + its unit tests) — no populated live
  instance exists to migrate. Revisit only if an in-place migration is ever needed.

## Path Conventions

Infrahub reference-design repo (single project). Schema under `schemas/`, generated protocols under `src/solution_arista_avd/`, tests under `tests/`, docs under `docs/docs/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch and file scaffold for a branch-first schema rollout.

- [X] T001 Confirm Infrahub reachable (`uv run infrahubctl info` → Connection Status ✅) and create the rollout branch `uv run infrahubctl branch create device-design-entities`
- [X] T002 [P] Create `schemas/device_design.yml` scaffold with the `# yaml-language-server` `$schema` header and `version: "1.0"` (empty `generics:`/`nodes:`/`extensions:` sections)
- [X] T003 [P] Capture a clean baseline: run `uv run infrahubctl schema check schemas/` and confirm the current schema set validates with zero errors (guards against pre-existing breakage before edits)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `NetworkDeviceDesign` generic is inherited by every concrete tier node, so it MUST exist before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Define the `NetworkDeviceDesign` generic in `schemas/device_design.yml` per data-model.md: `namespace: Network`, `branch: agnostic`, `include_in_menu: false`, `display_label: role__value`; attributes `role` (Dropdown; choices super_spine/spine/leaf/l2leaf) and `device_quantity` (Number, `optional: false`, `parameters: {min_value: 1}`); relationship `device_template` (peer `CoreObjectTemplate`, `kind: Attribute`, `cardinality: one`, `optional: false`, `on_delete: no-action`)
- [X] T005 Validate the generic: `uv run infrahubctl schema check schemas/` passes. If a `device_template` identifier collision is reported across inheriting kinds, apply the per-node identifier fallback from research Decision 5 and re-check

**Checkpoint**: Generic in place and schema-valid — tier stories can begin.

---

## Phase 3: User Story 1 - Normalize rack device designs (leaf + L2 leaf) (Priority: P1) 🎯 MVP

**Goal**: Racks express leaf and L2-leaf designs through a `device_designs` many relationship of `NetworkRackDeviceDesign` entities instead of the fixed `leaf_switch_template`/`amount_of_leafs` and `l2leaf_switch_template`/`amount_of_l2leafs` fields.

**Independent Test**: On the branch, create a `LocationRack`, attach a `leaf` design (qty 2) and an `l2leaf` design (qty 1); confirm the rack renders its designs, rejects a duplicate-role design, and cascades on delete while preserving the template.

### Tests for User Story 1 ⚠️ (write first, expect FAIL before schema load)

- [X] T006 [P] [US1] Integration test in `tests/integration/test_device_design_schema.py` covering: (a) create `NetworkRackDeviceDesign` with role `leaf`, qty 2, a `device_template`; (b) second `leaf` design on the same rack is rejected by the `(rack, role)` uniqueness constraint; (c) deleting the rack cascade-deletes its designs while the `CoreObjectTemplate` survives (maps SC-003/SC-004/SC-005, US1 scenarios 2–4)

### Implementation for User Story 1

- [X] T007 [US1] Define the `NetworkRackDeviceDesign` concrete node in `schemas/device_design.yml`: `inherit_from: [NetworkDeviceDesign]`, `namespace: Network`, `branch: agnostic`, `include_in_menu: false`, `Parent` relationship `rack` → `LocationRack` (`cardinality: one`, `optional: false`, `identifier: "rack__device_designs"`), `uniqueness_constraints: [["rack", "role__value"]]`, `human_friendly_id: ["rack__name__value", "role__value"]`
- [X] T008 [US1] Add the `device_designs` Component relationship to `LocationRack` via the `extensions:` block in `schemas/device_design.yml`: peer `NetworkRackDeviceDesign`, `kind: Component`, `cardinality: many`, `optional: true`, `on_delete: cascade`, `identifier: "rack__device_designs"` (must match T007)
- [X] T009 [US1] Load and regenerate: `uv run infrahubctl schema check schemas/ --branch device-design-entities` → `schema load schemas --branch device-design-entities` → `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py`
- [X] T010 [US1] Run the acceptance checks from quickstart.md Stage 1 (steps 1–3) against the branch and confirm T006's integration test passes (SC-003/SC-004/SC-005)

**Checkpoint**: Rack device designs fully functional and independently testable (MVP).

---

## Phase 4: User Story 2 - Apply the pattern to pod (spines) and fabric (super-spines) (Priority: P2)

**Goal**: `NetworkPod` and `NetworkFabric` express designs through the same `device_designs` relationship, replacing `spine_switch_template`/`amount_of_spines` and `super_spine_switch_template`/`amount_of_super_spines`.

**Independent Test**: On the branch, attach a `spine` design to a pod and a `super_spine` design to a fabric; confirm both render through the identical entity shape and pass schema check.

### Tests for User Story 2 ⚠️

- [X] T011 [P] [US2] Integration test in `tests/integration/test_device_design_schema.py` covering: create a `NetworkPodDeviceDesign` (role `spine`) on a pod and a `NetworkFabricDeviceDesign` (role `super_spine`) on a fabric, and assert both expose `role`/`device_quantity`/`device_template` and enforce `(container, role)` uniqueness (maps SC-006 additive part, US2 scenarios 1–3)

### Implementation for User Story 2

- [X] T012 [US2] Define the `NetworkPodDeviceDesign` concrete node in `schemas/device_design.yml`: `inherit_from: [NetworkDeviceDesign]`, `Parent` `pod` → `NetworkPod` (`identifier: "pod__device_designs"`), `uniqueness_constraints: [["pod", "role__value"]]`, `human_friendly_id: ["pod__name__value", "role__value"]`
- [X] T013 [US2] Define the `NetworkFabricDeviceDesign` concrete node in `schemas/device_design.yml`: `inherit_from: [NetworkDeviceDesign]`, `Parent` `fabric` → `NetworkFabric` (`identifier: "fabric__device_designs"`), `uniqueness_constraints: [["fabric", "role__value"]]`, `human_friendly_id: ["fabric__name__value", "role__value"]`
- [X] T014 [US2] Add `device_designs` Component relationships to `NetworkPod` and `NetworkFabric` via the `extensions:` block in `schemas/device_design.yml` (each `kind: Component`, `cardinality: many`, `optional: true`, `on_delete: cascade`, matching identifiers `pod__device_designs` / `fabric__device_designs`)
- [X] T015 [US2] Load and regenerate (`schema check` → `schema load --branch` → `protocols`); confirm all three tiers render designs through the same shape and T011 passes (SC-006 additive part)

**Checkpoint**: All three tiers carry device designs through the normalized entity — additive schema (Stage 1) complete.

---

## Phase 5: User Story 3 - Add a new device type without a schema change (Priority: P3)

**Goal**: Prove the normalization pays off — a new supported-role design can be added at the data layer with no schema edit.

**Independent Test**: With the additive schema loaded and no further schema change, add a supported-role design to a container via GraphQL/object load and confirm acceptance; change its `device_quantity` and confirm no schema change is needed.

- [X] T016 [US3] Data-only validation: with no edit to `schemas/`, add a `NetworkRackDeviceDesign` (or pod/fabric equivalent) for a supported role via the GraphQL API or an ad-hoc `objects/` entry on the branch, and update its `device_quantity`; confirm both succeed with no schema reload (SC-007, US3 scenarios 1–2)
- [X] T017 [P] [US3] Document that tier↔role validity (fabric→super_spine, pod→spine, rack→leaf/l2leaf) is intentionally NOT schema-enforced (research Decision 6) and record a follow-on Check cycle as the candidate owner — note in `specs/005-device-design-entities/research.md` cross-reference and the follow-on handoff (T023)

**Checkpoint**: Extensibility outcome demonstrated; all user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting (Migration & Removal — staged, load gated)

**Purpose**: Author the migration and removal so the end-to-end change is ready, but keep their load gated behind the follow-on generator + objects cycles (research Decision 8, FR-062).

- [~] T018 **N/A — descoped**: no live populated instance to migrate (project is pre-production), so the one-time backfill helper is not needed. The Objects cycle (003) rewrote `objects/*.yml` instead.
- [~] T019 **N/A — descoped**: no migration helper to test (see T018).
- [X] T020 Removal of the 8 old fields — **superseded**: `state: absent` was unnecessary pre-production, so the field definitions were deleted outright from `schemas/logical_design.yml` (4), `schemas/location_extensions.yml` (2), and `schemas/l3ls_extensions.yml` (2, whole `LocationRack` extension block). Verified absent from the loaded schema, the regenerated `protocols.py`, and the exported `schema.graphql`.
- [X] T021 Integration test in `tests/integration/test_device_design_schema.py` — rewritten for the completed migration: asserts `device_designs` exists (peer + cardinality) and all 8 legacy fields are gone, plus the design nodes' `role`/`device_quantity`/`device_template` surface. Every assertion cross-checked against the live loaded schema.
- [X] T022 [P] Update developer-guide docs describing the entity: `docs/docs/developer-guide/schemas.md` and `docs/docs/developer-guide/architecture.md` (device-design model, three-tier `device_designs`, `(container, role)` key, absence-means-none); update `docs/sidebars.ts` only if navigation changes
- [X] T023 Full end-to-end run captured: `schema check` → `schema load` (24 schemas) → `protocols` regen → `graphql export-schema` → menu + object load → fabric/pod/rack generator chain, with `ruff`/`mypy`/`yamllint` clean and 417 unit tests passing. The Generator + Objects cycles (002/003) are implemented in the same tree, so the handoff is a merge, not a hand-off.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup. **Blocks all user stories** (generic must exist to inherit).
- **US1 (Phase 3)**: depends on Foundational. Delivers the MVP.
- **US2 (Phase 4)**: depends on Foundational. Logically independent of US1 but edits the **same file** (`schemas/device_design.yml`), so sequence its edits after US1's.
- **US3 (Phase 5)**: depends on US1 **and** US2 being loaded (it demonstrates data-only add across the tiers).
- **Polish (Phase 6)**: depends on the additive schema (US1+US2) being complete; T020's load is additionally gated behind the follow-on generator + objects cycles.

### Within Each User Story

- Integration test authored first (expected to fail pre-load) → concrete node → container relationship → load + protocol regen → acceptance verification.
- Both sides of a Component/Parent pair share an `identifier` — author the concrete node's `Parent` and the container's `Component` together before loading.

### Parallel Opportunities

- Setup: T002 and T003 run in parallel (different concerns).
- US1 vs US2 concrete-node authoring is **not** `[P]` — both edit `schemas/device_design.yml`. Their integration tests (T006, T011) are separate files and can be written in parallel.
- Polish: T018/T019 (migration helper + its tests) and T022 (docs) are `[P]` — different files.

---

## Parallel Example: cross-story test authoring

```bash
# Integration tests live in separate files — author in parallel:
Task: "T006 integration test in tests/integration/test_device_design_schema.py"
Task: "T011 integration test in tests/integration/test_device_design_schema.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational (generic) → Phase 3 US1 (rack).
2. **STOP and VALIDATE**: rack device designs create, reject duplicate roles, cascade correctly (T010).
3. This is a shippable, independently testable increment on the branch.

### Incremental Delivery

1. Setup + Foundational → generic ready.
2. US1 (rack) → validate → the normalized pattern is proven at the busiest tier.
3. US2 (pod + fabric) → validate → uniform model across all three tiers (additive Stage 1 done).
4. US3 → confirm data-only extensibility.
5. Polish: stage migration + removal; **do not load removals** until the follow-on generator + objects cycles land.

### Rollout safety

- Everything loads on the `device-design-entities` branch and merges via a proposed change — never a direct default-branch load.
- Stage 1 (Phases 1–5) is purely additive and safe to load immediately.
- Stage 3 removal (T020) is destructive and gated — loading it while a generator or seed file still reads the old fields breaks generation (research Decision 8).

---

## Notes

- `[P]` = different files, no incomplete dependencies.
- `[Story]` label maps each task to its user story for traceability; Setup/Foundational/Polish carry no story label by design.
- Regenerate `src/solution_arista_avd/protocols.py` after every schema load — never hand-edit it (Constitution Principle III).
- Follow-on `/speckit-specify` cycles required for the end-to-end change: **Generator** (largest), **Objects**, and docs (see `contracts/schema-contract.md` → "Consumers to update").
