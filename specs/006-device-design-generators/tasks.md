---
description: "Task list for Device-Design-Driven Fabric Generators (generator cycle)"
---

# Tasks: Device-Design-Driven Fabric Generators

**Input**: Design documents from `/specs/006-device-design-generators/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/generator-io-contract.md, quickstart.md

**Tests**: Included and treated as REQUIRED — Constitution Principle IV mandates unit tests for the shared helper, integration coverage of the generator chain (`$infrahub-run-integration-tests`), and generator idempotence evidence (`$infrahub-test-generator-idempotence`).

**Scope**: Behavior-preserving refactor of `generate_fabric`/`generate_pod`/`generate_rack` to read `device_designs` per role instead of the legacy `amount_of_*`/`*_switch_template` fields, plus the two cross-tier completeness reads. **Hard cutover** — co-requisite with the Objects cycle (which populates `device_designs`); the two land together. The 005 Stage-3 schema removal stays gated until after both.

**Format**: `[ID] [P?] [Story?] Description with file path` — `[P]` = parallelizable (different files, no incomplete deps).

**Authoritative skill**: Author all generator/query changes with the `infrahub-managing-generators` skill.

## Implementation status (2026-07-24)

All generator **code** is implemented and unit-validated; **runs are deferred** (per the "author all code, defer runs" decision) because they need the co-requisite Objects data + 001 merged. 11/23 tasks complete.

Done and validated:
- **T003/T004** — resolver `resolve_device_designs()` / `device_design_for()` on `GeneratorMixin`. Tests live in `tests/unit/test_generator_mixin.py` (alongside the other mixin tests) rather than a new `test_device_design_resolution.py` — same coverage, better cohesion. 9 tests pass.
- **T006–T008, T011–T016** — all three `.gql` queries rewritten to `device_designs` (+ cross-tier upstream reads); `*_query.py` regenerated via `generate-return-types` against the 005 schema (exported from the `device-design-entities` branch with `INFRAHUB_DEFAULT_BRANCH`); all three `generate()` methods refactored. `test_generate_fabric.py` mock builders updated for the new query shape.
- Gates: `mypy` (src) clean, `ruff check`/`format` clean, full unit suite **417 passed** (the 1 failure — `test_cv_integration.py` reading a missing `specs/004-cv-config-validation/quickstart.md` — is pre-existing and unrelated to this cycle).

## Validation status (2026-07-28)

**21/23 tasks complete.** All previously deferred runs were executed against a live local
stack with the migrated seed data loaded:

- **Parity** — the full chain produced 80 devices / 200 links / 10 MLAG domains, and all
  39 per-container design assertions matched (`device_design_mismatches` helper, now a
  permanent guard in `test_e2e_pipeline.py::test_devices_match_device_designs`). Note the
  design `role` names a *tier*: the generators map it onto a device role via the fabric
  underlay (l2spine / l3spine / p / pe / l2leaf for the non-L3LS example fabrics), and the
  parity check applies that mapping.
- **Convergence** (T018) — on branch `device-design-convergence`: a rack `leaf` design
  1 → 2 created the second leaf and formed a new MLAG domain (10 → 11); deleting a rack
  `l2leaf` design removed `l2leaf-pod-a2-1-1` with no dangling links or orphan interfaces;
  a pod `spine` design 4 → 2 cleaned up the excess spines.
- **Idempotence** (T019) — a second full chain run was a byte-for-byte no-op across
  devices, links, MLAG domains, and interfaces.

Outstanding (see T020/T023): the repository-driven `test_e2e_pipeline.py` run needs the
branch committed, since the `CoreRepository` clones the committed git state.

## Path Conventions

Infrahub reference-design repo (single project). Generators under `generators/`, shared helper under `src/solution_arista_avd/`, tests under `tests/`, docs under `docs/docs/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch and baseline for a branch-first, behavior-preserving refactor.

- [X] T001 Create/confirm branch `device-design-generators`; confirm the 005 `device_designs` schema is loaded on it; record the co-requisite that the Objects cycle must populate `device_designs` before this can generate devices (`uv run infrahubctl info` reachable)
- [X] T002 [P] Capture a clean baseline before edits: `uv run pytest tests/unit` and `uv run invoke lint` pass on the current tree

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared per-role resolver is used by all three generators and both cross-tier reads, so it MUST exist first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Write unit tests first in `tests/unit/test_device_design_resolution.py`: `device_design_for(edges, role)` returns `(template_id, quantity)` for a present role and `(None, 0)` for an absent role (absence-means-none), including a missing `leaf` design → `(None, 0)`; a role with multiple would-be entries is not expected (schema uniqueness)
- [X] T004 Implement `resolve_device_designs()` / `device_design_for()` on `GeneratorMixin` in `src/solution_arista_avd/generator.py` per data-model.md (keys `device_designs` edges by `role`, returns `(device_template_id, device_quantity)`, defaults `(None, 0)`); confirm T003 passes and Ruff C901 ≤17 holds

