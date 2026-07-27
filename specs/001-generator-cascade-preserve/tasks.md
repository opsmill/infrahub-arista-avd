# Tasks: Generator Cascade Preservation

**Input**: Design documents from `/specs/001-generator-cascade-preserve/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/regenerate-fabric-reconciliation.md`, `quickstart.md`

**Tests**: Required by the feature specification and project constitution. Write focused unit tests before implementation and validate with integration/idempotence skills for generator changes.

**Organization**: Tasks are grouped by user story so reconciliation, preservation, and override-contract handling can be implemented and validated independently.

## Phase 1: Setup (Shared Context)

**Purpose**: Confirm the current generator cascade and test surfaces before changing behavior.

- [X] T001 Review current cascade trigger behavior in `generators/generate_fabric.py`, `generators/generate_pod.py`, and `src/solution_arista_avd/generator.py`
- [X] T002 [P] Review existing device reconciliation and relationship helper tests in `tests/unit/test_generator_mixin.py`
- [X] T003 [P] Review existing fabric and rack generator tests in `tests/unit/test_generate_fabric.py` and `tests/unit/test_generate_rack.py`, and identify the pod generator test patterns needed for `tests/unit/test_generate_pod.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared generator continuation primitives and field-ownership helpers that all user stories depend on.

**Critical**: No user story work can begin until this phase is complete.

- [X] T004 Add named `trigger_pod_generation()` and `trigger_rack_generation()` wrappers around `_trigger_generator()` in `src/solution_arista_avd/generator.py`
- [X] T005 [P] Add relationship-presence helper tests for missing vs populated device relationships in `tests/unit/test_generator_mixin.py`
- [X] T006 Add helper methods for non-empty attribute and relationship detection in `src/solution_arista_avd/generator.py`
- [X] T007 Add logging context for preserved, populated, and skipped generator-owned device fields in `src/solution_arista_avd/generator.py`

**Checkpoint**: Shared helper layer is ready for story-specific generator changes.

---

## Phase 3: User Story 1 - Reconcile a Pre-Existing Fabric (Priority: P1) MVP

**Goal**: A single `generate-fabric` run continues through pod, rack, hostvar, and structured-config generation even when pod or rack checksums are already current.

**Independent Test**: Run fabric/pod unit tests against changed and unchanged downstream targets, then validate the pre-seeded scenario from `quickstart.md`.

### Tests for User Story 1

- [X] T008 [P] [US1] Add unit test proving unchanged non-fabric pods are directly scheduled for `generate-pod` in `tests/unit/test_generate_fabric.py`
- [X] T009 [P] [US1] Add unit test proving changed pods still rely on checksum-trigger saves and are not directly scheduled in `tests/unit/test_generate_fabric.py`
- [X] T010 [P] [US1] Add unit test proving fabric-role pods are skipped by direct pod continuation in `tests/unit/test_generate_fabric.py`
- [X] T011 [P] [US1] Add unit test proving unchanged racks are directly scheduled for `generate-rack` by pod generation in `tests/unit/test_generate_pod.py`
- [X] T012 [P] [US1] Add unit test proving changed racks still rely on checksum-trigger saves and are not directly scheduled by pod generation in `tests/unit/test_generate_pod.py`

### Implementation for User Story 1

- [X] T013 [US1] Update `FabricGenerator.update_checksum()` to collect unchanged non-fabric pod IDs and call `trigger_pod_generation()` in `generators/generate_fabric.py`
- [X] T014 [US1] Update `PodGenerator.update_checksum()` to collect unchanged rack IDs and call `trigger_rack_generation()` in `generators/generate_pod.py`
- [X] T015 [US1] Ensure direct continuation uses `CoreGeneratorDefinitionRun` node targets without fake checksum churn in `src/solution_arista_avd/generator.py`
- [X] T016 [US1] Run focused US1 tests from `tests/unit/test_generate_fabric.py` and `tests/unit/test_generate_pod.py` and update failing mocks or assertions in those files

**Checkpoint**: User Story 1 is independently testable as the MVP.

---

## Phase 4: User Story 2 - Preserve Operator-Provided Device Values (Priority: P2)

**Goal**: Device reconciliation fills missing generator-owned values while preserving pre-existing non-empty operator values such as `serial` and `mgmt_ip`.

**Independent Test**: Pre-seed devices with known values, run the shared device helper, and verify missing generated values are added without overwriting populated values.

### Tests for User Story 2

- [X] T017 [P] [US2] Add unit test proving `create_avd_device()` preserves existing non-empty `serial` and excludes it from upsert payloads in `tests/unit/test_generator_mixin.py`
- [X] T018 [P] [US2] Add unit test proving `create_avd_device()` preserves existing non-empty `mgmt_ip` relationships in `tests/unit/test_generator_mixin.py`
- [X] T019 [P] [US2] Add unit test proving `create_avd_device()` populates missing `mgmt_ip`, `node_id`, `loopback_ip`, `vtep_loopback_ip`, and `asn` relationships in `tests/unit/test_generator_mixin.py`
- [X] T020 [P] [US2] Add unit test proving `avd_devices` group membership is additive and unrelated groups are retained in `tests/unit/test_generator_mixin.py`

### Implementation for User Story 2

- [X] T021 [US2] Refactor `GeneratorMixin.create_avd_device()` to fetch existing devices with generated-owned relationships before constructing the upsert payload in `src/solution_arista_avd/generator.py`
- [X] T022 [US2] Implement fill-only payload construction for status, role, object template, pod, rack, index, group membership, node ID, management IP, loopback IP, VTEP IP, and ASN in `src/solution_arista_avd/generator.py`
- [X] T023 [US2] Preserve rollback behavior for newly created devices and newly allocated ASNs after post-save failures in `src/solution_arista_avd/generator.py`
- [X] T024 [US2] Run focused US2 tests from `tests/unit/test_generator_mixin.py` and update failing mocks or assertions in `tests/unit/test_generator_mixin.py`

**Checkpoint**: User Stories 1 and 2 both work independently and together.

---

## Phase 5: User Story 3 - Preserve the External Contract Boundary (Priority: P3)

**Goal**: Make the override decision explicit for this slice: no external override mode is added, and standard generation remains preservation mode.

**Independent Test**: Review the contract and docs to verify no hidden override input, environment variable, branch-name convention, or service-portal control is introduced.

### Tests for User Story 3

- [X] T025 [P] [US3] Add contract test proving no override runtime input is exposed by the generator run wrapper in `tests/unit/test_generator_cascade_contract.py`

### Implementation for User Story 3

- [X] T026 [US3] Verify no override input is added to `service_catalog/pages/4_Fabric_View.py` or `service_catalog/utils/api.py`
- [X] T027 [US3] Update override non-goal wording if implementation discoveries change the rationale in `specs/001-generator-cascade-preserve/contracts/regenerate-fabric-reconciliation.md`

**Checkpoint**: Override remains deliberately deferred and preservation mode is the only implemented external behavior.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the whole generator slice and update operator/developer documentation.

- [X] T028 [P] Update generator cascade documentation for preservation-mode reconciliation in `docs/docs/developer-guide/generators.md`
- [X] T029 [P] Update AVD pipeline debugging guidance for pre-seeded-device reconciliation in `docs/docs/developer-guide/avd/debugging.md`
- [X] T030 Run focused unit validation from `specs/001-generator-cascade-preserve/quickstart.md` against `tests/unit/test_generate_fabric.py`, `tests/unit/test_generate_pod.py`, `tests/unit/test_generator_mixin.py`, and `tests/unit/test_generate_rack.py`
- [X] T031 Run full local validation from `specs/001-generator-cascade-preserve/quickstart.md` with `uv run pytest tests/unit` and `uv run invoke lint`
- [ ] T032 Use `$infrahub-run-integration-tests` for the generator code changes and record branch/commit evidence in `specs/001-generator-cascade-preserve/quickstart.md`
- [X] T033 Use `$infrahub-test-generator-idempotence` when live validation is permitted and record repeated-run no-drift evidence in `specs/001-generator-cascade-preserve/quickstart.md`
- [X] T034 Add unit coverage in `tests/unit/test_generator_mixin.py` proving `GeneratorMixin.create_avd_device()` logs or records preserved, populated, and skipped field decisions for the target device

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion and is the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion; can run after or beside US1 but final validation should include both.
- **User Story 3 (Phase 5)**: Depends on Foundational completion; can run independently because it is contract/documentation confirmation.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Start after Phase 2. No dependency on US2 or US3.
- **User Story 2 (P2)**: Start after Phase 2. No dependency on US1, but integration validation should include US1 cascade behavior.
- **User Story 3 (P3)**: Start after Phase 2. No dependency on US1 or US2.

### Within Each User Story

- Tests before implementation.
- Shared helpers before generator-specific changes.
- Generator continuation before live cascade validation.
- Device fill-only reconciliation before preservation validation.
- Documentation and required validation skills after local unit/lint gates.

### Parallel Opportunities

- T002 and T003 can run in parallel.
- T005 can run in parallel with T004 after T001.
- T008, T009, T010, T011, and T012 can be drafted in parallel because they target independent test cases.
- T017, T018, T019, and T020 can be drafted in parallel because they cover independent device reconciliation cases.
- T025, T026, T028, and T029 can run in parallel after Phase 2.

---

## Parallel Example: User Story 1

```bash
Task: "T008 [US1] Add unit test proving unchanged non-fabric pods are directly scheduled for generate-pod in tests/unit/test_generate_fabric.py"
Task: "T009 [US1] Add unit test proving changed pods still rely on checksum-trigger saves and are not directly scheduled in tests/unit/test_generate_fabric.py"
Task: "T010 [US1] Add unit test proving fabric-role pods are skipped by direct pod continuation in tests/unit/test_generate_fabric.py"
Task: "T011 [US1] Add unit test proving unchanged racks are directly scheduled for generate-rack by pod generation in tests/unit/test_generate_pod.py"
Task: "T012 [US1] Add unit test proving changed racks still rely on checksum-trigger saves and are not directly scheduled by pod generation in tests/unit/test_generate_pod.py"
```

## Parallel Example: User Story 2

```bash
Task: "T017 [US2] Add unit test proving create_avd_device() preserves existing non-empty serial and excludes it from upsert payloads in tests/unit/test_generator_mixin.py"
Task: "T018 [US2] Add unit test proving create_avd_device() preserves existing non-empty mgmt_ip relationships in tests/unit/test_generator_mixin.py"
Task: "T019 [US2] Add unit test proving create_avd_device() populates missing mgmt_ip, node_id, loopback_ip, vtep_loopback_ip, and asn relationships in tests/unit/test_generator_mixin.py"
Task: "T020 [US2] Add unit test proving avd_devices group membership is additive and unrelated groups are retained in tests/unit/test_generator_mixin.py"
```

## Parallel Example: User Story 3

```bash
Task: "T025 [US3] Add contract test proving no override runtime input is exposed by the generator run wrapper in tests/unit/test_generator_cascade_contract.py"
Task: "T026 [US3] Verify no override input is added to service_catalog/pages/4_Fabric_View.py or service_catalog/utils/api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 to make `generate-fabric` continue the cascade for unchanged pods and racks.
3. Stop and validate with the US1 tests and the pre-seeded fabric scenario from `quickstart.md`.

