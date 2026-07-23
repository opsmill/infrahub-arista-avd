# Tasks: EVPN Gateway Domains

**Input**: Design documents from `/specs/004-evpn-gateway/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Tests are included because the feature specification, contracts, quickstart, and constitution require schema, generator-side validation, hostvar, pyAVD, menu, lint, integration, and generator idempotence validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested as an independent increment.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm prerequisite role support and identify stale per-device gateway surfaces before implementing the domain/group model.

- [X] T001 Verify the `border_leaf` dependency from PR #74 is present in `schemas/dcim_extensions.yml`, `src/solution_arista_avd/avd.py`, and `tests/unit/test_avd.py`
- [X] T002 [P] Review existing EVPN schema conventions in `schemas/evpn/evpn_services.yml` and `schemas/evpn/evpn_gateway.yml`
- [X] T003 [P] Review existing hostvar generator structure in `generators/avd_device_hostvar.gql`, `generators/generate_avd_device_hostvar.py`, and `generators/generate_avd_device_inputs_query.py`
- [X] T004 [P] Review existing EVPN Services menu placement in `menus/menu.yml`
- [X] T005 [P] Identify and record stale per-device `EvpnGateway` references that must be replaced in `schemas/evpn/evpn_gateway.yml`, `generators/`, `tests/unit/`, and `docs/docs/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare shared tests and validation helpers needed by the schema, menu, and hostvar stories.

**CRITICAL**: No user story work can be considered complete until these shared prerequisites are satisfied.

- [X] T006 [P] Add or reset EVPN Gateway schema contract test coverage in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T007 [P] Add or reset EVPN Gateway menu contract test coverage in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T008 [P] Add or reset EVPN Gateway hostvar fixture helpers in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T009 [P] Add or reset EVPN Gateway hostvar ordering coverage in `tests/unit/test_hostvar_ordering.py`

**Checkpoint**: Shared test locations exist and no user story depends on undefined test scaffolding.

---

## Phase 3: User Story 1 - Model EVPN Domains Across a Fabric (Priority: P1) MVP

**Goal**: A Fabric owns zero or more EVPN Domains, each Pod belongs to zero or one EVPN Domain, and the model does not define a dedicated `EvpnGateway` node.

**Independent Test**: Load schema for a Fabric with no EVPN Domains, then with multiple EVPN Domains and Pods assigned to only one domain each; verify duplicate domain IDs or names within a Fabric are rejected or reported.

### Tests for User Story 1

- [X] T010 [P] [US1] Add schema contract tests for `EvpnDomain` node kind, required `name` and `domain_id`, Fabric ownership, `include_in_menu: false`, and no `EvpnGateway` node in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T011 [P] [US1] Add schema contract tests for additive `NetworkFabric.evpn_domains`, optional `NetworkPod.evpn_domain`, and inverse `EvpnDomain.pods` relationships in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T012 [P] [US1] Add schema contract tests for `EvpnDomain` uniqueness by `[fabric, name__value]` and `[fabric, domain_id__value]` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T013 [P] [US1] Add migration-safety tests that existing Fabric and Pod schema extensions remain optional in `tests/unit/test_evpn_gateway_schema_contract.py`

### Implementation for User Story 1

- [X] T014 [US1] Replace stale per-device gateway schema with `EvpnDomain` and Fabric/Pod relationship extensions in `schemas/evpn/evpn_gateway.yml`
- [X] T015 [US1] Remove any concrete `EvpnGateway` node, `DcimDevice.evpn_gateway`, and selectable gateway-local-domain schema surfaces from `schemas/evpn/evpn_gateway.yml`
- [X] T016 [US1] Regenerate protocol classes from `schemas/` into `src/solution_arista_avd/protocols.py`
- [X] T017 [US1] Validate the schema changes with `uv run infrahubctl schema check schemas/ --branch evpn-gateway-validation` against `schemas/`
- [X] T018 [US1] Run focused US1 tests for `tests/unit/test_evpn_gateway_schema_contract.py`

**Checkpoint**: Domain membership is schema-modeled independently and existing non-gateway Fabrics and Pods remain valid.

---

## Phase 4: User Story 2 - Enable Gateways Through Border Leaf Groups (Priority: P2)

