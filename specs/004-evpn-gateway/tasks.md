# Tasks: EVPN Gateway Domains

**Input**: Design documents from `/specs/004-evpn-gateway/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md, contracts/

**Tests**: Tests are included because the feature specification, contracts, quickstart, and constitution require schema, generator-side validation, hostvar, pyAVD, menu, lint, integration, and generator idempotence validation.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested as an independent increment.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm prerequisite role support, stale gateway assumptions, and generation paths before implementing the domain-owned gateway group model.

- [X] T001 Verify the `border_leaf` dependency from PR #74 is present in `schemas/dcim_extensions.yml`, `src/solution_arista_avd/avd.py`, and `tests/unit/test_avd.py`
- [X] T002 [P] Review existing EVPN schema conventions in `schemas/evpn/evpn_services.yml` and `schemas/evpn/evpn_gateway.yml`
- [X] T003 [P] Review existing hostvar generator structure in `generators/avd_device_hostvar.gql`, `generators/generate_avd_device_hostvar.py`, and `generators/generate_avd_device_inputs_query.py`
- [X] T004 [P] Review existing structured-config hostvar aggregation in `generators/generate_avd_device_structured_config.py`
- [X] T005 [P] Review existing EVPN Services menu placement in `menus/menu.yml`
- [X] T006 [P] Identify stale Pod-owned or Pod-derived gateway group assumptions in `schemas/evpn/evpn_gateway.yml`, `generators/`, `tests/unit/`, and `docs/docs/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Prepare shared contract tests, fixtures, and generated-file guardrails needed by every story.

**Critical**: No user story work can be considered complete until these shared prerequisites are satisfied.

- [X] T007 [P] Add or reset EVPN Gateway schema contract test helpers in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T008 [P] Add or reset EVPN Gateway menu contract test helpers in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T009 [P] Add or reset EVPN Gateway hostvar fixture helpers in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T010 [P] Add or reset EVPN Gateway structured-config peer-resolution fixtures in `tests/unit/test_generate_avd_device_structured_config.py`
- [X] T011 [P] Add or reset EVPN Gateway hostvar ordering coverage in `tests/unit/test_hostvar_ordering.py`
- [X] T012 Document generated-file regeneration commands for `src/solution_arista_avd/protocols.py` and `generators/generate_avd_device_inputs_query.py` in `specs/004-evpn-gateway/quickstart.md`

**Checkpoint**: Shared test locations exist and no user story depends on undefined test scaffolding.

---

## Phase 3: User Story 1 - Model EVPN Domains Across a Fabric (Priority: P1) MVP

**Goal**: A Fabric owns zero or more EVPN Domains, each Pod belongs to zero or one EVPN Domain, and no dedicated `EvpnGateway` node exists.

**Independent Test**: Load the schema for a Fabric with no EVPN Domains, then with multiple EVPN Domains and Pods assigned to only one domain each; verify duplicate domain IDs or names within a Fabric are rejected or reported.

### Tests for User Story 1

- [X] T013 [P] [US1] Add schema contract tests for `EvpnDomain` kind, required `name` and `domain_id`, Fabric parent relationship, and `include_in_menu: false` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T014 [P] [US1] Add schema contract tests that `EvpnGateway` is not defined and no `DcimDevice.evpn_gateway` relationship exists in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T015 [P] [US1] Add schema contract tests for additive `NetworkFabric.evpn_domains`, optional `NetworkPod.evpn_domain`, and inverse `EvpnDomain.pods` relationships in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T016 [P] [US1] Add schema contract tests for `EvpnDomain` uniqueness by `[fabric, name__value]` and `[fabric, domain_id__value]` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T017 [P] [US1] Add migration-safety tests that existing Fabric and Pod extensions remain optional in `tests/unit/test_evpn_gateway_schema_contract.py`

### Implementation for User Story 1

