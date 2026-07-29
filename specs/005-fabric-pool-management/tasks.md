# Tasks: Fabric Pool Management

**Input**: Design documents from `/specs/005-fabric-pool-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/fabric-pool-schema-contract.md, quickstart.md, constitution.md

**Tests**: Required. The feature specification requires schema contract tests, active proposed-change validation, generator behavior, object compatibility, and full validation gates.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after the shared foundation is in place.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the implementation agent with the required Infrahub artifact guidance and existing local patterns.

- [X] T001 Review schema implementation guidance in .agents/skills/infrahub-managing-schemas/SKILL.md
- [X] T002 [P] Review proposed-change check guidance in .agents/skills/infrahub-managing-checks/SKILL.md
- [X] T003 [P] Review generator implementation guidance in .agents/skills/infrahub-managing-generators/SKILL.md
- [X] T004 [P] Review schema relationship and dropdown patterns in schemas/ipam_extensions.yml, schemas/logical_design.yml, schemas/l3ls_extensions.yml, and schemas/dci.yml
- [X] T005 [P] Review existing check registration and implementation patterns in .infrahub.yml, checks/cv_config_check.py, and checks/cv_config_check.gql
- [X] T006 [P] Review existing pool consumption in src/solution_arista_avd/generator.py and generators/generate_avd_device_hostvar.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared tests, constants, and validation scaffolding used by all pool-management stories.

**Critical**: No user story work should begin until this phase is complete because every story depends on the shared role model and validation surface.

- [X] T007 Create shared YAML-loading helpers for fabric pool schema assertions in tests/unit/test_fabric_pool_schema_contract.py
- [X] T008 Add failing contract assertions that no replacement NetworkFabric or NetworkPod node is introduced in tests/unit/test_fabric_pool_schema_contract.py
- [X] T009 Add failing contract assertions for retained legacy IpamPrefix.role choices in tests/unit/test_fabric_pool_schema_contract.py
- [X] T010 [P] Add failing role-mapping, role-homogeneity, and non-fabric-role rejection unit tests in tests/unit/test_pool_roles.py
- [X] T011 Implement shared pool role constants, role aliases, required-role dataclasses, and resource-role helpers in src/solution_arista_avd/pool_roles.py
- [X] T012 Add the fabric_pool_check GraphQL query skeleton in checks/fabric_pool_check.gql
- [X] T013 Add the FabricPoolValidationCheck class skeleton in checks/fabric_pool_check.py
- [X] T014 Register the fabric_pool_check query and fabric-pool-validation check definition in .infrahub.yml
- [X] T015 Run foundational role tests with uv run pytest tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_schema_contract.py

**Checkpoint**: Shared role constants, schema-test scaffolding, and check registration exist for story-specific implementation.

---

## Phase 3: User Story 1 - Manage Fabric Pools Through One Role-Driven Collection (Priority: P1) MVP

**Goal**: NetworkFabric exposes one many-valued fabric IP pool collection, required fabric pool purposes resolve from prefix roles, invalid fabric collections are actively rejected, and generators consume the new collection with legacy fallback during migration.

**Independent Test**: Load or model a fabric with management, overlay, underlay, DCI, and Fabric Supernet pool roles in fabric_ip_pools; confirm required fabric roles resolve without legacy fields, duplicate or mixed-role pools fail validation, and hostvars/generators still work while legacy relationships remain populated.

### Tests for User Story 1

- [X] T016 [P] [US1] Add failing contract assertions for IpamPrefix.role new fabric role choices in tests/unit/test_fabric_pool_schema_contract.py
- [X] T017 [P] [US1] Add failing contract assertions for NetworkFabric.fabric_ip_pools relationship shape and pool/prefix display labels in tests/unit/test_fabric_pool_schema_contract.py
- [X] T018 [P] [US1] Add failing fabric required-role, duplicate-role, mixed-role, and Fabric Supernet fallback tests in tests/unit/test_pool_roles.py
- [X] T019 [P] [US1] Add failing proposed-change check tests for missing, duplicate, mixed-role, non-IP, and Fabric Supernet fabric pool errors in tests/unit/test_fabric_pool_check.py
- [X] T020 [P] [US1] Add failing generator tests for resolving management, loopback, Loopback VTEP, and Fabric Point-to-Point pools from fabric_ip_pools in tests/unit/test_l3ls_pools.py
- [X] T021 [P] [US1] Add failing hostvar tests for resolving DCI and uplink pools from fabric_ip_pools in tests/unit/test_generate_avd_device_hostvar.py

### Implementation for User Story 1

- [X] T022 [US1] Add fabric_supernet, fabric_point_to_point, and dci role choices while retaining legacy choices and update pool/prefix display-label schema contracts in schemas/ipam_extensions.yml
- [X] T023 [US1] Update schema display labels for pool and prefix objects so operators can identify pool name, backing prefix, and role without internal IDs in schemas/ipam_extensions.yml and related pool schema definitions
- [X] T024 [US1] Add NetworkFabric.fabric_ip_pools as an optional many-valued Attribute relationship to CoreResourcePool in schemas/logical_design.yml
- [X] T025 [US1] Preserve NetworkFabric.mgmt_pool compatibility and document migration status in schemas/logical_design.yml
- [X] T026 [US1] Make NetworkFabric.uplink_pool, NetworkFabric.vtep_pool, and NetworkFabric.loopback_pool optional legacy relationships in schemas/l3ls_extensions.yml
- [X] T027 [US1] Preserve NetworkFabric.dci_pool as an optional legacy relationship and document migration status in schemas/dci.yml
- [X] T027a [US1] Run schema validation after fabric schema changes with uv run infrahubctl schema check schemas/
- [X] T027b [US1] Regenerate protocol classes after fabric schema changes in src/solution_arista_avd/protocols.py
- [X] T028 [US1] Implement fabric required-role, duplicate-role, mixed-role, non-IP, non-fabric-role rejection, and Fabric Supernet fallback logic in src/solution_arista_avd/pool_roles.py
- [X] T029 [US1] Expand fabric_pool_check query fields for fabric_ip_pools, legacy fabric pools, fabric routing attributes, and DCI NetworkLink membership in checks/fabric_pool_check.gql
- [X] T030 [US1] Implement FabricPoolValidationCheck fabric-scope validation errors in checks/fabric_pool_check.py
- [X] T031 [US1] Update generate_fabric.gql, generate_pod.gql, generate_rack.gql, and generators/avd_device_hostvar.gql to request fabric_ip_pools with pool resources and IpamPrefix.role
- [X] T032 [US1] Regenerate fabric, pod, rack, hostvar, and check query models in generators/fabric_generator_query.py, generators/pod_generator_query.py, generators/rack_generator_query.py, generators/generate_avd_device_inputs_query.py, and checks/fabric_pool_check_query.py
- [X] T033 [US1] Update GeneratorMixin.resolve_avd_pools to prefer fabric_ip_pools and fall back to legacy fabric relationships in src/solution_arista_avd/generator.py
- [X] T034 [US1] Implement deterministic Fabric Supernet allocation helpers for missing fabric prefix-pool roles in src/solution_arista_avd/generator.py
- [X] T034a [US1] Add failing generator tests that missing required fabric prefix-pool roles create or reuse persisted fallback pool objects from Fabric Supernet with stable natural keys in tests/unit/test_l3ls_pools.py
- [X] T034b [US1] Implement idempotent persisted fallback pool creation/upsert for missing fabric prefix-pool roles using `<fabric>-<role>-Pool` names in src/solution_arista_avd/generator.py
- [X] T034c [US1] Add failing generator and validation tests for Fabric Supernet exhaustion when no non-overlapping child prefix of the required size remains in tests/unit/test_l3ls_pools.py and tests/unit/test_fabric_pool_check.py
- [X] T035 [US1] Update GenerateAVDDeviceHostvar to resolve uplink and DCI pools from fabric_ip_pools with legacy fallback in generators/generate_avd_device_hostvar.py
- [X] T036 [US1] Run User Story 1 tests with uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_check.py tests/unit/test_l3ls_pools.py tests/unit/test_generate_avd_device_hostvar.py

**Checkpoint**: User Story 1 is independently testable as the MVP fabric pool collection and validation increment.

---

## Phase 4: User Story 2 - Model Pod Pools With Fabric Containment Rules (Priority: P2)

**Goal**: NetworkPod exposes one pod IP pool collection for pod-scoped Loopback, Loopback VTEP, and Fabric Point-to-Point pools; management remains fabric-scoped; pod pools must be contained by matching fabric pools.

**Independent Test**: Load or model a fabric with pod_ip_pools and confirm pod prefix pools resolve by role, management is never required at pod scope, non-contained pod prefixes fail validation, and generators prefer valid pod pools where they exist.

### Tests for User Story 2

- [X] T037 [P] [US2] Add failing contract assertions for NetworkPod.pod_ip_pools relationship shape in tests/unit/test_fabric_pool_schema_contract.py
- [X] T038 [P] [US2] Add failing pod role-resolution tests for management exclusion and allowed pod roles in tests/unit/test_pool_roles.py
- [X] T039 [P] [US2] Add failing subnet-containment tests for pod Loopback, Loopback VTEP, and Fabric Point-to-Point pools in tests/unit/test_pool_roles.py
- [X] T040 [P] [US2] Add failing proposed-change check tests for pod duplicate-role, mixed-role, non-IP, management-role, and containment errors in tests/unit/test_fabric_pool_check.py
- [X] T041 [P] [US2] Add failing generator tests for pod_ip_pools precedence over matching fabric pools in tests/unit/test_generate_pod.py and tests/unit/test_generate_rack.py

### Implementation for User Story 2

- [X] T042 [US2] Add NetworkPod.pod_ip_pools as an optional many-valued Attribute relationship to CoreResourcePool in schemas/l3ls_extensions.yml
- [X] T043 [US2] Preserve the NetworkFabric to NetworkPod to LocationRack hierarchy while extending pod relationships in schemas/logical_design.yml and schemas/l3ls_extensions.yml
- [X] T043a [US2] Run schema validation after pod schema changes with uv run infrahubctl schema check schemas/
- [X] T043b [US2] Regenerate protocol classes after pod schema changes in src/solution_arista_avd/protocols.py
- [X] T044 [US2] Implement pod allowed-role, management-exclusion, duplicate-role, mixed-role, non-fabric-role rejection, and subnet-containment logic in src/solution_arista_avd/pool_roles.py
- [X] T045 [US2] Expand fabric_pool_check query fields for pod_ip_pools, pod racks, parent fabric pools, and rack MLAG settings in checks/fabric_pool_check.gql
- [X] T046 [US2] Implement FabricPoolValidationCheck pod-scope validation errors in checks/fabric_pool_check.py
- [X] T047 [US2] Update generate_pod.gql, generate_rack.gql, and generators/avd_device_hostvar.gql to request pod_ip_pools with pool resources and IpamPrefix.role
- [X] T048 [US2] Regenerate pod, rack, hostvar, and check query models in generators/pod_generator_query.py, generators/rack_generator_query.py, generators/generate_avd_device_inputs_query.py, and checks/fabric_pool_check_query.py
- [X] T049 [US2] Update PodGenerator to resolve device loopback and VTEP pools from pod_ip_pools when present in generators/generate_pod.py
- [X] T050 [US2] Update RackGenerator to resolve device loopback and VTEP pools from pod_ip_pools when present in generators/generate_rack.py
- [X] T051 [US2] Update GenerateAVDDeviceHostvar to prefer pod Fabric Point-to-Point pools for pod-scoped uplink hostvars in generators/generate_avd_device_hostvar.py
- [X] T052 [US2] Run User Story 2 tests with uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_check.py tests/unit/test_generate_pod.py tests/unit/test_generate_rack.py tests/unit/test_generate_avd_device_hostvar.py

**Checkpoint**: User Story 2 is independently testable against pod pool role resolution and containment rules.

---

## Phase 5: User Story 3 - Represent MLAG Pool Requirements and Defaults (Priority: P3)

**Goal**: Pod pool collections represent MLAG and MLAG Peering roles, required MLAG pool conditions are actively validated, and deterministic default /31 behavior allows eligible fabrics and pods to generate without unique manually supplied MLAG pools.

**Independent Test**: Load or model pods with and without explicit MLAG pools; confirm required MLAG roles are derived from fabric underlay and rack MLAG state, default names/prefixes are used when explicit pools are missing, duplicate/mixed MLAG pools fail validation, and /31 reuse is accepted.

### Tests for User Story 3

- [X] T053 [P] [US3] Add failing contract assertions for mlag and mlag_peering IpamPrefix.role choices in tests/unit/test_fabric_pool_schema_contract.py
- [X] T054 [P] [US3] Add failing contract assertions that NetworkPod.mlag_peer_pool and NetworkPod.mlag_l3_pool remain optional legacy relationships in tests/unit/test_fabric_pool_schema_contract.py
- [X] T055 [P] [US3] Add failing MLAG required-role, default-prefix, /31 rack and cross-fabric reuse, and larger-than-/31 containment tests in tests/unit/test_pool_roles.py
- [X] T056 [P] [US3] Add failing proposed-change check tests for MLAG and MLAG Peering role errors in tests/unit/test_fabric_pool_check.py
- [X] T057 [P] [US3] Add failing hostvar tests for MLAG default prefixes and pod_ip_pools precedence in tests/unit/test_generate_avd_device_hostvar.py

### Implementation for User Story 3

- [X] T058 [US3] Add mlag and mlag_peering role choices while retaining technical for migration compatibility in schemas/ipam_extensions.yml
- [X] T059 [US3] Preserve NetworkPod.mlag_peer_pool and NetworkPod.mlag_l3_pool as optional legacy relationships with migration descriptions in schemas/l3ls_extensions.yml
- [X] T059a [US3] Run schema validation after MLAG role and legacy relationship schema changes with uv run infrahubctl schema check schemas/
- [X] T060 [US3] Implement MLAG required-role, default-prefix, /31 reuse, and larger-than-/31 containment logic in src/solution_arista_avd/pool_roles.py
- [X] T061 [US3] Implement FabricPoolValidationCheck MLAG and MLAG Peering validation errors in checks/fabric_pool_check.py
- [X] T062 [US3] Update generators/avd_device_hostvar.gql to request pod_ip_pools, legacy MLAG pools, rack MLAG state, and parent underlay fields needed for MLAG resolution
- [X] T063 [US3] Regenerate hostvar and check query models in generators/generate_avd_device_inputs_query.py and checks/fabric_pool_check_query.py
- [X] T064 [US3] Add failing tests that missing MLAG and MLAG Peering pools create or reuse persisted default pool objects with stable natural keys in tests/unit/test_generate_avd_device_hostvar.py
- [X] T064a [US3] Implement idempotent persisted default MLAG pool creation/upsert for MLAG-Peer-Subnet and MLAG-L3-Peering-Subnet in generators/generate_avd_device_hostvar.py
- [X] T064b [US3] Update GenerateAVDDeviceHostvar to resolve MLAG and MLAG Peering pools from pod_ip_pools, then legacy pools, then deterministic defaults in generators/generate_avd_device_hostvar.py
- [X] T065 [US3] Update contract text for MLAG-Peer-Subnet, MLAG-L3-Peering-Subnet, and /31 reuse semantics in specs/005-fabric-pool-management/contracts/fabric-pool-schema-contract.md
- [X] T066 [US3] Run User Story 3 tests with uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_check.py tests/unit/test_generate_avd_device_hostvar.py

**Checkpoint**: User Story 3 is independently testable against explicit and default MLAG pool behavior.

---

## Phase 6: User Story 4 - Preserve Existing Data Through a Compatible Migration (Priority: P4)

**Goal**: Current seed data remains load-compatible while dual-populated fabric_ip_pools and pod_ip_pools object data moves the repository to the role-driven collection model.

**Independent Test**: Load current seed object data after schema, check, and generator changes; confirm every existing fabric and pod pool assignment has a collection equivalent, legacy relationships remain present for compatibility, and superseded prefix roles are mapped to explicit new roles.

### Tests for User Story 4

- [X] T067 [P] [US4] Add object-data assertions that every NetworkFabric legacy pool assignment is represented in fabric_ip_pools in tests/unit/test_fabric_pool_object_migration.py
- [X] T068 [P] [US4] Add object-data assertions that every NetworkPod legacy MLAG pool assignment is represented in pod_ip_pools in tests/unit/test_fabric_pool_object_migration.py
- [X] T069 [P] [US4] Add object-data assertions for supernet, pod_leaf_spine, pod_super_spine_spine, and technical role migration targets in tests/unit/test_fabric_pool_object_migration.py
- [X] T070 [P] [US4] Add object compatibility smoke-test documentation assertions for quickstart commands in tests/unit/test_fabric_pool_schema_contract.py

### Implementation for User Story 4

- [X] T071 [US4] Update Fabric Supernet and Management pool role data in objects/04_ipam.yml
- [X] T072 [US4] Update Fabric-A and Fabric-B L3LS pool roles from legacy or technical values to explicit role values in objects/04a_l3ls_pools.yml
- [X] T073 [US4] Update Fabric-L3LS-Multi-Domain pool roles from legacy or technical values to explicit role values in objects/04c_fabric_l3ls_multi_domain_pools.yml
- [X] T074 [US4] Add dual-populated fabric_ip_pools and pod_ip_pools to Fabric-A and Fabric-B seed data in objects/10_fabric.yml
- [X] T075 [US4] Add dual-populated fabric_ip_pools and DCI role migration data to Fabric-L3LS-Multi-Domain seed data in objects/10a_fabric_l3ls_multi_domain_fabric.yml
- [X] T076 [US4] Add dual-populated fabric_ip_pools and pod_ip_pools to standalone L2LS seed data in objects/13a_fabric_l2ls.yml
- [X] T077 [US4] Add dual-populated fabric_ip_pools and pod_ip_pools to campus seed data in objects/13b_fabric_campus.yml
- [X] T078 [US4] Add dual-populated fabric_ip_pools to ISIS-LDP seed data in objects/13c_fabric_isis_ldp.yml
- [X] T079 [US4] Add dual-populated fabric_ip_pools and pod_ip_pools to single-DC L3LS seed data in objects/14_fabric_single_dc_l3ls.yml
- [X] T080 [US4] Record final migration mapping and state transitions in specs/005-fabric-pool-management/data-model.md
- [X] T081 [US4] Update object compatibility smoke-test commands and expected outcomes in specs/005-fabric-pool-management/quickstart.md
- [X] T082 [US4] Run User Story 4 tests with uv run pytest tests/unit/test_fabric_pool_object_migration.py tests/unit/test_fabric_pool_schema_contract.py

**Checkpoint**: User Story 4 is independently testable as the dual-populated migration and compatibility increment.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Regenerate derived artifacts, update documentation, and run full validation.

- [X] T083 Verify protocol classes are current after all schema changes in src/solution_arista_avd/protocols.py
- [X] T084 Regenerate all changed GraphQL return types for generators and checks in generators/ and checks/
- [X] T085 [P] Update schema documentation for role-driven fabric and pod pool collections in docs/docs/developer-guide/schemas.md
- [X] T086 [P] Update architecture documentation for pool role resolution, validation, and migration phases in docs/docs/developer-guide/architecture.md
- [X] T087 [P] Update generator documentation for fabric_ip_pools, pod_ip_pools, Fabric Supernet fallback, and MLAG defaults in docs/docs/developer-guide/generators.md
- [X] T088 [P] Update AVD hostvars documentation for role-driven pool inputs in docs/docs/developer-guide/avd/hostvars.md
- [X] T089 [P] Update supported capabilities for fabric and pod pool management behavior in docs/docs/supported-capabilities.md
- [X] T090 Run focused schema, role, check, object, and generator tests with uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_check.py tests/unit/test_fabric_pool_object_migration.py tests/unit/test_l3ls_pools.py tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_generate_pod.py tests/unit/test_generate_rack.py
- [X] T091 Run schema validation with uv run infrahubctl schema check schemas/
- [X] T092 Run object load compatibility validation against objects/ after schema load using specs/005-fabric-pool-management/quickstart.md
- [X] T093 Run full unit tests with uv run pytest tests/unit
- [X] T094 Run repository lint gates with uv run invoke lint
- [X] T095 Run documentation typecheck from docs/ with npm run typecheck
- [X] T096 Run documentation build from docs/ with npm run build
- [ ] T097 Run required Infrahub integration validation with $infrahub-run-integration-tests for schemas/, checks/, generators/, objects/, src/solution_arista_avd/, docs/docs/, and .infrahub.yml
- [ ] T098 Run required generator idempotence validation with $infrahub-test-generator-idempotence for generators/ and src/solution_arista_avd/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational and can start after the shared role model exists; generator integration depends on US1 pool resolution helpers.
- **User Story 3 (Phase 5)**: Depends on US2 because MLAG roles live in pod_ip_pools.
- **User Story 4 (Phase 6)**: Depends on US1-US3 schema and role decisions so object data can be dual-populated correctly.
- **Polish (Phase 7)**: Depends on all desired story phases being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories after Phase 2.
- **US2 (P2)**: Depends on the shared role model and reuses US1 fabric pool resolution helpers.
- **US3 (P3)**: Depends on US2 pod_ip_pools shape and pod role resolution helpers.
- **US4 (P4)**: Depends on US1-US3 because migration mapping must cover every new and legacy relationship.

### Parallel Opportunities

- T002, T003, T004, T005, and T006 can run in parallel during setup.
- T010 can run in parallel with T007-T009 during foundation because it targets a separate test file.
- T016, T017, T018, T019, T020, and T021 can run in parallel before US1 implementation.
- T037, T038, T039, T040, and T041 can run in parallel before US2 implementation.
- T053, T054, T055, T056, and T057 can run in parallel before US3 implementation.
- T067, T068, T069, and T070 can run in parallel before US4 object migration.
- T085, T086, T087, T088, and T089 can run in parallel because they update separate documentation files.

---

## Parallel Example: User Story 1

```bash
Task: "T016 [P] [US1] Add failing contract assertions for IpamPrefix.role new fabric role choices in tests/unit/test_fabric_pool_schema_contract.py"
Task: "T018 [P] [US1] Add failing fabric required-role, duplicate-role, mixed-role, and Fabric Supernet fallback tests in tests/unit/test_pool_roles.py"
Task: "T019 [P] [US1] Add failing proposed-change check tests for missing, duplicate, mixed-role, non-IP, and Fabric Supernet fabric pool errors in tests/unit/test_fabric_pool_check.py"
Task: "T021 [P] [US1] Add failing hostvar tests for resolving DCI and uplink pools from fabric_ip_pools in tests/unit/test_generate_avd_device_hostvar.py"
```

## Parallel Example: User Story 2

```bash
Task: "T037 [P] [US2] Add failing contract assertions for NetworkPod.pod_ip_pools relationship shape in tests/unit/test_fabric_pool_schema_contract.py"
Task: "T038 [P] [US2] Add failing pod role-resolution tests for management exclusion and allowed pod roles in tests/unit/test_pool_roles.py"
Task: "T040 [P] [US2] Add failing proposed-change check tests for pod duplicate-role, mixed-role, non-IP, management-role, and containment errors in tests/unit/test_fabric_pool_check.py"
Task: "T041 [P] [US2] Add failing generator tests for pod_ip_pools precedence over matching fabric pools in tests/unit/test_generate_pod.py and tests/unit/test_generate_rack.py"
```

## Parallel Example: User Story 3

```bash
Task: "T053 [P] [US3] Add failing contract assertions for mlag and mlag_peering IpamPrefix.role choices in tests/unit/test_fabric_pool_schema_contract.py"
Task: "T055 [P] [US3] Add failing MLAG required-role, default-prefix, /31 reuse, and larger-than-/31 containment tests in tests/unit/test_pool_roles.py"
Task: "T056 [P] [US3] Add failing proposed-change check tests for MLAG and MLAG Peering role errors in tests/unit/test_fabric_pool_check.py"
Task: "T057 [P] [US3] Add failing hostvar tests for MLAG default prefixes and pod_ip_pools precedence in tests/unit/test_generate_avd_device_hostvar.py"
```

## Parallel Example: User Story 4

```bash
Task: "T067 [P] [US4] Add object-data assertions that every NetworkFabric legacy pool assignment is represented in fabric_ip_pools in tests/unit/test_fabric_pool_object_migration.py"
Task: "T068 [P] [US4] Add object-data assertions that every NetworkPod legacy MLAG pool assignment is represented in pod_ip_pools in tests/unit/test_fabric_pool_object_migration.py"
Task: "T069 [P] [US4] Add object-data assertions for supernet, pod_leaf_spine, pod_super_spine_spine, and technical role migration targets in tests/unit/test_fabric_pool_object_migration.py"
Task: "T070 [P] [US4] Add object compatibility smoke-test documentation assertions for quickstart commands in tests/unit/test_fabric_pool_schema_contract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for User Story 1.
3. Validate with uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_pool_roles.py tests/unit/test_fabric_pool_check.py tests/unit/test_l3ls_pools.py tests/unit/test_generate_avd_device_hostvar.py.
4. Validate schema loadability with uv run infrahubctl schema check schemas/.
5. Stop and review before implementing pod, MLAG, and full object migration stories.

