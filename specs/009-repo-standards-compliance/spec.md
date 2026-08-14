# Feature Specification: Repository Standards Compliance

**Feature Branch**: `atg/loud-cooks-find`

**Created**: 2026-08-11

**Status**: Draft

**Input**: User description: "lets add these recommendations" — the nine remediation items produced by the OpsMill `auditing-repo-standards` audit of this repository (2026-08-11): CI file-change detection, markdown linting, a documentation build gate, npm→pnpm migration for `docs/`, project metadata completion, Infrahub/SDK auto-bump workflows plus pin reconciliation, Vale prose linting, and the smaller hygiene items (gitignore secret patterns, yamllint `truthy`, CI action version pins, `CLAUDE.md` entry-point form).

## Clarifications

### Session 2026-08-11

- **Q: How should the pre-existing violation backlog be handled when Markdown and prose linting are introduced across 257 previously-unlinted files?**
  **A:** Fix every violation now. The new checks land enforcing, over all authored content, with the backlog cleared in the same feature — no narrowed initial path set and no non-blocking grace period.
- **Q: Which Infrahub version should the reconciled pin land on?**
  **A:** `1.10.6` — the newest stable release in the 1.10.x line. This is a deliberate patch upgrade from the constitution's stated `1.10.1` and from the `1.10.3` the CI image build currently uses, so the constitution's Technology Stack section is amended in the same change and the upgrade is validated before merge.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Documentation defects are caught before merge (Priority: P1)

A contributor edits pages under `docs/docs/` and opens a pull request. Today nothing in CI builds the documentation site or lints Markdown, so a broken link target, an invalid MDX construct, or a malformed table merges unnoticed and is only discovered when someone builds the site by hand. After this change, the pull request runs a documentation build and a Markdown lint pass, and the contributor sees the failure on the pull request itself.

**Why this priority**: This is the largest correctness gap the audit found — 257 tracked Markdown/MDX files and a full Docusaurus site with zero automated verification. It is also self-contained: it delivers value with no dependency on the other stories.

**Independent Test**: Open a pull request containing a deliberately broken docs page (an unresolvable link or invalid MDX) and a Markdown file with a lint violation. Both the docs-build check and the Markdown-lint check must fail. Revert the defects and both must pass on an already-clean authored-content baseline.

**Acceptance Scenarios**:

1. **Given** a pull request that introduces a documentation page which fails to build, **When** CI runs, **Then** a documentation-build check fails and names the offending file.
2. **Given** a pull request that introduces a Markdown style violation in a linted path, **When** CI runs, **Then** a Markdown-lint check fails and names the file and rule.
3. **Given** a pull request whose documentation and Markdown are both valid, **When** CI runs, **Then** both checks pass.
4. **Given** a maintainer working locally, **When** they run the repository's task-runner lint command, **Then** Markdown linting runs alongside the existing Python and YAML linters and reports the same findings CI would.
5. **Given** a maintainer working locally, **When** they run the repository's documentation-build task, **Then** the site builds using the repository's single supported JavaScript package manager, with no second lockfile produced.

---

### User Story 2 - CI runs only the checks a change needs (Priority: P2)

A contributor opens a pull request that touches only Markdown files. Today every job runs: Python linting, mypy, and the full unit-test suite. After this change, CI determines which categories of file changed and runs only the matching jobs, so feedback arrives faster and runner time is not spent on checks that cannot be affected.

**Why this priority**: It reduces cost and latency on every pull request and is the prerequisite that keeps User Story 1 and User Story 4 from making CI slower for everyone. It is lower priority than P1 because the existing checks are correct today — just wasteful.

**Independent Test**: Open three pull requests — one touching only `docs/`, one touching only a Python file, one touching only a YAML file — and confirm that in each case only the relevant checks execute while the others report as skipped and do not block the merge.

**Acceptance Scenarios**:

1. **Given** a pull request that changes only Markdown files, **When** CI runs, **Then** the Python lint and unit-test checks do not execute and the pull request is still mergeable once the checks that did run have passed.
2. **Given** a pull request that changes a Python file, **When** CI runs, **Then** the Python lint and unit-test checks execute.
3. **Given** a pull request that changes only files in no recognised category, **When** CI runs, **Then** the pull request remains mergeable and no check is left permanently pending.
4. **Given** a pull request opened from a fork, **When** CI runs, **Then** change detection still resolves correctly and does not fail the run.

---

### User Story 3 - Upstream Infrahub and SDK releases arrive as reviewable pull requests (Priority: P2)

A new Infrahub release or `infrahub-sdk` release is published upstream. Today nothing notices, and the repository silently drifts — the audit found the Infrahub version already pinned inconsistently in two places. After this change, an upstream release opens a pull request against the default branch that updates every place the version is pinned, so a maintainer reviews a single coherent change instead of discovering the drift later.

