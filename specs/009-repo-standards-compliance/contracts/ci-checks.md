# Contract: CI Check Surface

**Feature**: [../spec.md](../spec.md) | **Date**: 2026-08-11

The pull-request check list is this repository's contract with contributors: it defines what CI promises to
verify and when. This document fixes that surface so `/speckit-tasks` and implementation cannot drift from
it, and so a future reader can tell an intentional gap from an oversight.

## Workflow-level invariants

| Property | Value | Source |
|---|---|---|
| `name` | `CI` | existing, unchanged |
| Triggers | `pull_request`, `push` to `main`, `workflow_dispatch` | existing, unchanged |
| Concurrency | `${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true` | existing, unchanged |
| Permissions | `contents: read` at workflow level | existing; no job widens it (FR-024) |
| `env` | `UV_FROZEN: "true"` | existing, unchanged |
| Action pins | `checkout@v7`, `setup-uv@v9`, `setup-node@v7`, `pnpm/action-setup@v6`, `opsmill/paths-filter@v3.0.2` | R7 |

## Job contract

`C` = change-gated (runs only when its category changed). Every job declares `timeout-minutes` (FR-024).

| Job | Gate | Timeout | Runs | Delivers |
|---|---|---|---|---|
| `files-changed` | always | 5 | `opsmill/paths-filter@v3.0.2` against `.github/file-filters.yml` | FR-008 |
| `lint` | C: `python` | 10 | ruff check, ruff format --check, yamllint, mypy (src enforced; generators/transforms non-blocking) | FR-023 preserved verbatim |
| `unit-tests` | C: `python` | 15 | `pytest tests/unit -v` | FR-023 preserved verbatim |
| `markdown-lint` | C: `markdown` | 5 | `uv run rumdl check` over the authored set | FR-002, SC-002 |
| `documentation` | C: `documentation` | 5 | pnpm install + Docusaurus build | FR-001, SC-001 |
| `validate-documentation-style` | C: `documentation` | 5 | Vale 3.17.1, downloaded then `vale sync` | FR-015 |
| `integration-tests` | `workflow_dispatch` only | 15 | subset suite | unchanged (out of scope) |
| `integration-tests-full` | `workflow_dispatch` only | 45 | testcontainers stack against the pinned image | unchanged; pin becomes `1.10.6` |

### Outputs of `files-changed`

Each output is consumed as `needs.files-changed.outputs.<name>`:

| Output | Filter alias |
|---|---|
| `documentation` | `documentation_all` |
| `python` | `python_all` |
| `yaml` | `yaml_all` |
| `markdown` | `markdown_all` |

### Gating expression

Change-gated jobs use the plain form:

```yaml
if: needs.files-changed.outputs.<category> == 'true'
needs: ["files-changed"]
```

The `documentation` and `validate-documentation-style` jobs additionally follow the audit rule's
never-mask-a-failure pattern when they depend on upstream lint jobs:

```yaml
if: |
  always() && !cancelled() &&
  !contains(needs.*.result, 'failure') &&
  !contains(needs.*.result, 'cancelled') &&
  needs.files-changed.outputs.documentation == 'true'
```

## Outcome semantics

| Situation | Contract |
|---|---|
| Category changed, check passes | Green |
| Category changed, check fails | Red, and the message names file and rule (SC-002) |
| Category unchanged | Job reports `skipped` |
| No category matched at all | Only `files-changed` runs; the pull request stays mergeable (FR-010) |
| Fork pull request | `files-changed` resolves using `github.token`; no elevated permission required (FR-009 edge case) |

**Why `skipped` is safe here**: this repository has no branch protection and therefore no required status
checks — verified during the audit (both the classic protection and rulesets endpoints return `403` on the
current plan). A skipped job cannot block a merge. **If branch protection is ever enabled, this contract
changes**: whoever configures required checks must list only always-running jobs, or introduce an
aggregating gate job, because a permanently-skipped required check blocks merges indefinitely (R10).

## Bump workflow contract

| Property | `update-infrahub.yml` | `update-infrahub-sdk.yml` |
|---|---|---|
| Triggers | `workflow_dispatch` (`version` required, `run` bool), `repository_dispatch: [trigger-infrahub-update]` | same shape, `[trigger-infrahub-sdk-python-update]` |
| Version resolution | `github.event_name == 'repository_dispatch' && github.event.client_payload.version \|\| github.event.inputs.version` | same |
| Concurrency | group keyed on the resolved version + branch, `cancel-in-progress: false` | same |
| Files updated | compose files, `Dockerfile` ARG, `infrahub-testcontainers` pin, `uv.lock`, documented version refs | `infrahub-sdk[all]` pin, `uv.lock` |
| Duplicate guard | skip create when a pull request for the head branch is already open | same |
| Identity | `opsmill-bot` / `github-bot@opsmill.com`, secret `GH_UPDATE_PACKAGE_OTTO` | same |
| Base branch | `main` | `main` |
| Failure mode | If the secret is absent the workflow MUST fail visibly, never succeed having changed nothing (spec edge case) | same |

## Backward-compatibility guarantees

1. The `lint` and `unit-tests` jobs keep their exact commands. Their only change is `if:` + `needs:` — a
   contributor's Python pull request sees identical behaviour (FR-023).
2. The two integration jobs keep their manual-only trigger. This feature does not change when they run.
3. `mypy` coverage is unchanged: `src/` enforced, `generators`/`transforms` non-blocking. Expanding it is
   explicitly out of scope.
4. No job name in use today is renamed, so any external reference to a check name keeps resolving.
