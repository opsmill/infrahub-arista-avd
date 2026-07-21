# Check Specification: CloudVision Configuration Validation

> **This is an Infrahub validation check spec.** To implement this check, use the `infrahub-managing-checks` skill.

**Feature Branch**: `feat/cv-config-check`
**Created**: 2026-07-20
**Status**: Draft
**Input**: User description: "Add a CloudVision Managed boolean at the fabric level. Managed fabrics are eligible for CloudVision configuration validation; unmanaged fabrics skip the proposed-change check. When at least one managed fabric is present, the check must authenticate to CloudVision, require every device in each managed fabric to have a serial number, and require every device in each managed fabric to exist in CloudVision inventory before configuration validation runs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Managed Fabric Configurations in CloudVision (Priority: P1)

As a network change reviewer, I need generated EOS configurations validated in CloudVision only for fabrics explicitly marked as CloudVision Managed, so configuration defects are caught for managed fabrics without blocking changes for unmanaged fabrics.

**Why this priority**: This is the primary safety gate. Without it, proposed changes can either merge even when CloudVision would reject a managed fabric's generated configuration, or fail unnecessarily for fabrics that are not managed by CloudVision.

**Independent Test**: Can be tested by creating proposed changes for one CloudVision Managed fabric and one unmanaged fabric, running the check, and verifying that the managed fabric passes only when CloudVision successfully builds the validation workspace while the unmanaged fabric is skipped.

**Acceptance Scenarios**:

1. **Given** a proposed change for a CloudVision Managed fabric whose devices all have serial numbers, exist in CloudVision inventory, and have generated EOS configuration, **When** the validation check runs, **Then** it creates or updates a CloudVision workspace, builds it, and records a passing validation result with the workspace location.
2. **Given** CloudVision rejects a configuration or the workspace build fails, **When** the validation check runs, **Then** the proposed change is blocked with a clear failure message that identifies the affected fabric and workspace.
3. **Given** CloudVision credentials are not available to the check runtime and at least one proposed-change fabric is CloudVision Managed, **When** the validation check runs, **Then** the proposed change is blocked with an actionable credentials configuration error.
4. **Given** a proposed change targets a fabric where CloudVision Managed is false, **When** the validation check runs, **Then** CloudVision configuration validation is skipped for that fabric and the proposed change is not blocked by CloudVision credentials, serial-number, inventory, or workspace validation rules.

---

### User Story 2 - Prove Managed Fabric Device Identity (Priority: P2)

As a repository maintainer, I need every device in a CloudVision Managed fabric to be identifiable and present in CloudVision before configuration validation starts, so the check only validates fabrics that are actually managed by CloudVision.

**Why this priority**: Device identity controls whether CloudVision can validate the intended fabric. Missing serial numbers or missing inventory records mean the fabric is not eligible for CloudVision configuration validation and must fail before workspace work begins.

**Independent Test**: Can be tested with fixture data containing CloudVision Managed and unmanaged fabrics, devices inside and outside each target fabric, devices with and without serial numbers, and devices present or absent in CloudVision inventory.

**Acceptance Scenarios**:

1. **Given** devices from multiple fabrics, **When** the check evaluates a CloudVision Managed target fabric, **Then** every device in that target fabric is considered for serial-number and CloudVision inventory eligibility, and devices outside that fabric are ignored.
2. **Given** at least one device in a CloudVision Managed fabric is missing a serial number, **When** the check runs, **Then** it fails before configuration validation and lists every device in that fabric missing a serial number.
3. **Given** every device in a CloudVision Managed fabric has a serial number but at least one device is absent from CloudVision inventory, **When** the check runs, **Then** it fails before configuration validation and lists every missing CloudVision inventory device.
4. **Given** every device in a CloudVision Managed fabric has a serial number and exists in CloudVision inventory, **When** the check runs, **Then** the fabric is eligible for CloudVision configuration validation.
5. **Given** a CloudVision Managed fabric passes authentication, serial-number, and inventory eligibility checks but has no generated structured-config artifacts, **When** the check runs, **Then** it records that no generated configurations are available and does not create or build a CloudVision validation workspace.

---

### User Story 3 - Reuse and Track Proposed-Change Workspaces (Priority: P3)

As an operator rerunning proposed-change validation, I need each proposed change and fabric to map to a stable CloudVision workspace, so repeated validation updates the same workspace and concurrent changes do not collide.

