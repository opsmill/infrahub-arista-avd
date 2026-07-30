# Implementation Plan: ContainerLab Topology for the Multi-Domain Fabric

**Branch**: `atg/quick-windows-bake` (spec dir `008-containerlab-multi-domain`) | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-containerlab-multi-domain/spec.md`

## Summary

Close the gap between the existing `containerlab_topology` artifact and the committed
`lab/topology.clab.yml`, then make the result deployable from Infrahub with one Ansible command.

Four substantive changes, in dependency order:

1. **Schema** — two optional `Text` attributes (`DcimPlatform.containerlab_image`,
   `DcimDeviceType.containerlab_interface_mapping`) so node kind, container image, and
   interface-mapping bind are data rather than code.
2. **Object data** — populate those attributes, and add a `Linux` platform carrying
   `containerlab_os: linux` / `containerlab_image: lab-server` for the server nodes.
3. **Transform** — include `border_leaf` (currently dropping 4 devices, 4 DCI links and 8
   uplinks), read kind/image/mapping from the graph, emit multiple kinds and per-node binds,
   include `ComputePhysicalServer` as `linux` nodes with netplan binds, make subnet derivation
   deterministic, and replace the inline GraphQL string with a registered query plus generated
   return types.
4. **Ansible** — fix the four verified parameter/return-key defects in
   the deploy playbook, stage every bind source, and wire it to a `Makefile` target. The playbook
   lives in `ansible/` so Semaphore can run it.

The artifact stays fabric-scoped: `Fabric-L3LS-Multi-Domain` is a single `NetworkFabric`
containing both pods, so no new target group is needed.

## Technical Context

**Language/Version**: Python >=3.11,<3.14 (repo venv on 3.12.13)

**Primary Dependencies**: `infrahub-sdk[all]` >=1.19.0 (installed 1.22.0), `pyavd>=6.3.0,<6.4.0`,
Jinja2, PyYAML. Deploy side: `opsmill.infrahub` 1.8.3 Ansible collection, `containerlab` 0.77.0,
Docker.

**Storage**: Infrahub graph (Neo4j) — no new storage. Artifact bodies stored by Infrahub.

**Testing**: pytest + pytest-asyncio. Unit at `tests/unit/test_containerlab_topology.py`;
integration at `tests/integration/test_e2e_pipeline.py`.

**Target Platform**: Infrahub 1.10.1 server-side artifact rendering; Linux ContainerLab host for
deployment.

**Project Type**: Infrahub repository — transform (hybrid Python + Jinja2) with a schema
prerequisite, plus an Ansible deployment playbook.

**Performance Goals**: Not latency-sensitive. One bounded constraint: link-endpoint resolution
batches 50 IDs per query and must stay O(links), not O(devices × links).

**Constraints**: Ruff C901 max-complexity 17. mypy `disallow_untyped_defs = true`. Output must be
byte-identical across renders of unchanged data. New attributes must be `optional: true` to avoid
invalidating already-loaded data.

**Scale/Scope**: 14 nodes / 24 links for the target fabric. The transform must stay correct for
the repo's other fabrics, which use different roles and interface-naming conventions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Schema-Driven Architecture | **PASS** | Both attributes land in `schemas/` before any code reads them, followed by `schema check` and `protocols` regeneration. Placed in `schemas/base/dcim.yml` beside the existing `containerlab_os` rather than in an extension file — these are attributes on nodes that file already owns, so no cross-file dependency is created. |
| II. Idempotent Operations | **PASS (adapted)** | No generator changes, so `$infrahub-test-generator-idempotence` does not apply. The analogous property for a transform is render determinism, covered by FR-006/SC-006 and an explicit test. |
| III. Type Safety | **PASS with tracked debt** | FR-014 replaces the inline GraphQL string with a registered `.gql` plus generated types. See Complexity Tracking for the hand-written-vs-generated `*_query.py` decision. |
| IV. Test-Required Quality | **PARTIAL — see Complexity Tracking** | Unit tests and lint are fully satisfiable here. The constitution mandates `$infrahub-run-integration-tests` for every Infrahub code change; that skill is not present in this environment. |
| V. Convention-Based Structure | **PASS** | `<transform>.py` / `<transform>.gql` / `<transform>_query.py` naming preserved; the new query follows it. Docs under `docs/docs/` with `docs/sidebars.ts` updated if navigation changes. |

### Gate outcome

Proceed to Phase 0. One partial (IV) and one tracked debt item (III) are recorded below rather
than silently accepted.

## Project Structure

### Documentation (this feature)

```text
specs/008-containerlab-multi-domain/
├── plan.md               # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
│   ├── containerlab-topology.md
│   └── parity-matrix.md
├── checklists/
│   └── requirements.md   # From /speckit-specify, re-validated by /speckit-clarify
└── tasks.md              # /speckit-tasks output — NOT created here
```

### Source Code (repository root)

```text
schemas/
└── base/dcim.yml                          # + DcimPlatform.containerlab_image
                                           # + DcimDeviceType.containerlab_interface_mapping

