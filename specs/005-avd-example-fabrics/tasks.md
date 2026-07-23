# Tasks: AVD Example Fabric Designs (Schema Cycle)

**Input**: Design documents from `/specs/005-avd-example-fabrics/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/schema.md`, `contracts/escape-hatch.md`, `.specify/memory/constitution.md`

**Tests**: Required by the constitution (Test-Required Quality) and by the spec/quickstart, which call for schema contract tests and role-mapping unit tests. Test tasks are listed before the implementation tasks they validate.

**Scope of this cycle**: This is the **schema-first cycle**. It delivers the schema surface the seven AVD example scenarios need (new roles, `ROLE_TO_AVD_TYPE` mappings, underlay choices, EVPN inputs, the DC Gateway flag), the native-vs-escape-hatch classification, protocol regeneration, tests, and docs. **Deferred to follow-on cycles**: GraphQL query/return-type changes and generator consumption (generator cycle: standalone L2LS topology, campus tiers, multi-DC/DCI assistance, route-server/vlan-aware-bundle/gateway rendering) and the per-scenario seed designs in `objects/` (objects cycle).

**Organization**: Tasks are grouped by user story (US1–US7 from spec.md) so each story is an independently validatable schema increment where dependencies allow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed prerequisite phases
- **[Story]**: User story label (`US1`–`US7`) for story-phase tasks only
- Every task includes an exact repository file path or validation artifact path

**Shared-file note**: `schemas/dcim_extensions.yml` (roles), `src/solution_arista_avd/avd.py` (`ROLE_TO_AVD_TYPE`), `schemas/l3ls_extensions.yml` (underlay/EVPN inputs), and `tests/unit/test_avd_example_fabrics_schema_contract.py` are edited by multiple stories. Tasks touching the same file across stories are **not** marked `[P]` and must be sequenced.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm scope and inspect the existing schema/mapping patterns before edits.

- [X] T001 Confirm the schema-only scope and follow-on cycle boundaries in `specs/005-avd-example-fabrics/plan.md`
- [X] T002 [P] Review schema authoring rules from the `infrahub-managing-schemas` skill
- [X] T003 [P] Inspect existing `DcimDevice.role` choices in `schemas/dcim_extensions.yml`
- [X] T004 [P] Inspect `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T005 [P] Inspect `NetworkFabric` underlay/overlay attributes and `Avd.Evpn` settings in `schemas/l3ls_extensions.yml` and `schemas/avd/avd.yml`
- [X] T006 [P] Confirm the pinned pyAVD `node_type_keys` values for `l2spine`, `l3spine`, `p`, `pe`, `rr`, `wan_router`, `wan_rr` and record the confirmed AVD node-type names in `specs/005-avd-example-fabrics/research.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared test scaffolding and the confirmed capability classification all stories rely on.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T007 Create the schema contract test scaffolding with YAML parse helpers for `schemas/dcim_extensions.yml` and `schemas/l3ls_extensions.yml` in `tests/unit/test_avd_example_fabrics_schema_contract.py`
- [X] T008 [P] Add a full role-coverage assertion helper (every `DcimDevice.role` choice maps to a non-empty AVD node type; unknown roles raise `ValueError`) in `tests/unit/test_avd.py`
- [X] T009 Finalize the per-capability native-vs-escape-hatch classification and confirmed pyAVD keys in `specs/005-avd-example-fabrics/research.md`

**Checkpoint**: Contract-test scaffolding and confirmed decisions are in place before story implementation.

---

## Phase 3: User Story 1 - Single-DC L3LS Reference Design (Priority: P1) 🎯 MVP

**Goal**: Confirm the baseline scenario needs no schema change and its behavior is unchanged by this feature.

**Independent Test**: Run the existing AVD unit tests and confirm the Single-DC L3LS role set and mappings are unchanged.

### Tests for User Story 1

- [X] T010 [US1] Add a regression test asserting the existing role set and Single-DC L3LS role mappings are unchanged in `tests/unit/test_avd.py`