- [X] T018 [US1] Replace stale per-device gateway schema with `EvpnDomain` and Fabric/Pod relationship extensions in `schemas/evpn/evpn_gateway.yml`
- [X] T019 [US1] Remove concrete `EvpnGateway` node, `DcimDevice.evpn_gateway`, and local-domain helper schema surfaces from `schemas/evpn/evpn_gateway.yml`
- [X] T020 [US1] Regenerate protocol classes from `schemas/` into `src/solution_arista_avd/protocols.py`
- [X] T021 [US1] Validate the schema changes with `uv run infrahubctl schema check schemas/ --branch evpn-gateway-validation` against `schemas/`
- [X] T022 [US1] Run focused US1 tests with `uv run pytest tests/unit/test_evpn_gateway_schema_contract.py` for `tests/unit/test_evpn_gateway_schema_contract.py`

**Checkpoint**: Domain membership is schema-modeled independently and existing non-gateway Fabrics and Pods remain valid.

---

## Phase 4: User Story 2 - Own Gateway Groups From Local Domains (Priority: P2)

**Goal**: Each `EvpnDomain` owns local `EvpnGatewayGroup` children through `EvpnGatewayGroup.local_domain`, while `pod` remains required non-owning context.

**Independent Test**: Model one EVPN Domain with two local EVPN Gateway Group children. Confirm each group has that EVPN Domain as parent `local_domain`, each group selects a Pod as context, and no group is owned by a Pod.

### Tests for User Story 2

- [X] T023 [P] [US2] Add schema contract tests for `EvpnDomain.local_gateway_groups` as Component inverse of `EvpnGatewayGroup.local_domain` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T024 [P] [US2] Add schema contract tests for `EvpnGatewayGroup.local_domain` as the required cardinality-one Parent relationship to `EvpnDomain` in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T025 [P] [US2] Add schema contract tests that `EvpnGatewayGroup.pod` is a required Attribute relationship and `NetworkPod.evpn_gateway_groups` is non-owning in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T026 [P] [US2] Add schema contract tests for `EvpnGatewayGroup` attributes, all-active-only `resiliency_model`, required `members`, and `[local_domain, pod, name__value]` uniqueness in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T027 [P] [US2] Add schema contract tests that `EvpnGatewayGroup` display/HFID uses native `local_domain`, `pod`, `remote_domain`, and `name` fields without denormalized local-domain helper attributes in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T028 [P] [US2] Add schema contract tests that relationship identifiers match and all peers use full schema kinds in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T085 [P] [US2] Add schema contract tests that `EvpnDomain` and `EvpnGatewayGroup` attribute and relationship order weights place Fabric, domain, group, Pod, members, resiliency, and Ethernet Segment fields consistently with existing EVPN service schemas in `tests/unit/test_evpn_gateway_schema_contract.py`

### Implementation for User Story 2

- [X] T029 [US2] Implement `EvpnGatewayGroup.local_domain` parent ownership and `EvpnDomain.local_gateway_groups` component inverse in `schemas/evpn/evpn_gateway.yml`
- [X] T030 [US2] Implement `EvpnGatewayGroup.pod` as a required Attribute relationship and `NetworkPod.evpn_gateway_groups` as a non-owning inverse in `schemas/evpn/evpn_gateway.yml`
- [X] T031 [US2] Implement `EvpnGatewayGroup.remote_domain`, `members`, all gateway attributes, all-active-only dropdown choices, display metadata, and uniqueness in `schemas/evpn/evpn_gateway.yml`
- [X] T086 [US2] Verify and adjust `schemas/evpn/evpn_gateway.yml` order weights for EVPN Domain and Gateway Group fields to satisfy FR-048
- [X] T032 [US2] Regenerate protocol classes from the gateway group schema state into `src/solution_arista_avd/protocols.py`
- [X] T033 [US2] Run focused US2 schema tests with `uv run pytest tests/unit/test_evpn_gateway_schema_contract.py` for `tests/unit/test_evpn_gateway_schema_contract.py`

**Checkpoint**: Gateway groups are owned by local EVPN Domains, and Pods are selected context rather than parents.

---

## Phase 5: User Story 3 - Validate Gateway Pod and Domain Consistency (Priority: P3)

**Goal**: The hostvar generator rejects gateway intent when the selected Pod has no EVPN Domain or a different EVPN Domain than the group parent `local_domain`.

**Independent Test**: Model a Pod assigned to EVPN Domain A. Create a gateway group under Domain A with that Pod and confirm it is valid. Attempt to use the same Pod under Domain B and confirm the invalid relationship is rejected before gateway hostvars are accepted.

### Tests for User Story 3

