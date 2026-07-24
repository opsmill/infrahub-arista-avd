# Implementation Plan: AVD Example Designs (Generator + Objects)

**Branch**: `006-avd-example-designs` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-avd-example-designs/spec.md`

## Summary

Make each of the seven AVD example scenarios demonstrable end to end: extend the
topology and hostvar generators to build/render the new designs, and ship one
loadable seed design per scenario (Fabric-C style). This builds on the `005`
schema cycle (roles, EVPN inputs, underlay modes) — no schema is re-added.

Two delivery models, decided in research:

- **Fabric-model scenarios** (Single-DC L3LS, 5-stage Clos, Dual-DC, L2LS,
  Campus) build topology through the existing `generate-fabric → generate-pod →
  generate-rack` chain, extended with role/underlay-aware branches, and render
  through `generate-avd-device-hostvar`.
- **WAN/provider scenarios** (ISIS-LDP IPVPN, CV-Pathfinder) seed their devices
  directly (they are not leaf-spine) and rely on the hostvar + structured-config
  generators plus `avd_custom_hostvars` escape-hatch payloads.

The central generator gap is that the hostvar generator sets PyAVD `type` but
never sets AVD `design.type`, and has no rendering for the new EVPN behaviors.
This plan adds: per-fabric `design.type` selection, `evpn_vlan_aware_bundles`
consumption, super-spine EVPN route-server derivation, `evpn_gateway` rendering,
and clean handling of the `none`/`isis-ldp` underlay values — all behind the
existing idempotent, checksum-guarded generation.

## Technical Context

**Language/Version**: Python >=3.11, <3.14; local development uses Python 3.12
**Primary Dependencies**: `infrahub-sdk[all]>=1.19.0`, pinned `pyavd>=6.3.0,<6.4.0`, Infrahub schema YAML + object data, pytest, ruff, mypy, yamllint
**Storage**: Infrahub graph data; seed data under `objects/`; generated hostvars stored as `AvdHostvarFile`, structured config as `AvdStructuredConfigFile`; artifacts rendered by the AVD transforms
**Testing**: pytest unit tests, `uv run invoke lint`, PyAVD input/render validation per scenario, mandatory `$infrahub-run-integration-tests`, and `$infrahub-test-generator-idempotence` for generator changes
**Target Platform**: Infrahub 1.10.x repository solution with branch/proposed-change workflows
**Project Type**: Single Infrahub repository solution: generators, objects, transforms, docs, tests
**Performance Goals**: Deterministic, idempotent generation for each scenario; re-running the generator chain against unchanged seed data yields no artifact diffs; loading all seven designs into one instance does not collide on pools/ASNs
**Constraints**: Build on `005` schema (do not re-add schema); `allow_upsert=True` everywhere; checksum-based change detection preserved; generated files (protocols, `*_query.py`) regenerated not hand-edited; existing L3LS/Fabric-A/B/C output unchanged; escape-hatch deep-merge precedence (generated wins) unchanged; every device resolves to a valid AVD node type (fail loud otherwise); WAN devices must not enter the leaf-spine topology groups
**Scale/Scope**: 7 seed designs; topology-generator branches for standalone L2LS and campus (hierarchical IDF); hostvar rendering for `design.type`, vlan-aware bundles, route-server, gateway, and `none`/`isis-ldp` underlay; escape-hatch payloads for campus access / MPLS-VPN / SD-WAN

No NEEDS CLARIFICATION remain — the delivery model, design-type strategy, and
scenario priorities are resolved in research.md.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Consumes the `005` schema; no new schema. Generators only emit shapes the loaded schema permits. |
| II. Idempotent Operations | PASS | All `save()` use `allow_upsert=True`; checksum-based skipping preserved; `$infrahub-test-generator-idempotence` planned for all seven designs. This is the highest-risk principle and is gated explicitly. |
| III. Type Safety | PASS | Any changed GraphQL query has its typed model regenerated; production code consumes typed models; generated files not hand-edited. |
| IV. Test-Required Quality | PASS | Unit tests for new generator branches and hostvar rendering; per-scenario render validation; integration + idempotence validation. |
| V. Convention-Based Structure | PASS | Generators keep `generate_<entity>.py` naming; seed data uses numbered `objects/` files in load order (Fabric-C convention); docs under `docs/docs/`. |

**Initial gate result**: PASS. Highest risk is idempotence across many new
objects — every generator write is upsert-based and validated by repeated runs.

## Project Structure

### Documentation (this feature)

```text
specs/006-avd-example-designs/
├── plan.md              # This file
├── research.md          # Phase 0: delivery model, design-type, topology-branch decisions
├── data-model.md        # Phase 1: generated entities + seed-design structure
├── quickstart.md        # Phase 1: per-scenario load/generate/validate steps
├── contracts/
│   ├── generator-hostvars.md   # What the generators must emit per scenario
│   └── seed-objects.md         # Seed-design file structure and load-order contract
├── checklists/
│   └── requirements.md  # Created by /speckit.specify
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
generators/
├── generate_fabric.py            # super-spine creation; unaffected for L2LS/campus unless super-spines used
├── generate_pod.py               # spine creation + spine↔super-spine cabling
├── generate_rack.py              # leaf/l2leaf creation + cabling; add L2LS (l2spine/l3spine) and campus hierarchical-IDF branches
├── generate_avd_device_hostvar.py# add design.type, vlan-aware bundles, route-server, evpn_gateway, none/isis-ldp underlay handling
├── avd_device_hostvar.gql        # add fields (evpn_vlan_aware_bundles, evpn_gateway) if consumed
└── *_query.py                    # regenerated typed models (not hand-edited)

