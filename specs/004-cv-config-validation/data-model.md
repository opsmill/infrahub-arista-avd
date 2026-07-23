# Data Model: CloudVision Configuration Validation

## NetworkFabric

**Purpose**: The target fabric selected by the proposed-change check and associated with a CloudVision workspace.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.
- `name`: Fabric name used as the targeted check parameter and in CloudVision workspace naming.
- `cloudvision_managed`: Boolean opt-in for CloudVision configuration validation; defaults to `false`.

**Relationships**:

- Parent of pods that contain candidate devices.
- Related from `CloudvisionWorkspace.fabric` for optional workspace tracking and submission traceability.

**Validation rules**:

- The validation check runs once per fabric target.
- If the target query returns no fabric node, validation records an informational result and exits without contacting CloudVision.
- If `cloudvision_managed` is false or absent, validation records an informational result and exits without requiring CloudVision credentials, device serial numbers, inventory membership, structured configs, workspaces, threads, or submission state.
- If `cloudvision_managed` is true, validation authenticates to CloudVision before evaluating device identity or generated configs.
- Fabric identity is included in submission outcome comments and fallback logs when available.

## NetworkPod

**Purpose**: The relationship path connecting devices to their parent fabric.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.

**Relationships**:

- `parent` points to the fabric that scopes a device.

**Validation rules**:

- Devices missing pod or parent fabric relationships are not considered members of the target fabric and must be ignored without failure.

## DcimDevice

**Purpose**: A candidate device whose generated EOS configuration may be validated in CloudVision.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.
- `name`: Hostname and user-facing device identifier.
- `serial`: CloudVision inventory identity.

**Relationships**:

- `pod` connects the device to a fabric through its parent.
- `avd_artifact` connects the device to generated AVD files.

**Validation rules**:

- A device is part of the managed-fabric eligibility set when it belongs to the target fabric, regardless of whether it has generated structured-config artifacts.
- Every device in the managed-fabric eligibility set must have a serial number.
- Every serial-numbered device in the managed-fabric eligibility set must exist in CloudVision inventory before workspace validation starts.
- Every targeted CloudVision device in the managed-fabric eligibility set must be active in CloudVision; inactive devices fail validation even if workspace build succeeds.
- Devices outside the target fabric are ignored.
- Devices with structured-config artifacts become the workspace validation set only after authentication, serial-number, inventory, and active-state eligibility pass for the whole managed fabric.

## AvdArtifact

**Purpose**: Per-device artifact container for generated AVD files.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.

**Relationships**:

- Parent or container relationship from a device.
- `structured_config_file` points to the generated structured config used for EOS rendering.

**Validation rules**:

- Missing artifact relationships do not remove a device from managed-fabric serial-number, inventory, or active-state eligibility.
- Devices without an artifact or without a structured-config file are omitted from workspace config deployment after managed-fabric eligibility passes.

## AvdStructuredConfigFile

**Purpose**: Generated structured configuration source for a device.

**Fields used by this feature**:

- `id`: Stable Infrahub file object identity.
- File content: JSON structured config downloaded from the check branch.

**Relationships**:

- Child of a device's `AvdArtifact`.

**Validation rules**:

- File content must be downloadable from the check branch for each device selected for workspace config deployment.
- Missing file nodes mean no config is deployed for that device, but do not bypass serial-number, inventory, or active-state eligibility.
- If a selected structured-config file cannot be downloaded, decoded, or rendered to EOS CLI, validation blocks the proposed change with a device-specific failure message.

## CoreProposedChange

**Purpose**: The Infrahub proposed change whose identity scopes workspace validation, thread comments, and direct post-merge submission.

**Fields used by this feature**:

- `id`: Stable proposed-change identity used to correlate workspace tracking, workspace identity, threads, and post-merge events.
- `name`: User-facing name used in workspace names and comments.
- `description`: User-facing description used in CloudVision workspace descriptions.
- `source_branch`: Branch that produced the workspace.
- `destination_branch`: Branch used for tracking lookup after merge.
- `state`: Used to distinguish pre-merge validation from merged post-processing.

**Relationships**:

- Owns `CoreChangeThread` overview threads used for workspace URL and submission outcome comments.
- May be resolved from check initializer metadata, proposed-change ID, or source branch.

**Validation rules**:

- Workspace identity and post-merge submission must use proposed-change ID as the primary correlation key.
- Missing initializer identity must fall back to open proposed-change source branch lookup when possible.
- If a proposed-change ID cannot be resolved during post-merge handling, no CloudVision submission is attempted and an operational outcome is logged.

## CloudvisionWorkspace

**Purpose**: Infrahub tracking object for a CloudVision workspace linked to a proposed change and fabric.

**Fields**:

- `id`: Infrahub node identity used for updates.
- `name`: Human-readable CloudVision workspace name.
- `workspace_id`: Deterministic CloudVision workspace ID; unique and human-friendly.
- `proposed_change_id`: Infrahub proposed-change ID that created the workspace.
- `status`: Workspace lifecycle state.
- `workspace_url`: Exact CloudVision workspace URL displayed to users when available.
- `thread_id`: `CoreChangeThread` ID used for idempotent comment updates.
- `change_control_id`: CloudVision change control ID returned by successful submission.
- `change_control_url`: User-openable change-control URL when available.
- `last_submission_error`: Last human-readable submission failure.
- `last_submission_attempt_at`: Timestamp of most recent failed or attempted submission.
- `submitted_at`: Timestamp of successful submission.

**Relationships**:

- `fabric`: The `NetworkFabric` validated by this workspace.

**State transitions**:

```text
pending -> built
pending -> abandoned
built -> pending -> built
built -> submitted
built -> submit_failed
submit_failed -> submitted
submit_failed -> submit_failed
submitted -> submitted
pending/abandoned/unknown -> submit_failed   # direct submission refuses them
```

**Validation rules**:

- Tracking is created or updated only when the schema exists.
- Missing tracking schema must not block CloudVision validation.
- `workspace_id` is unique, so reruns update the same tracking object.
- Lookup by `proposed_change_id` on the destination branch must produce exactly one record before CloudVision submission.
- `status=submitted` is complete and must not trigger another submit request.
- Only `built` and `submit_failed` are submit-ready.
- Missing `workspace_id` is a failure outcome, not a reason to create a new workspace.
- Zero linked records skip submission with an informational outcome.
- Multiple linked records block submission with an ambiguity outcome.

## CoreChangeThread

**Purpose**: The proposed-change overview conversation grouping comments for one linked CloudVision workspace or submission outcome.

**Fields used by this feature**:

- `id`: Stored on `CloudvisionWorkspace.thread_id` after creation or reuse.
- `label`: Deterministic label containing the workspace ID, or a submission outcome label when no exact workspace exists.
- `resolved`: `false` while workspace submission is pending, failed, or ambiguous; `true` only after a success, already-complete, or no-workspace skip outcome is saved.

**Relationships**:

- `change`: The owning `CoreProposedChange`.
- `comments`: Ordered `CoreThreadComment` entries for URL, success, failure, already-submitted, skip, or ambiguity outcomes.

**State transitions**:

```text
missing -> open
open -> resolved
resolved -> open      # only if a retry discovers a new failure before success
```

**Validation rules**:

- Repeated workspace creation for the same proposed change and workspace must reuse the existing thread by stored `thread_id` or deterministic label.
- A failure or ambiguity comment must leave `resolved` set to `false`.
- A success or already-complete comment must be written before the thread is marked resolved.

## CoreThreadComment

**Purpose**: User-visible text shown in the proposed-change Overview.

**Fields used by this feature**:

- `id`: Stable Infrahub comment identity.
- `text`: Comment body.

**Relationships**:

- `thread`: The `CoreChangeThread` that owns the comment.

**Validation rules**:

- The workspace URL comment must contain the exact CloudVision workspace URL.
- The success comment must state that CloudVision submission succeeded and must include the change control ID, plus a URL when one is available.
- Already-complete comments must explain that no duplicate CloudVision submission was issued.
- Skip comments must explain that no linked workspace was found and no submission was attempted.
- Ambiguity comments must list candidate workspace identities and state that no submission was attempted.
- Failure comments must include proposed-change ID, workspace ID, fabric when available, and a human-readable reason.
- Retry logic must avoid duplicate workspace URL comments for the same workspace.

## CloudVision Workspace

**Purpose**: External CloudVision workspace used to build and validate device configlets before merge and submit the already-built workspace after merge.

**Fields**:

- Workspace ID: Deterministic from proposed-change identity and fabric name.
- Display name: Includes proposed-change name and fabric name.
- Description: Proposed-change description or safe fallback.
- Workspace URL: Displayed in the proposed-change Overview when available.
- Current CloudVision state.
- Submission request ID.
- Submission response status.
- Change control IDs returned after successful submission.

