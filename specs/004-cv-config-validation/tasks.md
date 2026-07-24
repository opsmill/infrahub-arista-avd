---
description: "Task list for CloudVision Configuration Validation"
---

# Tasks: CloudVision Configuration Validation

**Input**: Design documents from `/specs/004-cv-config-validation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [quickstart.md](./quickstart.md), [contracts/](./contracts/)

**Tests**: Required by the feature specification and constitution. Write or update tests before completing the implementation tasks in each user story.

**Organization**: Tasks are grouped by user story so each behavior slice can be implemented and tested independently.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the CloudVision validation, lifecycle, schema, query, repository-object, test, and documentation surfaces before story work begins.

- [X] T001 Verify the planned feature file inventory from `specs/004-cv-config-validation/plan.md`
- [X] T002 [P] Review CloudVision runtime and validation commands in `specs/004-cv-config-validation/quickstart.md`
- [X] T003 [P] Review current CloudVision user documentation in `docs/docs/cloudvision.md`
- [X] T004 [P] Review CloudVision documentation navigation in `docs/sidebars.ts`
- [X] T005 [P] Inspect current repository query, transform, and check registrations in `.infrahub.yml`
- [X] T006 [P] Inspect current check, transform, and CustomWebhook seed objects in `repository_checks.yml`
- [X] T007 [P] Inspect current trigger or webhook seed objects in `triggers.yml`
- [X] T008 [P] Inspect existing CloudVision unit coverage in `tests/unit/test_cv_integration.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish schema, GraphQL, generated type, registration, and lifecycle primitives required by all user stories.

**CRITICAL**: No user story work is complete until this phase is complete.

- [X] T009 Add or confirm `NetworkFabric.cloudvision_managed` Boolean with default false in `schemas/logical_design.yml`
- [X] T010 Extend `CloudvisionWorkspace` lifecycle metadata and `submit_failed` status in `schemas/cv/cv.yml`
- [X] T011 Run schema validation for CloudVision schema changes and record command evidence in `specs/004-cv-config-validation/quickstart.md`
- [X] T012 Regenerate protocol classes after schema changes in `src/solution_arista_avd/protocols.py`
- [X] T013 Update targeted validation query fields and nullable relationship selections in `checks/cv_config_check.gql`
- [X] T014 Regenerate typed response models for `checks/cv_config_check.gql` in `checks/cv_config_check_query.py`
- [X] T015 Create or update CustomWebhook payload workspace lookup query in `transforms/cv_workspace_submission_webhook.gql`
- [X] T016 Regenerate typed response models for `transforms/cv_workspace_submission_webhook.gql` in `transforms/cv_workspace_submission_webhook_query.py`
- [X] T017 Register `cv_config_check` and `cv_workspace_submission_webhook` under top-level queries in `.infrahub.yml`
- [X] T018 Register targeted `cv-config-validation` without an invalid `query` key in `.infrahub.yml`
- [X] T019 Register the CustomWebhook payload Python transform in `.infrahub.yml`
- [X] T020 Register live check, query, transform, and placeholder CustomWebhook seed objects in `repository_checks.yml`
- [X] T021 Create or update typed submission result and lifecycle handler scaffolding in `checks/cv_workspace_lifecycle.py`
- [X] T022 Create or update CloudVision configuration, workspace identity, and metadata helpers in `checks/cv_helpers.py`
- [X] T023 Add shared fake CloudVision, fake Infrahub client, and proposed-change fixtures in `tests/unit/test_cv_integration.py`

**Checkpoint**: Schema, generated types, query registration, CustomWebhook registration scaffolding, lifecycle scaffolding, and shared tests are ready for user-story implementation.

---

## Phase 3: User Story 1 - Validate Managed Fabric Configurations in CloudVision (Priority: P1) MVP

**Goal**: Validate generated EOS configurations in CloudVision only for fabrics explicitly marked CloudVision Managed, and skip unmanaged fabrics without requiring CloudVision state.

**Independent Test**: Create proposed changes for one CloudVision Managed fabric and one unmanaged fabric, run `cv-config-validation`, and verify the managed fabric builds a CloudVision validation workspace while the unmanaged fabric skips CloudVision setup and validation.

### Tests for User Story 1

