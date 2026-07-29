# Implementation Plan: Fabric Pool Management

**Branch**: `emdash/supernet-pool-xo43k` | **Date**: 2026-07-28 | **Spec**: `specs/005-fabric-pool-management/spec.md`

**Input**: Feature specification from `specs/005-fabric-pool-management/spec.md`

## Summary

Replace type-specific fabric and pod pool assignments with role-driven IP pool collections on the existing `NetworkFabric` and `NetworkPod` schema. The schema design adds explicit `IpamPrefix.role` choices for fabric, DCI, management, and MLAG pool intent; adds many-valued pool collection relationships; keeps legacy relationships load-compatible during migration; and documents validation rules for uniqueness, role homogeneity, subnet containment, required-pool resolution, Fabric Supernet fallback, and MLAG defaults.

This implementation slice is schema-first but includes the immediate validation, generator, object migration, generated type, and documentation work required by the specification. Fabric Supernet allocation, role-based proposed-change checks, object-data migration, generated query updates, and documentation refreshes are in scope for this feature because the feature must protect users from invalid role-driven pool assignments immediately.

## Technical Context

**Language/Version**: Python >=3.11, <3.14 for repository tooling and tests; Infrahub schema YAML version `"1.0"`.

**Primary Dependencies**: Infrahub schema loader/checker via `infrahubctl`, `infrahub-sdk[all]>=1.19.0`, existing project `uv`/pytest/yamllint tooling. No new runtime dependency is planned.

**Storage**: Infrahub graph schema and object data stored in repository YAML under `schemas/` and `objects/`; generated protocol classes in `src/solution_arista_avd/protocols.py`.

**Testing**: Schema contract unit tests with pytest, `uv run infrahubctl schema check schemas/`, protocol regeneration check, `uv run pytest tests/unit`, `uv run invoke lint`, and `$infrahub-run-integration-tests` for Infrahub code changes.

**Target Platform**: Infrahub repository loading against the project Infrahub version target (`INFRAHUB_BASE_VERSION=1.10.1` unless changed by a separate feature).

**Project Type**: Infrahub repository containing schemas, generators, transforms, object data, documentation, and service portal workflows.

**Performance Goals**: Schema relationship changes have no direct runtime hot path, but this feature includes validation and generator role-resolution paths. Those paths should evaluate pool collections deterministically per fabric or pod without scanning unrelated fabrics.

**Constraints**: Extend existing `NetworkFabric` and `NetworkPod`; preserve current loaded data; avoid new mandatory attributes; keep relationship peers as full Infrahub kinds; do not remove legacy relationships abruptly; do not hand-edit generated protocol/query files.

**Scale/Scope**: Current repository fabric hierarchy (`NetworkFabric` -> `NetworkPod` -> `LocationRack`) and all seed objects using `mgmt_pool`, `uplink_pool`, `vtep_pool`, `loopback_pool`, `dci_pool`, `mlag_peer_pool`, `mlag_l3_pool`, and existing prefix roles.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Schema-Driven Architecture**: PASS. The feature is explicitly schema-first and changes begin in `schemas/`. Any generator or object migration that references new fields must wait for schema validation and protocol regeneration.

**Idempotent Operations**: PASS. This plan includes generator and generator-query changes. Generator work must use deterministic role resolution, upserts where objects are created, checksum-aware regeneration where applicable, and repeated-run validation for Fabric Supernet allocation and persisted MLAG default pools.

**Type Safety**: PASS. Schema changes require regenerating `src/solution_arista_avd/protocols.py`. Any later GraphQL query changes must regenerate the matching `*_query.py` files.

**Test-Required Quality**: PASS. The plan requires schema contract unit tests, schema check, unit tests, lint, integration validation skill, and generator idempotence validation because this feature updates generator-owned behavior.

**Convention-Based Structure**: PASS. Changes stay in existing `schemas/`, `objects/`, `src/solution_arista_avd/`, `tests/`, and `docs/` directories.

## Project Structure

### Documentation (this feature)