### Implementation for User Story 1

- [X] T011 [US1] Record that Single-DC L3LS requires no schema change and document the baseline reference-design scope in `specs/005-avd-example-fabrics/quickstart.md`
- [X] T012 [US1] Validate the baseline with `uv run pytest tests/unit/test_avd.py tests/unit/test_hostvar_ordering.py` and record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: Baseline scenario confirmed unchanged (SC-003).

---

## Phase 4: User Story 2 - Multi-Pod 5-Stage Clos (Priority: P1)

**Goal**: Add the native `evpn_vlan_aware_bundles` input; record that route-server and vlan-aware-bundle rendering are generator-cycle work.

**Independent Test**: Schema check passes and a contract test confirms `evpn_vlan_aware_bundles` exists with a backward-compatible default.

### Tests for User Story 2

- [X] T013 [US2] Add a contract test asserting an optional `evpn_vlan_aware_bundles` Boolean input exists with a backward-compatible default in `tests/unit/test_avd_example_fabrics_schema_contract.py`

### Implementation for User Story 2

- [X] T014 [US2] Add the optional `evpn_vlan_aware_bundles` Boolean input to `NetworkFabric` (or `Avd.Evpn`) with a default preserving current rendering in `schemas/l3ls_extensions.yml` (or `schemas/avd/avd.yml`)
- [X] T015 [US2] Record that super-spine EVPN route-server derivation and vlan-aware-bundle rendering are deferred to the generator cycle in `specs/005-avd-example-fabrics/research.md`
- [X] T016 [US2] Validate US2 with `uv run infrahubctl schema check schemas/` and `uv run pytest tests/unit/test_avd_example_fabrics_schema_contract.py`; record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: The vlan-aware-bundle input exists and existing fabrics render unchanged.

---

## Phase 5: User Story 3 - Dual-DC L3LS With EVPN DC Gateway (Priority: P1)

**Goal**: Add the native EVPN DC Gateway flag; record that multi-DC composition and gateway rendering are objects/generator-cycle work.

**Independent Test**: Schema check passes and a contract test confirms the `evpn_gateway` flag exists with default `false`.

### Tests for User Story 3

- [X] T017 [US3] Add a contract test asserting an optional `evpn_gateway` Boolean (default `false`) exists on the gateway device kind in `tests/unit/test_avd_example_fabrics_schema_contract.py`

### Implementation for User Story 3

- [X] T018 [US3] Add the optional `evpn_gateway` Boolean (default `false`) to the gateway device kind in `schemas/l3ls_extensions.yml`
- [X] T019 [US3] Record that multi-DC composition (two fabrics + `dci` NetworkLinks) and gateway next-hop-self rendering land in the objects/generator cycles, and the escape-hatch fallback for per-device gateway tuning, in `specs/005-avd-example-fabrics/research.md`
- [X] T020 [US3] Validate US3 with `uv run infrahubctl schema check schemas/` and the contract test; record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: The DC Gateway flag exists and defaults preserve existing behavior.

---

## Phase 6: User Story 4 - Standalone L2LS Fabric (Priority: P2)

**Goal**: Add native `l2spine`/`l3spine` roles (with AVD mappings) and the `none` underlay mode.

**Independent Test**: Schema check passes; role-mapping tests confirm `l2spine`/`l3spine` map to their node types; a contract test confirms the `none` underlay choice exists.

### Tests for User Story 4

- [X] T021 [US4] Add contract tests asserting `l2spine` and `l3spine` role choices and the `none` underlay choice exist in `tests/unit/test_avd_example_fabrics_schema_contract.py`
- [X] T022 [US4] Add role-mapping tests for `l2spine` and `l3spine` in `tests/unit/test_avd.py`

### Implementation for User Story 4

