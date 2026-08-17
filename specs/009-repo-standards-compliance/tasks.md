---

description: "Task list for Repository Standards Compliance"
---

# Tasks: Repository Standards Compliance

**Input**: Design documents from `/specs/009-repo-standards-compliance/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/](./contracts/)

**Tests**: No test tasks are generated. The spec requests none, and this feature adds no application logic —
its verification surface is CI behaviour and linter exit codes, covered by the checkpoint tasks and
[quickstart.md](./quickstart.md). The existing `pytest tests/unit` suite must keep passing unchanged (FR-023).

**Organization**: Tasks are grouped by user story so each can be implemented, verified, and merged
independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Include exact file paths in descriptions

## Path Conventions

Repository-root tooling feature. No `src/` or `tests/` layout applies — paths are the real files named in
[plan.md](./plan.md) under "Source Code (repository root)".

---

## Phase 1: Setup (Tool Availability)

**Purpose**: Make the three new tools available before any configuration references them

- [X] T001 Add `rumdl` to the `dev` dependency group in `pyproject.toml` and refresh `uv.lock` via `uv add --dev rumdl` (FR-022; required by US1)
- [X] T002 [P] Verify the pinned prose linter installs and syncs by downloading Vale 3.17.1 and running `vale sync`, recording the result in the PR description (required by US4; Vale is not `uv`-installable per research.md R6)
- [X] T003 [P] Confirm pnpm 11 is available via `corepack enable` and record the exact patch version to pin in `docs/package.json` (required by US1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The change-detection plumbing and current action pins that every later CI job builds on

**⚠️ CRITICAL**: No user story's CI work can begin until T004 and T005 are complete — every gated job reads
`needs.files-changed.outputs.*`

- [X] T004 Create `.github/file-filters.yml` with the four filter categories and their `_all` aliases (`documentation`, `python`, `yaml`, `markdown`) per data-model.md entity 1 (FR-008)
- [X] T005 Add the `files-changed` job to `.github/workflows/ci.yml` using `opsmill/paths-filter@v3.0.2`, `timeout-minutes: 5`, and the four named outputs per contracts/ci-checks.md (FR-008, FR-024)
- [X] T006 Bump all action pins in `.github/workflows/ci.yml` to `actions/checkout@v7` and `astral-sh/setup-uv@v9` across the four existing jobs (FR-020; sequenced here rather than in US5 so later jobs are added on current pins — see research.md R7 for why the audit rule's own `v6`/`v7` values are stale)

**Checkpoint**: `files-changed` runs and reports four outputs on every pull request; existing jobs still run
unconditionally and still pass

---

## Phase 3: User Story 1 - Documentation defects caught before merge (Priority: P1) 🎯 MVP

**Goal**: A pull request that breaks the docs site or introduces a Markdown defect fails CI, where today
neither is checked at all.

**Independent Test**: Open a PR with a broken internal link and a Markdown violation; both the
`documentation` and `markdown-lint` checks must fail. Revert both; both must pass against an already-clean
baseline.

### Documentation toolchain (FR-006, FR-007)

- [X] T007 [US1] Delete `docs/package-lock.json` and generate `docs/pnpm-lock.yaml` by running `pnpm install` in `docs/` (FR-007 — exactly one lockfile must remain)
- [X] T008 [US1] Add the `packageManager: "pnpm@<version from T003>"` field to `docs/package.json` so `pnpm/action-setup@v6` resolves the version from the repo
- [X] T009 [P] [US1] Create `.node-version` at the repository root pinning Node 22 LTS, for `actions/setup-node@v7` to read via `node-version-file`
- [X] T010 [P] [US1] Remove the `npm-debug.log*` and `yarn-*.log*` patterns from `docs/.gitignore` — residue of the removed toolchains
- [X] T011 [US1] Add a type-annotated `docs` task to `tasks.py` running `pnpm install --frozen-lockfile && pnpm run build` in `docs/`, per contracts/task-runner.md (FR-006)
- [X] T012 [US1] Add the `documentation` CI job to `.github/workflows/ci.yml`, gated on `needs.files-changed.outputs.documentation`, with `timeout-minutes: 5`, pnpm + Node setup, and `uv run invoke docs` (FR-001)

### Markdown lint configuration (FR-002, FR-003, FR-004)

- [X] T013 [US1] Add the `[tool.rumdl]` section to `pyproject.toml` with `disable = ["MD013", "MD033", "MD041"]` — **the list form, not `MD013 = false`, which research.md R1 verified is silently ignored** (FR-002, FR-003)
- [X] T014 [US1] Add the `exclude` list to `[tool.rumdl]` in `pyproject.toml` covering `.agents`, `.claude`, `.specify`, `.superset`, `specs`, `lab/avd`, `CLAUDE.md`, `node_modules`, `.venv` per research.md R2 (FR-004 — `lab/avd/**` is PyAVD-rendered output and `CLAUDE.md` is a symlink to `AGENTS.md`)
- [X] T015 [US1] Set `front-matter-title = ""` under `[MD025]` in `pyproject.toml`, eliminating 26 false positives caused by Docusaurus frontmatter `title:` colliding with the page H1 (research.md R4 — the alternative auto-fix would delete H1s and break anchors, violating FR-005b)

### Markdown backlog (FR-005a, FR-005b)

- [X] T016 [US1] Run `rumdl fmt` over the authored set to clear the 65 auto-fixable issues (MD031, MD032, MD029), then inspect the diff to confirm no code fence content changed (FR-005b)
- [X] T017 [US1] Convert the bold pseudo-headings in `docs/docs/troubleshooting.md` (`**Symptoms**`, `**Diagnose**`, `**Fix**`) to real headings, clearing the 15 MD036 findings (FR-005a)
- [X] T018 [P] [US1] Add the missing language identifier to the 11 unlabelled code fences reported by MD040 across `docs/`, `README.md`, and `AGENTS.md` (FR-005a)
- [X] T019 [US1] Run `uv run rumdl check` over the authored set and confirm zero remaining issues, so the gate lands on a clean baseline (FR-005a, SC-002a)

### Markdown lint enforcement (FR-005)

- [X] T020 [US1] Add type-annotated `lint_markdown` task to `tasks.py` running `rumdl check` over the authored set, and add `rumdl fmt` to the existing `format` task, per contracts/task-runner.md (FR-005)
- [X] T021 [US1] Wire `lint_markdown` into the `lint_all` fan-out in `tasks.py` alongside `lint_yaml`, `lint_ruff`, and `lint_mypy` (FR-005)
- [X] T022 [US1] Add the `markdown-lint` CI job to `.github/workflows/ci.yml`, gated on `needs.files-changed.outputs.markdown`, with `timeout-minutes: 5`, running `uv run rumdl check` (FR-002)

### Documentation of the new surface

- [X] T023 [US1] Replace the `npm run typecheck` / `npm run build` block in `AGENTS.md` with the pnpm equivalents and add `lint-markdown` and `docs` to the documented invoke task list (FR-007, SC-008)
- [X] T024 [P] [US1] Update any `npm` command references in `README.md` to pnpm (FR-007)

**Checkpoint**: US1 complete — docs build and Markdown lint both gate pull requests, both pass on the
default branch, and `invoke docs` / `invoke lint-markdown` reproduce CI locally. Validate with
quickstart.md Phases B and C.

---

## Phase 4: User Story 2 - CI runs only the checks a change needs (Priority: P2)

**Goal**: A pull request runs only the checks its changed files can affect, cutting feedback time and runner
cost.

**Independent Test**: Open three PRs — docs-only, Python-only, YAML-only — and confirm each runs only its
relevant checks while the others report `skipped` and the PR stays mergeable.

- [X] T025 [US2] Gate the existing `lint` job in `.github/workflows/ci.yml` on `needs.files-changed.outputs.python == 'true'` with `needs: ["files-changed"]`, leaving its commands byte-identical (FR-009, FR-023)
- [X] T026 [US2] Gate the existing `unit-tests` job in `.github/workflows/ci.yml` on `needs.files-changed.outputs.python == 'true'` with `needs: ["files-changed"]`, leaving its command byte-identical (FR-009, FR-023)
- [ ] T027 [US2] Verify the skip semantics with the three-PR matrix in quickstart.md Phase A, confirming skipped jobs do not block merges (FR-010; safe here only because no branch protection exists — research.md R10)
- [ ] T028 [US2] Measure and record a docs-only PR's total check time against a pre-feature baseline run, confirming at least a 50% reduction (SC-003)

**Checkpoint**: US1 and US2 both work — new gates are in place and no job runs when it cannot be affected

---

## Phase 5: User Story 3 - Upstream releases arrive as reviewable pull requests (Priority: P2)

**Goal**: The Infrahub version has one authoritative value, and upstream releases open a coherent pull
request instead of drifting unnoticed.

**Independent Test**: Trigger each bump workflow with an explicit version; each opens one PR updating every
pinned location, and re-triggering the same version opens no duplicate.

### Pin reconciliation on 1.10.6 (FR-014, FR-014a)

- [X] T029 [US3] Change the `ARG INFRAHUB_BASE_VERSION` default in `Dockerfile:1` from `1.8.3` to `1.10.6` — a fourth divergent version the audit missed, which makes an argument-less build produce a two-minor-old image (research.md R8)
- [X] T030 [P] [US3] Update the `${VERSION:-1.10.1}` defaults on all three service definitions in `docker-compose.yml` (lines 246, 279, 325) to `1.10.6`
- [X] T031 [P] [US3] Update the image tag and `INFRAHUB_BASE_VERSION` build arg in `docker-compose.override.yml` (lines 3, 22) to `1.10.6`
- [X] T032 [P] [US3] Update the `docker build --build-arg`, image tag, and `INFRAHUB_TESTING_IMAGE_VER` values in `.github/workflows/ci.yml` (lines 116, 122) from `1.10.3` to `1.10.6`, keeping the tag and the testing variable in agreement
- [X] T033 [P] [US3] Update the documented `export INFRAHUB_BASE_VERSION` and prose version references in `README.md` (lines 39, 90) to `1.10.6`
- [X] T034 [P] [US3] Update the documented `export INFRAHUB_BASE_VERSION` in `docs/docs/quick-start.md:35` to `1.10.6`
- [X] T035 [US3] Verify convergence by grepping for stale Infrahub version references across the repository per quickstart.md Phase E, and confirm an argument-less `docker build` produces a `1.10.6` base (SC-005)

### Governance (FR-014b)

- [X] T036 [US3] Amend `.specify/memory/constitution.md`: Technology Stack Infrahub target `1.10.1` → `1.10.6`, version `1.1.1` → `1.2.0`, plus a Sync Impact Report header per the file's existing convention (FR-014b, research.md R11). If US1 and US4 have already landed, include the dev-dependency and linter-set lines in this same edit; otherwise T053 completes them

### Auto-bump workflows (FR-011, FR-012, FR-013)

- [X] T037 [US3] Create `.github/workflows/update-infrahub.yml` with `workflow_dispatch` + `repository_dispatch: [trigger-infrahub-update]`, the version-resolution ternary in the concurrency group, `sed` steps covering compose files and the `Dockerfile` ARG, the `infrahub-testcontainers` bump, and the open-PR duplicate guard, per contracts/ci-checks.md (FR-011, FR-013)
- [X] T038 [P] [US3] Create `.github/workflows/update-infrahub-sdk.yml` with `repository_dispatch: [trigger-infrahub-sdk-python-update]`, the same concurrency ternary, `uv add "infrahub-sdk[all]==${INFRAHUB_SDK_VERSION}"`, and commits of `pyproject.toml` + `uv.lock` only (FR-012, FR-013)
- [ ] T039 [US3] Exercise both workflows manually per quickstart.md Phase E, confirming one PR each, correct file coverage, and no duplicate on a second run for the same version (SC-006)

### Required validation (FR-014c)

- [ ] T040 [US3] Run `$infrahub-run-integration-tests` for the `1.10.6` upgrade and record the tested branch and commit on the pull request — mandated by Constitution Principle IV for a dependency change against an Infrahub version; unit tests alone are not sufficient to merge this phase (FR-014c)

**Checkpoint**: US3 complete — one authoritative pin, governance updated, and upstream releases self-open

---

## Phase 6: User Story 4 - Documentation prose checked for house style (Priority: P3)

**Goal**: Prose style deviations are reported before merge, without rewriting the docs' voice.

**Independent Test**: Add a page with a known style violation; the prose check reports it with file and
line. Correct it; the check passes.

- [X] T041 [US4] Create `.vale.ini` at the repository root with `StylesPath = .vale`, `MinAlertLevel = warning`, `Packages = Google, write-good`, `BasedOnStyles` for `*.md` and `*.mdx`, and explicit `NO` entries for `Google.EmDash`, `write-good.Passive`, and `write-good.TooWordy` (FR-015; the three disables remove 445 alerts that contradict the house voice — research.md R5)
- [X] T042 [US4] Create `.vale/config/vocabularies/OpsMill/accept.txt` with the 77 project and vendor terms behind the 490 `Vale.Spelling` alerts (Infrahub, PyAVD, EVPN, VXLAN, hostvars, ASNs, SVIs, VNIs, …), per FR-016's requirement to accept terminology rather than reword it
- [X] T043 [P] [US4] Add `.vale/Google/` and `.vale/write-good/` to `.gitignore` — synced at CI time, not vendored (research.md R6)
- [X] T044 [US4] Fix the 194 residual Vale alerts across `docs/docs/`, of which 84 are `Google.Headings` sentence-case changes. **Case-only heading edits are anchor-safe because Docusaurus lowercases slugs; any edit changing heading words must carry an explicit `{#old-anchor}`** (FR-016, FR-005b — see data-model.md "Apparent conflict, resolved")
- [X] T045 [US4] Add a type-annotated `lint_prose` task to `tasks.py` that runs `vale sync` then Vale over `docs/docs`, degrades to a skip-with-warning when the binary is absent, and is wired into the `lint_all` fan-out, per contracts/task-runner.md
- [X] T046 [US4] Add the `validate-documentation-style` CI job to `.github/workflows/ci.yml`, gated on `needs.files-changed.outputs.documentation`, `timeout-minutes: 5`, downloading Vale 3.17.1 manually (the official Action is broken) and running `vale sync` before linting (FR-015)
- [X] T047 [US4] Confirm `uv run invoke lint-prose` reports zero findings on the default branch, so the gate lands clean (FR-016)

**Checkpoint**: US1–US4 all work independently; prose is gated without a voice rewrite

---

## Phase 7: User Story 5 - Baseline metadata and hygiene complete (Priority: P3)

**Goal**: The remaining audit findings close, so the next audit reports clean.

**Independent Test**: Re-run the repository-standards audit and confirm every finding in this story's scope
reports as passed.

- [X] T048 [P] [US5] Set `authors = [{name = "OpsMill", email = "info@opsmill.com"}]` and replace the generic `description = "Infrahub Repository"` in `pyproject.toml` with a sentence naming this project and what it produces (FR-017)
- [X] T049 [P] [US5] Add the secret-bearing filename patterns (`*.pem`, `*.key`, `*.p12`, `credentials.json`, `secrets.yaml`) to `.gitignore` (FR-018)
- [X] T050 [US5] Verify the new ignore patterns hide nothing already tracked, using the `git status --ignored` check in quickstart.md Phase F (FR-018)
- [X] T051 [P] [US5] Add `truthy: check-keys: false` under `rules` in `.yamllint.yml`, preserving the existing `line-length.max: 140` and `ignore` block, then confirm `uv run invoke lint-yaml` still passes (FR-019)
- [X] T052 [US5] Resolve the AI-assistant entry point in favour of the standard's documented mechanism: replace the `CLAUDE.md` symlink with a file containing `@AGENTS.md`, keeping `AGENTS.md` as the single source of guidance (FR-021)

**Note**: FR-020 (action version pins) is delivered by T006 in the Foundational phase, sequenced there so
later jobs were added on current pins. It belongs to this story for traceability.

**Checkpoint**: All five stories complete

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Close the governance record and verify the whole feature against its success criteria

- [X] T053 Complete the `.specify/memory/constitution.md` amendment if T036 could not cover it: add `rumdl` to the enumerated dev dependencies, state pnpm as the docs package manager, and expand Principle IV's linter set from `ruff`/`mypy`/`yamllint` to include `rumdl` and Vale (research.md R11)
- [X] T054 [P] Verify no `npm` binary invocation remains outside vendored agent content, using the grep in quickstart.md Phase B (FR-007)
- [X] T055 [P] Confirm no new `TODO`, `FIXME`, or `XXX` markers were introduced without tracking context, per the constitution's pre-merge quality gates
- [X] T056 Run the full local suite — `uv run invoke lint`, `uv run pytest tests/unit`, `uv run invoke docs` — and confirm all pass, proving FR-023 held and SC-008 is met
- [X] T057 Run the complete quickstart.md validation end to end, including the deliberate-failure checks that prove each new gate actually bites
- [X] T058 Re-run the repository-standards audit and confirm zero errors and zero warnings across priorities 1–4, with governance recorded as blocked for the stated plan limitation (SC-004)
- [X] T059 [P] Report the two upstream defects found during research: the audit rule's non-functional `MD013 = false` config syntax and `rumdl "**/*.md"` invocation (research.md R1), and the branch-protection checker crashing on a plan-gated `403` instead of skipping cleanly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Needs T001–T003 only loosely; T004–T006 can begin at once. **Blocks every
  gated CI job in US1, US2, and US4**
