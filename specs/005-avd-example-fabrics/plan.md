# Implementation Plan: AVD Example Fabric Designs

**Branch**: `005-avd-example-fabrics` | **Date**: 2026-07-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-avd-example-fabrics/spec.md`

## Summary

Deliver a demonstrable fabric design for each of the seven official Arista AVD
6.2 example scenarios, closing gaps with **native schema changes** where the
capability is reusable and first-class, and with the **`avd_custom_hostvars`
escape hatch** where a full native model would be disproportionate.

This plan covers the **schema-first cycle**. It defines the schema surface the
seven scenarios need — new device roles and their AVD node-type mappings, a
vlan-aware-bundle input, an EVPN route-server derivation, an EVPN DC Gateway
flag, an "underlay: none" mode, and an `isis-ldp` underlay choice — plus the
per-capability native-vs-escape-hatch classification that governs the later
generator and objects cycles. The generator paths (standalone L2LS, campus
tiers, multi-DC/DCI assistance) and the seed designs that prove each scenario
render are delivered in the follow-on `/speckit.specify` cycles noted in the
spec's Assumptions; this cycle makes them possible and validates the schema they
depend on.

The schema surface is intentionally minimal per scenario: add only the roles,
choices, and flags that must be first-class (selected in the UI, mapped to an
AVD node type, allocated, validated, or generated deterministically). Everything
scenario-specific and pass-through — dot1x/NAC, PoE, port profiles, in-band
management, MPLS/VPN-IPv4 rendering, CV-Pathfinder/DPS/virtual-topologies — flows
through the existing `avd_custom_hostvars` deep-merge surface.

## Technical Context

**Language/Version**: Python >=3.11, <3.14; local development uses Python 3.12
**Primary Dependencies**: Infrahub schema YAML, `infrahub-sdk[all]>=1.19.0`, pinned `pyavd>=6.3.0,<6.4.0`, pytest, ruff, mypy, yamllint
**Storage**: Infrahub graph data; schema YAML under `schemas/`; generated protocols in `src/solution_arista_avd/protocols.py`; generated hostvars stored as `AvdHostvarFile`
**Testing**: Infrahub schema check/load on a branch, protocol regeneration, GraphQL schema and return-type regeneration, PyAVD input validation, pytest unit tests, `uv run invoke lint`, mandatory Infrahub integration validation, and generator idempotence validation
**Target Platform**: Infrahub 1.10.x repository solution with branch/proposed-change workflows
**Project Type**: Single Infrahub repository solution: schemas, generators, transforms, menus, docs, tests
**Performance Goals**: Deterministic, idempotent generation for each scenario design; re-running generation against unchanged seed data produces no artifact diffs
**Constraints**: Schema-first; new attributes on existing nodes MUST be optional or defaulted so existing L3LS data stays valid; do not hand-edit generated protocols or `*_query.py`; every new role MUST have a `ROLE_TO_AVD_TYPE` mapping; escape-hatch keys MUST be accepted by the pinned pyAVD range and captured as seed data (not manual UI edits); the already-supported Single-DC L3LS scenario MUST NOT change behavior
**Scale/Scope**: Seven scenario designs. Native schema additions: device roles (`l2spine`, `l3spine`, and minimal provider/WAN roles `p`, `pe`, `rr`, `wan_router`, `wan_rr`), an EVPN vlan-aware-bundle input, super-spine EVPN route-server derivation, an EVPN DC Gateway flag, an "underlay: none" mode, and an `isis-ldp` underlay choice. Escape hatch: campus access features (dot1x/PoE/port-profiles/in-band mgmt), MPLS/VPN-IPv4 rendering (ISIS-LDP IPVPN), and the CV-Pathfinder SD-WAN surface.

No NEEDS CLARIFICATION remain: the seven scenarios, the pyAVD version, and the
native-vs-escape-hatch decision principle are fixed by the spec.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Every new role, choice, and flag is defined in `schemas/` before generators or objects consume it. Protocol regeneration is required after schema changes. |
| II. Idempotent Operations | PASS | Schema additions are optional/defaulted; the follow-on generator and objects cycles carry the idempotence obligation (checksum-based change detection, upserts, deterministic ordering). This cycle adds no non-idempotent behavior. |
| III. Type Safety | PASS | Query/schema changes trigger regenerated Pydantic models and protocols; production code consumes typed models. Generated files are regenerated, never hand-edited. |
| IV. Test-Required Quality | PASS | Schema contract tests, `ROLE_TO_AVD_TYPE` unit tests, lint, and — for the follow-on generator/objects cycles — integration and generator-idempotence validation are planned. |
| V. Convention-Based Structure | PASS | Changes stay in established `schemas/`, `src/solution_arista_avd/`, `generators/`, `objects/`, `docs/`, and `tests/` paths and naming. |

**Initial gate result**: PASS. The plan keeps the feature schema-first, adds only
minimal first-class schema surface, and routes scenario-specific behavior through
the existing escape hatch, preserving existing L3LS behavior.

## Project Structure

### Documentation (this feature)

```text
specs/005-avd-example-fabrics/
├── plan.md              # This file
├── research.md          # Phase 0 output: per-capability native-vs-escape-hatch decisions
├── data-model.md        # Phase 1 output: role/attribute/flag entities and validation rules
├── quickstart.md        # Phase 1 output: branch-based schema validation scenarios
├── contracts/           # Phase 1 output
│   ├── schema.md            # Native schema change contract
│   └── escape-hatch.md      # avd_custom_hostvars usage + render/demonstrability contract
├── checklists/
│   └── requirements.md  # Created by /speckit.specify
└── tasks.md             # Phase 2 output, created by /speckit.tasks (not this command)
```

### Source Code (repository root)

```text
schemas/
├── dcim_extensions.yml       # DcimDevice.role: add l2spine, l3spine, p, pe, rr, wan_router, wan_rr
├── l3ls_extensions.yml       # NetworkFabric: underlay "none" mode, isis-ldp underlay choice,
│                             #   evpn_vlan_aware_bundles input, EVPN DC Gateway flag surface
└── avd/avd.yml               # Avd.Evpn: vlan-aware-bundle / route-server settings if placed here