- [X] T024 [P] [US1] Add unmanaged-fabric skip and absent `cloudvision_managed` default-false tests in `tests/unit/test_cv_integration.py`
- [X] T025 [P] [US1] Add managed-fabric missing-credentials and authentication fail-fast tests in `tests/unit/test_cv_integration.py`
- [X] T026 [P] [US1] Add CloudVision runtime configuration tests for token, username/password, certificate, and proxy handling in `tests/unit/test_cv_integration.py`
- [X] T027 [P] [US1] Add branch-scoped structured-config download, JSON decode, and EOS render failure tests in `tests/unit/test_cv_integration.py`
- [X] T028 [P] [US1] Add mocked CloudVision deploy, connection failure, workspace build failure, and inactive-device tests in `tests/unit/test_cv_integration.py`
- [X] T029 [P] [US1] Add tests proving pre-merge validation builds CloudVision workspaces but never submits them in `tests/unit/test_cv_integration.py`

### Implementation for User Story 1

- [X] T030 [US1] Evaluate `cloudvision_managed` before CloudVision setup in `checks/cv_config_check.py`
- [X] T031 [US1] Return informational skip results for unmanaged or missing target fabrics in `checks/cv_config_check.py`
- [X] T032 [US1] Parse CloudVision credentials, certificate verification, and optional proxy settings in `checks/cv_helpers.py`
- [X] T033 [US1] Convert missing CloudVision credentials and authentication failures into actionable check errors in `checks/cv_config_check.py`
- [X] T034 [US1] Download selected structured-config files from the check branch in `checks/cv_config_check.py`
- [X] T035 [US1] Convert structured-config download, JSON decode, and EOS render failures into device-specific blocking results in `checks/cv_config_check.py`
- [X] T036 [US1] Convert CloudVision connection, deploy, build, and inactive-device failures into blocking results in `checks/cv_config_check.py`
- [X] T037 [US1] Ensure validation uses build-only CloudVision helpers and cannot reach workspace submission code in `checks/cv_config_check.py`
- [X] T038 [US1] Log successful workspace URL, deployed config count, skipped config count, inventory-confirmed count, and active-device eligibility in `checks/cv_config_check.py`

**Checkpoint**: User Story 1 validates eligible generated configurations and skips unmanaged fabrics independently.

---

## Phase 4: User Story 2 - Prove Managed Fabric Device Identity (Priority: P1)

**Goal**: Require every device in each CloudVision Managed target fabric to have a serial number, exist in CloudVision inventory, and be active before validation can pass.

**Independent Test**: Run fixture data with managed and unmanaged fabrics, in-fabric and out-of-fabric devices, missing serial numbers, missing CloudVision inventory records, inactive devices, nullable relationships, and no structured-config artifacts.

### Tests for User Story 2

- [X] T039 [P] [US2] Add target-fabric filtering tests for in-fabric and out-of-fabric devices in `tests/unit/test_cv_integration.py`
- [X] T040 [P] [US2] Add nullable relationship tests for missing pod and parent fabric fields in `tests/unit/test_cv_integration.py`
- [X] T041 [P] [US2] Add nullable relationship tests for missing AVD artifact and structured-config fields in `tests/unit/test_cv_integration.py`
- [X] T042 [P] [US2] Add missing serial-number tests listing every affected managed-fabric device in `tests/unit/test_cv_integration.py`
- [X] T043 [P] [US2] Add CloudVision inventory absence tests listing every missing inventory device in `tests/unit/test_cv_integration.py`
- [X] T044 [P] [US2] Add inactive targeted device tests that fail even when workspace build succeeds in `tests/unit/test_cv_integration.py`
- [X] T045 [P] [US2] Add no-devices, no-generated-configs, and target-fabric-not-found informational tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 2

- [X] T046 [US2] Split managed-fabric device selection from structured-config deployment selection in `checks/cv_config_check.py`
- [X] T047 [US2] Harden target-fabric membership checks against nullable generated query fields in `checks/cv_config_check.py`
- [X] T048 [US2] Enforce missing serial-number failures for every confirmed managed-fabric device in `checks/cv_config_check.py`
- [X] T049 [US2] Verify CloudVision inventory membership for every serial-numbered managed-fabric device in `checks/cv_config_check.py`
- [X] T050 [US2] Enforce blocking results for every inactive targeted CloudVision device in `checks/cv_config_check.py`
- [X] T051 [US2] Skip workspace validation with an informational result when no generated structured-config artifacts exist after eligibility passes in `checks/cv_config_check.py`

