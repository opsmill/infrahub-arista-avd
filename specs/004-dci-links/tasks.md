# Tasks: DCI Links

**Input**: Design documents from `/specs/004-dci-links/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `.specify/memory/constitution.md`

**Tests**: Required by the feature specification and constitution. Test tasks are listed before the implementation tasks they validate.

**Organization**: Tasks are grouped by user story so each increment can be implemented and validated independently where dependencies allow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files or depends only on completed prerequisite phases
- **[Story]**: User story label (`US1`, `US2`, `US3`, `US4`) for story-phase tasks only
- Every task includes an exact repository file path or validation artifact path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm feature scope, local references, and generated-file workflow before schema or generator edits.

- [X] T001 Confirm active feature inputs and available design documents in `specs/004-dci-links/plan.md`
- [X] T002 [P] Review schema implementation rules for this feature in `.agents/skills/infrahub-managing-schemas/SKILL.md`
- [X] T003 [P] Review generator implementation rules for this feature in `.agents/skills/infrahub-managing-generators/SKILL.md`
- [X] T004 [P] Review menu implementation rules for the DCI Links navigation item in `.agents/skills/infrahub-managing-menus/SKILL.md`
- [X] T005 [P] Review the feature validation workflow and expected commands in `specs/004-dci-links/quickstart.md`
- [X] T006 [P] Inspect current `NetworkLink`, `DcimConnector`, `DcimDevice.role`, and interface schema patterns in `schemas/dcim_extensions.yml`
- [X] T007 [P] Inspect current hostvars role, uplink, connected endpoint, and PyAVD validation patterns in `generators/generate_avd_device_hostvar.py`
- [X] T008 [P] Use `avd-skill` to confirm required PyAVD `l3_edge` keys against the pinned pyAVD version and encode the validation in `tests/unit/test_generate_avd_device_hostvar.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared test helpers and generated-file guardrails that all user stories depend on.

**Critical**: No user story work should begin until this phase is complete.

