# Implementation Plan: ContainerLab Topology Generation

**Branch**: `003-generate-containerlab-topology` | **Date**: 2026-07-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-generate-containerlab-topology/spec.md`

## Summary

Add an Infrahub transform that renders a ContainerLab topology file (`topology.clab.yml`,
`application/yaml`) from a `NetworkFabric` and its devices, cabling, management IPs, and device
types. The transform resolves a per-device-type EOS interface-mapping file for each device and
translates the Infrahub/EOS interface names on every link endpoint into their ContainerLab short
names using that mapping. An accompanying Ansible workflow uses the `opsmill.infrahub` collection to
pull the generated artifact (plus the interface-mapping files and per-device config artifacts it
references) onto the lab host and deploy the lab with ContainerLab.

**Technical approach**: Hybrid transform — a Python `InfrahubTransform` subclass walks the fabric
hierarchy (mirroring `CablingPlan`), builds a typed topology model, resolves device-type→mapping,
translates interface names, de-duplicates links, then renders YAML via a Jinja2 template. Interface
mappings are bundled static JSON files keyed by device-type model name.

## Technical Context

**Language/Version**: Python >=3.11, <3.14 (repo runs 3.12)
**Primary Dependencies**: `infrahub-sdk[all]` (`InfrahubTransform`, `execute_graphql`); Jinja2 (via SDK); PyYAML for safe serialization/round-trip validation; `opsmill.infrahub` + ContainerLab (Ansible workflow only)
**Storage**: Infrahub (Neo4j graph) — read-only via GraphQL; interface-mapping files are static repo resources under `lab/configs/eos-intf-mapping/`
**Testing**: pytest (`asyncio_mode=auto`) unit tests + Infrahub Resources Testing Framework YAML tests (`infrahubctl transform`/render)
**Target Platform**: Infrahub server 1.10.x; artifact rendered per fabric; ContainerLab on a lab host (Ansible)
**Project Type**: single (Infrahub repository solution — transforms/, queries in .gql, `.infrahub.yml` registration)
**Performance Goals**: Not latency-sensitive; render must be deterministic and complete for a full fabric (tens of devices, ~hundreds of links) within normal artifact-render time
**Constraints**: Deterministic output (stable ordering, FR-012); no untyped GraphQL access (Pydantic models); ruff C901 max-complexity=17; mypy strict; must fail loudly on unmapped device type / interface
**Scale/Scope**: One `topology.clab.yml` per fabric; two seeded fabrics (Fabric-A, Fabric-B); device types currently Dell PowerSwitch models (`Z9864F-ON`, `S5232F-ON`) with `Ethernet1/N` naming

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Schema-Driven Architecture | ✅ PASS | No new schema. Reuses existing `NetworkFabric`, `DcimDevice` (`role`, `mgmt_ip`, `device_type`), `NetworkLink`, `IpamIPAddress`. Interface-mapping files are cEOS runtime resources, not infrastructure data — modeling them as Infrahub objects is explicitly deferred to a separate cycle (spec Assumptions). |
| II. Idempotent Operations | ✅ PASS | Transform is a pure function of queried data; FR-012 mandates stable ordering so repeated renders of unchanged data are byte-identical. No mutations. |
| III. Type Safety | ✅ PASS | Pydantic query model `containerlab_topology_query.py`; typed helpers; mypy strict. Any ad-hoc secondary GraphQL (link endpoint fetch, à la CablingPlan) is narrowly scoped and typed at the boundary. |
| IV. Test-Required Quality | ✅ PASS | Unit tests for mapping resolution, interface translation, link dedup, edge cases; YAML-driven transform test rendering a fabric; `inv lint` (ruff+mypy+yamllint) green. |
| V. Convention-Based Structure | ✅ PASS | `transforms/containerlab_topology.py` + `containerlab_topology_query.py` + `containerlab_topology.gql`; template under `transforms/templates/`; registered in `.infrahub.yml`. Ansible artifacts live under `lab/`. |

**Result**: PASS — no violations, Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-generate-containerlab-topology/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── graphql-query.md
│   ├── artifact-output.md
│   └── interface-mapping.md
└── tasks.md             # Phase 2 (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
transforms/
├── containerlab_topology.py          # InfrahubTransform subclass (data prep + render)
├── containerlab_topology_query.py    # Pydantic models for the GraphQL response
├── containerlab_topology.gql         # GraphQL query (fabric → devices, device_type, mgmt_ip, links)
├── templates/
│   └── containerlab_topology.j2       # Jinja2 template rendering ContainerLab YAML
└── common.py                          # (optional) shared response-normalisation helpers

lab/
├── configs/eos-intf-mapping/
│   ├── <DeviceTypeModel>.json         # Per-device-type EOS interface-mapping files
│   └── ...
└── playbooks/
    └── deploy_clab.yml                # Ansible: pull artifact + referenced files, containerlab deploy

tests/
├── unit/
│   └── test_containerlab_topology.py  # Mapping resolution, name translation, dedup, edge cases
└── (transform YAML test definitions co-located per Resources Testing Framework)

.infrahub.yml                          # Register query, python_transform, artifact_definition
```

**Structure Decision**: Single-project Infrahub repository layout. The transform follows the exact
convention of the existing `cabling_plan` fabric-targeted transform (closest analog: same
NetworkFabric traversal to reach links). Ansible deployment assets are isolated under `lab/` so they
do not affect the Python package or linting targets.

## Complexity Tracking

> No Constitution Check violations — this section intentionally left empty.