**Goal**: An EVPN Gateway Group activates gateway behavior for one or more Border Leaf devices from its Pod, derives its local domain from the Pod, and carries shared EVPN L2/L3, D-PATH, resiliency, and all-active Ethernet Segment settings.

**Independent Test**: Assign a Pod to a local EVPN Domain, create a remote EVPN Domain, create a gateway group for that Pod with Border Leaf members from the same Pod, and verify non-members remain normal Border Leafs.

### Tests for User Story 2

- [X] T019 [P] [US2] Add schema contract tests for `EvpnGatewayGroup` attributes, all-active-only `resiliency_model`, Pod parent, remote-domain relationship, member relationship, inverse `DcimDevice.evpn_gateway_group` cardinality-one membership, and `[pod, name__value]` uniqueness in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T020 [P] [US2] Add schema contract tests that `EvpnGatewayGroup` has no independently selected `local_domain` relationship and no helper attributes solely for Pod-derived local-domain display in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T021 [P] [US2] Add schema contract tests that all new bidirectional relationships use matching `identifier` values and relationship `peer` values use full schema kinds in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T022 [P] [US2] Add hostvar tests for grouped `border_leaf` devices receiving shared EVPN L2/L3, D-PATH, resiliency, and Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T023 [P] [US2] Add hostvar omission tests for `leaf`, `l2leaf`, `spine`, `super_spine`, and ungrouped `border_leaf` devices in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T024 [P] [US2] Add generator-side validation tests for non-`border_leaf` members, cross-Pod members, missing Pod EVPN Domain, empty members, same local and remote domain, unsupported resiliency, and missing Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T025 [P] [US2] Add pyAVD validation and deprecated-key assertions for generated EVPN Gateway payloads in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement `EvpnGatewayGroup` node, attributes, Pod parent, remote-domain relationship, member relationship, display metadata, and uniqueness in `schemas/evpn/evpn_gateway.yml`
- [X] T027 [US2] Add optional inverse `NetworkPod.evpn_gateway_groups` and `DcimDevice.evpn_gateway_group` relationships in `schemas/evpn/evpn_gateway.yml`, then regenerate protocol classes from the current schema state into `src/solution_arista_avd/protocols.py`
- [X] T028 [US2] Update `generators/avd_device_hostvar.gql` to fetch the target device `evpn_gateway_group`, group Pod, Pod local EVPN Domain, remote EVPN Domain, group members, and required gateway attributes
- [X] T029 [US2] Regenerate `generators/generate_avd_device_inputs_query.py` from `generators/avd_device_hostvar.gql`
- [X] T030 [US2] Implement EVPN Gateway Group extraction, eligibility validation, shared payload mapping, ungrouped-device omission, and actionable generator errors in `generators/generate_avd_device_hostvar.py`
- [X] T031 [US2] Call `pyavd.validate_inputs()` on final hostvars before writing `AvdHostvarFile` in `generators/generate_avd_device_hostvar.py`
- [X] T032 [US2] Preserve deterministic hostvar ordering and add gateway ordering assertions in `tests/unit/test_hostvar_ordering.py`
- [X] T033 [US2] Run focused US2 tests for `tests/unit/test_evpn_gateway_schema_contract.py`, `tests/unit/test_generate_avd_device_hostvar.py`, and `tests/unit/test_hostvar_ordering.py`

**Checkpoint**: Gateway behavior is activated only by valid Border Leaf membership in an EVPN Gateway Group.

---

## Phase 5: User Story 3 - Derive Full-Mesh Peering from Remote Domains (Priority: P3)

**Goal**: Gateway Border Leafs sharing the same remote EVPN Domain derive deterministic full-mesh hostname-only remote peers without manually modeled peer objects.

**Independent Test**: Model two or more gateway groups in different local domains sharing a remote CORE domain and verify each member Border Leaf sees all other enabled gateway Border Leafs sharing CORE in sorted remote peer order.

### Tests for User Story 3

