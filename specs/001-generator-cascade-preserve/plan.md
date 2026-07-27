# Implementation Plan: Generator Cascade Preservation

**Branch**: `001-generator-cascade-preserve` | **Date**: 2026-07-27 | **Spec**: `specs/001-generator-cascade-preserve/spec.md`

**Input**: Feature specification from `specs/001-generator-cascade-preserve/spec.md`

## Summary

Make `generate-fabric` a reconciliation entry point for existing fabrics, not only a checksum bump for newly generated topology. The implementation should keep the existing trigger-based cascade for changed pod/rack targets, explicitly continue the cascade for unchanged downstream targets, and make device upserts fill missing generator-owned values without overwriting pre-existing non-empty operator values such as `serial` and `mgmt_ip`.

No schema change is planned for the default implementation. The current schema already represents the required fabric, pod, rack, device, IPAM, group, and AVD artifact data. Override mode is not planned as an external operator option in this slice because the local `CoreGeneratorDefinitionRun` schema accepts only `id` and `nodes`; adding an explicit runtime override would require a new generator definition contract, service-portal flow, or schema-backed setting.

## Technical Context

**Language/Version**: Python >=3.11, <3.14.

**Primary Dependencies**: `infrahub-sdk[all]>=1.19.0`, `pyavd>=6.3.0,<6.4.0`, `httpx>=0.28.1`; Streamlit service portal uses the `catalog` dependency group.

**Storage**: Infrahub graph data plus object-store-backed `AvdHostvarFile` and `AvdStructuredConfigFile` child nodes.

**Testing**: `pytest`, `pytest-asyncio`, repository integration tests, `$infrahub-run-integration-tests`, and `$infrahub-test-generator-idempotence` when live generator validation is permitted.

**Target Platform**: Infrahub repository generator execution in task workers, plus the service portal and Infrahub UI/API as operator entry points.

**Project Type**: Infrahub repository containing schemas, generators, transforms, object data, docs, and a Streamlit service portal.

**Performance Goals**: A single `generate-fabric` run on one target fabric should reconcile only that fabric's pods, racks, devices, and artifacts. Existing hostvar targeting should remain scoped: whole-fabric hostvars only when any device is missing hostvars; otherwise rack-local targets.

**Constraints**: Preserve non-empty operator-provided values by default; keep generator operations idempotent; do not add dependencies; do not hand-edit generated query models or protocols; branch trigger rules run on non-main branches.

**Scale/Scope**: Existing fabric hierarchy sizes supported by the repository: one selected `NetworkFabric`, all child `NetworkPod` targets, all pod `LocationRack` targets, all generated `DcimDevice` targets, and per-device AVD artifacts.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Schema-Driven Architecture**: PASS. No new schema fields are planned. If implementation discovers a missing schema contract, schema work must be handled first with `infrahub-managing-schemas`, schema validation, and protocol regeneration before generator code references it.

**Idempotent Operations**: PASS. The plan keeps `allow_upsert=True`, natural-name/HFID reconciliation, checksum storage, and explicit repeated-run validation. Direct continuation triggers must avoid duplicate downstream runs by targeting only unchanged objects when checksum-trigger updates already fire.

**Type Safety**: PASS. Existing GraphQL queries and generated Pydantic models remain sufficient for the planned code path. Any query change must regenerate the matching `*_query.py` model instead of hand-editing it.

**Test-Required Quality**: PASS. Unit coverage is required for downstream continuation, fill-only device reconciliation, preservation of pre-seeded values, and no-duplicate repeated runs. Integration and generator idempotence validation remain mandatory gates for generator code changes.

**Convention-Based Structure**: PASS. Changes stay in existing generator/helper/test/doc paths and do not introduce new directories outside the established repository layout.

## Project Structure

### Documentation (this feature)

```text
specs/001-generator-cascade-preserve/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── regenerate-fabric-reconciliation.md
└── tasks.md                    # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
generators/
├── generate_fabric.py          # Fabric kickoff and pod continuation behavior
├── generate_pod.py             # Pod reconciliation and rack continuation behavior
├── generate_rack.py            # Existing rack completion and hostvar cascade behavior
├── generate_avd_device_hostvar.py
└── generate_avd_device_structured_config.py

src/solution_arista_avd/
├── generator.py                # Shared trigger helpers and fill-only AVD device reconciliation
└── protocols.py                # Generated; update only if schema changes require regeneration

service_catalog/
├── pages/4_Fabric_View.py      # Existing operator entry point; no override UI planned in this slice
└── utils/api.py                # Existing CoreGeneratorDefinitionRun wrapper

tests/
├── unit/
│   ├── test_generate_fabric.py
│   ├── test_generate_pod.py
│   ├── test_generate_rack.py
│   ├── test_generator_cascade_contract.py
│   └── test_generator_mixin.py
└── integration/
    └── test_e2e_pipeline.py
```

**Structure Decision**: Use the existing generator/helper structure. The behavior is shared across fabric, pod, and rack generators, so common continuation and device-reconciliation helpers belong in `src/solution_arista_avd/generator.py`; generator-specific orchestration remains in `generators/generate_fabric.py` and `generators/generate_pod.py`.

## Planned Approach

1. Extend the generator trigger helper layer so `generate-fabric` can directly run `generate-pod` for child pods whose checksum did not change, and `generate-pod` can directly run `generate-rack` for child racks whose checksum did not change.
2. Keep existing checksum updates and `CoreNodeTriggerRule` behavior for changed targets, because those triggers also support direct pod/rack edits outside this feature.
3. Refactor `GeneratorMixin.create_avd_device()` into a fill-only reconciliation path:
   - Fetch an existing device by name before constructing the upsert payload.
   - Populate missing generator-owned values such as role, pod/rack, index, object template, AVD group membership, node ID, loopback IP, VTEP IP, ASN, and management IP where absent.
   - Preserve non-empty operator-provided values by default, especially `serial` and `mgmt_ip`.
   - Add `avd_devices` group membership additively without removing unrelated groups.
4. Preserve rack-owned hostvar cascade behavior: rack generation marks the fabric hostvars stale, marks rack completion, checks all racks, invalidates targeted hostvar files, and triggers hostvar generation for the correct device set.
5. Do not expose override mode in this slice. The internal reconciliation helper may be designed with a default-false overwrite parameter for future work, but no operator-visible override should be added without an explicit contract.

## Phase 1 Design Check

**Schema-Driven Architecture**: PASS. `data-model.md` uses existing entities and defines ownership semantics without new schema attributes.

**Idempotent Operations**: PASS. The continuation design avoids fake checksum churn and relies on explicit downstream generator runs only when no trigger-causing update occurred.

**Type Safety**: PASS. No query/model changes are required by the design. If implementation needs extra fields for preservation checks, the `.gql` file and generated model must be updated together.

**Test-Required Quality**: PASS. `quickstart.md` defines unit, local integration, required integration-skill, and live idempotence-skill validation paths.

**Convention-Based Structure**: PASS. Generated artifacts and source layout match repository conventions.

## Complexity Tracking

No constitution violations are planned.
