# Contract: Submission Outcomes And Notifications

## Purpose

Record direct CloudVision submission outcomes in proposed-change threads when
possible and in operational logs when thread writes fail.

## Success

Condition:

- Exactly one linked `CloudvisionWorkspace` exists.
- It is submit-ready.
- CloudVision submission succeeds.

Required outcome:

- `CloudvisionWorkspace.status = submitted`
- `submitted_at` is updated.
- `change_control_id` is stored when CloudVision returns one.
- `change_control_url` is stored when derivable.
- A success comment is written to the workspace thread.
- The thread is resolved only after the success comment is saved.
- `SubmissionResult.status = submitted`

## Already Submitted

Condition:

- Infrahub tracking status is `submitted`, or CloudVision reports the workspace
  is already submitted.

Required outcome:

- No duplicate CloudVision submit request is issued.
- `CloudvisionWorkspace.status = submitted`
- An already-complete comment is recorded when possible.
- The thread is resolved.
- `SubmissionResult.status = already_submitted`

## No Linked Workspace

Condition:

- Destination-branch lookup by proposed-change ID returns zero
  `CloudvisionWorkspace` records.

Required outcome:

- No CloudVision call is issued.
- Informational proposed-change outcome is recorded when possible.
- `SubmissionResult.status = skipped`

## Ambiguous Linked Workspaces

Condition:

- Destination-branch lookup by proposed-change ID returns more than one
  `CloudvisionWorkspace` record.

Required outcome:

- No CloudVision call is issued.
- Ambiguity outcome lists the linked workspace identities.
- Outcome thread remains unresolved.
- `SubmissionResult.status = failed`

## Submission Failure

Condition:

- Credentials, connectivity, CloudVision rejection, timeout, missing request ID,
  missing workspace ID, or non-submit-ready status prevents successful
  submission.

Required outcome:

- `CloudvisionWorkspace.status = submit_failed` when a workspace record exists.
- `last_submission_error` and `last_submission_attempt_at` are updated when
  possible.
- Failure comment states that Infrahub merge completed but CloudVision
  submission did not.
- Thread remains unresolved.
- `SubmissionResult.status = failed`

## Fallback Logging

If thread or comment writes fail, the handler must log:

- submission status,
- proposed-change ID,
- workspace ID when known,
- fabric name when known,
- change-control ID when known,
- human-readable reason.
