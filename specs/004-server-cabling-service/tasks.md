# Tasks: Server Cabling Service

**Input**: Design documents from `/specs/004-server-cabling-service/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Unit tests are included to verify generator logic.

**Organization**: US1 (cabling) and US2 (templates/profiles) are tightly coupled - templates are the input for cabling. US2 (seed data) is placed in the Foundational phase since it's a prerequisite for US1. US3 (validation) and US4 (idempotency) are behaviors built into the core generator.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Schema Changes

**Purpose**: Update schema to support server templates and generator targeting (FR-001, FR-011)

- [x] T001 Add `generate_template: true` and `GeneratorTarget` inheritance to `ComputePhysicalServer` in `schemas/compute/compute.yml`
  - Add `GeneratorTarget` to `inherit_from` list (gives checksum attribute for change detection)
  - Add `generate_template: true` (creates `TemplateComputePhysicalServer` for object templates)

**Checkpoint**: Schema supports server templates and generator targeting

---

## Phase 2: Seed Data (US2 - Templates & Profiles)

**Purpose**: Create server interface profiles with VLANs and server object templates (FR-011, FR-012)

- [x] T002 [P] [US2] Add server interface profiles with VLAN relationships in `objects/05_profiles.yml`
  - `profile-server-compute`: role=server, mtu=9000, tagged_vlan=[Servers, Storage]
  - `profile-server-gpu`: role=server, mtu=9000, tagged_vlan=[Servers, Storage, Backup]
- [x] T003 [P] [US2] Add `servers` group to `objects/01_groups.yml` for generator targeting
- [x] T004 [US2] Create server object templates in `objects/08_server_templates.yml`
  - `compute-server-single`: role=compute, 1x Ethernet1 with `profile-server-compute`
  - `compute-server-dual`: role=compute, 2x Ethernet[1-2] with `profile-server-compute`
  - `gpu-server-single`: role=gpu, 1x Ethernet1 with `profile-server-gpu`
  - Use `TemplateComputePhysicalServer` kind with `expand_range: true` for interfaces

**Checkpoint**: Server templates and profiles are defined; creating a server from template produces correct interfaces with VLANs

---

## Phase 3: Generator Implementation (US1 - Core Cabling + US3 - Validation + US4 - Idempotency)

**Purpose**: Implement the server cabling generator (FR-001 through FR-010)

- [x] T005 [US1] Create GraphQL query in `generators/generate_server_cabling.gql`
  - Root on `ComputePhysicalServer` with `server_name` parameter
  - Fetch: id, hostname, role, status, rack (with id, name)
  - Fetch: server interfaces with id, name, role, status, link, profiles (with tagged_vlan, untagged_vlan)
  - Fetch: rack devices (leaves) with interfaces including link and role
- [x] T006 [US1] Create the `ServerCablingGenerator` class in `generators/generate_server_cabling.py`
  - Extend `InfrahubGenerator`
  - Implement `generate(data)` method:
    1. Parse server data from query response
    2. Get server interfaces, filter out already-linked ones (US4 idempotency)
    3. Find leaf switches in the same rack (filter by role="leaf")
    4. Get available (unlinked) server/storage-role interfaces on leaves
    5. Validate sufficient interfaces are available (US3 - log warning and skip if not)
    6. Distribute server interfaces across leaves (round-robin for dual-homed)
    7. Create `NetworkLink` between paired interfaces (name, medium=copper, allow_upsert=True)
    8. Copy `tagged_vlan` and `untagged_vlan` from server interface profiles to leaf interfaces
    9. Set all connected interfaces to status="active"
  - Edge cases: no leaves in rack (warn+skip), no server interfaces (warn+skip), single leaf with dual-homed (connect both to single leaf with notice)
- [x] T007 [US1] Register the generator in `.infrahub.yml`
  - Add query: `generate_server_cabling` pointing to `./generators/generate_server_cabling.gql`
  - Add generator definition: `generate-server-cabling` with file_path, query, targets=servers, parameters (server_name: hostname__value), class_name=ServerCablingGenerator

**Checkpoint**: Generator can cable a server to leaf switches with VLAN assignments

---

## Phase 4: Unit Tests

**Purpose**: Verify generator logic for all user stories and edge cases

- [x] T008 [P] [US1] Add unit test for single-homed server cabling (1 interface → 1 leaf) in `tests/unit/test_server_cabling.py`
- [x] T009 [P] [US1] Add unit test for dual-homed server cabling (2 interfaces → 2 different leaves) in `tests/unit/test_server_cabling.py`
- [x] T010 [P] [US1] Add unit test for VLAN assignment from server interface profiles to leaf interfaces in `tests/unit/test_server_cabling.py`
- [x] T011 [P] [US1] Add unit test for interface status set to "active" after cabling in `tests/unit/test_server_cabling.py`
- [x] T012 [P] [US3] Add unit test for warning when no leaf switches in rack in `tests/unit/test_server_cabling.py`
- [x] T013 [P] [US3] Add unit test for warning when insufficient leaf interfaces available in `tests/unit/test_server_cabling.py`
- [x] T014 [P] [US4] Add unit test for idempotency (already-cabled server skipped) in `tests/unit/test_server_cabling.py`
- [x] T015 [P] Add unit test for single leaf with dual-homed server (both interfaces to same leaf) in `tests/unit/test_server_cabling.py`
- [x] T016 [P] Add unit test for server with zero interfaces (warn+skip) in `tests/unit/test_server_cabling.py`

**Checkpoint**: All tests pass, covering core cabling, validation, idempotency, and edge cases

---

## Phase 5: Polish & Validation

**Purpose**: Final validation and cleanup

- [x] T017 Run linters: `inv lint`
- [x] T018 Run full test suite: `pytest tests/unit/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Schema)**: No dependencies - start here
- **Phase 2 (Seed Data)**: Depends on Phase 1 (schema must support templates)
- **Phase 3 (Generator)**: Depends on Phase 1 (GeneratorTarget inheritance)
- **Phase 4 (Tests)**: Depends on Phase 3 (generator must exist to test)
- **Phase 5 (Polish)**: Depends on all previous phases