- [X] T034 [P] [US3] Add hostvar query contract tests that generated models expose `evpn_gateway_group.local_domain`, `evpn_gateway_group.pod.evpn_domain`, `remote_domain`, and `members` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T035 [P] [US3] Add successful hostvar tests where `EvpnGatewayGroup.local_domain` matches `EvpnGatewayGroup.pod.evpn_domain` in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T036 [P] [US3] Add generator validation tests for missing `local_domain`, missing selected `pod`, selected Pod without `evpn_domain`, and Pod/local-domain mismatch in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T037 [P] [US3] Add generator validation tests for non-`border_leaf` target, non-`border_leaf` member, cross-Pod member, empty member list, unsupported resiliency, and missing Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T038 [P] [US3] Add pyAVD validation and deprecated-key assertions for generated EVPN Gateway payloads in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T039 [P] [US3] Add ordering assertions for `l3leaf.nodes[].evpn_gateway` in `tests/unit/test_hostvar_ordering.py`

### Implementation for User Story 3

- [X] T040 [US3] Update `generators/avd_device_hostvar.gql` to fetch the target device `evpn_gateway_group.local_domain`, selected `pod`, Pod `evpn_domain`, `remote_domain`, `members`, and gateway attributes
- [X] T041 [US3] Regenerate `generators/generate_avd_device_inputs_query.py` from `generators/avd_device_hostvar.gql`
- [X] T042 [US3] Implement local-domain extraction from `EvpnGatewayGroup.local_domain` in `generators/generate_avd_device_hostvar.py`
- [X] T043 [US3] Implement generator-side validation for Pod/local-domain consistency, member role, member Pod, resiliency, and required all-active values in `generators/generate_avd_device_hostvar.py`
- [X] T044 [US3] Emit EVPN Gateway hostvars only for valid grouped `border_leaf` devices and omit gateway payloads for ungrouped or non-gateway devices in `generators/generate_avd_device_hostvar.py`
- [X] T045 [US3] Call `pyavd.validate_inputs()` before writing `AvdHostvarFile` in `generators/generate_avd_device_hostvar.py`
- [X] T046 [US3] Preserve deterministic hostvar ordering for gateway payload keys in `generators/generate_avd_device_hostvar.py`
- [X] T047 [US3] Run focused US3 tests with `uv run pytest tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py` for `tests/unit/test_generate_avd_device_hostvar.py`

**Checkpoint**: Gateway-specific hostvars are written only when the selected Pod belongs to the group's parent local EVPN Domain.

---

## Phase 6: User Story 4 - Keep Remote Domains Separate and Derive Peers (Priority: P4)

**Goal**: The remote domain remains a distinct relationship, local and remote domains cannot be the same, and remote peers derive deterministically from gateway groups sharing the selected remote domain.

**Independent Test**: Create a gateway group under local Domain A with remote Domain B and confirm it is valid. Select Domain A as remote and confirm validation reports the conflict. Model multiple valid groups sharing remote Domain B and confirm peer intent derives from that shared remote domain.

### Tests for User Story 4

- [X] T048 [P] [US4] Add schema contract tests for `EvpnGatewayGroup.remote_domain` and `EvpnDomain.remote_gateway_groups` relationship semantics in `tests/unit/test_evpn_gateway_schema_contract.py`
- [X] T049 [P] [US4] Add generator validation tests for missing remote domain, same local and remote domain object, and same local/remote `domain_id` in the same Fabric in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T050 [P] [US4] Add hostvar tests for full-mesh peer derivation from `remote_domain.remote_gateway_groups`, excluding members of the target device's own `EvpnGatewayGroup`, in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T051 [P] [US4] Add hostvar tests for deterministic peer hostname ordering, target self-exclusion, same-group peer exclusion, singleton remote-domain empty peer lists, and malformed peer candidates in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T052 [P] [US4] Add tests that route-server, route-reflector, manually modeled peer objects, peer IP fields, and peer BGP ASN fields are not accepted in `tests/unit/test_generate_avd_device_hostvar.py`
- [X] T053 [P] [US4] Add structured-config pyAVD smoke tests for hostname-only remote peers with `get_avd_facts()` and `get_device_structured_config()` in `tests/unit/test_generate_avd_device_structured_config.py`

### Implementation for User Story 4

