# Contract: Task Runner Surface

**Feature**: [../spec.md](../spec.md) | **Date**: 2026-08-11

`tasks.py` is the documented way contributors and agents run repository operations — `AGENTS.md` lists it as
the command surface. This contract fixes what the surface looks like after this feature, so local runs and
CI agree (SC-008) and no documented command breaks.

## Task inventory

| Task | Status | Command it runs | Mirrors CI job |
|---|---|---|---|
| `format` | modified | `ruff format .`, `ruff check . --fix`, **`rumdl fmt <authored set>`** | — |
| `lint` | modified | fan-out: `lint_yaml`, `lint_ruff`, `lint_mypy`, **`lint_markdown`**, **`lint_prose`** | `lint` + `markdown-lint` + `validate-documentation-style` |
| `lint-yaml` | unchanged | `yamllint .` | `lint` |
| `lint-ruff` | unchanged | `ruff check .`, `ruff format --check .` | `lint` |
| `lint-mypy` | unchanged | `mypy --show-error-codes src/solution_arista_avd` | `lint` |
| `lint-markdown` | **new** | `rumdl check <authored set>` | `markdown-lint` |
| `lint-prose` | **new** | `vale <docs/docs md+mdx>` | `validate-documentation-style` |
| `docs` | **new** | `pnpm install --frozen-lockfile && pnpm run build` in `docs/` | `documentation` |
| everything else (`build`, `start`, `stop`, `destroy`, `restart`, `load`, `load-schema`, `load-menu`, `init-semaphore`, `test`, `submit-cv-workspace`, `download-compose-file`) | unchanged | — | — |

## Signature and typing rules

Every new task follows the file's existing pattern and the constitution's Type Safety principle
(`disallow_untyped_defs = true`):

```python
@task
def lint_markdown(ctx: Context) -> None:
    """Run rumdl to lint authored Markdown files."""
```

- Parameter annotated `ctx: Context`; return annotated `-> None`.
- Body wrapped in `with ctx.cd(MAIN_DIRECTORY_PATH):`, matching every existing lint task.
- A short docstring, because `invoke --list` renders it as the task's help text.
- Task names use the file's existing convention: function `lint_markdown` surfaces as `lint-markdown`.

## Behavioural guarantees

| Guarantee | Why it matters |
|---|---|
| `invoke lint` remains a superset of what CI's lint jobs check | A contributor who runs it locally cannot be surprised by CI (SC-008) |
| `invoke lint` fails on the first failing linter, as today | Existing fan-out semantics unchanged |
| `invoke format` never edits generated or vendored files | `rumdl fmt` receives the same authored-set paths as `rumdl check`, so it cannot rewrite `lab/avd/**` output or vendored skill docs |
| Task names in `AGENTS.md` stay valid | No existing task is renamed or removed |

## Known asymmetry: `lint-prose` needs an external binary

`lint-markdown` works from a clean checkout after `uv sync`, because `rumdl` is a dev dependency.
`lint-prose` cannot, because Vale is a Go binary with no PyPI distribution (R6).

The contract for `lint-prose`:

1. It MUST detect a missing `vale` binary and exit with an actionable message naming the pinned version and
   how to install it — never fail with a bare `command not found`.
2. It MUST run `vale sync` before linting, so the style packages are present.
3. Its absence locally MUST NOT make `invoke lint` unusable. Treat a missing binary as a skip-with-warning
   rather than a hard failure, so contributors without Vale can still run the rest of the suite; CI has the
   binary and remains the enforcing gate.

This asymmetry is deliberate and is the local-side consequence of the Complexity Tracking deviation recorded
in [../plan.md](../plan.md).

## Documentation obligations

Because `AGENTS.md` publishes the command surface, these updates ship with the task changes:

- Add `lint-markdown`, `lint-prose`, and `docs` to the invoke task list.
- Replace the `npm run typecheck` / `npm run build` block with the pnpm equivalents, or point at
  `invoke docs`.
- Add `rumdl check` and the Vale invocation to the local linter list, alongside the existing `ruff`, `mypy`,
  and `yamllint` entries.
