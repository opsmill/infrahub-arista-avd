# Tasks: DCI Links

**Input**: Design documents from `/specs/004-dci-links/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `.specify/memory/constitution.md`

**Tests**: Required by the feature specification and constitution. Test tasks are listed before the implementation tasks they validate.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated as an independent increment where dependencies allow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed prerequisite phases
- **[Story]**: User story label (`US1`, `US2`, `US3`, `US4`) for story-phase tasks only
- Every task includes an exact repository file path or validation artifact path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm feature scope, local rules, and generated-file workflow before schema or generator edits.

- [X] T001 Confirm active feature inputs and current Network Link DCI scope in `specs/004-dci-links/plan.md`
- [X] T002 [P] Review schema implementation rules for this feature in `.agents/skills/infrahub-managing-schemas/SKILL.md`
- [X] T003 [P] Review generator implementation rules for this feature in `.agents/skills/infrahub-managing-generators/SKILL.md`
- [X] T004 [P] Review menu implementation rules for Network Link navigation cleanup in `.agents/skills/infrahub-managing-menus/SKILL.md`
- [X] T005 [P] Review the AVD schema validation requirement for `l3_edge.p2p_links` in `.agents/skills/avd-skill/SKILL.md`
- [X] T006 [P] Inspect existing `DcimDevice.role`, `NetworkLink`, `DcimConnector`, and `NetworkFabric` schema patterns in `schemas/dcim_extensions.yml`
- [X] T007 [P] Inspect current Border Leaf, connected endpoint, and hostvars generator patterns in `generators/generate_avd_device_hostvar.py`
- [X] T008 [P] Inspect current point-to-point allocation helpers in `src/solution_arista_avd/addressing.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared test helpers, stale-reference checks, and generated-file guardrails that all user stories depend on.

**Critical**: No user story work should begin until this phase is complete.

- [X] T009 Create YAML schema contract helpers for `schemas/dcim_extensions.yml`, `schemas/dci.yml`, `schemas/ipam_extensions.yml`, and `menus/menu.yml` in `tests/unit/test_dci_schema_contract.py`
- [X] T010 [P] Add reusable hostvars fixture builders for Border Leaf devices, physical interfaces, Network Link DCI records, DCI pools, and `l3_edge` assertions in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T011 [P] Add reusable ordering fixture builders for multiple and parallel DCI-role Network Links in `tests/unit/test_hostvar_ordering.py`
- [X] T012 [P] Add a reusable GraphQL query contract helper that parses `generators/avd_device_hostvar.gql` for required DCI Network Link fields from `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T013 [P] Add a stale-reference contract helper that asserts implementation paths contain no `NetworkDciLink` or unsupported `DciLink` references in `tests/unit/test_dci_schema_contract.py`
- [X] T014 Record the generated-file rule for `src/solution_arista_avd/protocols.py`, `schema.graphql`, and `generators/generate_avd_device_inputs_query.py` in `specs/004-dci-links/quickstart.md`
- [X] T015 Record the duplicate `allocate_p2p_prefix_from_pool` consolidation decision in `specs/004-dci-links/research.md`

**Checkpoint**: Shared DCI tests and regeneration guidance are in place before story implementation begins.

---

## Phase 3: User Story 1 - Classify Border Leafs (Priority: P1)

**Goal**: Operators can classify devices with role value `border_leaf`, and the AVD pipeline treats that role as PyAVD `l3leaf`.

**Independent Test**: Load/check the schema, create or update a `DcimDevice` with `role=border_leaf`, and run AVD unit tests proving `border_leaf -> l3leaf` while existing roles remain available.

### Tests for User Story 1

- [X] T016 [P] [US1] Update role mapping tests for `border_leaf -> l3leaf`, existing role preservation, and unknown-role errors in `tests/unit/test_avd.py`
- [X] T017 [P] [US1] Add schema contract tests proving `DcimDevice.role` keeps existing choices and adds `border_leaf` in `tests/unit/test_dci_schema_contract.py`
- [X] T018 [P] [US1] Add Border Leaf hostvars tests for leaf-family node output and generator target eligibility in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 1

- [X] T019 [US1] Add the `border_leaf` choice with label `Border Leaf` to the `DcimDevice.role` dropdown in `schemas/dcim_extensions.yml`
- [X] T020 [US1] Map `border_leaf` to PyAVD `l3leaf` in `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T021 [US1] Treat `border_leaf` as leaf-family wherever `leaf` receives L3LS, MLAG, EVPN, connected endpoint, node-group, uplink, and generator-target behavior in `generators/generate_avd_device_hostvar.py`
- [X] T022 [US1] Regenerate protocol classes after the role schema change in `src/solution_arista_avd/protocols.py`
- [X] T023 [US1] Validate User Story 1 with `uv run pytest tests/unit/test_avd.py tests/unit/test_dci_schema_contract.py tests/unit/test_generate_avd_device_hostvar.py` and record evidence in `specs/004-dci-links/quickstart.md`