### Incremental Delivery

1. Deliver US1 to make NetworkFabric.fabric_ip_pools authoritative for fabric roles with active validation.
2. Deliver US2 to make NetworkPod.pod_ip_pools authoritative for pod prefix roles and containment.
3. Deliver US3 to implement MLAG role requirements, defaults, and reuse behavior.
4. Deliver US4 to dual-populate seed data and complete the compatibility migration.
5. Run protocol regeneration, generated query regeneration, focused tests, schema check, object load smoke test, full unit tests, lint, docs validation, integration validation, and generator idempotence validation.

### Validation Notes

- Tests in each story are intentionally first because the feature specification requires test coverage and active validation.
- Do not hand-edit src/solution_arista_avd/protocols.py; regenerate it after schema changes.
- Do not hand-edit generated *_query.py files; regenerate them after changing .gql files.
- Story-local schema checks and regeneration tasks are incremental gates for each independently testable story. Phase 7 repeats them as final whole-feature verification after all schema, query, generator, object, and documentation changes are complete.
- Keep legacy relationships present and load-compatible in this feature; later removal must use the approved schema migration pattern after all code and object data no longer rely on them.
- Because this task list includes generator code and generator GraphQL changes, $infrahub-test-generator-idempotence is required before merge when live validation is allowed.
