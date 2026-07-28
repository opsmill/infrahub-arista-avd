# Implementation Plan: Normalized Device Design Entities

**Branch**: `005-device-design-entities` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-device-design-entities/spec.md`

## Summary

Replace the per-tier, per-role paired fields that describe device designs (`<role>_switch_template` relationship + `amount_of_<role>s` attribute) on `NetworkFabric`, `NetworkPod`, and `LocationRack` with a normalized, reusable **device design entity**. A `NetworkDeviceDesign` generic carries the shared shape — `device_template` → `CoreObjectTemplate` (cardinality one), `device_quantity` (Number ≥1), and an explicit `role` (Dropdown) — and three concrete tier nodes (`NetworkFabricDeviceDesign`, `NetworkPodDeviceDesign`, `NetworkRackDeviceDesign`) inherit it, each a cascade-owned `Component` child of its container keyed by `(container, role)`. Adding a device type then becomes data, not schema. The change is a staged migration: additive schema first, data migration, then removal of the old fields via `state: absent`, rolled out on a branch and merged through a proposed change. Generator, seed-object, protocol-regeneration, and docs updates are explicit follow-on cycles.

## Technical Context

**Language/Version**: Infrahub schema YAML (`version: "1.0"`); Python >=3.11,<3.14 for the one-time data-migration helper and tests.

**Primary Dependencies**: Infrahub 1.10.1 (`INFRAHUB_BASE_VERSION`), `infrahub-sdk[all]>=1.19.0`, `infrahubctl`. No new runtime dependencies.

**Storage**: Infrahub graph (Neo4j/PostgreSQL) — schema nodes and instances. No external storage.

**Testing**: `uv run infrahubctl schema check schemas/` (load-time validation); `uv run pytest tests/unit` for the migration helper; `$infrahub-run-integration-tests` for the schema migration + repository load per constitution Principle IV.

**Target Platform**: Infrahub server (Linux), UI + GraphQL API.

**Project Type**: Infrahub reference-design repository — schema-first artifact cycle (single project).

**Performance Goals**: N/A (schema definition). Design keeps queries flat: `(container, role)` HFID enables direct upsert/lookup without scans.

**Constraints**: Branch-first rollout (never load onto the default branch); `state: absent` for removals; new relationships must be additive/optional-first so existing data does not fail load; the old and new representations MUST coexist during migration so generators and seed data are never read against a removed field.

**Scale/Scope**: 3 container kinds, 1 new generic, 3 new concrete nodes, 6 removed fields (4 quantity attributes + 4 template relationships across the tiers — `super_spine`, `spine`, `leaf`, `l2leaf`), ~8 seed object files affected (follow-on cycle).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|------------|--------|
| **I. Schema-Driven Architecture** | This cycle *is* the schema change and precedes all code that reads the new fields. Uses `Network.*` namespace; container relationships added via `extensions` block (Rack) / node edits. Protocol regeneration (`infrahubctl protocols …`) is a mandatory step after load. | ✅ Pass |
| **II. Idempotent Operations** | Design enables idempotent downstream generation: each design is keyed by `(container, role)` HFID, so generators upsert designs and derive devices deterministically. The one-time migration helper is HFID-upsert based and safe to re-run. | ✅ Pass |
| **III. Type Safety** | Protocols regenerated from schema; no hand-edits. Generator/transform query-model updates that consume the new relationship are typed in their follow-on cycles. | ✅ Pass |
| **IV. Test-Required Quality** | This cycle carries schema-check + protocol-regen evidence and integration coverage of the schema migration + repo load (`$infrahub-run-integration-tests`). Migration helper gets unit tests. Generator idempotence (`$infrahub-test-generator-idempotence`) is exercised in the follow-on generator cycle. | ✅ Pass |
| **V. Convention-Based Structure** | New schema in `schemas/device_design.yml`; removals edited in the files where the fields are defined (`logical_design.yml`, `location_extensions.yml`, `l3ls_extensions.yml`); cross-file container relationships via `extensions`. Seed data stays numbered under `objects/`. | ✅ Pass |

**Result**: No violations. Complexity Tracking not required.

The one identified deviation from the user's literal ask — a single `RackDeviceDesignEntity` reused across tiers vs. a generic + three concrete nodes — is documented in [research.md](./research.md) (Decision 1) and is driven by an Infrahub constraint (`Parent` targets one kind), not added complexity.

## Project Structure

### Documentation (this feature)

```text
specs/005-device-design-entities/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — design decisions
├── data-model.md        # Phase 1 output — nodes/generics/attributes/relationships
├── quickstart.md        # Phase 1 output — validation & rollout guide
├── contracts/
│   └── schema-contract.md   # Resulting schema/GraphQL surface downstream consumers depend on
└── checklists/
    └── requirements.md  # Spec quality checklist (from /speckit-specify)
```

### Source Code (repository root)

```text
schemas/
├── device_design.yml        # NEW: NetworkDeviceDesign generic + 3 concrete nodes
│                            #      + device_designs Component relationships on the
│                            #      three containers (via `extensions:` block)
├── logical_design.yml       # EDIT: NetworkFabric/NetworkPod — mark super_spine_switch_template,
│                            #       amount_of_super_spines, spine_switch_template,
│                            #       amount_of_spines `state: absent` (removal stage)
├── location_extensions.yml  # EDIT: LocationRack — mark leaf_switch_template,
│                            #       amount_of_leafs `state: absent` (removal stage)
└── l3ls_extensions.yml      # EDIT: LocationRack — mark l2leaf_switch_template,
                             #       amount_of_l2leafs `state: absent` (removal stage)

src/solution_arista_avd/
└── protocols.py             # REGENERATE after schema load (not hand-edited)

# Follow-on cycles (OUT OF SCOPE here, noted for coordination):
generators/  generate_fabric.py|.gql, generate_pod.py|.gql, generate_rack.py|.gql + *_query.py
objects/     10_fabric.yml, 10a_fabric_c_fabric.yml, 11_rack.yml, 11a_fabric_c_rack.yml,
             13a_fabric_l2ls.yml, 13b_fabric_campus.yml, 13c_fabric_isis_ldp.yml, …
docs/docs/developer-guide/  schema + architecture pages
```

**Structure Decision**: Single Infrahub repository, schema-first. The feature is authored cohesively in a new `schemas/device_design.yml` (generic + concrete nodes + container `device_designs` relationships via the `extensions` block), so a reviewer sees the whole additive model in one file. The `state: absent` removals are edited in place in the files that currently define the fields, because a removal must sit on the original definition. This isolates the additive (safe, load-anytime) change from the destructive (gated) change.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