**Checkpoint**: User Story 2 proves managed-fabric device identity and active CloudVision state without requiring generated configs to exist for every device.

---

## Phase 5: User Story 3 - Reuse, Track, And Show Validation Workspaces (Priority: P1)

**Goal**: Map each proposed change and fabric to a deterministic CloudVision workspace, enrich it with proposed-change metadata, optionally track it in Infrahub, and show the exact workspace URL in the proposed-change Overview.

**Independent Test**: Run validation twice for the same proposed change and fabric and once for a separate proposed change on the same fabric, then compare workspace IDs, display metadata, tracking records, and proposed-change thread comments.

### Tests for User Story 3

- [X] T052 [P] [US3] Add deterministic workspace identity tests for reruns and concurrent proposed changes in `tests/unit/test_cv_integration.py`
- [X] T053 [P] [US3] Add workspace name and description fallback tests in `tests/unit/test_cv_integration.py`
- [X] T054 [P] [US3] Add proposed-change metadata and source-branch fallback tests in `tests/unit/test_cv_integration.py`
- [X] T055 [P] [US3] Add existing CloudVision workspace reuse and rollback-to-pending tests in `tests/unit/test_cv_integration.py`
- [X] T056 [P] [US3] Add `CloudvisionWorkspace` tracking create, update, and missing-schema tests in `tests/unit/test_cv_integration.py`
- [X] T057 [P] [US3] Add proposed-change thread reuse and exact workspace URL comment tests in `tests/unit/test_cv_integration.py`
- [X] T058 [P] [US3] Add duplicate thread and duplicate URL comment prevention tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 3

- [X] T059 [US3] Implement workspace ID, display name, and description helper rules in `checks/cv_helpers.py`
- [X] T060 [US3] Resolve proposed-change metadata from check context and source-branch fallback in `checks/cv_config_check.py`
- [X] T061 [US3] Reuse existing CloudVision workspaces instead of recreating them in `checks/cv_config_check.py`
- [X] T062 [US3] Return existing non-pending CloudVision workspaces to pending before deploying configs in `checks/cv_config_check.py`
- [X] T063 [US3] Upsert `CloudvisionWorkspace` tracking by `workspace_id` in `checks/cv_config_check.py`
- [X] T064 [US3] Skip tracking without masking validation when the tracking schema is unavailable in `checks/cv_config_check.py`
- [X] T065 [US3] Implement deterministic proposed-change thread lookup and creation in `checks/cv_workspace_lifecycle.py`
- [X] T066 [US3] Implement idempotent workspace URL comments in `checks/cv_workspace_lifecycle.py`
- [X] T067 [US3] Persist `workspace_url` and `thread_id` on `CloudvisionWorkspace` after workspace creation or reuse in `checks/cv_config_check.py`
- [X] T068 [US3] Add operational fallback logging for thread or comment creation failures in `checks/cv_workspace_lifecycle.py`

**Checkpoint**: User Story 3 exposes the CloudVision workspace URL in the proposed-change Overview without duplicate threads or comments.

---

## Phase 6: User Story 4 - Submit The Linked Workspace From CustomWebhook (Priority: P1)

**Goal**: Submit exactly one linked submit-ready CloudVision workspace through CustomWebhook processing, add a success or already-complete comment, and resolve the workspace thread only after the outcome comment is saved.

**Independent Test**: Simulate or invoke a submitted proposed change with one linked submit-ready workspace and verify CloudVision submission is called once, the success comment identifies the workspace, and the thread is resolved.

### Tests for User Story 4

- [X] T069 [P] [US4] Add tests for resolving exactly one linked `CloudvisionWorkspace` by proposed-change ID and branch in `tests/unit/test_cv_integration.py`
- [X] T070 [P] [US4] Add tests for successful CloudVision submission and response waiting in `tests/unit/test_cv_integration.py`
- [X] T071 [P] [US4] Add tests proving success and already-complete comments are saved before thread resolution in `tests/unit/test_cv_integration.py`
- [X] T072 [P] [US4] Add tests proving already-submitted workspaces do not issue duplicate submissions in `tests/unit/test_cv_integration.py`
- [X] T073 [P] [US4] Add tests proving the CustomWebhook event adapter passes proposed-change ID and branch to the shared handler in `tests/unit/test_cv_integration.py`
- [X] T074 [P] [US4] Add manual retry task tests that call the same shared handler as CustomWebhook processing in `tests/unit/test_cv_integration.py`

