# Contract: Proposed-Change Thread Notifications

## Purpose

Create and update the proposed-change Overview conversation for the CloudVision workspace lifecycle.

## Thread Identity

- Concrete type: `CoreChangeThread`
- Relationship to proposed change: `change`
- Deterministic label: `CloudVision workspace <workspace_id>`
- Resolution state:
  - `resolved=false` when created, pending, failed, or ambiguous
  - `resolved=true` only after a successful, already-complete, or safe skip comment is saved

Lookup order:

1. Use `CloudvisionWorkspace.thread_id` when present.
2. Query `CoreChangeThread` by `change__ids` and `label__value`.
3. Create a new `CoreChangeThread` when no existing thread is found.

## Comment Types

### Workspace URL

Required after workspace creation or reuse:

```text
CloudVision workspace for proposed change <proposed_change_id> and fabric <fabric_name>: <workspace_url>
```

Rules:

- Must include the exact workspace URL.
- Must not be duplicated for the same proposed-change/workspace pair.

### Submission Success

Required after CloudVision submission succeeds:

```text
CloudVision workspace <workspace_id> submitted successfully. Workspace: <workspace_url_if_available>
```

Rules:

- Must include workspace identity.
- Must include a user-openable workspace URL when available.
- The thread is marked resolved only after this comment is saved.
- Must not claim that CloudVision change-control approvals, scheduling, or Semaphore deployment completed.

### Already Complete

Required when the workspace is already submitted:

```text
CloudVision workspace <workspace_id> was already submitted. No duplicate submission was issued.
```

Rules:

- Must not issue another CloudVision submission.
- The thread may be resolved after the comment is saved.

### Submission Failure

Required when CustomWebhook processing fails after proposed-change submission:

```text
Proposed change <proposed_change_id> was submitted, but CloudVision workspace <workspace_id> was not submitted for fabric <fabric_name>: <reason>
```

Rules:

- Must include proposed-change ID.
- Must include workspace ID when known.
- Must include fabric identity when available.
- Must keep the thread unresolved.

### Skip Or Ambiguity

Required when no linked workspace or multiple linked workspaces are found:

```text
No CloudVision workspace was submitted for proposed change <proposed_change_id>: <reason>
```

Rules:

- No linked workspace is informational and may resolve the outcome thread.
- Multiple linked workspaces is an ambiguity failure and must remain unresolved.
- The comment must state that no CloudVision submission was attempted.

## Mutation Shape

Create a thread:

```graphql
mutation CreateCloudVisionWorkspaceThread($change: RelatedNodeInput!, $label: String!) {
  CoreChangeThreadCreate(
    data: {
      change: $change
      label: { value: $label }
      resolved: { value: false }
    }
  ) {
    ok
    object {
      id
      label { value }
      resolved { value }
    }
  }
}
```

Add a comment:

```graphql
mutation AddCloudVisionWorkspaceThreadComment($thread: RelatedNodeInput!, $text: String!) {
  CoreThreadCommentCreate(
    data: {
      thread: $thread
      text: { value: $text }
    }
  ) {
    ok
    object {
      id
      text { value }
    }
  }
}
```

Resolve a thread:

```graphql
mutation ResolveCloudVisionWorkspaceThread($id: String!) {
  CoreChangeThreadUpdate(
    data: {
      id: $id
      resolved: { value: true }
    }
  ) {
    ok
    object {
      id
      resolved { value }
    }
  }
}
```

## Error Handling

- If thread lookup fails, create a new deterministic thread and continue.
- If comment creation fails, log the full outcome with proposed-change ID, workspace ID, fabric, and failure reason.
- If success comment succeeds but resolve fails, log the resolve failure and keep `CloudvisionWorkspace.status` aligned with CloudVision submission state.