src/solution_arista_avd/
├── avd.py                        # role→type mapping (from 005); add design-type helper if needed
└── protocols.py                  # regenerated

objects/
├── NN*_single_dc_l3ls_*.yml      # seed design per scenario (Fabric-C style)
├── NN*_multipod_*.yml
├── NN*_dual_dc_*.yml
├── NN*_l2ls_*.yml
├── NN*_campus_*.yml
├── NN*_isis_ldp_ipvpn_*.yml
└── NN*_cv_pathfinder_*.yml

docs/docs/
├── supported-capabilities.md
└── developer-guide/avd/{overview,role-mapping,hostvars,extending,debugging}.md

tests/
├── unit/
│   ├── test_generate_avd_device_hostvar.py   # design.type, route-server, gateway, vlan-aware, underlay modes
│   ├── test_hostvar_ordering.py              # deterministic ordering for new shapes
│   └── test_generate_rack.py (or similar)    # L2LS/campus topology branches
└── integration/
    └── test_e2e_pipeline.py                  # per-scenario render + idempotence
```

**Structure Decision**: Extend the existing generator chain rather than adding
parallel generators — L2LS and campus are variations of leaf-spine topology, so
they belong as role/underlay-aware branches in `generate_rack`/`generate_pod`
and rendering branches in the hostvar generator. WAN/provider scenarios do not
fit the leaf-spine model, so they are delivered as directly-seeded devices plus
escape-hatch payloads, avoiding speculative WAN generators. Seed designs follow
the Fabric-C convention (own suffixed numbered files) so they are additive and
load deterministically.

## Complexity Tracking

No Constitution Check violations.

Scope risk (not a violation): this feature is large and spans five generator
behaviors plus seven seed designs. It is managed by phasing — P1 (scenarios 1–3)
is a shippable increment on its own; P2 (4–5) and P3 (6–7) follow. Per `005`
research R8, scenarios 6–7 may be split into a dedicated feature if their depth
warrants; this plan keeps them in scope but last.

## Phase 0 Research Output

`research.md` resolves:

- Delivery model per scenario (generated topology vs directly-seeded devices).
- Setting AVD `design.type` per fabric and why the default `node_type_keys`
  alone is insufficient for correct rendering.
- Mapping the `none` underlay mode to AVD L2LS (`design.type: l2ls`, no
  `underlay_routing_protocol`) and `isis-ldp` to AVD's underlay value.
- Super-spine EVPN route-server derivation and `evpn_vlan_aware_bundles`
  rendering.
- `evpn_gateway` next-hop-self rendering for the dual-DC gateway leaves.
- Campus hierarchical IDF modeling with existing rack/parent relationships.
- Seed-design addressing/ASN isolation so all seven can coexist.
- Idempotence strategy for the new objects and escape-hatch payloads.

## Phase 1 Design Output

`data-model.md` defines the generated entities and the seed-design structure per
scenario. Contracts in `contracts/` define what the generators must emit
(hostvars per scenario) and the seed-object file/load-order contract.
`quickstart.md` gives per-scenario load → generate → render → idempotence steps.

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Design consumes existing schema; contracts emit only permitted shapes. |
| II. Idempotent Operations | PASS | Contracts and quickstart require upserts, deterministic ordering, and repeated-run validation for every design. |
| III. Type Safety | PASS | Query/model regeneration required where queries change; typed models consumed. |
| IV. Test-Required Quality | PASS | Unit + integration + idempotence coverage specified per scenario. |
| V. Convention-Based Structure | PASS | Generator naming, numbered `objects/`, and docs paths preserved. |

**Final gate result**: PASS.
