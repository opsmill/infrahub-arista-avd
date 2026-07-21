# Tasks: CloudVision Configuration Validation

**Input**: Design documents from `/specs/004-cv-config-validation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md), [contracts/](./contracts/)

**Tests**: Required by the feature specification and constitution. Add or update focused tests before completing implementation tasks in each user story.

**Organization**: Tasks are grouped by user story so each behavior slice can be implemented and tested independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the current branch has the planned CloudVision check surfaces before story work continues.

- [X] T001 Verify the feature file inventory from `specs/004-cv-config-validation/plan.md` exists at `checks/cv_config_check.py`, `checks/cv_helpers.py`, `checks/cv_config_check.gql`, `checks/cv_config_check_query.py`, `schemas/cv/cv.yml`, `schemas/logical_design.yml`, `repository_checks.yml`, `.infrahub.yml`, `tests/unit/test_cv_integration.py`, and `docs/docs/cloudvision.md`
- [X] T002 [P] Reconcile CloudVision runtime environment variables from `specs/004-cv-config-validation/contracts/runtime-validation.md` with task-worker notes in `docker-compose.override.yml`
- [X] T003 [P] Confirm CloudVision documentation navigation is discoverable through `docs/docs/cloudvision.md` and `docs/sidebars.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish schema, query, registration, and generated type foundations required by every user story.

**CRITICAL**: No user story work is complete until this phase is complete.

- [X] T004 Add or verify the `NetworkFabric.cloudvision_managed` Boolean defaulting to false in `schemas/logical_design.yml`
- [X] T005 Validate the `CloudvisionWorkspace` tracking schema contract from `specs/004-cv-config-validation/contracts/workspace-tracking.md` in `schemas/cv/cv.yml`
- [X] T006 Run schema validation from `specs/004-cv-config-validation/quickstart.md` and fix schema issues in `schemas/logical_design.yml` and `schemas/cv/cv.yml`
- [X] T007 Regenerate protocol classes after schema changes and review generated output in `src/solution_arista_avd/protocols.py`
- [X] T008 Add `cloudvision_managed.value` and nullable relationship fields required by `specs/004-cv-config-validation/contracts/graphql-query.md` to `checks/cv_config_check.gql`
- [X] T009 Regenerate the typed GraphQL response model for `checks/cv_config_check.gql` and review generated output in `checks/cv_config_check_query.py`
- [X] T010 Align top-level query and targeted check registration with `specs/004-cv-config-validation/contracts/check-registration.md` in `.infrahub.yml`
- [X] T011 Align live `CoreGraphQLQuery` and `CoreCheckDefinition` seed objects with `specs/004-cv-config-validation/contracts/check-registration.md` in `repository_checks.yml`

**Checkpoint**: Schema, generated types, query registration, and check registration are ready for user-story implementation.

---

## Phase 3: User Story 1 - Validate Managed Fabric Configurations in CloudVision (Priority: P1) MVP

**Goal**: Validate generated EOS configurations in CloudVision only for fabrics explicitly marked CloudVision Managed, and block managed-fabric proposed changes when credentials, connection, deployment, or build validation fails.

**Independent Test**: Create proposed changes for one managed fabric and one unmanaged fabric, run `cv-config-validation`, and verify the managed fabric builds a CloudVision validation workspace while the unmanaged fabric skips CloudVision setup and validation.

### Tests for User Story 1

- [X] T012 [US1] Add unmanaged-fabric skip and missing `cloudvision_managed` default-false tests in `tests/unit/test_cv_integration.py`
- [X] T013 [US1] Add managed-fabric missing-credentials and CloudVision authentication fail-fast tests in `tests/unit/test_cv_integration.py`
- [X] T014 [US1] Add CloudVision runtime configuration tests for token credentials, username/password credentials, certificate verification, and blank proxy handling in `tests/unit/test_cv_integration.py`
- [X] T015 [US1] Add branch-scoped structured-config download, JSON decode failure, and PyAVD render failure tests in `tests/unit/test_cv_integration.py`
- [X] T016 [US1] Add mocked CloudVision deploy success, connection failure, and workspace build failure tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 1

- [X] T017 [US1] Evaluate `cloudvision_managed` before CloudVision setup and skip unmanaged fabrics with `log_info` in `checks/cv_config_check.py`
- [X] T018 [US1] Update CloudVision credential parsing, authentication setup, certificate verification, optional proxy normalization, and actionable fail-fast errors in `checks/cv_helpers.py`
- [X] T019 [US1] Convert selected structured-config file download, JSON parsing, and `pyavd.get_device_config` rendering failures into blocking device-specific `log_error` results in `checks/cv_config_check.py`
- [X] T020 [US1] Ensure CloudVision connection, deployment, and build exceptions produce blocking `log_error` results without uncaught tracebacks in `checks/cv_config_check.py`
- [X] T021 [US1] Ensure successful validation logs workspace URL, deployed device count, skipped config count, and inventory-confirmed device count in `checks/cv_config_check.py`

