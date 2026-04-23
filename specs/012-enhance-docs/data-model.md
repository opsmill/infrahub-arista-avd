# Phase 1 Data Model — 012-enhance-docs

For a documentation feature the "data model" is the page sitemap, the sidebar entities, and the front-matter schema each page must satisfy.

## Entity: DocPage

Every Markdown file under `docs/docs/` is a `DocPage`.

### Required fields (front-matter)

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `title` | string | free text | Shown in the browser tab and at the top of the page. |
| `description` | string | free text | One-sentence page summary; surfaced in search and link previews. |
| `audience` | enum | `user`, `developer`, `landing` | Per R4. `landing` reserved for the home page. |
| `sidebar_position` | int | 1..N within parent category | Determines order within the sidebar category. Optional only for `landing`. |

### Optional fields

| Field | Type | Notes |
|-------|------|-------|
| `slug` | string | Override URL path. Avoid unless renaming a page that already has external links. |
| `hide_table_of_contents` | bool | Default `false`. Set `true` only on landing/index pages. |
| `keywords` | list[string] | Optional search terms; rarely needed. |
| `tags` | list[string] | Reserved for future taxonomy. Do not introduce now. |

### Validation rules

- A page's directory MUST agree with its `audience` field: pages under `user-guide/` MUST have `audience: user`; pages under `developer-guide/` MUST have `audience: developer`; `home.md` MUST have `audience: landing`.
- Every page with `audience: developer` MUST include the developer admonition (`:::info Developer Guide ... :::`) immediately after the H1.
- Every internal link from a page in one track to a page in the other MUST use audience-signalling text (R5).
- Code or CLI snippets MUST be copy-pasteable as-is on a fresh clone (per spec Edge Case "Reader copies a code/CLI snippet"): no shell prompts inside the code block, no unspecified placeholders.

### State transitions

DocPages have no runtime state. Authoring lifecycle:
- `draft` (PR open) → `merged` (on `main`) → `published` (after the next docs build/deploy).

## Entity: SidebarCategory

The `docs/sidebars.ts` file declares one `mainSidebar` containing exactly two SidebarCategory entries.

| Field | Value |
|-------|-------|
| `type` | `'category'` |
| `label` | `"User Guide"` or `"Developer Guide"` |
| `collapsed` | `false` (both categories collapsible but expanded by default) |
| `link` | `{ type: 'doc', id: '<track>/index' }` so the category label is itself a navigable entry pointing to that track's index page |
| `items` | ordered list of doc IDs in that track |

A sub-category (e.g. `developer-guide/avd/`) is a nested `SidebarCategory` with the same shape.

### Validation rules

- The sidebar MUST contain exactly two top-level categories with labels "User Guide" and "Developer Guide" (FR-001).
- The home page (`home.md`) MUST appear once at the top of `mainSidebar` *outside* both categories so that landing on it does not visually expand a track (FR-002).
- The order of `items` within a category is the recommended reading order; broken or shuffled order is a review-blocker.

## Entity: TrackEntryPage

Each track has exactly one TrackEntryPage. These are special DocPages whose role is to orient the reader and link onward.

| Field | Value |
|-------|-------|
| Path | `docs/docs/user-guide/index.md` and `docs/docs/developer-guide/index.md` |
| `audience` | matches the directory |
| Content shape | (1) one-sentence audience statement, (2) a "Start here" list linking to the first 1–3 pages, (3) a "Reference" list linking to deeper material |

These pages are what the SidebarCategory `link` field points to.

## Sitemap

The full set of DocPages this feature creates or moves:

```text
home.md                                         (audience: landing — REWRITTEN)

user-guide/
├── index.md                                    (audience: user — NEW)
├── quick-start.md                              (audience: user — NEW; satisfies FR-005)
├── provision-first-fabric.md                   (audience: user — NEW; FR-006)
├── how-to/
│   ├── add-network-segment.md                  (audience: user — NEW; FR-007)
│   ├── add-server.md                           (audience: user — NEW; FR-007)
│   ├── create-tenant.md                        (audience: user — NEW; FR-007)
│   └── regenerate-fabric.md                    (audience: user — NEW; FR-007)
├── viewing-artifacts.md                        (audience: user — NEW; FR-009)
└── troubleshooting.md                          (audience: user — NEW; FR-010)

developer-guide/
├── index.md                                    (audience: developer — NEW)
├── architecture.md                             (audience: developer — MOVED from docs/architecture.md)
├── schemas.md                                  (audience: developer — MOVED from docs/schemas.md)
├── generators.md                               (audience: developer — MOVED from docs/generators.md)
├── transforms.md                               (audience: developer — MOVED from docs/transforms.md)
└── avd/
    ├── overview.md                             (audience: developer — REWRITTEN from avd/README.md; FR-012, FR-020)
    ├── hostvars.md                             (audience: developer — NEW; FR-015)
    ├── transforms.md                           (audience: developer — NEW; extracted; FR-016)
    ├── artifacts.md                            (audience: developer — NEW; FR-013, FR-017)
    ├── role-mapping.md                         (audience: developer — NEW; FR-014)
    ├── extending.md                            (audience: developer — NEW; FR-018)
    └── debugging.md                            (audience: developer — NEW; FR-019)
```

**Counts**: 1 landing page (rewritten), 9 user-guide pages (all new), 12 developer-guide pages (5 moved, 7 new).

## Coverage matrix: requirements → pages

| Requirement | Realised by |
|-------------|-------------|
| FR-001 (two visually distinct tracks) | `sidebars.ts` two-category layout |
| FR-002 (home page describes each track) | `home.md` rewrite |
| FR-003 (each page in one track) | Directory + front-matter `audience` |
| FR-004 (cross-track links labelled) | Linking convention enforced in review |
| FR-005 (Quick Start) | `user-guide/quick-start.md` |
| FR-006 (Provision First Fabric) | `user-guide/provision-first-fabric.md` |
| FR-007 (one How-To per portal workflow) | 4 pages under `user-guide/how-to/` |
| FR-008 (How-To content shape) | Authoring template baked into each how-to page |
| FR-009 (Viewing Artifacts) | `user-guide/viewing-artifacts.md` |
| FR-010 (Common Issues) | `user-guide/troubleshooting.md` |
| FR-011 (no Python/GraphQL required) | Reviewer assertion against user-guide pages |
| FR-012 (AVD pipeline overview) | `developer-guide/avd/overview.md` |
| FR-013 (AvdArtifact + object store) | `developer-guide/avd/artifacts.md` |
| FR-014 (role mapping table) | `developer-guide/avd/role-mapping.md` |
| FR-015 (hostvars per role) | `developer-guide/avd/hostvars.md` |
| FR-016 (each transform documented) | `developer-guide/avd/transforms.md` |
| FR-017 (artifact definitions documented) | `developer-guide/avd/artifacts.md` |
| FR-018 (extending the integration) | `developer-guide/avd/extending.md` |
| FR-019 (debugging the pipeline) | `developer-guide/avd/debugging.md` |
| FR-020 (pyAVD version pin) | Callout in `developer-guide/avd/overview.md` |
| FR-021 (relative links to source) | Linking contract; reviewed per page |
| FR-022 (test-name references) | Linking contract; reviewed per page |
| FR-023 (UI labels match exactly) | Reviewer assertion against user-guide pages |
| FR-024 (no new doc-build deps) | `package.json` unchanged |
| FR-025 (declarative sidebar split) | `sidebars.ts` shape (two categories) |
| FR-026 (no duplication of existing AVD content) | `git mv` migration path (R3) |

## Out of model

- Tags / taxonomy beyond `audience`.
- Per-version doc trees (Docusaurus versioning).
- Translation strings (i18n).
- Search-index customisation.
