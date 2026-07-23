---
description: "Task list for CloudVision Configuration Validation"
---

# Tasks: CloudVision Configuration Validation

**Input**: Design documents from `/specs/004-cv-config-validation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md), [contracts/](./contracts/)

**Tests**: Required by the feature specification and constitution. Write or update tests before completing the implementation tasks in each user story.

**Organization**: Tasks are grouped by user story so each behavior slice can be implemented and tested independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the CloudVision validation, lifecycle, schema, query, test, and documentation surfaces before story work begins.

- [X] T001 Verify the planned feature file inventory from `specs/004-cv-config-validation/plan.md`
- [X] T002 [P] Review CloudVision runtime environment requirements in `specs/004-cv-config-validation/quickstart.md`
- [X] T003 [P] Inspect existing CloudVision documentation navigation in `docs/docs/cloudvision.md`
- [X] T004 [P] Inspect existing CloudVision documentation navigation in `docs/sidebars.ts`
- [X] T005 [P] Inspect placeholder webhook registrations in `.infrahub.yml`
- [X] T006 [P] Inspect placeholder webhook registrations in `repository_checks.yml`
- [X] T007 [P] Inspect existing CloudVision unit coverage in `tests/unit/test_cv_integration.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish schema, query, registration, generated type, and lifecycle primitives required by all user stories.

**CRITICAL**: No user story work is complete until this phase is complete.

- [X] T008 Add `NetworkFabric.cloudvision_managed` Boolean with default false in `schemas/logical_design.yml`
- [X] T009 Extend `CloudvisionWorkspace` lifecycle fields and `submit_failed` status in `schemas/cv/cv.yml`
- [X] T010 Run schema validation for CloudVision schema changes and record the command evidence in `specs/004-cv-config-validation/quickstart.md`
- [X] T011 Regenerate protocol classes after schema changes in `src/solution_arista_avd/protocols.py`
- [X] T012 Update targeted validation query fields and nullable relationship selections in `checks/cv_config_check.gql`
- [X] T013 Regenerate typed response models for `checks/cv_config_check.gql` in `checks/cv_config_check_query.py`
- [X] T014 Create the destination-branch workspace lookup query in `checks/cv_workspace_submission.gql`
- [X] T015 Regenerate typed response models for `checks/cv_workspace_submission.gql` in `checks/cv_workspace_submission_query.py`
- [X] T016 Register `cv_config_check` under top-level repository queries in `.infrahub.yml`
- [X] T017 Register targeted `cv-config-validation` without an invalid `query` key in `.infrahub.yml`
- [X] T018 Register live check/query seed objects for CloudVision validation in `repository_checks.yml`
- [X] T019 Create typed submission result and lifecycle handler scaffolding in `checks/cv_workspace_lifecycle.py`
- [X] T020 Add CloudVision configuration, URL, workspace identity, and metadata helper scaffolding in `checks/cv_helpers.py`
- [X] T021 Add shared fake CloudVision, fake Infrahub client, and proposed-change fixtures in `tests/unit/test_cv_integration.py`

**Checkpoint**: Schema, generated types, query registration, lifecycle scaffolding, and shared tests are ready for user-story implementation.

---

## Phase 3: User Story 1 - Validate Managed Fabric Configurations in CloudVision (Priority: P1)

**Goal**: Validate generated EOS configurations in CloudVision only for fabrics explicitly marked CloudVision Managed, and block managed-fabric proposed changes when credentials, connection, deployment, build validation, or inactive targeted device checks fail.

**Independent Test**: Create proposed changes for one CloudVision Managed fabric and one unmanaged fabric, run `cv-config-validation`, and verify the managed fabric builds a CloudVision validation workspace while the unmanaged fabric skips CloudVision setup and validation.

### Tests for User Story 1

