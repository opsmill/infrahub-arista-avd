# Quickstart: CloudVision Configuration Validation

## Prerequisites

- Dependencies are installed with `uv sync --all-packages`.
- `.env` is present and exports the Infrahub address and token for the target validation environment.
- CloudVision task-worker environment includes either token credentials or username/password credentials.
- The AVD generator chain has produced structured-config artifacts for the fabric under test.
- The feature branch is pushed if the remote Infrahub repository sync validates from Git.

## Local Static Validation

Run focused unit tests for the CloudVision check:

```bash
uv run pytest tests/unit/test_cv_integration.py
```

Expected outcome:

- CloudVision Managed gating skips unmanaged fabrics before CloudVision credential setup.
- Device filtering covers target-fabric membership and nullable relationships.
- Serial-number enforcement covers every confirmed device in a CloudVision Managed fabric before workspace validation.
- CloudVision inventory enforcement blocks when any serial-numbered managed-fabric device is absent from CloudVision inventory.
- Inactive CloudVision device enforcement blocks when any targeted CloudVision device is inactive, including the false-positive case where workspace build reports success.
- Structured-config download, decode, and render failures for devices selected for workspace deployment are blocking failures with device-specific messages.
- Managed fabrics with no generated structured configs skip workspace validation only after authentication, serial-number, and inventory eligibility pass.
- Workspace ID, name, and description helpers behave deterministically.
- Proposed-change metadata lookup falls back to source branch and short `feat/` branch names.
- Structured-config retrieval uses the check branch.

Run focused lint and type checks:

```bash
uv run ruff check checks/cv_config_check.py checks/cv_helpers.py checks/cv_config_check_query.py tests/unit/test_cv_integration.py
uv run mypy checks/cv_helpers.py checks/cv_config_check.py tests/unit/test_cv_integration.py
```

Expected outcome:

- Ruff reports no findings for touched CloudVision files.
- Mypy reports no errors for touched CloudVision files.

Run the full unit suite when the branch is ready:

```bash
uv run pytest tests/unit
```

Expected outcome:

- All unit tests pass.

## Schema and Repository Validation

Check schema validity:

```bash
set -a; source .env; set +a
uv run infrahubctl schema check schemas/
```

Regenerate protocols after schema changes:

```bash
set -a; source .env; set +a
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

Expected outcome:

- Schema check passes.
- Protocol regeneration completes. Any generated diff is reviewed and kept if required.

Validate repository registration shape:

```bash
uv run yamllint .infrahub.yml repository_checks.yml
```

Expected outcome:

- YAML linting passes for both files.
- Manual review confirms `.infrahub.yml` keeps `cv-config-validation` under `check_definitions` without a `query` key.
- Manual review confirms `cv_config_check` remains registered under top-level `queries`.
- Manual review confirms `repository_checks.yml` still loads live `CoreGraphQLQuery` and `CoreCheckDefinition` seed objects.

## Live Proposed-Change Validation

Load repository artifacts into a prepared Infrahub environment:

```bash
set -a; source .env; set +a
uv run invoke load-schema
uv run invoke load
```

Expected outcome:

- Schemas, menus, seed objects, repository definition, repository checks, and triggers load successfully.
- Repository sync reaches `in-sync`.

Run the CloudVision validation check through the proposed-change validation pipeline, or run the check directly against a prepared branch:

```bash
set -a; source .env; set +a
uv run infrahubctl check cv-config-validation --branch <branch-name>
```

Expected outcome for valid generated configs:

- The check creates or updates one deterministic CloudVision workspace for the proposed change and fabric.
- The workspace builds successfully.
- Every targeted CloudVision device is active.
- The check logs a success message with the workspace location and deployment counts.
- When the tracking schema is loaded, a `CloudvisionWorkspace` object exists for the workspace.

Expected outcome for invalid generated configs or CloudVision build errors:

- The check logs a failure that blocks the proposed change.
- The message includes the fabric and workspace location when available.

Expected outcome when CloudVision reports inactive targeted devices:

- The check logs a failure that blocks the proposed change even if the workspace build succeeded.
- The failure message identifies the inactive device or devices.

## Required Integration Validation

Before merge, run the project integration validation skill:

```text
$infrahub-run-integration-tests
```

Expected outcome:

- The integration report identifies the tested branch and commit.
- The integration suite passes or records an explicit approved exception.

Generator idempotence validation is not required for this feature because it does not change generator code, generator queries, or generator-owned relationships.

## Validation Evidence

- Branch under test: `feat/cv-config-check`
- Base commit under test: `b25027a5d827a9fc5ea727483bcaa54eefd6dcfd`
- Remote integration worktree: `~/git/infrahub-worktrees/cv-config-check`
- Integration command: `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd INFRAHUB_TESTING_IMAGE_VER=1.10.1 INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1 GIT_CONFIG_GLOBAL=/dev/null uv run pytest tests/integration -vv --tb=short --maxfail=1`
- Result on 2026-07-20: blocked. The tracked local patch was applied to the remote worktree and the suite reached `tests/integration/test_e2e_pipeline.py::TestE2EPipeline::test_asn_nodes_created_and_linked`, then the pytest process remained idle and was interrupted. Earlier integration tests through `test_rack_trigger_creates_leaves` passed in the verbose rerun.
- Branch under test: `feat/cv-config-check`
- Commit under test: `6adf4207b3b20aaa69cdb83b504e08854a8e8b47`
- Remote integration worktree: `~/git/infrahub-worktrees/cv-config-check`
- Integration command: `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd INFRAHUB_TESTING_IMAGE_VER=1.10.1 INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1 GIT_CONFIG_GLOBAL=/dev/null uv run pytest tests/integration`
- Result on 2026-07-21: blocked. The suite completed with `22 passed, 6 failed, 32 warnings in 803.13s`; the failed tests were E2E pipeline checks that errored after the test Infrahub server reported `Unable to connect to the database` / database port 7687 connection refused. No CloudVision check assertion failure was reported in the failure summary.
- Docs-only follow-up validation on 2026-07-21: `npm run typecheck` and `npm run build` passed from `docs/`. Integration tests were not rerun for the docs/navigation changes.
- Inactive-device follow-up validation on 2026-07-21: `uv run pytest tests/unit/test_cv_integration.py`, focused `uv run ruff check`, focused `uv run mypy`, targeted `uv run yamllint`, `uv run pytest tests/unit`, `uv run invoke lint`, `npm run typecheck`, and `npm run build` passed. A remote integration run was started against local changes applied on top of commit `267e5919d9501cdf4915e6a792df836a3eaf1401` and stopped before completion by user direction.
