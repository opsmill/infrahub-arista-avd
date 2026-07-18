# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.1] - 2026-07-19

### Changed

- Made hook command wording agent-neutral so the same extension works for Codex
  skills and Claude Code slash commands.
- Updated install and troubleshooting guidance to refer to the active agent's
  available OpsMill Infrahub skills instead of assuming Claude Code only.
- Changed template resolution to prefer templates shipped by this extension.

### Added

- Bundled Infrahub-specific spec templates for schema, objects, checks,
  generators, transforms, and menus.
- Added object-data artifact routing through `infrahub-managing-objects`.

## [3.0.0] - 2026-05-28

### Changed

- **BREAKING**: This package is now a spec-kit **extension** (`extension.yml`), not a preset (`preset.yml`). Composition has moved from the slash-command layer (preset/wrap) to the skill-runtime layer (hooks). Install with `specify extension add` instead of `specify preset add`. The extension id is `infrahub-speckit` (renamed from `infrahub` to avoid collision with the standalone `infrahub` JPD/Jira branch validator extension).
- **BREAKING**: The three customized commands (`speckit.specify`, `speckit.plan`, `speckit.implement`) are no longer wrapped. The Infrahub routing logic now lives in three new hook commands (`speckit.infrahub-speckit.route-specify`, `route-plan`, `route-implement`) registered against `before_specify`, `before_plan`, and `before_implement` respectively. From a user's perspective, `/speckit.specify` behaves the same — the hook fires before the core skill body runs. From an integrator's perspective, the routing now fires for *any* invocation of the underlying skills, not just the slash command — so callers like `opsmill-speckit/auto` are now covered.

### Why this matters

The v2.x preset wrapped slash command files. When `opsmill-speckit/auto` (or any other skill or agent) invoked the `speckit-specify` skill directly without going through `/speckit.specify`, the wrap was bypassed and Infrahub routing did not run. The v3.0 hook fires inside the core skill's pre-execution checks, regardless of caller.

### Migration

```bash
specify preset remove infrahub
specify extension add infrahub-speckit --from https://github.com/opsmill/infrahub-speckit/archive/refs/tags/v3.0.0.zip
```

After upgrade, `.specify/extensions.yml` will have three new entries under `hooks.before_specify`, `hooks.before_plan`, and `hooks.before_implement`. No other consumer-side changes required.

### Removed

- `preset.yml` (replaced by `extension.yml`).
- `commands/speckit.specify.md`, `commands/speckit.plan.md`, `commands/speckit.implement.md` (replaced by the three `route-*` hook commands).

## [2.0.0] - 2026-04-24

### Added

- Preflight skill-availability check in all three wrapped commands. If `.infrahub.yml` is present and any required `infrahub-managing-*` skill from the OpsMill Infrahub skill package is missing, the command halts with install guidance for the active agent and a pointer to https://docs.infrahub.app/skills/installation-setup. Closes a silent-failure hole where the "MUST invoke skill" instruction no-op'd when the skills weren't installed.

### Changed

- **BREAKING**: Commands now use the `wrap` composition strategy introduced in spec-kit v0.8.0 instead of `replace`. The core command body (including `before_specify` / `after_plan` / `after_implement` hooks, `SPECIFY_FEATURE_DIRECTORY` resolution, `.specify/feature.json` persistence, marker-based agent context updates, and language-specific `.gitignore` patterns) is inherited automatically from upstream.
- Minimum required `speckit_version` bumped from `>=0.4.1` to `>=0.8.0`.
- `speckit.specify.md`, `speckit.plan.md`, and `speckit.implement.md` now contain only the Infrahub-specific pre-logic (routing, preflight, skill invocation, template selection) followed by the `{CORE_TEMPLATE}` placeholder.
- README now distinguishes the REQUIRED `opsmill/infrahub` Claude Code skills package from the OPTIONAL `infrahub` spec-kit extension, with install commands for both.

### Removed

- `requires.extensions` entry in `preset.yml` — not part of the official spec-kit preset schema. The `infrahub` extension dependency is now documented in README instead.
- `replaces:` fields on template entries in `preset.yml` — superseded by `strategy: "wrap"`, which identifies the wrapped command via the `name` field.
- Duplicated `before_specify` / `after_specify` / `before_plan` / `after_plan` / `before_implement` / `after_implement` hook-handling blocks — now inherited from core.
- Duplicated Outline, Phases, and Quick Guidelines sections — now inherited from core.

## [1.0.0] - 2026-04-01

### Added

- Initial release of the Infrahub Workflow Routing preset
- `speckit.specify` command override with Infrahub artifact routing
- `speckit.plan` command override with mandatory Infrahub skill invocation
- `speckit.implement` command override with task-level artifact detection
- Multi-artifact dependency chain ordering (Schema first)
- Connectivity gating via `infrahubctl info`
- Artifact type detection for schema, transform, check, generator, and menu