- [X] T054 [US4] Extend `generators/avd_device_hostvar.gql` with `remote_domain.remote_gateway_groups.local_domain`, selected Pod, Pod domain, and member traversal for peer candidates
- [X] T055 [US4] Regenerate `generators/generate_avd_device_inputs_query.py` from the remote-domain traversal in `generators/avd_device_hostvar.gql`
- [X] T056 [US4] Implement validation that `remote_domain` is present, differs from `local_domain`, and does not reuse the same `domain_id` in the same Fabric in `generators/generate_avd_device_hostvar.py`
- [X] T057 [US4] Implement deterministic full-mesh peer derivation from valid gateway groups sharing `remote_domain`, excluding the target device's own `EvpnGatewayGroup`, in `generators/generate_avd_device_hostvar.py`
- [X] T058 [US4] Ensure structured-config peer resolution failures surface actionable errors for missing hostname-only peer facts in `generators/generate_avd_device_structured_config.py`
- [X] T059 [US4] Run focused US4 tests with `uv run pytest tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_generate_avd_device_structured_config.py` for `tests/unit/test_generate_avd_device_structured_config.py`

**Checkpoint**: Remote-domain membership is the only source of gateway peer intent in this phase.

---

## Phase 7: User Story 5 - Align Generated Data, Navigation, and Evidence (Priority: P5)

**Goal**: Generated model surfaces, gateway validation, menu navigation, documentation, quickstart steps, tests, and evidence all reflect domain-owned local gateway groups.

**Independent Test**: Review generated type surfaces, hostvar data retrieval, validation behavior, domain relationship documentation, quickstart evidence, and tests. Confirm each refers to `local_domain` parent ownership and no longer treats `pod` as the group parent.

### Tests for User Story 5

- [X] T060 [P] [US5] Add menu contract tests for one EVPN Services Domains item using `kind: EvpnDomain` in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T061 [P] [US5] Add menu contract tests that no EVPN Services item points to `EvpnGatewayGroup` or `EvpnGateway` in `tests/unit/test_evpn_gateway_menu_contract.py`
- [X] T062 [P] [US5] Add documentation wording assertions for domain-owned gateway text in `tests/unit/test_evpn_gateway_docs_contract.py`
- [X] T063 [P] [US5] Add schema/query regression tests that `src/solution_arista_avd/protocols.py` and `generators/generate_avd_device_inputs_query.py` expose `local_domain` parent semantics in `tests/unit/test_evpn_gateway_schema_contract.py`

### Implementation for User Story 5

- [X] T064 [US5] Add or keep the EVPN Services Domains menu item for `EvpnDomain` and remove direct gateway or gateway-group menu items from `menus/menu.yml`
- [X] T065 [US5] Verify `EvpnDomain` and `EvpnGatewayGroup` both set `include_in_menu: false` and schema-valid display metadata in `schemas/evpn/evpn_gateway.yml`
- [X] T066 [US5] Update supported-capability documentation for domain-owned EVPN Gateway Group scope in `docs/docs/supported-capabilities.md`
- [X] T067 [US5] Update schema documentation for `EvpnDomain.local_gateway_groups`, `EvpnGatewayGroup.local_domain`, `EvpnGatewayGroup.pod`, `remote_domain`, uniqueness, navigation, and exclusions in `docs/docs/developer-guide/schemas.md`
- [X] T068 [US5] Update hostvar documentation to derive local D-PATH IDs from `EvpnGatewayGroup.local_domain` in `docs/docs/developer-guide/avd/hostvars.md`
- [X] T069 [US5] Update role-mapping documentation for `border_leaf` gateway eligibility in `docs/docs/developer-guide/avd/role-mapping.md`
- [X] T070 [US5] Update generator documentation for domain-owned gateway group query and validation behavior in `docs/docs/developer-guide/generators.md`
- [X] T071 [US5] Update quickstart positive and negative scenarios for local-domain parent ownership, Pod/local mismatch, same local/remote domain, and validation evidence in `specs/004-evpn-gateway/quickstart.md`
- [X] T072 [US5] Run focused US5 tests with `uv run pytest tests/unit/test_evpn_gateway_menu_contract.py tests/unit/test_evpn_gateway_schema_contract.py` for `tests/unit/test_evpn_gateway_menu_contract.py`