**Checkpoint**: Shared resolver in place and unit-tested — generator stories can begin.

---

## Phase 3: User Story 1 - Rack generator reads device designs (leaf + L2 leaf) (Priority: P1) 🎯 MVP

**Goal**: `generate-rack` sources leaf and L2-leaf count/template from `device_designs` (roles `leaf`, `l2leaf`) and the pod-completeness guard from the pod's `spine` design, producing the same devices as the legacy fields.

**Independent Test**: On a branch with populated designs, run `generate-rack` for one rack and confirm the same leaf/L2-leaf `DcimDevice`s (names, roles, templates, count, MLAG) as before, and an idempotent re-run.

### Tests for User Story 1 ⚠️

- [X] T005 [P] [US1] Add/extend integration coverage in `tests/integration/test_e2e_pipeline.py` (or a focused `tests/integration/test_device_design_rack_generation.py`) asserting rack parity: `leaf`×2 + `l2leaf`×1 designs produce the same devices as the equivalent legacy fields, and a second run is a no-op (SC-001, SC-002; US1 scenarios 1–4)

### Implementation for User Story 1

- [X] T006 [US1] Update `generators/generate_rack.gql`: select `device_designs { edges { node { role{value} device_quantity{value} device_template{node{id}} } } }` on `LocationRack` and on `pod`; remove `amount_of_leafs`, `leaf_switch_template`, `amount_of_l2leafs`, `l2leaf_switch_template`, and `pod { amount_of_spines }`
- [X] T007 [US1] Regenerate `generators/rack_generator_query.py` from the updated `.gql` (`uv run infrahubctl graphql generate-return-types generators/generate_rack.gql`); do not hand-edit
- [X] T008 [US1] Update `generators/generate_rack.py`: resolve `leaf` and `l2leaf` designs via `device_design_for()`; drive `create_leaf_switches` (leaf qty/template, still via `LEAF_ROLE_BY_UNDERLAY`) and `create_l2leaf_switches` (l2leaf qty/template, skip when 0/none); source the pod-completeness guard from the pod `spine` design quantity; treat a missing `leaf` design as 0 leaves; keep MLAG pairing, cabling, `generation_complete`, and hostvar triggering unchanged; keep `allow_upsert=True`
- [X] T009 [US1] Validate US1: `uv run invoke lint`; run `uv run infrahubctl generator generate-rack --target <rack> --branch device-design-generators` twice; confirm device parity and an idempotent second run (T005 passes)

**Checkpoint**: Rack generator fully functional on device designs and independently testable (MVP).

---

## Phase 4: User Story 2 - Pod and fabric generators read device designs (spine, super-spine) (Priority: P2)

**Goal**: `generate-pod` and `generate-fabric` source spine / super-spine count/template from `device_designs`; the pod's fabric-completeness guard reads the fabric `super_spine` design.

**Independent Test**: On a branch with populated designs, run `generate-fabric` and `generate-pod` and confirm the same spine / super-spine devices as before, idempotently.

### Tests for User Story 2 ⚠️

- [X] T010 [P] [US2] Add/extend integration coverage in `tests/integration/test_e2e_pipeline.py` asserting pod/fabric parity: a `spine` design produces the same spine devices and a `super_spine` design the same super-spines as the equivalent legacy fields; absent `super_spine` design → no super-spines (SC-003, SC-004; US2 scenarios 1–3)

### Implementation for User Story 2

- [X] T011 [P] [US2] Update `generators/generate_fabric.gql`: select `device_designs` on `NetworkFabric`; remove `amount_of_super_spines` and `super_spine_switch_template`
- [X] T012 [US2] Regenerate `generators/fabric_generator_query.py` from the updated `.gql`; do not hand-edit
- [X] T013 [US2] Update `generators/generate_fabric.py`: resolve the `super_spine` design via `device_design_for()`; `create_super_spine_switches` uses that qty/template; `qty == 0` → skip; `qty > 0` with no template → raise; keep pools, naming (`ss-<fabric>-<idx>`), and checksum-bump unchanged
- [X] T014 [P] [US2] Update `generators/generate_pod.gql`: select `device_designs` on `NetworkPod` and on the parent `... on NetworkFabric`; remove `amount_of_spines`, `spine_switch_template`, and parent `amount_of_super_spines`
- [X] T015 [US2] Regenerate `generators/pod_generator_query.py` from the updated `.gql`; do not hand-edit
- [X] T016 [US2] Update `generators/generate_pod.py`: resolve the pod `spine` design (via `device_design_for()`, still `SPINE_ROLE_BY_UNDERLAY`) for `create_spine_switches`; source the fabric-completeness guard and `connect_spine_to_super_spine` gate from the fabric `super_spine` design quantity; keep pools, cabling, and checksum-bump unchanged
- [X] T017 [US2] Validate US2: `uv run invoke lint`; run `generate-fabric` and `generate-pod` on the branch; confirm parity and idempotent re-runs (T010 passes)

**Checkpoint**: All three generators read device designs; the full fabric generates from the normalized model.