**Checkpoint**: Border Leaf is available as a device role and behaves as an AVD `l3leaf`.

---

## Phase 4: User Story 2 - Mark Network Links As DCI Links (Priority: P1)

**Goal**: Operators can model one DCI connection as an existing `NetworkLink` with role `dci`, reusing the standard physical link endpoint model and removing the stale standalone DCI link model.

**Independent Test**: Create a Network Link with two Border Leaf endpoint interfaces and role `dci`, then confirm ordinary Network Link behavior still works for non-DCI links and no `NetworkDciLink` implementation artifact remains.

### Tests for User Story 2

- [X] T024 [P] [US2] Add schema contract tests proving `NetworkLink.role` supports the `dci` choice while preserving optional role behavior in `tests/unit/test_dci_schema_contract.py`
- [X] T025 [P] [US2] Add schema contract tests proving existing `NetworkLink` identity, display, and `DcimConnector.connected_endpoints` behavior remains unchanged in `tests/unit/test_dci_schema_contract.py`
- [X] T026 [P] [US2] Add schema contract tests proving non-DCI Network Links are not DCI candidates in `tests/unit/test_dci_schema_contract.py`
- [X] T027 [P] [US2] Add schema contract tests proving no standalone `NetworkDciLink` node remains in `schemas/dci.yml` or `schemas/dcim_extensions.yml` in `tests/unit/test_dci_schema_contract.py`
- [X] T028 [P] [US2] Add menu contract tests proving `menus/menu.yml` does not expose `NetworkDciLink` and keeps Network Link discovery available in `tests/unit/test_dci_schema_contract.py`
- [X] T029 [P] [US2] Add hostvars tests proving only Network Links with role value `dci` are selected as DCI candidates in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 2

- [X] T030 [US2] Add or extend the optional `role` dropdown on `NetworkLink` with machine value `dci` and label `DCI` in `schemas/dcim_extensions.yml`
- [X] T031 [US2] Preserve existing `NetworkLink` inheritance from `DcimConnector` and shared `connected_endpoints` behavior while adding role coverage in `schemas/dcim_extensions.yml`
- [X] T032 [US2] Remove the stale standalone `NetworkDciLink` schema surface from `schemas/dci.yml`
- [X] T033 [US2] Remove stale standalone DCI link navigation from `menus/menu.yml` while keeping existing Network Link navigation usable
- [X] T034 [US2] Remove stale `NetworkDciLink` references from hostvars query and generated query model inputs in `generators/avd_device_hostvar.gql`
- [X] T035 [US2] Regenerate protocol classes after Network Link role and stale schema removal in `src/solution_arista_avd/protocols.py`
- [X] T036 [US2] Regenerate the exported GraphQL schema after stale kind removal in `schema.graphql`
- [X] T037 [US2] Regenerate the typed hostvars query model after query changes in `generators/generate_avd_device_inputs_query.py`
- [X] T038 [US2] Validate zero stale implementation references with `rg "NetworkDciLink|DciLink" schemas generators transforms tests docs src menus .infrahub.yml schema.graphql` and record exceptions only in `specs/004-dci-links/quickstart.md`; the validation must prove regenerated `schema.graphql` no longer exposes `NetworkDciLink` types or fields
- [X] T039 [US2] Validate User Story 2 schema, menu, query, and stale-reference contracts with `uv run pytest tests/unit/test_dci_schema_contract.py tests/unit/test_generate_avd_device_hostvar.py` and record evidence in `specs/004-dci-links/quickstart.md`

