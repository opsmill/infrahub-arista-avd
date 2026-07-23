# Contract: Direct Post-Merge Submission Handler

## Purpose

Submit the existing CloudVision workspace linked to a merged Infrahub proposed
change without requiring a separate webhook receiver service.

## Entry Points

Primary handler:

```python
async def submit_linked_workspace_for_proposed_change(
    client: InfrahubClient,
    proposed_change_id: str,
    *,
    branch: str = "main",
) -> SubmissionResult:
    ...
```

Event adapter:

```python
async def submit_linked_workspace_for_merged_event(
    client: InfrahubClient,
    event: Mapping[str, Any],
    *,
    branch: str = "main",
) -> SubmissionResult:
    ...
```

Manual retry adapter:

```bash
uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main
```

## Inputs

| Field | Required | Source |
| ----- | -------- | ------ |
| `client` | Yes | Infrahub SDK client authenticated to the destination environment |
| `proposed_change_id` | Yes | Post-merge/API execution path, event payload, or manual retry argument |
| `branch` | Yes | Destination branch containing merged tracking objects; defaults to `main` |
| `event` | Adapter only | Optional merged proposed-change event payload |

## Behavior

1. Resolve `proposed_change_id` and destination branch.
2. Query `CloudvisionWorkspace` by `proposed_change_id__value` on the destination
   branch.
3. If zero records are found, return `status=skipped` and record an
   informational outcome when possible.
4. If more than one record is found, return `status=failed` and record an
   ambiguity outcome without calling CloudVision.
5. If exactly one record is found, submit only that existing CloudVision
   workspace when it is submit-ready.
6. Return a typed `SubmissionResult`.

## Output

`SubmissionResult` fields:

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `submitted`, `already_submitted`, `skipped`, or `failed` |
| `proposed_change_id` | `str` | Proposed change processed |
| `workspace_id` | `str | None` | Workspace processed when known |
| `fabric_name` | `str | None` | Fabric context when known |
| `thread_id` | `str | None` | Thread updated when known |
| `change_control_id` | `str | None` | CloudVision change control ID when available |
| `message` | `str` | Safe human-readable outcome |

## Prohibited Behavior

- Must not create a new CloudVision workspace after merge.
- Must not rebuild the workspace after merge.
- Must not force-submit by default.
- Must not depend on a repository-loaded placeholder webhook registration.
- Must not duplicate submission when Infrahub or CloudVision already reports the
  workspace as submitted.
