---
description: "Task list for L2LS Fabric Example Conformance — Schema cycle"
---

# Tasks: L2LS Fabric Example Conformance (Schema cycle)

**Input**: Design documents from `/specs/001-l2ls-example-conformance/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/schema-contract.md, quickstart.md

**Tests**: Included. The spec and constitution mandate tests; schema-contract
tests parse the schema YAML directly (fast unit tests, no live instance), so each
story's edit + test is independently runnable and follows fail-then-pass.

**Scope of this cycle**: the **schema / data-model foundation** (first in a Schema
→ Generator → Transform chain). Device naming (SPINE1-2/LEAF1-4), MLAG carving,
tag emission, endpoint cabling, rendered-config parity, and the fabric-selectable
integration suite are delivered in later cycles — see **Deferred to later cycles**
at the end.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 (maps to spec.md user stories)

## Path Conventions

Infrahub reference-design repo: `schemas/`, `objects/`, `src/solution_arista_avd/`,
`tests/`, `docs/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch-first working environment and a known-good baseline.

- [X] T001 Create the working branch and session alias: `uv run infrahubctl branch create l2ls-example-conformance` and `alias ihctl='uv run infrahubctl'` (never edit schema on the default branch, per constitution I / schema skill `workflow-branch-first`)
- [X] T002 [P] Capture a green baseline: run `uv run pytest tests/unit -q` and `uv run invoke lint` and record that existing fabric contract tests + lint pass before any edit

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the current schema is loadable on the branch before edits, so any later failure is attributable to this cycle's changes.

**⚠️ CRITICAL**: Complete before starting any user story.

- [X] T003 Baseline schema check on the branch: `ihctl schema check schemas/ --branch l2ls-example-conformance` passes unchanged

**Checkpoint**: Foundation ready — user story work can begin.

---

## Phase 3: User Story 1 - Reproduce the L2LS spine/leaf topology (Priority: P1) 🎯 MVP

**Goal**: The schema + seed can represent the example's 2 MLAG `l2spine` switches and 4 `l2leaf` switches across 2 MLAG racks, with per-tier MSTP priorities (l2spine=4096, l2leaf=16384).

**Independent Test**: `ihctl object load objects/12_l2ls_fabric.yml` on the branch yields `Fabric-L2LS` with 2 spines, 2 MLAG racks (a LEAF pair each), and `Network.SpanningTreePriority` objects for l2spine=4096 and l2leaf=16384; contract test C1 passes.

### Tests for User Story 1

- [X] T004 [P] [US1] Extend the schema-contract test for STP roles (contract C1) in `tests/unit/test_avd_example_fabrics_schema_contract.py`: assert `Network.SpanningTreePriority.role` choices include `l2spine` and `l3spine` alongside the existing `super_spine`/`spine`/`leaf`/`l2leaf` (note: `SpanningTreePriority` is a top-level `nodes:` entry, not under `extensions.nodes` — add a node accessor helper). Write it to FAIL before T005, PASS after.

### Implementation for User Story 1

- [X] T005 [US1] Add `l2spine` and `l3spine` choices to the `role` dropdown of the `Network.SpanningTreePriority` node in `schemas/l3ls_extensions.yml` (preserve existing choices; additive only)
- [X] T006 [US1] Reshape `objects/12_l2ls_fabric.yml` to mirror the example topology: keep `underlay_routing_protocol: none` + `spanning_tree_mode: mstp`; set pod `amount_of_spines: 2` with an MLAG spine pair; add a second MLAG rack (`L2LS_RACK2`, `amount_of_leafs: 2`, `mlag: true`) alongside `L2LS_RACK1`; add `Network.SpanningTreePriority` objects (l2spine=4096, l2leaf=16384) linked to `Fabric-L2LS` (do NOT hardcode device hostnames — SPINE1-2/LEAF1-4 naming is the generator cycle)
- [X] T007 [US1] Validate on the branch: `ihctl schema check schemas/ --branch l2ls-example-conformance`, `ihctl schema load schemas --branch l2ls-example-conformance`, `ihctl object load objects/12_l2ls_fabric.yml --branch l2ls-example-conformance`; confirm 2 racks + 2 STP priority objects present

**Checkpoint**: The L2LS topology (tiers, MLAG racks, per-tier STP priorities) is representable and loads clean.

---

## Phase 4: User Story 2 - Model pure Layer-2 network services exactly (Priority: P2)

**Goal**: An overlay-free tenant (`MY_FABRIC`, no VNI base) carrying VLANs BLUE-NET(10)/GREEN-NET(20)/ORANGE-NET(30), each scoped to the correct leaf pair by tag.

**Independent Test**: `ihctl object load objects/12_l2ls_fabric.yml` yields a tenant with no `mac_vrf_vni_base` and three `Evpn.L2Vlan` objects carrying rack/AVD tags; contract tests C2 and C3 pass.

