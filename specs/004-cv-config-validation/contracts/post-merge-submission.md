# Contract: Post-Merge Workspace Submission Handler

## Purpose

Submit exactly one CloudVision workspace after its linked Infrahub proposed
change has merged, then write the outcome to the proposed-change workspace
thread.

## Entry Point

Repository code exposes one typed async handler:

```python
async def submit_linked_workspace_for_proposed_change(
    client: InfrahubClient,
    proposed_change_id: str,
    *,
    branch: str = "main",
) -> SubmissionResult:
    ...
```

Transport adapters may call this handler from:

- an Infrahub `ProposedChangeMergedEvent` webhook receiver,
- an operational task runner,
- an invoke task used for manual retry,
- unit and integration tests.

Business logic must live in the handler, not in the transport adapter.

## Event Input

The post-merge adapter must provide or resolve:

| Field | Required | Source |
| ----- | -------- | ------ |
| `proposed_change_id` | Yes | Event primary node, payload, or explicit CLI argument |
| `source_branch` | No | Event payload when present |
| `merged_by_account_id` | No | Event payload when present |
| `merged_by_account_name` | No | Event payload when present |

If `proposed_change_id` cannot be resolved unambiguously, the handler returns a
failed `SubmissionResult` and does not call CloudVision.

## Workspace Resolution

Query `CloudvisionWorkspace` by `proposed_change_id__value` on the destination
branch after merge.

Outcomes:

| Linked workspaces | Behavior |
| ----------------- | -------- |
| `0` | Do not submit; create an informational proposed-change thread/comment when possible, otherwise log |
| `1` | Continue submission checks |
| `>1` | Do not submit; write an ambiguity failure comment and leave the thread unresolved |

## Submission Preconditions

The single linked workspace must have:

- `workspace_id` present,
- `workspace_url` present or derivable from configured CloudVision server,
- `status` not equal to `submitted`,
- CloudVision state eligible for submission.

If any precondition fails, do not submit and write a failure or already-complete
comment according to the outcome.

## Result Contract

`SubmissionResult` fields:

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `status` | `str` | `submitted`, `already_submitted`, `skipped`, or `failed` |
| `proposed_change_id` | `str` | Proposed change processed |
| `workspace_id` | `str | None` | Workspace processed |
| `fabric_name` | `str | None` | Fabric context |
| `thread_id` | `str | None` | Thread updated |
| `change_control_id` | `str | None` | Change control returned by CloudVision |
| `message` | `str` | Safe human-readable outcome |

## Idempotence Rules

- A workspace already marked `submitted` must not be submitted again.
- A CloudVision workspace already in submitted state must update Infrahub as
  already complete and must not issue another submit request.
- Retry after `submit_failed` may issue a new submit request for the same
  workspace.
- The workspace URL comment must not be duplicated on retry.
- Success after a previous failure must add a success comment and resolve the
  existing thread.

## Failure Rules

- CloudVision authentication, connectivity, rejection, inactive-device, and
  timeout errors return `status=failed`.
- Failure comments must state that Infrahub merge completed but CloudVision
  submission did not.
- Failure comments keep the thread unresolved.
- If Infrahub thread/comment writes fail, the handler logs the complete
  `SubmissionResult` as the fallback notification.