**Checkpoint**: User Story 1 validates eligible generated configurations and skips unmanaged fabrics independently.

---

## Phase 4: User Story 2 - Prove Managed Fabric Device Identity (Priority: P2)

**Goal**: Require every device in each CloudVision Managed target fabric to have a serial number and exist in CloudVision inventory before workspace validation starts.

**Independent Test**: Run fixture data with managed and unmanaged fabrics, in-fabric and out-of-fabric devices, missing serial numbers, missing CloudVision inventory records, nullable relationships, and no structured-config artifacts.

### Tests for User Story 2

- [X] T022 [US2] Add target-fabric filtering tests for devices inside and outside the managed fabric in `tests/unit/test_cv_integration.py`
- [X] T023 [US2] Add nullable relationship tests for missing pod, parent fabric, artifact, and structured-config relationships in `tests/unit/test_cv_integration.py`
- [X] T024 [US2] Add missing serial-number tests that expect every missing managed-fabric device name in a blocking error in `tests/unit/test_cv_integration.py`
- [X] T025 [US2] Add CloudVision inventory absence tests that expect every missing managed-fabric device name in a blocking error before workspace validation in `tests/unit/test_cv_integration.py`
- [X] T026 [US2] Add managed-fabric no-devices and no-generated-configs informational skip tests after authentication and inventory eligibility pass in `tests/unit/test_cv_integration.py`
- [X] T027 [US2] Add target-fabric-not-found tests that expect an informational `log_info` result and no proposed-change failure after CloudVision runtime setup succeeds in `tests/unit/test_cv_integration.py`

### Implementation for User Story 2

- [X] T028 [US2] Split managed-fabric device selection from structured-config deployment selection in `checks/cv_config_check.py`
- [X] T029 [US2] Harden target-fabric membership checks against nullable generated query fields in `checks/cv_config_check.py`
- [X] T030 [US2] Enforce missing serial-number failures for every confirmed managed-fabric device before inventory or workspace validation in `checks/cv_config_check.py`
- [X] T031 [US2] Verify CloudVision inventory membership for every serial-numbered managed-fabric device with missing devices reported through blocking `log_error` results in `checks/cv_config_check.py`
- [X] T032 [US2] Skip workspace validation with `log_info` when a managed fabric has no generated structured-config artifacts after authentication, serial-number, and inventory eligibility pass in `checks/cv_config_check.py`
- [X] T033 [US2] Handle empty target fabric query results with a non-blocking `log_info` result in `checks/cv_config_check.py`

**Checkpoint**: User Story 2 proves managed-fabric device identity without requiring generated configs to exist for every device.

---

## Phase 5: User Story 3 - Reuse and Track Proposed-Change Workspaces (Priority: P3)

**Goal**: Map each proposed change and fabric to a deterministic CloudVision workspace, enrich it with proposed-change metadata, and optionally track it in Infrahub.

**Independent Test**: Run validation twice for the same proposed change and fabric and once for a separate proposed change on the same fabric, then compare workspace IDs, display metadata, and tracking records.

### Tests for User Story 3

- [X] T034 [US3] Add deterministic workspace identity tests for reruns and concurrent proposed changes in `tests/unit/test_cv_integration.py`
- [X] T035 [US3] Add workspace name and description fallback tests using proposed-change name, description, identity, source branch, and fabric name in `tests/unit/test_cv_integration.py`
- [X] T036 [US3] Add existing CloudVision workspace reuse and non-pending rollback-to-pending tests in `tests/unit/test_cv_integration.py`
- [X] T037 [US3] Add `CloudvisionWorkspace` tracking create, update, and missing-schema tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 3

- [X] T038 [US3] Ensure workspace ID, display name, and description helpers meet metadata fallback rules in `checks/cv_helpers.py`
- [X] T039 [US3] Fix CloudVision workspace create-or-update flow so existing workspaces are reused and not recreated after lookup in `checks/cv_config_check.py`
- [X] T040 [US3] Return existing non-pending CloudVision workspaces to pending before deploying configs in `checks/cv_config_check.py`
- [X] T041 [US3] Implement idempotent `CloudvisionWorkspace` create-or-update tracking by `workspace_id` in `checks/cv_config_check.py`
- [X] T042 [US3] Ensure missing `CloudvisionWorkspace` schema skips tracking without masking CloudVision validation success or failure in `checks/cv_config_check.py`