**Checkpoint**: Review surfaces and operator documentation consistently describe EVPN Domain-owned local gateway groups.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Repository-wide validation, generated-file checks, documentation validation, and required project gates.

- [X] T073 [P] Run full unit coverage with `uv run pytest tests/unit` for `tests/unit/`
- [X] T074 [P] Run repository lint with `uv run invoke lint` for `.`
- [X] T075 Run branch-first schema check/load, repository load, menu load, hostvar generation, and structured-config scenarios from `specs/004-evpn-gateway/quickstart.md`
- [X] T078 [P] Run docs typecheck from `docs/` using `npm run typecheck` for `docs/docs/`
- [X] T079 [P] Run docs build from `docs/` using `npm run build` for `docs/docs/`
- [X] T080 Update implementation evidence and validation notes in `specs/004-evpn-gateway/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and is the MVP.
- **User Story 2 (Phase 4)**: Depends on US1 schema surfaces and protocol regeneration.
- **User Story 3 (Phase 5)**: Depends on US2 gateway group schema surfaces.
- **User Story 4 (Phase 6)**: Depends on US2 schema and US3 hostvar query/model surfaces.
- **User Story 5 (Phase 7)**: Depends on US1 through US4 surfaces for accurate docs, menu, and evidence.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2; no dependency on other stories.
- **US2 (P2)**: Depends on US1 domain model and generated protocol classes.
- **US3 (P3)**: Depends on US2 domain-owned gateway group schema.
- **US4 (P4)**: Depends on US2 gateway group model and US3 query/model updates.
- **US5 (P5)**: Depends on US1 through US4 to avoid documenting stale relationship semantics.

### Within Each User Story

- Write tests before implementation and verify they fail for missing behavior.
- Schema changes precede protocol regeneration.
- GraphQL query changes precede query-model regeneration.
- Generated files are regenerated rather than hand-edited.
- Generator logic must remain deterministic and must validate pyAVD payloads before writing `AvdHostvarFile`.
- Story checkpoints should pass before moving to the next priority when implementing sequentially.

### Parallel Opportunities

- T002, T003, T004, T005, and T006 can run in parallel after T001.
- T007, T008, T009, T010, and T011 can run in parallel after setup.
- US1 test tasks T013 through T017 can run in parallel.
- US2 test tasks T023 through T028 and T085 can run in parallel.
- US3 test tasks T034 through T039 can run in parallel.
- US4 test tasks T048 through T053 can run in parallel.
- US5 test tasks T060 through T063 can run in parallel.
- Documentation tasks T066 through T071 can run in parallel after their schema and generator contracts are stable.
- Polish validation tasks marked [P] can run in parallel when they do not share generated outputs.

---

## Parallel Example: User Story 1

```bash
Task: "Add schema contract tests for `EvpnDomain` kind, required `name` and `domain_id`, Fabric parent relationship, and `include_in_menu: false` in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests that `EvpnGateway` is not defined and no `DcimDevice.evpn_gateway` relationship exists in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for additive `NetworkFabric.evpn_domains`, optional `NetworkPod.evpn_domain`, and inverse `EvpnDomain.pods` relationships in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for `EvpnDomain` uniqueness by `[fabric, name__value]` and `[fabric, domain_id__value]` in `tests/unit/test_evpn_gateway_schema_contract.py`"
```

## Parallel Example: User Story 2

```bash
Task: "Add schema contract tests for `EvpnDomain.local_gateway_groups` as Component inverse of `EvpnGatewayGroup.local_domain` in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for `EvpnGatewayGroup.local_domain` as the required cardinality-one Parent relationship to `EvpnDomain` in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests that `EvpnGatewayGroup.pod` is a required Attribute relationship and `NetworkPod.evpn_gateway_groups` is non-owning in `tests/unit/test_evpn_gateway_schema_contract.py`"
Task: "Add schema contract tests for `EvpnGatewayGroup` attributes, all-active-only `resiliency_model`, required `members`, and `[local_domain, pod, name__value]` uniqueness in `tests/unit/test_evpn_gateway_schema_contract.py`"
```

## Parallel Example: User Story 3

```bash
Task: "Add successful hostvar tests where `EvpnGatewayGroup.local_domain` matches `EvpnGatewayGroup.pod.evpn_domain` in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add generator validation tests for missing `local_domain`, missing selected `pod`, selected Pod without `evpn_domain`, and Pod/local-domain mismatch in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add generator validation tests for non-`border_leaf` target, non-`border_leaf` member, cross-Pod member, empty member list, unsupported resiliency, and missing Ethernet Segment values in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add ordering assertions for `l3leaf.nodes[].evpn_gateway` in `tests/unit/test_hostvar_ordering.py`"
```

## Parallel Example: User Story 4

```bash
Task: "Add generator validation tests for missing remote domain, same local and remote domain object, and same local/remote `domain_id` in the same Fabric in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add hostvar tests for full-mesh peer derivation from `remote_domain.remote_gateway_groups` in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add hostvar tests for deterministic peer hostname ordering, target self-exclusion, singleton remote-domain empty peer lists, and malformed peer candidates in `tests/unit/test_generate_avd_device_hostvar.py`"
Task: "Add structured-config pyAVD smoke tests for hostname-only remote peers with `get_avd_facts()` and `get_device_structured_config()` in `tests/unit/test_generate_avd_device_structured_config.py`"
```

## Parallel Example: User Story 5

```bash
Task: "Add menu contract tests for one EVPN Services Domains item using `kind: EvpnDomain` in `tests/unit/test_evpn_gateway_menu_contract.py`"
Task: "Add menu contract tests that no EVPN Services item points to `EvpnGatewayGroup` or `EvpnGateway` in `tests/unit/test_evpn_gateway_menu_contract.py`"
Task: "Add documentation wording assertions for domain-owned gateway text in `tests/unit/test_evpn_gateway_docs_contract.py`"
Task: "Add schema/query regression tests that `src/solution_arista_avd/protocols.py` and `generators/generate_avd_device_inputs_query.py` expose `local_domain` parent semantics in `tests/unit/test_evpn_gateway_schema_contract.py`"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 through T022.
3. Stop and validate US1 independently with schema contract tests and schema validation.
4. Use the MVP to prove domain membership is modeled without a dedicated `EvpnGateway` node.

