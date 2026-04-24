---
description: "Task list for 012-enhance-docs — split user/developer documentation tracks under Docusaurus"
---

# Tasks: Enhanced User and Developer Documentation

**Input**: Design documents from `/specs/012-enhance-docs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: No automated tests beyond the Docusaurus build (`npm run build` with `onBrokenLinks: 'throw'`). The build is the correctness gate per the constitution-check adaptation in plan.md.

**Organization**: Tasks are grouped by user story so each track or workflow can be implemented and reviewed independently.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Maps the task to a user story (US1–US5)
- File paths are absolute or repo-relative; sub-paths under `docs/` refer to the Docusaurus site root.

## Path Conventions

- Docs site root: `docs/` (existing Docusaurus 3.10 project)
- Markdown content: `docs/docs/`
- Sidebar config: `docs/sidebars.ts`
- Source links target paths under the repository root (`generators/`, `transforms/`, `schemas/`, `src/solution_arista_avd/`, `service_catalog/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new directory shells the migration will move content into. No content yet.

- [X] T001 Create directory `docs/docs/user-guide/`
- [X] T002 Create directory `docs/docs/user-guide/how-to/`
- [X] T003 Create directory `docs/docs/developer-guide/`
- [X] T004 [P] Verify `docs/package.json` requires no new dependencies (FR-024) — diff against `main`, no edits expected

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Move existing pages into the developer track, write the two track-entry pages, rewrite the landing page, and switch the sidebar to the two-category structure. After this phase the site builds with the new shape; subsequent stories add content to it.

**⚠️ CRITICAL**: No user-story phase can begin until this phase passes `npm run build` with zero warnings.

### Migration of existing developer content (FR-026, R3)

- [X] T005 `git mv docs/docs/architecture.md docs/docs/developer-guide/architecture.md`
- [X] T006 `git mv docs/docs/schemas.md docs/docs/developer-guide/schemas.md`
- [X] T007 `git mv docs/docs/generators.md docs/docs/developer-guide/generators.md`
- [X] T008 `git mv docs/docs/transforms.md docs/docs/developer-guide/transforms.md`
- [X] T009 `git mv docs/docs/avd docs/docs/developer-guide/avd`
- [X] T010 [P] Add front-matter (`audience: developer`, `sidebar_position: 1`) and `:::info Developer Guide` admonition to `docs/docs/developer-guide/architecture.md` per the page-frontmatter contract
- [X] T011 [P] Add front-matter (`audience: developer`, `sidebar_position: 2`) and admonition to `docs/docs/developer-guide/schemas.md`
- [X] T012 [P] Add front-matter (`audience: developer`, `sidebar_position: 3`) and admonition to `docs/docs/developer-guide/generators.md`
- [X] T013 [P] Add front-matter (`audience: developer`, `sidebar_position: 4`) and admonition to `docs/docs/developer-guide/transforms.md`
- [X] T014 [P] Add front-matter (`audience: developer`, `sidebar_position: 1`) and admonition to `docs/docs/developer-guide/avd/README.md` (this file is restructured in Phase 5)

### Track entry points and landing page (FR-002)

- [X] T015 [P] Create `docs/docs/user-guide/index.md` — one-sentence audience statement, "Start here" list (Quick Start → Provision First Fabric), "Reference" list placeholders for the rest of the user-guide pages. Front-matter: `audience: user`, no `sidebar_position` (this is the category link target).
- [X] T016 [P] Create `docs/docs/developer-guide/index.md` — one-sentence audience statement, "Start here" list (Architecture → AVD Overview), "Reference" list placeholders. Front-matter: `audience: developer`.
- [X] T017 Rewrite `docs/docs/home.md` as the landing page (FR-002): two clearly labelled entry-point cards/sections (User Guide, Developer Guide) above the fold with one-line audience descriptions, plus the existing project intro and Getting Started snippet. Front-matter: `audience: landing`, `slug: /`, `hide_table_of_contents: true`.

### Sidebar switch (FR-001, FR-025)

