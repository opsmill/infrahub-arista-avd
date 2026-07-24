# Contract: Placeholder CustomWebhook Registration

## Purpose

Register the CloudVision workspace submission handoff in Infrahub while keeping the URL explicitly placeholder for this phase.

## Required Repository Objects

The repository must load one `CoreCustomWebhook` for CloudVision workspace submission. `CoreCustomWebhook` requires a `transformation` relationship to a `CoreTransformPython`, so the registration also requires a Python transform object.

Illustrative object shape:

```yaml
---
apiVersion: infrahub.app/v1
kind: Object
spec:
  kind: CoreTransformPython
  data:
    - name: cv-workspace-submission-webhook-payload
      repository: test-repository
      query: cv_workspace_submission_webhook
      file_path: "./transforms/cv_workspace_submission_webhook.py"
      class_name: CVWorkspaceSubmissionWebhookPayload
      convert_query_response: false
---
apiVersion: infrahub.app/v1
kind: Object
spec:
  kind: CoreCustomWebhook
  data:
    - name: cloudvision-workspace-submission
      event_type: infrahub.proposed_change.merged
      active: true
      branch_scope: other_branches
      description: Placeholder CloudVision workspace submission handoff for cv-config-validation
      url: https://placeholder.invalid/cloudvision-workspace-submission
      validate_certificates: false
      transformation: cv-workspace-submission-webhook-payload
```

Exact enum values and relationship syntax must be schema-validated against the target Infrahub version before load.

## Required `.infrahub.yml` Entries

The payload transform must be registered as a Python transform:

```yaml
python_transforms:
  - name: cv_workspace_submission_webhook_payload
    class_name: CVWorkspaceSubmissionWebhookPayload
    file_path: "./transforms/cv_workspace_submission_webhook.py"
    convert_query_response: false
```

The transform query must be registered:

```yaml
queries:
  - name: cv_workspace_submission_webhook
    file_path: "./transforms/cv_workspace_submission_webhook.gql"
```

## Placeholder Rules

- The URL must be syntactically valid and clearly non-production.
- Documentation must call the URL a placeholder.
- The placeholder URL must not be presented as a required external automation receiver.
- The placeholder registration must not start CloudVision change-control management or Semaphore Ansible playbook execution.
- A later deployment automation feature may replace the placeholder URL with a real endpoint and add receiver-specific authentication.

## Acceptance Criteria

- Repository load creates exactly one intended `CoreCustomWebhook` for CloudVision workspace submission.
- The webhook references a `CoreTransformPython` payload transform.
- The payload transform references the `cv_workspace_submission_webhook` query.
- The webhook is active only for the intended proposed-change merge event. Do not set `node_kind` for `infrahub.proposed_change.merged` events in Infrahub 1.10.
- The registration or docs associate the handoff with `cv-config-validation`.
- No `CoreStandardWebhook` is used for this feature.
