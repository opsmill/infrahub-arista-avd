# Quickstart: CloudVision Configuration Validation

## Prerequisites

- Dependencies are installed with `uv sync --all-packages`.
- `.env` is present and exports `INFRAHUB_ADDRESS` and `INFRAHUB_API_TOKEN` for the target validation environment.
- CloudVision task-worker or lifecycle environment includes `CLOUDVISION_SERVERS` and either `CLOUDVISION_TOKEN` or `CLOUDVISION_USERNAME` plus `CLOUDVISION_PASSWORD` for managed-fabric validation or workspace submission.
- The AVD generator chain has produced structured-config artifacts for the fabric under test.
- The feature branch is pushed if the remote Infrahub repository sync validates from Git.

For server-backed commands, export `.env` first:

```bash
set -a
source .env
set +a
uv run infrahubctl info
```

## Validate Pre-Merge CloudVision Configuration Checks

Run focused unit tests for the CloudVision check:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "cloudvision_managed or inventory or inactive or structured_config or workspace"
```

Expected outcome:

- CloudVision Managed gating skips unmanaged fabrics before CloudVision credential setup.
- Device filtering covers target-fabric membership and nullable relationships.
- Serial-number enforcement covers every confirmed device in a CloudVision Managed fabric before workspace validation.
- CloudVision inventory enforcement blocks when any serial-numbered managed-fabric device is absent from CloudVision inventory.
- Inactive CloudVision device enforcement blocks when any targeted CloudVision device is inactive, including the false-positive case where workspace build reports success.
- Structured-config download, decode, and render failures for devices selected for workspace deployment are blocking failures with device-specific messages.
- Managed fabrics with no generated structured configs skip workspace validation only after authentication, serial-number, inventory, and active-state eligibility pass.
- Workspace ID, name, and description helpers behave deterministically.
- Proposed-change metadata lookup falls back to source branch and short `feat/` branch names.
- Structured-config retrieval uses the check branch.

## Validate Workspace Threads And CustomWebhook Submission

Run focused unit tests for proposed-change thread updates and CustomWebhook submission processing:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "submit_linked_workspace or workspace_thread or custom_webhook or webhook"
```

Expected outcome:

- Workspace URL thread creation and reuse pass.
- Repeated workspace processing avoids duplicate URL threads and duplicate URL comments.
- The CustomWebhook event adapter resolves proposed-change ID and branch from the event payload.
- A linked submit-ready workspace is submitted exactly once.
- Already-submitted workspaces do not issue duplicate CloudVision submit requests.
- Missing linked workspaces produce a skip outcome without CloudVision calls.
- Multiple linked workspaces produce an ambiguity failure without CloudVision calls.
- Submission failures record unresolved outcomes and fallback logs when comment writes fail.
- Manual retry calls the same submission handler as CustomWebhook processing.

## Validate Placeholder CustomWebhook Registration

Inspect repository-loaded objects and docs for the required placeholder registration:

```bash
rg -n \
  "CoreCustomWebhook|cv-config-validation|cloudvision.*workspace.*submission|placeholder|Semaphore|change control" \
  triggers.yml repository_checks.yml .infrahub.yml objects docs/docs/cloudvision.md
```

Expected outcome:

- Exactly one intended CloudVision workspace submission `CoreCustomWebhook` is present in repository-loaded objects.
- The `CoreCustomWebhook` references a `CoreTransformPython` payload transform registered in `.infrahub.yml`.
- The CustomWebhook is associated with proposed-change submission and `cv-config-validation`.
- The CustomWebhook URL is clearly placeholder and is not documented as a real external automation endpoint.
- Documentation states that CloudVision change-control management and Semaphore Ansible playbooks are out of scope for this phase.

## Validate Manual Retry Path

For a real or lab proposed change with a linked workspace, source the repository environment and call the manual retry adapter:

```bash
set -a
source .env
set +a
uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main
```

Expected outcome:

- The invoke task calls `checks.cv_workspace_lifecycle`.
- The lifecycle module resolves `CloudvisionWorkspace` by proposed-change ID on the selected branch.
- It submits only the existing linked workspace when exactly one submit-ready record exists.
- It records `submitted`, `already_submitted`, `skipped`, or `failed` in the returned result and proposed-change outcome when possible.
- It does not create, rebuild, force-submit, or submit an unrelated workspace.

## Run Static And Unit Validation

Run the full local validation suite appropriate for this feature:

```bash
uv run pytest tests/unit/test_cv_integration.py
uv run pytest tests/unit
uv run ruff check checks/cv_workspace_lifecycle.py checks/cv_config_check.py checks/cv_helpers.py tests/unit/test_cv_integration.py tasks.py
uv run ruff check transforms/cv_workspace_submission_webhook.py
uv run ruff check tests/integration/helpers.py tests/integration/test_e2e_pipeline.py
uv run mypy --show-error-codes src/solution_arista_avd
uv run mypy --show-error-codes src/solution_arista_avd checks tests/unit/test_cv_integration.py tasks.py
uv run yamllint .
uv run invoke lint
```

Expected outcome:

- Unit tests pass.
- Static checks pass, including the full repository lint gate.
- Mypy covers both the existing enforced `src/solution_arista_avd` package and the changed CloudVision check, lifecycle, test, and task Python surfaces.
- CustomWebhook registration, placeholder URL, and scope-exclusion tests pass.

## Schema, Query, And Repository Validation

Check schema validity:

```bash
set -a
source .env
set +a
uv run infrahubctl schema check schemas/
```

Regenerate protocols after schema changes:

```bash
set -a
source .env
set +a
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

Regenerate typed GraphQL response models after query changes:

```bash
set -a
source .env
set +a
uv run infrahubctl graphql generate-return-types checks/cv_config_check.gql
uv run infrahubctl graphql generate-return-types transforms/cv_workspace_submission_webhook.gql
```

Expected outcome:

- Schema check passes.
- Protocol regeneration completes. Any generated diff is reviewed and kept if required.
- Query models are regenerated from current `.gql` files rather than hand-written.
- Manual review confirms `.infrahub.yml` keeps `cv-config-validation` under `check_definitions` without an invalid `query` key.
- Manual review confirms `.infrahub.yml` registers the CustomWebhook payload transform under `python_transforms`.
- Manual review confirms repository-loaded objects include the intended placeholder `CoreCustomWebhook`, its `CoreTransformPython` payload transform, and no CloudVision change-control or Semaphore deployment orchestration.

## Live Proposed-Change Validation

Load repository artifacts into a prepared Infrahub environment:

```bash
set -a
source .env
set +a
uv run invoke load-schema
uv run invoke load
```

Expected outcome:

- Schemas, menus, seed objects, repository definition, repository checks, CustomWebhook registration, and allowed triggers load successfully.
- Repository sync reaches `in-sync`.
- Repository load installs exactly one intended placeholder CloudVision workspace submission CustomWebhook.

Run the CloudVision validation check through the proposed-change validation pipeline, or run the check directly against a prepared branch:

```bash
set -a
source .env
set +a
uv run infrahubctl check cv-config-validation --branch <branch-name>
```

Expected outcome for valid generated configs:

- The check creates or updates one deterministic CloudVision workspace for the proposed change and fabric.
- The workspace builds successfully.
- Every targeted CloudVision device is active.
- The check logs a success message with the workspace location and deployment counts.
- When the tracking schema is loaded, a `CloudvisionWorkspace` object exists for the workspace.
- When thread APIs and URL metadata are available, the proposed-change Overview has one workspace thread with the exact workspace URL.
- The validation check does not submit the CloudVision workspace.

Expected outcome for invalid generated configs, CloudVision build errors, or inactive targeted devices:

- The check logs a failure that blocks the proposed change.
- The message includes the fabric and workspace location when available.
- Inactive targeted devices block the proposed change even if the workspace build succeeded.

## CustomWebhook Submission Validation

Simulate or invoke the CustomWebhook processing path for a submitted proposed change:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "custom_webhook or submit_linked_workspace"
```

Expected outcome for exactly one linked submit-ready workspace:

- The linked CloudVision workspace is submitted once.
- The existing workspace thread receives a success comment with the workspace identity and URL when available.
- The thread is marked resolved after the success or already-complete comment is saved.
- `CloudvisionWorkspace.status` is `submitted`.
- No CloudVision change-control approval scheduling or Semaphore playbook execution is attempted.

Expected outcome for failure or skip cases:

- Missing linked workspace records skip CloudVision submission and record a skip outcome when possible.
- Ambiguous linked workspace records block CloudVision submission and record an ambiguity outcome when possible.
- Non-submit-ready workspace status blocks submission without creating or rebuilding a workspace.
- CloudVision submission failures record an unresolved failure comment or fallback log.
- Failure comments state that proposed-change submission completed but CloudVision workspace submission did not.

## Performance Validation

Validate or simulate a representative CloudVision Managed fabric with up to 50 devices:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "performance or fifty_devices or representative_fabric"
```

Expected outcome:

- The run records whether pre-merge validation completes within 10 minutes for the representative 50-device managed-fabric scenario.
- If a real CloudVision timing run is not available, the evidence identifies the approved simulated or mocked scenario and its limits.

## Required Integration Validation

Before merge, run the project integration validation skill:

```text
$infrahub-run-integration-tests
```

Expected outcome:

- The integration report identifies the tested branch and commit.
- Repository load, schema, query registration, CloudVision validation behavior, CustomWebhook registration, placeholder URL, CustomWebhook submission processing, manual retry, and scope exclusions for CloudVision change controls and Semaphore pass in the project-designated Infrahub validation environment.
- The integration suite passes or records an explicit approved exception.

Generator idempotence validation is not required for this feature because it does not change generator code, generator queries, or generator-owned relationships.

## Current Validation Evidence

Recorded on 2026-07-24 for the working tree on `feat/cv-config-check`:

- `uv run pytest tests/unit/test_cv_integration.py -q`: PASS, 47 passed.
- `uv run ruff check checks/cv_workspace_lifecycle.py checks/cv_config_check.py checks/cv_helpers.py transforms/cv_workspace_submission_webhook.py tests/unit/test_cv_integration.py tasks.py`: PASS.
- `uv run ruff format --check checks/cv_workspace_lifecycle.py checks/cv_config_check.py checks/cv_helpers.py transforms/cv_workspace_submission_webhook.py tests/unit/test_cv_integration.py tasks.py`: PASS.
- `uv run mypy --show-error-codes checks tests/unit/test_cv_integration.py tasks.py`: PASS.
- `uv run yamllint .`: PASS.
- `set -a; source .env; set +a; uv run infrahubctl info`: PASS against Infrahub 1.10.1.
- `set -a; source .env; set +a; uv run infrahubctl schema check schemas/`: PASS; all schema files valid.
- `set -a; source .env; set +a; uv run infrahubctl graphql generate-return-types checks/cv_config_check.gql`: PASS; regenerated `checks/cv_config_check_query.py`.
- `set -a; source .env; set +a; uv run infrahubctl graphql generate-return-types transforms/cv_workspace_submission_webhook.gql`: PASS; regenerated `transforms/cv_workspace_submission_webhook_query.py`.
- `uv run pytest tests/unit/test_cv_integration.py -k "performance or fifty_devices or representative_fabric" -q`: NOT COVERED; pytest selected no tests and returned exit 5 with 47 deselected.
- `uv run pytest tests/unit -q`: FAIL in existing hostvar test `test_generated_hostvars_take_precedence_over_custom_hostvars`; expected `l3leaf.defaults` lacks `spanning_tree_priority`, but the generated hostvars include it.
- `uv run mypy --show-error-codes src/solution_arista_avd`: FAIL with existing generated-protocol attribute errors in `src/solution_arista_avd/generator.py`, `src/solution_arista_avd/cabling.py`, and `src/solution_arista_avd/addressing.py`.
- `uv run invoke lint`: FAIL because the `lint-mypy` step runs `uv run mypy --show-error-codes src/solution_arista_avd` and hits the same existing protocol attribute errors.
- `$infrahub-run-integration-tests`: NOT RUN for this working tree because the integration skill requires a committed branch/commit available on the remote integration host, and the current implementation is still uncommitted.