### Implementation for User Story 4

- [X] T075 [US4] Implement `submit_linked_workspace_for_proposed_change` in `checks/cv_workspace_lifecycle.py`
- [X] T076 [US4] Resolve linked workspaces by `proposed_change_id` on the selected branch in `checks/cv_workspace_lifecycle.py`
- [X] T077 [US4] Submit existing workspaces through CloudVision client helpers in `checks/cv_workspace_lifecycle.py`
- [X] T078 [US4] Restrict submission to `built` and `submit_failed` workspace states in `checks/cv_workspace_lifecycle.py`
- [X] T079 [US4] Prevent create, rebuild, and force-submit behavior during CustomWebhook processing in `checks/cv_workspace_lifecycle.py`
- [X] T080 [US4] Update `CloudvisionWorkspace` success status and submission timestamp in `checks/cv_workspace_lifecycle.py`
- [X] T081 [US4] Append success and already-complete comments to the existing workspace thread in `checks/cv_workspace_lifecycle.py`
- [X] T082 [US4] Resolve the workspace thread only after the outcome comment is saved in `checks/cv_workspace_lifecycle.py`
- [X] T083 [US4] Implement `submit_linked_workspace_for_custom_webhook` in `checks/cv_workspace_lifecycle.py`
- [X] T084 [US4] Add manual retry task wiring for `submit-cv-workspace` in `tasks.py`

**Checkpoint**: User Story 4 submits the linked workspace once through CustomWebhook processing and closes the user-visible conversation on success.

---

## Phase 7: User Story 5 - Show Submission Failures And Safe Skip Outcomes (Priority: P2)

**Goal**: Record CloudVision submission failures, no-workspace skips, ambiguity errors, non-submit-ready states, and fallback logs without duplicate submissions or duplicate comments.

**Independent Test**: Force each failure and skip path, then verify the returned result, proposed-change thread state, comments, CloudVision calls, and fallback logs.

### Tests for User Story 5

- [X] T085 [P] [US5] Add CloudVision rejection, authentication, connectivity, and timeout tests in `tests/unit/test_cv_integration.py`
- [X] T086 [P] [US5] Add missing workspace ID and non-submit-ready state tests in `tests/unit/test_cv_integration.py`
- [X] T087 [P] [US5] Add missing-workspace and ambiguous-workspace tests that forbid CloudVision submission calls in `tests/unit/test_cv_integration.py`
- [X] T088 [P] [US5] Add failure comment content tests for proposed-change, workspace, fabric, and reason in `tests/unit/test_cv_integration.py`
- [X] T089 [P] [US5] Add fallback logging tests for thread and comment write failures in `tests/unit/test_cv_integration.py`
- [X] T090 [P] [US5] Add retry tests proving no duplicate URL comments, success comments, or CloudVision submissions in `tests/unit/test_cv_integration.py`

### Implementation for User Story 5

- [X] T091 [US5] Convert CloudVision submission exceptions and timeouts into failed `SubmissionResult` values in `checks/cv_workspace_lifecycle.py`
- [X] T092 [US5] Update `CloudvisionWorkspace.status`, `last_submission_error`, and `last_submission_attempt_at` on submission failure in `checks/cv_workspace_lifecycle.py`
- [X] T093 [US5] Append unresolved failure comments to the existing workspace thread in `checks/cv_workspace_lifecycle.py`
- [X] T094 [US5] Distinguish completed proposed-change submission from failed CloudVision workspace submission in `checks/cv_workspace_lifecycle.py`
- [X] T095 [US5] Record no-workspace, ambiguous-workspace, and non-submit-ready outcomes without CloudVision submission in `checks/cv_workspace_lifecycle.py`
- [X] T096 [US5] Include proposed-change, workspace, fabric, status, reason, and CloudVision-call context in fallback logs in `checks/cv_workspace_lifecycle.py`
- [X] T097 [US5] Preserve retry behavior after `submit_failed` without duplicate URL comments, duplicate success comments, or duplicate CloudVision submissions in `checks/cv_workspace_lifecycle.py`

**Checkpoint**: User Story 5 makes CustomWebhook submission failures visible and retryable.

---

## Phase 8: User Story 6 - Register Placeholder CustomWebhook For Future Deployment Automation (Priority: P2)

