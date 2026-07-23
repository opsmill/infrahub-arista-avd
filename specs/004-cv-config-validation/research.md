# Research: CloudVision Configuration Validation

## Decision: Implement pre-merge validation as a targeted fabric check

**Rationale**: The validation is fabric-scoped and must receive the target fabric name as a query variable. A targeted check against the `fabrics` group matches the Infrahub check model: the query variable maps to the fabric target's `name__value`, and each validation run can build a workspace for that one fabric.

**Alternatives considered**:

- Global check across all fabrics: rejected because it would make every proposed change scan all fabrics, complicate workspace identity, and blur per-fabric validation results.
- Generator-based validation: rejected because this is a proposed-change quality gate, not object generation.

## Decision: Bind the query on the Python check class and register the query separately

**Rationale**: Infrahub check definitions do not accept a `query` field in `.infrahub.yml`; the Python check class owns the query name and that name must match a top-level `queries` entry. The live `CoreCheckDefinition` seed object can carry its own query relationship because it is object data, not the repository config schema.

**Alternatives considered**:

- Put `query: cv_config_check` under `.infrahub.yml` `check_definitions`: rejected because the repository config model forbids that key.
- Skip repository seed data and rely only on `.infrahub.yml`: rejected because this project also loads live check/query objects through `repository_checks.yml`.

## Decision: Use generated typed GraphQL response models

**Rationale**: The constitution requires typed models for GraphQL responses. The validation check and workspace submission lookup both need to tolerate nullable relationships, so generated models must accurately represent optional fabric, pod, artifact, structured-config, workspace, and thread fields.

**Alternatives considered**:

- Use untyped dictionaries in production code: rejected by the Type Safety principle and because missing relationships are more likely to become runtime errors.
- Hand-write query response classes: rejected because repository convention is to regenerate return types from `.gql` files.

## Decision: Gate validation with `NetworkFabric.cloudvision_managed`

**Rationale**: Existing and newly created fabrics must skip CloudVision validation unless explicitly enabled. The fabric-level Boolean gives operators a clear opt-in boundary and lets unmanaged fabrics avoid CloudVision credential, serial-number, inventory, workspace, and submission requirements.

**Alternatives considered**:

- Infer management state from CloudVision credentials or generated artifacts: rejected because it would make validation behavior implicit and could block unmanaged fabrics unexpectedly.
- Use a per-device CloudVision Managed flag only: rejected because the requirement is fabric-level eligibility and reviewers need one fabric-scoped validation decision.

## Decision: Validate identity for every device in each managed fabric before workspace work

**Rationale**: CloudVision configuration validation is only meaningful when every device in the managed fabric can be matched to CloudVision inventory. The check must authenticate first, then fail before configuration validation if any device in the managed fabric lacks a serial number or any serial-numbered device is absent from CloudVision inventory.

**Alternatives considered**:

- Validate only devices with structured-config artifacts: rejected because all devices in a CloudVision Managed fabric must pass serial-number and inventory eligibility before configuration validation.
- Treat missing inventory devices as warnings and skip them: rejected because missing inventory membership must block the proposed change.
- Treat missing serial numbers as informational when no structured configs exist: rejected because serial-number eligibility precedes generated-config availability for managed fabrics.

## Decision: Treat inactive CloudVision devices as blocking validation failures

**Rationale**: A CloudVision workspace build can succeed even when one or more targeted devices are inactive and not streaming. That state is not a valid managed-fabric validation outcome, so the check must inspect CloudVision device state for the targeted fabric and fail when any targeted CloudVision device is inactive, even if workspace build reports success.

**Alternatives considered**:

- Rely only on CloudVision workspace build status: rejected because inactive devices can produce a false positive where the workspace builds while CloudVision still shows inactive devices.
- Treat inactive devices as warnings after a successful build: rejected because inactive targeted CloudVision devices must fail validation.
- Skip inactive devices during deployment validation: rejected because every targeted CloudVision device in the managed fabric must be considered for the proposed-change safety gate.

## Decision: Use generated structured configs only for the workspace validation set

**Rationale**: After CloudVision authentication, serial-number validation, inventory validation, and active-state validation succeed for all devices in the managed fabric, only devices with generated structured-config artifacts can be converted to EOS CLI configuration and deployed into the validation workspace. If none are available, the check records an informational result and does not create or build a CloudVision workspace.

**Alternatives considered**:

- Fail a managed fabric with no structured-config artifacts: rejected because the intended behavior is an informational skip after eligibility succeeds.
- Attempt to synthesize missing structured configs in the check: rejected because the AVD generator chain owns artifact creation and this feature is a validation check, not a generator.

## Decision: Use deterministic CloudVision workspace identity per proposed change and fabric

**Rationale**: Rerunning validation should update the same workspace instead of creating a new one, while concurrent proposed changes on the same fabric must not collide. Proposed-change identity plus fabric name provides the stable boundary.

**Alternatives considered**:

- Use only fabric name for workspace identity: rejected because concurrent proposed changes would share a workspace.
- Create a new workspace for every run: rejected because it would create workspace sprawl and make review correlation harder.

## Decision: Derive workspace name and description from proposed-change metadata

**Rationale**: Reviewers need human-readable correlation between Infrahub and CloudVision. The workspace display name should include proposed-change name and fabric name. The workspace description should use the proposed-change description when present and a safe validation fallback when absent.

**Alternatives considered**:

- Use branch name only: rejected because branch names are less meaningful to reviewers and can differ between repository and proposed-change source branch naming.
- Use a fixed description for every workspace: rejected because proposed-change descriptions provide useful review context.

## Decision: Fall back to source-branch lookup when initializer metadata is incomplete

**Rationale**: Live check executions may not always expose proposed-change identity in the initializer. Looking up the open proposed change by source branch preserves deterministic workspace identity and metadata. For `feat/` repository branches, also trying the short branch name handles environments where the proposed-change source branch omits the prefix.

**Alternatives considered**:

- Always fall back to `local`: rejected because live proposed-change validations would share an identity and workspace.
- Fail when initializer metadata is missing: rejected because Infrahub can still expose enough proposed-change metadata through branch lookup.

## Decision: Build before merge, submit only after merge through the direct lifecycle path

**Rationale**: Pre-merge validation should build the CloudVision workspace for review and block invalid proposed changes before merge. Submission changes production state, so it must happen only after Infrahub merge and only for the exact existing workspace linked to the merged proposed change.

**Alternatives considered**:

- Submit immediately from the validation check: rejected because it would deploy unmerged changes and break review semantics.
- Create or rebuild a workspace after merge: rejected because post-merge processing must operate on the already-built linked workspace.
- Submit based only on branch name: rejected because retries and concurrent same-fabric proposed changes need the stable proposed-change ID.

## Decision: Treat workspace thread updates as part of the CloudVision lifecycle

**Rationale**: The created CloudVision workspace URL, submission success, change-control reference, already-complete state, skip outcome, ambiguity outcome, and failure reason are all review or operator-facing lifecycle events. A deterministic `CoreChangeThread` with `CoreThreadComment` entries keeps those events visible in the proposed-change Overview and makes retries idempotent.

**Alternatives considered**:

- Log the workspace URL and submission outcomes only in task logs: rejected because reviewers should not need to inspect task logs for the normal workflow.
- Create a new thread for every retry: rejected because duplicate threads make the proposed-change audit trail harder to read.
- Store only comment text and infer state by parsing it: rejected because text parsing is brittle; lifecycle metadata belongs on `CloudvisionWorkspace`.

## Decision: Extend `CloudvisionWorkspace` with optional lifecycle metadata

**Rationale**: The tracking node already links a deterministic workspace ID to a proposed change and fabric. Optional fields such as `workspace_url`, `thread_id`, `change_control_id`, `change_control_url`, `last_submission_error`, `last_submission_attempt_at`, and `submitted_at` make thread updates and direct submission retry-safe without requiring a second tracking node.

