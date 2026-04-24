# Implementation Plan: Enforce Protocol-Typed Access

**Branch**: `001-enforce-protocols` | **Date**: 2026-02-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-enforce-protocols/spec.md`

## Summary

Enforce consistent typed access across all generators and transforms by replacing string-based kind references with protocol class imports, converting raw dict access to Pydantic query models, and cleaning up dead untyped code. The compliance audit revealed the scope is narrower than expected — most components are already compliant. The work targets 3 files for protocol fixes, 1 transform for dict-to-Pydantic conversion, and 1 utility module for dead code cleanup.

## Technical Context

**Language/Version**: Python >=3.11, <3.14
**Primary Dependencies**: infrahub-sdk==1.18.1, pyavd>=5.0.0
**Storage**: Neo4j (via Infrahub), PostgreSQL, Redis, RabbitMQ
**Testing**: pytest with pytest-asyncio (asyncio_mode = "auto")
**Target Platform**: Infrahub repository solution (Docker Compose local dev)
**Project Type**: Single project (Python library + generators + transforms)
**Performance Goals**: N/A (refactoring, no runtime behavior change)
**Constraints**: Must maintain behavioral equivalence; mypy strict mode; ruff C901 max-complexity=17
**Scale/Scope**: 5 files modified, ~50 lines changed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Schema-Driven Architecture | Pass | Routing schemas already exist in `schemas/routing/routing.yml`; protocol regeneration follows constitution requirement |
| II. Idempotent Operations | Pass | No changes to generator idempotency behavior |
| III. Type Safety | Pass (this feature enforces it) | Core goal of this feature — eliminates string kinds and dict access |
| IV. Test-Required Quality | Pass | Existing tests must continue passing; no new untested code paths |
| V. Convention-Based Structure | Pass | All file changes follow established naming conventions |

**Post-Phase 1 re-check**: All gates still pass. No new abstractions, patterns, or files introduced beyond the established conventions.

## Project Structure

### Documentation (this feature)

```text
specs/001-enforce-protocols/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Routing entity documentation
├── quickstart.md        # Developer quickstart guide
├── contracts/           # Contract documentation
│   └── README.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/solution_arista_avd/
├── protocols.py          # REGENERATE: add 7 Routing protocol classes
└── avd.py                # MODIFY: remove/type dead code with Any types

generators/
├── backfill_structured_config.py  # MODIFY: 10 string-kind → protocol class
└── generate_avd_device_hostvar.py # MODIFY: 1 string-kind → protocol class