### Tests for User Story 2

- [X] T008 [P] [US2] Create `tests/unit/test_l2ls_services_schema_contract.py` parsing `schemas/evpn/evpn_services.yml`: assert C2 (`Evpn.Tenant.mac_vrf_vni_base` is `optional: true`) and C3 (`Evpn.L2Vlan` has `rack_tags` → `LocationRack` and `avd_tags` → `AvdTag`, cardinality many, optional, with identifiers distinct from the `Evpn.Svi` tag identifiers). Write it to FAIL before T009/T010, PASS after.

### Implementation for User Story 2

- [X] T009 [US2] In `schemas/evpn/evpn_services.yml`, make `Evpn.Tenant.mac_vrf_vni_base` `optional: true` (backward compatible — existing overlay tenants keep their value)
- [X] T010 [US2] In `schemas/evpn/evpn_services.yml`, add `rack_tags` (peer `LocationRack`) and `avd_tags` (peer `AvdTag`) relationships to `Evpn.L2Vlan`, mirroring the shape on `Evpn.Svi` (cardinality many, optional, kind Attribute, unique identifiers)
- [X] T011 [US2] Reshape `objects/12_l2ls_fabric.yml`: tenant `MY_FABRIC` with NO `mac_vrf_vni_base`; VLANs `BLUE-NET`(10)/`GREEN-NET`(20)/`ORANGE-NET`(30) as `Evpn.L2Vlan` (+ underlying `Ipam.VLAN`); `Avd.Tag` zones `bluezone`/`greenzone`/`orangezone` linked to the correct racks; scope VLANs via `rack_tags`/`avd_tags` (RACK1 → blue+green, RACK2 → blue+orange); remove the VNI-based `L2LS-TENANT`/`mac_vrf_vni_base: 20000` modeling
- [X] T012 [US2] Validate on the branch: schema check + load, `ihctl object load objects/12_l2ls_fabric.yml`; confirm overlay-free tenant + per-rack VLAN tag scoping

**Checkpoint**: Pure-L2, tag-scoped services are representable with no VNI/overlay modeling.

---

## Phase 5: User Story 3 - Model connected endpoints (Priority: P3)

**Goal**: Host access ports (per-color access VLAN + edge portfast) are representable. The dual-homed
`FIREWALL` trunk Port-Channel is out of scope — dropped in cycle 002 (T016/T017).

**Independent Test**: `ihctl object load objects/12_l2ls_fabric.yml` yields host endpoints with access switchport intent; contract test C4 passes.

### Tests for User Story 3

- [X] T013 [P] [US3] Add contract test C4 to `tests/unit/test_l2ls_services_schema_contract.py`: assert the endpoint/adapter model exposes switchport `mode` (access|trunk), access VLAN, trunk VLANs, and edge portfast; and that a connected endpoint is attachable to `l2spine` devices (or, if the escape-hatch fallback is chosen, assert `DcimDevice.avd_custom_hostvars` accepts a firewall block — document the exception). Write it to FAIL before T014/T015, PASS after.

### Implementation for User Story 3

- [X] T014 [US3] Add switchport intent to the connected-endpoint/adapter model in `schemas/objects/objects.yml` (or the endpoint schema per data-model §4): `mode` (access/trunk) dropdown, `access_vlan` (Number, optional), `trunk_vlans` (List/Text, optional), `portfast` (edge, optional); reuse the existing `Interface.Lag` + adapter `port_channel` for LACP
- [~] T015 [US3] (DROPPED — firewall excluded per request; see 002 T016/T017) Enable a connected endpoint to attach to `l2spine` devices (firewall dual-homed to both spines) per research Decision 4
- [X] T016 [US3] Reshape the connected endpoints in `objects/12_l2ls_fabric.yml`: named host endpoints on leaf access ports with per-color access profiles (access VLAN 10/20/30 + edge portfast). The `FIREWALL` trunk Port-Channel is dropped with T015.
- [X] T017 [US3] Validate on the branch: schema check + load, `ihctl object load objects/12_l2ls_fabric.yml`; confirm host access ports are representable

**Checkpoint**: Connected endpoints and the dual-homed firewall are representable.

---

## Phase 6: Integration & Rollout (Shared)

**Purpose**: Consolidate the schema changes into regenerated types and prove no regression.