### Incremental Delivery

1. Deliver US1 to restore cascade completion.
2. Deliver US2 to make reconciliation safe for pre-seeded operator values.
3. Deliver US3 as explicit contract confirmation that override is deferred.
4. Complete Phase 6 validation before merge.

### Parallel Team Strategy

1. One engineer implements shared trigger wrappers and cascade tests.
2. One engineer implements fill-only device reconciliation tests and helper changes.
3. One engineer updates contract/docs and prepares validation evidence.

---

## Notes

- Preservation mode is the only implemented external behavior in this slice.
- Do not add schema fields unless implementation discovers a hard data-model gap; if that happens, stop and use `infrahub-managing-schemas`.
- Do not hand-edit generated query models or `src/solution_arista_avd/protocols.py`.
- Use `allow_upsert=True`, natural keys, additive relationships, and repeated-run validation for all generator-owned data changes.

## Phase 7: Convergence

- [ ] T035 CRITICAL complete remote integration validation with `$infrahub-run-integration-tests` and record tested branch/commit evidence in `specs/001-generator-cascade-preserve/quickstart.md` per Constitution IV / T032 (missing)
- [X] T036 CRITICAL complete live generator idempotence validation with `$infrahub-test-generator-idempotence` when permitted, or record an approved repeated-run validation exception in `specs/001-generator-cascade-preserve/quickstart.md`, per Constitution II / T033 (missing)