- [X] T023 [US4] Add `l2spine` and `l3spine` choices to `DcimDevice.role` in `schemas/dcim_extensions.yml`
- [X] T024 [US4] Map `l2spine` and `l3spine` in `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T025 [US4] Add the `none` underlay mode to `NetworkFabric.underlay_routing_protocol` (preserving `ebgp`/`ospf` and the default) in `schemas/l3ls_extensions.yml`
- [X] T026 [US4] Record that standalone L2LS topology generation and the L3-on-spine variant are deferred to the generator cycle in `specs/005-avd-example-fabrics/research.md`
- [X] T027 [US4] Validate US4 with `uv run infrahubctl schema check schemas/` and `uv run pytest tests/unit/test_avd.py tests/unit/test_avd_example_fabrics_schema_contract.py`; record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: L2LS roles and underlay-none mode exist and validate; existing L3LS data remains valid.

---

## Phase 7: User Story 5 - Campus Fabric (Priority: P2)

**Goal**: Confirm campus reuses `l3spine` (core) and native OSPF underlay; classify access features as escape hatch. No new schema.

**Independent Test**: A contract test confirms `l3spine` and the `ospf` underlay choice are available for campus reuse.

**Dependency**: Requires US4 (`l3spine` role added).

### Tests for User Story 5

- [X] T028 [US5] Add a contract test confirming `l3spine` (campus core) exists and the `ospf` underlay choice is available in `tests/unit/test_avd_example_fabrics_schema_contract.py`

### Implementation for User Story 5

- [X] T029 [US5] Record the campus escape-hatch classification (dot1x/NAC, PoE, port profiles, in-band management via `avd_custom_hostvars`) in `specs/005-avd-example-fabrics/research.md`
- [X] T030 [US5] Validate US5 with the contract test and record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: Campus core role and OSPF underlay confirmed reusable; access features classified as escape hatch.

---

## Phase 8: User Story 6 - ISIS-LDP IPVPN WAN (Priority: P3)

**Goal**: Add native `isis-ldp` underlay choice and minimal `p`/`pe`/`rr` roles (with mappings); classify MPLS/VPN-IPv4 as escape hatch.

**Independent Test**: Schema check passes; role-mapping tests confirm `p`/`pe`/`rr`; a contract test confirms the `isis-ldp` underlay choice exists.

**Dependency**: Shares `schemas/dcim_extensions.yml` and `src/solution_arista_avd/avd.py` with US4/US7 — sequence edits.

### Tests for User Story 6

- [X] T031 [US6] Add contract tests asserting the `isis-ldp` underlay choice and `p`/`pe`/`rr` role choices exist in `tests/unit/test_avd_example_fabrics_schema_contract.py`
- [X] T032 [US6] Add role-mapping tests for `p`, `pe`, `rr` in `tests/unit/test_avd.py`

### Implementation for User Story 6

- [X] T033 [US6] Add `p`, `pe`, `rr` choices to `DcimDevice.role` in `schemas/dcim_extensions.yml`
- [X] T034 [US6] Map `p`, `pe`, `rr` in `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T035 [US6] Add the `isis-ldp` choice to `NetworkFabric.underlay_routing_protocol` in `schemas/l3ls_extensions.yml`
- [X] T036 [US6] Record the MPLS/LDP/VPN-IPv4 escape-hatch classification and the R8 phasing recommendation in `specs/005-avd-example-fabrics/research.md`
- [X] T037 [US6] Validate US6 with `uv run infrahubctl schema check schemas/` and `uv run pytest tests/unit/test_avd.py tests/unit/test_avd_example_fabrics_schema_contract.py`; record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: ISIS-LDP underlay and provider roles exist; MPLS/VPN-IPv4 classified as escape hatch.

---

## Phase 9: User Story 7 - CV-Pathfinder SD-WAN (Priority: P3)

**Goal**: Add minimal native `wan_router`/`wan_rr` roles (with mappings); classify the SD-WAN surface as escape hatch.

**Independent Test**: Schema check passes; role-mapping tests confirm `wan_router`/`wan_rr`; a contract test confirms the role choices exist.

