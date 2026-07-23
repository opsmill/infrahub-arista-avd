# Contract: Proposed-Change Thread Notifications

## Purpose

Create and update the proposed-change Overview conversation for the CloudVision
workspace lifecycle.

## Thread Identity

- Concrete type: `CoreChangeThread`
- Relationship to proposed change: `change`
- Deterministic label: `CloudVision workspace <workspace_id>`
- Resolution state:
  - `resolved=false` when created, pending, or failed
  - `resolved=true` only after a successful submission comment is saved

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
CloudVision workspace <workspace_id> submitted successfully. Change control: <change_control_id> <change_control_url_if_available>
```

Rules:

- Must include `change_control_id` when CloudVision returns one.
- Must include `change_control_url` when a reliable URL can be derived.
- The thread is marked resolved only after this comment is saved.

### Submission Failure

Required when post-merge submission fails:

```text
Infrahub proposed change <proposed_change_id> was merged, but CloudVision workspace <workspace_id> was not submitted for fabric <fabric_name>: <reason>
```

Rules:

- Must include proposed-change ID.
- Must include workspace ID when known.
- Must include fabric identity when available.
- Must keep the thread unresolved.

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
- If comment creation fails, log the full outcome with proposed-change ID,
  workspace ID, and failure reason.
- If success comment succeeds but resolve fails, log the resolve failure and
  keep `CloudvisionWorkspace.status` aligned with CloudVision submission state.