**Goal**: Register exactly one placeholder CustomWebhook and payload transform for proposed-change submission while keeping CloudVision change controls, external receivers, and Semaphore playbooks out of scope.

**Independent Test**: Inspect repository-loaded objects and documentation, then run unit/static checks proving one placeholder CustomWebhook exists, references the payload transform, and is documented as a placeholder handoff only.

### Tests for User Story 6

- [X] T098 [P] [US6] Add repository-object tests for exactly one `CoreCustomWebhook` placeholder in `tests/unit/test_cv_integration.py`
- [X] T099 [P] [US6] Add repository-object tests for `CoreCustomWebhook` relationship to `CoreTransformPython` in `tests/unit/test_cv_integration.py`
- [X] T100 [P] [US6] Add payload transform registration tests for `.infrahub.yml` in `tests/unit/test_cv_integration.py`
- [X] T101 [P] [US6] Add placeholder URL and no-real-receiver documentation tests in `tests/unit/test_cv_integration.py`
- [X] T102 [P] [US6] Add no change-control and no Semaphore orchestration documentation tests in `tests/unit/test_cv_integration.py`
- [X] T103 [P] [US6] Add CustomWebhook payload transform output tests in `tests/unit/test_cv_integration.py`

### Implementation for User Story 6

- [X] T104 [US6] Register the `cv_workspace_submission_webhook_payload` Python transform in `.infrahub.yml`
- [X] T105 [US6] Register the `cv_workspace_submission_webhook` query used by the payload transform in `.infrahub.yml`
- [X] T106 [US6] Implement `CVWorkspaceSubmissionWebhookPayload` in `transforms/cv_workspace_submission_webhook.py`
- [X] T107 [US6] Add the required `CoreTransformPython` repository object in `repository_checks.yml`
- [X] T108 [US6] Add exactly one placeholder `CoreCustomWebhook` repository object in `repository_checks.yml`
- [X] T109 [US6] Confirm no duplicate placeholder CustomWebhook object exists in `triggers.yml`
- [X] T110 [US6] Confirm no duplicate placeholder CustomWebhook object exists in `objects/`
- [X] T111 [US6] Document the CustomWebhook placeholder URL and submission handoff in `docs/docs/cloudvision.md`
- [X] T112 [US6] Document that no external automation receiver is required in `docs/docs/cloudvision.md`
- [X] T113 [US6] Document that CloudVision change controls and Semaphore playbooks are out of scope in `docs/docs/cloudvision.md`
- [X] T114 [US6] Update validation commands for placeholder CustomWebhook registration in `specs/004-cv-config-validation/quickstart.md`

**Checkpoint**: Repository-loaded objects and operator documentation expose the placeholder CustomWebhook handoff without requiring a real receiver or deployment workflow.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Run repository quality gates and record merge-ready validation evidence.

