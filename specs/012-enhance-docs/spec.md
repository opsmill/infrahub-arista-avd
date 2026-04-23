# Feature Specification: Enhanced User and Developer Documentation

**Feature Branch**: `012-enhance-docs`
**Created**: 2026-04-23
**Status**: Draft
**Input**: User description: "I need to enhance the docs. I need a user docs and a developer docs. The developer docs will detail the tight integration with avd where as the userdocks are how to consume the integration and do standard things"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator gets first fabric to "configs rendered" via the user guide (Priority: P1)

A network engineer who has just cloned the repository follows the user documentation to stand up the stack, load seed data, run the fabric generator chain, and view the rendered AVD EOS configurations and fabric documentation for `Fabric-A` — without needing to read a single Python file.

**Why this priority**: This is the core promise of the project — turn an opinionated data model into device configurations. If a new operator cannot reach rendered configs by following the docs, the integration is effectively unusable to its target audience. Everything else (extending, customising, troubleshooting) builds on this baseline.

**Independent Test**: A reviewer with no prior context can clone the repo, follow only the user docs from "Getting Started" to "View Artifacts", and end up with a generated EOS config artifact attached to a leaf device in the Infrahub UI. No CLAUDE.md, source code, or external help required.

**Acceptance Scenarios**:

1. **Given** a fresh clone of the repository, **When** the operator follows the "Quick Start" page, **Then** they have Infrahub running, schemas loaded, and seed data populated.
2. **Given** the stack is running and seed data is loaded, **When** the operator follows the "Provision Your First Fabric" page, **Then** they have a populated `Fabric-A` with super-spines, spines, leaves, and rendered AVD artifacts (EOS config, fabric doc, device doc) viewable in the Infrahub UI.
3. **Given** a generator run failed mid-way, **When** the operator consults the "Troubleshooting" page, **Then** they find a documented cause and remediation for the most common failure modes (Infrahub not healthy, generators run out of order, missing seed data).

---

### User Story 2 - Operator performs standard service-catalog workflows (Priority: P1)

An operator uses the user documentation to perform the day-2 workflows exposed by the Streamlit service portal: adding a network segment (VRF + VLAN + SVI), adding a server to a compute rack, creating a new EVPN tenant, and triggering a full fabric regeneration from the Fabric Design page.

**Why this priority**: The service portal is the intended consumption surface for non-developer users. Without docs covering each portal workflow end-to-end (inputs, what gets created, what proposed change appears, how to merge it), users will either avoid the portal or fall back to creating objects directly in Infrahub — losing the safety of the branch+proposed-change pattern.

**Independent Test**: A reviewer who has completed Story 1 can complete each of the four service-portal workflows (network segment, server, tenant, fabric regeneration) by following only the corresponding "How To" pages in the user docs, and ends each workflow with a merged proposed change and updated AVD artifacts.

**Acceptance Scenarios**:

1. **Given** a populated fabric and a tenant, **When** the operator follows "Add a Network Segment", **Then** they create a VRF + VLAN + SVI on the chosen fabric and see the resulting proposed change with regenerated AVD configs.
2. **Given** a compute rack with at least one slot, **When** the operator follows "Add a Server", **Then** a new server is provisioned with cabling and the proposed change shows updated leaf-side configuration for the connected ports.
3. **Given** a fabric exists, **When** the operator follows "Create a Tenant", **Then** a tenant is created with MAC VRF VNI base allocations on the chosen fabrics and is selectable in the network-segment workflow.
4. **Given** a fabric in any state, **When** the operator follows "Regenerate a Fabric from the Fabric Design page", **Then** the generator chain runs to completion and updated artifacts are available.

---

### User Story 3 - Developer understands the AVD pipeline well enough to extend it (Priority: P1)

A developer joining the project (or an existing developer asked to support a new device role, EVPN feature, or transform output) reads the developer documentation and can describe — from memory after one read — the two-phase generator pipeline, the role of `AvdArtifact` and the object store, the hostvars contract passed to pyAVD, and where to add code for a new generator, transform, or schema extension.

**Why this priority**: The AVD integration is the technically distinguishing feature of this repository and the area most likely to need extension. Without accurate developer docs, contributors will reverse-engineer the pipeline from source each time, producing inconsistent extensions and regressions in the hostvars contract.

