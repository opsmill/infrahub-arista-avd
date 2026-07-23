# Check Specification: CloudVision Configuration Validation

> **This is an Infrahub validation check and lifecycle spec.** To implement this behavior, use the `infrahub-managing-checks` skill and preserve proposed-change pipeline semantics.

**Feature Branch**: `feat/cv-config-check`
**Created**: 2026-07-20
**Status**: Draft
**Input**: Merged feature scope: opt CloudVision validation in per fabric, validate managed-fabric generated EOS configurations before merge, expose the created CloudVision workspace in the proposed-change Overview, and submit the linked built workspace after merge through the direct post-merge/API lifecycle path without registering a placeholder external webhook receiver.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Managed Fabric Configurations in CloudVision (Priority: P1)

As a network change reviewer, I need generated EOS configurations validated in CloudVision only for fabrics explicitly marked as CloudVision Managed, so configuration defects are caught for managed fabrics without blocking changes for unmanaged fabrics.

**Why this priority**: This is the primary safety gate. Without it, proposed changes can either merge even when CloudVision would reject a managed fabric's generated configuration, or fail unnecessarily for fabrics that are not managed by CloudVision.

**Independent Test**: Can be tested by creating proposed changes for one CloudVision Managed fabric and one unmanaged fabric, running the check, and verifying that the managed fabric passes only when CloudVision successfully builds the validation workspace while the unmanaged fabric is skipped.

**Acceptance Scenarios**:

1. **Given** a proposed change for a CloudVision Managed fabric whose devices all have serial numbers, exist in CloudVision inventory, are active, and have generated EOS configuration, **When** validation runs, **Then** it creates or updates a CloudVision workspace, builds it, and records a passing validation result with the workspace location.
2. **Given** CloudVision rejects a configuration or the workspace build fails, **When** validation runs, **Then** the proposed change is blocked with a clear failure message that identifies the affected fabric and workspace.
3. **Given** CloudVision credentials are not available and at least one proposed-change fabric is CloudVision Managed, **When** validation runs, **Then** the proposed change is blocked with an actionable credentials configuration error.
4. **Given** a proposed change targets a fabric where CloudVision Managed is false, **When** validation runs, **Then** CloudVision configuration validation is skipped for that fabric and the proposed change is not blocked by CloudVision credentials, serial-number, inventory, workspace, or submission rules.

---

### User Story 2 - Prove Managed Fabric Device Identity (Priority: P1)

As a repository maintainer, I need every device in a CloudVision Managed fabric to be identifiable, present in CloudVision inventory, and active before configuration validation can pass, so the check only validates fabrics that are actually managed by CloudVision.

**Why this priority**: Device identity and active inventory state control whether CloudVision can validate the intended fabric. Missing serial numbers, missing inventory records, or inactive CloudVision devices mean the fabric is not eligible for a passing validation result.

**Independent Test**: Can be tested with fixture data containing CloudVision Managed and unmanaged fabrics, devices inside and outside each target fabric, devices with and without serial numbers, devices present or absent in CloudVision inventory, and active or inactive CloudVision devices.

**Acceptance Scenarios**:

1. **Given** devices from multiple fabrics, **When** validation evaluates a CloudVision Managed target fabric, **Then** every device in that target fabric is considered for serial-number, inventory, and active-state eligibility, and devices outside that fabric are ignored.
2. **Given** at least one device in a CloudVision Managed fabric is missing a serial number, **When** validation runs, **Then** it fails before configuration validation and lists every device in that fabric missing a serial number.
3. **Given** every device in a CloudVision Managed fabric has a serial number but at least one device is absent from CloudVision inventory, **When** validation runs, **Then** it fails before configuration validation and lists every missing CloudVision inventory device.
4. **Given** every device exists in CloudVision inventory but at least one targeted CloudVision device is inactive, **When** validation runs, **Then** validation fails even if the CloudVision workspace build succeeds.
5. **Given** a CloudVision Managed fabric passes authentication, serial-number, inventory, and active-state checks but has no generated structured-config artifacts, **When** validation runs, **Then** it records that no generated configurations are available and does not create or build a CloudVision validation workspace.

