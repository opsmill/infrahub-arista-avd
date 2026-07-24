# Contract: CustomWebhook Submission Processing

## Purpose

Process the CloudVision workspace submission CustomWebhook event by resolving the workspace linked to the submitted proposed change and submitting that existing workspace exactly once.

## Entry Points

CustomWebhook event adapter:

```python
async def submit_linked_workspace_for_custom_webhook(
    client: InfrahubClient,
    event: Mapping[str, Any],
    *,
    branch: str = "main",
) -> SubmissionResult:
    ...
```

Shared handler:

```python
async def submit_linked_workspace_for_proposed_change(
    client: InfrahubClient,
    proposed_change_id: str,
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
| `client` | Yes | Infrahub SDK client authenticated to the target environment |
| `event` | CustomWebhook adapter only | Raw CustomWebhook payload |
| `proposed_change_id` | Yes | Event payload or manual retry argument |
| `branch` | Yes | Branch containing workspace tracking; defaults to `main` for manual retry |
| `check_name` | Recommended | Event payload; must be `cv-config-validation` when present |

## Behavior

1. Resolve `proposed_change_id` and branch from the CustomWebhook event.
2. Reject events that explicitly identify a different check than `cv-config-validation`.
3. Query `CloudvisionWorkspace` by `proposed_change_id__value` on the selected branch.
4. If zero records are found, return `status=skipped` and record an informational outcome when possible.
5. If more than one record is found, return `status=failed` and record an ambiguity outcome without calling CloudVision.
6. If exactly one record is found, submit only that existing CloudVision workspace when it is submit-ready.
7. Return a typed `SubmissionResult`.

## Output

`SubmissionResult` fields:

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `submitted`, `already_submitted`, `skipped`, or `failed` |
| `proposed_change_id` | `str` | Proposed change processed |
| `workspace_id` | `str | None` | Workspace processed when known |
| `fabric_name` | `str | None` | Fabric context when known |
| `thread_id` | `str | None` | Thread updated when known |
| `message` | `str` | Safe human-readable outcome |

## Prohibited Behavior

- Must not create a new CloudVision workspace.
- Must not rebuild the workspace.
- Must not force-submit by default.
- Must not depend on CloudVision change-control management or Semaphore playbooks.
- Must not duplicate submission when Infrahub or CloudVision already reports the workspace as submitted.
- Must not treat the placeholder URL as a real production endpoint in this phase.
