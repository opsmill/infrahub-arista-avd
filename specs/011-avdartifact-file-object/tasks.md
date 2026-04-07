# Tasks: Migrate AvdArtifact to CoreFileObject

**Input**: Design documents from `/specs/011-avdartifact-file-object/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: SDK upgrade and dependency resolution

- [x] T001 Upgrade infrahub-sdk from `==1.18.1` to `>=1.19.0` in pyproject.toml, preserving ariadne-codegen override in `[tool.uv]`
- [x] T002 Run `uv sync --all-packages` and verify no dependency conflicts

**Checkpoint**: SDK upgraded, CoreFileObject API available

---

## Phase 2: Foundational (Schema & Config)

**Purpose**: Schema changes and infrastructure config that MUST be complete before any generator/transform work

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Add `AvdHostvarFile` and `AvdStructuredConfigFile` node definitions to schemas/objects/objects.yml — both inherit from `CoreFileObject`, each with a Parent relationship to `AvdArtifact` using identifiers `avdartifact__hostvar_file` and `avdartifact__structured_config_file`. Set `human_friendly_id: ["artifact__name__value"]`, `display_label: artifact__name__value`, `uniqueness_constraints: [["artifact"]]`, `include_in_menu: false`
- [x] T004 Add Component relationships on AvdArtifact in schemas/objects/objects.yml — `hostvar_file` (peer: AvdHostvarFile, Component, cardinality one, optional, identifier: `avdartifact__hostvar_file`) and `structured_config_file` (peer: AvdStructuredConfigFile, Component, cardinality one, optional, identifier: `avdartifact__structured_config_file`)
- [x] T005 Mark 6 deprecated attributes on AvdArtifact with `state: absent` in schemas/objects/objects.yml — `hostvar_identifier`, `hostvar_checksum`, `hostvar_url`, `structured_config_identifier`, `structured_config_checksum`, `structured_config_url`
- [x] T006 Add `avd_structured_configs` group definition to objects/01_groups.yml for AvdStructuredConfigFile nodes (used as backfill generator target)
- [x] T007 [P] Update .infrahub.yml — change backfill-structured-config generator `targets` from `avd_artifacts` to `avd_structured_configs`, update `parameters` to `device_hostname: artifact__device__name__value`
- [x] T008 [P] Update triggers.yml — change backfill trigger `node_kind` from `AvdArtifact` to `AvdStructuredConfigFile`, change watched attribute from `structured_config_checksum` to `checksum`
- [ ] T009 Regenerate protocol classes by running `infrahubctl protocols --output src/solution_ai_dc/protocols.py` (requires Infrahub running with updated schema loaded)

**Checkpoint**: Schema loaded, protocols regenerated, config files updated. Generator/transform work can begin.

---

## Phase 3: User Story 1 — Add CoreFileObject child nodes to AvdArtifact (Priority: P1)

**Goal**: Generators create AvdHostvarFile and AvdStructuredConfigFile as children of AvdArtifact using the CoreFileObject upload API instead of manual object_store calls.

**Independent Test**: After running the hostvar and structured config generators, AvdArtifact nodes own child file objects with auto-populated file_name, file_size, checksum, and storage_id.

### Implementation for User Story 1

- [x] T010 [US1] Update generators/generate_avd_device_hostvar.py — replace `client.object_store.upload(content=json.dumps(hostvars))` + manual AvdArtifact creation with: (1) create/upsert AvdArtifact with name and device, (2) create AvdHostvarFile child node, (3) call `upload_from_bytes(content=json.dumps(hostvars).encode(), name=f"{hostname}-hostvars.json")`, (4) save with `allow_upsert=True`. Remove references to `hostvar_checksum` and `hostvar_identifier`.
- [x] T011 [US1] Update generators/generate_avd_device_structured_config.py — replace `client.object_store.upload(content=json.dumps(structured_config))` + manual AvdArtifact update with: (1) get existing AvdArtifact for device, (2) create AvdStructuredConfigFile child node, (3) call `upload_from_bytes(content=json.dumps(structured_config).encode(), name=f"{hostname}-structured-config.json")`, (4) save with `allow_upsert=True`. Remove references to `structured_config_checksum` and `structured_config_identifier`.
- [x] T012 [US1] Update generators/generate_avd_device_structured_config.py — replace `client.object_store.get(identifier=hostvar_identifier)` calls that read hostvars with: get AvdArtifact for device, get its `hostvar_file` child, call `await hostvar_file.download_file()` and `json.loads(content)`.

**Checkpoint**: Hostvar and structured config generators create CoreFileObject children. AvdArtifact nodes have navigable child file objects.

---

## Phase 4: User Story 2 — Maintain pipeline triggers via file object checksum (Priority: P2)

**Goal**: The backfill generator is retargeted to AvdStructuredConfigFile nodes and retrieves file content via the CoreFileObject API.

**Independent Test**: Updating a structured config file object triggers the backfill generator, which successfully retrieves and processes the structured config.

### Implementation for User Story 2

- [x] T013 [US2] Rewrite generators/backfill_structured_config.gql — reroot query on `AvdStructuredConfigFile` instead of `AvdArtifact`. Traverse `artifact { device { ... } }` to reach device data. Parameter changes from `device_hostname: device__name__value` to `device_hostname: artifact__device__name__value`.
- [x] T014 [US2] Regenerate generators/backfill_structured_config_query.py — update Pydantic models to match the new GQL query structure rooted on AvdStructuredConfigFile with nested artifact and device.
- [x] T015 [US2] Update generators/backfill_structured_config.py — replace `client.object_store.get(identifier=identifier)` with `await structured_config_file.download_file()`. Update the `generate()` method to navigate from AvdStructuredConfigFile → artifact → device instead of AvdArtifact → device. Update type annotations to match new Pydantic models.

**Checkpoint**: Backfill generator runs when structured config checksum changes. End-to-end: hostvar gen → structured config gen → backfill triggered automatically.

---

## Phase 5: User Story 3 — Clean up deprecated manual attributes (Priority: P3)

**Goal**: All transforms use the CoreFileObject download API. No code references the removed attributes.

**Independent Test**: All three AVD transforms successfully retrieve structured config from AvdStructuredConfigFile and produce correct output.

### Implementation for User Story 3

- [x] T016 [P] [US3] Update transforms/avd_eos_config.py — replace `client.object_store.get(identifier=structured_config_value)` with: get device's `avd_artifact`, get its `structured_config_file` child, call `await structured_config_file.download_file()`. Update the GQL query in transforms/avd_device_config.gql to fetch `avd_artifact { structured_config_file { id } }` instead of `avd_artifact { structured_config_identifier, structured_config_checksum }`.
- [x] T017 [P] [US3] Update transforms/avd_fabric_doc.py — replace both `client.object_store.get(identifier=hostvar_id)` and `client.object_store.get(identifier=structured_config_id)` with CoreFileObject downloads via `hostvar_file.download_file()` and `structured_config_file.download_file()`. Update transforms/avd_fabric_devices.gql to fetch file object children instead of identifier attributes.
- [x] T018 [P] [US3] Update transforms/avd_device_doc.py — same pattern as T016: replace `client.object_store.get()` with `download_file()` on the structured config file object. Update GQL query accordingly.

**Checkpoint**: All transforms use CoreFileObject API. No references to `hostvar_identifier`, `hostvar_checksum`, `structured_config_identifier`, or `structured_config_checksum` in any generator or transform.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Test updates, linting, and final validation

- [x] T019 Update tests/unit/test_backfill_structured_config.py — update test fixtures and mocks to match new AvdStructuredConfigFile-rooted query models and download_file pattern
- [x] T020 [P] Update tests/unit/test_avd.py — no changes needed (no old attribute references) — update any tests that reference the old AvdArtifact attributes (hostvar_identifier, structured_config_identifier, etc.)
- [x] T021 Run `inv lint` (ruff + mypy + yamllint) and fix any issues across all modified files
- [x] T022 Run `inv format` to auto-fix formatting in all modified files
- [x] T023 Verify no remaining references to removed attributes: grep for `hostvar_identifier`, `hostvar_checksum`, `structured_config_identifier`, `structured_config_checksum`, `object_store.upload`, `object_store.get` across generators/, transforms/, and src/

**Checkpoint**: All tests pass, all linters pass, no stale references remain.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational phase completion
- **US2 (Phase 4)**: Depends on US1 (needs file objects to exist before backfill can target them)
- **US3 (Phase 5)**: Can run in parallel with US2 (transforms are independent of backfill generator)
- **Polish (Phase 6)**: Depends on US1, US2, and US3 completion

### Within Each User Story

- Schema and config changes must complete before generator/transform code changes
- Generator changes before transform changes (generators produce data that transforms consume)
- All implementation before test updates

### Parallel Opportunities

- T007 and T008 can run in parallel (different config files)
- T016, T017, T018 can all run in parallel (three independent transforms)
- T019 and T020 can run in parallel (different test files)
- US2 (Phase 4) and US3 (Phase 5) can run in parallel after US1 completes

---

## Parallel Example: User Story 3

```text
# Launch all three transform updates together (different files, no dependencies):
Task T016: "Update transforms/avd_eos_config.py"
Task T017: "Update transforms/avd_fabric_doc.py"
Task T018: "Update transforms/avd_device_doc.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (SDK upgrade)
2. Complete Phase 2: Foundational (schema + config)
3. Complete Phase 3: User Story 1 (generator updates)
4. **STOP and VALIDATE**: Run generators, verify file objects created with correct metadata
5. Generators work with new file objects — core migration functional

### Incremental Delivery

1. Setup + Foundational → Schema ready, SDK upgraded
2. Add US1 → Generators produce file objects → **MVP**
3. Add US2 → Backfill generator retargeted, triggers work
4. Add US3 → Transforms use file objects, no stale references
5. Polish → Tests updated, linting passes, final validation

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- T009 (protocol regeneration) requires Infrahub running — may need to defer if running offline
- All generators use `allow_upsert=True` for idempotent file object creation
- After migration, re-running all generators repopulates file objects (no manual data migration)