- [X] T034 [P] [US3] Add hostvar tests for full-mesh peer derivation across gateway groups sharing one remote EVPN Domain in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T035 [P] [US3] Add hostvar tests for deterministic peer hostname ordering, target self-exclusion, same-local-domain exclusion or rejection, and singleton remote-domain empty peer lists in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T036 [P] [US3] Add validation tests that route-server, route-reflector, manually modeled peer objects, peer IP fields, and peer BGP ASN fields are not accepted in this phase in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T037 [P] [US3] Add a pyAVD smoke test for two generated gateway hostvar files with hostname-only remote peers using `get_avd_facts()` and `get_device_structured_config()` in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 3

- [X] T038 [US3] Extend `generators/avd_device_hostvar.gql` with `remote_domain.remote_gateway_groups` traversal for peer candidate gateway groups and members
- [X] T039 [US3] Regenerate `generators/generate_avd_device_inputs_query.py` from the updated remote-domain traversal in `generators/avd_device_hostvar.gql`
- [X] T040 [US3] Implement deterministic full-mesh peer derivation from remote-domain gateway groups in `generators/generate_avd_device_hostvar.py`
- [X] T041 [US3] Implement validation for malformed remote peer candidates, same local and remote domain IDs in the same Fabric, and unsupported remote-domain models in `generators/generate_avd_device_hostvar.py`
- [X] T042 [US3] Ensure structured-config peer resolution failures surface actionable errors for missing hostname-only peer facts in `generators/generate_avd_device_structured_config.py`
- [X] T043 [US3] Run focused US3 tests for `tests/unit/test_generate_avd_device_hostvar.py` and `tests/unit/test_generate_avd_device_structured_config.py`

**Checkpoint**: Remote-domain membership is the only source of gateway peer intent in this phase.

---

## Phase 6: User Story 4 - Discover Gateway Groups Through EVPN Domains (Priority: P4)

**Goal**: EVPN Services exposes a Domains tab for `EvpnDomain`, does not expose a direct Gateway Groups tab, and lets users discover gateway groups from EVPN Domain relationships.

**Independent Test**: Load schema and menu, then verify EVPN Services contains exactly one Domains item for `EvpnDomain`, no Gateways or EVPN Gateway Groups item, and no duplicate automatic entries for the new nodes.

### Tests for User Story 4

- [X] T044 [P] [US4] Add menu contract tests for one EVPN Services Domains item using `kind: EvpnDomain` in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T045 [P] [US4] Add menu contract tests that no EVPN Services item points to `EvpnGatewayGroup` or `EvpnGateway` in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T046 [P] [US4] Add schema display and order-weight tests for `EvpnDomain` and schema-valid `EvpnGatewayGroup` HFID/display without denormalized local-domain helper attributes in `tests/unit/test_evpn_gateway_schema_contract.py`

### Implementation for User Story 4

- [X] T047 [US4] Add the EVPN Services Domains menu item for `EvpnDomain` and remove any direct gateway or gateway-group item from `menus/menu.yml`
- [X] T048 [US4] Verify `EvpnDomain` and `EvpnGatewayGroup` both set `include_in_menu: false` and schema-valid display metadata in `schemas/evpn/evpn_gateway.yml`
- [X] T049 [US4] Update supported-capability documentation for EVPN Domain and Gateway Group scope in `docs/docs/supported-capabilities.md`
- [X] T050 [US4] Update schema documentation for `EvpnDomain`, `EvpnGatewayGroup`, domain-first navigation, relationships, uniqueness, and exclusions in `docs/docs/developer-guide/schemas.md`
- [X] T051 [US4] Run focused US4 tests for `tests/unit/test_evpn_gateway_menu_contract.py` and `tests/unit/test_evpn_gateway_schema_contract.py`

**Checkpoint**: Operators start from EVPN Domains and discover gateway groups through domain relationships.

---

## Phase 7: User Story 5 - Scope All-Active Settings to the Selected Resiliency Model (Priority: P5)

**Goal**: All-active multihoming and Ethernet Segment settings are visible and applicable only for the supported all-active resiliency model, or clearly marked as not applicable if conditional visibility is unavailable.

**Independent Test**: Review an EVPN Gateway Group with `all_active_multihoming` selected and confirm all-active fields are available, required as applicable, documented, and validated.

### Tests for User Story 5