- [X] T022 [P] [US1] Add unmanaged-fabric skip and absent `cloudvision_managed` default-false tests in `tests/unit/test_cv_integration.py`
- [X] T023 [P] [US1] Add managed-fabric missing-credentials and authentication fail-fast tests in `tests/unit/test_cv_integration.py`
- [X] T024 [P] [US1] Add CloudVision runtime configuration tests for token, username/password, certificate, and proxy handling in `tests/unit/test_cv_integration.py`
- [X] T025 [P] [US1] Add branch-scoped structured-config download and decode failure tests in `tests/unit/test_cv_integration.py`
- [X] T026 [P] [US1] Add PyAVD render failure tests for selected structured configs in `tests/unit/test_cv_integration.py`
- [X] T027 [P] [US1] Add mocked CloudVision deploy, connection failure, workspace build failure, and inactive-device tests in `tests/unit/test_cv_integration.py`
- [X] T027a [P] [US1] Add tests proving pre-merge validation builds CloudVision workspaces but never calls CloudVision workspace submission APIs in `tests/unit/test_cv_integration.py`

### Implementation for User Story 1

- [X] T028 [US1] Evaluate `cloudvision_managed` before CloudVision setup in `checks/cv_config_check.py`
- [X] T029 [US1] Return informational skip results for unmanaged fabrics in `checks/cv_config_check.py`
- [X] T030 [US1] Parse CloudVision credentials, certificate verification, and optional proxy settings in `checks/cv_helpers.py`
- [X] T031 [US1] Convert missing CloudVision credentials and authentication failures into actionable check errors in `checks/cv_config_check.py`
- [X] T032 [US1] Download selected structured-config files from the check branch in `checks/cv_config_check.py`
- [X] T033 [US1] Convert structured-config download, JSON decode, and EOS render failures into device-specific blocking results in `checks/cv_config_check.py`
- [X] T034 [US1] Convert CloudVision connection, deploy, build, and inactive-device failures into blocking results in `checks/cv_config_check.py`
- [X] T034a [US1] Ensure pre-merge validation uses build-only CloudVision helpers and cannot reach workspace submission code in `checks/cv_config_check.py`
- [X] T035 [US1] Log successful workspace URL, deployed config count, skipped config count, inventory-confirmed count, and active-device eligibility in `checks/cv_config_check.py`

**Checkpoint**: User Story 1 validates eligible generated configurations and skips unmanaged fabrics independently.

---

## Phase 4: User Story 2 - Prove Managed Fabric Device Identity (Priority: P1)

**Goal**: Require every device in each CloudVision Managed target fabric to have a serial number, exist in CloudVision inventory, and be active before validation can pass.

**Independent Test**: Run fixture data with managed and unmanaged fabrics, in-fabric and out-of-fabric devices, missing serial numbers, missing CloudVision inventory records, inactive devices, nullable relationships, and no structured-config artifacts.

### Tests for User Story 2

- [X] T036 [P] [US2] Add target-fabric filtering tests for in-fabric and out-of-fabric devices in `tests/unit/test_cv_integration.py`
- [X] T037 [P] [US2] Add nullable relationship tests for missing pod and parent fabric fields in `tests/unit/test_cv_integration.py`
- [X] T038 [P] [US2] Add nullable relationship tests for missing AVD artifact and structured-config fields in `tests/unit/test_cv_integration.py`
- [X] T039 [P] [US2] Add missing serial-number tests listing every affected managed-fabric device in `tests/unit/test_cv_integration.py`
- [X] T040 [P] [US2] Add CloudVision inventory absence tests listing every missing inventory device in `tests/unit/test_cv_integration.py`
- [X] T041 [P] [US2] Add inactive targeted device tests that fail even when workspace build succeeds in `tests/unit/test_cv_integration.py`
- [X] T042 [P] [US2] Add no-devices, no-generated-configs, and target-fabric-not-found informational tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 2

- [X] T043 [US2] Split managed-fabric device selection from structured-config deployment selection in `checks/cv_config_check.py`
- [X] T044 [US2] Harden target-fabric membership checks against nullable generated query fields in `checks/cv_config_check.py`
- [X] T045 [US2] Enforce missing serial-number failures for every confirmed managed-fabric device in `checks/cv_config_check.py`
- [X] T046 [US2] Verify CloudVision inventory membership for every serial-numbered managed-fabric device in `checks/cv_config_check.py`
- [X] T047 [US2] Enforce blocking results for every inactive targeted CloudVision device in `checks/cv_config_check.py`
- [X] T048 [US2] Skip workspace validation with an informational result when no generated structured-config artifacts exist after eligibility passes in `checks/cv_config_check.py`
- [X] T049 [US2] Handle empty target fabric query results with a non-blocking informational result in `checks/cv_config_check.py`