### Within Phases

- T002 and T003 can run in parallel (different files)
- T004 depends on T001 (needs TemplateComputePhysicalServer from schema)
- T005 and T006 are sequential (GQL before Python class)
- T007 depends on T005 and T006
- T008-T016 can all run in parallel (all write to same test file but test independent methods)

### Parallel Opportunities

- Phase 2: T002 + T003 in parallel
- Phase 4: All test tasks (T008-T016) in parallel

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Schema changes for template and generator support
2. Complete Phase 2: Seed data (profiles with VLANs, server templates, group)
3. Complete Phase 3: Generator implementation
4. **STOP and VALIDATE**: Run linters and existing tests
5. Complete Phase 4: Unit tests for the new generator
6. Complete Phase 5: Final lint and full test suite

### Key Design Decisions

- The generator queries `ComputePhysicalServer` directly (not via AvdArtifact like the backfill generator)
- Server interface profiles carry VLAN information; the generator copies VLANs to leaf interfaces
- Round-robin distribution ensures dual-homed servers connect to different leaves when available
- `allow_upsert=True` on NetworkLink creation provides idempotency via HFID

---

## Notes

- Schema changes require `generate_template: true` on ComputePhysicalServer to create TemplateComputePhysicalServer
- Protocols will need regeneration (`infrahubctl protocols`) after schema changes, but unit tests use mocks
- The `TemplateNetworkInterface` already has `tagged_vlan` and `untagged_vlan` relationships from the vlan.yml extensions
- Existing `connect_interface_maps()` in `src/solution_ai_dc/cabling.py` handles link creation and status setting - can be reused or adapted
- The `ProfileNetworkInterface` also already has VLAN relationship support from schema extensions
