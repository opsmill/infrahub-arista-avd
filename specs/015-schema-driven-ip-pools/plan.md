# Implementation Plan: Schema-Driven AVD IP Pools

**Branch**: `015-schema-driven-ip-pools` | **Date**: 2026-06-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-schema-driven-ip-pools/spec.md`

## Summary

Make the AVD generator's IP pools fully schema-driven so the three hardcoded fallback literals (`10.250.0.0/16`, `10.251.0.0/24`, `10.255.0.0/24`) can be removed in the follow-up generator cycle.

**Corrected from spec (see [research.md](./research.md), R1):** four of the five pool relationships already exist in `schemas/l3ls_extensions.yml` as `optional: true` — `uplink_pool`, `vtep_pool` (fabric) and `mlag_peer_pool`, `mlag_l3_pool` (pod). The spec assumed they were missing. The actual schema delta is therefore:

1. **Add** one genuinely-missing relationship: a fabric-level `loopback_pool` (→ `CoreIPPrefixPool`) — the source for pyAVD `loopback_ipv4_pool`, currently the unconditional `10.255.0.0/24` literal that also **collides with the management subnet** (`10.255.0.0/24`).
2. **Flip** `uplink_pool` and `vtep_pool` from `optional: true` to `optional: false` (and make the new `loopback_pool` mandatory) so a fabric without them fails loudly at the data layer instead of falling back to literals.
3. **Keep** `mlag_peer_pool` / `mlag_l3_pool` optional — not every pod uses MLAG (already correct).
4. **Backfill seed data** so the mandatory flip is safe: Fabric-B currently has no uplink/vtep pools, so loading it would fail once they are mandatory. Add the missing pool objects and references for Fabric-B, plus a non-overlapping loopback pool for both fabrics.

All schema changes are made in the **extensions** file `schemas/l3ls_extensions.yml` (never `logical_design.yml`), per Constitution Principle I.

## Technical Context

**Language/Version**: Python >=3.11, <3.14 (no runtime code changes this cycle — schema YAML + seed YAML + protocol regeneration)
**Primary Dependencies**: `infrahub-sdk==1.18.1` (`infrahubctl` for schema check / protocols), Infrahub 1.9.x server
**Storage**: Infrahub (Neo4j graph); IP pools are `CoreIPPrefixPool` / `CoreIPAddressPool` built-ins
**Testing**: `infrahubctl schema check schemas/`, `inv load`, `pytest tests/integration` against a running instance
**Target Platform**: Infrahub repository solution (Docker Compose stack)
**Project Type**: Single project (Infrahub schema + generators + transforms)
**Performance Goals**: N/A (schema definition)
**Constraints**: New mandatory relationships must not break loading of existing seed data → migration-safe ordering required (see research.md R3). New loopback pool prefix MUST NOT overlap the management subnet (`10.255.0.0/24`).
**Scale/Scope**: 2 fabrics, ~6 pods in seed data; one new relationship + one optionality change on two existing relationships + seed-data backfill.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Schema-Driven Architecture | Schema change made before code; uses `extensions` block, not the original `logical_design.yml`; namespace `Network.*` unchanged; protocols regenerated after change | ✅ PASS — all changes in `l3ls_extensions.yml`; `infrahubctl protocols` is a planned step |
| II. Idempotent Operations | No generator logic changed this cycle; schema load and `inv load` are idempotent (`allow_upsert`) | ✅ PASS — N/A to schema-only delta |
| III. Type Safety | Protocol classes regenerated so the new `loopback_pool` relationship is typed for the downstream generator | ✅ PASS — `infrahubctl protocols --out src/solution_arista_avd/protocols.py` planned |
| IV. Test-Required Quality | Schema validated via `infrahubctl schema check`; full `inv load` exercises the mandatory-relationship migration; generator behavior tests deferred to the consuming cycle | ✅ PASS — validation steps defined in quickstart.md |
| V. Convention-Based Structure | Extension lives in existing `l3ls_extensions.yml`; seed data in numbered `objects/04a_l3ls_pools.yml` + `objects/10_fabric.yml` | ✅ PASS — no new conventions introduced |

**Result**: No violations. Complexity Tracking section omitted.

## Project Structure

### Documentation (this feature)

```text
specs/015-schema-driven-ip-pools/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — reconciles spec vs. actual schema
├── data-model.md        # Phase 1 output — relationship definitions
├── quickstart.md        # Phase 1 output — validate & load steps
├── contracts/
│   └── schema-extension.md   # The exact YAML delta (the "contract")
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
schemas/
└── l3ls_extensions.yml          # EDIT: add fabric loopback_pool; flip uplink_pool/vtep_pool to optional:false

objects/
├── 04a_l3ls_pools.yml           # EDIT: add Fabric-A/Fabric-B loopback pools + Fabric-B uplink/vtep pools
└── 10_fabric.yml                # EDIT: reference loopback_pool on both fabrics; add uplink/vtep on Fabric-B

src/solution_arista_avd/
└── protocols.py                 # REGENERATE: infrahubctl protocols (picks up loopback_pool)
```

**Structure Decision**: Single-project Infrahub solution. This cycle touches only declarative artifacts (schema YAML, seed YAML) plus the generated `protocols.py`. No generator/transform Python is edited here — that is the follow-up generator cycle.

## Complexity Tracking

No constitution violations — section intentionally omitted.