**Checkpoint**: User Story 2 proves managed-fabric device identity and active CloudVision state without requiring generated configs to exist for every device.

---

## Phase 5: User Story 3 - Reuse, Track, And Show Validation Workspaces (Priority: P1)

**Goal**: Map each proposed change and fabric to a deterministic CloudVision workspace, enrich it with proposed-change metadata, optionally track it in Infrahub, and show the exact workspace URL in the proposed-change Overview.

**Independent Test**: Run validation twice for the same proposed change and fabric and once for a separate proposed change on the same fabric, then compare workspace IDs, display metadata, tracking records, and proposed-change thread comments.

### Tests for User Story 3

- [X] T050 [P] [US3] Add deterministic workspace identity tests for reruns and concurrent proposed changes in `tests/unit/test_cv_integration.py`
- [X] T051 [P] [US3] Add workspace name and description fallback tests in `tests/unit/test_cv_integration.py`
- [X] T052 [P] [US3] Add proposed-change metadata and source-branch fallback tests in `tests/unit/test_cv_integration.py`
- [X] T053 [P] [US3] Add existing CloudVision workspace reuse and rollback-to-pending tests in `tests/unit/test_cv_integration.py`
- [X] T054 [P] [US3] Add `CloudvisionWorkspace` tracking create, update, and missing-schema tests in `tests/unit/test_cv_integration.py`
- [X] T055 [P] [US3] Add proposed-change thread reuse and exact workspace URL comment tests in `tests/unit/test_cv_integration.py`
- [X] T056 [P] [US3] Add duplicate thread and duplicate URL comment prevention tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 3

- [X] T057 [US3] Implement workspace ID, display name, and description helper rules in `checks/cv_helpers.py`
- [X] T058 [US3] Resolve proposed-change metadata from check context and source-branch fallback in `checks/cv_config_check.py`
- [X] T059 [US3] Reuse existing CloudVision workspaces instead of recreating them in `checks/cv_config_check.py`
- [X] T060 [US3] Return existing non-pending CloudVision workspaces to pending before deploying configs in `checks/cv_config_check.py`
- [X] T061 [US3] Upsert `CloudvisionWorkspace` tracking by `workspace_id` in `checks/cv_config_check.py`
- [X] T062 [US3] Skip tracking without masking validation when the tracking schema is unavailable in `checks/cv_config_check.py`
- [X] T063 [US3] Implement deterministic proposed-change thread lookup and creation in `checks/cv_workspace_lifecycle.py`
- [X] T064 [US3] Implement idempotent workspace URL comments in `checks/cv_workspace_lifecycle.py`
- [X] T065 [US3] Persist `workspace_url` and `thread_id` on `CloudvisionWorkspace` after workspace creation or reuse in `checks/cv_config_check.py`
- [X] T066 [US3] Add operational fallback logging for thread or comment creation failures in `checks/cv_workspace_lifecycle.py`

**Checkpoint**: User Story 3 exposes the CloudVision workspace URL in the proposed-change Overview without duplicate threads or comments.

---

## Phase 6: User Story 4 - Submit The Linked Workspace After Merge (Priority: P1)

**Goal**: Submit exactly one linked submit-ready CloudVision workspace after proposed-change merge, add a success or already-complete comment, and resolve the workspace thread only after the outcome comment is saved.

**Independent Test**: Simulate or invoke a merged proposed change with one linked submit-ready workspace and verify CloudVision submission is called once, the success comment includes the change control, and the thread is resolved.

### Tests for User Story 4

- [X] T067 [P] [US4] Add tests for resolving exactly one linked `CloudvisionWorkspace` by proposed-change ID in `tests/unit/test_cv_integration.py`
- [X] T068 [P] [US4] Add tests for successful CloudVision submission and response waiting in `tests/unit/test_cv_integration.py`
- [X] T069 [P] [US4] Add tests for change-control ID and change-control URL display in `tests/unit/test_cv_integration.py`
- [X] T070 [P] [US4] Add tests proving the thread is resolved only after success or already-complete comments are saved in `tests/unit/test_cv_integration.py`
- [X] T071 [P] [US4] Add tests proving already-submitted workspaces do not issue duplicate submissions in `tests/unit/test_cv_integration.py`
- [X] T072 [P] [US4] Add tests proving the merged-event adapter passes proposed-change ID and destination branch to the shared handler in `tests/unit/test_cv_integration.py`

