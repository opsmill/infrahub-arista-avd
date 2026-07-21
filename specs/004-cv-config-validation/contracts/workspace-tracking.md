# Contract: CloudVision Workspace Tracking

## Schema Node

The optional tracking object is `CloudvisionWorkspace`.

## Fields

| Field | Type | Required | Contract |
| ----- | ---- | -------- | -------- |
| `name` | Text | Yes | CloudVision workspace display name |
| `workspace_id` | Text | Yes | Deterministic CloudVision workspace ID; unique |
| `proposed_change_id` | Text | No | Infrahub proposed-change identity |
| `status` | Dropdown | Yes | One of `pending`, `built`, `submitted`, `abandoned` |
| `fabric` | Relationship | Yes | Related `NetworkFabric` |

## Status Semantics

| Status | Meaning |
| ------ | ------- |
| `pending` | Workspace exists and is ready for validation changes |
| `built` | Workspace built successfully for validation |
| `submitted` | Reserved for future post-merge workflow |
| `abandoned` | Workspace is no longer active or validation failed after workspace operations |

## Upsert Behavior

When tracking schema exists:

1. Lookup by `workspace_id`.
2. If found, update `status` and `proposed_change_id`.
3. If not found, create a new tracking object with name, workspace ID, proposed-change ID, status, and fabric.

When tracking schema is absent:

1. Do not block CloudVision validation.
2. Log server-side diagnostic context for maintainers.

## Acceptance Criteria

- `workspace_id` is the human-friendly and uniqueness identity.
- Repeated validation for the same proposed change and fabric updates one tracking object.
- Different proposed changes on the same fabric use different tracking objects.
- Tracking absence never masks CloudVision validation success or failure.