**Checkpoint**: DCI links are represented only by existing Network Link objects with role `dci`; stale standalone DCI link artifacts are removed.

---

## Phase 5: User Story 3 - Capture DCI Settings And Addressing Source (Priority: P1)

**Goal**: Operators can control underlay participation, record two endpoint BGP ASN values, and assign a fabric-level DCI IP pool as the source for generated `/31` point-to-point addressing.

**Independent Test**: Create DCI-role Network Links with default underlay participation, endpoint ASN values, and an available fabric DCI pool, then confirm the modeled and allocated values are unambiguous for generated intent.

### Tests for User Story 3

- [X] T040 [P] [US3] Add schema contract tests for direct Network Link DCI attributes `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and `endpoint_2_bgp_asn` in `tests/unit/test_dci_schema_contract.py`
- [X] T041 [P] [US3] Add schema contract tests proving `include_in_underlay_protocol` defaults to enabled in `tests/unit/test_dci_schema_contract.py`
- [X] T042 [P] [US3] Add schema contract tests proving `NetworkLink` has no DCI-specific endpoint A/B, pool, subnet, endpoint IP, speed, BFD, MTU, protocol-selection, external-network, or EVPN Gateway fields in `tests/unit/test_dci_schema_contract.py`
- [X] T043 [P] [US3] Add schema contract tests proving `NetworkFabric.dci_pool` is an optional relationship to `CoreIPPrefixPool` in `tests/unit/test_dci_schema_contract.py`
- [X] T044 [P] [US3] Add addressing tests proving `/31` allocation uses `NetworkFabric.dci_pool`, stable link identity, and no direct endpoint IP storage in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 3

- [X] T045 [US3] Add `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and `endpoint_2_bgp_asn` attributes with safe defaults or optional schema behavior to `NetworkLink` in `schemas/dcim_extensions.yml`
- [X] T046 [US3] Add the optional `dci_pool` relationship from `NetworkFabric` to `CoreIPPrefixPool` with identifier `fabric__dci_pool` in `schemas/dci.yml`
- [X] T047 [US3] Confirm no DCI-specific prefix role metadata is added in `schemas/ipam_extensions.yml`
- [X] T048 [US3] Consolidate DCI generation on the shared `allocate_p2p_prefix_from_pool` implementation or document a tested exception in `src/solution_arista_avd/addressing.py`
- [X] T049 [US3] Update `generators/avd_device_hostvar.gql` to fetch Network Link DCI attributes and `NetworkFabric.dci_pool` data in `generators/avd_device_hostvar.gql`
- [X] T050 [US3] Regenerate protocol classes after DCI attribute and fabric pool schema changes in `src/solution_arista_avd/protocols.py`
- [X] T051 [US3] Regenerate the exported GraphQL schema after DCI attribute and fabric pool schema changes in `schema.graphql`
- [X] T052 [US3] Regenerate the typed hostvars query model after GraphQL changes in `generators/generate_avd_device_inputs_query.py`
- [X] T053 [US3] Document `NetworkFabric.dci_pool` as the authoritative DCI pool selector and excluded DCI fields in `specs/004-dci-links/quickstart.md`
- [X] T054 [US3] Validate User Story 3 schema and allocation contracts with `uv run pytest tests/unit/test_dci_schema_contract.py tests/unit/test_generate_avd_device_hostvar.py` and record evidence in `specs/004-dci-links/quickstart.md`

**Checkpoint**: DCI underlay participation, endpoint ASN values, and fabric pool source are modeled without adding prohibited endpoint or addressing fields to Network Link.

---

## Phase 6: User Story 4 - Generate L3 Edge Intent (Priority: P1)

**Goal**: Valid DCI-role Network Links between Border Leafs appear in generated AVD hostvars as deterministic PyAVD `l3_edge` intent with one self-contained `p2p_links` entry per valid DCI link.