**Checkpoint**: User Story 3 can be verified through deterministic helper tests and mocked Infrahub tracking behavior.

---

## Phase 6: User Story 4 - Preserve a Clear Scope Boundary for Deployment (Priority: P4)

**Goal**: Keep the check limited to workspace build validation and explicitly exclude workspace submission, deletion-time abandonment, and post-merge deployment.

**Independent Test**: Run successful validation and verify a CloudVision workspace build is requested but no submit, abandon-on-delete, or post-merge deployment action is invoked.

### Tests for User Story 4

- [X] T043 [US4] Add tests proving successful validation requests a built workspace but does not submit the workspace in `tests/unit/test_cv_integration.py`
- [X] T044 [US4] Add tests proving proposed-change deletion and post-merge deployment lifecycle hooks are absent from `checks/cv_config_check.py`

### Implementation for User Story 4

- [X] T045 [US4] Keep CloudVision workspace requested state limited to built validation behavior in `checks/cv_config_check.py`
- [X] T046 [US4] Confirm no trigger, generator, or post-merge deployment registration was added for this feature in `.infrahub.yml`
- [X] T047 [US4] Document the out-of-scope submission, deletion abandonment, and post-merge deployment boundary in `docs/docs/cloudvision.md`

**Checkpoint**: User Story 4 confirms validation-only behavior and leaves deployment to a separate feature.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Run repository quality gates and record merge-ready validation evidence.

- [X] T048 Run focused unit tests from `specs/004-cv-config-validation/quickstart.md` and fix failures in `tests/unit/test_cv_integration.py`
- [X] T049 Run focused ruff checks from `specs/004-cv-config-validation/quickstart.md` and fix findings in `checks/cv_config_check.py`, `checks/cv_helpers.py`, `checks/cv_config_check_query.py`, and `tests/unit/test_cv_integration.py`
- [X] T050 Run focused mypy checks from `specs/004-cv-config-validation/quickstart.md` and fix findings in `checks/cv_config_check.py`, `checks/cv_helpers.py`, and `tests/unit/test_cv_integration.py`
- [X] T051 Run `uv run pytest tests/unit` and fix feature regressions in `tests/unit/`
- [X] T052 Run `uv run yamllint .infrahub.yml repository_checks.yml schemas/logical_design.yml schemas/cv/cv.yml` and fix YAML findings in `.infrahub.yml`, `repository_checks.yml`, `schemas/logical_design.yml`, and `schemas/cv/cv.yml`
- [X] T053 Re-run schema validation from `specs/004-cv-config-validation/quickstart.md` after implementation changes and fix schema issues in `schemas/logical_design.yml` and `schemas/cv/cv.yml`
- [X] T054 Run the full lint gate with `uv run invoke lint` and fix findings in `checks/cv_config_check.py`, `checks/cv_helpers.py`, `checks/cv_config_check_query.py`, `tests/unit/test_cv_integration.py`, `.infrahub.yml`, `repository_checks.yml`, `schemas/logical_design.yml`, and `schemas/cv/cv.yml`
- [X] T055 Add a representative 50-device mocked validation timing test for the SC-001 10-minute target in `tests/unit/test_cv_integration.py`, asserting the local non-network validation path completes within a documented threshold and recording that live CloudVision latency is excluded from the unit measurement
- [X] T056 Use `$infrahub-run-integration-tests` for required Infrahub integration validation and record the tested branch and commit in `specs/004-cv-config-validation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; MVP scope.
- **User Story 2 (Phase 4)**: Depends on Foundational; can run after or alongside User Story 1 with shared-file coordination.
- **User Story 3 (Phase 5)**: Depends on Foundational; can run after or alongside User Story 1 with shared-file coordination.
- **User Story 4 (Phase 6)**: Depends on User Story 1 because it verifies successful validation does not deploy.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Core MVP; no dependency on other stories after Phase 2.
- **US2 (P2)**: Device identity eligibility; no dependency on US1 CloudVision workspace build behavior, but shares `checks/cv_config_check.py`.
- **US3 (P3)**: Workspace identity and tracking; no dependency on US2, but shares `checks/cv_helpers.py` and `checks/cv_config_check.py`.
- **US4 (P4)**: Depends on US1 behavior because it verifies successful workspace build without submission.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001 because they touch different files.
- T004, T005, T008, T010, and T011 can be reviewed in parallel, but T006 depends on T004 and T005, T007 depends on T006, and T009 depends on T008.
- Test design for each story can start before implementation, but tasks editing `tests/unit/test_cv_integration.py` should be serialized to avoid conflicts.
- User stories can be assigned in parallel only with explicit ownership of shared files: `checks/cv_config_check.py`, `checks/cv_helpers.py`, and `tests/unit/test_cv_integration.py`.
- T048, T049, T050, T052, and T053 can be run by separate executors only if each executor owns remediation for non-overlapping files.

---

## Parallel Example: Foundational Review

```text
Task: "Add or verify NetworkFabric.cloudvision_managed in schemas/logical_design.yml"
Task: "Validate CloudvisionWorkspace tracking schema in schemas/cv/cv.yml"
Task: "Add cloudvision_managed.value to checks/cv_config_check.gql"
Task: "Align check registration in .infrahub.yml"
Task: "Align live seed objects in repository_checks.yml"
```

---

## Parallel Example: User Story 1

```text
Task: "Add unmanaged-fabric skip tests in tests/unit/test_cv_integration.py"
Task: "Update CloudVision credential parsing in checks/cv_helpers.py"
Task: "Evaluate cloudvision_managed before CloudVision setup in checks/cv_config_check.py"
```

---

## Parallel Example: User Story 2

```text
Task: "Add nullable relationship tests in tests/unit/test_cv_integration.py"
Task: "Split managed-fabric device selection from deployment selection in checks/cv_config_check.py"
Task: "Enforce missing serial-number failures in checks/cv_config_check.py"
```

---

## Parallel Example: User Story 3

```text
Task: "Add deterministic workspace identity tests in tests/unit/test_cv_integration.py"
Task: "Ensure workspace metadata helper fallbacks in checks/cv_helpers.py"
Task: "Implement workspace tracking upsert in checks/cv_config_check.py"
```

---

## Parallel Example: User Story 4

```text
Task: "Add validation-only behavior tests in tests/unit/test_cv_integration.py"
Task: "Confirm no post-merge deployment registration in .infrahub.yml"
Task: "Document deployment boundary in docs/docs/cloudvision.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 for User Story 1.
3. Run focused unit, ruff, and mypy checks from `specs/004-cv-config-validation/quickstart.md`.
4. Validate the MVP against a prepared branch with `cv-config-validation`.

