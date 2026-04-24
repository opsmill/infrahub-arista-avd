# Implementation Plan: Enhanced User and Developer Documentation

**Branch**: `012-enhance-docs` | **Date**: 2026-04-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-enhance-docs/spec.md`

## Summary

Re-organise the existing Docusaurus site under `docs/` into two clearly separated tracks — a **User Guide** for operators consuming the system through the Streamlit service portal and the Infrahub UI, and a **Developer Guide** that documents the AVD integration internals (two-phase generator pipeline, hostvars contract, `AvdArtifact` and the object store, role mapping, transforms). Migrate existing technical pages (`architecture.md`, `schemas.md`, `generators.md`, `transforms.md`, `avd/README.md`) into the developer track and write net-new user-track content covering Quick Start, the four service-portal workflows, viewing artifacts, and troubleshooting. Express the split declaratively in `sidebars.ts` so future page additions are one-line changes; rely on Docusaurus's existing broken-link enforcement (`onBrokenLinks: 'throw'`, `onBrokenMarkdownLinks: 'throw'`) as the build-time correctness gate.

## Technical Context

**Language/Version**: Markdown (CommonMark + MDX) authored against Docusaurus 3.10
**Primary Dependencies**: `@docusaurus/core@^3.10.0`, `@docusaurus/preset-classic@^3.10.0`, `@docusaurus/theme-mermaid@^3.10.0` (already installed; no new deps)
**Storage**: Files on disk under `docs/docs/`; sidebar in `docs/sidebars.ts`
**Testing**: `npm run build` from `docs/` — fails on broken internal links (already configured), broken Markdown links, and duplicate routes; manual review of rendered output via `npm run start`
**Target Platform**: Static site (currently configured to publish to `https://opsmill.github.io/infrahub-arista-avd/`)
**Project Type**: Documentation site (single, not multi-package)
**Performance Goals**: N/A — static site, no runtime performance concerns
**Constraints**: No new doc-build dependencies (FR-024); existing GitHub Pages publication path must keep working; absolute GitHub URLs preserved when they target external resources (issues, PRs, repo root) and replaced with relative links when they target files inside this repo
**Scale/Scope**: ~5 existing pages (~1,500 lines), expanding to ~14–16 pages across the two tracks; ~1,500 lines of new content across user-guide pages, ~500 lines of net-new developer reference content layered on the migrated pages

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution at `.specify/memory/constitution.md` (v1.0.0) defines five principles. Applicability to this feature:

| Principle | Applies? | Compliance |
|-----------|----------|------------|
| I. Schema-Driven Architecture | No | No schema, generator, transform, or library code is touched. |
| II. Idempotent Operations | No | No data mutations or generator code is added. |
| III. Type Safety | No | No Python code is added. (Docusaurus TypeScript config is unchanged; `tsc` continues to run via `npm run typecheck`.) |
| IV. Test-Required Quality | Partially — adapted | Documentation has no unit tests, but Docusaurus's `onBrokenLinks: 'throw'` and `onBrokenMarkdownLinks: 'throw'` settings are the equivalent build-time correctness gate. The plan keeps both settings on and treats `npm run build` as the gate every PR must pass. |
| V. Convention-Based Structure | Yes | Docusaurus expects a sidebar config and a `docs/` content tree. The plan uses one sub-directory per track (`user-guide/`, `developer-guide/`), matching the convention the existing `avd/` sub-directory already establishes. Sidebar config uses one `category` per track (FR-025). |

**Result**: PASS. No violations to justify in the Complexity Tracking table.

**Post-design re-check** (after Phase 1): PASS. The page sitemap, sidebar contract, and link conventions do not introduce any new compliance concerns. Principle V (conventions) is strengthened — the chosen subdirectory-per-track layout mirrors the existing `docs/docs/avd/` precedent and the contracts make per-page conventions explicit. No new schema, generator, transform, or Python code is added in Phase 1.

## Infrahub Skill Integration

**Decision**: No Infrahub skill is invoked for this feature.

