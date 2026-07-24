# Implementation Plan: CloudVision Configuration Validation

**Branch**: `feat/cv-config-check` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-cv-config-validation/spec.md`

**Note**: This plan is the canonical planning artifact for the active CustomWebhook scope. It replaces the older direct/no-placeholder submission design with the current requirement to register one placeholder `CoreCustomWebhook` for proposed-change submission and `cv-config-validation`.

## Summary

Add an Infrahub proposed-change validation and CloudVision workspace submission lifecycle for CloudVision-managed fabrics. The design adds a fabric-level `cloudvision_managed` Boolean gate, validates CloudVision credentials only for managed fabrics, requires every managed-fabric device to have a serial number, exist in CloudVision inventory, and be active, builds a deterministic CloudVision workspace per proposed change and fabric when generated structured configs are available, records workspace tracking and proposed-change thread comments when possible, and submits the linked built workspace only through CustomWebhook processing. Repository-loaded objects must include exactly one intended placeholder `CoreCustomWebhook` registration and its required `CoreTransformPython` payload transform for the submission handoff; CloudVision change-control management and Semaphore Ansible execution are out of scope for this phase.

## Technical Context

**Language/Version**: Python >=3.11, <3.14

**Primary Dependencies**: Infrahub SDK, PyAVD >=6.3.0,<6.4.0, CloudVision client/workflow helpers from the pinned PyAVD release, pytest, pytest-asyncio, invoke

**Storage**: Infrahub graph objects and file objects, including `NetworkFabric`, `CloudvisionWorkspace`, `CoreProposedChange`, `CoreChangeThread`, `CoreThreadComment`, `CoreTransformPython`, and `CoreCustomWebhook`; external CloudVision workspace state; no new local persistent storage

**Testing**: pytest and pytest-asyncio for unit coverage; ruff, mypy, and yamllint for lint/type checks; schema check and protocol regeneration for schema changes; GraphQL return-type generation for changed query files; project-designated Infrahub integration validation via `$infrahub-run-integration-tests`

**Target Platform**: Infrahub task-worker runtime executing proposed-change checks against the configured Infrahub server and CloudVision endpoint; CustomWebhook-triggered runtime path for workspace submission; manual retry path for replaying the same submission handler

**Project Type**: Infrahub repository with Python check, Python transform, lifecycle code, GraphQL queries, schema, object seed data, invoke tasks, and documentation

**Performance Goals**: Complete pre-merge validation within 10 minutes for a representative fabric of up to 50 CloudVision-managed devices; complete Infrahub thread/comment updates in under 5 seconds excluding CloudVision calls; submit a linked workspace within the existing CloudVision submission timeout

**Constraints**: Do not contact CloudVision for unmanaged fabrics; do not submit CloudVision workspaces from the validation check; submit only the existing linked workspace when exactly one submit-ready workspace exists; do not create, rebuild, or force-submit a workspace during CustomWebhook processing; keep the CustomWebhook URL clearly placeholder in this phase; do not require a real external automation receiver, CloudVision change-control orchestration, or Semaphore playbooks; keep CloudVision credentials out of committed files; preserve idempotent retry behavior; avoid runtime tracebacks for missing optional relationships; keep check and query registration compatible with Infrahub repository rules

**Scale/Scope**: One targeted check run per fabric target in a proposed change; deterministic workspace identity per proposed change and fabric; one workspace thread per proposed-change/workspace pair; one placeholder CustomWebhook registration; one linked-workspace submission attempt per CustomWebhook processing run or manual retry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Schema-Driven Architecture**: PASS. The feature adds or uses `NetworkFabric.cloudvision_managed`, `CloudvisionWorkspace` tracking fields, a repository-loaded `CoreTransformPython`, and a repository-loaded `CoreCustomWebhook`; schema validation and protocol regeneration are required before code relies on new fields.
- **Idempotent Operations**: PASS. Validation uses deterministic workspace identity per proposed change and fabric. Thread creation, URL comments, CustomWebhook registration, workspace lookup, submission, and retry behavior resolve existing state before mutating Infrahub or CloudVision.
- **Type Safety**: PASS. GraphQL responses are represented by generated Pydantic models, lifecycle outcomes are typed, and changed query files require regenerated return types.
- **Test-Required Quality**: PASS WITH REQUIRED VALIDATION. Unit coverage, focused static checks, schema/query regeneration checks, full lint, and `$infrahub-run-integration-tests` are required for the merged feature.
- **Convention-Based Structure**: PASS. Check files live under `checks/`, schemas under `schemas/`, repository objects in repository YAML, tasks in `tasks.py`, tests under `tests/`, and user docs under `docs/docs/`.

No constitution violations require a complexity exception.

## Project Structure

### Documentation (this feature)

```text
specs/004-cv-config-validation/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- check-registration.md
|   +-- graphql-query.md
|   +-- runtime-validation.md
|   +-- workspace-tracking.md
|   +-- workspace-tracking-schema.md
|   +-- cloudvision-submission.md
|   +-- custom-webhook-registration.md
|   +-- custom-webhook-processing.md
|   +-- thread-notifications.md
|   +-- submission-outcomes.md
|   +-- validation-evidence.md
+-- tasks.md
```

### Source Code (repository root)

```text
.infrahub.yml
repository_checks.yml
triggers.yml
schema.graphql
tasks.py