### Implementation for User Story 4

- [X] T073 [US4] Implement `submit_linked_workspace_for_proposed_change` in `checks/cv_workspace_lifecycle.py`
- [X] T074 [US4] Resolve linked workspaces by `proposed_change_id` on the destination branch in `checks/cv_workspace_lifecycle.py`
- [X] T075 [US4] Submit existing workspaces through CloudVision client helpers in `checks/cv_workspace_lifecycle.py`
- [X] T076 [US4] Restrict submission to `built` and `submit_failed` workspace states in `checks/cv_workspace_lifecycle.py`
- [X] T077 [US4] Prevent create, rebuild, and force-submit behavior after merge in `checks/cv_workspace_lifecycle.py`
- [X] T078 [US4] Update `CloudvisionWorkspace` success status, change-control fields, and submission timestamps in `checks/cv_workspace_lifecycle.py`
- [X] T079 [US4] Append success and already-complete comments to the existing workspace thread in `checks/cv_workspace_lifecycle.py`
- [X] T080 [US4] Resolve the workspace thread only after the outcome comment is saved in `checks/cv_workspace_lifecycle.py`
- [X] T081 [US4] Implement `submit_linked_workspace_for_merged_event` in `checks/cv_workspace_lifecycle.py`
- [X] T082 [US4] Add manual retry task wiring for `submit-cv-workspace` in `tasks.py`

**Checkpoint**: User Story 4 submits the linked workspace once and closes the user-visible conversation on success.

---

## Phase 7: User Story 5 - Show Submission Failures And Safe Skip Outcomes (Priority: P2)

**Goal**: Record post-merge CloudVision submission failures, no-workspace skips, ambiguity errors, non-submit-ready states, and fallback logs without duplicate submissions or duplicate comments.

**Independent Test**: Force each failure and skip path, then verify the returned result, proposed-change thread state, comments, CloudVision calls, and fallback logs.

### Tests for User Story 5

- [X] T083 [P] [US5] Add CloudVision rejection, authentication, connectivity, and timeout tests in `tests/unit/test_cv_integration.py`
- [X] T084 [P] [US5] Add missing request ID and non-submit-ready state tests in `tests/unit/test_cv_integration.py`
- [X] T085 [P] [US5] Add missing-workspace and ambiguous-workspace tests that forbid CloudVision submission calls in `tests/unit/test_cv_integration.py`
- [X] T086 [P] [US5] Add failure comment content tests for proposed-change, workspace, fabric, and reason in `tests/unit/test_cv_integration.py`
- [X] T087 [P] [US5] Add fallback logging tests for thread and comment write failures in `tests/unit/test_cv_integration.py`
- [X] T088 [P] [US5] Add retry tests proving no duplicate URL comments, success comments, or CloudVision submissions in `tests/unit/test_cv_integration.py`

### Implementation for User Story 5

- [X] T089 [US5] Convert CloudVision submission exceptions and timeouts into failed `SubmissionResult` values in `checks/cv_workspace_lifecycle.py`
- [X] T090 [US5] Update `CloudvisionWorkspace.status`, `last_submission_error`, and `last_submission_attempt_at` on submission failure in `checks/cv_workspace_lifecycle.py`
- [X] T091 [US5] Append unresolved failure comments to the existing workspace thread in `checks/cv_workspace_lifecycle.py`
- [X] T092 [US5] Distinguish completed Infrahub merge from failed CloudVision submission in failure comments in `checks/cv_workspace_lifecycle.py`
- [X] T093 [US5] Record no-workspace, ambiguous-workspace, and non-submit-ready outcomes without CloudVision submission in `checks/cv_workspace_lifecycle.py`
- [X] T094 [US5] Include proposed-change, workspace, fabric, change-control, status, and reason context in fallback logs in `checks/cv_workspace_lifecycle.py`
- [X] T095 [US5] Preserve retry behavior after `submit_failed` without duplicate URL comments, duplicate success comments, or duplicate CloudVision submissions in `checks/cv_workspace_lifecycle.py`

