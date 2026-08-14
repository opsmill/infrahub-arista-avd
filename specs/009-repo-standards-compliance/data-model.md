# Phase 1 Data Model: Repository Standards Compliance

**Feature**: [spec.md](./spec.md) | **Research**: [research.md](./research.md) | **Date**: 2026-08-11

This feature persists no runtime data and defines no Infrahub nodes. Its "entities" are configuration
artifacts, so this document inventories each one: where it lives, the fields that matter, the validation
rules drawn from the requirements, and how it relates to the others. Field values that research fixed are
given concretely; values left open are marked as chosen at implementation time.

## Entity relationship overview

```text
file-filters.yml ──(categories)──> ci.yml files-changed job ──(outputs)──> every gated job
                                                                   │
pyproject.toml ──[tool.rumdl]──> markdown-lint job ────────────────┤
             └──[project]/[dependency-groups] ──> python-lint, unit-tests
                                                                   │
.vale.ini + accept.txt ──> validate-documentation-style job ───────┤
                                                                   │
docs/package.json + pnpm-lock.yaml + .node-version ──> documentation job
                                                                   │
Dockerfile + docker-compose*.yml ──(Infrahub pin)──> integration-tests-full job
             └──────────────> update-infrahub.yml (keeps them in step)
pyproject.toml + uv.lock ────────> update-infrahub-sdk.yml
constitution.md ──(states)──> the Infrahub pin, dev deps, and the linter set
tasks.py ──(mirrors locally)──> every CI check
```

## 1. Change-detection filter set

**File**: `.github/file-filters.yml` (new) — satisfies FR-008

| Field | Value | Rule |
|---|---|---|
| `documentation` | `docs/**/*` | Anchor + `documentation_all` alias |
| `python` | `**/*.py`, `pyproject.toml`, `uv.lock` | Anchor + `python_all` alias |
| `yaml` | `**/*.yml`, `**/*.yaml`, `!.github/workflows/**` | Anchor + `yaml_all` alias |
| `markdown` | `**/*.md`, `**/*.mdx` | Anchor + `markdown_all` alias |

**Validation rules**:

- Every category MUST expose a `<name>_all` alias, because the `files-changed` job reads
  `steps.changes.outputs.<name>_all`.
- The four categories are the minimum FR-008 requires; more may be added but none removed.
- `markdown` deliberately overlaps `documentation`: a change under `docs/` triggers both the docs build and
  the Markdown lint, which is correct.

**Relationships**: consumed only by the `files-changed` job; every other job depends on that job's outputs.

## 2. CI workflow structure

**File**: `.github/workflows/ci.yml` (modified) — satisfies FR-001, FR-002, FR-009, FR-010, FR-015, FR-020,
FR-024. Full job contract in [contracts/ci-checks.md](./contracts/ci-checks.md).

| Field | Current | Target |
|---|---|---|
| `actions/checkout` | `v4` | `v7` (R7) |
| `astral-sh/setup-uv` | `v6` | `v9` (R7) |
| `actions/setup-node` | absent | `v7` |
| `pnpm/action-setup` | absent | `v6` |
| `opsmill/paths-filter` | absent | `v3.0.2` |
| Jobs | `lint`, `unit-tests`, `integration-tests`, `integration-tests-full` | plus `files-changed`, `markdown-lint`, `documentation`, `validate-documentation-style` |

**Validation rules**:

- Every job MUST declare `timeout-minutes` (FR-024). New lint/docs jobs use 5; `files-changed` uses 5.
- `permissions: contents: read` stays at workflow level; no job may widen it without stating why (FR-024).
- Existing `lint` and `unit-tests` jobs keep their current commands verbatim (FR-023) and gain only an
  `if:` condition and `needs: ["files-changed"]`.
- The two integration jobs keep `if: github.event_name == 'workflow_dispatch'` — out of scope per the spec.
- `env: UV_FROZEN: "true"` is preserved.

## 3. Project metadata and Python tool configuration

**File**: `pyproject.toml` (modified) — satisfies FR-002, FR-003, FR-017, FR-022