**Independent Test**: Model multiple DCI-role Network Links from one Border Leaf to remote Border Leafs, run hostvars generation, and confirm deterministic `l3_edge.p2p_links` output with invalid links reported and excluded.

### Tests for User Story 4

- [X] T055 [P] [US4] Use the reusable GraphQL query contract helper to assert required `NetworkLink` fields, shared endpoints, endpoint device fabric data, and `NetworkFabric.dci_pool` in `generators/avd_device_hostvar.gql` using `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T056 [P] [US4] Add hostvars tests for valid DCI `l3_edge.p2p_links` output with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and resolved `speed` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T057 [P] [US4] Add hostvars tests proving DCI link speed is omitted when endpoint/interface speed cannot be resolved in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T058 [P] [US4] Add hostvars tests proving DCI output never emits `l3_edge.p2p_links_profiles`, `profile`, or shared DCI profile references in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T059 [P] [US4] Add hostvars tests for `/31` DCI prefix allocation and stable reuse from `NetworkFabric.dci_pool` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T060 [P] [US4] Add invalid DCI link tests for endpoint count, non-physical endpoints, non-Border Leaf endpoints, same-device endpoints, duplicate interface pairs, missing ASN values, missing DCI pool, allocation failure, and reported failure context proving invalid links are excluded while valid links in the same fabric still generate in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T061 [P] [US4] Add deterministic ordering tests for multiple DCI links and multiple parallel links between the same Border Leafs in `tests/unit/test_hostvar_ordering.py`
- [X] T062 [P] [US4] Add hostvars scale tests for 10, 100, and 250 DCI links per fabric, proving stable ordering, allocation reuse, and no duplicate `l3_edge.p2p_links` entries in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T063 [P] [US4] Add a pinned PyAVD validation test for generated DCI `l3_edge` shapes with and without `speed` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T064 [P] [US4] Add integration coverage that creates a complete Network Link with role `dci` between two Border Leafs and verifies generated `l3_edge` hostvars in `tests/integration/test_e2e_pipeline.py`

### Implementation for User Story 4

- [X] T065 [US4] Extend `generators/avd_device_hostvar.gql` with Network Link role, shared `connected_endpoints`, endpoint physical interface fields, endpoint device role/fabric fields, DCI ASN fields, underlay flag, and fabric DCI pool fields
- [X] T066 [US4] Regenerate the typed hostvars query model after GraphQL changes in `generators/generate_avd_device_inputs_query.py`
- [X] T067 [US4] Add or update typed helpers to extract, normalize, and pair DCI endpoints, endpoint devices, interface names, ASN values, allocated IP addresses, and optional speed in `generators/generate_avd_device_hostvar.py`
- [X] T068 [US4] Implement generator-side DCI eligibility validation, invalid-link exclusion, and actionable invalid-link reporting in `generators/generate_avd_device_hostvar.py`
- [X] T069 [US4] Implement deterministic DCI link sorting and duplicate endpoint-interface pair detection in `generators/generate_avd_device_hostvar.py`
- [X] T070 [US4] Implement `l3_edge.p2p_links` emission with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and resolved `speed` when available in `generators/generate_avd_device_hostvar.py`
- [X] T071 [US4] Ensure generated DCI hostvars do not emit `l3_edge.p2p_links_profiles`, `profile`, or shared DCI profile references in `generators/generate_avd_device_hostvar.py`
- [X] T072 [US4] Ensure generated hostvars pass PyAVD validation before saving `AvdHostvarFile` content in `generators/generate_avd_device_hostvar.py`
- [X] T073 [US4] Validate User Story 4 unit and integration tests with `uv run pytest tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py tests/integration/test_e2e_pipeline.py` and record evidence in `specs/004-dci-links/quickstart.md`

**Checkpoint**: Valid DCI-role Network Links generate stable PyAVD `l3_edge` hostvars, and invalid links are excluded and reported with actionable context.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, generated schema refresh, and project validation gates.

- [X] T074 [P] Update supported capability scope for Border Leaf and DCI Network Links in `docs/docs/supported-capabilities.md`
- [X] T075 [P] Update Border Leaf mapping in `docs/docs/developer-guide/avd/role-mapping.md`
- [X] T076 [P] Update DCI hostvars behavior, DCI pool allocation, and supported field boundary in `docs/docs/developer-guide/avd/hostvars.md`
- [X] T077 [P] Update schema documentation for `NetworkLink.role=dci`, `NetworkFabric.dci_pool`, and `border_leaf` in `docs/docs/developer-guide/schemas.md`
- [X] T078 [P] Update AVD pipeline overview with DCI `l3_edge` generation from Network Links in `docs/docs/developer-guide/avd/overview.md`
- [X] T079 Run schema validation and address schema failures in `schemas/dcim_extensions.yml` and `schemas/dci.yml`
- [X] T080 Run DCI-focused unit tests and address failures in `tests/unit/test_dci_schema_contract.py`, `tests/unit/test_generate_avd_device_hostvar.py`, and `tests/unit/test_hostvar_ordering.py`
- [X] T081 Run the standard lint suite and address lint failures in `generators/generate_avd_device_hostvar.py`
- [X] T082 Run documentation typecheck/build and address documentation failures in `docs/docs/supported-capabilities.md`
- [X] T083 Review changed specs, quickstart, docs, and validation evidence for private lab hostnames, tokens, and environment-specific command sequences, and remove or replace any findings in `specs/004-dci-links/quickstart.md`
- [X] T084 Run `$infrahub-run-integration-tests` for the Infrahub schema, menu, generator, query, and documentation changes and record evidence in `specs/004-dci-links/quickstart.md`
- [X] T085 Run `$infrahub-test-generator-idempotence` for the DCI `l3_edge` generator path when live validation is approved, or document the approved exception in `specs/004-dci-links/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks user story phases.
- **User Story 1 (Phase 3)**: Depends on Foundational; required before full DCI endpoint eligibility can pass.
- **User Story 2 (Phase 4)**: Depends on Foundational; can proceed in parallel with US1 for schema modeling, but full endpoint-role validation uses US1.
- **User Story 3 (Phase 5)**: Depends on US2 because it extends the Network Link and fabric schema surfaces consumed by the generator.
- **User Story 4 (Phase 6)**: Depends on US1, US2, and US3 because complete `l3_edge` output consumes Border Leaf role, DCI Network Links, ASN fields, and DCI pool allocation.
- **Polish (Phase 7)**: Depends on all desired user story phases being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2; MVP role/classification increment.
- **US2 (P1)**: Independent after Phase 2 for Network Link DCI modeling; full endpoint-role validation uses US1 role support.
- **US3 (P1)**: Depends on US2 because it extends Network Link and Network Fabric with DCI settings and pool source.
- **US4 (P1)**: Depends on US1, US2, and US3 because generated `l3_edge` output consumes Border Leaf role, DCI Network Links, DCI ASN fields, and DCI pool allocation.