objects/
├── 03_device_type.yml                     # EOS platform image; Arista device-type mappings;
│                                          #   new Linux platform (linux / lab-server)
└── 11b_l3ls_multi_domain_server_templates.yml  # server platform assignment

src/solution_arista_avd/
└── protocols.py                           # regenerated, never hand-edited

transforms/
├── containerlab_topology.gql              # + platform attrs, device_type mapping,
│                                          #   servers, NetworkLink.role
├── containerlab_topology_query.py         # typed models (see Complexity Tracking)
├── containerlab_link_endpoints.gql        # NEW — replaces the inline string literal
├── containerlab_link_endpoints_query.py   # NEW — generated return types
├── containerlab_topology.py               # roles, kind/image from graph, binds, servers,
│                                          #   deterministic subnet, logger warnings
├── container_lab_topology.py              # REMOVED — dead generated orphan
└── templates/containerlab_topology.j2     # multiple kinds, per-node binds

.infrahub.yml                              # register the new query

lab/
├── Makefile                               # + target that deploys from Infrahub
│                                          # (playbook moved to ansible/deploy_clab.yml)
├── configs/servers/
│   ├── dc1-server-netplan.yaml            # renamed from dc1-server1-netplan.yaml
│   └── dc2-server-netplan.yaml            # renamed from dc2-server1-netplan.yaml
└── README.md                              # drop "Planned:" section; document the target

tests/
├── unit/test_containerlab_topology.py     # extended; binds assertion replaced
└── integration/test_e2e_pipeline.py       # multi-domain coverage

docs/docs/                                 # new ContainerLab page (+ sidebars.ts)
pyproject.toml                             # stop lint-excluding a hand-written file
```

**Structure Decision**: No new top-level directories. This feature modifies an existing transform
in place and follows the repository's established `transforms/` + `schemas/` + `objects/` layout.
The only new source files are the second GraphQL query and its generated return-type module, both
named per the `<name>.gql` / `<name>_query.py` convention.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| **Integration tests not run via the mandated validation skill** (Principle IV) | The constitution requires `$infrahub-run-integration-tests` for every Infrahub code change. That skill is not present in this environment's skill inventory, so the mandated path cannot be executed. | Running `uv run pytest tests/integration` directly is explicitly discouraged by project guidance except for ad-hoc local debugging, and would not produce the branch/commit-attributed report the constitution requires. The constitution's own escape clause applies: the change must carry a documented, maintainer-approved exception. Recorded here and surfaced in the completion report rather than quietly skipped. |
| **Two `*_query.py` modules with different provenance** (Principle III) | `containerlab_topology_query.py` is hand-written lean Pydantic; the new `containerlab_link_endpoints_query.py` will be generated. Mixed provenance under one naming convention is a wart. | Regenerating `containerlab_topology_query.py` wholesale is the constitution-aligned end state, but it forces a rewrite of every traversal in the transform inside the same change — the generated models discriminate unions (`NetworkBuildingBlock \| NetworkPod`, `DcimPhysicalDevice \| DcimDevice`) that the hand-written models flatten. Bundling that rewrite with a behavioural fix would make the diff hard to review and put the border-leaf fix at risk. Resolved in research.md R-004: generate the new query's types now, convert the existing module as a separate follow-up, and narrow the `pyproject.toml` exclusion now so the hand-written file is actually linted. |

## Phase Status

- [x] Constitution Check (pre-research)
- [x] Phase 0 — research.md
- [x] Phase 1 — data-model.md, contracts/, quickstart.md
- [x] Constitution Check (post-design re-evaluation) — see research.md R-008