**Independent Test**: A reviewer who has not contributed to the AVD code can read the developer docs and answer the following without referring to source: (a) what runs in Phase 1 vs Phase 2 and on what target, (b) what is stored in the object store vs in graph attributes, (c) what fields a new device role would need to add to hostvars, (d) which file(s) to modify to add a new transform output. Each answer should map cleanly to one section of the developer docs.

**Acceptance Scenarios**:

1. **Given** the developer docs, **When** a contributor needs to add support for a new device role, **Then** the docs identify (a) where the Infrahub→AVD role map lives, (b) which generator emits the role-specific hostvar block, and (c) the test that exercises the role mapping.
2. **Given** the developer docs, **When** a contributor needs to add a new artifact type, **Then** the docs walk through the four touch-points: GraphQL query, Pydantic query model, transform class, and `.infrahub.yml` registration.
3. **Given** the developer docs, **When** a contributor needs to debug a "missing structured config" error, **Then** the docs describe the object-store identifier flow (`AvdArtifact.hostvar_identifier` → Phase 2 reads → `structured_config_identifier` → transform reads) so the contributor can locate the broken step.

---

### User Story 4 - Reader navigates between user and developer docs without confusion (Priority: P2)

A reader landing on the documentation home page can identify within 10 seconds whether they want the user track or the developer track, choose accordingly, and navigate within the chosen track without accidentally landing in pages written for the other audience. Cross-links from a user page to a relevant developer deep-dive are explicit and labelled as such.

**Why this priority**: Mixed audiences in a single doc set is the most common failure mode of "we have docs". The split is only valuable if the navigation makes the split obvious — otherwise readers see one big sidebar and we are back to where we started. P2 because the value depends on Stories 1–3 being solid first.

**Independent Test**: Open the docs home page in a browser. Within 10 seconds, identify the entry point for "I want to use the system" vs "I want to extend the system". Click into one track and confirm the sidebar shows only that track's pages (with at most a labelled link to the other track). Do the same for the second track.

**Acceptance Scenarios**:

1. **Given** the docs home page, **When** the reader scans it, **Then** two clearly labelled entry points ("User Guide" and "Developer Guide") are visible above the fold with a one-line description of each audience.
2. **Given** a user guide page, **When** it references something that lives in the developer guide, **Then** the link text explicitly signals the audience switch (e.g. "see the developer reference for the hostvars schema").
3. **Given** the sidebar on any page, **When** the reader looks at it, **Then** the active section (User vs Developer) is visually distinct and the other section is reachable in one click.

---

### User Story 5 - Docs stay in sync with the code via referenced sources (Priority: P3)

Where developer docs describe code (file paths, class names, schema kinds), they reference the canonical source so that a reader can jump from doc to code in one click. Where they describe runtime behaviour (e.g. role mapping table, hostvars structure), they include or link to the test that pins that behaviour.

**Why this priority**: Documentation drift is inevitable; what matters is making it discoverable. P3 because this is a quality-of-life improvement on top of correct content — the docs are useful even without it.

**Independent Test**: Pick five concrete claims from the developer docs (e.g. "the role map lives in `src/solution_arista_avd/avd.py`", "Phase 2 runs per fabric"). For each, confirm the docs link directly to the source file (or a labelled section anchor) and to the test that exercises the behaviour.

**Acceptance Scenarios**:

1. **Given** a developer doc page, **When** it names a Python class or file path, **Then** that name links to the file in the repository (relative link to the source tree).
2. **Given** a developer doc page describing observable behaviour, **When** that behaviour is covered by a test, **Then** the doc names the test file so a reader can verify or update it.

---

### Edge Cases