**Why this priority**: Version drift is already present, and drift between the local stack pin and the CI build pin produces failures that are expensive to diagnose. It ranks below the docs gate because it prevents future problems rather than fixing a currently-broken gate.

**Independent Test**: Manually trigger each bump workflow with an explicit version and confirm it opens one pull request that updates every pinned location consistently, and that re-triggering the same version does not open a duplicate.

**Acceptance Scenarios**:

1. **Given** the repository after reconciliation, **When** any consumer of the Infrahub version is inspected, **Then** it resolves to `1.10.6`.
2. **Given** an upstream Infrahub release notification, **When** the bump process runs, **Then** a single pull request updates every location where the Infrahub version is pinned and leaves no location on the old version.
3. **Given** an upstream SDK release notification, **When** the bump process runs, **Then** a single pull request updates the dependency declaration and the lockfile together.
4. **Given** a bump process that has already opened a pull request for a given version, **When** it is triggered again for that same version, **Then** no duplicate pull request is created.
5. **Given** the repository after this change, **When** a maintainer looks for the Infrahub version the project targets, **Then** there is one authoritative value and every other reference derives from or matches it.

---

### User Story 4 - Documentation prose is checked for house style (Priority: P3)

A contributor writes a new documentation page. After this change, a prose-style check runs against the documentation tree and reports terminology and style deviations, so the docs read consistently without a reviewer having to catch every instance by hand.

**Why this priority**: Valuable for documentation quality but the lowest-risk gap — inconsistent prose does not break the product, and the audit rates it a warning. It depends on the change-detection work (US2) to avoid running on every unrelated pull request.

**Independent Test**: Add a documentation page containing a known style violation and confirm the prose-style check reports it; correct the wording and confirm the check passes.

**Acceptance Scenarios**:

1. **Given** a pull request that changes documentation prose containing a style violation, **When** CI runs, **Then** the prose-style check reports the violation with file and line.
2. **Given** a pull request that touches no documentation, **When** CI runs, **Then** the prose-style check does not execute.
3. **Given** the documentation tree as it exists at the time this lands, **When** the prose-style check runs on the default branch, **Then** it completes without reporting failures, so the check starts from a clean baseline.

---

### User Story 5 - Repository baseline metadata and hygiene are complete (Priority: P3)

A maintainer or an automated audit inspects the repository. After this change the baseline is complete: the project declares real authorship and a description that says what the project is, secrets cannot be committed by common filename patterns, the YAML linter is configured so workflow-style keys cannot produce false positives, CI actions are on the versions the standard specifies, and the AI-assistant entry point is in the documented form.

**Why this priority**: Individually small and non-blocking, but together they close the remaining audit findings and make the next audit clean. Grouped last because none of them change contributor-visible behaviour.

**Independent Test**: Re-run the repository-standards audit and confirm every finding in this story's scope reports as passed.

**Acceptance Scenarios**:

1. **Given** the project metadata, **When** it is inspected, **Then** authorship is populated and the description identifies this project specifically rather than describing a generic repository.
2. **Given** a contributor who accidentally stages a private key, certificate, or credentials file matching a common name pattern, **When** they check repository status, **Then** the file is ignored rather than staged.
3. **Given** a YAML file outside the currently-excluded directories that uses workflow-style keys, **When** the YAML linter runs, **Then** no false-positive truthiness finding is reported.
4. **Given** the CI workflow, **When** its action versions are compared against the repository standard, **Then** they match.
5. **Given** an AI assistant reading the repository entry point, **When** it loads the entry point file, **Then** it receives the project guidance, and the mechanism is the one the repository standard documents.

---

### Edge Cases