---

### User Story 3 - Reuse, Track, And Show Validation Workspaces (Priority: P1)

As a proposed-change reviewer, I need each created CloudVision workspace to be stable and visible directly in the proposed-change Overview, so I can inspect the generated workspace without searching external systems or task logs.

**Why this priority**: Stable workspace identity prevents rerun collisions and workspace sprawl. Showing the workspace URL in the proposed-change Overview gives reviewers a durable handoff between Infrahub validation and CloudVision review.

**Independent Test**: Can be tested by running validation more than once for the same proposed change and fabric, then verifying that the same workspace is reused and that the proposed change has exactly one workspace thread containing the exact workspace URL.

**Acceptance Scenarios**:

1. **Given** the same proposed change and fabric are validated more than once, **When** validation runs, **Then** it reuses the same CloudVision workspace identity.
2. **Given** two open proposed changes target the same fabric, **When** both validations run, **Then** each proposed change receives a different CloudVision workspace identity.
3. **Given** a CloudVision workspace is created or reused for a proposed change, **When** the workspace URL is available, **Then** the proposed change has a workspace overview thread with a comment containing the exact CloudVision workspace URL.
4. **Given** workspace creation is retried for the same proposed change and workspace, **When** the retry completes, **Then** the proposed change does not accumulate duplicate workspace URL threads or duplicate URL comments for the same workspace.
5. **Given** proposed-change metadata is available, **When** the workspace is created or updated, **Then** the workspace display name and description identify the proposed change and fabric.

---

### User Story 4 - Submit The Linked Workspace After Merge (Priority: P1)

As an operator, I need the linked CloudVision workspace to be submitted after the proposed change is merged, so a successful Infrahub merge can advance the already-built CloudVision workspace without manual CloudVision submission.

**Why this priority**: A merged Infrahub change should not leave the linked CloudVision workspace waiting for manual submission when exactly one submit-ready workspace is known. Submission must happen only after merge and only for the workspace linked to that proposed change.

**Independent Test**: Can be tested by simulating or invoking the post-merge/API execution path with a merged proposed-change ID and verifying that the linked workspace is resolved by proposed-change ID, submitted exactly once, and documented in the existing workspace thread.

**Acceptance Scenarios**:

1. **Given** a proposed change with exactly one linked submit-ready workspace is merged, **When** direct post-merge processing runs, **Then** the linked workspace is submitted in CloudVision.
2. **Given** workspace submission succeeds, **When** the submission result is recorded, **Then** the workspace overview thread receives a success comment with the CloudVision change control and the thread is marked resolved after the comment is saved.
3. **Given** the linked workspace has already been submitted, **When** direct post-merge processing is retried, **Then** no duplicate CloudVision submission is issued and an already-complete outcome is recorded.
4. **Given** two proposed changes target the same fabric and each has a different linked workspace, **When** one proposed change is merged, **Then** only that proposed change's workspace is submitted.

---

### User Story 5 - Show Submission Failures And Safe Skip Outcomes (Priority: P2)

As an operator, I need CloudVision submission failures, missing workspace outcomes, and ambiguous workspace outcomes to appear in the proposed-change conversation when possible, so I can understand whether Infrahub merged and what CloudVision action remains.

**Why this priority**: Submission failures happen after the proposed change has merged. Operators need durable, user-visible evidence of post-merge CloudVision outcomes and clear retry behavior.

**Independent Test**: Can be tested by forcing no linked workspace, multiple linked workspaces, non-submit-ready workspace state, CloudVision submission failure, and thread/comment write failure, then verifying the returned outcome, proposed-change comments, thread resolution state, and fallback logs.

**Acceptance Scenarios**:

