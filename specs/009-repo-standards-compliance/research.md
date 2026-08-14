# Phase 0 Research: Repository Standards Compliance

**Feature**: [spec.md](./spec.md) | **Date**: 2026-08-11

All findings below were verified by running the tools against this repository, not inferred from the
audit rule text. Two of the audit rule's own instructions turned out to be wrong; both are recorded.

## R1 — Markdown linter: rumdl, configured in `pyproject.toml`

**Decision**: Adopt `rumdl` as a `uv` dev dependency, configured under `[tool.rumdl]` in `pyproject.toml`,
invoked as `rumdl check <paths>`.

**Rationale**: `rumdl` is on PyPI (`rumdl 0.2.53`, upstream `rvben/rumdl`), so it installs through the
project's existing `uv` dependency management with no new toolchain — unlike Node-based `markdownlint`.
Verified that `[tool.rumdl]` in `pyproject.toml` is read and honoured, which satisfies the audit rule's
"config must live in pyproject.toml" requirement.

**Corrections to the audit rule** (`02-linting/markdown-linting-markdownlint.md`):

1. **The documented disable syntax does not work.** The rule shows `MD013 = false`. Verified against a
   file containing MD013, MD033, and MD041 violations: with `MD013 = false` style config, all three rules
   still fired. The working form is a global list: `disable = ["MD013", "MD033", "MD041"]`. Confirmed by
   the CLI's own validator: *"Unknown key: disable. Must be in the form global.key, MDxxx.key, or MDxxx"*.
2. **The documented invocation does not work.** The rule shows `rumdl "**/*.md" "**/*.mdx"`. `rumdl`
   requires a subcommand: `rumdl check <paths>`. There is also `rumdl fmt` for auto-fixing.
3. The rule's reference link (`github.com/squalrus/rumdl`) points at an unrelated project.

**Alternatives considered**: Node `markdownlint-cli2` — rejected, adds a second Node toolchain outside
`docs/` for a check that must also run locally. `rumdl import` can convert markdownlint config if the repo
ever inherits one.

## R2 — Markdown lint scope: the authored set

**Decision**: Lint `README.md`, `AGENTS.md`, `docs/`, `schemas/*.md`, and `lab/README.md`. Exclude
`.agents/`, `.claude/`, `.specify/`, `.superset/`, `specs/`, `lab/avd/**`, and `CLAUDE.md`.

**Rationale**: Of 257 tracked Markdown/MDX files, only ~31 are authored by this project:

| Path | Files | Status |
|---|---|---|
| `.agents/`, `.claude/`, `.specify/` | 152 | Vendored third-party skill/command content — excluded per FR-004 |
| `specs/` | 58 | Spec-kit process artifacts, high churn, not reader-facing — excluded |
| `lab/avd/**` | 14 | **PyAVD-rendered output** (device docs, fabric docs, ANTA report) — generated, excluded |
| `docs/` | 27 | Authored |
| `README.md`, `AGENTS.md`, `schemas/`, `lab/README.md` | 4 | Authored |

`lab/avd/**` is the significant discovery: these are rendered artifacts, exactly parallel to
`lab/avd/intended`, which `.yamllint.yml:14` already ignores for the same reason. Including them would
mean "fixing" generator output that regenerates on every deploy. `CLAUDE.md` is excluded because it is a
symlink to `AGENTS.md` and would otherwise be linted twice.

**Alternatives considered**: Linting `specs/` too — rejected: spec-kit writes these, so violations return
with every `/speckit-*` run and the check would fight the tooling that generates it.

## R3 — Markdown backlog is small and mostly mechanical

**Decision**: Clear the backlog with `rumdl fmt` plus a targeted manual pass; no baseline suppression.

**Measured** against the R2 authored set with MD013/MD033/MD041 disabled: **80 issues across 26 of 31
files, 65 of them auto-fixable** by `rumdl fmt`.

| Rule | Count | Disposition |
|---|---|---|
| MD025 multiple H1 | 26 | **Config, not a defect** — see R4 |
| MD031 blank line around fences | 16 | `rumdl fmt` |
| MD036 emphasis used as heading | 15 | Manual — `docs/docs/troubleshooting.md` uses bold pseudo-headings (`**Symptoms**`, `**Diagnose**`, `**Fix**`). Convert to real headings; improves in-page navigation |
| MD040 code fence missing language | 11 | Manual (one word each) |
| MD032 list spacing | 10 | `rumdl fmt` |
| MD029 ordered list numbering | 2 | `rumdl fmt` |

After R4's config change, roughly **15 manual edits** remain. This is far smaller than the "257 files"
the spec's edge case feared, because 226 of those files are vendored or generated.

## R4 — MD025 is a Docusaurus frontmatter interaction, not a violation

**Decision**: Set `front-matter-title = ""` for MD025 rather than editing 26 pages.