## Phase 8: Convergence

- [ ] T037 CRITICAL complete remote integration validation with `$infrahub-run-integration-tests` and record tested branch/commit evidence in `specs/001-generator-cascade-preserve/quickstart.md` per Constitution IV / T032 (missing)

## Phase 9: Convergence

- [ ] T038 CRITICAL complete remote integration validation with `$infrahub-run-integration-tests` and record tested branch/commit evidence in `specs/001-generator-cascade-preserve/quickstart.md` per Constitution IV / T032 (missing)
- [X] T039 Update `connect_interface_maps()` to preserve existing non-empty connector relationships, populate only missing connectors and generated-owned interface state, reuse deterministic `NetworkLink` nodes, and log skipped connector conflicts per FR-026 / plan: connectivity reconciliation (contradicts)
- [X] T040 Update point-to-point IP assignment to preserve existing non-empty interface IP relationships, populate only missing IPs with stable allocation identifiers, and log skipped IP conflicts per FR-026 / SC-008 (contradicts)
- [X] T041 Add unit coverage for cabling and addressing fill-only reconciliation, including missing connector/IP population and conflicting connector/IP preservation with skipped-conflict logs, per Constitution IV / plan: Test-Required Quality (missing)

## Phase 10: Convergence

- [ ] T042 CRITICAL complete remote integration validation with `$infrahub-run-integration-tests` and record tested branch/commit evidence in `specs/001-generator-cascade-preserve/quickstart.md` per Constitution IV / T032 (missing)