### 3a. `[project]` metadata (FR-017)

| Field | Current | Target | Rule |
|---|---|---|---|
| `authors` | `[]` | `[{name = "OpsMill", email = "info@opsmill.com"}]` | MUST be non-empty |
| `description` | `"Infrahub Repository"` | A sentence naming this project and what it produces | MUST identify this project, not a generic repository |
| `name`, `version`, `readme`, `requires-python` | already valid | unchanged | — |

### 3b. `[tool.rumdl]` (FR-002, FR-003, FR-004; shape verified in R1/R2/R4)

| Field | Value | Rule |
|---|---|---|
| `disable` | `["MD013", "MD033", "MD041"]` | MUST use the list form — `MD013 = false` is silently ignored (R1) |
| `exclude` | `.agents`, `.claude`, `.specify`, `.superset`, `specs`, `lab/avd`, `CLAUDE.md`, `node_modules`, `.venv` | Vendored, generated, and symlinked content (R2) |
| `[MD025] front-matter-title` | `""` | Decouples Docusaurus frontmatter `title:` from H1 counting (R4) |

### 3c. `[dependency-groups] dev` (FR-022)

| Field | Change | Rule |
|---|---|---|
| `rumdl` | added | MUST land with a `uv.lock` update in the same change |

**Validation rules**: `[tool.ruff]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` are not modified —
FR-023 requires existing linters to behave identically.

## 4. Prose style configuration

**Files**: `.vale.ini` (new), `.vale/config/vocabularies/OpsMill/accept.txt` (new) — satisfies FR-015, FR-016

| Field | Value | Rule |
|---|---|---|
| `StylesPath` | `.vale` | Per audit rule |
| `MinAlertLevel` | `warning` | MUST NOT be raised to `error` to hide findings (R5) |
| `Packages` | `Google, write-good` | Synced in CI, not vendored (R6) |
| `[*.md]` / `[*.mdx]` `BasedOnStyles` | `Vale, Google, write-good` | Both extensions covered |
| `Vocab` | `OpsMill` | Required, or the vocabulary file is present but ignored |
| `Google.EmDash` | `NO` | Contradicts house voice; 241 alerts (R5) |
| `write-good.Passive` | `NO` | Unavoidable in reference prose; 166 alerts (R5) |
| `write-good.TooWordy` | `NO` | Subjective; 38 alerts (R5) |
| `Google.Colons` | `NO` | Wants schema kind names lowercased (`NetworkFabric`, `DcimDevice`) |
| `Google.WordList` | `NO` | Wants `CLI` to become "command-line tool" |
| `Google.WordListCase` | `NO` | Wants `touch` (the Unix command) to become "tap" |
| `Google.HeadingPunctuation` | `NO` | Reads the ordinal in `## 1. Install dependencies` as a trailing period |
| `Vale.Terms` | `NO` | Cannot tell a sentence-initial capital from a casing error |
| `TokenIgnores` | `(\{#[^}]+\})` | Explicit heading anchors are identifiers, not prose. Must sit in the syntax section |
| `accept.txt` | 96 project terms | Terminology goes here, never reworded away (FR-016) |

**Validation rules**:

- The vocabulary MUST hold genuine project/vendor terms only — it is not a suppression list for
  misspellings.
- Any disabled rule MUST carry a stated reason in `.vale.ini`, so the config does not quietly erode.
- The check MUST report zero findings on the default branch once enforcing (FR-016, SC-002a).

## 5. Documentation toolchain

**Files**: `docs/package.json` (modified), `docs/pnpm-lock.yaml` (new), `docs/package-lock.json` (deleted),
`.node-version` (new), `docs/.gitignore` (modified) — satisfies FR-006, FR-007

| Field | Value | Rule |
|---|---|---|
| `packageManager` | `pnpm@11.x` (exact version at implementation time) | Read by `pnpm/action-setup@v6`, so the pin lives in the repo |
| `.node-version` | Node 22 LTS | Read by `actions/setup-node@v7` via `node-version-file` |
| Lockfile | exactly one, `pnpm-lock.yaml` | `package-lock.json` MUST be deleted in the same change (FR-007) |
| `docs/.gitignore` | drop `npm-debug.log*`, `yarn-*.log*` | Residue of the removed toolchains |

