# Infrahub Workflow Routing Extension

`infrahub-speckit` hooks the core Spec Kit specify, plan, and implement
workflows when `.infrahub.yml` is present. It is intended to work with multiple
Spec Kit integrations, including Codex skills and Claude Code slash commands.

## What It Does

The extension registers three `before_*` hooks:

- `before_specify`: detects the Infrahub artifact type, loads the matching
  `infrahub-managing-*` skill, and tells the core specify workflow which
  Infrahub-specific template to use.
- `before_plan`: reloads the matching Infrahub skill before research and design
  artifacts are generated.
- `before_implement`: reads `tasks.md` and `plan.md`, then loads one Infrahub
  skill for each artifact type touched by the implementation.

The extension also ships the Infrahub spec templates directly:

- `spec-schema-template`
- `spec-objects-template`
- `spec-check-template`
- `spec-generator-template`
- `spec-transform-template`
- `spec-menu-template`

## Supported Agents

Command names are integration-specific. The hook command IDs remain the same.

| Integration | User-facing command style |
|-------------|---------------------------|
| Codex skills | `/speckit-specify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-implement` |
| Claude Code slash commands | `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement` |

The hook text avoids assuming a specific agent. It checks that the active
session has the required OpsMill Infrahub skills available:

- `infrahub-managing-schemas`
- `infrahub-managing-transforms`
- `infrahub-managing-checks`
- `infrahub-managing-generators`
- `infrahub-managing-menus`
- `infrahub-managing-objects`

## Requirements

- Spec Kit `>=0.8.0`
- The active agent has the `infrahub-managing-*` skills installed or available
- `infrahubctl` is available for the `before_specify` connectivity check

## Local Development Install

From a project that should use this local extension:

```bash
specify extension remove infrahub-speckit --force
specify extension add ~/git/infrahub-speckit-codex --dev --force
specify extension list
```

Re-run the `add --dev --force` command after changing this extension source.

## Published Install

Install from a released archive when a fixed version is published:

```bash
specify extension add infrahub-speckit --from https://github.com/opsmill/infrahub-speckit/archive/refs/tags/v3.0.1.zip
```

Install from the catalog when available:

```bash
specify extension add infrahub-speckit
```

## Artifact Routing

The specify hook classifies prompts into one or more artifact types.

| Artifact Type | Skill | Template |
|---------------|-------|----------|
| Schema | `infrahub-managing-schemas` | `spec-schema-template` |
| Objects | `infrahub-managing-objects` | `spec-objects-template` |
| Check | `infrahub-managing-checks` | `spec-check-template` |
| Generator | `infrahub-managing-generators` | `spec-generator-template` |
| Transform | `infrahub-managing-transforms` | `spec-transform-template` |
| Menu | `infrahub-managing-menus` | `spec-menu-template` |

When a request spans multiple artifact types, run one Spec Kit cycle per
artifact. Schema is first because every other Infrahub artifact depends on the
data model.

```text
Schema -> [Objects / Check / Generator / Transform / Menu]
```

## Template Resolution

The specify hook resolves templates in this order:

1. `.specify/extensions/infrahub-speckit/templates/<template-name>.md`
2. `.specify/templates/spec-template.md` as a generic fallback

## Troubleshooting

**Skills are missing**

Install or enable the OpsMill Infrahub skills for the active agent. In Codex,
confirm the skills are listed in the session inventory. In Claude Code, install
the skills package or plugin for that environment.

**Infrahub is not reachable**

The `before_specify` hook runs `infrahubctl info`. Start an Infrahub instance or
configure the environment expected by the project, including `INFRAHUB_ADDRESS`
and authentication when using a remote lab.

**The hook uses the generic spec template**

Confirm this extension was installed from the source that includes the
`templates/` directory, then re-run:

```bash
specify extension add ~/git/infrahub-speckit-codex --dev --force
```