src/solution_arista_avd/
├── avd.py                    # ROLE_TO_AVD_TYPE: map new roles to AVD node types
└── protocols.py             # Regenerated, not hand-edited

generators/
├── avd_device_hostvar.gql               # Query fields for new inputs (regenerate models)
├── generate_avd_device_inputs_query.py  # Regenerated after query changes
└── generate_avd_device_hostvar.py       # (follow-on generator cycle) emit new inputs / derive evpn_role

objects/
└── NN_*.yml                  # (follow-on objects cycle) seed design per scenario

docs/docs/
├── supported-capabilities.md            # Update per-scenario status
└── developer-guide/avd/
    ├── role-mapping.md                  # New roles → AVD node types
    ├── hostvars.md                      # New inputs and escape-hatch usage
    └── extending.md                     # Native-vs-escape-hatch decision guidance

tests/
├── unit/
│   ├── test_avd.py                       # ROLE_TO_AVD_TYPE coverage for new roles
│   └── test_avd_example_fabrics_schema_contract.py  # New role/choice/flag contract tests
└── integration/
    └── test_e2e_pipeline.py             # (follow-on) render each scenario design
```

**Structure Decision**: Keep schema changes in the existing extension files
(`dcim_extensions.yml` for roles, `l3ls_extensions.yml` for fabric-level
underlay/overlay inputs, `avd/avd.yml` for EVPN settings) rather than new files,
because each addition extends an existing node. Map new roles in the single
`ROLE_TO_AVD_TYPE` source of truth. Do not add scenario-specific nodes for
campus/WAN/SD-WAN features; those flow through `avd_custom_hostvars`. Defer
device creation, cabling, and seed designs to the generator and objects cycles so
this cycle stays schema-first and independently validatable.

## Complexity Tracking

No Constitution Check violations.

The one scoping risk — scenarios 6 (ISIS-LDP IPVPN) and 7 (CV-Pathfinder) are
whole new routing/WAN domains — is handled by phasing, not by a constitution
exception: this cycle adds only their minimal native anchors (roles, underlay
choice) and classifies the rest as escape hatch. Their full generator/objects
work is recommended for a dedicated feature (see research.md, Decision R8).

## Phase 0 Research Output

`research.md` records the per-capability native-vs-escape-hatch decisions:

- Single-DC L3LS: no schema change (baseline).
- 5-stage Clos: native `evpn_vlan_aware_bundles` input + super-spine EVPN
  route-server derivation.
- Dual-DC: native EVPN DC Gateway flag; multi-DC composition via seed data.
- L2LS: native `l2spine`/`l3spine` roles + "underlay: none" mode.
- Campus: reuse `l3spine`/`l2leaf`; OSPF underlay already native; access features
  via escape hatch.
- ISIS-LDP IPVPN: native `isis-ldp` underlay choice + minimal `p`/`pe`/`rr`
  roles; MPLS/VPN-IPv4 rendering via escape hatch.
- CV-Pathfinder: native `wan_router`/`wan_rr` roles; SD-WAN surface via escape
  hatch.
- Phasing recommendation for scenarios 6–7.

## Phase 1 Design Output

`data-model.md` defines the new roles, attributes, and flags with validation
rules and their AVD node-type mappings. Contracts in `contracts/` define the
native schema surface and the escape-hatch/demonstrability surface.
`quickstart.md` gives branch-based schema validation scenarios.

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | `data-model.md` and contracts require schema/protocol/query updates before consumption. |
| II. Idempotent Operations | PASS | Schema additions are optional/defaulted; idempotence obligations are explicit for the follow-on generator/objects cycles. |
| III. Type Safety | PASS | Contracts require protocol and GraphQL return-type regeneration and typed model usage. |
| IV. Test-Required Quality | PASS | Quickstart includes schema check, role-mapping unit tests, contract tests, and lint; integration/idempotence apply to follow-on cycles. |
| V. Convention-Based Structure | PASS | Design keeps changes in established `schemas/`, `src/`, `generators/`, `objects/`, `docs/`, and `tests/` paths and naming. |

**Final gate result**: PASS.
