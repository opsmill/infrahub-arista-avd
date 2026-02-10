# Tasks: Enforce Protocol-Typed Access

**Input**: Design documents from `/specs/001-enforce-protocols/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Regenerate protocol classes so Routing and IPAM types are available for generator fixes

**CRITICAL**: US1 cannot begin until this phase is complete. US2 and US3 have no dependency on this phase.

- [ ] T001 Regenerate protocol classes by running `infrahubctl protocols --output src/solution_ai_dc/protocols.py`. If Infrahub is not running, hand-write the 7 Routing protocol classes (`RoutingBGPPeerGroup`, `RoutingBGPNeighbor`, `RoutingPrefixList`, `RoutingPrefixListEntry`, `RoutingRouteMap`, `RoutingRouteMapEntry`, `RoutingStaticRoute`) in `src/solution_ai_dc/protocols.py` following the existing `@runtime_checkable` pattern. See `specs/001-enforce-protocols/data-model.md` for entity attributes.
- [ ] T002 Verify and format regenerated `src/solution_ai_dc/protocols.py`: confirm 7 Routing types exist (`grep -c "class Routing" src/solution_ai_dc/protocols.py` should return 7), confirm existing IPAM types preserved (`IpamIPPrefix`, `IpamIPAddress`), run `inv format` to normalize formatting, run `inv lint-mypy` on the file.

**Checkpoint**: Protocol classes for all schema-defined types now exist. Generator work can begin.

---

## Phase 2: User Story 1 - Consistent Protocol Usage in All Generators (Priority: P1)

**Goal**: Replace all string-based kind references in generators with protocol class imports. Zero `kind="..."` string patterns should remain.

**Independent Test**: `grep 'kind="' generators/*.py` returns zero matches; `inv lint-mypy` passes on both modified files.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Replace 10 string-kind calls with protocol class references in `generators/backfill_structured_config.py`. Update imports to add `IpamIPAddress`, `IpamIPPrefix`, `RoutingBGPNeighbor`, `RoutingBGPPeerGroup`, `RoutingPrefixList`, `RoutingPrefixListEntry`, `RoutingRouteMap`, `RoutingRouteMapEntry`, `RoutingStaticRoute` from `solution_ai_dc.protocols`. Replace each `kind="TypeName"` with the protocol class (e.g., `await self.client.create(kind="IpamIPPrefix", ...)` becomes `await self.client.create(IpamIPPrefix, ...)`). Lines: 74, 82, 146, 174, 203, 217, 240, 265, 302.
- [ ] T004 [P] [US1] Replace 1 string-kind call in `generators/generate_avd_device_hostvar.py`. Add `NetworkPod` to imports from `solution_ai_dc.protocols` (line 11). Replace `kind="NetworkPod"` with `NetworkPod` on line 27: `await client.filters(NetworkPod, parent__ids=[fabric_id])`.
- [ ] T005 [US1] Verify generator compliance: run `grep 'kind="' generators/*.py` (expect zero matches), run `inv lint-mypy` on `generators/backfill_structured_config.py` and `generators/generate_avd_device_hostvar.py`, run `pytest tests/unit/test_backfill_structured_config.py` to confirm behavioral equivalence.

**Checkpoint**: All generators use protocol classes for client operations. SC-001 satisfied.

---

## Phase 3: User Story 2 - Typed Access in All Transforms (Priority: P2)

**Goal**: Replace raw dict access in `avd_fabric_doc.py` with Pydantic query model attribute access. Fix the underlying GraphQL query to include correct fields.

**Independent Test**: No raw dict access patterns (`data["key"]`, `device["hostname"]`) remain in `transforms/avd_fabric_doc.py`; `inv lint-mypy` passes on modified files.

### Implementation for User Story 2

- [ ] T006 [US2] Add `avd_artifact` relationship fields to GraphQL query in `transforms/avd_fabric_devices.gql`. Add to the `NetworkDevice` query block: `avd_artifact { node { hostvar_identifier { value } structured_config_identifier { value } } }`. Reference `transforms/avd_eos_config.gql` for the correct pattern.
- [ ] T007 [US2] Extend Pydantic query models in `transforms/avd_fabric_devices_query.py` to include the `avd_artifact` path. Add new model classes following the established naming convention: `AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifact` (with `node` field) and `AvdFabricDevicesQueryNetworkDeviceEdgesNodeAvdArtifactNode` (with `hostvar_identifier` and `structured_config_identifier` Optional fields). Add `Field(alias=...)` mappings and `.model_rebuild()` calls. Reference `transforms/avd_eos_config_query.py` for the pattern.
- [ ] T008 [US2] Refactor `transforms/avd_fabric_doc.py` to replace all raw dict access with Pydantic model attribute access. Change the `transform()` method signature to accept and parse the Pydantic query model (`AvdFabricDevicesQuery`). Replace dict patterns: `fabric_edges[0]["node"]` → `data.network_fabric.edges[0].node`, `device["hostname"]["value"]` → `device.hostname.value`, `device.get("avd_inputs", {})` → object store fetch via `device.avd_artifact.node`. Follow the data access pattern from `transforms/avd_eos_config.py` for object store retrieval.
- [ ] T009 [US2] Verify transform compliance: run `inv lint-mypy` on all modified transform files, visually confirm no `["key"]` dict access patterns remain in `transforms/avd_fabric_doc.py`.

**Checkpoint**: All transforms use typed access (Pydantic models or protocol classes). SC-002 and SC-006 satisfied.

---

## Phase 4: User Story 3 - Protocol Types in Core Utility Modules (Priority: P3)

**Goal**: Remove dead code with `Any` type annotations from `avd.py`. The two functions with `Any` types (`extract_uplink_info` and `build_fabric_hostvars`) are unused — confirmed by grep showing zero callers.

**Independent Test**: `inv lint-mypy` passes on `src/solution_ai_dc/avd.py`; no `Sequence[Any]` patterns remain in function signatures.

### Implementation for User Story 3

- [ ] T010 [US3] Remove dead functions `extract_uplink_info()` and `build_fabric_hostvars()` from `src/solution_ai_dc/avd.py`. These functions use `Sequence[Any]` parameters and have zero callers in the codebase (verified by grep). Also remove any imports that become unused after removal (e.g., `Sequence` from `typing` if no longer needed). If the user prefers to keep them, replace `Sequence[Any]` with `Sequence[NetworkInterface]` and `Sequence[NetworkDevice]` respectively, adding imports from `solution_ai_dc.protocols`.
- [ ] T011 [US3] Verify utility module compliance: run `inv lint-mypy` on `src/solution_ai_dc/avd.py`, run `pytest tests/unit/test_avd.py` to confirm existing tests still pass (tests cover `build_device_hostvars`, not the removed functions).

**Checkpoint**: Core utility modules use typed access throughout. SC-004 satisfied for avd.py.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all changes

- [ ] T012 Run full test suite: `pytest tests/unit` — all tests must pass without modification to test assertions (SC-005)
- [ ] T013 Run full linting suite: `inv lint` (ruff + mypy + yamllint) — must pass without new `# type: ignore` suppressions (SC-004, FR-007)
- [ ] T014 Final compliance verification: (1) `grep 'kind="' generators/*.py` returns zero matches (SC-001), (2) no raw dict access in transforms (SC-006), (3) all Routing protocol classes exist in `protocols.py` (SC-003). Report pass/fail for each success criterion.

**Checkpoint**: All success criteria verified. Feature is complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 (protocol classes must exist for Routing types)
- **US2 (Phase 3)**: No dependencies on Phase 1 or US1 — can start immediately or in parallel with Phase 1
- **US3 (Phase 4)**: No dependencies — can start immediately or in parallel with any phase
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Blocked by Phase 1 (Foundational). No dependencies on other stories.
- **US2 (P2)**: Independent. Can start in parallel with Phase 1.
- **US3 (P3)**: Independent. Can start in parallel with anything.

### Within Each User Story

- Implementation tasks within a story are sequential (each builds on the previous)
- Tasks marked [P] within the same story can run in parallel
- Verification task is always last within each story

### Parallel Opportunities

- T003 and T004 (US1): Different files, can run in parallel
- US2 (Phase 3) and Phase 1 + US1 (Phases 1-2): Fully independent, can run in parallel
- US3 (Phase 4): Fully independent, can run in parallel with everything except Polish

---

## Parallel Example: Maximum Parallelism

```text
# Stream A: Foundation + US1 (sequential dependency)
T001 → T002 → T003 + T004 (parallel) → T005

# Stream B: US2 (independent, can start immediately)
T006 → T007 → T008 → T009

# Stream C: US3 (independent, can start immediately)
T010 → T011

# After all streams complete:
T012 → T013 → T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Regenerate protocols
2. Complete Phase 2: Fix generator string-kinds
3. **STOP and VALIDATE**: `grep 'kind="' generators/*.py` returns zero matches
4. All generators now use protocol classes

### Incremental Delivery

1. Phase 1 (Foundation) → Protocol classes ready
2. US1 → Generators compliant → Validate independently
3. US2 → Transforms compliant → Validate independently
4. US3 → Utilities cleaned up → Validate independently
5. Polish → Full suite verification → Feature complete

### Parallel Execution (Fastest Path)

With parallel agents:
1. Start US2 + US3 immediately (no Phase 1 dependency)
2. Start Phase 1 concurrently
3. Start US1 after Phase 1 completes
4. Polish after all complete
5. Estimated: 3 sequential stages instead of 5

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests are not explicitly requested in the spec — verification tasks use existing test suite
- The spec explicitly states existing tests must pass without assertion changes (FR-006)
- Commit after each completed user story phase
- Stop at any checkpoint to validate story independently
