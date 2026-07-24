# Contract: CloudvisionWorkspace Tracking Schema

## Purpose

Persist enough Infrahub metadata to correlate proposed changes, CloudVision workspaces, user-visible threads, and CustomWebhook submission outcomes.

## Schema Kind

- Kind: `CloudvisionWorkspace`
- File: `schemas/cv/cv.yml`
- Human-friendly ID: `workspace_id__value`
- Existing uniqueness: `workspace_id` unique

## Fields

Required existing fields:

| Field | Kind | Rules |
| ----- | ---- | ----- |
| `name` | `Text` | CloudVision display name |
| `workspace_id` | `Text` | Unique deterministic CloudVision workspace ID |
| `status` | `Dropdown` | Tracks lifecycle state |
| `fabric` | relationship to `NetworkFabric` | Required fabric correlation |

Optional fields:

| Field | Kind | Rules |
| ----- | ---- | ----- |
| `proposed_change_id` | `Text` | Primary correlation key for CustomWebhook submission |
| `workspace_url` | `URL` | Exact URL shown in the first thread comment |
| `thread_id` | `Text` | CoreChangeThread ID for idempotent updates |
| `last_submission_error` | `TextArea` | Human-readable last failure |
| `last_submission_attempt_at` | `DateTime` | Last submission attempt timestamp |
| `submitted_at` | `DateTime` | Successful submission timestamp |

Existing `change_control_id` or `change_control_url` fields, if retained from earlier work, are optional implementation details and are not required by this phase. They must not imply change-control management, approval scheduling, or Semaphore execution.

## Status Choices

Required choices:

- `pending`
- `built`
- `submitted`
- `abandoned`
- `submit_failed`

## Validation Rules

- Optional fields must be added as `optional: true` so existing tracking objects remain valid.
- `workspace_id` remains the primary unique identity.
- `proposed_change_id` plus `fabric` plus `workspace_id` must be sufficient to distinguish concurrent proposed changes against the same fabric.
- `thread_id` must be updated after the thread is created or reused.
- `status=submitted` means the CustomWebhook handler must not resubmit the workspace.
- `status=submit_failed` means retries may attempt the same workspace again.
- Schema changes require schema check and protocol regeneration.
- Do not hand-edit `src/solution_arista_avd/protocols.py`.
