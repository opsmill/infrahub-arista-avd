# Implementation Plan: Repository Standards Compliance

**Branch**: `atg/loud-cooks-find` (feature dir `009-repo-standards-compliance`) | **Date**: 2026-08-11 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-repo-standards-compliance/spec.md`

## Summary

Close the nine findings from the 2026-08-11 `auditing-repo-standards` audit. The work splits into three
kinds of change: **new CI capability** (change detection, a Markdown lint job, a documentation build job, a
prose-style job, two version-bump workflows), **a content pass** to clear the lint backlog so those gates
land enforcing, and **configuration corrections** (project metadata, gitignore, yamllint, action pins,
Infrahub version pin, constitution amendment).

Research changed the shape of two items materially. The Markdown backlog is 80 issues over 31 authored
files — not 257 files — because 226 are vendored agent content or PyAVD-rendered output, and 65 of the 80
auto-fix. Vale is the opposite: unmodified Google + write-good produces 1,135 alerts, so the plan adopts a
project vocabulary and disables the rules that contradict the house voice. Both numbers are measured, not
estimated. See [research.md](./research.md). Implementation took this further than planned - eight rules
ended up disabled rather than three, because several Google rules are written for consumer product docs and
actively misfire on developer reference material. Each disable carries its reasoning in `.vale.ini`, and the
tree finishes at zero alerts; see the Implementation Record in [tasks.md](./tasks.md).

## Technical Context

**Language/Version**: Python 3.11–3.13 (`requires-python = ">=3.11, <3.14"`); Node 22 LTS for the docs site

**Primary Dependencies**: New dev dependency `rumdl` (Markdown lint, PyPI). Vale 3.17.1 as a CI-downloaded
binary (not `uv`-installable). `pnpm` 11 replacing npm for `docs/`. Existing `ruff`, `mypy`, `yamllint`,
`pytest`, `invoke` unchanged.

**Storage**: N/A — no data persistence in scope

**Testing**: Existing `pytest` unit suite unchanged. This feature's own verification is CI behaviour plus
linter exit codes; see [quickstart.md](./quickstart.md)

**Target Platform**: GitHub Actions `ubuntu-latest` runners; local developer machines via `invoke`

**Project Type**: Infrahub solution repository — Python library plus generators/transforms, a Docusaurus
site, and Docker Compose stack tooling. This feature touches only the repository's tooling surface

**Performance Goals**: A documentation-only pull request runs no Python or test jobs, cutting its total
check time by at least half (SC-003). New lint jobs complete within their 5-minute timeouts

**Constraints**: No change to rendered documentation meaning — commands, samples, link targets, and heading
anchors must survive the content pass byte-equivalent in behaviour (FR-005b). All new checks must pass on
the default branch the moment they become enforcing (FR-005a, SC-007). Existing linters and unit tests must
keep passing unchanged (FR-023)

**Scale/Scope**: 8 files carry the Infrahub pin; 31 authored Markdown files carry 80 lint issues; 27 docs
pages carry 194 post-configuration Vale alerts; 4 new CI jobs; 2 new workflows; 1 constitution amendment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.1.1.

| Principle / Gate | Applies? | Status | Notes |
|---|---|---|---|
| I — Schema-Driven Architecture | No | N/A | No schema, node, attribute, or relationship change. No protocol regeneration needed |
| II — Idempotent Operations | No | N/A | No generator or data mutation. `$infrahub-test-generator-idempotence` not triggered |
| III — Type Safety | **Yes** | PASS by design | New `tasks.py` tasks must carry full annotations (`ctx: Context) -> None`) to satisfy `disallow_untyped_defs = true`. No GraphQL or Infrahub node access is added, so no `*_query.py` or protocol work |
| IV — Test-Required Quality | **Yes** | PASS with gates | No generator/transform/library logic changes, so no new unit tests are owed. Three gates do bind: (a) all linters pass before merge — now including the two new ones; (b) **the Infrahub 1.10.6 bump is a dependency change against an Infrahub version, so `$infrahub-run-integration-tests` evidence is required with branch and commit recorded**; (c) no new TODO/FIXME/XXX without tracking context |
| V — Convention-Based Structure | **Yes** | PASS | Documentation edits stay within the `docs/docs/` Docusaurus tree. No pages are added, renamed, or moved, so `docs/sidebars.ts` needs no change. New workflows follow the audit rule's canonical filenames |
| Tech Stack — dependency discipline | **Yes** | PASS with one deviation | `rumdl` enters `pyproject.toml` + `uv.lock` with rationale (R1). **Vale cannot** — it is a Go binary with no PyPI distribution. Recorded in Complexity Tracking |
| Tech Stack — Infrahub target `1.10.1` | **Yes** | Requires amendment | The constitution states `1.10.1` "unless a feature explicitly plans an upgrade". This feature explicitly plans it, so the amendment is in scope (FR-014b, R11) |
| Governance — amendment process | **Yes** | PASS | One amendment, `1.1.1 → 1.2.0`, with Sync Impact Report and dependent-template review (R11) |

**Gate result: PASS.** One deviation justified below; one amendment planned as an explicit deliverable
rather than an incidental edit.

### Post-Phase-1 re-evaluation

Re-checked after the design artifacts were written. No new violations. Two design decisions were made
specifically to stay inside the constitution:

- MD025 is resolved by configuration rather than by deleting redundant H1 headings (R4), because deleting
  them would change heading anchors and break the cross-references Principle V's documentation convention
  depends on.
- `lab/avd/**` is excluded from linting (R2) rather than corrected, because it is PyAVD-rendered output;
  editing it would violate the project-wide rule that generated artifacts are regenerated, never
  hand-edited (Principle I's rationale, applied to rendered output).

## Project Structure

### Documentation (this feature)

```text
specs/009-repo-standards-compliance/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — 11 decisions, measured baselines
├── data-model.md        # Phase 1 output — configuration artifact inventory
├── quickstart.md        # Phase 1 output — validation guide
├── contracts/
│   ├── ci-checks.md     # CI job contract: names, triggers, gating, outcomes
│   └── task-runner.md   # invoke task surface contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
.github/
├── file-filters.yml                    # NEW — python/yaml/markdown/documentation filters
└── workflows/
    ├── ci.yml                          # MODIFIED — files-changed job, gating, 3 new jobs, action pins
    ├── update-infrahub.yml             # NEW — Infrahub instance auto-bump
    └── update-infrahub-sdk.yml         # NEW — infrahub-sdk auto-bump

pyproject.toml                          # MODIFIED — [project] metadata, rumdl dev dep, [tool.rumdl]
uv.lock                                 # MODIFIED — rumdl resolution
tasks.py                                # MODIFIED — lint_markdown, lint_prose, docs tasks; lint_all fan-out
.gitignore                              # MODIFIED — secret patterns, synced Vale styles
.yamllint.yml                           # MODIFIED — truthy.check-keys: false
.vale.ini                               # NEW — Vale configuration
.vale/config/vocabularies/OpsMill/accept.txt          # NEW — 77 project terms
.node-version                           # NEW — Node 22 pin for the docs toolchain
Dockerfile                              # MODIFIED — ARG default 1.8.3 -> 1.10.6
docker-compose.yml                      # MODIFIED — VERSION default -> 1.10.6 (3 services)
docker-compose.override.yml             # MODIFIED — image tag + build arg -> 1.10.6
.specify/memory/constitution.md          # MODIFIED — amendment 1.1.1 -> 1.2.0

docs/
├── package.json                        # MODIFIED — packageManager: pnpm@11
├── pnpm-lock.yaml                      # NEW — replaces package-lock.json
├── package-lock.json                   # DELETED
├── .gitignore                          # MODIFIED — drop npm/yarn log patterns
└── docs/**/*.md                        # MODIFIED — Markdown + prose backlog pass

README.md                               # MODIFIED — pin refs, pnpm commands, lint backlog
AGENTS.md                               # MODIFIED — pnpm commands, new invoke tasks, lint backlog
lab/README.md, schemas/*.md             # MODIFIED — lint backlog only
```

**Structure Decision**: No new source directories. This feature edits repository tooling in place, so the
layout above is the existing tree annotated with the change per file. The one structural addition is
`.vale/` at the root, holding only committed configuration and vocabulary — synced third-party styles are
gitignored (R6).

## Implementation Sequence

Ordered so that no step leaves the default branch red. Each phase is independently mergeable.

**Phase A — Foundations (no gating yet)**
Add `.github/file-filters.yml` and the `files-changed` job; bump action versions; fix `[project]` metadata;
add gitignore secret patterns and `truthy.check-keys: false`. Gate the *existing* jobs on their categories.
Delivers US2 and the FR-017 to FR-020 slice of US5.

**Phase B — Docs toolchain**
Migrate `docs/` to pnpm (delete `package-lock.json`, add `pnpm-lock.yaml`, pin `packageManager`, add
`.node-version`), add the `documentation` CI job and the `docs` invoke task, and update the npm command
references in `README.md`/`AGENTS.md`. Delivers FR-006, FR-007 and SC-001. The docs build doubles as the
link checker (R9).

**Phase C — Markdown lint**
Add `rumdl` dev dep and `[tool.rumdl]` config (with `disable`, `exclude`, and MD025 `front-matter-title = ""`),
run `rumdl fmt`, hand-fix the ~15 residual issues, then add the `markdown-lint` CI job and invoke task
**in the same change** so the gate never sees a dirty baseline. Delivers US1 and FR-005a/FR-005b.

**Phase D — Prose lint**
Add `.vale.ini`, the project vocabulary, and the rule disables; fix the residual alerts; then add the
`validate-documentation-style` CI job. Same ordering discipline as Phase C. Delivers US4.

**Phase E — Version currency**
Reconcile all 8 pin locations on `1.10.6`, amend the constitution to v1.2.0, add both auto-bump workflows,
and record `$infrahub-run-integration-tests` evidence for the upgrade. Delivers US3. Sequenced last because
it is the only phase that needs integration-test validation, and it should not block the CI improvements.

## Complexity Tracking

> Filled because the Constitution Check recorded one deviation.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Vale is installed as a downloaded binary, outside `pyproject.toml`/`uv.lock`, deviating from the constitution's dependency-discipline constraint | Vale is written in Go and publishes no PyPI package, so `uv` cannot manage it. The audit rule prescribes downloading the release tarball, pinned by version, and notes the official GitHub Action is broken | Wrapping Vale in a Python shim package — adds an unmaintained indirection for one binary. Dropping prose linting — abandons FR-015/FR-016 and an audit finding. Using the official Vale Action — the audit rule documents it as broken |
| A third-party style corpus (`Google`, `write-good`) is fetched at CI time rather than committed | `vale sync` completes in ~1s, and vendoring would commit hundreds of third-party rule files that then need manual updating (R6) | Committing the styles — larger diff, ongoing manual maintenance, and no version signal. The trade-off is a network dependency in one CI job, which already needs the network to check out and download Vale |