**Rationale**: `rumdl`'s MD025 defaults to `front-matter-title = "title"`, so it counts a page's
frontmatter `title:` as a top-level heading. Every Docusaurus page here has both `title: X` in frontmatter
and a `# X` heading — a normal Docusaurus pattern. The available auto-fix would demote or delete those H1s,
changing rendered output and heading anchors, which **FR-005b forbids**. Clearing `front-matter-title`
removes the false coupling and the 26 alerts with it.

**Alternatives considered**: Disabling MD025 entirely — rejected, it would also stop catching genuine
duplicate H1s. Deleting the redundant H1s — rejected, breaks anchors and cross-references.

## R5 — Vale: adopt Google + write-good, but tune before enforcing

**Decision**: Adopt Vale 3.17.1 with `Packages = Google, write-good`, then (a) load project terminology
into `.vale/config/vocabularies/OpsMill/accept.txt`, and (b) disable the three rules that contradict the house voice:
`Google.EmDash`, `write-good.Passive`, `write-good.TooWordy`.

**Rationale**: This is the finding that most changes the shape of the work. Running Vale unmodified over
the 27 authored docs pages produces **1,135 alerts (763 error, 372 warning)** — an order of magnitude more
than rumdl, and mostly not defects:

| Check | Count | Why it fires | Disposition |
|---|---|---|---|
| `Vale.Spelling` | 490 | Networking and vendor jargon: EVPN, VXLAN, PyAVD, Infrahub, hostvars, ASNs, SVIs, VNIs… | **77 unique terms** → `accept.txt`. FR-016 already mandates this over rewording |
| `Google.EmDash` | 241 | Google style forbids spaced em dashes; this repo's docs use them throughout as a voice choice | Disable |
| `write-good.Passive` | 166 | Flags all passive voice; unavoidable and often correct in technical reference prose | Disable |
| `write-good.TooWordy` | 38 | Subjective phrase blacklist | Disable |
| `Google.Headings` | 84 | Sentence-case heading enforcement | Fix |
| `Google.Colons`, `Latin`, `WordList*`, `Will`, `Quotes`, others | ~110 | Genuine, mechanical style fixes | Fix |

After the vocabulary and the three disables, **194 alerts remain** — real, bounded prose work
(84 of them heading capitalisation). That is what FR-016's clean baseline costs.

**Trade-off stated plainly**: enforcing Google + write-good verbatim would mean ~1,135 edits and would
rewrite the docs' voice — 241 em-dash removals alone. The recommendation keeps the enforcing gate the
user asked for while confining it to findings the team would actually accept in review.

**Alternatives considered**: `MinAlertLevel = error` to hide the 372 warnings — rejected, it silently
drops real findings and the ratio is arbitrary. Dropping `write-good` entirely — rejected, its
non-disabled rules are useful; three targeted disables are more precise.

## R6 — Vale styles: sync in CI, do not vendor

**Decision**: Commit `.vale.ini` and `.vale/config/vocabularies/OpsMill/accept.txt`; run `vale sync` in CI before
linting; gitignore the synced `.vale/Google/` and `.vale/write-good/` trees.

**Rationale**: Verified `vale sync` fetches both packages in about one second, so it is not a meaningful
CI cost. Vendoring them would commit hundreds of third-party rule files that then need manual updating.
The audit rule's example CI job downloads only the Vale binary and implies committed styles; syncing is
the smaller, more maintainable deviation.

**Note**: Vale is a Go binary and is **not** installable through `uv`, so it cannot become a dev
dependency. CI downloads the release tarball, as the audit rule prescribes. This is a documented deviation
from the constitution's "no dependencies outside `pyproject.toml`" constraint — see Complexity Tracking in
[plan.md](./plan.md).

## R7 — CI action versions: the audit rule's own pins are stale

**Decision**: Use `actions/checkout@v7`, `astral-sh/setup-uv@v9`, `actions/setup-node@v7`,
`pnpm/action-setup@v6`, `opsmill/paths-filter@v3.0.2`.

**Rationale**: The audit rule specifies `checkout@v6` and `setup-uv@v7` as the target, but current
releases are `checkout v7.0.1` and `setup-uv v9.0.0` — the rule text lags upstream. Adopting current
majors satisfies the rule's floor (FR-020's intent is "not lagging") without re-pinning to something
already outdated. `opsmill/paths-filter` has exactly one release, `v3.0.2`, matching the rule.

**Alternatives considered**: Literal compliance with `v6`/`v7` — rejected, it would leave the repo behind
on the very axis the rule exists to police, and a second bump would be needed immediately.

## R8 — Infrahub pin: five locations, one of them at 1.8.3

**Decision**: Converge every location on `1.10.6`, with `docker-compose.yml`'s `${VERSION:-…}` default and
the `Dockerfile` `ARG` as the two values that must be edited in lockstep.