---

## Phase 5: User Story 3 - Design changes re-drive generation idempotently (Priority: P3)

**Goal**: Changing a design (quantity up/down, add/remove a role) converges the fabric on re-run without duplicates or orphans.

**Independent Test**: Change a design quantity and re-run; confirm the device count converges and no orphans remain; revert and re-run to converge back.

- [X] T018 [US3] Convergence validation: increase a rack `leaf` design quantity → re-run creates the new leaf + updates MLAG/cabling; remove the `l2leaf` design → re-run cleans up the L2-leaf devices (no orphans); decrease a `spine` design → excess spines cleaned up (SC-005; US3 scenarios 1–2)
- [X] T019 [US3] Idempotence gate: run each generator twice unchanged and confirm a no-op (checksum/upsert) (SC-002; US3 scenario 3); run `$infrahub-test-generator-idempotence` where live validation is permitted and record branch/scenario/snapshot/no-diff

**Checkpoint**: Idempotence and stale-cleanup confirmed across the refactor.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [~] T020 Full generator chain run — **done directly, one gate outstanding**: the chain ran end-to-end on the live local stack against migrated seed data (fabric → pod → rack, twice, with parity and idempotence verified). The repository-driven variant (`test_e2e_pipeline.py`, which registers the `CoreRepository` and exercises the trigger cascade) still needs the branch committed, because Infrahub clones the committed git state from the `/upstream` bind mount. Not yet run.
- [X] T021 [P] Update generator docs in `docs/docs/developer-guide/generators.md` (and AVD generator docs if affected) to describe device-design-driven generation and the cross-tier completeness reads
- [X] T022 Run `quickstart.md` end-to-end; capture lint + parity + idempotence evidence
- [~] T023 Merge coordination — **no longer a cross-cycle gate**: 001, 002, and 003 are all implemented in this one tree and validated together, and the legacy-field removal already landed (005 T020, plain deletion rather than `state: absent`). What remains is committing and merging the branch as a single change.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: depends on Setup. **Blocks all user stories** (the resolver is shared).
- **US1 (Phase 3)**: depends on Foundational. Delivers the MVP (rack).
- **US2 (Phase 4)**: depends on Foundational. Independent of US1 (different files: fabric/pod vs rack) — can run in parallel with US1 once the resolver exists.
- **US3 (Phase 5)**: depends on US1 **and** US2 (it exercises the full generated fabric).
- **Polish (Phase 6)**: depends on US1–US3; T020/T023 additionally depend on the co-requisite Objects cycle populating `device_designs`.

### Within Each User Story / Generator

- `.gql` edit → regenerate `*_query.py` → update `generate()` → validate. The regenerate step is sequential after its `.gql` edit (same generator family).
- Within US2, the fabric chain (T011→T012→T013) and the pod chain (T014→T015→T016) are independent of each other and can proceed in parallel.

### Parallel Opportunities

- Setup T002 ∥ other prep.
- Foundational: T003 (tests) authored ∥ but T004 (impl) must land to make them pass.
- **US1 ∥ US2** once Foundational is done (rack files vs fabric/pod files are disjoint).
- Within US2: fabric `.gql` (T011) ∥ pod `.gql` (T014); the two regenerate+impl chains are independent.
- Integration tests T005 ∥ T010 (assertions in the same suite should be coordinated to avoid edit conflicts).
- Docs T021 ∥ code.

---

## Parallel Example: after Foundational

```bash
# Rack (US1) and Fabric/Pod (US2) touch disjoint files — parallelizable:
Task: "T006 update generators/generate_rack.gql + T008 generate_rack.py"
Task: "T011 update generators/generate_fabric.gql + T013 generate_fabric.py"
Task: "T014 update generators/generate_pod.gql + T016 generate_pod.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational (shared resolver) → Phase 3 US1 (rack).
2. **STOP and VALIDATE**: rack generator parity + idempotence (T009).
3. Rack is the busiest generator, so a green US1 proves the pattern end-to-end.

### Incremental Delivery

1. Setup + Foundational → resolver ready.
2. US1 (rack) → validate → MVP.
3. US2 (pod + fabric) → validate → full fabric generates from designs.
4. US3 → confirm convergence/idempotence.
5. Polish + coordinate the co-requisite Objects merge.

### Rollout safety

- All runs happen on the `device-design-generators` branch and merge via a proposed change **together with the Objects cycle** — a fabric with un-migrated seed data would generate nothing under the hard cutover.
- The 005 Stage-3 schema removal stays gated until this cycle and the Objects cycle are both merged.

---

## Notes

- `[P]` = different files, no incomplete dependencies.
- Regenerate `generators/*_query.py` from the `.gql` after every query edit — never hand-edit (Constitution Principle III).
- Every `save()` keeps `allow_upsert=True`; preserve the generator tracking context so quantity-down / removed designs are cleaned up (Principle II).
- Behavior-preserving: for a design equivalent to the legacy fields, the generated fabric is identical.
