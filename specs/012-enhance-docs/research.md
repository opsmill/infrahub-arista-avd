# Phase 0 Research — 012-enhance-docs

This phase resolves all open questions raised by the Technical Context and the spec's assumptions, so that Phase 1 can produce a deterministic data model, contracts, and quickstart.

## R1 — Sidebar structure: single sidebar with two categories vs. two sidebars

**Decision**: Single `mainSidebar` in `docs/sidebars.ts` containing two top-level `category` entries — "User Guide" and "Developer Guide" — each with its own collapsible item list.

**Rationale**:
- The current `docs/docusaurus.config.ts` references the sidebar by ID (`sidebarId: 'mainSidebar'`) in exactly one navbar item. Introducing a second sidebar (`userSidebar`, `developerSidebar`) would also require adding a second navbar entry and a routing strategy for the home page — UI work the spec did not ask for.
- A single sidebar with two categories satisfies FR-001 (visually distinct tracks) and FR-003 (one track per page), while keeping Story 4's "navigate to either track in one click" trivially achievable from any page (the other category is always visible in the sidebar).
- It is a one-line change per new page (FR-025): add an entry under the appropriate category.
- Docusaurus categories can be set `collapsed: false` for the active track and `collapsed: true` for the inactive one, which gives the visual cue Story 4 asks for.

**Alternatives considered**:
- *Multiple sidebars (one per track)*: Rejected — requires navbar changes and a landing-page routing strategy that adds scope. Better fit when tracks have different theming or doc instances.
- *Single flat sidebar with section headers*: Rejected — does not satisfy "visually distinct" (FR-001) and makes per-track collapse impossible.
- *Docusaurus tabs on a single page*: Rejected — does not scale to 14+ pages and breaks deep-linking and search.

## R2 — Page layout: subdirectories vs. front-matter–only categorisation

**Decision**: Use subdirectories (`docs/docs/user-guide/`, `docs/docs/developer-guide/`) to group pages by track, mirroring the structure already established by the existing `docs/docs/avd/` subdirectory.

**Rationale**:
- The folder structure becomes self-documenting; a contributor opening `docs/docs/` sees the two-track split immediately.
- Subdirectories give natural URL paths (`/user-guide/quick-start`, `/developer-guide/avd/hostvars`) that match the sidebar grouping and survive page renames within a track.
- Sidebar entries can be expressed as simple ID strings (`'user-guide/quick-start'`) without a custom `link` field per entry.

**Alternatives considered**:
- *Flat `docs/docs/` with front-matter `track: user|developer`*: Rejected — requires custom sidebar logic to filter by front-matter and produces meaningless URLs that don't reveal audience.
- *Two separate `docs/` instances under Docusaurus*: Rejected — overkill and adds publication complexity for no reader-facing benefit.

## R3 — Migration of existing pages: copy vs. `git mv`

**Decision**: Use `git mv` to relocate `docs/docs/architecture.md`, `schemas.md`, `generators.md`, `transforms.md`, and the `avd/` directory into `docs/docs/developer-guide/`.

**Rationale**:
- Preserves git history for blame and `git log --follow`, which matters because these pages are the authoritative starting point of the developer guide and FR-026 explicitly forbids duplication.
- Forces an editorial pass: every moved file must have its internal links updated, which surfaces stale anchors as a side effect of the move.

**Alternatives considered**:
- *Copy then delete*: Rejected — loses git history for the moved files, which makes future doc-rot diagnosis harder.
- *Leave existing pages in place, add new pages alongside*: Rejected — violates FR-003 (every page in exactly one track) since the existing pages are inherently developer content but live at the doc root.

## R4 — Track identification on each page

**Decision**: Per-page front-matter field `audience: user` or `audience: developer`, plus a track-specific Docusaurus admonition shown at the top of each developer page (e.g. `:::info Developer Guide`). User pages do not need an admonition because the URL prefix and sidebar location already signal the track unambiguously to a reader who arrived via the sidebar — but a search-engine arrival to a developer page is the failure mode worth defending against (Edge Case "Reader lands on a developer page from a search engine").

**Rationale**:
- Front-matter is machine-readable and lets future tooling (broken-link checkers, search facets) filter by track without parsing page content.
- Admonitions on developer pages are a low-cost, theme-native banner that a misrouted user can spot in one glance.
- Symmetric admonitions on user pages would add visual noise for the common case (operator browsing the user track) without adding value.

**Alternatives considered**:
- *Custom React component for a track badge*: Rejected — introduces a swizzle and JSX into MDX pages for what an admonition already covers.
- *No track marker beyond URL*: Rejected — fails the search-engine-arrival edge case.

## R5 — Cross-track linking convention

**Decision**: Cross-track links MUST use explicit audience-signalling text. Pattern:

> "see the [developer reference for the hostvars schema](/developer-guide/avd/hostvars)"
> "for the operator workflow, see [Add a Network Segment](/user-guide/how-to/add-network-segment)"

Where `audience: user` → audience word "operator workflow" or "user guide"; where `audience: developer` → audience word "developer reference" or "developer guide". Plain link text without an audience word is reserved for same-track links.