1. **Given** CloudVision rejects workspace submission, **When** direct post-merge processing handles the failure, **Then** the existing workspace thread receives a failure comment with the rejection reason and remains unresolved.
2. **Given** CloudVision is unreachable or credentials are invalid after Infrahub merge, **When** direct post-merge processing handles the failure, **Then** the existing workspace thread receives a comment explaining that Infrahub merge completed but CloudVision submission did not.
3. **Given** no linked workspace is found for the merged proposed change, **When** direct post-merge processing runs, **Then** no CloudVision workspace is submitted and a user-visible skip outcome is recorded when possible.
4. **Given** multiple candidate workspaces are linked ambiguously to the merged proposed change, **When** direct post-merge processing runs, **Then** no workspace is submitted and a user-visible ambiguity error is recorded when possible.
5. **Given** proposed-change thread or comment writes fail, **When** an outcome is recorded, **Then** the system emits a clear operational log containing the proposed-change, workspace, fabric, and submission outcome context.

---

### User Story 6 - Remove Placeholder Submission Transport (Priority: P2)

As a repository maintainer, I need the CloudVision submission workflow to avoid registering a placeholder external webhook receiver, so repository loading and deployment documentation do not depend on a nonexistent service or made-up URL.

**Why this priority**: A placeholder webhook creates false operational requirements and can break repository loading or deployment reviews. The repository should expose direct lifecycle code and a manual retry path without shipping fake transport registration.

**Independent Test**: Can be tested by inspecting repository-loaded objects and documentation after implementation and verifying that no placeholder CloudVision workspace submission webhook, placeholder receiver URL, placeholder shared key, or separate placeholder receiver service remains.

**Acceptance Scenarios**:

1. **Given** repository trigger and registration files are loaded or reviewed, **When** maintainers inspect the CloudVision workspace submission path, **Then** no placeholder external receiver registration is required for submission.
2. **Given** deployment documentation is read, **When** an operator follows the CloudVision workspace submission instructions, **Then** they are not told to deploy or configure a separate placeholder webhook receiver service.
3. **Given** a placeholder submission webhook was previously added, **When** the revision is complete, **Then** that placeholder registration is removed.

### Edge Cases