- [X] T009 Create YAML schema contract test helpers for `schemas/dcim_extensions.yml`, `schemas/dci.yml`, `schemas/ipam_extensions.yml`, and `menus/menu.yml` in `tests/unit/test_dci_schema_contract.py`
- [X] T010 [P] Add DCI hostvars fixture builders for Border Leaf devices, physical interfaces, DCI links, DCI pools, and generated `l3_edge` assertions in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T011 [P] Add DCI ordering fixture builders for multiple and parallel DCI links in `tests/unit/test_hostvar_ordering.py`
- [X] T012 [P] Add a GraphQL query contract helper that validates required DCI fields in `generators/avd_device_hostvar.gql` from `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T013 Record the generated-file rule for `src/solution_arista_avd/protocols.py`, `schema.graphql`, and `generators/generate_avd_device_inputs_query.py` in `specs/004-dci-links/quickstart.md`

**Checkpoint**: Shared DCI tests and regeneration guidance are in place before story implementation begins.

---

## Phase 3: User Story 1 - Identify Border Leafs (Priority: P1)

**Goal**: Operators can classify devices with role value `border_leaf`, and the AVD pipeline treats that role as PyAVD `l3leaf`.

**Independent Test**: Load/check the schema, create or update a `DcimDevice` with `role=border_leaf`, and run AVD unit tests proving `border_leaf -> l3leaf` while existing roles remain available.

### Tests for User Story 1

- [X] T014 [P] [US1] Update role mapping tests for `border_leaf -> l3leaf`, existing role preservation, and unknown-role errors in `tests/unit/test_avd.py`
- [X] T015 [P] [US1] Add schema contract tests proving `DcimDevice.role` keeps existing choices and adds `border_leaf` in `tests/unit/test_dci_schema_contract.py`
- [X] T016 [P] [US1] Add Border Leaf hostvars tests for leaf-family node output and generator target eligibility in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 1

- [X] T017 [US1] Add the `border_leaf` choice with label `Border Leaf` to the `DcimDevice.role` dropdown in `schemas/dcim_extensions.yml`
- [X] T018 [US1] Map `border_leaf` to PyAVD `l3leaf` in `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`
- [X] T019 [US1] Treat `border_leaf` as leaf-family wherever `leaf` receives L3LS, MLAG, EVPN, connected endpoint, node-group, uplink, and generator-target behavior in `generators/generate_avd_device_hostvar.py`
- [X] T020 [US1] Regenerate protocol classes after the role schema change in `src/solution_arista_avd/protocols.py`
- [X] T021 [US1] Validate User Story 1 with unit tests and fix failures or record tracked follow-up tasks outside test source files

**Checkpoint**: Border Leaf is available as a device role and behaves as an AVD `l3leaf`.

---

## Phase 4: User Story 2 - Specialize Existing Links As DCI Links (Priority: P1)

**Goal**: Operators can model one DCI link as a user-facing `NetworkDciLink` that reuses existing physical endpoint behavior without duplicating endpoint or addressing fields.

**Independent Test**: Schema tests prove `NetworkDciLink` inherits the same `DcimConnector` physical endpoint behavior used by `NetworkLink`, keeps compatible identity/display behavior, directly defines no prohibited endpoint or addressing fields, and is exposed through the menu.

### Tests for User Story 2

- [X] T022 [P] [US2] Add schema contract tests proving `NetworkDciLink` and `NetworkLink` both inherit `DcimConnector` physical endpoint behavior in `tests/unit/test_dci_schema_contract.py`
- [X] T023 [P] [US2] Add schema contract tests proving `NetworkDciLink` uses compatible `human_friendly_id`, `display_label`, label, icon, and `include_in_menu: false` values in `tests/unit/test_dci_schema_contract.py`
- [X] T024 [P] [US2] Add schema contract tests proving `NetworkDciLink` has no direct endpoint A/B, subnet, `p2p_pool`, `p2p_link_id`, endpoint IP, endpoint description, speed, BFD, MTU, protocol-selection, external-network, or EVPN Gateway fields in `tests/unit/test_dci_schema_contract.py`
- [X] T025 [P] [US2] Add menu contract tests proving DCI Links navigation points to `NetworkDciLink` in `tests/unit/test_dci_schema_contract.py`
- [X] T026 [P] [US2] Add schema contract tests proving DCI link uniqueness constraints use Infrahub `__value` suffixes for attributes and bare relationship names in `tests/unit/test_dci_schema_contract.py`

### Implementation for User Story 2

- [X] T027 [US2] Create `NetworkDciLink` in `schemas/dci.yml` with the required schema header, label `DCI Link`, icon, `include_in_menu: false`, `inherit_from: [DcimConnector]`, `human_friendly_id`, and `display_label`
- [X] T028 [US2] Preserve existing `NetworkLink` inheritance from `DcimConnector` and shared `DcimConnector.connected_endpoints` behavior while adding DCI schema coverage in `schemas/dci.yml`
- [X] T029 [US2] Add `NetworkDciLink` uniqueness constraints for stable link identity and detectable duplicate endpoint-interface pairs in `schemas/dci.yml`
- [X] T030 [US2] Add the user-facing DCI Links navigation entry for `NetworkDciLink` under the existing Devices or Network menu hierarchy in `menus/menu.yml`
- [X] T031 [US2] Regenerate protocol classes after adding `NetworkDciLink` in `src/solution_arista_avd/protocols.py`
- [X] T032 [US2] Validate User Story 2 schema and menu contracts and fix failures or record tracked follow-up tasks outside test source files

**Checkpoint**: A DCI link object is modeled through shared physical endpoints and exposes no prohibited DCI-specific endpoint or addressing fields.

---

## Phase 5: User Story 3 - Capture DCI BGP Settings And Addressing Source (Priority: P1)

**Goal**: Operators can control underlay participation, record two endpoint BGP ASN values, and assign a fabric-level DCI IP pool as the source for generated `/31` point-to-point addressing.

**Independent Test**: Schema tests prove `NetworkDciLink` directly defines only `include_in_underlay_protocol` and two ASN values as DCI-specific additions, and `NetworkFabric.dci_pool` is optional for existing fabrics but available to the generator.

### Tests for User Story 3

- [X] T033 [P] [US3] Add schema contract tests for direct DCI attributes `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and `endpoint_2_bgp_asn` in `tests/unit/test_dci_schema_contract.py`
- [X] T034 [P] [US3] Add schema contract tests proving `include_in_underlay_protocol` defaults to enabled in `tests/unit/test_dci_schema_contract.py`
- [X] T035 [P] [US3] Add schema contract tests proving no routing protocol, BFD, MTU, speed, pool, subnet, or endpoint IP attribute exists on `NetworkDciLink` in `tests/unit/test_dci_schema_contract.py`
- [X] T036 [P] [US3] Add schema contract tests proving `NetworkFabric.dci_pool` is an optional relationship to `CoreIPPrefixPool` in `tests/unit/test_dci_schema_contract.py`
- [X] T037 [P] [US3] Add schema contract tests proving new `NetworkDciLink` attributes and `NetworkFabric.dci_pool` relationship use order weights consistent with existing schema conventions in `tests/unit/test_dci_schema_contract.py`