**Checkpoint**: User Story 5 makes post-merge submission failures visible and retryable.

---

## Phase 8: User Story 6 - Remove Placeholder Submission Transport (Priority: P2)

**Goal**: Remove the placeholder external webhook registration and prevent repository or documentation drift back toward a fake receiver service.

**Independent Test**: Inspect repository registration files and documentation, then run a unit/static absence check proving no placeholder receiver URL, shared key, or required separate receiver service remains.

### Tests for User Story 6

- [X] T096 [P] [US6] Add placeholder absence tests for repository-loaded object files in `tests/unit/test_cv_integration.py`
- [X] T097 [P] [US6] Add placeholder absence tests for CloudVision documentation in `tests/unit/test_cv_integration.py`
- [X] T098 [P] [US6] Add direct post-merge/API wording tests for CloudVision documentation in `tests/unit/test_cv_integration.py`
- [X] T099 [P] [US6] Add manual retry wording tests for CloudVision documentation in `tests/unit/test_cv_integration.py`

### Implementation for User Story 6

- [X] T100 [US6] Remove placeholder CloudVision workspace submission webhook registrations from `.infrahub.yml`
- [X] T101 [US6] Remove placeholder CloudVision workspace submission webhook registrations from `repository_checks.yml`
- [X] T102 [US6] Remove placeholder CloudVision workspace submission webhook registrations from `triggers.yml`
- [X] T103 [US6] Confirm no replacement placeholder receiver object exists in `objects/`
- [X] T104 [US6] Document the direct post-merge/API execution path in `docs/docs/cloudvision.md`
- [X] T105 [US6] Document the manual retry command in `docs/docs/cloudvision.md`
- [X] T106 [US6] Remove separate placeholder receiver service instructions from `docs/docs/cloudvision.md`
- [X] T107 [US6] Update validation notes for placeholder absence in `specs/004-cv-config-validation/quickstart.md`

**Checkpoint**: Repository-loaded objects and operator documentation no longer require or describe a fake webhook receiver.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Run repository quality gates and record merge-ready validation evidence.

