# Implementation Plan: L2LS Fabric Example Conformance

**Branch**: `001-l2ls-example-conformance` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-l2ls-example-conformance/spec.md`

## Summary

Make the reference design reproduce the Arista AVD `l2ls-fabric` example to
golden-config parity: two MLAG `l2spine` switches, four `l2leaf` switches in two
MLAG rack pairs, tag-scoped pure-Layer-2 VLANs, connected server endpoints, and a
dual-homed firewall — rendering EOS that matches the example's
`intended/configs/*.cfg`.

This is the **schema / data-model cycle** (first in a Schema → Generator →
Transform chain). Its deliverable is the schema deltas and the source-of-truth
data model that let the example be represented faithfully. The technical approach:
extend four existing schema areas (spanning-tree priority roles, overlay-free L2
services, tag-based VLAN scoping, connected-endpoint/port-profile modeling),
reshape the `Fabric-L2LS` seed data to mirror the example, regenerate protocols,
and add schema-contract tests. Generator behavior (device naming, MLAG carving,
tag emission, endpoint cabling), transform/comparison-harness parity, and the
fabric-selectable integration tests are delivered in the subsequent cycles but are
gated by the schema contract defined here.

## Technical Context

**Language/Version**: Python >=3.11,<3.14 (schema authored as Infrahub YAML)

**Primary Dependencies**: Infrahub 1.10.1, `infrahub-sdk[all]>=1.19.0`,
`pyavd>=6.3.0,<6.4.0`

**Storage**: Infrahub graph (Neo4j/PostgreSQL) — schema nodes, generics,
relationships; seed data under `objects/`

**Testing**: `pytest` (unit + integration via testcontainers),
`$infrahub-run-integration-tests`, `$infrahub-test-generator-idempotence`;
schema-contract tests under `tests/unit/`

**Target Platform**: Infrahub server (Linux); rendered artifacts are Arista EOS
device configs

**Project Type**: Infrahub reference-design repository (schema + generators +
transforms + seed data)

**Performance Goals**: N/A for schema; end-to-end goal is zero-diff parity against
6 golden configs and zero PyAVD validation violations

**Constraints**: Schema changes MUST be additive/backward-compatible for the
existing EVPN/L3LS fabrics (Fabric-A/B/C, Campus, ISIS-LDP); no regression in
their rendered output. Schema load runs migrations against loaded data, so all
changes are validated on a branch first.

**Scale/Scope**: One fabric (`Fabric-L2LS`), 6 fabric devices + endpoints; 3 L2
VLANs; 2 MLAG rack pairs. Four schema areas touched.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.1.1:

| Principle | Gate | Status |
|-----------|------|--------|
| I. Schema-Driven Architecture | Every new entity/attribute/relationship defined in `schemas/` before code references it; schema-check + protocol regen after changes; approved namespaces (`Network.*`, `Evpn.*`, `Ipam.*`, `Dcim.*`, `Avd.*`, `Compute.*`); extensions used for existing base nodes | ✅ PASS — this cycle *is* the schema layer; all deltas are additive extensions to existing nodes in approved namespaces |
| II. Idempotent Operations | Generators idempotent (upsert, natural keys, checksum) | ✅ PASS (deferred) — no generator changes this cycle; the seed-data reshape uses existing HFIDs/upsert load; generator idempotence is a gate for the next cycle |
| III. Type Safety | Typed models; regenerate `protocols.py`; mypy clean | ✅ PASS — protocol regeneration is a required task; no hand-edited generated code |
| IV. Test-Required Quality | Unit + integration tests; lint (ruff/mypy/yamllint) | ✅ PASS — schema-contract unit tests added; integration coverage delivered with the fabric-selectable suite in a later cycle; `$infrahub-run-integration-tests` gates merge |
| V. Convention-Based Structure | Schema under `schemas/`; numbered `objects/`; docs under `docs/docs/` | ✅ PASS — extends existing schema files; reuses `objects/13*` seed files; updates `supported-capabilities.md` |

**Initial gate: PASS.** No violations; Complexity Tracking not required.

**Post-design re-check (after Phase 1): PASS.** The design is additive-only (new
enum values, one attribute made optional, new optional relationships — see
[contracts/schema-contract.md](./contracts/schema-contract.md) C5), keeps all
elements in approved namespaces (C6), tasks protocol regeneration (III) and
schema-contract + regression tests (IV), and defers generator idempotence to its
cycle's gate (II). No new violations introduced.

## Project Structure

### Documentation (this feature)

```text
specs/001-l2ls-example-conformance/
├── plan.md              # This file
├── research.md          # Phase 0 output — schema design decisions
├── data-model.md        # Phase 1 output — schema deltas + entities
├── quickstart.md        # Phase 1 output — validation guide
├── contracts/
│   └── schema-contract.md   # Phase 1 output — the schema contract downstream cycles depend on
├── checklists/
│   └── requirements.md  # From /speckit-specify
└── tasks.md             # From /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
schemas/
├── l3ls_extensions.yml        # NetworkSpanningTreePriority.role (+l2spine/l3spine); already hosts fabric/pod/MLAG L2LS extensions
├── evpn/evpn_services.yml     # EvpnTenant.mac_vrf_vni_base -> optional; EvpnL2Vlan +rack_tags/+avd_tags scoping
├── dcim_extensions.yml        # (already has l2spine/l2leaf roles, mlag_peer interface role)
├── objects/objects.yml        # connected-endpoint / port-profile schema (or escape-hatch decision)
└── avd/avd.yml                # AvdTag (already models rack scoping)

objects/
├── 13a_fabric_l2ls.yml        # reshape: DC1-mirroring fabric, 2 spines (MLAG), 2 racks, STP priorities
├── 13e_fabric_l2ls_services.yml  # reshape: overlay-free tenant + 3 VLANs (BLUE/GREEN/ORANGE) + tag scoping
└── 13h_fabric_l2ls_servers.yml   # reshape: named hosts + firewall endpoint model

src/solution_arista_avd/
└── protocols.py               # regenerated after schema changes

tests/unit/
├── test_avd_example_fabrics_schema_contract.py  # extend: l2spine STP role, overlay-free tenant, vlan tag scoping
└── test_l2ls_services_schema_contract.py        # new: pure-L2 + tag-scoping contract

docs/docs/
├── supported-capabilities.md            # update L2LS parity statement
└── developer-guide/avd/*.md             # role-mapping / hostvars notes as needed
```

**Structure Decision**: Single Infrahub reference-design repository. All schema
changes are additive extensions in existing files under `schemas/`; seed data
reuses the existing numbered `objects/13*` files; generated `protocols.py` is
regenerated, not hand-edited. No new top-level structure is introduced.

## Complexity Tracking

> No constitution violations — section intentionally empty.