### Implementation for User Story 3

- [X] T038 [US3] Add `include_in_underlay_protocol`, `endpoint_1_bgp_asn`, and `endpoint_2_bgp_asn` attributes with conventional order weights to `NetworkDciLink` in `schemas/dci.yml`
- [X] T039 [US3] Add the optional `dci_pool` relationship from `NetworkFabric` to `CoreIPPrefixPool` with identifier `fabric__dci_pool` in `schemas/dci.yml`
- [X] T040 [US3] Document in `specs/004-dci-links/quickstart.md` that `NetworkFabric.dci_pool` is the authoritative DCI pool selector and that no DCI prefix role metadata, direct DCI link pool field, or DCI-specific pool relationship is added
- [X] T041 [US3] Verify no DCI-specific `IpamPrefix.role` choice is added in `schemas/ipam_extensions.yml` for this feature
- [X] T042 [US3] Regenerate protocol classes after the DCI attribute and fabric pool schema changes in `src/solution_arista_avd/protocols.py`
- [X] T043 [US3] Validate User Story 3 schema contracts and fix failures or record tracked follow-up tasks outside test source files

**Checkpoint**: DCI underlay participation, endpoint ASN values, and fabric pool source are modeled without adding prohibited endpoint or addressing fields to the DCI link.

---

## Phase 6: User Story 4 - Generate L3 Edge Intent (Priority: P1)

**Goal**: Valid DCI links between Border Leafs appear in generated AVD hostvars as deterministic PyAVD `l3_edge` intent with one self-contained `p2p_links` entry per valid DCI link.

**Independent Test**: Model one Border Leaf with multiple DCI links, run the hostvars generator, and confirm generated hostvars include deterministic `l3_edge.p2p_links[]` entries with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and `speed` only when endpoint/interface data provides a resolvable speed, without `p2p_links_profiles` or `profile` references.

### Tests for User Story 4