**Rationale**: The audit found two divergent pins; a full sweep finds **four distinct versions across
eight files**, including a `Dockerfile` default two minor versions behind that nothing else references:

| Location | Current | Notes |
|---|---|---|
| `Dockerfile:1` | **1.8.3** | `ARG INFRAHUB_BASE_VERSION` default — not previously reported |
| `docker-compose.yml:246,279,325` | 1.10.1 | `${VERSION:-1.10.1}` on three services |
| `docker-compose.override.yml:3,22` | 1.10.1 | Solution image tag + build arg |
| `.github/workflows/ci.yml:116,122` | 1.10.3 | Build arg, image tag, and `INFRAHUB_TESTING_IMAGE_VER` |
| `README.md:39,90` | 1.10.1 | Documented `export` and prose |
| `docs/docs/quick-start.md:35` | 1.10.1 | Documented `export` |
| `.specify/memory/constitution.md:168` | 1.10.1 | Stated project target |

Verified upstream that `infrahub-v1.10.6` is the newest stable 1.10.x release; `1.11.0a0/b0/b1` are
pre-releases and excluded per the spec's assumptions. The `Dockerfile` default at `1.8.3` means a build
that omits the build arg silently produces a two-minor-version-old image — worth fixing regardless.

**Alternatives considered**: A single `VERSION` file as the one source of truth — attractive, and the
auto-bump rule supports it, but it would change how `docker-compose` and `tasks.py` resolve the version.
Deferred: this feature reconciles the values and the bump workflow keeps them in step. Recorded as a
follow-up candidate.

## R9 — Docs toolchain: pnpm, Node, and the build is already a link checker

**Decision**: Migrate `docs/` to pnpm 11 with `packageManager` pinned in `docs/package.json`, add a
`.node-version` file (pinned to 22, matching the development machine), and run the existing
Docusaurus build as the CI docs gate.

**Rationale**: `docs/docusaurus.config.ts:19,76` already sets `onBrokenLinks: 'throw'` and
`onBrokenMarkdownLinks: 'throw'`, so `docusaurus build` fails on any unresolvable internal link. The docs
job therefore delivers link checking for free — no separate link checker needed, and SC-001 is satisfied
by the build alone. `pnpm/action-setup@v6` reads the version from `packageManager`, and
`actions/setup-node@v7` reads `node-version-file`, so both pins live in the repo rather than the workflow.
Current pnpm is 11.21.0 and current Node LTS is 24.x.

**Alternatives considered**: Keeping npm — rejected, FR-007 and the audit rule require one package manager
and it must be pnpm. Adding a standalone link-checker job — rejected as redundant given `onBrokenLinks`.

## R10 — Skipped checks cannot block merges here

**Decision**: Gate jobs with `if: needs.files-changed.outputs.<category> == 'true'` and accept the
resulting "skipped" conclusion without adding status-check shims.

**Rationale**: The classic "skipped required check blocks the PR forever" problem only arises when branch
protection lists required status checks. This repository has **no** branch protection at all — verified
during the audit: both the classic protection and rulesets endpoints return
`403 Upgrade to GitHub Pro or make this repository public`. With no required checks configured, a skipped
job cannot block a merge, so FR-009 and FR-010 are satisfied by plain `if:` conditions.

**Consequence to carry forward**: if the plan or visibility changes and branch protection is later
enabled, whoever configures required checks must either list only always-running jobs or add aggregating
gate jobs. Noted in [quickstart.md](./quickstart.md) so it is not rediscovered painfully.

**Alternatives considered**: An always-running aggregate "CI passed" gate job — sound practice, but it
solves a problem this repo cannot currently have; adding it now is unjustified complexity.

## R11 — Constitution amendment scope

**Decision**: One amendment to `.specify/memory/constitution.md`, version `1.1.1 → 1.2.0`.

**Rationale**: Three separate statements in the constitution stop being true after this feature, so they
must change together:

1. Technology Stack — Infrahub target `1.10.1` → `1.10.6` (FR-014b).
2. Technology Stack — the enumerated dev dependency list gains `rumdl`; the linting line gains Markdown
   and prose linting; a JavaScript package manager (pnpm) is now stated.
3. Principle IV — "All linters (`ruff`, `mypy`, `yamllint`) MUST pass before merge" becomes the expanded
   set including `rumdl` and Vale.

Item 3 materially expands the quality-gate guidance, which the constitution's own governance rules make a
**MINOR** bump rather than a patch. The amendment also requires a Sync Impact Report header, per the
existing file's convention.

## Summary of unresolved items

None. No `NEEDS CLARIFICATION` markers remain from the spec, and no research question was left open. Two
items are explicitly deferred as follow-ups rather than unknowns: a single-`VERSION`-file source of truth
(R8) and required-status-check configuration if branch protection becomes available (R10).