```text
specs/005-fabric-pool-management/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── fabric-pool-schema-contract.md
└── tasks.md                    # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
schemas/
├── ipam_extensions.yml         # Add authoritative new IpamPrefix.role choices
├── logical_design.yml          # Add/adjust NetworkFabric base pool collection
├── l3ls_extensions.yml         # Add/adjust L3LS fabric/pod pool extensions and legacy compatibility
└── dci.yml                     # Keep DCI fabric pool compatibility during migration

objects/
├── 04_ipam.yml                 # Migration targets for Fabric Supernet and Management pools
├── 04a_l3ls_pools.yml          # Migration targets for L3LS pool resources
├── 04c_fabric_l3ls_multi_domain_pools.yml
├── 10_fabric.yml               # Later object migration to populate pool collections
├── 10a_fabric_l3ls_multi_domain_fabric.yml
├── 13a_fabric_l2ls.yml
├── 13b_fabric_campus.yml
├── 13c_fabric_isis_ldp.yml
└── 14_fabric_single_dc_l3ls.yml

src/solution_arista_avd/
└── protocols.py                # Generated after schema changes; do not hand-edit

generators/
├── *.gql                       # Later query updates consume new pool collections
└── *_query.py                  # Generated after query changes; do not hand-edit

tests/
├── unit/
│   ├── test_fabric_pool_schema_contract.py
│   ├── test_pool_roles.py
│   ├── test_fabric_pool_check.py
│   ├── test_fabric_pool_object_migration.py
│   ├── test_l3ls_pools.py
│   ├── test_generate_pod.py
│   ├── test_generate_rack.py
│   └── test_generate_avd_device_hostvar.py
└── integration/
    └── test_e2e_pipeline.py

docs/docs/
├── developer-guide/schemas.md
├── developer-guide/architecture.md
├── developer-guide/generators.md
├── developer-guide/avd/hostvars.md
└── supported-capabilities.md
```

**Structure Decision**: Use existing schema files and extension points. The implementation should update the files that already own IPAM roles, fabric/pod relationships, and DCI compatibility instead of introducing replacement fabric or pod nodes. Generated protocol/query files are regeneration outputs only.

## Planned Approach

1. Extend `IpamPrefix.role` in `schemas/ipam_extensions.yml` with new explicit choices:
   - `fabric_supernet` (`Fabric Supernet`)
   - `fabric_point_to_point` (`Fabric Point-to-Point`)
   - `dci` (`DCI`)
   - `mlag` (`MLAG`)
   - `mlag_peering` (`MLAG Peering`)
   Existing choices such as `supernet`, `pod_leaf_spine`, `pod_super_spine_spine`, `technical`, `loopback`, `loopback-vtep`, `management`, and `backfill` remain during migration.
2. Add a many-valued fabric pool collection relationship on `NetworkFabric`, named `fabric_ip_pools`, labeled `Fabric IP Pools`. It should use the narrowest common pool peer supported by the loaded Infrahub schema for both `CoreIPPrefixPool` and `CoreIPAddressPool`; the local generated protocols expose `CoreResourcePool` as that common built-in pool target. Validation contract tests and later checks must reject non-IP pool members.
3. Add a many-valued pod pool collection relationship on `NetworkPod`, named `pod_ip_pools`, labeled `Pod IP Pools`, with the same common pool peer and later validation restricting members to `CoreIPPrefixPool` or `CoreIPAddressPool`.
4. Make legacy type-specific fabric relationships non-authoritative but load-compatible:
   - Keep `mgmt_pool`, `uplink_pool`, `vtep_pool`, `loopback_pool`, and `dci_pool` present for migration.
   - Ensure `uplink_pool`, `vtep_pool`, and `loopback_pool` are optional before relying on Fabric Supernet fallback.
   - Add deprecation text where supported by schema validation; do not use `state: absent` until object migration and downstream code migration are complete.
5. Make legacy pod MLAG relationships non-authoritative but load-compatible:
   - Keep `mlag_peer_pool` and `mlag_l3_pool` present and optional during migration.
   - Add deprecation text where supported.
6. Treat role uniqueness, mixed-role pool resources, fabric-required pool resolution, pod subnet containment, DCI requirement detection, and MLAG default/reuse semantics as validation contract behavior. Infrahub schema relationships can model the collections, but these conditional rules require proposed-change checks and generator logic in downstream work.
7. Add schema contract tests that parse YAML and verify:
   - New role choices exist and legacy choices remain.
   - `NetworkFabric.fabric_ip_pools` and `NetworkPod.pod_ip_pools` are many-valued Attribute relationships with full-kind peers.
   - Legacy pool relationships remain present and optional where compatibility requires it.
   - No replacement fabric or pod node is introduced.
8. Regenerate `src/solution_arista_avd/protocols.py` after schema changes and update downstream generated query models only when `.gql` files are changed in later tasks.

## Phase 1 Design Check

**Schema-Driven Architecture**: PASS. `data-model.md` defines schema entities and derived validation contracts before implementation code uses the new relationships.

**Idempotent Operations**: PASS. The schema design keeps legacy relationships available throughout migration and avoids destructive removal. Downstream generators must use deterministic collection resolution and repeated-run validation.

**Type Safety**: PASS. The design explicitly requires protocol regeneration after schema changes and generated query regeneration after future query edits.

**Test-Required Quality**: PASS. `quickstart.md` defines focused schema contract tests, schema check, full unit/lint gates, required integration validation, and generator idempotence validation because this feature updates generator-owned behavior.

**Convention-Based Structure**: PASS. New relationships use snake_case names, full-kind peers, existing schema files, and established test/doc locations.

## Complexity Tracking

No constitution violations are planned.
