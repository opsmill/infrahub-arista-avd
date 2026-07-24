# Contract: CloudVision Workspace Submission

## Purpose

Submit an existing CloudVision workspace from CustomWebhook processing and capture a safe user-visible outcome without creating, rebuilding, or force-submitting a workspace.

## CloudVision Configuration

Use the existing `get_cloudvision_config()` helper. Required environment:

- `CLOUDVISION_SERVERS`
- `CLOUDVISION_TOKEN`, or `CLOUDVISION_USERNAME` and `CLOUDVISION_PASSWORD`

Optional environment:

- `CLOUDVISION_VERIFY_CERTS`
- `CLOUDVISION_PROXY_HOST`
- `CLOUDVISION_PROXY_PORT`
- `CLOUDVISION_PROXY_USERNAME`
- `CLOUDVISION_PROXY_PASSWORD`

Missing required configuration is a submission failure and must produce a proposed-change failure comment when possible.

## Submission Flow

1. Resolve exactly one linked `CloudvisionWorkspace` by proposed-change ID and branch.
2. Confirm its status is submit-ready: `built` or `submit_failed`.
3. Open `CVClient` with the configured CloudVision connection.
4. Fetch the existing workspace with `get_workspace(workspace_id)`.
5. If the workspace is already submitted, return an already-complete outcome.
6. Submit the existing workspace with non-forced semantics.
7. Wait for the workspace submission response.
8. Update `CloudvisionWorkspace` and the proposed-change thread.

## Rules

- Do not create a workspace during CustomWebhook processing.
- Do not rebuild the workspace during CustomWebhook processing.
- Do not force-submit by default.
- Do not submit if the linked workspace is missing, ambiguous, already submitted, pending, abandoned, or validation-failed.
- Do treat CloudVision rejection, connection failure, authentication failure, and timeout as failed submission outcomes.
- Do not manage CloudVision change controls, approval scheduling, or Semaphore playbooks in this phase.

## Output Mapping

Successful submission:

- `CloudvisionWorkspace.status = submitted`
- `CloudvisionWorkspace.submitted_at = <current timestamp>`
- Thread success comment is appended with workspace identity and URL when available.
- Thread is resolved.

Already submitted:

- No CloudVision submit request is issued.
- `CloudvisionWorkspace.status = submitted`
- Thread receives an already-complete comment if no success comment exists.
- Thread is resolved when the outcome is complete.

Failure:

- `CloudvisionWorkspace.status = submit_failed` when a workspace record exists.
- `CloudvisionWorkspace.last_submission_error = <reason>`
- `CloudvisionWorkspace.last_submission_attempt_at = <current timestamp>`
- Thread failure comment is appended when possible.
- Thread remains unresolved.
