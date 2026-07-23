# Implementation Plan: CloudVision Configuration Validation

**Branch**: `feat/cv-config-check` | **Date**: 2026-07-23 | **Spec**: [spec.md](./spec.md)

**Input**: Merged feature specification from `specs/004-cv-config-validation/spec.md`

**Note**: This plan is the canonical CloudVision validation and submission plan for the feature. It keeps the final direct post-merge/API submission design and removes the placeholder webhook transport from the merged scope.

## Summary

Add an Infrahub proposed-change validation and lifecycle flow for CloudVision-managed fabrics. The design adds a fabric-level `cloudvision_managed` Boolean gate, validates CloudVision credentials only for managed fabrics, requires every managed-fabric device to have a serial number, exist in CloudVision inventory, and be active, builds a deterministic CloudVision workspace per proposed change and fabric when generated structured configs are available, records workspace tracking and proposed-change thread comments when possible, and submits the linked built workspace after merge through the direct post-merge/API lifecycle path. Repository-loaded objects and documentation must not include a placeholder external webhook receiver for submission.

## Technical Context

**Language/Version**: Python >=3.11, <3.14

**Primary Dependencies**: Infrahub SDK, PyAVD >=6.3.0,<6.4.0, CloudVision client/workflow helpers from the pinned PyAVD release, pytest, pytest-asyncio, invoke

**Storage**: Infrahub graph objects and file objects, including `CloudvisionWorkspace`, `CoreProposedChange`, `CoreChangeThread`, and `CoreThreadComment`; external CloudVision workspace and change-control state; no new local persistent storage

**Testing**: pytest and pytest-asyncio for unit coverage; ruff, mypy, and yamllint for lint/type checks; schema check and protocol regeneration for schema changes; GraphQL return-type generation for changed query files; project-designated Infrahub integration validation via `$infrahub-run-integration-tests`

**Target Platform**: Infrahub task-worker runtime executing proposed-change checks against the configured Infrahub server and CloudVision endpoint; direct post-merge/API or manual retry execution path for workspace submission after proposed-change merge

**Project Type**: Infrahub repository with Python check and lifecycle code, GraphQL queries, schema, object seed data, invoke tasks, and documentation

**Performance Goals**: Complete pre-merge validation within 10 minutes for a representative fabric of up to 50 CloudVision-managed devices; complete Infrahub thread/comment updates in under 5 seconds excluding CloudVision calls; wait up to the existing CloudVision timeout for normal submission responses

**Constraints**: Do not contact CloudVision for unmanaged fabrics; do not submit CloudVision workspaces before the Infrahub proposed change is merged; do not create, rebuild, or force-submit a workspace after merge; submit only when exactly one linked workspace exists and is submit-ready; do not register a placeholder external webhook receiver; keep CloudVision credentials out of committed files; preserve idempotent retry behavior; avoid runtime tracebacks for missing optional relationships; keep check and query registration compatible with Infrahub repository rules

**Scale/Scope**: One targeted check run per fabric target in a proposed change; deterministic workspace identity per proposed change and fabric; one workspace thread per proposed-change/workspace pair; one direct submission attempt per post-merge execution or manual retry

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Schema-Driven Architecture**: PASS. The feature adds `NetworkFabric.cloudvision_managed`, extends `CloudvisionWorkspace` tracking fields, and requires schema validation plus protocol regeneration before code relies on those fields.
- **Idempotent Operations**: PASS. Validation uses deterministic workspace identity per proposed change and fabric. Thread creation, URL comments, submission, and retry behavior resolve existing state before mutating Infrahub or CloudVision.
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
|   +-- cloudvision-submission.md
|   +-- post-merge-submission.md
|   +-- thread-notifications.md
|   +-- workspace-tracking-schema.md
|   +-- direct-submission-handler.md
|   +-- no-placeholder-webhook.md
|   +-- submission-outcomes.md
|   +-- validation-evidence.md
+-- tasks.md
```

### Source Code (repository root)

```text
.infrahub.yml
repository_checks.yml
schema.graphql
tasks.py

checks/
+-- __init__.py
+-- cv_config_check.gql
+-- cv_config_check.py
+-- cv_config_check_query.py
+-- cv_helpers.py
+-- cv_workspace_lifecycle.py
+-- cv_workspace_submission.gql
+-- cv_workspace_submission_query.py

schemas/
+-- logical_design.yml
+-- cv/
    +-- cv.yml

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

**Structure Decision**: Use the repository's existing Infrahub artifact layout. Pre-merge validation remains in `checks/cv_config_check.py`; shared CloudVision helpers remain in `checks/cv_helpers.py`; direct post-merge submission and manual retry behavior use `checks/cv_workspace_lifecycle.py`; optional tracking stays in `schemas/cv/cv.yml`; repository registration stays in `.infrahub.yml` and `repository_checks.yml`; user documentation stays in `docs/docs/cloudvision.md`.

## Phase 0 Research Summary

Research decisions are captured in [research.md](./research.md). All planning unknowns are resolved. The final submission design is direct post-merge/API lifecycle execution, not a repository-loaded placeholder webhook receiver.

## Phase 1 Design Summary

The data model is captured in [data-model.md](./data-model.md). Interface contracts are captured under [contracts/](./contracts/), covering check registration, targeted validation queries, runtime validation, workspace tracking, proposed-change thread notifications, direct submission handling, no-placeholder registration, submission outcomes, and validation evidence.

## Post-Design Constitution Check

- **Schema-Driven Architecture**: PASS. Design keeps the fabric-level CloudVision Managed Boolean and `CloudvisionWorkspace` lifecycle fields explicit and requires schema validation plus protocol regeneration.
- **Idempotent Operations**: PASS. Deterministic workspace identity, tracking upserts, thread reuse, no duplicate URL comments, exact linked-workspace lookup, no duplicate submission for submitted workspaces, and retry-safe result updates are core acceptance criteria.
- **Type Safety**: PASS. Design requires generated query models for GraphQL responses and typed submission result helpers.
- **Test-Required Quality**: PASS WITH REQUIRED VALIDATION. The quickstart lists required unit, schema, generated model, lint/type, placeholder absence, and integration checks.
- **Convention-Based Structure**: PASS. Planned artifacts follow established repository directories and naming.

## Complexity Tracking

No constitution violations.