- [X] T044 [P] [US4] Add a GraphQL contract assertion for required `NetworkDciLink` fields, shared endpoints, endpoint device fabric data, and `NetworkFabric.dci_pool` in `generators/avd_device_hostvar.gql` using `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T045 [P] [US4] Add hostvars tests for valid DCI `l3_edge.p2p_links` output with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and resolved `speed` when endpoint/interface data provides it in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T045a [P] [US4] Add hostvars tests proving DCI link speed is omitted when endpoint/interface speed cannot be resolved in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T046 [P] [US4] Add hostvars tests proving DCI output never emits `l3_edge.p2p_links_profiles`, `profile`, or shared DCI profile references in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T047 [P] [US4] Add hostvars tests for `/31` DCI prefix allocation and stable reuse from `NetworkFabric.dci_pool` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T048 [P] [US4] Add hostvars tests for invalid DCI link handling covering endpoint count, non-physical endpoints, non-Border Leaf endpoints, same-device endpoints, duplicate interface pairs, missing ASN values, missing DCI pool, allocation failure, and reported failure context in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T049 [P] [US4] Add deterministic ordering tests for multiple DCI links and multiple parallel links between the same Border Leafs in `tests/unit/test_hostvar_ordering.py`
- [X] T050 [P] [US4] Add hostvars scale tests for 10, 100, and 250 DCI links per fabric, proving stable ordering, allocation reuse, and no duplicate `l3_edge.p2p_links` entries in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T051 [P] [US4] Add a pinned PyAVD validation test for the generated DCI `l3_edge` shape in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 4

- [X] T052 [US4] Extend the hostvars GraphQL query with `NetworkDciLink`, shared `connected_endpoints`, endpoint physical interface fields, endpoint device role/fabric fields, DCI ASN fields, underlay flag, and fabric DCI pool fields in `generators/avd_device_hostvar.gql`
- [X] T053 [US4] Regenerate the typed hostvars query model after GraphQL changes in `generators/generate_avd_device_inputs_query.py`
- [X] T054 [US4] Add or extend addressing helpers to allocate or reuse one stable `/31` prefix per DCI link from `NetworkFabric.dci_pool` without assigning direct DCI endpoint IP attributes in `src/solution_arista_avd/addressing.py`
- [X] T055 [US4] Add typed helpers to extract, normalize, and pair DCI endpoints, endpoint devices, interface names, ASN values, and allocated IP addresses in `generators/generate_avd_device_hostvar.py`
- [X] T056 [US4] Implement generator-side DCI eligibility validation and report invalid DCI link context through the generator execution result or logs in `generators/generate_avd_device_hostvar.py`
- [X] T057 [US4] Implement deterministic DCI link sorting and duplicate endpoint-interface pair detection in `generators/generate_avd_device_hostvar.py`
- [X] T058 [US4] Implement `l3_edge.p2p_links` emission with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and resolved `speed` when available directly on every DCI link entry in `generators/generate_avd_device_hostvar.py`
- [X] T059 [US4] Ensure generated DCI hostvars do not emit `l3_edge.p2p_links_profiles`, `profile`, or shared DCI profile references in `generators/generate_avd_device_hostvar.py`
- [X] T060 [US4] Ensure generated hostvars pass PyAVD validation before saving `AvdHostvarFile` content in `generators/generate_avd_device_hostvar.py`
- [X] T061 [US4] Validate User Story 4 unit tests and fix failures or record tracked follow-up tasks outside test source files

**Checkpoint**: Valid DCI links generate stable PyAVD `l3_edge` hostvars, and invalid links are rejected or excluded with actionable context.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, generated schema refresh, and project validation gates.

- [X] T062 [P] Update supported capability scope for Border Leaf and DCI links in `docs/docs/supported-capabilities.md`
- [X] T063 [P] Update Border Leaf mapping in `docs/docs/developer-guide/avd/role-mapping.md`
- [X] T064 [P] Update DCI hostvars behavior, DCI pool allocation, and supported field boundary in `docs/docs/developer-guide/avd/hostvars.md`
- [X] T065 [P] Update schema documentation for `NetworkDciLink`, `NetworkFabric.dci_pool`, and `border_leaf` in `docs/docs/developer-guide/schemas.md`
- [X] T066 [P] Update AVD pipeline overview with DCI `l3_edge` generation scope in `docs/docs/developer-guide/avd/overview.md`
- [X] T067 Run schema validation and address schema failures in `schemas/dci.yml`
- [X] T068 Regenerate the committed GraphQL schema after schema load or schema check in `schema.graphql`
- [X] T069 Run DCI-focused unit tests and address failures in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T070 Run the standard lint suite and address lint failures in `generators/generate_avd_device_hostvar.py`
- [X] T071 Run documentation typecheck/build and address documentation failures in `docs/docs/supported-capabilities.md`
- [X] T071a Review changed specs, quickstart, docs, and validation evidence for private lab hostnames, tokens, and environment-specific command sequences, and remove or replace any findings with generic placeholders
- [X] T072 Add integration coverage that creates a complete `NetworkDciLink` between two Border Leafs with endpoint interfaces through the shared connected-endpoint object workflow and verifies generated `l3_edge` hostvars in `tests/integration/test_e2e_pipeline.py`
- [ ] T073 Run `$infrahub-run-integration-tests` for the Infrahub schema, menu, generator, query, and documentation changes and record evidence in `specs/004-dci-links/quickstart.md`
- [ ] T074 Run `$infrahub-test-generator-idempotence` for the DCI `l3_edge` generator path when live validation is approved, or document the approved exception in `specs/004-dci-links/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks user story phases.
- **User Story 1 (Phase 3)**: Depends on Foundational; required before full DCI endpoint eligibility can pass.
- **User Story 2 (Phase 4)**: Depends on Foundational; can proceed in parallel with US1 for schema modeling, but full endpoint-role validation requires US1.
- **User Story 3 (Phase 5)**: Depends on US2 because BGP settings and `dci_pool` extend the DCI link and fabric schema surface.
- **User Story 4 (Phase 6)**: Priority P1, but execution depends on US1, US2, and US3 because generator output consumes Border Leaf role, DCI endpoints, ASN values, and DCI pool allocation.
- **Polish (Phase 7)**: Depends on all desired user story phases being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after Phase 2; MVP role/classification increment.
- **US2 (P1)**: Independent after Phase 2 for schema modeling; full endpoint-role validation uses US1 role support.
- **US3 (P1)**: Depends on US2 because it extends the DCI link and fabric schema.
- **US4 (P1)**: Depends on US1, US2, and US3 because complete `l3_edge` output consumes Border Leaf role, DCI endpoints, DCI ASN fields, and DCI pool allocation.

