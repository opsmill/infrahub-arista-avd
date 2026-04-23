# Implementation Plan: Migrate AvdArtifact to CoreFileObject

**Branch**: `011-avdartifact-file-object` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-avdartifact-file-object/spec.md`

## Summary

Migrate the AvdArtifact node from manual object store attribute tracking (6 attributes: identifier/checksum/url pairs for hostvars and structured config) to Infrahub 1.8's CoreFileObject system. AvdArtifact is preserved as the parent node with two new CoreFileObject-based Component children: `AvdHostvarFile` and `AvdStructuredConfigFile`. Requires infrahub-sdk upgrade to >= 1.19.0.

## Technical Context

**Language/Version**: Python >=3.11, <3.14
**Primary Dependencies**: infrahub-sdk >=1.19.0 (upgrade from 1.18.1), pyavd >=5.0.0
**Storage**: Infrahub object storage (via CoreFileObject), Neo4j, PostgreSQL
**Testing**: pytest with pytest-asyncio (asyncio_mode = "auto")
**Target Platform**: Infrahub server (Docker Compose local dev)
**Project Type**: Single — Infrahub repository solution
**Constraints**: Must preserve AVD pipeline end-to-end (hostvar → structured config → backfill → transforms)
**Scale/Scope**: ~10 files modified (1 schema, 3 generators, 3 transforms, 1 GQL query, 1 trigger, 1 pyproject.toml)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Schema changes come first; new nodes defined in schema YAML before code |
| II. Idempotent Operations | PASS | `allow_upsert=True` preserved for file object creation |
| III. Type Safety | PASS | Protocols regenerated after schema change; Pydantic query models updated |
| IV. Test-Required Quality | PASS | Unit tests updated for new file object patterns |
| V. Convention-Based Structure | PASS | New nodes follow Avd namespace; no new files outside conventions |

**Technology Stack**: SDK upgrade from 1.18.1 → >=1.19.0 is a justified dependency change (CoreFileObject requires it). `ariadne-codegen` override preserved.

## Project Structure

### Documentation (this feature)

```text
specs/011-avdartifact-file-object/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: SDK API, trigger strategy, storage differences
├── data-model.md        # Phase 1: Entity definitions, relationship identifiers
├── quickstart.md        # Phase 1: Migration steps
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (repository root)

```text
schemas/
└── objects/objects.yml            # Modified: AvdArtifact + 2 new CoreFileObject nodes

generators/
├── generate_avd_device_hostvar.py           # Modified: upload_from_bytes pattern
├── generate_avd_device_structured_config.py # Modified: upload_from_bytes pattern
├── backfill_structured_config.py            # Modified: retarget to AvdStructuredConfigFile
└── backfill_structured_config.gql           # Modified: rerooted query

transforms/
├── avd_eos_config.py              # Modified: download_file pattern
├── avd_fabric_doc.py              # Modified: download_file pattern
└── avd_device_doc.py              # Modified: download_file pattern

objects/
└── 01_groups.yml                  # Modified: add avd_structured_configs group

triggers.yml                       # Modified: watch AvdStructuredConfigFile.checksum
.infrahub.yml                      # Modified: backfill generator targets
pyproject.toml                     # Modified: infrahub-sdk >=1.19.0
src/solution_arista_avd/protocols.py    # Regenerated after schema change

tests/unit/
├── test_backfill_structured_config.py  # Modified: updated for new query model
└── test_avd.py                         # Modified: updated for new file patterns
```

**Structure Decision**: No new directories. All changes fit within existing project structure.

## Complexity Tracking

No constitution violations to justify.

## Phase 0: Research Summary

All research consolidated in [research.md](./research.md). Key decisions:

1. **SDK API**: Use `upload_from_bytes()` / `download_file()` (requires >= 1.19.0)
2. **Trigger strategy**: Retarget backfill generator to `avd_structured_configs` group, trigger on `AvdStructuredConfigFile.checksum`
3. **Storage**: CoreFileObject uses same backend as object_store but adds metadata, versioning, branch isolation
4. **Architecture**: AvdArtifact preserved as parent with Component relationships to file objects

## Phase 1: Design Summary

Full data model in [data-model.md](./data-model.md). Key entities:

- **AvdArtifact**: Preserved. Gains 2 Component relationships, loses 6 attributes (`state: absent`)
- **AvdHostvarFile**: New CoreFileObject node, Parent→AvdArtifact, stores hostvars JSON
- **AvdStructuredConfigFile**: New CoreFileObject node, Parent→AvdArtifact, stores structured config JSON

## Phase 2: Implementation Tasks

> Tasks will be generated by `/speckit.tasks`. The following is the implementation order:

### Task Order (dependency chain)

1. **SDK Upgrade** — Update pyproject.toml, run uv sync
2. **Schema Changes** — Add AvdHostvarFile, AvdStructuredConfigFile to objects.yml; mark old attributes absent; add Component/Parent relationships
3. **Group & Config** — Add `avd_structured_configs` group to objects/01_groups.yml; update .infrahub.yml backfill target; update triggers.yml
4. **Regenerate Protocols** — Run `infrahubctl protocols` after schema load
5. **Update Hostvar Generator** — Replace object_store.upload with upload_from_bytes on AvdHostvarFile
6. **Update Structured Config Generator** — Replace object_store.upload with upload_from_bytes on AvdStructuredConfigFile
7. **Update Backfill Generator** — Retarget query to AvdStructuredConfigFile, update GQL and Pydantic models
8. **Update Transforms** — Replace object_store.get with download_file on file object nodes (3 transforms)
9. **Update Tests** — Modify unit tests for new file object patterns
10. **Lint & Validate** — Run `inv lint`, `infrahubctl schema check`

### Files Changed Per Task

| Task | Files |
|------|-------|
| 1. SDK Upgrade | `pyproject.toml` |
| 2. Schema Changes | `schemas/objects/objects.yml` |
| 3. Group & Config | `objects/01_groups.yml`, `.infrahub.yml`, `triggers.yml` |
| 4. Protocols | `src/solution_arista_avd/protocols.py` |
| 5. Hostvar Generator | `generators/generate_avd_device_hostvar.py` |
| 6. Structured Config Generator | `generators/generate_avd_device_structured_config.py` |
| 7. Backfill Generator | `generators/backfill_structured_config.py`, `generators/backfill_structured_config.gql`, `generators/backfill_structured_config_query.py` |
| 8. Transforms | `transforms/avd_eos_config.py`, `transforms/avd_fabric_doc.py`, `transforms/avd_device_doc.py` |
| 9. Tests | `tests/unit/test_backfill_structured_config.py`, `tests/unit/test_avd.py` |
| 10. Validate | No file changes — verification only |