**Why this priority**: Stable workspace identity makes reruns predictable, avoids workspace sprawl, and lets reviewers correlate Infrahub validations with CloudVision state.

**Independent Test**: Can be tested by running the same proposed-change validation more than once for the same fabric, then running a separate proposed change for the same fabric and comparing workspace identities and tracking records.

**Acceptance Scenarios**:

1. **Given** the same proposed change and fabric are validated more than once, **When** the check runs, **Then** it reuses the same CloudVision workspace identity.
2. **Given** two open proposed changes target the same fabric, **When** both validations run, **Then** each proposed change receives a different CloudVision workspace identity.
3. **Given** proposed-change name and description metadata are available, **When** the workspace is created or updated, **Then** the workspace display name includes the proposed-change name and fabric name, and the description uses the proposed-change description.
4. **Given** proposed-change metadata is incomplete or unavailable, **When** the workspace is created or updated, **Then** the check uses deterministic fallback metadata derived from the proposed-change identity or source branch and the fabric name, then continues validation.

---

### User Story 4 - Preserve a Clear Scope Boundary for Deployment (Priority: P4)

As a change manager, I need validation to build CloudVision workspaces without submitting them after merge, so workspace submission can be designed separately with explicit operator choice and failure handling.

**Why this priority**: Submission changes production state. Combining validation and deployment without a separate workflow could merge an Infrahub proposed change before CloudVision submission succeeds.

**Independent Test**: Can be tested by running successful validation and verifying that the resulting CloudVision workspace is built for review but not submitted as part of this check.

**Acceptance Scenarios**:

1. **Given** CloudVision validation succeeds, **When** the proposed-change check completes, **Then** the workspace remains available for review and is not submitted by this feature.
2. **Given** a future workflow needs workspace submission or abandonment on proposed-change lifecycle events, **When** that work is planned, **Then** it is handled in a separate feature with its own operator choice and failure-handling requirements.

### Edge Cases