**Relationships**:

- Contains configlets derived from selected devices' generated EOS configs.
- Corresponds to one optional `CloudvisionWorkspace` tracking object.

**State transitions**:

```text
missing -> pending -> built
built -> pending -> built
built -> submitted
submitted -> submitted
```

**Validation rules**:

- Existing non-pending workspaces must be returned to pending before pre-merge config validation.
- Build failure blocks the proposed change.
- A successful build is not sufficient for a passing validation result when any targeted CloudVision device is inactive.
- Pre-merge validation builds but does not submit the workspace.
- Direct post-merge processing submits only the existing linked workspace.
- Direct post-merge processing must not create, rebuild, or force-submit a workspace.
- If CloudVision reports the workspace is already submitted, the Infrahub tracking object is updated to complete without issuing a duplicate submission.
- Authentication, connectivity, rejection, timeout, or missing request ID produce failed outcomes.

## CloudVision Change Control

**Purpose**: External CloudVision change control created by successful workspace submission.

**Fields used by this feature**:

- `change_control_id`: Stable user-identifiable ID.
- `change_control_url`: Optional user-openable URL.

**Relationships**:

- Created from successful submission of one CloudVision workspace.
- Stored on `CloudvisionWorkspace` and referenced in the success comment.

**Validation rules**:

- Success comments must include the ID when CloudVision returns one.
- Missing change-control URL does not fail a successful submission.
- Missing displayable change-control data after a successful submission must be recorded as a limited success detail, not as a failed submission.

## DirectSubmissionRequest

**Purpose**: Runtime input delivered by the post-merge/API execution path or manual retry command.

**Fields**:

- `proposed_change_id`: Required merged proposed-change ID.
- `branch`: Destination branch containing workspace tracking, defaulting to `main`.
- `event`: Optional merged proposed-change event payload when using the adapter.

**Validation rules**:

- Event adapters must extract `proposed_change_id` and destination branch before calling the shared direct handler.
- Manual retry must call the same direct handler, not a separate submission implementation.

## SubmissionResult

**Purpose**: Typed internal outcome returned by the direct submission handler.

**Fields**:

- `status`: `submitted`, `already_submitted`, `skipped`, or `failed`.
- `proposed_change_id`: Proposed change processed.
- `workspace_id`: Workspace processed when known.
- `fabric_name`: Fabric context when known.
- `thread_id`: Thread updated when known.
- `change_control_id`: Change control returned by CloudVision when available.
- `message`: Safe human-readable outcome for comments and logs.

**Validation rules**:

- Every result must be safe to log.
- `skipped` means no CloudVision submission was attempted.
- `failed` includes enough context to troubleshoot after the Infrahub merge has already completed.

## RepositoryLoadedObjects

**Purpose**: Repository YAML objects loaded into Infrahub for triggers, webhooks, checks, and related registrations.

**Fields used by this feature**:

- `kind`: Object kind being loaded.
- `name`: Registration name.
- `url`: External URL for webhook objects when present.
- `shared_key`: Webhook shared secret when present.

**Validation rules**:

- Repository-loaded objects must not contain a placeholder `cloudvision-workspace-submission` `CoreStandardWebhook`.
- Repository-loaded objects must not contain the placeholder receiver URL `http://cloudvision-workspace-submitter:8080/infrahub/proposed-change-merged`.
- Repository-loaded objects must not contain the placeholder shared key `replace-in-deployment` for CloudVision workspace submission.
- If a real deployment later adds a webhook receiver, that belongs to a separate feature or deployment-specific registration with real endpoint ownership.

## Runtime Configuration

**Purpose**: Runtime values needed to connect to CloudVision.

**Fields**:

- `CLOUDVISION_SERVERS`: One or more CloudVision servers.
- `CLOUDVISION_TOKEN`: Preferred token credential.
- `CLOUDVISION_USERNAME` and `CLOUDVISION_PASSWORD`: Alternate credential pair.
- `CLOUDVISION_VERIFY_CERTS`: Optional certificate verification control.
- `CLOUDVISION_PROXY_*`: Optional proxy configuration.
- `CLOUDVISION_CHANGE_CONTROL_URL_TEMPLATE`: Optional template used to render change-control links.

**Validation rules**:

- Servers plus token, or servers plus username/password, are required when CloudVision is contacted.
- Blank optional proxy values are treated as unset.
- Missing required credentials block validation or submission with an actionable error.