- [X] T108 [P] Run focused CloudVision unit tests and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T109 Run `uv run pytest tests/unit` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T110 [P] Run focused ruff checks for CloudVision files and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T111 Run `uv run mypy --show-error-codes src/solution_arista_avd` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T111a Run `uv run mypy --show-error-codes src/solution_arista_avd checks tests/unit/test_cv_integration.py tasks.py` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T112 Run `uv run yamllint .` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T113 Run `uv run invoke lint` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T114 Re-run schema validation after implementation changes and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T115 Regenerate `src/solution_arista_avd/protocols.py` after final schema validation if schema output changed
- [X] T116 Regenerate `checks/cv_config_check_query.py` after final query validation if query output changed
- [X] T117 Regenerate `checks/cv_workspace_submission_query.py` after final query validation if query output changed
- [X] T118 Run placeholder absence search and record evidence in `specs/004-cv-config-validation/quickstart.md`
- [X] T119 Use `$infrahub-run-integration-tests` and record tested branch, commit, result, and placeholder-webhook absence evidence in `specs/004-cv-config-validation/quickstart.md`
- [X] T119a Validate or simulate representative CloudVision Managed fabric timing for up to 50 devices and record whether pre-merge validation completes within 10 minutes in `specs/004-cv-config-validation/quickstart.md`
- [X] T120 Review final consistency across validation, lifecycle, schema, query, tests, docs, quickstart, and task artifacts in `specs/004-cv-config-validation/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **US1 Validation Gate (Phase 3)**: Depends on Foundational; MVP validation scope.
- **US2 Device Identity (Phase 4)**: Depends on Foundational and shares validation code with US1.
- **US3 Workspace Tracking And Threads (Phase 5)**: Depends on Foundational and successful workspace identity behavior from US1.
- **US4 Direct Submission (Phase 6)**: Depends on Foundational and benefits from US3 thread helpers.
- **US5 Failure/Skip Outcomes (Phase 7)**: Depends on US4 submission result structure.
- **US6 No Placeholder Transport (Phase 8)**: Can start after Setup, but final documentation depends on US4 and US5 behavior.
- **Polish (Phase 9)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 and is the suggested MVP.
- **US2 (P1)**: Can start after Phase 2, but coordinate edits to `checks/cv_config_check.py` with US1.
- **US3 (P1)**: Can start after Phase 2, but depends on workspace creation behavior from US1 for final validation.
- **US4 (P1)**: Can start after Phase 2, but depends on linked `CloudvisionWorkspace` records and benefits from US3 thread helpers.
- **US5 (P2)**: Depends on US4 result handling and lifecycle helper boundaries.
- **US6 (P2)**: Can start after Setup for repository inspection, with docs finalized after US4 and US5 behavior is stable.

### Parallel Opportunities

- T002 through T007 can run in parallel after T001 starts.
- T008, T009, T012, T014, T016, T018, T019, T020, and T021 can start in parallel with file ownership coordination.
- Generated files T011, T013, and T015 depend on the matching schema or query edits.
- Tests within each user story are marked `[P]`, but edits to `tests/unit/test_cv_integration.py` should be serialized if handled by one agent.
- US1 and US2 share `checks/cv_config_check.py`; coordinate implementation order around device selection and runtime validation.
- US4 and US5 share `checks/cv_workspace_lifecycle.py`; implement the typed result structure before failure and retry variants.
- US6 repository-file removals can proceed in parallel with US4/US5 lifecycle work, while documentation should be finalized after the lifecycle behavior is stable.

---

## Parallel Example: User Story 1

```bash
Task: "T022 [P] [US1] Add unmanaged-fabric skip and absent cloudvision_managed default-false tests in tests/unit/test_cv_integration.py"
Task: "T023 [P] [US1] Add managed-fabric missing-credentials and authentication fail-fast tests in tests/unit/test_cv_integration.py"
Task: "T024 [P] [US1] Add CloudVision runtime configuration tests for token, username/password, certificate, and proxy handling in tests/unit/test_cv_integration.py"
```

## Parallel Example: User Story 3

```bash
Task: "T050 [P] [US3] Add deterministic workspace identity tests for reruns and concurrent proposed changes in tests/unit/test_cv_integration.py"
Task: "T051 [P] [US3] Add workspace name and description fallback tests in tests/unit/test_cv_integration.py"
Task: "T055 [P] [US3] Add proposed-change thread reuse and exact workspace URL comment tests in tests/unit/test_cv_integration.py"
```

## Parallel Example: User Story 6

```bash
Task: "T100 [US6] Remove placeholder CloudVision workspace submission webhook registrations from .infrahub.yml"
Task: "T101 [US6] Remove placeholder CloudVision workspace submission webhook registrations from repository_checks.yml"
Task: "T102 [US6] Remove placeholder CloudVision workspace submission webhook registrations from triggers.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate with the focused US1 tests in `tests/unit/test_cv_integration.py`.
5. Stop and review before adding workspace tracking, direct submission, and no-placeholder behavior.

### Incremental Delivery

1. Complete Setup and Foundational tasks.
2. Deliver US1 managed-fabric validation and unmanaged skip behavior.
3. Add US2 managed-fabric identity and active-state enforcement.
4. Add US3 deterministic workspace tracking and proposed-change URL threads.
5. Add US4 direct post-merge submission.
6. Add US5 failure, skip, ambiguity, and retry outcomes.
7. Add US6 placeholder transport removal and documentation.
8. Complete Phase 9 validation evidence before merge.

### Parallel Team Strategy

1. Complete Phase 1 and Phase 2 with schema/query ownership coordination.
2. Assign US1 and US2 to engineers who can coordinate `checks/cv_config_check.py`.
3. Assign US3, US4, and US5 to engineers who can coordinate `checks/cv_workspace_lifecycle.py`.
4. Assign US6 to documentation and repository-object owners after the direct lifecycle behavior is stable.

---

## Phase 10: Convergence

- [X] T121 Harden CloudVision validation query parsing and tests so absent optional relationship keys for pod, parent fabric, AVD artifact, and structured-config file are handled without runtime validation errors per FR-012
- [X] T122 Require `CloudvisionWorkspace.fabric` in the tracking schema and regenerate/validate schema artifacts so every workspace tracking record has fabric correlation per FR-020
