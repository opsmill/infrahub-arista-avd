# Implementation Plan: Device-Design-Driven Fabric Generators

**Branch**: `006-device-design-generators` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-device-design-generators/spec.md`

## Summary

Rewire the three fabric generators (`generate_fabric`, `generate_pod`, `generate_rack`) to source their per-role device count and object template from the `device_designs` relationship introduced in `005-device-design-entities`, instead of the legacy `amount_of_<role>s` / `<role>_switch_template` fields. The change spans each generator's `.gql` query, its regenerated `*_query.py` model, and its Python `generate()` logic. A shared helper resolves `role → (template_id, quantity)` from a container's designs, returning zero for an absent role. Two **cross-tier completeness reads** — the pod reading the fabric's super-spine count, and the rack reading the pod's spine count — also move to `device_designs`. The refactor is behavior-preserving (identical fabric for an equivalent design), idempotent, and lands as a hard cutover together with the co-requisite Objects cycle.

## Technical Context

**Language/Version**: Python >=3.11,<3.14 (generators + shared helper); Infrahub GraphQL for the `.gql` queries.

**Primary Dependencies**: `infrahub-sdk[all]>=1.19.0` (`InfrahubGenerator`, typed query models), Infrahub 1.10.1. No new dependencies.

**Storage**: Infrahub graph. Generators read `device_designs` and create `DcimDevice`/`DcimInterface`/`NetworkLink`/`MlagDomain` + allocate pool resources (unchanged).

**Testing**: `uv run pytest tests/unit` (resolution-helper + absence-means-none logic); `$infrahub-run-integration-tests` for the generator chain; `$infrahub-test-generator-idempotence` for repeated-run validation (Constitution Principles II & IV).

**Target Platform**: Infrahub server; generators run from triggers and manual `infrahubctl generator` invocations.

**Project Type**: Infrahub reference-design repository — Generator artifact cycle (single project).

**Performance Goals**: N/A. Keep query round-trips no worse than today; `device_designs` is a single bounded relationship per container.

**Constraints**: Behavior-preserving (same devices for an equivalent design); idempotent (`allow_upsert=True`, tracking cleanup intact); typed query-model access (no untyped dict access); hard cutover — generators read `device_designs` only, so seed data MUST be migrated (co-requisite Objects cycle) before this lands on a shared branch.

**Scale/Scope**: 3 generators × (`.gql` + `*_query.py` + `.py`) = 9 files, plus 1 shared helper and unit tests. Two cross-tier reads migrated. `.infrahub.yml` unchanged (paths/names stable).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|------------|--------|
| **I. Schema-Driven Architecture** | Consumes the `device_designs` schema from 001 (already loaded); no new schema. Protocols already regenerated in 001. | ✅ Pass |
| **II. Idempotent Operations** | All `save()` keep `allow_upsert=True`; per-role designs keyed by `(container, role)` HFID make re-runs deterministic; tracking cleanup handles quantity-down/removed designs. Must be validated with `$infrahub-test-generator-idempotence`. | ✅ Pass (gated by idempotence validation) |
| **III. Type Safety** | Each `.gql` change is followed by regenerating `*_query.py`; `generate()` uses the typed model. No untyped dict access; no hand-editing generated models. | ✅ Pass |
| **IV. Test-Required Quality** | Unit tests for the resolution helper + absence handling; integration coverage of the generator chain (`$infrahub-run-integration-tests`); generator idempotence evidence. Ruff C901 ≤17 respected by extracting the resolver. | ✅ Pass |
| **V. Convention-Based Structure** | Generator/query names and `.infrahub.yml` registrations unchanged; `.gql` co-located with the Python consumer; shared helper lives in `src/solution_arista_avd/`. | ✅ Pass |

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-device-design-generators/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — refactor decisions
├── data-model.md        # Phase 1 — query shape + role→(template,quantity) resolution, cross-tier reads
├── quickstart.md        # Phase 1 — run/validate guide (parity + idempotence)
├── contracts/
│   └── generator-io-contract.md   # Per-generator input/output + shared helper signature
└── checklists/
    └── requirements.md  # Spec quality checklist (from /speckit-specify)
```

### Source Code (repository root)

```text
generators/
├── generate_fabric.py         # EDIT: read device_designs[super_spine]
├── generate_fabric.gql        # EDIT: select device_designs; drop amount_of_super_spines + super_spine_switch_template
├── fabric_generator_query.py  # REGENERATE from generate_fabric.gql
├── generate_pod.py            # EDIT: read device_designs[spine]; read fabric device_designs[super_spine] count (cross-tier)
├── generate_pod.gql           # EDIT: select pod device_designs + parent fabric device_designs; drop legacy fields
├── pod_generator_query.py     # REGENERATE from generate_pod.gql
├── generate_rack.py           # EDIT: read device_designs[leaf] + [l2leaf]; read pod device_designs[spine] count (cross-tier)
├── generate_rack.gql          # EDIT: select rack device_designs + pod device_designs; drop legacy fields
└── rack_generator_query.py    # REGENERATE from generate_rack.gql

src/solution_arista_avd/
└── generator.py               # EDIT: add shared resolve_device_designs() helper on GeneratorMixin

tests/unit/
└── test_device_design_resolution.py  # NEW: resolver + absence-means-none unit tests

# Co-requisite (separate Objects cycle, OUT OF SCOPE here):
objects/  10_fabric.yml, 11_rack.yml, 10a_*, 11a_*, 13a_*, 13b_*, 13c_*, 14_*  # migrate to device_designs
```

**Structure Decision**: Single Infrahub repository. Each generator keeps its three co-located files; the shared `role → (template_id, quantity)` resolution lives once on `GeneratorMixin` in `src/solution_arista_avd/generator.py` (DRY — the three generators and the two cross-tier reads all use it). `.infrahub.yml` needs no edit because query/generator names and file paths are unchanged.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