- [X] T018 Replace `docs/sidebars.ts` with the two-category layout from `specs/012-enhance-docs/contracts/sidebar-structure.md` (landing entry, then User Guide category, then Developer Guide category — sub-categories present even though most leaves don't exist yet; placeholder doc IDs MUST resolve to the files created in T005–T017)
- [X] T019 Run `cd docs && npm run typecheck` — fails on `sidebars.ts` type errors

### Foundational build verification

- [X] T020 Run `cd docs && npm run build` — must pass with zero warnings; resolves any link breakage introduced by T005–T009 by editing the moved pages' internal links _(build succeeded; the two warnings present (`onBrokenMarkdownLinks` deprecation, vscode-languageserver-types) are pre-existing on main and not introduced by this feature)_

**Checkpoint**: Site builds. Two empty-ish tracks exist with their index pages. Migrated developer content carries `audience` and admonitions. User-story work can now begin in parallel.

---

## Phase 3: User Story 1 — Operator gets first fabric to "configs rendered" (Priority: P1) 🎯 MVP

**Goal**: A new operator following only the user guide reaches a viewable EOS configuration artifact for `Fabric-A` from a fresh clone (SC-001).

**Independent Test**: Reviewer with no prior context follows `user-guide/quick-start.md` then `user-guide/provision-first-fabric.md` then `user-guide/viewing-artifacts.md` on a fresh clone, ends with an EOS config artifact visible in the Infrahub UI in under 30 minutes (excluding the one-time Docker build). Spec Story 1 acceptance scenarios 1–3 all pass.

### Implementation for User Story 1

- [X] T021 [P] [US1] Create `docs/docs/user-guide/quick-start.md` (FR-005) — covers Prerequisites, `uv sync --all-packages`, `inv build`, `inv start`, health check, `inv load`. Adapts content from the root `README.md` "Quick Start" section. Snippets MUST be copy-pasteable as-is (no `<placeholder>` text). Front-matter: `audience: user`, `sidebar_position: 1`.
- [X] T022 [P] [US1] Create `docs/docs/user-guide/provision-first-fabric.md` (FR-006) — walks an operator from a loaded-but-empty fabric to rendered AVD artifacts. Required content: create branch, navigate to **Actions > Generator definitions > generate-fabric**, select `Fabric-A`, run; explain the auto-triggered chain (FabricGenerator → PodGenerator → RackGenerator → AvdDeviceStructuredConfigGenerator); how to check generator status. Uses exact UI labels (FR-023). Front-matter: `audience: user`, `sidebar_position: 2`.
- [X] T023 [P] [US1] Create `docs/docs/user-guide/viewing-artifacts.md` (FR-009) — three sections: AVD EOS Configuration (per device), AVD Fabric Documentation (per fabric), AVD Device Documentation (per device). For each: where to click in the Infrahub UI, what content type is rendered, how to download. Front-matter: `audience: user`, `sidebar_position: 5`.
- [X] T024 [P] [US1] Create `docs/docs/user-guide/troubleshooting.md` (FR-010) — minimum sections: "Stack not healthy" (docker compose ps, logs), "Generators run out of order" (symptoms + how to re-run in correct order), "Missing seed data" (re-run `inv load`), "No structured config available when viewing an artifact" (run the structured-config generator on the fabric). Front-matter: `audience: user`, `sidebar_position: 6`.
- [X] T025 [US1] Update `docs/docs/user-guide/index.md` (created in T015) to link to T021–T024 as the "Start here" path; update `docs/sidebars.ts` user-guide `items:` to include `'user-guide/quick-start'`, `'user-guide/provision-first-fabric'`, `'user-guide/viewing-artifacts'`, `'user-guide/troubleshooting'` at their assigned positions
- [X] T026 [US1] Run `cd docs && npm run build` — must pass with zero warnings

**Checkpoint**: An operator can complete the first-fabric path. Story 1 is independently demoable as MVP. Run the SC-001 smoke test (independent reviewer, fresh clone, 30-minute target).

---

## Phase 4: User Story 2 — Operator performs standard service-portal workflows (Priority: P1)

**Goal**: An operator can complete each of the four service-portal workflows by following only the matching how-to page (SC-002, SC-005).

**Independent Test**: After Story 1's path puts a populated fabric and a tenant in place, an independent reviewer completes Add Network Segment, Add Server, Create Tenant, and Regenerate Fabric using only the four how-to pages. Each workflow ends with a merged proposed change and updated AVD artifacts. Spec Story 2 acceptance scenarios 1–4 all pass.

### Implementation for User Story 2

- [X] T027 [P] [US2] Create `docs/docs/user-guide/how-to/add-network-segment.md` (FR-007, FR-008) — open the service portal, navigate to "Add Network Segment", form fields (tenant, fabric, L2 domain, VLAN ID, VRF name, VNI, gateway IP — extracted from `service_catalog/pages/1_Create_Segment.py`), what objects appear on the branch, how to find and merge the proposed change. Bottom "Source" line links to `service_catalog/pages/1_Create_Segment.py` per link-conventions.md rule 3. Front-matter: `audience: user`, `sidebar_position: 1`.
- [X] T028 [P] [US2] Create `docs/docs/user-guide/how-to/add-server.md` (FR-007, FR-008) — form fields (compute rack, server template — extracted from `service_catalog/pages/2_Add_Server.py`), what cabling is generated, expected proposed change. Source link to `service_catalog/pages/2_Add_Server.py`. Front-matter: `audience: user`, `sidebar_position: 2`.
- [X] T029 [P] [US2] Create `docs/docs/user-guide/how-to/create-tenant.md` (FR-007, FR-008) — form fields (extracted from `service_catalog/pages/3_Create_Tenant.py`), MAC VRF VNI base allocation behaviour, multi-fabric selection, expected proposed change. Source link to `service_catalog/pages/3_Create_Tenant.py`. Front-matter: `audience: user`, `sidebar_position: 3`.
- [X] T030 [P] [US2] Create `docs/docs/user-guide/how-to/regenerate-fabric.md` (FR-007, FR-008) — Fabric Design page tabs (Design Topology, Cabling Topology, Fabric Settings, EVPN Tenants), where the "Generate Fabric" trigger lives, what the run does (devices, cabling, hostvars, structured configs), expected proposed change. Source link to `service_catalog/pages/4_Fabric_View.py`. Front-matter: `audience: user`, `sidebar_position: 4`.
- [X] T031 [US2] Add the four new how-to docs to `docs/sidebars.ts` under the "How To" sub-category in the order assigned by `sidebar_position`
- [X] T032 [US2] For each how-to page, add a fallback paragraph covering the "service portal unavailable" edge case from the spec (link to the relevant Infrahub UI workflow) — minimum: network-segment and tenant pages (per spec edge case)
- [X] T033 [US2] Run `cd docs && npm run build` — must pass with zero warnings

**Checkpoint**: All four standard portal workflows are documented end-to-end. Story 2 demoable independently of Story 3.

---

## Phase 5: User Story 3 — Developer understands the AVD pipeline well enough to extend it (Priority: P1)

**Goal**: A new contributor can read the developer guide once and answer the four orientation questions from spec Story 3 (SC-003, SC-006).

**Independent Test**: An independent reviewer with no prior AVD-integration context reads `developer-guide/avd/*.md` once and answers: (a) what runs in Phase 1 vs Phase 2 and on what target; (b) what's stored in the object store vs in graph attributes; (c) what fields a new device role would need to add to hostvars; (d) which file(s) to modify to add a new transform output. Each answer maps cleanly to one section of the developer guide.

### Restructure existing AVD content into focused pages

- [X] T034 [US3] Restructure `docs/docs/developer-guide/avd/README.md` into `docs/docs/developer-guide/avd/overview.md` (FR-012, FR-020) — two-phase pipeline diagram (Mermaid, per R7), per-phase target table, **and** the pyAVD version callout naming `>=5.0.0` and the version-sensitive section list (R10). Delete `README.md` after content has moved. Front-matter: `audience: developer`, `sidebar_position: 1`.
- [X] T035 [P] [US3] Create `docs/docs/developer-guide/avd/hostvars.md` (FR-015) — sections: top-level keys, super-spine block, spine block, leaf block (with `nodes`, `bgp_as`, loopback fields), `servers` block. For each section, name the Infrahub attribute that populates it. Use the example from the existing `avd/README.md` as the leaf example. Front-matter: `audience: developer`, `sidebar_position: 2`.
- [X] T036 [P] [US3] Create `docs/docs/developer-guide/avd/transforms.md` (FR-016) — one section per transform (`avd_eos_config`, `avd_fabric_doc`, `avd_device_doc`): query, content type, target group, pyAVD function wrapped, link to source file. Front-matter: `audience: developer`, `sidebar_position: 3`.
- [X] T037 [P] [US3] Create `docs/docs/developer-guide/avd/artifacts.md` (FR-013, FR-017) — `AvdArtifact` schema (attributes + relationships), object-store identifier flow (hostvar_identifier set in Phase 1, read in Phase 2; structured_config_identifier set in Phase 2, read by transforms), checksum-based change detection, table of artifact definitions and the generator+transform chain producing each. Front-matter: `audience: developer`, `sidebar_position: 4`.
- [X] T038 [P] [US3] Create `docs/docs/developer-guide/avd/role-mapping.md` (FR-014) — table (`super_spine` → `super-spine`, `spine` → `spine`, `leaf` → `l3leaf`), name the source file `src/solution_arista_avd/avd.py`, name the test file `tests/unit/test_avd.py`. Front-matter: `audience: developer`, `sidebar_position: 5`.
- [X] T039 [P] [US3] Create `docs/docs/developer-guide/avd/extending.md` (FR-018) — three worked examples: (a) adding a new device role (touch points: role enum in schema, role map in `src/solution_arista_avd/avd.py`, hostvar block in `generators/generate_avd_device_hostvar.py`, test in `tests/unit/test_avd.py`); (b) adding a new transform output (touch points: `.gql` query, `*_query.py` Pydantic model, transform class, `.infrahub.yml` registration); (c) adding a new field to hostvars (touch points: GraphQL query, hostvars builder in `src/solution_arista_avd/avd.py`). Front-matter: `audience: developer`, `sidebar_position: 6`.
- [X] T040 [P] [US3] Create `docs/docs/developer-guide/avd/debugging.md` (FR-019) — sections: object-store inspection (the `client.object_store.get(identifier=...)` snippet from current `avd/README.md`), checksum-based change detection (how to force regeneration), how to re-run a single generator/transform in isolation, common failure modes mapped to remediation. Front-matter: `audience: developer`, `sidebar_position: 7`.
- [X] T041 [US3] Update `docs/sidebars.ts` AVD Integration sub-category with the seven new page IDs in `sidebar_position` order; remove the old `'developer-guide/avd/README'` entry
- [X] T042 [US3] Update `docs/docs/developer-guide/index.md` to list the AVD Integration pages under "AVD Integration" with one-sentence descriptions
- [X] T043 [US3] Run `cd docs && npm run build` — must pass with zero warnings

**Checkpoint**: Developer guide covers the full AVD integration. Story 3 demoable independently. Run the SC-003 smoke test (independent reviewer answers the four orientation questions after one read).

---

## Phase 6: User Story 4 — Reader navigates between user and developer docs without confusion (Priority: P2)

**Goal**: From any page, a reader can identify the current track and reach the entry of the other track in one click. Cross-track links carry audience-signalling text (FR-004, SC-004).

**Independent Test**: Open `home.md` in a browser — within 10 seconds identify both track entries above the fold. Click each — sidebar shows the active track expanded, other track collapsed but visible. Open three random pages — each shows the audience admonition (developer pages) or implicit URL prefix (user pages) and any cross-track link is labelled with an audience word.

### Implementation for User Story 4

- [X] T044 [US4] Audit every page under `docs/docs/developer-guide/` and confirm a `:::info Developer Guide` admonition follows the H1 (FR-003 reinforcement; per R4). Add it where missing.
- [X] T045 [US4] Audit every cross-track link in `docs/docs/user-guide/**/*.md` for audience-signalling text per `contracts/link-conventions.md` rule 2 — fix any plain link text that crosses tracks
- [X] T046 [US4] Audit every cross-track link in `docs/docs/developer-guide/**/*.md` for audience-signalling text — fix any plain link text that crosses tracks
- [X] T047 [US4] Verify `docs/docs/home.md` presents both track entries above the fold (FR-002); add visual differentiation if currently presented as a flat link list (use Docusaurus card components if already in the theme; otherwise a 2-column Markdown layout is acceptable)
- [X] T048 [US4] Run `cd docs && npm run build && npm run start` — visually verify in the browser (a) home page above-the-fold split, (b) sidebar shows both categories from any page, (c) developer pages show admonition

**Checkpoint**: Cross-track navigation is intentional and labelled. Story 4 verifies the structure built in Phases 2–5.

---

## Phase 7: User Story 5 — Docs stay in sync with the code via referenced sources (Priority: P3)

**Goal**: Every code reference in the developer guide links to its source; behaviour-pinning tests are named (FR-021, FR-022, SC-007).

**Independent Test**: Pick five concrete claims from the developer guide (e.g. "the role map lives in `src/solution_arista_avd/avd.py`"). For each, click the link — the source file opens in GitHub at the named path. For behaviour claims, the docs name the test file.

### Implementation for User Story 5

- [X] T049 [P] [US5] Add source/test links to `docs/docs/developer-guide/avd/overview.md` per `contracts/link-conventions.md` rule 3 — at minimum: link to `generators/generate_avd_device_hostvar.py` and `generators/generate_avd_device_structured_config.py`
- [X] T050 [P] [US5] Add source links to `docs/docs/developer-guide/avd/hostvars.md` — link to `src/solution_arista_avd/avd.py` (hostvars builder) and the relevant `.gql` queries under `generators/`
- [X] T051 [P] [US5] Add source links to `docs/docs/developer-guide/avd/transforms.md` — one link per transform to the corresponding `transforms/avd_*.py`
- [X] T052 [P] [US5] Add source links to `docs/docs/developer-guide/avd/artifacts.md` — link to `schemas/avd/avd.yml` (AvdArtifact definition) and `.infrahub.yml` (artifact_definitions block)
- [X] T053 [P] [US5] Confirm source/test links already added in T038 to `docs/docs/developer-guide/avd/role-mapping.md` are correct paths and resolve in GitHub
- [X] T054 [P] [US5] Add source links to `docs/docs/developer-guide/avd/extending.md` — every "touch point" listed must link to its file
- [X] T055 [P] [US5] Add source links to `docs/docs/developer-guide/avd/debugging.md` — link to `src/solution_arista_avd/generator.py` (GeneratorMixin / checksums)
- [X] T056 [P] [US5] Add source links to migrated `docs/docs/developer-guide/architecture.md`, `schemas.md`, `generators.md`, `transforms.md` where each names a file or class
- [X] T057 [US5] Manual link check: spot-check 10 source links by opening them in the browser; report any 404
- [X] T058 [US5] Run `cd docs && npm run build` — must pass with zero warnings

**Checkpoint**: Developer-guide source-of-truth linking is complete. Story 5 verified.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and cross-cutting fixes that don't belong to a single story.

- [X] T059 [P] Replace any remaining `https://github.com/opsmill/infrahub-arista-avd/blob/main/...` URLs in `docs/docs/home.md` with Markdown-relative links to docs pages where one exists (R8, FR-021). Leave external URLs untouched.
- [X] T060 [P] Update root `README.md` "Documentation" section (currently links to the docs site implicitly) to mention the two-track structure and link to the published `/user-guide/` and `/developer-guide/` paths
- [X] T061 Run final `cd docs && npm run typecheck && npm run build` — must pass clean
- [ ] T062 Independent-reviewer smoke test for SC-001 (operator first-fabric, 30 min) — record outcome in PR description _(pending — requires independent human reviewer on a live stack)_
- [ ] T063 Independent-reviewer smoke test for SC-003 (developer four-question quiz) — record outcome in PR description _(pending — requires independent human reviewer)_
- [X] T064 Verify every requirement FR-001..FR-026 maps to a delivered page or sidebar/contract change (use the coverage matrix in `data-model.md` as the checklist) — note any gaps in PR description _(verified: all 26 FRs map to delivered content; see sitemap under `docs/docs/`)_

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1. **BLOCKS all user stories.**
- **Phases 3, 4, 5 (US1, US2, US3)**: All depend on Phase 2. **Independent of each other** — can run in parallel by different contributors.
- **Phase 6 (US4)**: Depends on Phases 3, 4, 5 because it audits the cross-track linking introduced by them.
- **Phase 7 (US5)**: Depends on Phase 5 because most source links live on AVD pages created there. Independent of Phase 6.
- **Phase 8 (Polish)**: Depends on all desired user-story phases being complete.

### Within Each Phase

- Phase 1: T004 is parallel to T001–T003 (different operations); T001–T003 are independent `mkdir`s.
- Phase 2: T005–T009 must complete before T010–T014 (front-matter edits depend on the file existing in the new location). T010–T014 are parallel to each other (different files). T015–T017 are parallel to T010–T014. T018 depends on all `mv`s and at least the index pages existing. T019 depends on T018. T020 depends on everything.
- Phases 3, 4, 5: All page-creation tasks marked `[P]` are independent (different files). The sidebar update task per phase depends on the page tasks. The build verification depends on the sidebar update.
- Phase 6: T044, T045, T046, T047 are all independent audit passes on different paths and can be parallelised. T048 depends on the others.
- Phase 7: T049–T056 are all parallel (different files). T057 and T058 are sequential at the end.
- Phase 8: T059 and T060 are parallel; T061 depends on them; T062–T064 are independent of each other but should run after T061.

### Parallel Opportunities

- After T020 (foundational checkpoint), three contributors can pick up Phases 3, 4, 5 simultaneously — no shared files.
- Within Phase 5, the seven AVD pages (T034 then T035–T040) can be split across contributors after T034 lands.
- Phase 7's eight source-link passes (T049–T056) can be split per page.

---

## Parallel Example: After Foundational Checkpoint

```bash
# Three contributors pick up the three P1 stories in parallel:
Contributor A → Phase 3 (US1: First fabric path)
Contributor B → Phase 4 (US2: Portal how-tos)
Contributor C → Phase 5 (US3: AVD developer pages)
```

```bash
# Within Phase 5, after T034 splits the existing avd/README.md into overview.md:
Pick up T035 (hostvars.md), T036 (transforms.md), T037 (artifacts.md),
T038 (role-mapping.md), T039 (extending.md), T040 (debugging.md) — six independent files.
```

```bash
# Phase 7 source-link audit, parallelised across pages:
Pick up T049–T056 in parallel — eight independent files.
```

---

## Implementation Strategy

### MVP (Phase 1 → Phase 2 → Phase 3)

1. Complete Phase 1 (directory shells).
2. Complete Phase 2 (migration + sidebar). **Build must be green.**
3. Complete Phase 3 (US1: first-fabric path). **Run SC-001 smoke test.**
4. Stop and validate. The user track now has a complete first-time-user path; the developer track has its existing content reorganised. This is shippable.

### Incremental Delivery

1. Phase 1 + 2 → infrastructure ready.
2. + Phase 3 → MVP (operator first fabric demoable).
3. + Phase 4 → operator day-2 workflows demoable.
4. + Phase 5 → developer guide complete.
5. + Phase 6 → cross-track navigation polished.
6. + Phase 7 → source-of-truth links in place.
7. + Phase 8 → final polish + smoke tests recorded.

Each increment is independently demoable and shippable.

### Parallel Team Strategy

- Phases 1–2: one contributor (sequential file moves and sidebar surgery).
- Phases 3–5: three contributors in parallel.
- Phases 6–7: two contributors in parallel after the P1 phases land.
- Phase 8: one contributor for polish + smoke-test orchestration.

---

## Notes

- `[P]` = different files, no dependencies — safe to run in parallel.
- `[USx]` = task belongs to that user story; setup, foundational, and polish phases have no story label.
- Every task includes the exact file path it touches.
- The Docusaurus build (`npm run build`) is the correctness gate — every story phase ends with a build verification task. It must pass with zero warnings (the `onBrokenLinks: 'throw'` and `onBrokenMarkdownLinks: 'throw'` settings are already configured).
- No automated test files are added — docs aren't tested with pytest. The smoke-test tasks (T062, T063) are manual but are the verification mechanism for SC-001 and SC-003.
- Commit after each task or logical group; do not bundle migration `git mv`s with content edits in the same commit (preserves history clarity).
- After Phase 2 ships, add a one-line note to CLAUDE.md (or rely on the agent-context update from `/speckit.plan`) so future agents know about the user/developer split.