**Validation rules**: no file in the repository may invoke the `npm` binary after this change, excluding
vendored agent content under `.agents/`, `.claude/`, and `.specify/` (FR-007, and the spec's out-of-scope
note). `docs/docusaurus.config.ts` is not modified — its existing `onBrokenLinks: 'throw'` is what makes the
build a link gate (R9).

## 6. Infrahub version pin

**Files**: `Dockerfile`, `docker-compose.yml`, `docker-compose.override.yml`, `.github/workflows/ci.yml`,
`README.md`, `docs/docs/quick-start.md`, `.specify/memory/constitution.md` — satisfies FR-014, FR-014a

| Location | Current | Target |
|---|---|---|
| `Dockerfile:1` `ARG INFRAHUB_BASE_VERSION` | `1.8.3` | `1.10.6` |
| `docker-compose.yml:246,279,325` `${VERSION:-…}` | `1.10.1` | `1.10.6` |
| `docker-compose.override.yml:3,22` | `1.10.1` | `1.10.6` |
| `ci.yml:116,122` build arg / tag / `INFRAHUB_TESTING_IMAGE_VER` | `1.10.3` | `1.10.6` |
| `README.md:39,90` | `1.10.1` | `1.10.6` |
| `docs/docs/quick-start.md:35` | `1.10.1` | `1.10.6` |
| `constitution.md:168` | `1.10.1` | `1.10.6` |

**Validation rules**:

- After the change, `grep -rn '1\.10\.[0-5]\|1\.8\.3'` MUST return no target-version references (SC-005).
- The `Dockerfile` ARG default and the compose `${VERSION:-…}` default MUST match, or an argument-less build
  produces a mismatched image — the defect that put the Dockerfile two minor versions behind (R8).
- `INFRAHUB_TESTING_IMAGE_VER` MUST match the tag the preceding `docker build` step produces.

## 7. Version-bump workflows

**Files**: `.github/workflows/update-infrahub.yml`, `.github/workflows/update-infrahub-sdk.yml` (new) —
satisfies FR-011, FR-012, FR-013

| Field | Infrahub workflow | SDK workflow |
|---|---|---|
| `repository_dispatch` type | `trigger-infrahub-update` | `trigger-infrahub-sdk-python-update` |
| `workflow_dispatch` inputs | `version` (required), `run` (bool) | same |
| Concurrency group version | `github.event_name == 'repository_dispatch' && github.event.client_payload.version \|\| github.event.inputs.version` | same ternary |
| Update steps | compose `sed`, `Dockerfile` ARG, `uv add --group dev infrahub-testcontainers==`, docs/README refs | `uv add "infrahub-sdk[all]==…"` |
| Committed files | `pyproject.toml`, `uv.lock`, `docker-compose.yml`, `docker-compose.override.yml`, `Dockerfile` | `pyproject.toml`, `uv.lock` |
| Identity / secret | `opsmill-bot` / `GH_UPDATE_PACKAGE_OTTO` | same |
| Base branch | `main` | `main` |

**Validation rules**:

- The concurrency group MUST use the ternary, or manual runs collapse onto one group key (audit rule).
- Both MUST skip creation when a pull request for that head branch is already open (FR-013).
- The Infrahub workflow MUST cover **every** location in entity 6, including the `Dockerfile` ARG — a bump
  that misses one recreates the drift this feature is fixing.
- Neither may use Poetry or commit `poetry.lock`.

## 8. Task runner surface

**File**: `tasks.py` (modified) — satisfies FR-005, FR-006. Full contract in
[contracts/task-runner.md](./contracts/task-runner.md).

