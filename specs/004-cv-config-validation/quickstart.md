# Quickstart: CloudVision Configuration Validation

## Prerequisites

- Dependencies are installed with `uv sync --all-packages`.
- `.env` is present and exports `INFRAHUB_ADDRESS` and `INFRAHUB_API_TOKEN` for the target validation environment.
- CloudVision task-worker or lifecycle environment includes `CLOUDVISION_SERVERS` and either `CLOUDVISION_TOKEN` or `CLOUDVISION_USERNAME` plus `CLOUDVISION_PASSWORD` for managed-fabric validation or real submission.
- Optional change-control links require `CLOUDVISION_CHANGE_CONTROL_URL_TEMPLATE`, for example `https://www.cv.example.com/cc/{change_control_id}`.
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

## Validate Workspace Threads And Direct Submission

Run focused unit tests for proposed-change thread updates and direct post-merge submission:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "submit_linked_workspace or workspace_thread or placeholder or webhook"
```

Expected outcome:

- Workspace URL thread creation and reuse pass.
- Repeated workspace processing avoids duplicate URL threads and duplicate URL comments.
- A linked submit-ready workspace is submitted exactly once.
- Already-submitted workspaces do not issue duplicate CloudVision submit requests.
- Missing linked workspaces produce a skip outcome without CloudVision calls.
- Multiple linked workspaces produce an ambiguity failure without CloudVision calls.
- Submission failures record unresolved outcomes and fallback logs when comment writes fail.
- Placeholder webhook registration checks pass.

## Validate Placeholder Webhook Removal

Run a repository search for the removed placeholder registration:

```bash
rg -n \
  "cloudvision-workspace-submission|cloudvision-workspace-submitter|replace-in-deployment|placeholder shared key|separate webhook receiver" \
  triggers.yml repository_checks.yml .infrahub.yml objects docs/docs/cloudvision.md