- [X] T115 [P] Run focused CloudVision unit tests and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T116 Run `uv run pytest tests/unit` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T117 [P] Run focused ruff checks for CloudVision files and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T118 Run `uv run mypy --show-error-codes src/solution_arista_avd` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T119 Run `uv run mypy --show-error-codes src/solution_arista_avd checks tests/unit/test_cv_integration.py tasks.py` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T120 Run `uv run yamllint .` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T121 Run `uv run invoke lint` and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T122 Re-run schema validation after implementation changes and record results in `specs/004-cv-config-validation/quickstart.md`
- [X] T123 Regenerate `src/solution_arista_avd/protocols.py` after final schema validation if schema output changed
- [X] T124 Regenerate `checks/cv_config_check_query.py` after final query validation if query output changed
- [X] T125 Regenerate `transforms/cv_workspace_submission_webhook_query.py` after final query validation if query output changed
- [X] T126 Run placeholder CustomWebhook registration search and record evidence in `specs/004-cv-config-validation/quickstart.md`
- [ ] T127 Validate or simulate representative CloudVision Managed fabric timing for up to 50 devices and record results in `specs/004-cv-config-validation/quickstart.md`
- [ ] T128 Use `$infrahub-run-integration-tests` and record tested branch, commit, result, CustomWebhook registration evidence, and scope-exclusion evidence in `specs/004-cv-config-validation/quickstart.md`
- [X] T129 Review final consistency across validation, lifecycle, schema, query, tests, docs, quickstart, and task artifacts in `specs/004-cv-config-validation/tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories.
- **User Stories (Phase 3+)**: Depend on Foundational completion.
- **Polish (Phase 9)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational; delivers the MVP validation gate.
- **US2 (P1)**: Can start after Foundational; strengthens US1 device eligibility.
- **US3 (P1)**: Can start after Foundational; workspace tracking depends on schema and lifecycle scaffolding from Phase 2.
- **US4 (P1)**: Can start after Foundational and benefits from US3 tracking/thread helpers.
- **US5 (P2)**: Depends on US4 submission handler surfaces.
- **US6 (P2)**: Can start after Foundational; final validation should run after US4 and US5 confirm the handler path.

### Within Each User Story

- Tests should be written first and should fail before implementation.
- Schema and generated model tasks precede code that references those fields.
- Lifecycle helper changes precede CustomWebhook adapter and manual retry wiring.
- Documentation and repository-object tests must pass before final integration validation.

### Parallel Opportunities

- Setup review tasks T002-T008 can run in parallel.
- Foundational schema, query, registration, helper, and fixture tasks T009-T023 can be split by file after T001 confirms scope.
- Tests within each user story are marked `[P]` because they target independent cases in the same test file but can be drafted independently before consolidation.
- US1, US2, US3, and US6 can be developed in parallel after Phase 2 if file ownership is coordinated.
- US4 and US5 should be sequenced around the shared lifecycle handler in `checks/cv_workspace_lifecycle.py`.

---

## Parallel Example: User Story 1

```bash
Task: "T024 [P] [US1] Add unmanaged-fabric skip and absent cloudvision_managed default-false tests in tests/unit/test_cv_integration.py"
Task: "T025 [P] [US1] Add managed-fabric missing-credentials and authentication fail-fast tests in tests/unit/test_cv_integration.py"
Task: "T026 [P] [US1] Add CloudVision runtime configuration tests for token, username/password, certificate, and proxy handling in tests/unit/test_cv_integration.py"
```

## Parallel Example: User Story 3

```bash
Task: "T052 [P] [US3] Add deterministic workspace identity tests for reruns and concurrent proposed changes in tests/unit/test_cv_integration.py"
Task: "T054 [P] [US3] Add proposed-change metadata and source-branch fallback tests in tests/unit/test_cv_integration.py"
Task: "T057 [P] [US3] Add proposed-change thread reuse and exact workspace URL comment tests in tests/unit/test_cv_integration.py"
```

## Parallel Example: User Story 6

```bash
Task: "T098 [P] [US6] Add repository-object tests for exactly one CoreCustomWebhook placeholder in tests/unit/test_cv_integration.py"
Task: "T100 [P] [US6] Add payload transform registration tests for .infrahub.yml in tests/unit/test_cv_integration.py"
Task: "T102 [P] [US6] Add no change-control and no Semaphore orchestration documentation tests in tests/unit/test_cv_integration.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundational schema, query, generated model, registration, and helper scaffolding.
3. Complete Phase 3 User Story 1.
4. Validate User Story 1 independently with focused unit tests in `tests/unit/test_cv_integration.py`.

### Incremental Delivery

1. Add US1 validation gate and unmanaged skip behavior.
2. Add US2 identity, inventory, and active-state enforcement.
3. Add US3 deterministic workspace tracking and proposed-change thread visibility.
4. Add US4 CustomWebhook submission of the linked built workspace.
5. Add US5 failure, skip, ambiguity, and retry-safe outcomes.
6. Add US6 placeholder CustomWebhook registration and operator documentation.
7. Complete Phase 9 validation evidence.

### Validation Gates

1. Run focused unit tests after each story in `tests/unit/test_cv_integration.py`.
2. Run schema and query regeneration checks after schema or `.gql` changes.
3. Run `uv run invoke lint` before final review.
4. Use `$infrahub-run-integration-tests` before merge for the required Infrahub integration evidence.

---

## Notes

- `[P]` tasks can be worked independently but may still require consolidation in shared files.
- Story labels map tasks to the user stories in `spec.md`.
- The CustomWebhook URL remains a clearly documented placeholder in this phase.
- CloudVision change-control management and Semaphore Ansible execution remain out of scope.
- Generator idempotence validation is not required unless implementation unexpectedly changes generator code, generator queries, or generator-owned relationships.