| Task | Status | Behaviour |
|---|---|---|
| `lint-markdown` | new | `rumdl check` over the authored set |
| `lint-prose` | new | Vale over `docs/docs`; requires the Vale binary on PATH |
| `docs` | new | pnpm install + Docusaurus build |
| `lint` | modified | fan-out gains `lint_markdown` and `lint_prose` |
| `format` | modified | gains `rumdl fmt` alongside the existing ruff commands |
| all others | unchanged | — |

**Validation rules**: every new task MUST be fully type-annotated (`ctx: Context) -> None`) to satisfy
`disallow_untyped_defs = true` (Constitution III). Tasks MUST run the same commands CI runs, so local and
CI results agree (SC-008).

## 9. Ignore rules

**File**: `.gitignore` (modified) — satisfies FR-018

| Pattern | Purpose |
|---|---|
| `*.pem`, `*.key`, `*.p12`, `credentials.json`, `secrets.yaml` | Secret-bearing filenames (FR-018) |
| `.vale/Google/`, `.vale/write-good/` | Synced third-party styles, not vendored (R6) |

**Validation rules**: the secret patterns MUST NOT be so broad that they hide legitimate tracked files —
verify with `git status --ignored` that no currently-tracked file becomes ignored.

## 10. YAML lint configuration

**File**: `.yamllint.yml` (modified) — satisfies FR-019

| Field | Current | Target |
|---|---|---|
| `rules.truthy.check-keys` | absent | `false` |
| everything else | unchanged | unchanged |

**Validation rules**: `line-length.max: 140` and the existing `ignore` block are deliberate local choices
and are preserved. The `truthy` fix must not depend on `.github` remaining in `ignore` (FR-019).

## 11. Governance record

**File**: `.specify/memory/constitution.md` (modified) — satisfies FR-014b

| Field | Change |
|---|---|
| Version | `1.1.1` → `1.2.0` (MINOR — Principle IV's linter set materially expands; R11) |
| Sync Impact Report | New header block, following the file's existing convention |
| Technology Stack — Infrahub image | `1.10.1` → `1.10.6` |
| Technology Stack — dev dependencies | add `rumdl` |
| Technology Stack — linting | add Markdown (`rumdl`) and prose (Vale) |
| Technology Stack — package manager | state `pnpm` for the docs site alongside `uv` for Python |
| Principle IV — linter gate | `ruff`, `mypy`, `yamllint` → plus `rumdl` and Vale |

**Validation rules**: the amendment MUST list dependent templates reviewed, per the file's own governance
section, and MUST be part of this feature rather than a follow-up (FR-014b).

## Content backlog (not a configuration entity, but a tracked deliverable)

| Scope | Volume | Method |
|---|---|---|
| Markdown, auto-fixable | 65 issues | `rumdl fmt` |
| Markdown, manual | ~15 issues (MD036 pseudo-headings, MD040 fence languages) | Hand edit |
| Markdown, resolved by config | 26 issues (MD025) | R4 — no file edits |
| Prose, vocabulary | 490 alerts → 77 terms | `accept.txt` |
| Prose, resolved by config | 445 alerts (EmDash, Passive, TooWordy) | R5 — no file edits |
| Prose, manual | ~60 edits (heading case, Latin abbreviations, tense, quotes) | Hand edit |

**Validation rule spanning all of it (FR-005b)**: after the pass, every documented command, code sample,
configuration snippet, link target, and heading anchor MUST behave identically. The docs build with
`onBrokenLinks: 'throw'` is the automated half of that check.

**Apparent conflict, resolved**: FR-016 wants a clean Vale baseline, but 84 of the residual alerts are
`Google.Headings` (sentence-case enforcement) and FR-005b forbids changing heading anchors. These do not
actually collide, because Docusaurus slugs are lowercased — `## Getting Started` and `## Getting started`
both yield `#getting-started`, so case-only edits are anchor-preserving. The rule that follows from this:

- Case-only heading edits are permitted freely.
- Any heading edit that changes, adds, or removes *words* MUST either be skipped or carry an explicit
  `{#existing-anchor}` to hold the old slug.
- `onBrokenLinks: 'throw'` catches broken *internal* links, but not external inbound links to an anchor, so
  word-level heading changes need deliberate review rather than reliance on the build.