### Within Each User Story

- Tests are written before implementation and should fail before the matching implementation task lands.
- Schema changes precede protocol regeneration.
- GraphQL query changes precede generated query model updates.
- Typed query models precede production generator logic that reads new fields.
- PyAVD validation and deterministic ordering tests must pass before integration and idempotence validation.

---

## Parallel Opportunities

- T002, T003, T004, T005, T006, T007, and T008 can run in parallel during Setup.
- T010, T011, and T012 can run in parallel during Foundational work after T009.
- T014, T015, and T016 can run in parallel for US1 tests.
- T022, T023, T024, T025, and T026 can run in parallel for US2 schema and menu contract tests.
- T033, T034, T035, T036, and T037 can run in parallel for US3 schema contract tests.
- T044, T045, T046, T047, T048, T049, T050, and T051 can run in parallel for US4 hostvars, allocation, ordering, scale, PyAVD, and GraphQL tests.
- T062, T063, T064, T065, and T066 can run in parallel once implementation behavior is stable.

---

## Parallel Example: User Story 1

```bash
Task: "Update role mapping tests for border_leaf -> l3leaf, existing role preservation, and unknown-role errors in tests/unit/test_avd.py"
Task: "Add schema contract tests proving DcimDevice.role keeps existing choices and adds border_leaf in tests/unit/test_dci_schema_contract.py"
Task: "Add Border Leaf hostvars tests for leaf-family node output and generator target eligibility in tests/unit/test_generate_avd_device_hostvar.py"
```