### Within Each User Story

- Tests are written before implementation and should fail before the matching implementation task lands.
- Schema changes precede protocol regeneration.
- GraphQL query changes precede generated query model updates.
- Typed query models precede production generator logic that reads new fields.
- PyAVD validation and deterministic ordering tests must pass before integration and idempotence validation.

---

## Parallel Opportunities

- T002, T003, T004, T005, T006, T007, and T008 can run in parallel during Setup.
- T010, T011, T012, and T013 can run in parallel during Foundational work after T009.
- T016, T017, and T018 can run in parallel for US1 tests.
- T024, T025, T026, T027, T028, and T029 can run in parallel for US2 schema, menu, stale-reference, and hostvars tests.
- T040, T041, T042, T043, and T044 can run in parallel for US3 schema and allocation tests.
- T055, T056, T057, T058, T059, T060, T061, T062, T063, and T064 can run in parallel for US4 hostvars, allocation, ordering, scale, PyAVD, GraphQL, and integration tests.
- T074, T075, T076, T077, and T078 can run in parallel once implementation behavior is stable.

---

## Parallel Example: User Story 1

```text
Task: "T016 [P] [US1] Update role mapping tests for `border_leaf -> l3leaf`, existing role preservation, and unknown-role errors in `tests/unit/test_avd.py`"
Task: "T017 [P] [US1] Add schema contract tests proving `DcimDevice.role` keeps existing choices and adds `border_leaf` in `tests/unit/test_dci_schema_contract.py`"
Task: "T018 [P] [US1] Add Border Leaf hostvars tests for leaf-family node output and generator target eligibility in `tests/unit/test_generate_avd_device_hostvar.py`"
```