- No fabrics in the proposed change are marked CloudVision Managed; validation skips CloudVision configuration validation without requiring CloudVision authentication.
- CloudVision Managed is absent on existing fabric records during rollout; the value is treated as false through the fabric-level default.
- At least one target fabric is CloudVision Managed and CloudVision credentials, authentication, or connectivity fail during runtime setup; validation fails before evaluating device serial numbers, inventory, generated configuration, workspace threads, or submission.
- After CloudVision runtime setup succeeds, the target fabric query returns no fabric node; validation records that no fabric was found and does not fail the proposed change.
- A CloudVision Managed fabric has no devices; after successful CloudVision authentication, serial-number and inventory eligibility pass with zero devices and workspace validation is skipped with an informational result.
- A CloudVision Managed fabric has devices but no generated EOS configs; after successful CloudVision authentication, serial-number, inventory, and active-state checks, validation records that no generated configurations were found and does not run workspace validation.
- Device relationships such as pod, parent fabric, AVD artifact, or structured-config file are absent; unrelated devices are ignored, but every device confirmed to belong to a CloudVision Managed fabric remains subject to serial-number, inventory, and active-state eligibility checks.
- Structured-config files for a device selected for workspace validation cannot be downloaded, decoded, or rendered; validation blocks the proposed change with a clear device-specific error.
- An existing deterministic workspace is already built or otherwise not pending; validation returns it to a pending state before revalidating the proposed change.
- The workspace tracking schema is not loaded in the target Infrahub environment; CloudVision validation still runs and tracking/thread updates are skipped or logged without masking validation results.
- Proposed-change metadata is unavailable from the check initializer; validation attempts to identify the open proposed change by source branch, including a short branch-name fallback for `feat/` branches.
- Workspace creation succeeds but the CloudVision workspace URL is missing or malformed; the workspace is still tracked and an operational fallback is logged instead of creating an empty URL comment.
- A proposed change is merged before the workspace thread was created or before the workspace URL was recorded.
- The proposed change is merged but no CloudVision workspace was created because the fabric was not CloudVision managed or no generated configurations were available.
- More than one workspace appears linked to the same proposed change.
- The linked workspace exists but is not in a submit-ready state.
- The linked workspace has already been submitted before post-merge processing runs.
- CloudVision accepts the submission request but does not return a change control that can be displayed to the user.
- CloudVision accepts the submission request but does not reach a submitted state within the expected confirmation window.
- The proposed change thread exists but comment creation fails.
- Post-merge processing is retried after an earlier submission failure.
- A placeholder external webhook registration exists from an earlier implementation attempt.
- Documentation still references a deployment webhook receiver, receiver URL, or placeholder shared key after the implementation changes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The NetworkFabric data model MUST expose a fabric-level Boolean labeled CloudVision Managed, with a default value of false so existing and newly created fabrics skip CloudVision validation unless explicitly enabled.
- **FR-002**: Validation MUST run as a targeted proposed-change validation for fabric targets and MUST evaluate each target fabric's CloudVision Managed value before requiring CloudVision runtime setup.
- **FR-003**: When a target fabric has CloudVision Managed set to false, validation MUST skip CloudVision configuration validation for that fabric with an informational result and MUST NOT fail because CloudVision credentials, device serial numbers, CloudVision inventory, generated configs, workspaces, or submission tracking are absent.
- **FR-004**: For each targeted validation invocation, if the target fabric has CloudVision Managed set to true, validation MUST perform eligibility validation in this order: authenticate to CloudVision, verify every device in the managed fabric has a serial number, verify every serial-numbered device exists in CloudVision inventory, and verify every targeted CloudVision device is active.
- **FR-005**: Validation MUST block the proposed change when required CloudVision credentials are missing or CloudVision authentication cannot be established for a proposed change containing at least one CloudVision Managed fabric.
- **FR-006**: For each CloudVision Managed fabric, validation MUST gather the fabric identity, every device in that fabric, each device serial number, CloudVision inventory membership, active CloudVision state, and generated structured-config artifact references needed for configuration validation.
- **FR-007**: For each CloudVision Managed fabric, validation MUST fail before configuration validation when any device in that fabric is missing a serial number, and the failure message MUST list every device missing a serial number.
- **FR-008**: For each CloudVision Managed fabric, validation MUST fail before configuration validation when any serial-numbered fabric device is absent from CloudVision inventory, and the failure message MUST list every device missing from inventory.
- **FR-009**: For each CloudVision Managed fabric, validation MUST fail when any targeted CloudVision device is inactive even if the CloudVision workspace build itself succeeds.
- **FR-010**: After CloudVision authentication, serial-number validation, inventory validation, and active-state validation succeed, validation MUST convert each selected device's generated structured configuration into EOS CLI configuration for CloudVision validation.
- **FR-011**: After CloudVision eligibility succeeds, validation MUST skip workspace validation with an informational result when the target fabric has no generated structured-config artifacts to validate.
- **FR-012**: Validation MUST ignore devices outside the target fabric and MUST avoid runtime errors when unrelated or optional relationships are absent.
- **FR-013**: Validation MUST block the proposed change when a selected device's structured-config file cannot be downloaded, decoded, or rendered into EOS CLI configuration, and the failure message MUST identify the affected device.
- **FR-014**: Validation MUST create or update a deterministic CloudVision workspace per proposed change and fabric, so reruns reuse the same workspace and concurrent proposed changes do not collide.
- **FR-015**: The CloudVision workspace display name MUST include the proposed-change name and fabric name.
- **FR-016**: The CloudVision workspace description MUST use the proposed-change description when present. When absent, it MUST use `Infrahub CloudVision validation for proposed change <proposed-change-identity> on fabric <fabric-name>`.
- **FR-017**: Validation MUST return an existing deterministic CloudVision workspace to a pending/buildable state before deploying configs and requesting a workspace build.
- **FR-018**: Validation MUST block the proposed change when CloudVision connection, deployment, or build validation fails.
- **FR-019**: Validation MUST record successful pre-merge validation with the built workspace location, the count of deployed device configs, the count of CloudVision inventory-confirmed devices, and active-device eligibility.
- **FR-020**: Validation MUST create or update Infrahub workspace tracking for the validated workspace when the tracking schema is available, including workspace identity, proposed-change identity, status, related fabric, workspace URL when available, and proposed-change thread identity when available.
- **FR-021**: Validation MUST continue CloudVision validation when workspace tracking is unavailable because the tracking schema is not loaded.
- **FR-022**: Validation MUST use proposed-change metadata from the check context when available and MUST fall back to source-branch lookup when the context lacks proposed-change identity.
- **FR-023**: The check registration MUST keep the check definition, query registration, target group, and target parameters aligned so validation receives the intended fabric data.
- **FR-024**: After CloudVision runtime setup succeeds, when the target fabric is not found, validation MUST record an informational result and MUST NOT fail the proposed change solely because the target fabric is absent.
- **FR-025**: Pre-merge validation MUST build CloudVision workspaces for review and MUST NOT submit CloudVision workspaces before the Infrahub proposed change is merged.
- **FR-026**: When a CloudVision workspace is created or reused for a proposed change, the system MUST create or reuse a proposed-change overview conversation thread for that workspace when thread APIs and tracking fields are available.
- **FR-027**: The workspace overview thread MUST be associated with the proposed change that caused the workspace to be created.
- **FR-028**: The workspace overview thread MUST include a thread comment containing the exact CloudVision workspace URL when the URL is available and valid.
- **FR-029**: Repeated processing for the same proposed change and workspace MUST NOT create duplicate workspace URL threads or duplicate workspace URL comments.
- **FR-030**: After a proposed change is merged, direct post-merge/API processing MUST identify any CloudVision workspace linked to that proposed change by proposed-change ID on the destination branch.
- **FR-031**: When exactly one linked workspace is found and it is submit-ready, direct post-merge/API processing MUST submit that existing CloudVision workspace in CloudVision.
- **FR-032**: A linked workspace is submit-ready only when its tracked status is `built` or `submit_failed`; workspaces in any other status, including missing, ambiguous, already submitted, pending, abandoned, or validation-failed states, MUST NOT be submitted as a new CloudVision operation.
- **FR-033**: Direct post-merge/API processing MUST NOT create, rebuild, or force-submit a new CloudVision workspace when the linked workspace cannot be found or is not submit-ready.
- **FR-034**: If no linked workspace is found, direct post-merge/API processing MUST skip workspace submission and record a user-visible informational outcome when possible.
- **FR-035**: If multiple candidate workspaces are linked ambiguously to the merged proposed change, direct post-merge/API processing MUST NOT submit any workspace and MUST record a clear user-visible error when possible.
- **FR-036**: If the linked workspace is already submitted, direct post-merge/API processing MUST treat the operation as already complete and MUST NOT issue another CloudVision submission.
- **FR-037**: When workspace submission succeeds, the system MUST add a success comment to the existing workspace overview thread with the CloudVision change control ID and user-openable URL when available.
- **FR-038**: After the successful submission or already-complete comment is recorded, the system MUST mark the workspace overview thread resolved.
- **FR-039**: If workspace submission fails, the system MUST add an unresolved failure comment to the same workspace overview thread when possible and MUST include a human-readable failure reason.
- **FR-040**: Submission failure comments MUST include the proposed-change identity, workspace identity, fabric identity when available, and distinguish the completed Infrahub merge from the failed CloudVision submission.
- **FR-041**: A retry after a failed submission MUST either submit the same linked workspace successfully or report the current blocking reason without creating duplicate submissions, duplicate URL comments, or duplicate success comments.
- **FR-042**: If proposed-change thread or comment updates fail, the system MUST emit a clear operational log containing proposed-change, workspace, fabric, and submission outcome context.
- **FR-043**: The repository MUST NOT register a placeholder external webhook receiver for CloudVision workspace submission.
- **FR-044**: The repository MUST NOT require a separate placeholder webhook receiver service for post-merge CloudVision workspace submission.
- **FR-045**: Any previously added placeholder CloudVision workspace submission webhook registration MUST be removed from repository-loaded objects and deployment documentation.
- **FR-046**: Documentation and quickstart material MUST describe the direct post-merge/API execution path and manual retry path without referencing a placeholder receiver service.
- **FR-047**: Validation evidence MUST include local unit/static validation and required integration validation for the merged CloudVision validation and submission path, or an explicit approved exception.

