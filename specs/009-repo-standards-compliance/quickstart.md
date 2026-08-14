# Quickstart: Validating Repository Standards Compliance

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-08-11

How to prove this feature works, phase by phase. Each section maps to a success criterion and can be run
independently, so a partially-merged feature can still be validated. Entity details live in
[data-model.md](./data-model.md); job and task definitions live in [contracts/](./contracts/).

## Prerequisites

```bash
uv sync --all-packages          # includes rumdl once Phase C lands
corepack enable                 # pnpm, once Phase B lands
```

Vale is not managed by `uv` (R6). To validate prose locally, install the pinned version:

```bash
curl -sL "https://github.com/errata-ai/vale/releases/download/v3.17.1/vale_3.17.1_Linux_64-bit.tar.gz" \
  -o /tmp/vale.tar.gz && tar -xzf /tmp/vale.tar.gz -C ~/.local/bin vale
vale sync                       # fetches the Google and write-good packages (~1s)
```

## Phase A — Change-scoped CI (SC-003, FR-008 to FR-010)

Nothing to run locally; this is validated on pull requests. Open three throwaway pull requests:

| Change | Expect to run | Expect to skip |
|---|---|---|
| One word in `docs/docs/home.md` | `files-changed`, `markdown-lint`, `documentation`, `validate-documentation-style` | `lint`, `unit-tests` |
| A comment in `src/solution_arista_avd/avd.py` | `files-changed`, `lint`, `unit-tests` | docs and markdown jobs |
| A key in `objects/01_*.yml` | `files-changed`, `lint` (yamllint path) | docs, markdown, unit-tests |

Pass criteria:

- Skipped jobs report `skipped`, and each pull request is still mergeable (FR-010).
- The docs-only pull request's total check time is at most half the same change's time before this feature
  (SC-003). Compare against a pre-feature run on the same branch.

Also confirm action pins:

```bash
grep -nE 'uses: (actions/checkout|astral-sh/setup-uv|actions/setup-node|pnpm/action-setup|opsmill/paths-filter)' \
  .github/workflows/ci.yml
# expect checkout@v7, setup-uv@v9, setup-node@v7, action-setup@v6, paths-filter@v3.0.2
```

## Phase B — Documentation build gate (SC-001, FR-001, FR-006, FR-007)

```bash
uv run invoke docs              # must build cleanly
```

Then prove the gate bites. Introduce a broken internal link and confirm the build fails — the site already
sets `onBrokenLinks: 'throw'` (R9), so this is a genuine link check:

```bash
printf '\n[broken](/no-such-page)\n' >> docs/docs/home.md
uv run invoke docs              # MUST fail, naming home.md
git checkout docs/docs/home.md
```

Single-package-manager checks:

```bash
test ! -e docs/package-lock.json && echo "npm lockfile removed"
test -e docs/pnpm-lock.yaml && echo "pnpm lockfile present"
grep -c packageManager docs/package.json          # expect 1
grep -rn --include='*.md' --include='*.yml' --include='*.sh' -E '\bnpm (install|ci|run|test)\b' \
  . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.agents --exclude-dir=.claude \
  --exclude-dir=.specify --exclude-dir=specs
# expect no hits (vendored agent content is excluded per FR-007)
```

## Phase C — Markdown lint (SC-002, SC-002a, FR-002 to FR-005b)

```bash
uv run invoke lint-markdown     # MUST report zero issues on a clean tree
```

Prove the gate bites, and that config beats false positives:

```bash
printf '\ntext\n```\nno language\n```\n' >> docs/docs/home.md
uv run invoke lint-markdown     # MUST fail with MD040 on home.md
git checkout docs/docs/home.md
```

Verify the two research-driven config decisions actually took effect:

```bash
# MD013/MD033/MD041 must be off via the list form, not `MD013 = false` (R1)
uv run rumdl config get global.disable          # expect MD013, MD033, MD041

# MD025 must not fire on Docusaurus frontmatter + H1 (R4)
uv run rumdl config get MD025.front-matter-title   # expect empty string
uv run rumdl check docs/docs/developer-guide/generators.md   # expect no MD025
```

Verify exclusions hold — generated and vendored content must not be linted (FR-004, R2):

```bash
uv run rumdl check lab/avd/documentation/devices/ih-dc1-leaf2a.md 2>&1 | tail -2
# expect the file to be excluded, not reported: it is PyAVD-rendered output
```

Meaning-preservation spot check (FR-005b) after the backlog pass:

```bash
git diff --stat main -- docs/ README.md AGENTS.md   # expect prose-only churn
git diff main -- docs/ | grep -E '^[+-].*```' | sort | uniq -c
# fence lines should be balanced: no code sample gained or lost content
uv run invoke docs                                  # links and anchors still resolve
```

## Phase D — Prose style (FR-015, FR-016)

```bash
uv run invoke lint-prose        # MUST report zero findings on a clean tree
```

Confirm every disable is deliberate and documented, not accidental suppression (R5):

```bash
grep -c ' = NO$' .vale.ini                          # expect 8 disabled rules
grep -B3 ' = NO$' .vale.ini                         # every one must carry a comment explaining why
grep -c 'MinAlertLevel = warning' .vale.ini         # expect 1 — must not be raised to error
grep -c 'Vocab = OpsMill' .vale.ini                 # expect 1 — without it the vocabulary is ignored
grep -c '^[A-Za-z]' .vale/config/vocabularies/OpsMill/accept.txt   # expect ~96 project terms
```

Prove the gate bites:

```bash
printf '\nThe fabric can be utilized to leverage synergies.\n' >> docs/docs/home.md
uv run invoke lint-prose        # MUST report findings on home.md
git checkout docs/docs/home.md
```

Heading-anchor safety (the FR-005b / FR-016 interaction resolved in data-model.md):

```bash
git diff main -- docs/ | grep -E '^[+-]#{1,6} '
# review every hit: case-only changes are safe (Docusaurus lowercases slugs);
# any change to heading WORDS must carry an explicit {#old-anchor}
```

## Phase E — Version currency (SC-005, SC-006, FR-011 to FR-014c)

Confirm the pin converged across all eight locations (R8):

```bash
grep -rn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv \
  --exclude=uv.lock --exclude=package-lock.json --exclude-dir=specs \
  -E '1\.(8|9|10)\.[0-9]+' . | grep -vE 'objects/|CHANGELOG'
# every Infrahub version reference must read 1.10.6 — including Dockerfile:1,
# which was at 1.8.3 before this feature
```

Confirm the Dockerfile default and the compose default agree, so an argument-less build is correct:

```bash
grep -n 'INFRAHUB_BASE_VERSION' Dockerfile docker-compose.override.yml
grep -n 'VERSION:-' docker-compose.yml
docker build -t infrahub-avd-pin-check .          # no --build-arg: must produce a 1.10.6 base
```

Exercise each bump workflow manually (FR-013):

```bash
gh workflow run update-infrahub.yml -f version=1.10.6 -f run=false
gh workflow run update-infrahub-sdk.yml -f version=1.22.0 -f run=false
gh pr list --state open        # expect one PR each, and no duplicate on a second run
```

Then confirm the concurrency ternary is present — the audit rule's most common defect:

```bash
grep -n "repository_dispatch' && github.event.client_payload.version || github.event.inputs.version" \
  .github/workflows/update-infrahub*.yml   # expect hits in both files
```

### Required validation for this phase

The `1.10.6` upgrade is a dependency change against an Infrahub version, so Constitution Principle IV binds:
run `$infrahub-run-integration-tests` and record the tested branch and commit on the pull request (FR-014c).
Do not merge Phase E on unit tests alone.

## Phase F — Governance and hygiene (SC-004, FR-017 to FR-021, FR-014b)

```bash
# Metadata
grep -A2 '^authors' pyproject.toml            # non-empty OpsMill entry
grep '^description' pyproject.toml            # names this project specifically

# Secret patterns actually ignore, and hide nothing tracked
touch test.pem test.key credentials.json
git status --porcelain | grep -E 'test\.(pem|key)|credentials\.json' && echo "LEAK" || echo "ignored"
rm -f test.pem test.key credentials.json
git status --ignored --porcelain | grep -f <(git ls-files) && echo "TRACKED FILE NOW IGNORED" || echo "clean"

# yamllint truthy
grep -A1 'truthy' .yamllint.yml               # expect check-keys: false
uv run invoke lint-yaml

# Constitution amendment
grep -nE 'Version.*1\.2\.0|1\.10\.6|rumdl' .specify/memory/constitution.md
```

## Full-suite regression (FR-023, SC-008)

```bash
uv run invoke lint              # ruff, yamllint, mypy, rumdl, vale — all green
uv run pytest tests/unit        # unchanged, still passing
uv run invoke docs              # site builds
```

Then the closing check for the whole feature (SC-004): re-run the audit and confirm zero errors and zero
warnings across priorities 1 to 4, with governance recorded as blocked.

```text
/opsmill-repo:auditing-repo-standards
```

## Known limitations to expect in the results

- **Branch protection stays non-compliant.** `main` is unprotected because the private repository's GitHub
  plan returns `403` for both classic protection and rulesets. Out of scope per the spec; expect the audit to
  report it as blocked, not fixed.
- **Skipped-check semantics depend on that.** With no required status checks, skipped jobs cannot block
  merges. If branch protection is later enabled, revisit
  [contracts/ci-checks.md](./contracts/ci-checks.md) before configuring required checks (R10).
- **`mypy` coverage is unchanged** — `generators`/`transforms` stay non-blocking, `checks/`, `scripts/`, and
  `tests/` stay unchecked. Deliberately out of scope.
- **Integration tests still run on demand only**, so a pull request's green checks do not imply integration
  coverage. Unchanged by this feature.