**Rationale**:
- Satisfies FR-004 (cross-track links labelled with destination audience) without requiring a custom MDX component.
- Reviewable mechanically: a PR diff that introduces a cross-track link can be checked for the audience word in the link text.
- Survives docs build because Docusaurus's `onBrokenLinks: 'throw'` already validates the path; this convention only adds discipline to the surrounding text.

**Alternatives considered**:
- *Custom `<CrossTrackLink>` MDX component*: Rejected — adds a swizzle for a discipline that prose can carry.
- *Color-coded link styling via CSS*: Rejected — fails for users with custom themes or screen readers.

## R6 — Source-of-truth linking: relative paths vs. permalinks

**Decision**: When a developer-guide page references a file inside this repository, link with a path relative to the docs root using Docusaurus's `editUrl` base (`https://github.com/opsmill/infrahub-arista-avd/tree/main/<path>`) for source files outside `docs/`, and Markdown-relative links (`./other-page.md`) for sibling doc pages. Pin links that name a specific commit only when documenting historical behaviour; otherwise track `main`.

**Rationale**:
- The existing `docusaurus.config.ts` already wires `editUrl` to a `main`-branch GitHub URL for the docs themselves, so reusing that pattern for source links keeps the convention consistent.
- Markdown-relative links between sibling docs are validated at build time by `onBrokenMarkdownLinks: 'throw'`. Absolute GitHub URLs cannot be validated by Docusaurus but cover the source-tree case where Docusaurus has no knowledge of `src/`, `generators/`, `transforms/`, etc.
- Tracking `main` (rather than the current commit SHA) means docs stay current as code evolves, accepting the minor risk that a temporary `main` breakage could break a doc link.

**Alternatives considered**:
- *Permalink-pinning every source link to a SHA*: Rejected — forces a docs PR every time the linked file moves, and provides no practical benefit since the docs are versioned with the code.
- *Custom Docusaurus plugin to rewrite repo-relative paths*: Rejected — out of scope; FR-024 forbids new doc-build dependencies.

## R7 — Mermaid diagrams vs. ASCII art

**Decision**: Adopt Mermaid (`@docusaurus/theme-mermaid` is already installed and `markdown.mermaid: true` is already set in `docusaurus.config.ts`) for all *new* architectural diagrams. Existing ASCII diagrams (architecture overview, IP pool tree) may stay as-is during the migration; a follow-up pass can convert them.

**Rationale**:
- Mermaid renders interactively, supports dark mode (already themed in the config), and is searchable by node label.
- The dependency is already installed, satisfying FR-024.
- A bulk ASCII→Mermaid conversion is gold-plating that the spec did not request; deferring it keeps the migration focused.

**Alternatives considered**:
- *Convert all existing diagrams during this feature*: Rejected — adds scope without changing reader outcomes and risks introducing rendering regressions.
- *Stick with ASCII everywhere*: Rejected — Mermaid is already a dependency and offers strictly better readability for new diagrams.

## R8 — Replace absolute GitHub URLs with relative links?

**Decision**: For URLs pointing inside this repository (e.g. the existing `https://github.com/opsmill/infrahub-arista-avd/blob/main/README.md` link in `docs/docs/home.md`), replace with a Markdown-relative link to a docs page where one exists, or with a `https://github.com/opsmill/infrahub-arista-avd/tree/main/<path>` link otherwise. Leave external URLs (issues, PRs, third-party docs) untouched. This addresses Edge Case "Project rename / repo move" without breaking external references.

**Rationale**: Aligns with FR-021 (relative links to source). Reduces breakage if the repo is forked or renamed.

**Alternatives considered**:
- *Make this a hard MUST in the spec*: The spec downgraded this to SHOULD in the edge-case list because the URLs in question are valid today and the cost of leaving them is low. Plan respects that.

## R9 — Streamlit page → user-guide mapping

The four service-portal pages live under `service_catalog/pages/`:

| Streamlit page | User-guide page |
|----------------|------------------|
| `1_Create_Segment.py` (Add Network Segment) | `user-guide/how-to/add-network-segment.md` |
| `2_Add_Server.py` (Add Server) | `user-guide/how-to/add-server.md` |
| `3_Create_Tenant.py` (Create Tenant) | `user-guide/how-to/create-tenant.md` |
| `4_Fabric_View.py` (Fabric Design) | `user-guide/how-to/regenerate-fabric.md` |

Each how-to page MUST describe the form fields shown in the corresponding Streamlit page (visible at the top of each `.py`'s `main()` function), the objects created on the resulting branch, and how to find the proposed change.

**Decision**: Each how-to page draws its inputs/outputs section directly from the Streamlit form definition (which lives in the `.py` files above) so screenshots and field lists stay in sync with the implementation. The page will name the Streamlit `.py` file at the bottom under "Source" so a reader can verify behaviour.

## R10 — pyAVD version pinning in the developer guide (FR-020)

**Decision**: The developer guide's "AVD Integration Overview" page MUST include a callout naming the pyAVD version as `>=5.0.0` (the constraint pinned in `pyproject.toml`) and listing the version-sensitive sections: hostvars structure (R10-A), role names (R10-B), and pyAVD function names referenced in transforms (R10-C). On a future pyAVD upgrade, those sections can be audited as a unit.

**Rationale**: FR-020 requires it; centralising the version pin and the version-sensitive section list in one place makes upgrade-time review tractable.

## Open Items

None. All NEEDS CLARIFICATION items resolved.