### Check Architecture

- **Check Type**: Targeted proposed-change validation plus direct post-merge/API lifecycle action.
- **Target Group**: `fabrics` for pre-merge validation; merged proposed changes with linked CloudVision workspaces for post-merge submission.
- **Query Parameters**: Fabric target `name`; proposed-change identity; destination branch; linked workspace identity; workspace status; workspace thread identity; CloudVision submission result.

### Key Files

- **Fabric schema**: `schemas/logical_design.yml`
- **Workspace tracking schema**: `schemas/cv/cv.yml`
- **Python validation check**: `checks/cv_config_check.py`
- **Validation GraphQL query**: `checks/cv_config_check.gql`
- **Validation query model**: `checks/cv_config_check_query.py`
- **Workspace lifecycle handler**: `checks/cv_workspace_lifecycle.py`
- **Workspace submission GraphQL query**: `checks/cv_workspace_submission.gql`
- **Workspace submission query model**: `checks/cv_workspace_submission_query.py`
- **Shared utilities**: `checks/cv_helpers.py`
- **Configuration**: `.infrahub.yml`, `repository_checks.yml`, and repository-loaded trigger objects when present
- **Manual retry adapter**: `tasks.py`
- **Unit coverage**: `tests/unit/test_cv_integration.py`
- **Integration coverage**: `tests/integration/helpers.py` and `tests/integration/test_e2e_pipeline.py`
- **User documentation**: `docs/docs/cloudvision.md`