```

Expected outcome:

- No repository-loaded object registers a `cloudvision-workspace-submission` placeholder webhook.
- No documentation instructs operators to deploy a separate placeholder receiver service.
- No placeholder receiver URL or placeholder shared key remains.

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
- The lifecycle module resolves `CloudvisionWorkspace` by proposed-change ID on the destination branch.
- It submits only the existing linked workspace when exactly one submit-ready record exists.
- It records `submitted`, `already_submitted`, `skipped`, or `failed` in the returned result and proposed-change outcome when possible.

## Run Static And Unit Validation

Run the full local validation suite appropriate for this feature:

```bash
uv run pytest tests/unit/test_cv_integration.py
uv run pytest tests/unit
uv run ruff check checks/cv_workspace_lifecycle.py checks/cv_config_check.py checks/cv_helpers.py checks/cv_config_check_query.py checks/cv_workspace_submission_query.py tests/unit/test_cv_integration.py tasks.py
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
- Placeholder absence tests pass.

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
uv run infrahubctl graphql generate-return-types checks/cv_workspace_submission.gql
```

Expected outcome:

- Schema check passes.
- Protocol regeneration completes. Any generated diff is reviewed and kept if required.
- Query models are regenerated from current `.gql` files rather than hand-written.
- Manual review confirms `.infrahub.yml` keeps `cv-config-validation` under `check_definitions` without an invalid `query` key.
- Manual review confirms repository-loaded objects do not include placeholder CloudVision submission webhook registration.

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

- Schemas, menus, seed objects, repository definition, repository checks, and allowed triggers load successfully.
- Repository sync reaches `in-sync`.
- Repository load does not install a placeholder CloudVision submission webhook.

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

Expected outcome for invalid generated configs, CloudVision build errors, or inactive targeted devices:

- The check logs a failure that blocks the proposed change.
- The message includes the fabric and workspace location when available.
- Inactive targeted devices block the proposed change even if the workspace build succeeded.
- Pre-merge validation builds CloudVision workspaces for review but does not call CloudVision workspace submission APIs.

## Performance Validation

Validate or simulate a representative CloudVision Managed fabric with up to 50 devices:

```bash
uv run pytest tests/unit/test_cv_integration.py -k "performance or fifty_devices or representative_fabric"
```

Expected outcome:

- The run records whether pre-merge validation completes within 10 minutes for the representative 50-device managed-fabric scenario.
- If a real CloudVision timing run is not available, the evidence identifies the approved simulated or mocked scenario and its limits.

## Post-Merge Submission Validation

Automatic post-merge integrations should call `submit_linked_workspace_for_merged_event(client, event, branch="main")` from `checks/cv_workspace_lifecycle.py`, or call `submit_linked_workspace_for_proposed_change(client, proposed_change_id, branch="main")` when the execution path already has the merged proposed-change ID.

Manual retry remains available through:

```bash
uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main
```

Expected outcome for exactly one linked submit-ready workspace:

- The linked CloudVision workspace is submitted once.
- The existing workspace thread receives a success comment.
- The success comment includes the CloudVision change control ID and URL when available.
- The thread is marked resolved after the success or already-complete comment is saved.
- `CloudvisionWorkspace.status` is `submitted`.

Expected outcome for failure or skip cases:

- Missing linked workspace records skip CloudVision submission and record a skip outcome when possible.
- Ambiguous linked workspace records block CloudVision submission and record an ambiguity outcome when possible.
- CloudVision submission failures record an unresolved failure comment or fallback log.
- Failure comments state that Infrahub merge completed but CloudVision submission did not.

## Required Integration Validation

Before merge, run the project integration validation skill:

```text
$infrahub-run-integration-tests
```

Expected outcome:

- The integration report identifies the tested branch and commit.
- Repository load, schema, query registration, CloudVision validation behavior, direct submission path, and no-placeholder registration behavior pass in the project-designated Infrahub validation environment.
- The integration suite passes or records an explicit approved exception.

Generator idempotence validation is not required for this feature because it does not change generator code, generator queries, or generator-owned relationships.

## Validation Evidence

### Earlier Validation Notes

- Branch under test: `feat/cv-config-check`
- Base commit under test: `b25027a5d827a9fc5ea727483bcaa54eefd6dcfd`
- Remote integration worktree: `~/git/infrahub-worktrees/cv-config-check`
- Integration command: `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd INFRAHUB_TESTING_IMAGE_VER=1.10.1 INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1 GIT_CONFIG_GLOBAL=/dev/null uv run pytest tests/integration -vv --tb=short --maxfail=1`
- Result on 2026-07-20: blocked. The tracked local patch was applied to the remote worktree and the suite reached `tests/integration/test_e2e_pipeline.py::TestE2EPipeline::test_asn_nodes_created_and_linked`, then the pytest process remained idle and was interrupted. Earlier integration tests through `test_rack_trigger_creates_leaves` passed in the verbose rerun.
- Commit under test: `6adf4207b3b20aaa69cdb83b504e08854a8e8b47`
- Result on 2026-07-21: blocked. The suite completed with `22 passed, 6 failed, 32 warnings in 803.13s`; the failed tests were E2E pipeline checks that errored after the test Infrahub server reported `Unable to connect to the database` / database port 7687 connection refused. No CloudVision check assertion failure was reported in the failure summary.
- Docs-only follow-up validation on 2026-07-21: `npm run typecheck` and `npm run build` passed from `docs/`. Integration tests were not rerun for the docs/navigation changes.
- Inactive-device follow-up validation on 2026-07-21: `uv run pytest tests/unit/test_cv_integration.py`, focused `uv run ruff check`, focused `uv run mypy`, targeted `uv run yamllint`, `uv run pytest tests/unit`, `uv run invoke lint`, `npm run typecheck`, and `npm run build` passed. A remote integration run was started against local changes applied on top of commit `267e5919d9501cdf4915e6a792df836a3eaf1401` and stopped before completion by user direction.

### Final Direct Submission Validation - 2026-07-23

Local validation:

- `uv run pytest tests/unit/test_cv_integration.py`: passed, 43 tests.
- `uv run pytest tests/unit`: passed, 292 tests.
- `uv run ruff check checks/cv_workspace_lifecycle.py checks/cv_config_check.py checks/cv_helpers.py checks/cv_config_check_query.py checks/cv_workspace_submission_query.py tests/unit/test_cv_integration.py tasks.py`: passed.
- `uv run ruff check tests/integration/helpers.py tests/integration/test_e2e_pipeline.py`: passed.
- `uv run mypy --show-error-codes src/solution_arista_avd`: passed.
- `uv run mypy --show-error-codes src/solution_arista_avd checks tests/unit/test_cv_integration.py tasks.py`: passed.
- `uv run yamllint .`: passed.
- `uv run invoke lint`: passed.
- `uv run infrahubctl schema check schemas/`: passed.
- `uv run infrahubctl graphql generate-return-types checks/cv_config_check.gql`: passed.
- `uv run infrahubctl graphql generate-return-types checks/cv_workspace_submission.gql`: passed.
- `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py`: completed; protocol compatibility was preserved for existing extension relationships while adding the new `CloudvisionWorkspace` lifecycle fields.
- `npm run typecheck` and `npm run build` from `docs/`: passed.
- Placeholder absence search against `triggers.yml`, `repository_checks.yml`, `.infrahub.yml`, `objects`, and `docs/docs/cloudvision.md`: passed with no matches.
- Schema/protocol changes are present in the working tree; generated `schema.graphql` and `src/solution_arista_avd/protocols.py` are updated, and the integration run below loaded the schema successfully.
- Convergence follow-up: `uv run pytest tests/unit/test_cv_integration.py -k "optional_relationship_keys or cloudvision_managed or no_generated_configs"` passed, 4 selected tests. `uv run ruff check checks/cv_config_check.py tests/unit/test_cv_integration.py` passed. `uv run mypy --show-error-codes checks/cv_config_check.py tests/unit/test_cv_integration.py` passed.

Integration validation:

- Tested branch: `feat/cv-config-check`.
- Tested base commit: `7d258c4931667f0c11bd56b9fb4cabe834cc5f95`.
- Tested state: base commit plus the current uncommitted working-tree patch, copied intentionally to isolated remote worktree `/home/mtache/git/infrahub-worktrees/cv-config-check`.
- Command: `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd INFRAHUB_TESTING_IMAGE_VER=1.10.1 INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1 GIT_CONFIG_GLOBAL=/dev/null uv run pytest tests/integration --tb=short`.
- Result: passed, 28 tests and 31 warnings in 848.60 seconds.
- Placeholder-webhook absence evidence: local repository search and unit tests passed; repository load in the integration run completed without installing a placeholder CloudVision submission webhook.
- Convergence integration follow-up: branch `feat/cv-config-check`, base commit `7d258c4931667f0c11bd56b9fb4cabe834cc5f95` plus current uncommitted working-tree patch intentionally synced to remote worktree `/home/mtache/git/infrahub-worktrees/cv-config-check`; command `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd INFRAHUB_TESTING_IMAGE_VER=1.10.1 INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1 GIT_CONFIG_GLOBAL=/dev/null uv run pytest tests/integration --tb=short`; result passed, 28 tests and 31 warnings in 830.85 seconds.