## Parallel Example: User Story 2

```text
Task: "T024 [P] [US2] Add schema contract tests proving `NetworkLink.role` supports the `dci` choice while preserving optional role behavior in `tests/unit/test_dci_schema_contract.py`"
Task: "T027 [P] [US2] Add schema contract tests proving no standalone `NetworkDciLink` node remains in `schemas/dci.yml` or `schemas/dcim_extensions.yml` in `tests/unit/test_dci_schema_contract.py`"
Task: "T029 [P] [US2] Add hostvars tests proving only Network Links with role value `dci` are selected as DCI candidates in `tests/unit/test_generate_avd_device_hostvar.py`"
```

## Parallel Example: User Story 3

```text
Task: "T040 [P] [US3] Add schema contract tests for direct Network Link DCI attributes `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and `endpoint_2_bgp_asn` in `tests/unit/test_dci_schema_contract.py`"
Task: "T043 [P] [US3] Add schema contract tests proving `NetworkFabric.dci_pool` is an optional relationship to `CoreIPPrefixPool` in `tests/unit/test_dci_schema_contract.py`"
Task: "T044 [P] [US3] Add addressing tests proving `/31` allocation uses `NetworkFabric.dci_pool`, stable link identity, and no direct endpoint IP storage in `tests/unit/test_generate_avd_device_hostvar.py`"
```

## Parallel Example: User Story 4

```text
Task: "T056 [P] [US4] Add hostvars tests for valid DCI `l3_edge.p2p_links` output with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and resolved `speed` in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "T060 [P] [US4] Add invalid DCI link tests for endpoint count, non-physical endpoints, non-Border Leaf endpoints, same-device endpoints, duplicate interface pairs, missing ASN values, missing DCI pool, allocation failure, and reported failure context proving invalid links are excluded while valid links in the same fabric still generate in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "T061 [P] [US4] Add deterministic ordering tests for multiple DCI links and multiple parallel links between the same Border Leafs in `tests/unit/test_hostvar_ordering.py`"
Task: "T064 [P] [US4] Add integration coverage that creates a complete Network Link with role `dci` between two Border Leafs and verifies generated `l3_edge` hostvars in `tests/integration/test_e2e_pipeline.py`"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate `border_leaf` schema and AVD `l3leaf` mapping independently.

### Incremental Delivery

1. Complete Setup and Foundational phases.
2. Deliver US1 to classify Border Leafs.
3. Deliver US2 to model DCI through Network Link role `dci` and remove stale standalone artifacts.
4. Deliver US3 to add DCI per-link settings and fabric DCI pool allocation source.
5. Deliver US4 to generate deterministic PyAVD `l3_edge` hostvars.
6. Complete cross-cutting docs, lint, integration, and idempotence validation.

### Parallel Team Strategy

1. One implementer completes schema contracts and helper setup in Phase 2.
2. Schema-focused work can progress through US1, US2, and US3 while generator-focused tests for US4 are drafted after the shared fixture helpers exist.
3. Documentation tasks T074 through T078 can run in parallel after implementation behavior stabilizes.

---

## Notes

- Generated files must be regenerated, not hand-edited: `src/solution_arista_avd/protocols.py`, `schema.graphql`, and `generators/generate_avd_device_inputs_query.py`.
- DCI generation must source candidates from `NetworkLink.role = dci`; a standalone `NetworkDciLink` kind is stale by definition.
- Each story should be validated independently before moving to the next dependent story.
- Required project validation remains `$infrahub-run-integration-tests` and `$infrahub-test-generator-idempotence` for this Infrahub generator change.