The skill detection table maps spec signals (schema, transform, check, generator, menu) to skills. The spec for `012-enhance-docs` does not design or modify any of these artifact types — it documents the existing AVD integration but does not change it. Per the rule "If the spec involves multiple artifact types, invoke the skill for the primary type", no primary type exists when no artifact type is in scope.

The developer-guide content does describe the existing AVD generator and transform implementations, but documenting existing code does not require the skill's curated reference material — the source files in `generators/`, `transforms/`, and `schemas/` are themselves the authoritative reference, and FR-021/FR-022 require the docs to link to them.

## Project Structure

### Documentation (this feature)

```text
specs/012-enhance-docs/
├── plan.md              # This file
├── spec.md              # Feature spec (already created)
├── checklists/
│   └── requirements.md  # Spec-quality checklist (already created)
├── research.md          # Phase 0 output — Docusaurus structure decisions
├── data-model.md        # Phase 1 output — page sitemap and sidebar entities
├── quickstart.md        # Phase 1 output — author/reviewer workflow
└── contracts/
    ├── page-frontmatter.md     # Required front-matter for every doc page
    ├── sidebar-structure.md    # Sidebars.ts contract (two top-level categories)
    └── link-conventions.md     # Cross-track and source-link conventions
```

### Source Code (repository root)

```text
docs/                              # Docusaurus root (existing)
├── docusaurus.config.ts           # Existing — unchanged in this feature
├── sidebars.ts                    # MODIFIED — two-category structure
├── package.json                   # Unchanged (no new deps)
└── docs/                          # MDX/MD content
    ├── home.md                    # REWRITTEN — landing page routing to both tracks
    ├── user-guide/                # NEW directory
    │   ├── index.md               # User-guide entry page
    │   ├── quick-start.md         # FR-005
    │   ├── provision-first-fabric.md  # FR-006
    │   ├── how-to/
    │   │   ├── add-network-segment.md      # FR-007
    │   │   ├── add-server.md               # FR-007
    │   │   ├── create-tenant.md            # FR-007
    │   │   └── regenerate-fabric.md        # FR-007
    │   ├── viewing-artifacts.md   # FR-009
    │   └── troubleshooting.md     # FR-010
    └── developer-guide/           # NEW directory (existing technical content migrated here)
        ├── index.md               # Developer-guide entry page
        ├── architecture.md        # MOVED from docs/architecture.md
        ├── schemas.md             # MOVED from docs/schemas.md
        ├── generators.md          # MOVED from docs/generators.md
        ├── transforms.md          # MOVED from docs/transforms.md
        └── avd/
            ├── overview.md        # FR-012 — derived from current avd/README.md
            ├── hostvars.md        # FR-015 — net-new reference content
            ├── transforms.md      # FR-016 — extracted from current avd/README.md
            ├── artifacts.md       # FR-013, FR-017 — AvdArtifact + object store + chains
            ├── role-mapping.md    # FR-014 — table + source link to src/solution_arista_avd/avd.py
            ├── extending.md       # FR-018 — worked examples
            └── debugging.md       # FR-019 — pipeline-level troubleshooting
```

**Structure Decision**: Two-track layout via sub-directories (`user-guide/`, `developer-guide/`) under `docs/docs/`, with a single `mainSidebar` in `sidebars.ts` containing two `category`-typed entries (one per track). This was chosen over Docusaurus's "multiple sidebars" feature because (a) the existing `docusaurus.config.ts` references a single `mainSidebar` ID in the navbar (`sidebarId: 'mainSidebar'`), so introducing a second sidebar would also touch the navbar config and add a UI element that isn't required by the spec; (b) a single sidebar with two collapsible categories satisfies FR-001 (visually distinct) and FR-003 (one track per page) while keeping Story 4's "navigate to either track in one click" achievable from any page; (c) it is a one-line change per new page (FR-025). See `research.md` for the full evaluation.

The migration preserves all existing page content as the foundation of the developer guide (FR-026); migration is by `git mv` to keep history.

## Complexity Tracking

> No constitution violations; this section is intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |
