# Contract: CloudVision Workspace Submission

## Purpose

Submit an existing CloudVision workspace and capture the resulting change
control without creating or rebuilding a workspace after Infrahub merge.

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

Missing required configuration is a submission failure and must produce a
proposed-change failure comment when possible.

## Submission Flow

1. Open `CVClient` with the configured CloudVision connection.
2. Fetch the existing workspace with `get_workspace(workspace_id)`.
3. If the workspace is already submitted, return an already-complete outcome.
4. Submit with `submit_workspace(workspace_id, force=False)`.
5. Wait for the submission response with `wait_for_workspace_response()`.
6. On success, read the change control ID from the returned workspace response
   when CloudVision provides one.
7. Update `CloudvisionWorkspace` and the proposed-change thread.

## Rules

- Do not create a workspace after merge.
- Do not force-submit by default.
- Do not rebuild the workspace as part of post-merge submission.
- Do not treat missing change-control URL as failure when the ID is available.
- Do treat CloudVision rejection, connection failure, authentication failure,
  and timeout as failed submission outcomes.

## Output Mapping

Successful submission:

- `CloudvisionWorkspace.status = submitted`
- `CloudvisionWorkspace.change_control_id = <id when available>`
- `CloudvisionWorkspace.change_control_url = <url when available>`
- `CloudvisionWorkspace.submitted_at = <current timestamp>`
- Thread success comment is appended.
- Thread is resolved.

Already submitted:

- No CloudVision submit request is issued.
- `CloudvisionWorkspace.status = submitted`
- Thread receives an already-complete comment if no success comment exists.
- Thread is resolved when the outcome is complete.

Failure:

- `CloudvisionWorkspace.status = submit_failed`
- `CloudvisionWorkspace.last_submission_error = <reason>`
- `CloudvisionWorkspace.last_submission_attempt_at = <current timestamp>`
- Thread failure comment is appended.
- Thread remains unresolved.