- [X] T018 Regenerate typed protocols after all schema edits (depends on T005, T009, T010, T014, T015): `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py`; review the diff (do NOT hand-edit — constitution III)
- [X] T019 Full regression: `uv run pytest tests/unit -q` — new contract tests (C1–C4) pass AND existing fabric contract tests (Fabric-A/C/Campus/ISIS-LDP) remain green (contract C5, backward compatibility)
- [X] T020 Lint gate: `uv run invoke lint` (ruff + mypy + yamllint) clean; run `uv run invoke format` if needed

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T021 [P] Update `docs/docs/supported-capabilities.md`: state the L2LS example is targeted at golden-config parity and record any documented exception (e.g. firewall via `avd_custom_hostvars`, if chosen in T015) — FR-019
- [X] T022 [P] Update `docs/docs/developer-guide/avd/role-mapping.md` and `docs/docs/developer-guide/avd/hostvars.md` where the STP-role additions and L2-VLAN tag scoping need documenting
- [X] T023 Run the full `quickstart.md` validation (Steps 1–6) on the branch and confirm all cycle validation-criteria checkboxes pass
- [X] T024 Record hand-off markers for the next `/speckit-specify` cycles (Generator: device naming SPINE1-2/LEAF1-4, MLAG peer carving, `filter.tags` emission, host/firewall cabling; Transform/integration: `scripts/compare_avd_examples.py` parity + fabric-selectable `pytest tests/integration --fabric Fabric-L2LS` + `$infrahub-run-integration-tests`) so no deferred scope is lost

---

## Deferred to later cycles (not tasks in this schema cycle)

These spec items require generation/rendering/running and are delivered after the schema foundation merges:

- **US1 rendering acceptance** (MLAG/MSTP/uplink config diff) → Generator + Transform cycles.
- **US2/US3 rendering acceptance** (VLAN/trunk/access/firewall config diff; no VXLAN/BGP/EVPN) → Transform cycle (SC-001, SC-002, SC-003, SC-004).
- **US4 — fabric-selectable integration tests (P1)** (FR-020–FR-024, SC-008): the `--fabric <name>` pytest option + conftest fixture and the end-to-end deployment assertions (parity, zero violations, idempotence) → **Transform / integration cycle**, validated via `$infrahub-run-integration-tests`. This cycle only adds the schema-contract unit tests; it deliberately does not substitute for the integration suite.
- **Generator idempotence** (`$infrahub-test-generator-idempotence`) → Generator cycle gate.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies.
- **Foundational (Phase 2)**: after Setup; blocks user stories.
- **User Stories (Phase 3–5)**: after Foundational. Each story's edit + contract test is independently runnable (contract tests parse YAML). Seed-load validation (T007/T012/T017) shares the branch schema load.
- **Integration & Rollout (Phase 6)**: after all story schema edits (T005, T009, T010, T014, T015).
- **Polish (Phase 7)**: after Phase 6.

### User Story Dependencies

- **US1 (P1)**: independent — STP role enum + topology seed.
- **US2 (P2)**: independent of US1 (different schema file + seed file). Tag scoping reuses `Avd.Tag`, which already exists.
- **US3 (P3)**: independent of US1/US2 (endpoint schema + seed file); benefits from US1's racks existing for seed-load validation.

### Within Each User Story

- Contract test (parses YAML) is written first, FAILS before the edit, PASSES after.
- Schema edit → schema check → branch load → seed load.

### Parallel Opportunities

- T002 (baseline) runs alongside setup with nothing blocking it.
- Contract tests T004, T008, T013 are `[P]` (independent files/assertions).
- Schema edits across stories touch different files (`l3ls_extensions.yml`, `evpn_services.yml`, `objects.yml`) and can be authored in parallel, but converge at T018 (single protocol regen) and T019 (single regression run).
- Docs tasks T021, T022 are `[P]`.

---

## Parallel Example: Contract tests

```bash
# The three schema-contract tests touch independent assertions and can be authored together:
Task: "STP roles contract (C1) in tests/unit/test_avd_example_fabrics_schema_contract.py"
Task: "Overlay-free tenant + L2Vlan tags (C2/C3) in tests/unit/test_l2ls_services_schema_contract.py"
Task: "Endpoint switchport intent (C4) in tests/unit/test_l2ls_services_schema_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → Phase 2 Foundational → Phase 3 US1.
2. **STOP and VALIDATE**: STP-role schema + 2-MLAG-rack topology load clean; C1 passes.
3. This is the minimum that lets the example's topology be modeled.

### Incremental Delivery

1. Setup + Foundational → baseline green.
2. US1 (topology/STP) → validate → the example's structure is representable.
3. US2 (pure-L2 services + tag scoping) → validate.
4. US3 (endpoints + firewall) → validate.
5. Phase 6 rollout (protocol regen + regression + lint) → Phase 7 polish.
6. Then proceed to the Generator cycle (`/speckit-specify` again).

### Notes

- `[P]` = different files, no dependencies.
- Additive-only schema changes (constitution I; contract C5) — no removals/renames.
- Commit after each task or logical group; keep the branch as the single rollout unit.
- Do not hand-edit `protocols.py`; regenerate (T018).