## Parallel Example: User Story 2

```bash
Task: "Add schema contract tests proving NetworkDciLink and NetworkLink both inherit DcimConnector physical endpoint behavior in tests/unit/test_dci_schema_contract.py"
Task: "Add schema contract tests proving NetworkDciLink has no prohibited direct endpoint or addressing fields in tests/unit/test_dci_schema_contract.py"
Task: "Add menu contract tests proving DCI Links navigation points to NetworkDciLink in tests/unit/test_dci_schema_contract.py"
```

## Parallel Example: User Story 3

```bash
Task: "Add schema contract tests for direct DCI attributes include_in_underlay_protocol, endpoint_1_bgp_asn, and endpoint_2_bgp_asn in tests/unit/test_dci_schema_contract.py"
Task: "Add schema contract tests proving NetworkFabric.dci_pool is an optional relationship to CoreIPPrefixPool in tests/unit/test_dci_schema_contract.py"
Task: "Add schema contract tests proving new DCI attributes and the dci_pool relationship use conventional order weights in tests/unit/test_dci_schema_contract.py"
```

## Parallel Example: User Story 4

```bash
Task: "Add hostvars tests for valid DCI l3_edge.p2p_links output in tests/unit/test_generate_avd_device_hostvar.py"
Task: "Add hostvars tests proving DCI output never emits l3_edge.p2p_links_profiles, profile, or shared DCI profile references in tests/unit/test_generate_avd_device_hostvar.py"
Task: "Add hostvars tests for /31 DCI prefix allocation and stable reuse from NetworkFabric.dci_pool in tests/unit/test_generate_avd_device_hostvar.py"
Task: "Add hostvars tests for invalid DCI link handling in tests/unit/test_generate_avd_device_hostvar.py"
Task: "Add deterministic ordering tests for multiple DCI links in tests/unit/test_hostvar_ordering.py"
Task: "Add a pinned PyAVD validation test for the generated DCI l3_edge shape in tests/unit/test_generate_avd_device_hostvar.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to introduce `border_leaf` and AVD `l3leaf` classification.
3. Complete US2 to introduce `NetworkDciLink` through shared `DcimConnector` endpoint behavior.
4. Complete US3 because US4 consumes DCI ASN attributes and the fabric DCI pool.
5. Complete the US4 happy path for one valid DCI link and validate generated PyAVD `l3_edge`.
6. Stop and validate the MVP with the DCI-focused unit tests before adding broad edge-case coverage.

### Incremental Delivery

1. Deliver US1 role classification and tests.
2. Deliver US2 DCI link schema and menu visibility.
3. Deliver US3 DCI underlay, ASN, and pool modeling.
4. Deliver US4 generator output for valid links.
5. Add invalid-link reporting, deterministic ordering, docs, integration validation, and idempotence validation.

### Parallel Team Strategy

1. One engineer handles schema and menu work in `schemas/` and `menus/`.
2. One engineer handles hostvars query/model and generator work in `generators/` and `src/solution_arista_avd/`.
3. One engineer handles tests and docs in `tests/` and `docs/docs/`.
4. Coordinate at generated-file boundaries: `src/solution_arista_avd/protocols.py`, `schema.graphql`, and `generators/generate_avd_device_inputs_query.py`.

---

## Notes

- `NetworkDciLink` must inherit `DcimConnector`, not the concrete `NetworkLink` node.
- DCI generated output must not use `l3_edge.p2p_links_profiles` or `profile`.
- DCI generated output must place `include_in_underlay_protocol` and resolved `speed`, when available, directly under each `l3_edge.p2p_links[]` entry; unresolved `speed` must be omitted.
- Generated files must be regenerated from schemas or GraphQL queries, not hand-edited.
- Dedicated check implementation remains out of scope unless implementation discovers a rule that cannot be enforced or reported through schema constraints and generator behavior.
