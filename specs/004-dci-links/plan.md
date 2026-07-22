# Implementation Plan: DCI Links

**Branch**: `feat/dci-links` | **Date**: 2026-07-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-dci-links/spec.md`

## Summary

Update the DCI feature so DCI connections are ordinary `NetworkLink` objects
selected by `role = dci`, not a standalone DCI link kind. Preserve existing
Network Link behavior for non-DCI links, add the `border_leaf` device role that
maps to PyAVD `l3leaf`, keep the fabric-level DCI IP pool source, and extend the
AVD hostvars generator to emit deterministic profile-free PyAVD `l3_edge`
intent for valid DCI-role links.

The schema surface for DCI intent is intentionally small: `NetworkLink.role`,
`NetworkLink.include_in_underlay_protocol`, and two endpoint BGP ASN values.
Endpoint devices, endpoint interfaces, names, media, and physical connection
identity continue to come from the existing Network Link connector model.

## Technical Context

**Language/Version**: Python >=3.11, <3.14; local development uses Python 3.12
**Primary Dependencies**: Infrahub schema YAML, `infrahub-sdk[all]>=1.19.0`, pinned `pyavd>=6.3.0,<6.4.0`, pytest, ruff, mypy, yamllint
**Storage**: Infrahub graph data; schema YAML under `schemas/`; generated protocols in `src/solution_arista_avd/protocols.py`; generated hostvars stored as `AvdHostvarFile`
**Testing**: Infrahub schema check/load on a branch, protocol regeneration, GraphQL schema and return-type regeneration, PyAVD input validation, pytest unit tests, `uv run invoke lint`, mandatory Infrahub integration validation, and generator idempotence validation
**Target Platform**: Infrahub 1.10.x repository solution with branch/proposed-change workflows
**Project Type**: Single Infrahub repository solution: schemas, generators, transforms, menus, docs, tests
**Performance Goals**: Deterministic generation for at least 250 DCI-role links per fabric without duplicate allocations or unstable hostvar diffs
**Constraints**: Schema-first; no private lab hostnames/tokens in committed artifacts; do not hand-edit generated protocols or `*_query.py`; no standalone DCI link kind; no DCI-specific endpoint, protocol-selection, BFD, MTU, subnet, pool, link-id, endpoint-IP, endpoint-description, or enabled fields on `NetworkLink`; generated `l3_edge` uses native PyAVD keys and no `p2p_links_profiles`
**Scale/Scope**: One device-role choice, one `NetworkLink.role` choice, safe Network Link extension attributes, one fabric-level DCI pool relationship, hostvars query/model refresh, hostvars generator `l3_edge` emission, removal of stale standalone DCI link references, docs/tests/menu cleanup, helper-consolidation decision, unit/integration/idempotence validation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | Schema changes extend existing `DcimDevice`, `NetworkLink`, and `NetworkFabric` before generator code consumes them. Protocol regeneration is required. |
| II. Idempotent Operations | PASS | DCI prefix allocation uses stable link identity and normalized endpoint ordering; repeated generation must not duplicate links or allocations. |
| III. Type Safety | PASS | `generators/avd_device_hostvar.gql` changes require regenerated Pydantic models; production code consumes typed query models. |
| IV. Test-Required Quality | PASS | Unit tests, local lint, required integration validation, and generator idempotence validation are planned. |
| V. Convention-Based Structure | PASS | Schema, generator, docs, menu, and tests follow existing repository paths and naming. |

**Initial gate result**: PASS. The plan keeps DCI inside the existing Network
Link model, removes stale standalone link artifacts, and uses native PyAVD
`l3_edge` fields validated against the pinned pyAVD range.

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
├── dcim_extensions.yml       # DcimDevice.role, existing NetworkLink, NetworkLink DCI role/fields
└── dci.yml                   # NetworkFabric.dci_pool extension and stale DCI link removal/migration surface

src/solution_arista_avd/
├── addressing.py             # Shared /31 allocation helper used by DCI generation
├── avd.py                    # Map border_leaf to l3leaf
└── protocols.py              # Regenerated, not hand-edited

generators/
├── avd_device_hostvar.gql
├── generate_avd_device_inputs_query.py  # Regenerated after query changes
└── generate_avd_device_hostvar.py       # Border Leaf handling and l3_edge emission from NetworkLink.role=dci

menus/
└── menu.yml                  # Remove stale standalone DCI link navigation; keep Network Link discovery

docs/docs/
├── supported-capabilities.md
├── developer-guide/schemas.md
└── developer-guide/avd/
    ├── role-mapping.md
    ├── hostvars.md
    └── overview.md

tests/
├── integration/
│   └── test_e2e_pipeline.py
└── unit/
    ├── test_avd.py
    ├── test_dci_schema_contract.py
    ├── test_generate_avd_device_hostvar.py
    └── test_hostvar_ordering.py
```

**Structure Decision**: Extend the existing hostvars generator because `l3_edge`
is PyAVD hostvars input and the current pipeline validates and stores hostvars
per device. Keep the DCI physical-link model schema-first by extending
`NetworkLink`; do not create or expose a parallel link node. Keep the DCI pool
source at fabric scope so individual links do not gain prohibited pool or IP
relationships.

## Complexity Tracking

No Constitution Check violations.

## Phase 0 Research Output

`research.md` resolves all planning decisions:

- Border Leaf role placement and AVD classification.
- DCI modeled as `NetworkLink.role = dci`.
- Limited Network Link DCI attribute surface.
- Fabric-scoped DCI pool allocation.
- Profile-free PyAVD `l3_edge.p2p_links` output.
- Generator validation boundary and invalid-link reporting.
- Removal/migration decision for stale standalone DCI link artifacts.
- Consolidation decision for duplicate `allocate_p2p_prefix_from_pool` helpers.

## Phase 1 Design Output

`data-model.md` defines the updated entities and state transitions. Contracts in
`contracts/` define the schema, GraphQL input, allocation, and PyAVD output
surfaces. `quickstart.md` gives branch-based validation scenarios.

## Post-Design Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | PASS | `data-model.md` and contracts require schema/protocol/query updates before code consumption. |
| II. Idempotent Operations | PASS | Research and contracts specify stable allocation identifiers, duplicate detection, and repeated-run validation. |
| III. Type Safety | PASS | Contracts require GraphQL return-type regeneration and typed model usage. |
| IV. Test-Required Quality | PASS | Quickstart includes schema, unit, lint, integration, and generator idempotence validation. |
| V. Convention-Based Structure | PASS | Design keeps changes in established `schemas/`, `generators/`, `src/`, `menus/`, `docs/`, and `tests/` paths. |

**Final gate result**: PASS.
