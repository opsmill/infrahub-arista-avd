# Implementation Plan: DCI Links

**Branch**: `feat/dci-links` | **Date**: 2026-07-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-dci-links/spec.md`

## Summary

Implement DCI link support for the current Arista AVD reference design phase.
Add a `border_leaf` device role that maps to PyAVD `l3leaf`, add a
user-facing `NetworkDciLink` model that reuses the existing `NetworkLink`
physical endpoint behavior through the shared `DcimConnector` generic, add a
fabric-level DCI IP pool source, and extend
the AVD hostvars generation path to emit PyAVD `l3_edge` intent for valid DCI
links between Border Leaf devices.

The DCI link schema owns only DCI-specific underlay participation and endpoint
BGP ASN intent. Endpoint devices, endpoint interfaces, descriptions, and base
link identity are inherited from shared Network Link behavior. Point-to-point
addresses are allocated from the fabric DCI IP pool and emitted as `ip` values
in generated `l3_edge.p2p_links`; they are not modeled as direct DCI-specific
fields on the DCI link.

## Technical Context

**Language/Version**: Python >=3.11, <3.14; local development uses Python 3.12
**Primary Dependencies**: Infrahub schema YAML, `infrahub-sdk[all]>=1.19.0`, pinned `pyavd>=6.3.0,<6.4.0` (validated locally as pyavd 6.3.0), pytest, ruff, mypy, yamllint
**Storage**: Infrahub graph data; schema YAML under `schemas/`; generated protocols in `src/solution_arista_avd/protocols.py`; generated hostvars stored as `AvdHostvarFile`
**Testing**: `infrahubctl schema check`, protocol regeneration, GraphQL schema and return-type regeneration, PyAVD input validation, pytest unit tests, `uv run invoke lint`, mandatory Infrahub integration validation, and generator idempotence validation
**Target Platform**: Infrahub 1.10.x repository solution with branch/proposed-change workflows
**Project Type**: Single Infrahub repository solution: schemas, generators, transforms, menus, docs, tests
**Performance Goals**: Deterministic generation for at least 250 DCI links per fabric without duplicate allocations or unstable hostvar diffs
**Constraints**: Schema-first; no private lab hostnames/tokens in committed artifacts; do not hand-edit generated protocols or `*_query.py`; no DCI-specific endpoint, protocol-selection, BFD, MTU, subnet, pool, link-id, endpoint-IP, endpoint-description, or enabled fields on `NetworkDciLink`; generated `l3_edge` uses native PyAVD keys
**Scale/Scope**: One device-role choice, schema-safe reuse of `NetworkLink` physical behavior by having `NetworkDciLink` inherit the same `DcimConnector` generic as `NetworkLink`, one `NetworkDciLink` node, one fabric-level DCI pool relationship, hostvars query/model refresh, hostvars generator `l3_edge` emission, menu/docs updates, unit/integration/idempotence validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Schema changes define role, `NetworkDciLink`, and DCI pool source before generator code reads them. Protocol regeneration is required. |
| II. Idempotent Operations | PASS | DCI prefix allocation uses stable link identity; generated `p2p_links` ordering is deterministic; repeated generation must not duplicate links or allocations. |
| III. Type Safety | PASS | `generators/avd_device_hostvar.gql` changes require regenerated Pydantic models; production code consumes typed query models. |
| IV. Test-Required Quality | PASS | Unit tests, local lint, required integration validation, and generator idempotence validation are planned. |
| V. Convention-Based Structure | PASS | Schema, menu, generator, docs, and tests follow existing repository paths and naming. |

**Initial gate result**: PASS. The plan keeps the DCI schema surface aligned
with the feature specification and uses native PyAVD `l3_edge` fields validated
against pyavd 6.3.0.

## Project Structure

### Documentation (this feature)

```text
specs/004-dci-links/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── schema.md
│   └── graphql-dci-generator-input.md
└── tasks.md              # Phase 2 output, not created by /speckit-plan
```

### Source Code (repository root)

```text
schemas/
├── dcim_extensions.yml       # DcimConnector behavior and DcimDevice.role choice
├── dci.yml                   # NetworkDciLink schema and NetworkFabric.dci_pool extension
└── ipam_extensions.yml       # No DCI prefix role metadata is added for this feature

src/solution_arista_avd/
├── addressing.py             # Reuse or extend allocation helpers for /31 DCI prefix/IP assignment
├── avd.py                    # Map border_leaf -> l3leaf
└── protocols.py              # Regenerated, not hand-edited

generators/
├── avd_device_hostvar.gql
├── generate_avd_device_inputs_query.py  # Regenerated after query changes
└── generate_avd_device_hostvar.py       # Border Leaf handling and l3_edge emission

menus/
└── menu.yml                  # Add user-facing DCI Links navigation

docs/docs/
├── supported-capabilities.md
├── developer-guide/schemas.md
└── developer-guide/avd/
    ├── role-mapping.md
    ├── hostvars.md
    └── overview.md

tests/
└── unit/
    ├── test_avd.py
    ├── test_generate_avd_device_hostvar.py
    └── test_hostvar_ordering.py
```

**Structure Decision**: Extend the existing hostvars generator because `l3_edge`
is PyAVD hostvars input and the current pipeline validates and stores hostvars
per device. Keep the DCI physical-link model schema-first by having
`NetworkDciLink` inherit the same `DcimConnector` generic used by
`NetworkLink`, because Infrahub schema inheritance is modeled through generics
rather than concrete node inheritance in this repository. Add the DCI pool source at
fabric scope so individual DCI links do not gain prohibited pool or IP
relationships.

## Complexity Tracking

No Constitution Check violations.

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | `data-model.md` and contracts require schema and protocol updates before code consumption. |
| II. Idempotent Operations | PASS | Research and contracts specify stable allocation identifiers, duplicate detection, and repeated-run validation. |
| III. Type Safety | PASS | Contracts require GraphQL return-type regeneration and typed model usage. |
| IV. Test-Required Quality | PASS | Quickstart includes schema, unit, lint, integration, and generator idempotence validation. |
| V. Convention-Based Structure | PASS | Design keeps changes in established `schemas/`, `generators/`, `src/`, `menus/`, `docs/`, and `tests/` paths. |

**Final gate result**: PASS.
