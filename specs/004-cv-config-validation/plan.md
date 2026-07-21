# Implementation Plan: CloudVision Configuration Validation

**Branch**: `feat/cv-config-check` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-cv-config-validation/spec.md`

**Note**: This plan continues from the tentative implementation already present on `feat/cv-config-check`.

## Summary

Add an Infrahub proposed-change validation check that validates generated EOS configurations in CloudVision before a proposed change can merge. The design adds a fabric-level `cloudvision_managed` Boolean gate, validates CloudVision credentials and authentication only when at least one target fabric is managed, keeps validation scoped to fabric targets, requires every device in each managed fabric to have a serial number and exist in CloudVision inventory, builds a deterministic CloudVision workspace per proposed change and fabric when generated structured configs are available, and records workspace tracking in Infrahub when the tracking schema is loaded. Post-merge workspace submission and deletion-time abandonment remain out of scope for this feature.

## Technical Context

**Language/Version**: Python >=3.11, <3.14

**Primary Dependencies**: Infrahub SDK, PyAVD >=6.3.0,<6.4.0, CloudVision workflow helpers from the pinned PyAVD release, httpx for repository load helpers

**Storage**: Infrahub graph objects and file objects; external CloudVision workspace state; no new local persistent storage

**Testing**: pytest and pytest-asyncio for unit coverage; ruff, mypy, and yamllint for lint/type checks; project-designated Infrahub integration validation via `$infrahub-run-integration-tests`

**Target Platform**: Infrahub task-worker runtime executing proposed-change checks against the configured Infrahub server and CloudVision endpoint

**Project Type**: Infrahub repository with Python check, GraphQL query, schema, object seed data, and documentation

**Performance Goals**: Complete validation within 10 minutes for a representative fabric of up to 50 CloudVision-managed devices

**Constraints**: Do not contact CloudVision for unmanaged fabrics; do not submit CloudVision workspaces after merge; do not abandon workspaces on proposed-change deletion in this feature; fail fast when CloudVision credentials, authentication, or connection setup cannot be established for managed fabrics; fail before workspace validation when any managed-fabric device is missing a serial number or absent from CloudVision inventory; avoid runtime tracebacks for missing optional relationships; keep CloudVision credentials out of committed files; keep check registration compatible with Infrahub check definition rules

**Scale/Scope**: One targeted check run per fabric target in a proposed change; deterministic workspace identity per proposed change and fabric; optional workspace tracking object per built validation workspace

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Schema-Driven Architecture**: PASS. The feature adds `NetworkFabric.cloudvision_managed` in the fabric schema and introduces the `CloudvisionWorkspace` tracking node under `schemas/cv/cv.yml` before check code stores workspace tracking. Implementation tasks must include schema check and protocol regeneration evidence for the schema changes.
- **Idempotent Operations**: PASS. The check uses deterministic workspace identity per proposed change and fabric, updates or reuses an existing workspace on rerun, and updates the Infrahub tracking node instead of duplicating it.
- **Type Safety**: PASS. The check query has a generated Pydantic response model and production code should continue using typed query parsing and typed protocol classes where available.
- **Test-Required Quality**: PASS WITH REQUIRED VALIDATION. Unit coverage exists for core CloudVision helpers and selection behavior; remaining work must run focused unit tests, lint/type checks, and `$infrahub-run-integration-tests` for the Infrahub code change.
- **Convention-Based Structure**: PASS. Check files live under `checks/`, the GraphQL query is co-located with the Python check, the schema lives under `schemas/`, object seed data is in `repository_checks.yml`, and user docs live under `docs/docs/`.

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
+-- tasks.md
```

### Source Code (repository root)

```text
.infrahub.yml
repository_checks.yml
tasks.py
docker-compose.override.yml

checks/
+-- __init__.py
+-- cv_config_check.gql
+-- cv_config_check.py
+-- cv_config_check_query.py
+-- cv_helpers.py

schemas/
+-- logical_design.yml
+-- cv/
    +-- cv.yml

tests/
+-- unit/
    +-- test_cv_integration.py

docs/
+-- docs/cloudvision.md
+-- sidebars.ts
```

**Structure Decision**: Use the repository's existing Infrahub artifact layout. The check, query, generated query model, and helper module are co-located under `checks/`; the optional workspace tracking node is a schema file under `schemas/cv/`; repository seed objects stay in `repository_checks.yml`; validation docs stay in the Docusaurus developer guide.

## Phase 0 Research Summary

Research decisions are captured in [research.md](./research.md). All planning unknowns are resolved.

## Phase 1 Design Summary

The data model is captured in [data-model.md](./data-model.md). Interface contracts are captured under [contracts/](./contracts/), covering Infrahub check registration, the targeted GraphQL query, validation runtime behavior, and workspace tracking.

## Post-Design Constitution Check

- **Schema-Driven Architecture**: PASS. Design keeps the fabric-level CloudVision Managed Boolean and `CloudvisionWorkspace` schema explicit and requires schema validation plus protocol regeneration in implementation tasks.
- **Idempotent Operations**: PASS. Deterministic workspace identity and upsert-style tracking are core acceptance criteria.
- **Type Safety**: PASS. Design requires generated query models for GraphQL responses and typed access to structured-config file objects.
- **Test-Required Quality**: PASS WITH REQUIRED VALIDATION. Design requires unit, lint/type, schema, and integration validation before completion.
- **Convention-Based Structure**: PASS. All planned files align with established repository directories and naming.

## Complexity Tracking

No constitution violations.