- **US1 (Phase 3)**: Needs T001 (rumdl available), T003 (pnpm), T005 (`files-changed` outputs)
- **US2 (Phase 4)**: Needs T005. Independent of US1 — gating existing jobs does not touch US1's files beyond
  the same workflow
- **US3 (Phase 5)**: Needs only Phase 2. Fully independent of US1/US2/US4 except T036's optional coupling
- **US4 (Phase 6)**: Needs T002 (Vale verified), T005 (`documentation` output)
- **US5 (Phase 7)**: Needs nothing beyond Setup — every task is an isolated config file edit
- **Polish (Phase 8)**: Needs all stories that are in scope for the release

### Story Independence Notes

- US1, US2, US4, and US5 all edit `.github/workflows/ci.yml`. They are logically independent but will
  **conflict textually** if worked in parallel by different people. Either serialise the workflow edits or
  accept merge resolution in that one file.
- US3 is the only story requiring integration-test evidence (T040), so it should not gate the others'
  delivery — this is why plan.md sequences it last despite its P2 priority.
- T036 and T053 both touch the constitution. If US3 lands after US1 and US4, T036 absorbs T053 and T053
  becomes a no-op verification.

### Within Each User Story

- Configuration before backlog: T013–T015 must precede T016–T019, or `rumdl fmt` runs with the wrong rule
  set and rewrites files unnecessarily
