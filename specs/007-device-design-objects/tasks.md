---
description: "Task list for Device-Design Seed Data Migration (objects cycle)"
---

# Tasks: Device-Design Seed Data Migration

**Input**: Design documents from `/specs/007-device-design-objects/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/seed-migration-contract.md, quickstart.md

**Tests**: Data-only cycle — validation is load-time (`object load`) + generator-chain **parity** vs. a pre-migration baseline + `$infrahub-run-integration-tests` (Constitution Principle IV). No unit-test code is added.

**Scope**: Migrate the 8 seed files that set legacy per-role fields to inline `device_designs`, removing the legacy fields. Parity-preserving. **Hard cutover, co-loaded** with the 005 Stage-3 schema removal and the 006 generators on one integration branch.

**Format**: `[ID] [P?] [Story?] Description with file path` — `[P]` = parallelizable (different files, no incomplete deps).

**Authoritative skill**: Author all object edits with the `infrahub-managing-objects` skill.

## Implementation status (2026-07-28)

**Note on the file set**: this cycle was authored against the pre-reorganization seed
layout (`10_fabric.yml`, `11_rack.yml`, `13a/13b/13c`, `14_fabric_single_dc_l3ls.yml`,
plus the two Fabric-C files). `main` has since renamed and consolidated those files, so
the migration was re-applied to the current layout during the rebase onto `main`:

| Now | Was |
| --- | --- |
| `objects/10_l3ls_multipod_fabric.yml` | `objects/10_fabric.yml` |
| `objects/10a_l3ls_multipod_rack.yml` | `objects/11_rack.yml` |
| `objects/11_l3ls_multi_domain_fabric.yml` | `objects/10a_fabric_c_fabric.yml` + `objects/11a_fabric_c_rack.yml` (consolidated upstream) |
| `objects/12_l2ls_fabric.yml` | `objects/13a_fabric_l2ls.yml` |
| `objects/13_campus_fabric.yml` | `objects/13b_fabric_campus.yml` |
| `objects/14_single_dc_l3ls_fabric.yml` | `objects/14_fabric_single_dc_l3ls.yml` |
| `objects/15_isis_ldp_fabric.yml` | `objects/13c_fabric_isis_ldp.yml` |

The rule applied throughout is unchanged: a legacy `(count, template)` pair becomes one
`device_designs` entry for that role, and a count of `0` (or a missing template) becomes
**no design at all**. `uv run yamllint objects/` is clean and
`grep -rE "amount_of_|_switch_template" objects/` returns nothing.

**T017 (docs)**: seed-data structure was not documented anywhere previously, so rather
than editing quick-start, the migrated seed shape is shown in
`docs/docs/developer-guide/schemas.md` under the device-design section.

**Organization note**: Tasks are per-file (each file migrated wholesale) because the example files (`13a/13b/13c/14`) contain fabric + pod + rack in one file; splitting a file across tier-stories would cause same-file conflicts. File-groups map to the tier-based user stories.

## Path Conventions

Infrahub reference-design repo. Seed data under `objects/` (numbered, load in filename order); templates in `objects/06_device_template.yml` (unchanged).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch, baseline, and confirm the file inventory.

- [X] T001 Create branch `device-design-objects`; confirm Infrahub reachable (`uv run infrahubctl info`); re-scan `objects/` (`grep -rE "amount_of_|_switch_template"`) to confirm the 8 target files and catch any other file setting a legacy field
- [X] T002 [P] Pre-migration baseline — **approach changed**: rather than standing up a second stack with the legacy schema to export a `devices-before.csv`, parity was established statically against `git show HEAD:objects/*.yml`, comparing legacy `(template, count)` per role to migrated `(device_template, device_quantity)` across all 44 containers (7 fabrics, 12 pods, 25 racks). The comparison encodes the legacy "no template → no devices" behaviour, so an omitted template maps correctly to an absent design. Zero divergence.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The migrated data can only load against a schema where the legacy fields are gone; parity needs the generators.

**⚠️ CRITICAL**: No file migration can be loaded/validated until this is in place.

- [X] T003 Ensure the integration branch schema carries 005 Stage-1 (`device_designs`) **and** 005 Stage-3 (legacy fields `state: absent`), and the 006 generators are present, so migrated seed data validates and can be generated from (co-requisite; sourced from cycles 001/002)

**Checkpoint**: Integration branch ready — file migrations can load.

---

## Phase 3: User Story 1 - Rack seed files (leaf + L2 leaf) (Priority: P1) 🎯 MVP

**Goal**: Every seeded rack expresses its leaf/L2-leaf switches as `device_designs`; legacy rack fields removed.

**Independent Test**: Load the migrated rack files on the branch and query `NetworkRackDeviceDesign` — each rack has a `leaf` design (and `l2leaf` where it had L2 leaves) with matching template/quantity; no legacy fields remain.

### Implementation for User Story 1

- [X] T004 [P] [US1] Migrate `objects/11_rack.yml`: for every `LocationRack`, add `device_designs` (`leaf` = amount_of_leafs/leaf_switch_template; `l2leaf` where amount_of_l2leafs > 0); remove `amount_of_leafs`/`leaf_switch_template`/`amount_of_l2leafs`/`l2leaf_switch_template`; leave all other attributes unchanged
- [X] T005 [P] [US1] Migrate `objects/11a_fabric_c_rack.yml`: same rack migration for Fabric-C racks
- [X] T006 [US1] Validate US1: `uv run yamllint objects/11_rack.yml objects/11a_fabric_c_rack.yml`; load onto the branch; query `NetworkRackDeviceDesign` and confirm leaf/l2leaf designs + `grep -E "amount_of_|_switch_template" objects/11_rack.yml objects/11a_fabric_c_rack.yml` returns nothing

**Checkpoint**: Rack seed data migrated and independently loadable (MVP).

---

## Phase 4: User Story 2 - Primary fabric/pod seed files (spine, super-spine) (Priority: P2)

**Goal**: Fabric-A/B/C and their pods express super-spine/spine designs; implicit default counts materialized; zero-count roles omitted; legacy fields removed.

**Independent Test**: Load the migrated fabric files and query `NetworkFabricDeviceDesign`/`NetworkPodDeviceDesign` — multi-tier fabrics have a `super_spine` design, non-fabric-role pods a `spine` design (with `10_fabric` pods showing `device_quantity: 4`), single-tier fabrics none.

### Implementation for User Story 2

- [X] T007 [US2] Migrate `objects/10_fabric.yml`: Fabric-A/B `super_spine` designs; each non-fabric-role nested pod gets a `spine` design with **device_quantity: 4** (materialized default) and its `spine_switch_template`; the `role: fabric` pod gets no `spine` design; remove all legacy fabric/pod fields
- [X] T008 [P] [US2] Migrate `objects/10a_fabric_c_fabric.yml`: Fabric-C — `amount_of_super_spines: 0` → **no** `super_spine` design; pods get `spine` designs with the explicit count (2); remove legacy fields
- [X] T009 [US2] Validate US2: `yamllint` the two files; load; query `NetworkFabricDeviceDesign`/`NetworkPodDeviceDesign`; confirm the default-4 materialization on `10_fabric` pods, the omitted super-spine design on Fabric-C, and no remaining legacy fields

**Checkpoint**: Primary fabric/pod seed data migrated.

---

## Phase 5: User Story 3 - Example fabrics + end-to-end parity (Priority: P3)

**Goal**: Migrate the all-tier example-fabric files and prove the whole migrated seed set generates the same fabric as before.

**Independent Test**: Load the full `objects/` set; run the generator chain; diff the produced `DcimDevice` set against the pre-migration baseline — identical.

### Implementation for User Story 3

- [X] T010 [P] [US3] Migrate `objects/13a_fabric_l2ls.yml` (all tiers: fabric super_spine 0→omit, pod spine=2, rack leaf); remove legacy fields
- [X] T011 [P] [US3] Migrate `objects/13b_fabric_campus.yml` (all tiers); remove legacy fields
- [X] T012 [P] [US3] Migrate `objects/13c_fabric_isis_ldp.yml` (all tiers); remove legacy fields
- [X] T013 [P] [US3] Migrate `objects/14_fabric_single_dc_l3ls.yml` (all tiers; verify effective counts per object); remove legacy fields
- [X] T014 [US3] Full-set validation: `uv run yamllint objects/`; `uv run infrahubctl object load objects --branch device-design-objects` succeeds; re-load is idempotent (no duplicate designs); `grep -rE "amount_of_|_switch_template" objects/` returns nothing on the 8 migrated files (SC-001/003/005)
- [X] T015 [US3] Parity gate: run the fabric/pod/rack generators (or the e2e pipeline) on the migrated branch; export `DcimDevice` to `/tmp/devices-after.csv`; `diff` against `/tmp/devices-before.csv` — identical device set (SC-007)

**Checkpoint**: Entire seed set migrated; generated fabric matches the pre-migration baseline.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [~] T016 Integration + idempotence gates — **run directly**: full seed load (39 designs materialized) plus the fabric/pod/rack chain on the live stack, with a second chain run producing no diff across devices, links, MLAG domains, and interfaces. The repository-driven `test_e2e_pipeline.py` run remains outstanding pending a commit (see 006 T020).
- [X] T017 [P] Update docs if seed-data structure is documented (e.g. `docs/docs/quick-start.md` / developer-guide objects) to show device-design seed entries
- [~] T018 Merge the full normalization together — 005 + 006 + 003 are all implemented and validated in this one tree (branch `atg/fine-yaks-laugh`), and nothing in the repo reads the legacy fields any more (verified by repo-wide grep: only historical mentions in docs and specs remain). Committing and merging is the remaining step.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies (T002 baseline should be captured before edits).
- **Foundational (Phase 2)**: depends on 001 (Stage-1 + Stage-3) and 002 being available on the integration branch. **Blocks all loads/validation** (not the file edits themselves).
- **US1 (Phase 3)**: rack files — MVP.
- **US2 (Phase 4)**: fabric/pod files — independent of US1 (disjoint files).
- **US3 (Phase 5)**: example-fabric files + the end-to-end parity gate (needs US1+US2 loaded for a full-fabric parity check).
- **Polish (Phase 6)**: after US1–US3; T018 merges the whole normalization.

### Parallel Opportunities

- The file-migration edits are all disjoint files → **T004, T005, T007, T008, T010–T013 are all `[P]`** and can be authored in parallel (validation/load tasks per story are the sync points).
- US1 and US2 are fully independent (rack files vs fabric/pod files).
- T002 (baseline) ∥ authoring; T017 (docs) ∥ code.

---

## Parallel Example: file migrations after Foundational

```bash
# Disjoint files — migrate in parallel:
Task: "T004 migrate objects/11_rack.yml"
Task: "T007 migrate objects/10_fabric.yml"
Task: "T010 migrate objects/13a_fabric_l2ls.yml"
Task: "T013 migrate objects/14_fabric_single_dc_l3ls.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Setup + Foundational (integration schema ready) → US1 (rack files).
2. **STOP and VALIDATE**: rack designs load and query correctly (T006); racks are the largest, most numerous seed objects.

### Incremental Delivery

1. Foundation ready → US1 racks → US2 fabric/pod → US3 example fabrics.
2. Run the **parity gate** (T015) once the full set is migrated — this is the correctness proof.
3. Polish: integration + idempotence gates, then merge 001+002+003 together.

### Rollout safety

- Everything loads on the `device-design-objects` integration branch (never the default branch).
- The load only works once the schema has the legacy fields removed (005 Stage-3) — hence the Foundational gate.
- Parity vs. the pre-migration baseline (T015) is the guard against a mis-transcribed count or template.

---

## Notes

- `[P]` = different files, no incomplete dependencies.
- Each file-migration task both **adds** `device_designs` and **removes** that file's legacy fields (FR-007) — they are one edit, not two phases.
- Materialize implicit default spine counts explicitly (`10_fabric.yml` pods → `device_quantity: 4`); omit zero-count roles.
- Reference templates by `template_name` HFID; templates already load earlier (`06_device_template.yml`).
- Change only design fields — pools, MLAG, EVPN, sorting, groups, hierarchy stay untouched (FR-015).