transforms/
├── avd_fabric_doc.py              # MODIFY: dict access → Pydantic models
├── avd_fabric_devices.gql         # MODIFY: add avd_artifact fields
└── avd_fabric_devices_query.py    # MODIFY: extend Pydantic models
```

**Structure Decision**: No new files or directories. All changes are modifications to existing files within the established project structure.

## Complexity Tracking

No constitution violations to justify.

## Implementation Phases

### Phase 1: Regenerate Protocol Classes (FR-003)

**Prerequisite**: Running Infrahub instance with all schemas loaded.

1. Run `infrahubctl protocols --output src/solution_arista_avd/protocols.py`
2. Verify 7 new Routing protocol classes are generated
3. Verify existing IPAM protocol classes (`IpamIPPrefix`, `IpamIPAddress`) are preserved
4. Run `inv lint-mypy` to confirm the regenerated file passes

**Risk**: If `infrahubctl protocols` is not available (requires Infrahub instance), the protocol classes can be hand-written following the existing pattern. Each protocol class is ~15 lines following the established `@runtime_checkable` pattern.

### Phase 2: Fix Generator String-Kind References (FR-001)

**Depends on**: Phase 1 (Routing protocol classes must exist)

#### 2a. Backfill Generator (`generators/backfill_structured_config.py`)

Replace 10 string-kind calls with protocol class imports:

| Line | Current | Target |
| ---- | ------- | ------ |
| 74 | `kind="IpamIPPrefix"` | `IpamIPPrefix` |
| 82 | `kind="IpamIPAddress"` | `IpamIPAddress` |
| 146 | `kind="RoutingBGPPeerGroup"` | `RoutingBGPPeerGroup` |
| 174 | `kind="RoutingBGPNeighbor"` | `RoutingBGPNeighbor` |
| 203 | `kind="RoutingPrefixList"` | `RoutingPrefixList` |
| 217 | `kind="RoutingPrefixListEntry"` | `RoutingPrefixListEntry` |
| 240 | `kind="RoutingRouteMap"` | `RoutingRouteMap` |
| 265 | `kind="RoutingRouteMapEntry"` | `RoutingRouteMapEntry` |
| 302 | `kind="RoutingStaticRoute"` | `RoutingStaticRoute` |

Add imports:
```python
from solution_arista_avd.protocols import (
    IpamIPAddress,
    IpamIPPrefix,
    NetworkInterface,
    RoutingBGPNeighbor,
    RoutingBGPPeerGroup,
    RoutingPrefixList,
    RoutingPrefixListEntry,
    RoutingRouteMap,
    RoutingRouteMapEntry,
    RoutingStaticRoute,
)
```

#### 2b. AVD Hostvar Generator (`generators/generate_avd_device_hostvar.py`)

Replace 1 string-kind call:

| Line | Current | Target |
| ---- | ------- | ------ |
| 27 | `kind="NetworkPod"` | `NetworkPod` |

Add `NetworkPod` to existing imports from `solution_arista_avd.protocols`.

### Phase 3: Fix Transform Typed Access (FR-002, FR-008)

**Depends on**: None (independent of Phase 1-2)

Fix `transforms/avd_fabric_doc.py` and its supporting files:

#### 3a. Fix GraphQL Query (`transforms/avd_fabric_devices.gql`)

Add `avd_artifact` relationship to `NetworkDevice` query:
```graphql
avd_artifact {
  node {
    hostvar_identifier { value }
    structured_config_identifier { value }
  }
}
```

#### 3b. Update Pydantic Query Model (`transforms/avd_fabric_devices_query.py`)

Add model classes for the `avd_artifact` path following the established pattern:
- `...NodeAvdArtifact` with `node` field
- `...NodeAvdArtifactNode` with `hostvar_identifier` and `structured_config_identifier`

#### 3c. Refactor Transform (`transforms/avd_fabric_doc.py`)

Replace all raw dict access with Pydantic model attribute access:
- `fabric_edges[0]["node"]` → `data.network_fabric.edges[0].node`
- `device["hostname"]["value"]` → `device.hostname.value`
- `device.get("avd_inputs", {})` → `device.avd_artifact.node.hostvar_identifier.value` (with object store fetch)

Follow the pattern established in `avd_eos_config.py` and `avd_device_doc.py` for object store access.

### Phase 4: Clean Up Utility Module (FR-004)

**Depends on**: None (independent)

In `src/solution_arista_avd/avd.py`:

Two functions have `Any` types but are **dead code** (not called anywhere):
- `extract_uplink_info()` — `Sequence[Any]` parameter
- `build_fabric_hostvars()` — `Sequence[Any]` parameter

**Option A (recommended)**: Remove the dead functions entirely.
**Option B**: Replace `Any` with protocol types (`NetworkInterface`, `NetworkDevice`) and keep for future use.

Decision deferred to implementation — user can choose during task execution.

### Phase 5: Verification (FR-006, FR-007)

**Depends on**: All previous phases

1. Run `pytest tests/unit` — all tests must pass
2. Run `inv lint` — ruff, mypy, yamllint must pass
3. Run `grep 'kind="' generators/*.py` — must return zero matches
4. Manual review: no raw dict access patterns in transforms

## Risks & Mitigations

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| `infrahubctl protocols` requires running Infrahub instance | Blocks Phase 1 | Protocol classes can be hand-written following existing pattern |
| avd_fabric_doc.py has broken data access patterns beyond dict typing | Increases Phase 3 scope | Research confirmed the issue; fix is well-scoped using existing transform patterns |
| Dead code removal in avd.py may affect downstream consumers | Low (verified no callers exist) | Grep confirmed zero references; tests validate |
| Regenerated protocols.py may have formatting differences | Cosmetic | Run `inv format` after regeneration |