- **Pre-existing violation backlog**: The Markdown and prose checks are being introduced against 257 existing Markdown/MDX files that have never been linted, so the checks would fail on the default branch and block every unrelated pull request. Resolved: the backlog is cleared inside this feature, so the checks are enforcing from the moment they land. This makes the change large in line count — a substantial share of the diff will be prose corrections rather than tooling — and the correction pass must not alter documented commands, code samples, or link targets.
- **Vendored agent content**: `.claude/`, `.agents/`, `.specify/`, and `.superset/` contain third-party skill and command Markdown that this repository does not author. Linting it would produce findings nobody can act on, so these paths must be excluded from Markdown and prose checks.
- **Generated and rendered content**: `schema.graphql`, generated `*_query.py` models, `src/solution_arista_avd/protocols.py`, and AVD-rendered YAML under `lab/avd/intended` are already excluded from existing linters; new checks must not reintroduce them.
- **Skipped checks and merge blocking**: When change detection skips a job, the check must resolve in a state that does not leave a pull request permanently pending or falsely block it.
- **Two lockfiles**: If the JavaScript package-manager migration leaves both lockfiles present, dependency resolution diverges between contributors and CI. The old lockfile must be removed in the same change, and documentation must stop referencing the old commands.
- **Fork and bot pull requests**: Change detection and the docs build must work for pull requests from forks and from dependency bots, which run with a restricted token.
- **Bump workflow with no upstream credentials**: If the organisation-level token used to open bump pull requests is unavailable, the workflow must fail visibly rather than appear to succeed having changed nothing.
- **Version pin already ahead**: The local stack pin, the CI build pin, and the constitution's stated target currently disagree three ways. Resolved: all converge on `1.10.6`. Because that is ahead of every current reference, the change is an upgrade rather than a correction, so it carries upgrade validation and a constitution amendment — and any behaviour difference between `1.10.1`/`1.10.3` and `1.10.6` surfaces here rather than in a later unrelated pull request.
- **Locally-running instance differs from the pin**: The development instance in use reports a `1.11.0b1` pre-release, ahead of the reconciled `1.10.6` pin. Contributors must not infer the project target from whatever their local stack happens to be running; the authoritative pin is the only source.

## Requirements *(mandatory)*

### Functional Requirements

**Documentation quality gate (US1)**

- **FR-001**: Pull requests that change documentation MUST run a documentation site build, and the pull request MUST fail when the build fails.
- **FR-002**: Pull requests that change Markdown or MDX files MUST run a Markdown lint pass whose configuration lives with the project's other tool configuration rather than in a standalone file.
- **FR-003**: Markdown lint configuration MUST disable the line-length, inline-HTML, and first-line-heading rules, which conflict with MDX and long-form prose in this repository.
- **FR-004**: Markdown and prose checks MUST exclude vendored agent content and generated files, and MUST cover the documentation tree, `README.md`, and `AGENTS.md`.
- **FR-005**: The repository's task runner MUST expose a Markdown lint task, and the aggregate lint task MUST include it alongside the existing Python and YAML linters.
- **FR-005a**: Every Markdown and prose violation in authored content MUST be corrected within this feature, so both checks pass on the default branch the moment they become enforcing. Neither check may be introduced in a non-blocking mode or against a narrowed subset of authored content.
- **FR-005b**: The correction pass MUST NOT change the meaning of documentation: documented commands, code samples, configuration snippets, link targets, and heading anchors MUST remain functionally identical, so existing cross-references and copy-paste instructions continue to work.
- **FR-006**: The repository's task runner MUST expose a documentation-build task that produces the same result CI produces.
- **FR-007**: The repository MUST use exactly one JavaScript package manager for the documentation site, with exactly one committed lockfile, and all documentation and agent guidance MUST reference that manager's commands.

**Change-scoped CI (US2)**

- **FR-008**: CI MUST classify each pull request's changed files into categories covering at minimum Python, YAML, Markdown, and documentation.
- **FR-009**: Each existing and new CI check MUST execute only when its category changed, and MUST resolve in a non-blocking state otherwise.
- **FR-010**: A pull request whose changes match no category MUST remain mergeable with no check left indefinitely pending.

**Version currency (US3)**

- **FR-011**: The repository MUST provide an automated process that, on notification of an upstream Infrahub release, opens a pull request updating every location where the Infrahub version is pinned.
- **FR-012**: The repository MUST provide an automated process that, on notification of an upstream SDK release, opens a pull request updating the dependency declaration and lockfile together.
- **FR-013**: Both processes MUST be manually triggerable with an explicit target version and MUST NOT open a duplicate pull request when re-triggered for a version that already has one open.
- **FR-014**: The Infrahub version the project targets MUST have a single authoritative definition; the local stack, the CI image build, and any other consumer MUST agree with it.
- **FR-014a**: That authoritative value MUST be `1.10.6`. No location may remain on `1.10.1` or `1.10.3` after this change.
- **FR-014b**: Because `1.10.6` is ahead of the project's currently-stated target, the project constitution's stated Infrahub target MUST be amended in the same change, with the version bump its governance rules require.
- **FR-014c**: The upgrade to `1.10.6` MUST be validated before merge against the project's existing quality gates for a dependency change, and the result recorded on the pull request.

**Prose style (US4)**

- **FR-015**: Pull requests that change documentation prose MUST run a prose-style check reporting file and line for each finding.
- **FR-016**: The prose-style check MUST pass on the default branch when it is introduced, so it starts from a clean baseline. Where a finding reflects correct project or vendor terminology rather than a genuine style error, the term MUST be added to an accepted-terminology list rather than the prose being reworded to satisfy the checker.

**Baseline hygiene (US5)**