- [X] T052 [P] [US5] Add schema contract tests that all-active fields are required or clearly described for `all_active_multihoming` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T053 [P] [US5] Add generator-side validation tests for missing all-active Ethernet Segment identifier and RT import values in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T054 [P] [US5] Add pyAVD contract tests for `all_active_multihoming.evpn_ethernet_segment.identifier` and `rt_import` output in `tests/unit/test_generate_avd_device_hostvar.py`

### Implementation for User Story 5

- [X] T055 [US5] Ensure all-active field labels, descriptions, requirements, defaults, and resiliency applicability are clear in `schemas/evpn/evpn_gateway.yml`
- [X] T056 [US5] Regenerate protocol classes from final schema state in `schemas/` into `src/solution_arista_avd/protocols.py`
- [X] T057 [US5] Ensure generator validation rejects missing all-active Ethernet Segment values before writing hostvars in `generators/generate_avd_device_hostvar.py`
- [X] T058 [US5] Update hostvar documentation for all-active EVPN Gateway payloads and deprecated pyAVD key exclusions in `docs/docs/developer-guide/avd/hostvars.md`
- [X] T059 [US5] Update role-mapping documentation for `border_leaf` gateway eligibility in `docs/docs/developer-guide/avd/role-mapping.md`
- [X] T060 [US5] Run focused US5 tests for `tests/unit/test_evpn_gateway_schema_contract.py` and `tests/unit/test_generate_avd_device_hostvar.py`

**Checkpoint**: All-active configuration is explicit, validatable, and not confused with unsupported resiliency models.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Repository-wide validation, generated-file checks, documentation validation, and required project gates.

- [X] T061 [P] Run full unit coverage with `uv run pytest tests/unit` for `tests/unit/`
- [X] T062 [P] Run repository lint with `uv run invoke lint` for `.`
- [X] T063 Run branch-first schema, repository, menu, hostvar generation, and structured-config scenarios from `specs/004-evpn-gateway/quickstart.md`
- [ ] T064 Run required Infrahub integration validation with `$infrahub-run-integration-tests` for changes in `schemas/`, `generators/`, `menus/`, `src/solution_arista_avd/`, and `tests/`
- [ ] T065 Run required generator idempotence validation with `$infrahub-test-generator-idempotence` for `generators/generate_avd_device_hostvar.py` and `generators/avd_device_hostvar.gql`
- [X] T066 [P] Run docs typecheck from `docs/` using `npm run typecheck` for `docs/docs/`
- [X] T067 [P] Run docs build from `docs/` using `npm run build` for `docs/docs/`
- [X] T068 Update implementation evidence and validation notes in `specs/004-evpn-gateway/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and is the MVP.
- **User Story 2 (Phase 4)**: Depends on US1 schema surfaces and protocol regeneration.
- **User Story 3 (Phase 5)**: Depends on US2 gateway-group query and generator surfaces.
- **User Story 4 (Phase 6)**: Depends on US1 and US2 schema kinds; can run in parallel with US3 after schema tasks complete.
- **User Story 5 (Phase 7)**: Depends on US2 gateway-group all-active fields; can run in parallel with US3 and US4 after T026.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; no dependency on other stories.
- **US2 (P2)**: Depends on US1 domain model and generated protocol classes.
- **US3 (P3)**: Depends on US2 gateway-group model and query surfaces.
- **US4 (P4)**: Depends on the `EvpnDomain` and `EvpnGatewayGroup` schema kinds from US1 and US2.
- **US5 (P5)**: Depends on the `EvpnGatewayGroup` all-active attributes from US2.

### Within Each User Story

- Write tests before implementation and verify they fail for missing behavior.
- Schema changes precede protocol regeneration.
- GraphQL query changes precede query-model regeneration.
- Generated files are regenerated rather than hand-edited.
- Generator logic must remain deterministic and must validate pyAVD payloads before writing `AvdHostvarFile`.
- Story checkpoints should pass before moving to the next priority when implementing sequentially.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001.
- T006, T007, T008, and T009 can run in parallel after setup.
- US1 test tasks T010 through T013 can run in parallel.
- US2 test tasks T019 through T025 can run in parallel.
- US3 test tasks T034 through T037 can run in parallel.
- US4 test tasks T044 through T046 can run in parallel.
- US5 test tasks T052 through T054 can run in parallel.
- Documentation tasks T049, T050, T058, and T059 can run in parallel after their schema and generator contracts are stable.
- Polish validation tasks marked [P] can run in parallel when they do not share generated outputs.

---

## Parallel Example: User Story 1

```bash
Task: "Add schema contract tests for `EvpnDomain` node kind, required `name` and `domain_id`, Fabric ownership, `include_in_menu: false`, and no `EvpnGateway` node in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for additive `NetworkFabric.evpn_domains`, optional `NetworkPod.evpn_domain`, and inverse `EvpnDomain.pods` relationships in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for `EvpnDomain` uniqueness by `[fabric, name__value]` and `[fabric, domain_id__value]` in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add migration-safety tests that existing Fabric and Pod schema extensions remain optional in `tests/unit/test_evpn_gateway_schema_contract.py`"
```

## Parallel Example: User Story 2

```bash
Task: "Add schema contract tests for `EvpnGatewayGroup` attributes, all-active-only `resiliency_model`, Pod parent, remote-domain relationship, member relationship, inverse device membership cardinality, and `[pod, name__value]` uniqueness in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests that all new bidirectional relationships use matching `identifier` values and relationship `peer` values use full schema kinds in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add hostvar tests for grouped `border_leaf` devices receiving shared EVPN L2/L3, D-PATH, resiliency, and Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add generator-side validation tests for non-`border_leaf` members, cross-Pod members, missing Pod EVPN Domain, empty members, same local and remote domain, unsupported resiliency, and missing Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`"
```

## Parallel Example: User Story 3

```bash
Task: "Add hostvar tests for full-mesh peer derivation across gateway groups sharing one remote EVPN Domain in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add hostvar tests for deterministic peer hostname ordering, target self-exclusion, same-local-domain exclusion or rejection, and singleton remote-domain empty peer lists in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add a pyAVD smoke test for two generated gateway hostvar files with hostname-only remote peers using `get_avd_facts()` and `get_device_structured_config()` in `tests/unit/test_generate_avd_device_hostvar.py`"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 through T018.
3. Stop and validate US1 independently with schema contract tests and schema validation.
4. Use the MVP to prove domain membership is modeled without a dedicated `EvpnGateway` node.

