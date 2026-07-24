# Contract: CloudVision Workspace Tracking

## Schema Node

The optional tracking object is `CloudvisionWorkspace`.

## Fields

| Field | Type | Required | Contract |
| ----- | ---- | -------- | -------- |
| `name` | Text | Yes | CloudVision workspace display name |
| `workspace_id` | Text | Yes | Deterministic CloudVision workspace ID; unique |
| `proposed_change_id` | Text | No | Infrahub proposed-change identity |
| `workspace_url` | URL | No | Exact CloudVision workspace URL shown to reviewers |
| `thread_id` | Text | No | Proposed-change overview thread used for workspace and submission comments |
| `status` | Dropdown | Yes | One of `pending`, `built`, `submitted`, `abandoned`, `submit_failed` |
| `last_submission_error` | TextArea | No | Latest failed CustomWebhook submission reason |
| `last_submission_attempt_at` | DateTime | No | Latest CustomWebhook submission attempt timestamp |
| `submitted_at` | DateTime | No | Successful CloudVision workspace submission timestamp |
| `fabric` | Relationship | Yes | Related `NetworkFabric` |

## Status Semantics

| Status | Meaning |
| ------ | ------- |
| `pending` | Workspace exists and is ready for validation changes |
| `built` | Workspace built successfully for validation and may be submit-ready |
| `submitted` | Workspace submission already completed |
| `abandoned` | Workspace is no longer active or validation failed after workspace operations |
| `submit_failed` | Last CustomWebhook submission attempt failed; retry may try the same workspace again |

## Upsert Behavior

When tracking schema exists:

1. Lookup by `workspace_id`.
2. If found, update `status`, `proposed_change_id`, URL, and thread metadata.
3. If not found, create a new tracking object with name, workspace ID, proposed-change ID, status, URL when available, and fabric.

When tracking schema is absent:

1. Do not block CloudVision validation.
2. Log server-side diagnostic context for maintainers.

## Acceptance Criteria

- `workspace_id` is the human-friendly and uniqueness identity.
- Repeated validation for the same proposed change and fabric updates one tracking object.
- Different proposed changes on the same fabric use different tracking objects.
- Tracking absence never masks CloudVision validation success or failure.
- CustomWebhook submission resolves by proposed-change ID and never creates a replacement workspace.
