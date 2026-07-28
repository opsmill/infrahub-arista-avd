# Implementation Plan: Device-Design Seed Data Migration

**Branch**: `007-device-design-objects` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-device-design-objects/spec.md`

## Summary

Migrate the eight numbered seed files that define fabrics, pods, and racks from the legacy per-role fields (`amount_of_<role>s` + `<role>_switch_template`) to inline `device_designs` entries (`role`, `device_quantity`, `device_template`), and remove the legacy fields. Each container reproduces its current effective design — implicit default counts (spines default 4) are materialized explicitly, and zero-count roles (single-tier fabrics, fabric-role pods, racks without L2 leaves) become absent designs. Because the pod/rack legacy template relationships are required in the Stage-1 schema, dropping them from seed data co-loads with the 005 Stage-3 schema removal, and the whole thing lands with the 006 generator hard cutover on one integration branch.

## Technical Context

**Language/Version**: Infrahub object YAML (`apiVersion: infrahub.app/v1`, `kind: Object`). No Python.

**Primary Dependencies**: `infrahubctl object load/validate`, Infrahub 1.10.1, the `device_designs` schema from 001. No new dependencies.

**Storage**: Infrahub graph — populates `NetworkFabricDeviceDesign` / `NetworkPodDeviceDesign` / `NetworkRackDeviceDesign` as inline component children of their containers.

**Testing**: `uv run infrahubctl object load objects --branch <b>` (load-time validation); `$infrahub-run-integration-tests` for the full load + generator-chain parity per Constitution Principle IV.

**Target Platform**: Infrahub server; seed data loaded via `infrahubctl object load` / repository sync.

**Project Type**: Infrahub reference-design repository — Objects artifact cycle (single project).

**Performance Goals**: N/A.

**Constraints**: Parity (same effective design → same generated fabric); idempotent re-load (designs keyed by `(container, role)` HFID); preserve existing file numbering/load order; materialize implicit default counts explicitly (`device_quantity` has no default, requires ≥1); drop legacy fields only where the schema no longer requires them (co-load with Stage-3).

**Scale/Scope**: 8 files (`10_fabric`, `10a_fabric_c_fabric`, `11_rack`, `11a_fabric_c_rack`, `13a_fabric_l2ls`, `13b_fabric_campus`, `13c_fabric_isis_ldp`, `14_fabric_single_dc_l3ls`); ~fabrics/pods across them plus dozens of racks (`11_rack.yml` alone has 36 legacy-field occurrences). No new files; no `.infrahub.yml` change.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|------------|--------|
| **I. Schema-Driven Architecture** | Data conforms to the `device_designs` schema from 001; no new schema here. The load depends on the schema having the legacy fields removed (005 Stage-3) so the migrated data validates. | ✅ Pass |
| **II. Idempotent Operations** | The object loader upserts by human_friendly_id; device designs keyed `(container, role)` re-load without duplicates. No generator logic in this cycle. | ✅ Pass |
| **III. Type Safety** | N/A — no Python/GraphQL code; pure data. | ✅ Pass (n/a) |
| **IV. Test-Required Quality** | Validated by loading the full `objects/` set and running the generator chain for parity (`$infrahub-run-integration-tests`); `test_e2e_pipeline.py` covers generation from seed data. `yamllint` on the edited files. | ✅ Pass |
| **V. Convention-Based Structure** | Numbered files under `objects/` keep their names and load order; templates already load earlier (`06_device_template.yml`). | ✅ Pass |

**Result**: No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/007-device-design-objects/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 — migration decisions
├── data-model.md        # Phase 1 — device_designs entry shape + per-tier/per-file parity mapping
├── quickstart.md        # Phase 1 — load & parity validation guide
├── contracts/
│   └── seed-migration-contract.md   # Old-field → device_designs mapping + per-file inventory
└── checklists/
    └── requirements.md  # Spec quality checklist (from /speckit-specify)
```

### Source Code (repository root)

```text
objects/
├── 10_fabric.yml                 # EDIT: Fabric-A/B super_spine designs; nested pod spine designs (pods rely on DEFAULT amount_of_spines=4 → materialize 4)
├── 10a_fabric_c_fabric.yml       # EDIT: Fabric-C fabric/pods (amount_of_super_spines: 0 → no super_spine design; spine qty explicit)
├── 11_rack.yml                   # EDIT: rack leaf (+ l2leaf) designs (heaviest file)
├── 11a_fabric_c_rack.yml         # EDIT: Fabric-C rack leaf designs
├── 13a_fabric_l2ls.yml           # EDIT: L2LS fabric/pod/rack designs (spine qty 2)
├── 13b_fabric_campus.yml         # EDIT: campus designs
├── 13c_fabric_isis_ldp.yml       # EDIT: ISIS-LDP designs
└── 14_fabric_single_dc_l3ls.yml  # EDIT: single-DC L3LS designs

objects/06_device_template.yml    # UNCHANGED: CoreObjectTemplate referenced by device_designs (loads earlier)

# Co-loaded on the integration branch (from other cycles, not authored here):
schemas/  001 device_design.yml (Stage-1) + 005 Stage-3 state:absent removals
generators/  002 device-design-driven generators
```

**Structure Decision**: Single Infrahub repository. Edits are confined to the eight seed files that carry legacy fields; each container gains an inline `device_designs:` block and loses its legacy per-role fields. No new files, no renumbering, no `.infrahub.yml` change — templates already load before the fabric/rack files.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