checks/
+-- __init__.py
+-- cv_config_check.gql
+-- cv_config_check.py
+-- cv_config_check_query.py
+-- cv_helpers.py
+-- cv_workspace_lifecycle.py

schemas/
+-- logical_design.yml
+-- cv/
    +-- cv.yml

transforms/
+-- cv_workspace_submission_webhook.py
+-- cv_workspace_submission_webhook.gql
+-- cv_workspace_submission_webhook_query.py

tests/
+-- unit/
|   +-- test_cv_integration.py
+-- integration/
    +-- helpers.py
    +-- test_e2e_pipeline.py

docs/
+-- docs/cloudvision.md
+-- sidebars.ts
```

**Structure Decision**: Use the repository's existing Infrahub artifact layout. Pre-merge validation remains in `checks/cv_config_check.py`; shared CloudVision helpers remain in `checks/cv_helpers.py`; the CustomWebhook payload transform and its GraphQL query/model live together under `transforms/` as `cv_workspace_submission_webhook.py`, `cv_workspace_submission_webhook.gql`, and `cv_workspace_submission_webhook_query.py`; CustomWebhook processing and manual retry behavior use `checks/cv_workspace_lifecycle.py`; optional tracking stays in `schemas/cv/cv.yml`; repository registration stays in `.infrahub.yml`, `repository_checks.yml`, and trigger/object YAML when present; user documentation stays in `docs/docs/cloudvision.md`.

## Phase 0 Research Summary

Research decisions are captured in [research.md](./research.md). All planning unknowns are resolved. The final submission design is CustomWebhook-triggered linked-workspace submission with a repository-loadable placeholder URL and required Python payload transform, not direct post-merge/API execution and not CloudVision change-control or Semaphore orchestration.

## Phase 1 Design Summary

The data model is captured in [data-model.md](./data-model.md). Interface contracts are captured under [contracts/](./contracts/), covering check registration, targeted validation queries, runtime validation, workspace tracking, proposed-change thread notifications, CustomWebhook registration, CustomWebhook processing, submission outcomes, and validation evidence.

## Post-Design Constitution Check

- **Schema-Driven Architecture**: PASS. Design keeps the fabric-level CloudVision Managed Boolean, `CloudvisionWorkspace` lifecycle fields, repository-loaded `CoreTransformPython`, and repository-loaded `CoreCustomWebhook` explicit and requires schema validation plus protocol regeneration where schema changes occur.
- **Idempotent Operations**: PASS. Deterministic workspace identity, tracking upserts, thread reuse, no duplicate URL comments, exact linked-workspace lookup, no duplicate submission for submitted workspaces, and retry-safe result updates are core acceptance criteria.
- **Type Safety**: PASS. Design requires generated query models for GraphQL responses and typed submission result helpers.
- **Test-Required Quality**: PASS WITH REQUIRED VALIDATION. The quickstart lists required unit, schema, generated model, lint/type, CustomWebhook registration, placeholder URL, and integration checks.
- **Convention-Based Structure**: PASS. Planned artifacts follow established repository directories and naming.

## Complexity Tracking

No constitution violations.