- **FR-017**: Project metadata MUST declare authorship and a description that identifies this project rather than a generic placeholder.
- **FR-018**: Version control MUST ignore common secret-bearing filename patterns, including private keys, certificates, and credential files.
- **FR-019**: YAML lint configuration MUST prevent false-positive truthiness findings on workflow-style keys, independently of which directories are currently excluded.
- **FR-020**: CI action versions MUST match those the repository standard specifies.
- **FR-021**: The AI-assistant entry point MUST use the mechanism the repository standard documents, and MUST continue to deliver the same project guidance.

**Cross-cutting**

- **FR-022**: Every new tool this feature introduces MUST be declared as a project development dependency with the lockfile updated in the same change, per the project's dependency-change gate.
- **FR-023**: All existing linters (Python, type checking, YAML) MUST continue to pass unchanged, and the existing unit-test suite MUST continue to run on every pull request that changes Python.
- **FR-024**: Every new CI job MUST declare an explicit timeout and MUST run under the workflow's existing least-privilege permissions, or declare the narrowest additional permission it requires.

### Out of Scope

- **Branch protection on the default branch.** The audit's governance finding cannot be remediated in this repository: `main` is unprotected because the private repository's GitHub plan returns `403` for both classic branch protection and rulesets. It requires a plan change or making the repository public, and is therefore excluded.
- **Running integration tests on pull requests.** The integration suites remain manually triggered. Changing that affects CI cost and runtime materially and is a separate decision.
- **Extending type-check coverage** to `generators/`, `transforms/`, `checks/`, `scripts/`, and `tests/`. The existing workflow already documents this as a tracked backlog with a deliberate non-blocking report; this feature does not change it.
- **Priority-7 audit extras** (dependency bot config, pull-request labeller, code owners, changelog tooling). Not part of the default audit and not requested.
- **Fixing the audit tooling itself.** The branch-protection checker crashing on a plan-gated `403` instead of skipping cleanly is an upstream skill defect to report, not work in this repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A documentation change that breaks the site build is rejected before merge in 100% of cases; today it is caught in 0%.
- **SC-002**: A Markdown style violation in an authored file is reported before merge in 100% of cases; today it is caught in 0%.
- **SC-002a**: Markdown and prose checks report zero findings across all authored content on the default branch once this feature lands, and every documented command and internal link still resolves after the correction pass.
- **SC-003**: A pull request touching only documentation runs no Python or test checks, and its total check time is reduced by at least half relative to the same change today.
- **SC-004**: Re-running the repository-standards audit reports zero errors and zero warnings across audit priorities 1 through 4, with the single governance item recorded as blocked for a stated external reason.
- **SC-005**: The Infrahub version the project targets resolves to `1.10.6` everywhere it is consumed — local stack, CI image build, and project governance — verifiable by inspection in under one minute, with zero remaining references to `1.10.1` or `1.10.3` as a target.
- **SC-006**: An upstream release of Infrahub or the SDK results in a review-ready pull request without a maintainer taking any manual step.
- **SC-007**: All new checks pass on the default branch immediately after this feature lands, so no unrelated pull request is blocked by a pre-existing violation.
- **SC-008**: A new contributor can build the documentation and run every linter the repository enforces using only commands listed in the repository's agent guidance, with no command that references a removed tool.

## Assumptions

- The nine recommendations in the 2026-08-11 audit report define the scope; no further findings are introduced.
- The audit rule set (`opsmill-repo/auditing-repo-standards` v0.0.10) is authoritative for tool choice and configuration shape, so its named tools and versions are adopted rather than alternatives.
- `CLAUDE.md` is currently a symlink to `AGENTS.md`, which is functionally correct. The default resolution is to keep the two files' content unified and satisfy the standard's documented mechanism, rather than fork the content into two maintained files.
- The organisation-level credential the bump workflows require already exists at the GitHub organisation level, as it does for other OpsMill repositories; if it does not, the bump workflows are inert until it is provisioned and that is treated as configuration, not a code defect.
- The default branch remains `main`, and the bump workflows target it.
- Vendored agent directories (`.claude/`, `.agents/`, `.specify/`, `.superset/`) are treated as third-party content excluded from authored-content checks.
- `1.10.6` is the newest stable release in the 1.10.x line at the time of writing; the newer `1.11.0` builds are pre-releases and are deliberately not adopted here.
- The `1.10.6` upgrade is expected to be behaviour-compatible within the 1.10.x line. If validation shows otherwise, that is a finding for this feature to surface, not to absorb silently.
- No Infrahub schema, generator, transform, check, menu, or object data is touched, so the project's schema-check, protocol-regeneration, and generator-idempotence gates are not triggered by the tooling work itself. The Infrahub version upgrade is a dependency change and carries the validation its own gate requires.
- Clearing the Markdown and prose backlog is expected to touch a large number of files. Reviewers should expect the diff to be dominated by mechanical prose corrections, with the tooling change being the small part.
