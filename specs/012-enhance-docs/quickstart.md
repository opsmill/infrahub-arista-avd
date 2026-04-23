# Quickstart — Authoring & Reviewing 012-enhance-docs

The author/reviewer loop for this feature. (Distinct from the *user-facing* Quick Start page that the docs themselves will ship — see `user-guide/quick-start.md` in the deliverables.)

## Prerequisites

- Node.js >= 18 (the version `docs/package.json` declares).
- Repo cloned and on branch `012-enhance-docs`.

## First-time setup

```bash
cd docs
npm install
```

This installs Docusaurus 3.10 and the existing dev dependencies. No new dependencies are added by this feature (FR-024).

## Author loop: writing or editing a page

```bash
cd docs
npm run start
```

Opens a hot-reloading preview at `http://localhost:3000/infrahub-arista-avd/`. Editing any `.md` under `docs/docs/` updates the browser within a second.

### When you add a new page

1. Create the file under the correct track directory (`docs/docs/user-guide/...` or `docs/docs/developer-guide/...`).
2. Add the front-matter required by [page-frontmatter contract](./contracts/page-frontmatter.md). Be sure `audience` matches the directory.
3. Add one entry to `docs/sidebars.ts` under the right category, in the order you want it to appear (see [sidebar-structure contract](./contracts/sidebar-structure.md)).
4. Save — the preview updates.

### When you migrate an existing page

Use `git mv` so history is preserved (see Phase 0 R3):

```bash
cd docs/docs
git mv architecture.md developer-guide/architecture.md
git mv schemas.md developer-guide/schemas.md
git mv generators.md developer-guide/generators.md
git mv transforms.md developer-guide/transforms.md
git mv avd developer-guide/avd
```

After the move:
- Add `audience: developer` and a `sidebar_position` to each migrated page's front-matter.
- Add a `:::info Developer Guide` admonition immediately after the H1 (per Phase 0 R4).
- Update any internal links broken by the move (the build will tell you which).

### When you add a cross-track link

Follow rule 2 of [link-conventions](./contracts/link-conventions.md) — the link text MUST contain an audience word ("operator workflow", "developer reference", etc.) so the reader knows they are switching track.

## Verification loop

Before opening the PR:

```bash
cd docs
npm run build
```

Must complete with **zero warnings**. The site config already has:

- `onBrokenLinks: 'throw'` — any `.md` → `.md` link that doesn't resolve fails the build.
- `onBrokenMarkdownLinks: 'throw'` — any Markdown-syntax link with a broken target fails the build.
- `onDuplicateRoutes: 'throw'` — two pages resolving to the same URL fail the build.

These are the **build-time correctness gate** referenced in the constitution check (Principle IV adapted for docs). If `npm run build` passes, link integrity is established.

```bash
npm run typecheck
```

Validates `sidebars.ts` and `docusaurus.config.ts` against `@docusaurus/tsconfig`. Run after editing either file.

## Review loop

A reviewer of a PR for this feature MUST verify, for each changed page:

1. **Front-matter contract** ([page-frontmatter](./contracts/page-frontmatter.md)) — `audience` matches directory; `sidebar_position` present on non-landing pages.
2. **Sidebar contract** ([sidebar-structure](./contracts/sidebar-structure.md)) — new pages appear in the correct category and at the intended position.
3. **Link contract** ([link-conventions](./contracts/link-conventions.md)) — same-track links use `./...md`, cross-track links use `/user-guide/...` or `/developer-guide/...` with an audience word.
4. **Audience separation** — user-guide pages are completable without reading Python, GraphQL, or YAML (FR-011); developer-guide pages name source files and tests (FR-021, FR-022).
5. **Build is green** — CI or local `npm run build` must succeed.

## Smoke test for the user track

Once the user-guide pages are written, an independent reviewer (someone who hasn't worked on the code) follows them on a fresh clone:

```bash
git clone <repo> /tmp/docs-smoke && cd /tmp/docs-smoke
# Follow user-guide/quick-start.md verbatim
# Then user-guide/provision-first-fabric.md verbatim
# Open http://localhost:8000 → fabric → device → AVD EOS Configuration artifact
```

Success criterion: the reviewer reaches a viewable EOS configuration artifact in under 30 minutes (excluding the one-time Docker build) without consulting source, CLAUDE.md, or external help (SC-001).

## Smoke test for the developer track

After the developer-guide pages are written, an independent reviewer (no prior AVD-integration context) reads the developer guide once and answers the four orientation questions from spec Story 3:

1. What runs in Phase 1 vs Phase 2 and on what target?
2. What is stored in the object store vs in graph attributes?
3. What fields would a new device role need to add to hostvars?
4. Which file(s) to modify to add a new transform output?

Each answer should map cleanly to one section of the developer guide (SC-003).
