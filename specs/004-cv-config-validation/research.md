# Research: CloudVision Configuration Validation

## Decision: Implement as a targeted fabric check

**Rationale**: The validation is fabric-scoped and must receive the target fabric name as a query variable. A targeted check against the `fabrics` group matches the Infrahub check model: the query variable maps to the fabric target's `name__value`, and each validation run can build a workspace for that one fabric.

**Alternatives considered**:

- Global check across all fabrics: rejected because it would make every proposed change scan all fabrics, complicate workspace identity, and blur per-fabric validation results.
- Generator-based validation: rejected because this is a proposed-change quality gate, not object generation.

## Decision: Bind the query on the Python check class and register the query separately

**Rationale**: Infrahub check definitions do not accept a `query` field in `.infrahub.yml`; the Python check class owns the query name and that name must match a top-level `queries` entry. The live `CoreCheckDefinition` seed object can carry its own query relationship because it is object data, not the repository config schema.

**Alternatives considered**:

- Put `query: cv_config_check` under `.infrahub.yml` `check_definitions`: rejected because the repository config model forbids that key.
- Skip repository seed data and rely only on `.infrahub.yml`: rejected because this project also loads live check/query objects through `repository_checks.yml`.

## Decision: Use a generated typed GraphQL response model

**Rationale**: The constitution requires typed models for GraphQL responses. The check needs to tolerate nullable relationships, so the generated model must accurately represent optional `pod`, `parent`, `avd_artifact`, and `structured_config_file` relationships.

**Alternatives considered**:

- Use untyped dictionaries in production check code: rejected by the Type Safety principle and because it made missing relationships more likely to become runtime errors.
- Query only fabric devices directly through a narrower relationship path: deferred because the current schema relationship path and generated model already provide the required selection data.

## Decision: Gate validation with `NetworkFabric.cloudvision_managed`

**Rationale**: Existing and newly created fabrics must skip CloudVision validation unless explicitly enabled. The fabric-level Boolean gives operators a clear opt-in boundary and lets unmanaged fabrics avoid CloudVision credential, serial-number, inventory, and workspace requirements.

**Alternatives considered**:

- Infer management state from CloudVision credentials or generated artifacts: rejected because it would make validation behavior implicit and could block unmanaged fabrics unexpectedly.
- Use a per-device CloudVision Managed flag only: rejected because the requirement is fabric-level eligibility and reviewers need one fabric-scoped validation decision.

## Decision: Validate identity for every device in each managed fabric before workspace work

**Rationale**: CloudVision configuration validation is only meaningful when every device in the managed fabric can be matched to CloudVision inventory. The check must authenticate first, then fail before configuration validation if any device in the managed fabric lacks a serial number or any serial-numbered device is absent from CloudVision inventory.

**Alternatives considered**:

- Validate only devices with structured-config artifacts: rejected because FR-004, FR-006, FR-007, and FR-008 require all devices in a CloudVision Managed fabric to pass serial-number and inventory eligibility before configuration validation.
- Treat missing inventory devices as warnings and skip them: rejected because the spec requires missing inventory membership to block the proposed change.
- Treat missing serial numbers as informational when no structured configs exist: rejected because serial-number eligibility precedes the generated-config availability check for managed fabrics.

## Decision: Treat inactive CloudVision devices as blocking validation failures

**Rationale**: A CloudVision workspace build can succeed even when one or more targeted devices are inactive and not streaming. That state is not a valid managed-fabric validation outcome, so the check must inspect CloudVision device state for the targeted fabric and fail when any targeted CloudVision device is inactive, even if workspace build reports success.

**Alternatives considered**:

- Rely only on CloudVision workspace build status: rejected because inactive devices can produce a false positive where the workspace builds while CloudVision still shows inactive devices.
- Treat inactive devices as warnings after a successful build: rejected because FR-025 requires inactive targeted CloudVision devices to fail `cv-config-validation`.
- Skip inactive devices during deployment validation: rejected because every targeted CloudVision device in the managed fabric must be considered for the proposed-change safety gate.

## Decision: Use generated structured configs only for the workspace validation set

**Rationale**: After CloudVision authentication, serial-number validation, and inventory validation succeed for all devices in the managed fabric, only devices with generated structured-config artifacts can be converted to EOS CLI configuration and deployed into the validation workspace. If none are available, the check records an informational result and does not create or build a CloudVision workspace.

**Alternatives considered**:

- Fail a managed fabric with no structured-config artifacts: rejected because FR-010 requires an informational skip after eligibility succeeds.
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

## Decision: Build but do not submit CloudVision workspaces

**Rationale**: Building validates the generated configuration and provides review feedback. Submission changes production state and has its own failure modes, so it needs a separate workflow with explicit operator choice and failure handling.

**Alternatives considered**:

- Submit immediately after a successful build: rejected because Infrahub could merge before CloudVision submission succeeds.
- Abandon or submit based on proposed-change lifecycle in this check: rejected as out of scope for validation and better suited to a separate Semaphore-backed workflow.

## Decision: Keep workspace tracking optional at runtime

**Rationale**: Validation should continue in environments where the tracking schema has not been loaded yet. When the schema is present, tracking provides auditability by linking workspace identity, proposed-change identity, status, and fabric.

**Alternatives considered**:

- Require the tracking schema before running CloudVision validation: rejected because it would make rollout brittle and block validation even when CloudVision itself can validate the configs.
- Store tracking in an external local file: rejected because Infrahub is the source of truth for repository state.

## Decision: Validation evidence must include unit, schema, lint/type, and integration checks

**Rationale**: The feature touches Infrahub schema, repository config, check code, query models, object seed data, task loading behavior, and documentation. The constitution requires unit tests, schema validation, lint/type checks, and the project integration validation skill for Infrahub code changes.

**Alternatives considered**:

- Rely only on previous live handoff notes: rejected because the plan must produce reproducible merge evidence for the current branch state.
- Skip protocol regeneration because production code uses dynamic workspace access: rejected by the Schema-Driven Architecture principle; the regeneration command must still be run and recorded.
