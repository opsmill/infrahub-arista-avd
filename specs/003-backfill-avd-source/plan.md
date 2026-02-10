# Implementation Plan: Backfill AVD Attribute Source

**Branch**: `003-backfill-avd-source` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-backfill-avd-source/spec.md`

## Summary

Update the backfill structured config generator to tag all created/updated attributes with the "AVD" CoreAccountGroup as their source. This provides data lineage in Infrahub, distinguishing AVD-automated values from manual entries. The implementation adds a single CoreAccountGroup lookup at the start of `generate()` and passes the source to all `client.create()` calls and attribute updates via the infrahub-sdk `NodeProperty` mechanism.

## Technical Context

**Language/Version**: Python >=3.11, <3.14
**Primary Dependencies**: infrahub-sdk==1.18.1
**Storage**: Infrahub (Neo4j-backed)
**Testing**: pytest (unit tests with AsyncMock)
**Target Platform**: Infrahub generator runtime
**Project Type**: Single project (existing codebase modification)
**Constraints**: One API call for CoreAccountGroup lookup per generate() invocation

## Project Structure

### Documentation (this feature)

```text
specs/003-backfill-avd-source/
├── plan.md              # This file
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Task list (generated next)
```

### Source Code (files to modify)

```text
generators/
└── backfill_structured_config.py     # Main generator - add source lookup and propagation

tests/unit/
└── test_backfill_structured_config.py # Add tests for source attribution
```

### Implementation Approach

1. **CoreAccountGroup lookup**: At the top of `generate()`, use `self.client.get(kind="CoreAccountGroup", name__value="AVD")` to fetch the group. Wrap in try/except for graceful degradation.

2. **Source propagation**: The infrahub-sdk `NodeProperty` class allows setting `attribute.source` on any node attribute. After each `client.create()` call and before `save()`, iterate over the node's attributes and set `source = NodeProperty(data=avd_group.id)`.

3. **Alternative approach (simpler)**: If the SDK supports passing source at create time or if `save()` accepts a source parameter, use that instead. Research indicates the source is set per-attribute via `NodeProperty`.

4. **Graceful degradation**: If `CoreAccountGroup` named "AVD" is not found, set `avd_source = None` and skip source assignment throughout.

**Structure Decision**: Modifying existing files only. No new files needed.