- **Operator runs generators in the wrong order**: The user docs MUST document the required generator order and the symptoms of running them out of order, because the generator chain is not strictly enforced by the UI.
- **Service portal is unavailable but Infrahub is up**: The user docs MUST cover the "do this in the Infrahub UI instead" fallback for at least the network-segment and tenant workflows, since the portal is a convenience layer.
- **Reader lands on a developer page from a search engine**: Each developer page MUST carry a banner or front-matter label identifying it as developer content, so a misrouted user knows to switch tracks.
- **AVD/pyAVD upstream version changes**: The developer docs MUST pin the pyAVD version they describe and call out which sections are version-sensitive (hostvars schema, role names) so that a future upgrade can audit the right pages.
- **Project rename / repo move**: Hard-coded GitHub URLs in the existing docs SHOULD be replaced with relative links where possible, so that a fork or rename doesn't silently break navigation.
- **Reader copies a code/CLI snippet**: Snippets MUST be copy-pasteable as-is on a fresh clone (no placeholders like `<your-fabric>` without an explicit example, no shell prompts mixed into the command).

## Requirements *(mandatory)*

### Functional Requirements

#### Structure & Navigation

- **FR-001**: The documentation site MUST present two top-level tracks, "User Guide" and "Developer Guide", that are visually distinct in the sidebar and discoverable from the home page.
- **FR-002**: The home page MUST describe each track in one sentence and link to the entry page of each.
- **FR-003**: Every page MUST belong to exactly one track (user or developer) and MUST identify its track in the sidebar grouping.
- **FR-004**: Cross-track links MUST be labelled with the destination audience (e.g. "see the developer reference …").

#### User Guide Content

- **FR-005**: The user guide MUST include a "Prerequisites & Quick Start" page covering the install, build, start, and load steps required to reach a usable Infrahub instance with seed data.
- **FR-006**: The user guide MUST include a "Provision Your First Fabric" page that walks an operator from a loaded-but-empty fabric to rendered AVD artifacts (EOS config, fabric doc, device doc).
- **FR-007**: The user guide MUST include one "How To" page per service-portal workflow currently exposed: Add a Network Segment, Add a Server, Create a Tenant, Regenerate a Fabric from the Fabric Design page.
- **FR-008**: Each "How To" page MUST describe the inputs the operator supplies, the objects that are created on the branch, what appears in the resulting proposed change, and how to merge it.
- **FR-009**: The user guide MUST include a "Viewing Artifacts" page that explains how to find and download the EOS configuration, fabric documentation, and device documentation artifacts from the Infrahub UI.
- **FR-010**: The user guide MUST include a "Common Issues" troubleshooting page that covers at minimum: stack not healthy, generators run out of order, missing seed data, "no structured config available" when viewing an artifact.
- **FR-011**: The user guide MUST NOT require the reader to read Python source, GraphQL queries, or schema YAML to complete any documented workflow.

#### Developer Guide Content

- **FR-012**: The developer guide MUST include an "AVD Integration Overview" page describing the two-phase generator pipeline (hostvars → structured config) and naming the target (per-device vs per-fabric) of each phase.
- **FR-013**: The developer guide MUST document the `AvdArtifact` node and its role as the bridge between graph data and object-store payloads (hostvars and structured config identifiers + checksums).
- **FR-014**: The developer guide MUST document the Infrahub-role → AVD-type mapping table and identify the source file where the mapping is defined.
- **FR-015**: The developer guide MUST document the hostvars structure produced for each device role (super-spine, spine, leaf), including which fields are required by pyAVD and which are populated from which Infrahub attributes.
- **FR-016**: The developer guide MUST document each transform (`avd_eos_config`, `avd_fabric_doc`, `avd_device_doc`) including its query, content type, target group, and the pyAVD function it wraps.
- **FR-017**: The developer guide MUST document each artifact definition and the generator+transform chain that produces it.
- **FR-018**: The developer guide MUST include an "Extending the Integration" page that walks through, as worked examples: adding a new device role, adding a new transform output, and adding a new field to hostvars.
- **FR-019**: The developer guide MUST include a "Debugging the Pipeline" page covering object-store inspection, checksum-based change detection, and how to re-run a single generator or transform in isolation.
- **FR-020**: The developer guide MUST identify the pyAVD version it targets and call out sections that are version-sensitive.

#### Source-of-Truth Linking

- **FR-021**: Where the developer guide names a Python file, class, GraphQL query, or schema kind, it MUST link to the source location in the repository using a relative link.
- **FR-022**: Where the developer guide describes observable behaviour pinned by a test, it MUST name the test file.
- **FR-023**: Where the user guide references an Infrahub UI element (button, page, action), it MUST use the exact label shown in the UI.

#### Build & Maintenance

