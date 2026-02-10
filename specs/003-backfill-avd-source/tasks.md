# Tasks: Backfill AVD Attribute Source

**Input**: Design documents from `/specs/003-backfill-avd-source/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Tests are included as the existing test suite must be extended to verify source attribution.

**Organization**: US1 and US2 are tightly coupled (US2 provides the lookup, US1 consumes it), so they are combined into a single implementation phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (CoreAccountGroup Lookup)

**Purpose**: Add the CoreAccountGroup lookup mechanism that all source attribution depends on (FR-001, FR-003, FR-004)

- [x] T001 [US2] Add `_get_avd_source()` method to look up CoreAccountGroup named "AVD" with graceful fallback in `generators/backfill_structured_config.py`
  - Use `self.client.get(CoreAccountGroup, name__value="AVD")` (using protocol class)
  - Wrap in try/except `NodeNotFoundError` (or equivalent SDK exception)
  - On failure: log warning, return `None`
  - On success: return the group node (its `.id` will be used as source)
- [x] T002 [US2] Call `_get_avd_source()` at the top of `generate()` and store result as `avd_source` local variable in `generators/backfill_structured_config.py`
  - Pass `avd_source` (or its `.id`) to all backfill methods via a new parameter

**Checkpoint**: Generator can look up the AVD group and gracefully handle its absence

---

## Phase 2: Source Attribution on All Node Types (US1)

**Purpose**: Set source on every attribute written by the backfill generator (FR-002)

### Implementation

- [x] T003 [US1] Add `_set_source()` helper method that sets source on all attributes of a node in `generators/backfill_structured_config.py`
  - Accept a node and the avd_source reference
  - If avd_source is None, return immediately (no-op)
  - Iterate node attributes and set `attr.source = NodeProperty(data=avd_source_id)`
  - Call this before each `save()` call
- [x] T004 [US1] Apply source attribution in `_backfill_ip()` for IpamIPPrefix and IpamIPAddress in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on prefix and ip_address nodes before `save()`
- [x] T005 [US1] Apply source attribution in `_update_mtu()` for NetworkInterface in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Set source on the mtu attribute before `save()`
- [x] T006 [US1] Apply source attribution in `_backfill_bgp_peer_groups()` for RoutingBGPPeerGroup in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on peer group node before `save()`
- [x] T007 [US1] Apply source attribution in `_backfill_bgp_neighbors()` for RoutingBGPNeighbor in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on neighbor node before `save()`
- [x] T008 [US1] Apply source attribution in `_backfill_prefix_lists()` for RoutingPrefixList and RoutingPrefixListEntry in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on prefix list and entry nodes before `save()`
- [x] T009 [US1] Apply source attribution in `_backfill_route_maps()` for RoutingRouteMap and RoutingRouteMapEntry in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on route map and entry nodes before `save()`
- [x] T010 [US1] Apply source attribution in `_backfill_static_routes()` for RoutingStaticRoute in `generators/backfill_structured_config.py`
  - Add `avd_source` parameter to method signature
  - Call `_set_source()` on static route node before `save()`
- [x] T011 [US1] Update `_backfill_bgp()` and `_process_routing_sections()` to pass `avd_source` through to sub-methods in `generators/backfill_structured_config.py`
- [x] T012 [US1] Update `generate()` to pass `avd_source` to `_backfill_ip()`, `_update_mtu()`, and `_process_routing_sections()` in `generators/backfill_structured_config.py`

**Checkpoint**: All node types created/updated by the generator have source set to AVD CoreAccountGroup

---

## Phase 3: Tests

**Purpose**: Verify source attribution works correctly and existing tests still pass

- [x] T013 [P] [US2] Add unit test for `_get_avd_source()` success case (group found) in `tests/unit/test_backfill_structured_config.py`
- [x] T014 [P] [US2] Add unit test for `_get_avd_source()` failure case (group not found, graceful degradation) in `tests/unit/test_backfill_structured_config.py`
- [x] T015 [P] [US1] Add unit test verifying source is set on IpamIPPrefix and IpamIPAddress attributes in `tests/unit/test_backfill_structured_config.py`
- [x] T016 [P] [US1] Add unit test verifying source is set on NetworkInterface MTU attribute in `tests/unit/test_backfill_structured_config.py`
- [x] T017 [P] [US1] Add unit test verifying source is set on BGP peer group and neighbor attributes in `tests/unit/test_backfill_structured_config.py`
- [x] T018 [P] [US1] Add unit test verifying source is set on prefix list, route map, and static route attributes in `tests/unit/test_backfill_structured_config.py`
- [x] T019 [US1] Add unit test verifying no source is set when `avd_source` is None (graceful degradation path) in `tests/unit/test_backfill_structured_config.py`
- [x] T020 Run full test suite to verify no regressions: `pytest tests/unit/test_backfill_structured_config.py`

**Checkpoint**: All tests pass, including source attribution and graceful degradation

---

## Phase 4: Polish & Validation

**Purpose**: Final validation and cleanup

- [x] T021 Run linters: `inv lint`
- [x] T022 Verify all 80+ existing tests still pass: `pytest tests/unit/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundational)**: No dependencies - start here
- **Phase 2 (Source Attribution)**: Depends on Phase 1 (T001, T002 must complete first)
- **Phase 3 (Tests)**: Can start T013-T014 after Phase 1; T015-T019 after Phase 2
- **Phase 4 (Polish)**: Depends on all previous phases

### Parallel Opportunities

- T013 and T014 (US2 tests) can run in parallel after Phase 1
- T015, T016, T017, T018 can all run in parallel after Phase 2
- All test tasks write to the same file but test independent methods

### Within Implementation

- T001 → T002 (lookup before usage)
- T003 (helper) → T004-T010 (usage in each method)
- T004-T010 can be done in any order (independent methods)
- T011-T012 (wiring) depends on T004-T010

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: CoreAccountGroup lookup with graceful fallback
2. Complete Phase 2: Source attribution on all node types
3. **STOP and VALIDATE**: Run existing tests to ensure no regressions
4. Complete Phase 3: Add new tests for source attribution
5. Complete Phase 4: Lint and final validation

### Key Design Decision

The `_set_source()` helper centralizes source assignment logic. If the SDK provides a simpler mechanism (e.g., passing source directly to `client.create()`), prefer that approach and skip the helper.

---

## Notes

- All changes are in 2 files: `generators/backfill_structured_config.py` and `tests/unit/test_backfill_structured_config.py`
- The `objects/00_user_groups.yml` seed file already defines `CoreAccountGroup` named "AVD"
- The infrahub-sdk `NodeProperty` class (from `infrahub_sdk.node.property`) is used to set source metadata
- Source is per-attribute, not per-node - each attribute's `.source` property must be set individually