**Alternatives considered**:

- Store only comments and re-query comment text on retry: rejected because idempotence would depend on display wording.
- Create a separate submission node: rejected for this scope because there is a single submission lifecycle per deterministic workspace.

## Decision: Submit the existing CloudVision workspace through PyAVD `CVClient`

**Rationale**: The pinned PyAVD dependency exposes CloudVision client helpers that can submit an existing workspace and wait for the workspace response, including change control IDs when CloudVision creates them. This avoids rebuilding or recreating the workspace after merge.

**Alternatives considered**:

- Use the validation build workflow with requested state `submitted`: rejected for the post-merge path because it can rebuild and starts from validation behavior.
- Call CloudVision gRPC stubs directly everywhere: rejected because the current code already uses PyAVD's client abstraction for CloudVision operations.

## Decision: Resolve workspaces by proposed-change ID on the destination branch

**Rationale**: `CloudvisionWorkspace.proposed_change_id` is the stable correlation key between an Infrahub proposed change and its CloudVision workspace. Looking up the tracking object on the destination branch after merge lets the handler find the workspace created during validation without depending on branch-name heuristics or event-transport-specific payload shapes.

**Alternatives considered**:

- Resolve by source branch only: rejected because branch names are not durable enough for retries and concurrent same-fabric proposed changes.
- Create a workspace after merge when none is found: rejected because missing linked work must be skipped or reported, not invented after merge.

## Decision: Submit exactly one existing submit-ready workspace

**Rationale**: The direct path must submit only when the destination branch has exactly one linked `CloudvisionWorkspace` and its status indicates it is submit-ready. Zero linked workspaces produce a visible skip outcome. Multiple linked workspaces produce an ambiguity failure and no CloudVision submission. Already-submitted workspaces are treated as complete and must not issue another CloudVision submit request.

**Alternatives considered**:

- Submit every linked workspace: rejected because this can deploy ambiguous or unintended work after merge.
- Force-submit a workspace regardless of status: rejected because status captures whether validation created a built workspace ready for deployment.

## Decision: Remove placeholder external webhook registration

**Rationale**: The feature explicitly rejects a fake receiver URL, placeholder shared key, and implied external service dependency. Repository-loaded objects must not include `CoreStandardWebhook` data for CloudVision workspace submission unless a real deployment-specific receiver is implemented outside this feature. The repository should expose callable lifecycle code, an event adapter, and a manual retry path without shipping a placeholder transport binding.

**Alternatives considered**:

- Keep `cloudvision-workspace-submission` with a placeholder URL: rejected because it creates an operational requirement for a nonexistent receiver.
- Replace it with another placeholder trigger object: rejected because the requirement is to remove fake registration, not rename it.

## Decision: Validate placeholder absence as first-class behavior

**Rationale**: The main regression risk is reintroducing a fake webhook or continuing to document it. Unit/static validation should assert that repository objects and CloudVision documentation no longer mention the placeholder receiver name, URL, or shared key. Integration validation remains mandatory for the Infrahub repository changes and must record the tested branch and commit or an approved exception.

**Alternatives considered**:

- Treat webhook removal as manual review only: rejected because no-placeholder behavior is measurable and should be automated where practical.

## Decision: Validation evidence must include unit, schema, lint/type, placeholder absence, and integration checks

**Rationale**: The merged feature touches Infrahub schema, repository config, check code, lifecycle code, query models, object seed data, task loading behavior, integration tests, and documentation. The constitution requires unit tests, schema validation, lint/type checks, and the project integration validation skill for Infrahub code changes.

**Alternatives considered**:

- Rely only on previous live handoff notes: rejected because the plan must produce reproducible merge evidence for the current branch state.
- Skip protocol or query regeneration because production code uses dynamic access in some places: rejected by the Schema-Driven Architecture and Type Safety principles.