**Dependency**: Shares `schemas/dcim_extensions.yml` and `src/solution_arista_avd/avd.py` with US4/US6 — sequence edits.

### Tests for User Story 7

- [X] T038 [US7] Add contract tests asserting `wan_router` and `wan_rr` role choices exist in `tests/unit/test_avd_example_fabrics_schema_contract.py`
- [X] T039 [US7] Add role-mapping tests for `wan_router` and `wan_rr` in `tests/unit/test_avd.py`

### Implementation for User Story 7

- [X] T040 [US7] Add `wan_router` and `wan_rr` choices to `DcimDevice.role` in `schemas/dcim_extensions.yml`
- [X] T041 [US7] Map `wan_router` and `wan_rr` in `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T042 [US7] Record the CV-Pathfinder SD-WAN escape-hatch classification (path groups, DPS, virtual topologies, WAN HA, STUN, CVaaS) and the R8 phasing recommendation in `specs/005-avd-example-fabrics/research.md`
- [X] T043 [US7] Validate US7 with `uv run infrahubctl schema check schemas/` and `uv run pytest tests/unit/test_avd.py tests/unit/test_avd_example_fabrics_schema_contract.py`; record evidence in `specs/005-avd-example-fabrics/quickstart.md`

**Checkpoint**: WAN roles exist; SD-WAN surface classified as escape hatch.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Regenerate protocols, run project-wide validation, and update documentation.

- [X] T044 Regenerate protocol classes after all schema changes with `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py` (regenerated, not hand-edited)
- [X] T045 Run `uv run infrahubctl schema check schemas/` and address any failures in `schemas/dcim_extensions.yml` and `schemas/l3ls_extensions.yml`
- [X] T046 Run the full role-mapping and schema contract suite with `uv run pytest tests/unit/test_avd.py tests/unit/test_avd_example_fabrics_schema_contract.py` and address failures
- [X] T047 [P] Update the per-scenario status for all seven scenarios in `docs/docs/supported-capabilities.md`
- [X] T048 [P] Document the new role → AVD node-type mappings in `docs/docs/developer-guide/avd/role-mapping.md`
- [X] T049 [P] Document the new inputs (`evpn_vlan_aware_bundles`, `evpn_gateway`, underlay `none`/`isis-ldp`) and escape-hatch usage in `docs/docs/developer-guide/avd/hostvars.md`
- [X] T050 [P] Document the native-vs-escape-hatch decision guidance in `docs/docs/developer-guide/avd/extending.md`
- [X] T051 Run `uv run invoke lint` and address ruff/mypy/yamllint findings
- [ ] T052 Run docs build/typecheck (`npm run typecheck` and `npm run build` from `docs/`) and address failures
- [X] T053 Review changed specs and docs for private lab hostnames, tokens, and environment-specific command sequences, and remove or replace any findings in `specs/005-avd-example-fabrics/quickstart.md`
- [ ] T054 Run `$infrahub-run-integration-tests` for the schema and protocol changes and record the tested branch/commit evidence in `specs/005-avd-example-fabrics/quickstart.md`

> Generator idempotence validation (`$infrahub-test-generator-idempotence`) is **not** required in this cycle because it introduces no generator change; it applies to the follow-on generator cycle.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user story phases.
- **US1 (Phase 3)**: Depends on Foundational; no schema change (baseline).
- **US2 (Phase 4)**, **US3 (Phase 5)**: Depend on Foundational; independent of each other (different attributes in `schemas/l3ls_extensions.yml` — sequence same-file edits).
- **US4 (Phase 6)**: Depends on Foundational.
- **US5 (Phase 7)**: Depends on US4 (reuses `l3spine`).
- **US6 (Phase 8)**, **US7 (Phase 9)**: Depend on Foundational; share `schemas/dcim_extensions.yml` and `src/solution_arista_avd/avd.py` with US4 — sequence same-file edits.
- **Polish (Phase 10)**: Depends on all desired user story phases (protocol regen must follow all schema changes).

### Within Each User Story

- Tests are written before implementation and should fail before the matching implementation task lands.
- Schema YAML changes precede `ROLE_TO_AVD_TYPE` mapping where both apply.
- All schema changes precede the single protocol regeneration in Polish.
- Story validation (schema check + tests) completes before moving to the next dependent story.

---

## Parallel Opportunities

- T002–T006 can run in parallel during Setup.
- T008 can run in parallel with T007's follow-up once the test file exists.
- US2 and US3 attribute work can proceed in parallel with US1, but same-file edits in `schemas/l3ls_extensions.yml` must be sequenced.
- Role additions for US4, US6, US7 all touch `schemas/dcim_extensions.yml` and `src/solution_arista_avd/avd.py` — **not** parallel; sequence them.
- Documentation tasks T047, T048, T049, T050 touch different files and can run in parallel once behavior is stable.

---

## Parallel Example: Setup

```text
Task: "T003 [P] Inspect existing DcimDevice.role choices in schemas/dcim_extensions.yml"
Task: "T004 [P] Inspect ROLE_TO_AVD_TYPE in src/solution_arista_avd/avd.py"
Task: "T005 [P] Inspect NetworkFabric underlay/overlay and Avd.Evpn settings in schemas/l3ls_extensions.yml and schemas/avd/avd.yml"
Task: "T006 [P] Confirm pinned pyAVD node_type_keys and record in specs/005-avd-example-fabrics/research.md"
```

## Parallel Example: Polish Documentation

```text
Task: "T047 [P] Update per-scenario status in docs/docs/supported-capabilities.md"
Task: "T048 [P] Document role -> AVD node-type mappings in docs/docs/developer-guide/avd/role-mapping.md"
Task: "T049 [P] Document new inputs and escape-hatch usage in docs/docs/developer-guide/avd/hostvars.md"
Task: "T050 [P] Document native-vs-escape-hatch guidance in docs/docs/developer-guide/avd/extending.md"
```

---

## Implementation Strategy

### MVP First (User Stories 1–3, all P1)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete US1 (baseline unchanged), US2 (`evpn_vlan_aware_bundles`), US3 (`evpn_gateway`).
3. **STOP and VALIDATE**: schema check + contract/mapping tests pass; existing L3LS unchanged.
4. This is the schema MVP: the DC-family scenarios (1–3) have their schema surface.

### Incremental Delivery

1. Setup + Foundational → scaffolding ready.
2. US1–US3 (P1) → DC-family schema surface → validate.
3. US4–US5 (P2) → L2LS roles + underlay-none, campus reuse → validate.
4. US6–US7 (P3) → provider/WAN roles + ISIS-LDP underlay → validate.
5. Polish → single protocol regen, lint, docs, integration validation.

### Parallel Team Strategy

- One implementer owns `schemas/dcim_extensions.yml` + `src/solution_arista_avd/avd.py` role edits (US4, US6, US7) sequentially to avoid same-file conflicts.
- Another owns `schemas/l3ls_extensions.yml` EVPN/underlay inputs (US2, US3) and the contract-test file.
- Documentation (T047–T050) parallelizes at the end.

---

## Notes

- **Cycle boundary**: GraphQL query/return-type changes, generator consumption (route-server/vlan-aware-bundle/gateway rendering, standalone L2LS and campus topology generation, multi-DC/DCI assistance), and per-scenario `objects/` seed designs are **follow-on cycles** — run `/speckit.specify` again for the Generator and Objects artifact types.
- `src/solution_arista_avd/protocols.py` is regenerated (T044), never hand-edited.
- Every new role gets a `ROLE_TO_AVD_TYPE` entry in the same story; T008 asserts full coverage so no role resolves to a missing node type (SC-005).
- All new attributes are optional/defaulted and all new choices are additive, preserving the Single-DC L3LS baseline (SC-003).
- Confirm every new native input and (in later cycles) every escape-hatch key against `pyavd>=6.3.0,<6.4.0` (SC-007).
```