### Incremental Delivery

1. Add the EVPN Domain schema model and additive Fabric/Pod extensions.
2. Add the EVPN Gateway Group schema model and per-device hostvar activation.
3. Add full-mesh remote-domain peer derivation.
4. Add domain-first EVPN Services menu exposure.
5. Finalize all-active applicability, docs, and required validation gates.

### Parallel Team Strategy

1. Complete Setup and Foundational tasks together.
2. Implement US1 schema and generated type surfaces first.
3. After T026 stabilizes the gateway group schema, one implementer can continue hostvar work while another starts US4 menu/docs and a third starts US5 all-active tests/docs.
4. After T038 and T039 update the remote-domain query surfaces, US3 peer derivation can proceed independently from menu and docs work.

---

## Notes

- Use `infrahub-managing-schemas` for T014-T017, T019-T021, T026-T027, T046, T048, T052, T055, and T056.
- Use `avd-skill` for pyAVD EVPN Gateway field validation in T025, T031, T037, T054, and T057-T058.
- Use `infrahub-managing-generators` for T028-T032, T038-T043, and T057.
- Use `infrahub-managing-menus` for T044-T045 and T047.
- Use `$infrahub-run-integration-tests` for T064.
- Use `$infrahub-test-generator-idempotence` for T065.

## Phase 9: Convergence

- [ ] T069 CRITICAL: Run required Infrahub integration validation against an exact committed branch and commit, then record the tested branch/commit evidence per Constitution IV (partial)
- [ ] T070 CRITICAL: Run required generator idempotence validation for `generate-avd-device-hostvar` changes, or document the approved alternative when live validation is not allowed, per Constitution II / IV (missing)
- [X] T071 Execute the branch-first quickstart schema, repository, menu, hostvar-generation, and structured-config acceptance scenarios, creating concrete validation objects or targets as needed, per plan: Testing (partial)