- Backlog before enforcement: T019 must precede T022, and T047 must precede merging T046 — otherwise the
  gate lands red and blocks unrelated pull requests (FR-005a)
- Lockfile before pin: T007 (`pnpm-lock.yaml`) must precede T012, which runs `pnpm install --frozen-lockfile`

### Parallel Opportunities

- T002 and T003 in parallel with each other and with T001
- T009, T010 in parallel within US1; T018 and T024 in parallel with each other
- T030–T034 all in parallel — five separate files, one mechanical version substitution each
- T048, T049, T051 in parallel — three unrelated config files
- Whole stories in parallel across people, subject to the `ci.yml` conflict note above

---

## Parallel Example: User Story 3 pin reconciliation

```bash
# Five independent files, one substitution each — safe to fan out:
Task: "Update ${VERSION:-…} defaults on three services in docker-compose.yml"
Task: "Update image tag and build arg in docker-compose.override.yml"
Task: "Update build arg, tag, and INFRAHUB_TESTING_IMAGE_VER in .github/workflows/ci.yml"
Task: "Update export and prose references in README.md"
Task: "Update export in docs/docs/quick-start.md"

# Then serialise the verification, which reads all of them:
Task: "Verify convergence via grep and an argument-less docker build"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup — T001, T003 suffice for US1
2. Phase 2 Foundational — T004, T005, T006
3. Phase 3 US1 — T007 through T024
4. **STOP and VALIDATE**: quickstart.md Phases B and C, including the deliberate-failure checks
5. Merge. The repository now catches the largest gap the audit found: 257 Markdown files and a full docs
   site previously verified by nothing

### Incremental Delivery

1. Setup + Foundational → change detection reporting, nothing gated yet
2. US1 → docs build and Markdown lint enforcing (MVP)
3. US2 → checks scoped to changed files, PR feedback halves
4. US5 → baseline hygiene closes, cheapest story in the set
5. US4 → prose gate, after accepting the R5 configuration trade-off
6. US3 → pin reconciliation, governance amendment, bump workflows, integration-test evidence
7. Polish → audit re-run confirms clean

US5 is deliberately suggested ahead of US4 and US3 despite its P3 priority: it is five isolated config edits
with no backlog and no validation dependency, so it converts audit findings to green at the lowest cost.

### Parallel Team Strategy

1. Everyone waits on T004–T005 (one small PR)
2. Then: Developer A takes US1 (largest — toolchain plus backlog), Developer B takes US3 (independent, but
   owns the integration-test run), Developer C takes US2 + US5 (both small, both touch `ci.yml`, so pairing
   them in one person avoids conflict)
3. US4 follows US1, since both edit `docs/` content and would otherwise conflict in the backlog pass

---

## Notes

- **59 tasks**: 3 Setup, 3 Foundational, 18 US1, 4 US2, 12 US3, 7 US4, 5 US5, 7 Polish
- `[P]` tasks touch different files with no incomplete dependencies
- Two tasks encode research findings that contradict the audit rule text — T013 (`disable` list form, not
  `MD013 = false`) and T015 (MD025 `front-matter-title`). Implementing them from the rule text instead of
  from research.md R1/R4 will produce a config that silently does nothing
- Commit after each task or logical group; stop at any checkpoint to validate a story independently
- The one hard sequencing rule that spans stories: **never merge an enforcing lint job before its backlog
  task is complete** (FR-005a) — a red default branch blocks every unrelated pull request

---

## Implementation Record (2026-08-11)

55 of 59 tasks complete. Deviations from the task text, and why:

| Task | Planned | Done | Reason |
|---|---|---|---|
| T009 | Node 24 LTS | Node **22** | The development machine runs Node v22.23.1, still an active LTS. Pinning CI to 24 while contributors build on 22 invites version skew in the Docusaurus build for no gain. |
| T025 | Gate `lint` on `python` | Gated on `python` **or** `yaml` | That job also runs `yamllint`. Gating on `python` alone would skip YAML linting for a YAML-only change - a coverage regression the task text would have introduced. |
| T036 | Amend the Infrahub target | Amended target **plus** dev deps, package managers, and the Principle IV linter set | US1 and US4 landed in the same change, so T053's edits were folded in as planned. |
| T041 | Disable 3 Vale rules | Disabled **8** | `Google.Colons` wants schema kind names lowercased (`NetworkFabric`, `DcimDevice`); `Google.WordList` wants `CLI` to become "command-line tool"; `Google.WordListCase` wants `touch` (the Unix command) to become "tap"; `Google.HeadingPunctuation` reads the ordinal in `## 1. Install dependencies` as a trailing period; `Vale.Terms` cannot tell a sentence-initial capital from a casing error. Each carries its rationale in `.vale.ini`. |
| T044 | Fix 194 alerts | Fixed to **0 alerts** | 1,135 → 0. Roughly 60 were prose edits; the rest cleared through vocabulary and the rule decisions above. One heading in `supported-capabilities.md` uses a scoped `<!-- vale ... -->` comment so its published anchor is untouched. |
| - | - | Two extra `.yamllint.yml` ignores | The synced `.vale/` style packages and the new `docs/pnpm-lock.yaml` are generated YAML that yamllint began reporting. Required to keep FR-023 true. |

Not done - each needs a pull request, a live environment, or credentials this session does not have:

| Task | Blocker |
|---|---|
| T027 | Needs three real pull requests to observe skip semantics on GitHub. |
| T028 | Needs a before/after CI timing comparison from real runs. |
| T039 | `gh workflow run` requires the workflows on the default branch, and triggering them opens real pull requests. |
| T040 | `$infrahub-run-integration-tests` needs the designated validation environment. **Constitution Principle IV blocks merging the 1.10.6 upgrade without this evidence.** |

One `1.10.1` reference is deliberately left in place: `docs/handoff-rack-generator-repro-fix-20260727.md:84`
records, in the past tense, which image version a debugging session actually ran against on 2026-07-27.
Rewriting it would falsify a historical record, and it is not a pin any build consumes. FR-014a's "no location
may remain" is about pins, not narrative.

Verified locally: `uv run invoke lint` clean across ruff, yamllint, mypy, rumdl, and Vale; 562 unit tests pass;
`uv run invoke docs` builds with `onBrokenLinks: 'throw'`; audit priorities 1-4 report no findings.