- No fabrics in the proposed change are marked CloudVision Managed; the check skips CloudVision configuration validation without requiring CloudVision authentication.
- CloudVision Managed is absent on existing fabric records during rollout; the value is treated as false through the fabric-level default.
- At least one fabric in the proposed change is marked CloudVision Managed and CloudVision credentials, authentication, or connectivity fail during initial runtime setup; the check fails before evaluating device serial numbers, inventory, or generated configuration.
- After CloudVision runtime setup succeeds, the target fabric query returns no fabric node; the check records that no fabric was found and does not fail the proposed change.
- The target fabric exists and CloudVision Managed is false; the check records that CloudVision validation is disabled for the fabric and does not evaluate serial numbers, CloudVision inventory, or generated configuration.
- A CloudVision Managed fabric has no devices; after successful CloudVision authentication, serial-number and inventory eligibility pass with zero devices and workspace validation is skipped with an informational result.
- A CloudVision Managed fabric has devices but no generated EOS configs; after successful CloudVision authentication, serial-number, and inventory checks, the check records that no generated configurations were found and does not run workspace validation.
- Device relationships such as pod, parent fabric, AVD artifact, or structured-config file are absent; unrelated devices are ignored during fabric scoping, but every device confirmed to belong to a CloudVision Managed fabric remains subject to serial-number and inventory eligibility checks.
- Structured-config files for a device selected for workspace validation cannot be downloaded, decoded, or rendered; the check blocks the proposed change with a clear device-specific error instead of skipping validation for that device.
- CloudVision workspace build operations fail; the check fails with a clear message rather than a traceback.
- CloudVision inventory does not contain one or more devices from a CloudVision Managed fabric; the check fails before configuration validation and lists the devices missing from inventory.
- An existing deterministic workspace is already built or otherwise not pending; the check returns it to a pending state before revalidating the proposed change.
- The workspace tracking schema is not loaded in the target Infrahub environment; CloudVision validation still runs and tracking is skipped without blocking the check.
- Proposed-change metadata is unavailable from the check initializer; the check attempts to identify the open proposed change by source branch, including a short branch-name fallback for `feat/` branches.
- Proposed-change deletion, workspace abandonment after deletion, and post-merge workspace submission are out of scope for this validation check.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The NetworkFabric data model MUST expose a fabric-level Boolean labeled CloudVision Managed, with a default value of false so existing and newly created fabrics skip CloudVision validation unless explicitly enabled.
- **FR-002**: The check MUST run as a targeted proposed-change validation for fabric targets and MUST evaluate each target fabric's CloudVision Managed value before requiring CloudVision runtime setup.
- **FR-003**: When a target fabric has CloudVision Managed set to false, the check MUST skip CloudVision configuration validation for that fabric with an informational result and MUST NOT fail because CloudVision credentials, device serial numbers, CloudVision inventory, generated configs, or workspaces are absent.
- **FR-004**: For each targeted check invocation, if the target fabric has CloudVision Managed set to true, the check MUST perform eligibility validation in this order: authenticate to CloudVision, verify every device in the managed fabric has a serial number, verify every device in the managed fabric exists in CloudVision inventory.
- **FR-005**: The check MUST block the proposed change when required CloudVision credentials are missing or CloudVision authentication cannot be established for a proposed change containing at least one CloudVision Managed fabric.
- **FR-006**: For each CloudVision Managed fabric, the check MUST gather the fabric identity, every device in that fabric, each device serial number, CloudVision inventory membership, and generated structured-config artifact references needed for configuration validation.
- **FR-007**: For each CloudVision Managed fabric, the check MUST fail before configuration validation when any device in that fabric is missing a serial number, and the failure message MUST list every device missing a serial number.
- **FR-008**: For each CloudVision Managed fabric, the check MUST fail before configuration validation when any serial-numbered fabric device is absent from CloudVision inventory, and the failure message MUST list every device missing from inventory.
- **FR-009**: After CloudVision authentication, serial-number validation, and inventory validation succeed, the check MUST convert each selected device's generated structured configuration into EOS CLI configuration for CloudVision validation.
- **FR-010**: After CloudVision eligibility succeeds, the check MUST skip workspace validation with an informational result when the target fabric has no generated structured-config artifacts to validate.
- **FR-011**: The check MUST ignore devices outside the target fabric and MUST avoid runtime errors when unrelated or optional relationships are absent.
- **FR-012**: The check MUST block the proposed change when a selected device's structured-config file cannot be downloaded, decoded, or rendered into EOS CLI configuration, and the failure message MUST identify the affected device.
- **FR-013**: The check MUST create or update a deterministic CloudVision workspace per proposed change and fabric, so reruns reuse the same workspace and concurrent proposed changes do not collide.
- **FR-014**: The CloudVision workspace display name MUST include the proposed-change name and fabric name.
- **FR-015**: The CloudVision workspace description MUST use the proposed-change description when present. When absent, it MUST use `Infrahub CloudVision validation for proposed change <proposed-change-identity> on fabric <fabric-name>`.
- **FR-016**: The check MUST return an existing deterministic CloudVision workspace to a pending/buildable state before deploying configs and requesting a workspace build.
- **FR-017**: The check MUST block the proposed change when CloudVision connection, deployment, or build validation fails.
- **FR-018**: The check MUST record successful validation with the built workspace location, the count of deployed device configs, and the count of CloudVision inventory-confirmed devices.
- **FR-019**: The check MUST create or update Infrahub workspace tracking for the validated workspace when the tracking schema is available, including workspace identity, proposed-change identity, status, and related fabric.
- **FR-020**: The check MUST continue CloudVision validation when workspace tracking is unavailable because the tracking schema is not loaded.
- **FR-021**: The check MUST use proposed-change metadata from the check context when available and MUST fall back to source-branch lookup when the context lacks proposed-change identity.
- **FR-022**: The check MUST NOT submit CloudVision workspaces, abandon workspaces on proposed-change deletion, or automate post-merge deployment as part of this feature.
- **FR-023**: The check registration MUST keep the check definition, query registration, target group, and target parameters aligned so the validation receives the intended fabric data.
- **FR-024**: After CloudVision runtime setup succeeds, when the target fabric is not found, the check MUST record an informational result and MUST NOT fail the proposed change solely because the target fabric is absent.

### Check Architecture

- **Check Type**: Targeted
- **Target Group**: `fabrics`
- **Query Parameters**: `name` mapped from the fabric target's `name__value`

### Key Files

