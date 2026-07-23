# Contract: No Placeholder Webhook Registration

## Purpose

Ensure repository-loaded objects and operator documentation do not imply a fake
CloudVision workspace submission receiver service.

## Removed Registration

The repository must not load a placeholder object equivalent to:

```yaml
kind: CoreStandardWebhook
name: cloudvision-workspace-submission
event_type: infrahub.proposed_change.merged
url: http://cloudvision-workspace-submitter:8080/infrahub/proposed-change-merged
shared_key: replace-in-deployment
```

## Files To Validate

- `triggers.yml`
- `repository_checks.yml`
- `.infrahub.yml`
- `docs/docs/cloudvision.md`
- feature quickstart and task artifacts

## Required Absence Checks

The following placeholder strings must not appear in repository-loaded objects
or CloudVision operator instructions:

- `cloudvision-workspace-submission` as a placeholder webhook registration name
- `cloudvision-workspace-submitter`
- `http://cloudvision-workspace-submitter:8080/infrahub/proposed-change-merged`
- `replace-in-deployment`
- instructions requiring a separate placeholder webhook receiver service

## Allowed References

- Direct handler names such as `submit_linked_workspace_for_proposed_change`.
- Manual retry command documentation.
- General statements that a deployment-specific post-merge/API execution path
  may call the direct handler.
- Tests or contracts that assert the placeholder webhook is absent.

## Validation Rules

- Repository load must not create a placeholder `CoreStandardWebhook` for this
  workflow.
- Documentation must describe the direct post-merge/API execution path and
  manual retry path.
- Any future real webhook receiver must be introduced by a separate feature or
  deployment-specific configuration with real endpoint ownership and validation.