### Key Entities *(include if check involves specific Infrahub schema types)*

- **NetworkFabric**: The fabric selected for proposed-change validation. Its CloudVision Managed Boolean determines whether CloudVision configuration validation applies to the fabric.
- **NetworkPod**: The relationship path used to associate devices with their parent fabric.
- **DcimDevice**: A network device in a fabric. Every device in a CloudVision Managed fabric must have a serial number, exist in CloudVision inventory, and be active before validation can pass.
- **AvdArtifact**: The per-device artifact container that links a device to generated AVD files.
- **AvdStructuredConfigFile**: The generated structured configuration source used to produce EOS CLI configuration for CloudVision validation.
- **CoreProposedChange**: The Infrahub proposed change whose identity scopes workspace validation, thread comments, and post-merge submission.
- **CoreChangeThread**: The proposed-change overview conversation thread used to group workspace URL, submission success, skip, ambiguity, and failure comments.
- **CoreThreadComment**: The user-visible comment used to display workspace URLs, submission success, CloudVision change control, skip outcomes, ambiguity outcomes, or submission errors.
- **CloudvisionWorkspace**: The Infrahub tracking object that links a CloudVision workspace to a proposed change and fabric.
- **CloudVision Workspace**: The external validation workspace created and built before merge, then submitted after merge only through the direct post-merge/API lifecycle path.
- **CloudVision Change Control**: The external change control created by a successful workspace submission and shown back to the proposed-change reviewer when available.
- **SubmissionResult**: The typed lifecycle outcome for direct post-merge submission attempts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a proposed change with a CloudVision Managed fabric whose devices all have serial numbers, exist in CloudVision inventory, are active, and have valid generated configs, validation creates or updates one CloudVision workspace per fabric and reports success within 10 minutes for a representative fabric of up to 50 devices.
- **SC-002**: For a proposed change where every target fabric has CloudVision Managed set to false, validation skips CloudVision configuration validation 100% of the time without requiring CloudVision credentials, serial numbers, inventory membership, generated configs, workspaces, or submission state.
- **SC-003**: For a targeted validation invocation whose target fabric is CloudVision Managed, missing CloudVision credentials, CloudVision authentication failures, CloudVision connection failures, CloudVision workspace build failures, or inactive targeted CloudVision devices block the proposed change 100% of the time with a human-readable error message.
- **SC-004**: For a CloudVision Managed fabric with one or more devices missing serial numbers, validation fails before configuration validation and lists every missing device name in the failure message.
- **SC-005**: For a CloudVision Managed fabric with one or more serial-numbered devices absent from CloudVision inventory, validation fails before configuration validation and lists every missing inventory device name in the failure message.
- **SC-006**: For fixture data with missing pod, artifact, parent fabric, or structured-config relationships outside the target fabric's managed device set, validation completes without runtime exceptions and does not falsely fail solely because unrelated optional relationships are absent.
- **SC-007**: For the same proposed change and fabric, repeated validation produces the same workspace identity on every run; for two different proposed changes on the same fabric, workspace identities differ.
- **SC-008**: For a proposed change that creates one CloudVision workspace, the proposed change Overview shows one workspace thread with the exact workspace URL in 100% of automated test runs where thread APIs and URL metadata are available.
- **SC-009**: For repeated workspace creation processing for the same proposed change and workspace, duplicate workspace URL threads and duplicate workspace URL comments are avoided in 100% of automated test runs.
- **SC-010**: For a merged proposed change with exactly one linked submit-ready workspace, direct post-merge/API processing submits the workspace exactly once in 100% of automated test runs.
- **SC-011**: For successful workspace submission, the proposed change Overview shows a success comment with the CloudVision change control when available and the workspace thread is resolved in 100% of automated test runs where comment APIs are available.
- **SC-012**: For already-submitted linked workspaces, direct post-merge/API processing issues zero duplicate CloudVision submissions in 100% of automated test runs.
- **SC-013**: For missing or ambiguous linked workspace records, direct post-merge/API processing issues zero CloudVision submissions and records the appropriate skip or ambiguity outcome in 100% of automated test runs.
- **SC-014**: For CloudVision submission failures after merge, the proposed change shows or logs a failure outcome that identifies the proposed change, workspace, and reason in 100% of automated test runs.
- **SC-015**: Repository-loaded objects contain zero placeholder CloudVision workspace submission webhook receiver registrations in 100% of validation runs.
- **SC-016**: Documentation and quickstart references to placeholder receiver URLs, placeholder shared keys, or separate placeholder webhook receiver services are removed in 100% of reviewed CloudVision submission documents.
- **SC-017**: Maintainers can verify the merged behavior with automated tests covering CloudVision Managed gating, identity enforcement, inactive-device enforcement, workspace identity, workspace URL comments, direct submission, already-submitted idempotence, skip and ambiguity outcomes, submission failures, no-placeholder registration, manual retry, and branch-scoped structured-config retrieval.
- **SC-018**: Required integration validation records a passing tested branch and commit, or an approved exception, before the feature is considered ready for merge.

## Assumptions

- The AVD generator chain has already produced structured-config artifacts for devices intended to be validated.
- CloudVision Managed defaults to false for existing and new fabrics unless an operator explicitly enables it.
- In a CloudVision Managed fabric, every device in the fabric must be identifiable by serial number, present in CloudVision inventory, and active before any generated configuration can pass validation.
- CloudVision configuration validation deploys only generated structured configs after the fabric has passed CloudVision authentication, serial-number, inventory, and active-state eligibility checks.
- CloudVision credentials and optional proxy settings are provided to the Infrahub task-worker or lifecycle runtime through environment configuration.
- The target `fabrics` group exists and contains the fabrics that should trigger validation.
- The workspace tracking schema may be absent in some environments during rollout; missing tracking must not prevent CloudVision validation.
- The linked workspace is already created and tracked before the proposed change is merged.
- The direct post-merge/API execution path can provide the merged proposed-change identity to the lifecycle handler without an extra placeholder external webhook receiver service.
- Manual retry remains available for operators when automatic post-merge processing fails or needs to be replayed.