- **Fabric schema**: `schemas/logical_design.yml`
- **Python check**: `checks/cv_config_check.py`
- **GraphQL query**: `checks/cv_config_check.gql`
- **Generated query model**: `checks/cv_config_check_query.py`
- **Shared utilities**: `checks/cv_helpers.py`
- **Configuration**: `.infrahub.yml` and `repository_checks.yml`
- **Workspace tracking schema**: `schemas/cv/cv.yml`
- **Unit coverage**: `tests/unit/test_cv_integration.py`
- **User documentation**: `docs/docs/cloudvision.md`

### Key Entities *(include if check involves specific Infrahub schema types)*

- **NetworkFabric**: The fabric selected for proposed-change validation. Its CloudVision Managed Boolean determines whether CloudVision configuration validation applies to the fabric.
- **NetworkPod**: The relationship path used to associate devices with their parent fabric.
- **DcimDevice**: A network device in a fabric. Every device in a CloudVision Managed fabric must have a serial number and must exist in CloudVision inventory before configuration validation can run.
- **AvdArtifact**: The per-device artifact container that links a device to generated AVD files.
- **AvdStructuredConfigFile**: The generated structured configuration source used to produce EOS CLI configuration for CloudVision validation.
- **CloudvisionWorkspace**: The optional Infrahub tracking object for deterministic CloudVision workspaces created by validation.
- **CoreProposedChange**: The source of user-facing proposed-change identity, name, source branch, and description for workspace naming and tracking.
- **CloudVision Workspace**: The external validation workspace that receives device configlets and is built before the Infrahub proposed change can merge.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a proposed change with a CloudVision Managed fabric whose devices all have serial numbers, exist in CloudVision inventory, and have valid generated configs, validation creates or updates one CloudVision workspace per fabric and reports success within 10 minutes for a representative fabric of up to 50 devices.
- **SC-002**: For a proposed change where every target fabric has CloudVision Managed set to false, validation skips CloudVision configuration validation 100% of the time without requiring CloudVision credentials, serial numbers, inventory membership, or generated configs.
- **SC-003**: For a targeted check invocation whose target fabric is CloudVision Managed, missing CloudVision credentials, CloudVision authentication failures, CloudVision connection failures, or CloudVision workspace build failures block the proposed change 100% of the time with a human-readable error message.
- **SC-004**: For a CloudVision Managed fabric with one or more devices missing serial numbers, validation fails before configuration validation and lists every missing device name in the failure message.
- **SC-005**: For a CloudVision Managed fabric with one or more serial-numbered devices absent from CloudVision inventory, validation fails before configuration validation and lists every missing inventory device name in the failure message.
- **SC-006**: For fixture data with missing pod, artifact, parent fabric, or structured-config relationships outside the target fabric's managed device set, validation completes without runtime exceptions and does not falsely fail solely because unrelated optional relationships are absent.
- **SC-007**: For the same proposed change and fabric, repeated validation produces the same workspace identity on every run; for two different proposed changes on the same fabric, workspace identities differ.
- **SC-008**: For successful validation, the workspace is built for review but not submitted, preserving a separate deployment decision after merge.
- **SC-009**: Maintainers can verify the core behavior with automated tests covering CloudVision Managed gating, device serial-number enforcement, CloudVision inventory enforcement, workspace identity and metadata, CloudVision runtime configuration, source-branch proposed-change lookup, and branch-scoped structured-config retrieval.

## Assumptions

- The AVD generator chain has already produced structured-config artifacts for devices intended to be validated.
- CloudVision Managed defaults to false for existing and new fabrics unless an operator explicitly enables it.
- In a CloudVision Managed fabric, every device in the fabric must be identifiable by serial number and present in CloudVision inventory before any generated configuration is validated.
- CloudVision configuration validation deploys only generated structured configs after the fabric has passed CloudVision authentication, serial-number, and inventory eligibility checks.
- CloudVision credentials and optional proxy settings are provided to the Infrahub task-worker runtime through environment configuration, and credential/authentication validation happens before serial-number, inventory, or workspace checks when at least one fabric is CloudVision Managed.
- The target `fabrics` group exists and contains the fabrics that should trigger validation.
- The workspace tracking schema may be absent in some environments during rollout; missing tracking must not prevent CloudVision validation.
- Post-merge workspace submission, operator choice for submission, deletion-time workspace abandonment, and Semaphore-based deployment orchestration are separate future features.