### Incremental Delivery

1. Add US1 to provide the managed-fabric CloudVision validation gate.
2. Add US2 to enforce serial-number and inventory eligibility for every managed-fabric device.
3. Add US3 to make workspace reruns deterministic and trackable.
4. Add US4 to prove the deployment boundary remains validation-only.
5. Finish with unit, schema, lint, YAML, and integration validation.

### Validation Notes

- Generator idempotence validation is not required because this feature does not change generator code, generator queries, or generator-owned relationships.
- `$infrahub-run-integration-tests` is required before merge because this feature changes Infrahub check code, schema, query registration, repository seed data, and docs.
- Missing CloudVision inventory membership is blocking for managed fabrics and must use `log_error`, not warning-style `log_info`.
- Non-blocking observations must use `log_info` because Infrahub checks do not expose a warning log API.

## Phase 8: Convergence

- [X] T057 Reconcile and record the current required integration validation evidence, including the tested branch, commit, result, and T056 handoff state, per Constitution IV / T056
- [X] T058 Move the CloudVision validation guide from `docs/docs/developer-guide/cloudvision.md` into the user-facing guide/navigation and remove the developer-guide sidebar placement per User input / plan: documentation navigation
- [X] T059 Update the moved CloudVision guide so it matches the current implementation, including managed-fabric gating, validation order, optional workspace tracking, deterministic workspace reuse, rollback-to-pending behavior, source-branch proposed-change lookup, and validation-only scope per T047 / current implementation
- [X] T060 Update PR #73 body with a concise summary of how CloudVision validation works and the implementation choices documented in the moved guide per User input / PR body

## Phase 9: Convergence

- [X] T061 Add inactive targeted CloudVision device unit coverage, including the false-positive case where workspace build succeeds but an inventory-confirmed device is inactive, in `tests/unit/test_cv_integration.py` per FR-025 / SC-009 (missing)
- [X] T062 Enforce blocking `log_error` results for every inactive targeted CloudVision device in `checks/cv_config_check.py`, using CloudVision inventory streaming state and preventing a passing result even when workspace build succeeds, per FR-025 (missing)
- [X] T063 Document that inactive CloudVision devices fail `cv-config-validation` even when workspace build succeeds in `docs/docs/cloudvision.md` per plan: user documentation (missing)
- [X] T064 Re-run focused unit, ruff, mypy, and local validation for the inactive-device change and record that the remote integration run was stopped by user direction in `specs/004-cv-config-validation/quickstart.md` per User input / validation evidence