### Incremental Delivery

1. Add the EVPN Domain schema model and additive Fabric/Pod extensions.
2. Add domain-owned EVPN Gateway Group schema and generated protocol surfaces.
3. Add hostvar local-domain validation and valid grouped Border Leaf gateway output.
4. Add remote-domain conflict validation and full-mesh peer derivation.
5. Align menu, documentation, quickstart evidence, and required validation gates.

### Parallel Team Strategy

1. Complete Setup and Foundational tasks together.
2. Implement US1 schema and generated type surfaces first.
3. After T031 stabilizes the gateway group schema, one implementer can continue hostvar work while another starts menu/docs tasks.
4. After T054 and T055 update the remote-domain query surfaces, peer derivation can proceed independently from documentation and evidence work.

---

## Notes

- Use `infrahub-managing-schemas` for T018-T021, T023-T033, T063, T065, T085, and T086.
- Use `avd-skill` for pyAVD EVPN Gateway field validation in T038, T045, T053, T056-T058, and T068.
- Use `infrahub-managing-generators` for T034-T047 and T049-T059.
- Use `infrahub-managing-menus` for T060-T061 and T064.
- Use `$infrahub-run-integration-tests` for T081.
- Use `$infrahub-test-generator-idempotence` for T082.

## Phase 9: Convergence

- [X] T081 CRITICAL: Run required Infrahub integration validation with `$infrahub-run-integration-tests` and record tested branch and commit per Constitution IV
- [X] T082 CRITICAL: Run required generator idempotence validation with `$infrahub-test-generator-idempotence`, or record the approved non-live exception and alternative repeated-run evidence, per Constitution II
- [X] T083 Complete and record the missing branch-first quickstart repository load, positive/negative object scenarios, hostvar generation, and structured-config peer-resolution evidence per SC-013 (partial)
- [X] T084 Update `spec.md`, `schemas/evpn/evpn_gateway.yml`, schema contract tests, and quickstart evidence so the accepted Infrahub HFID limitation is documented and reviewer navigation distinguishes `local_domain` through EVPN Domain relationship views while preserving Pod, remote domain, and group name in gateway group identity/display metadata