- **FR-024**: The documentation site MUST build cleanly with the existing Docusaurus tooling (`docs/` directory, current `package.json`) without introducing new doc-build dependencies.
- **FR-025**: The sidebar configuration MUST express the user/developer split declaratively (one category per track) so that adding a page under the correct track is a one-line change.
- **FR-026**: The existing AVD content (`docs/docs/avd/README.md`) MUST be migrated into the developer guide rather than duplicated.

### Key Entities *(documentation artefacts)*

- **User Guide**: A track of pages aimed at network engineers and operators consuming the system. Pages: Quick Start, Provision Your First Fabric, How-To pages (one per portal workflow), Viewing Artifacts, Common Issues. No Python or GraphQL required to follow.
- **Developer Guide**: A track of pages aimed at contributors extending or maintaining the system. Pages: AVD Integration Overview, Hostvars Reference, Transforms Reference, AvdArtifact & Object Store, Role Mapping, Extending the Integration, Debugging the Pipeline. Links to source and tests throughout.
- **Documentation Home**: A single landing page that routes the reader to the correct track and provides project-level context (what the project is, which Infrahub version, which pyAVD version).
- **Sidebar Configuration**: The Docusaurus `sidebars.ts` definition expressing the two-track structure with one collapsible category per track.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new operator following only the user guide can go from a fresh clone to a viewable EOS configuration artifact in under 30 minutes (excluding the one-time Docker image build).
- **SC-002**: A new operator can complete each of the four service-portal workflows (network segment, server, tenant, regenerate fabric) by following only the corresponding "How To" page, with no need to consult source code or external resources.
- **SC-003**: A developer who has not previously worked on the AVD integration can, after one read of the developer guide, correctly answer all four orientation questions in Story 3's Independent Test (Phase 1 vs 2 targets, object-store vs graph storage, role-extension touch-points, transform-extension touch-points).
- **SC-004**: From the documentation home page, a reader can reach the entry page of either track in one click.
- **SC-005**: 100% of the standard service-portal workflows currently exposed in the Streamlit UI have a corresponding "How To" page in the user guide.
- **SC-006**: 100% of the components registered in `.infrahub.yml` under the AVD integration (queries, generator definitions, transforms, artifact definitions) are documented in the developer guide.
- **SC-007**: Every code reference in the developer guide (file path, class name, schema kind) resolves to an existing location in the repository at the time the docs are built.
- **SC-008**: The Docusaurus build completes without warnings about broken internal links.

## Assumptions

- The existing Docusaurus site under `docs/` is the documentation surface; this work extends it rather than introducing a new tool.
- The current technical pages (`architecture.md`, `schemas.md`, `generators.md`, `transforms.md`, `avd/README.md`) are the foundation of the developer guide and will be re-organised, expanded, and cross-linked rather than rewritten from scratch.
- "Standard things" in the user prompt refers to the workflows currently exposed in the Streamlit service portal (`service_catalog/`): add network segment, add server, create tenant, regenerate a fabric. If new portal workflows are added, the user guide gains a corresponding "How To" page.
- The AVD integration documented is the current implementation as of branch `juniper-study`; the pyAVD version is whatever `pyproject.toml` pins (currently `pyavd>=5.0.0`).
- Documentation changes do not require schema, generator, transform, or service-portal changes — this is a docs-only feature.
- The audience split is two-way (user vs developer). A possible third track (operator/SRE running this in production: backups, upgrades, scaling) is out of scope for this iteration.
- Per-page front-matter or banners identifying the track are acceptable; we do not need a separate Docusaurus instance per track.
- Existing GitHub issue/PR/repo URLs in the README and docs remain valid; we will replace absolute GitHub links with relative links only when the target lives inside this repository.

## Out of Scope

- Auto-generating reference content from source (e.g. extracting hostvars schema from `src/solution_arista_avd/avd.py` at build time). Manual cross-references with named source paths are sufficient for this iteration.
- An operator/SRE production-ops track (backups, upgrades, monitoring, scaling).
- Internationalisation or translation.
- Video walkthroughs or animated GIFs.
- A separate Docusaurus instance, custom theme, or branding redesign.
- Public hosting / GitHub Pages deployment configuration changes (the existing build target is unchanged).
