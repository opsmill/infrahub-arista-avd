# Contract: Validation Evidence

## Purpose

Define the evidence required before the CustomWebhook submission revision is considered ready for review.

## Local Unit Evidence

Required command:

```bash
uv run pytest tests/unit/test_cv_integration.py
```

Required coverage:

- CloudVision Managed gating and unmanaged fabric skip.
- Missing serial-number, missing inventory, inactive-device, and structured-config failure paths.
- Workspace identity and workspace URL thread idempotence.
- CustomWebhook payload transform registration and placeholder URL.
- CustomWebhook event adapter resolves proposed-change ID and branch.
- CustomWebhook handler submits exactly one linked submit-ready workspace.
- Already-submitted workspace path issues no duplicate submit request.
- Missing linked workspace path skips CloudVision calls.
- Ambiguous linked workspace path blocks submission.
- CloudVision failure path records unresolved failure outcomes.
- Fallback logging path preserves operational context.
- Documentation states that CloudVision change-control management and Semaphore playbooks are out of scope.

## Static Evidence

Required command:

```bash
uv run invoke lint
```

If a narrower local check is used while developing, final review still requires the full lint task or an explicit exception.

## Schema Evidence

If schema files are changed:

```bash
uv run infrahubctl schema check schemas/
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

If no schema files are changed, record that schema validation was not applicable for this revision.

## Query And Transform Evidence

If GraphQL query files are changed:

```bash
uv run infrahubctl graphql generate-return-types checks/cv_config_check.gql
uv run infrahubctl graphql generate-return-types transforms/cv_workspace_submission_webhook.gql
```

If the CustomWebhook payload transform is added or changed, validate it through unit tests and, when a running Infrahub server is available:

```bash
uv run infrahubctl transform cv_workspace_submission_webhook_payload proposed_change_id=<proposed-change-id>
```

## Integration Evidence

Required validation:

```text
$infrahub-run-integration-tests
```

The evidence must include:

- tested branch,
- tested commit,
- pass/fail result,
- confirmation that repository loading installs the intended placeholder `CoreCustomWebhook`,
- confirmation that repository loading does not imply CloudVision change-control management or Semaphore playbook execution,
- or an explicit maintainer-approved exception.

## Documentation Evidence

Review `docs/docs/cloudvision.md` and feature quickstart output for these required statements:

- validation builds but does not submit CloudVision workspaces,
- CustomWebhook processing submits only the linked workspace,
- the CustomWebhook URL is placeholder in this phase,
- no real external automation receiver is required by this phase,
- CloudVision change-control management and Semaphore Ansible playbooks are out of scope,
- manual retry uses `uv run invoke submit-cv-workspace`.
