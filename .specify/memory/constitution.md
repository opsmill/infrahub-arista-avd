<!--
Sync Impact Report
==================
Version change: 1.1.1 -> 1.2.0 (minor: the mandatory linter set gains Markdown
  and prose linting, which is materially expanded quality-gate guidance)

Modified principles:
  - Test-Required Quality: the pre-merge linter gate expands from ruff, mypy,
    and yamllint to include rumdl (Markdown) and Vale (prose).

Added sections: None

Removed sections: None

Supporting sections updated:
  - Technology Stack & Constraints: Infrahub image target moves from 1.10.1 to
    1.10.6 (deliberate patch upgrade, planned by the repo-standards-compliance
    feature); rumdl added to development dependencies; pnpm recorded as the
    documentation-site package manager; the linting entry now names Markdown and
    prose linting; a stated exception covers Vale, which ships as a Go binary and
    so cannot live in pyproject.toml.

Templates and command files requiring updates:
  - .specify/templates/plan-template.md: ✅ reviewed; no update required.
  - .specify/templates/spec-template.md: ✅ reviewed; no update required.
  - .specify/templates/tasks-template.md: ✅ reviewed; no update required.
  - AGENTS.md: ✅ updated with the new invoke tasks, pnpm commands, and the Vale
    install step.

Follow-up TODOs: None

Previous report (1.1.0 -> 1.1.1: remove committed lab-specific details and align
runtime guidance with Codex AGENTS.md)

Modified principles:
  - Idempotent Operations: generalized live idempotence safety-exception wording
    so environment-specific prohibitions stay in local guidance and skills.
  - Test-Required Quality: kept dedicated validation skills mandatory while
    removing committed validation-environment hostnames.

Added sections: None

Removed sections: None

Supporting sections updated:
  - Technology Stack & Constraints: removed the Docker Compose infrastructure
    constraint that implied required local-stack validation.
  - Development Workflow & Quality Gates: kept validation skill gates without
    environment-specific lab details.
  - Mandatory Validation Skills: removed lab hostnames, token-sensitive
    procedure details, and the rack-generator-specific live-validation sentence.
  - Governance: references Codex `AGENTS.md` guidance and requires
    environment-specific lab details to remain uncommitted.

Templates and command files requiring updates:
  - .specify/templates/plan-template.md: ✅ updated validation-skill gate wording.
  - .specify/templates/spec-template.md: ✅ reviewed; no update required.
  - .specify/templates/tasks-template.md: ✅ reviewed; wording remains aligned.
  - .agents/skills/speckit-tasks/SKILL.md: ✅ updated to generic live-validation
    safety-exception wording.
  - Legacy agent guidance: ✅ sanitized so committed files avoid lab names.
  - .gitignore: ✅ updated to keep local Codex guidance untracked.
  - AGENTS.md: ✅ created as local, ignored Codex runtime guidance.

Follow-up TODOs: None
-->

# Arista AVD Reference Design Constitution

## Core Principles

### I. Schema-Driven Architecture

All infrastructure modeling MUST begin with Infrahub YAML schema definitions.
Schemas are the single source of truth for the data model.

- Every new entity, relationship, or attribute MUST be defined in a schema file
  under `schemas/` before any generator, transform, or library code references
  it.
- Schema changes MUST be validated before load and MUST trigger regeneration of
  protocol classes with `infrahubctl protocols --schemas schemas --out
  src/solution_arista_avd/protocols.py`.
- Node namespaces MUST follow established conventions: `Network.*`,
  `Location.*`, `Organization.*`, `Ipam.*`, `Avd.*`, `Routing.*`, and other
  approved project namespaces.
- Schema extensions MUST be used to add relationships to existing base nodes
  unless the change intentionally modifies the base schema contract.

**Rationale**: Infrahub enforces schema-first design. Code that references
undefined schema elements fails at runtime. Keeping schemas authoritative
prevents drift between the graph model, generators, transforms, and tests.

### II. Idempotent Operations

All generators and data mutations MUST be idempotent. Running the same operation
multiple times MUST produce the same result without duplicate objects or stale
relationships.

- Generators MUST use `allow_upsert=True` for all node creation that can be
  re-executed safely.
- Generators MUST use HFID-based deduplication or another explicit natural key
  strategy to prevent duplicate nodes.
- Checksum-based change detection, including `GeneratorMixin.calculate_checksum()`
  where applicable, MUST be used to avoid unnecessary regeneration.
- Interface relationships MUST be re-fetched with the `link` relationship
  included before assignment when link state may have changed.
- Generator plans and tests MUST define how repeated execution is validated.
- Generator code, generator query, trigger, or generator-owned data changes MUST
  be validated with `$infrahub-test-generator-idempotence` before merge when
  live validation is permitted.
- When a validation skill or project safety rule prohibits a live repeated-run
  scenario, plans MUST use an approved non-live alternative and document the
  exception.

**Rationale**: Generators execute from triggers and manual re-runs. Non-idempotent
operations create duplicate data, broken relationships, and unpredictable
infrastructure state.

### III. Type Safety

All code interfacing with Infrahub data MUST use typed models. Untyped dictionary
access to GraphQL responses is prohibited in production code.

- All GraphQL query responses MUST have corresponding Pydantic models in
  `*_query.py` files.
- Protocol classes in `src/solution_arista_avd/protocols.py` MUST be used for
  type-safe Infrahub node access in generators and transforms.
- mypy MUST pass with `disallow_untyped_defs = true` on Python source files.
- Helper functions MUST use explicit type annotations for parameters and return
  values.
- Generated protocol code MUST NOT be hand-edited to satisfy static analysis;
  regenerate it from schemas instead.

**Rationale**: The Infrahub SDK returns deeply nested data structures. Typed
models surface field and shape errors before runtime, reducing generator and
transform failures.

### IV. Test-Required Quality

All generators, transforms, and library modules MUST have corresponding tests.
Tests may be written before, alongside, or after implementation, but MUST exist
before code is merged.

- Unit tests MUST cover generator logic, transform behavior, and utility
  functions affected by a change.
- Integration tests MUST cover every Infrahub code change. The required project
  path is `$infrahub-run-integration-tests`, which owns integration-suite
  execution in the project-designated validation environment and records the
  tested branch and commit.
- Integration tests MUST cover critical Infrahub interactions, generator chains,
  transforms, schema migrations, and repository-load behavior when behavior
  cannot be validated with unit tests alone.
- Idempotence-sensitive generator changes MUST be validated with repeated-run
  checks in unit, integration, or approved live-test scenarios. Generator changes
  MUST also use `$infrahub-test-generator-idempotence` when the live scenario is
  allowed.
- All linters (`ruff`, `mypy`, `yamllint`, `rumdl`, Vale) MUST pass before merge.
  The `uv run invoke lint` command validates the standard lint suite.
- Ruff complexity limit is C901 max-complexity=17. Functions exceeding this
  limit MUST be split into smaller methods.
- Schema YAML files and generated protocol code MUST NOT be hand-included in
  ruff targets.

**Rationale**: Generators create infrastructure at scale. A generator defect can
produce hundreds of misconfigured nodes. Tests and lint gates catch regressions
before they propagate to production infrastructure.

### V. Convention-Based Structure

All files MUST follow established naming conventions and directory organization.
Deviation from conventions MUST be justified in the plan or pull request.

- Generators MUST be named `generate_<entity>.py` with matching
  `<entity>_generator_query.py` and `generate_<entity>.gql` files when GraphQL is
  needed.
- Transforms MUST be named `<transform>.py` with matching `<transform>_query.py`
  and `<transform>.gql` files when GraphQL is needed.
- Object data files MUST remain numbered YAML files under `objects/` and MUST
  load in deterministic sequence order.
- Seed data MUST be added to existing numbered files or use the next available
  sequence number.
- GraphQL queries MUST be stored in `.gql` files co-located with their Python
  consumers.
- Documentation changes MUST use the Docusaurus tree under `docs/docs/` and
  update `docs/sidebars.ts` when navigation changes.

**Rationale**: Infrahub repository loading, `.infrahub.yml`, and developer
onboarding rely on predictable file locations and naming. Inconsistent structure
breaks discovery and makes cross-references expensive to maintain.

## Technology Stack & Constraints

- **Language**: Python >=3.11, <3.14.
- **Platform**: Infrahub with Neo4j, PostgreSQL, Redis, and RabbitMQ.
- **Infrahub image**: Build and local-stack workflows target
  `INFRAHUB_BASE_VERSION=1.10.6` unless a feature explicitly plans an upgrade.
- **Core dependencies**: `pyavd>=6.3.0,<6.4.0`, `httpx>=0.28.1`, and
  `streamlit-flow-component>=1.6.1`.
- **Development dependencies**: `infrahub-sdk` with the `all` extra at
  version >=1.19.0,
  `infrahub-testcontainers>=1.3.0`, `invoke>=2.2.0`, `pytest>=8.4.1`,
  `pytest-asyncio>=1.0.0`, `ruff>=0.12.0`, `mypy>=1.17.1`, `rumdl>=0.2.54`,
  and `yamllint>=1.37.1`.
- **Service portal dependencies**: the `catalog` dependency group owns Streamlit,
  pandas, python-dotenv, and the catalog SDK constraint.
- **Package manager**: `uv` with `hatchling` build backend for Python, and
  `pnpm` for the documentation site under `docs/`. npm and yarn MUST NOT be
  used, and only one JavaScript lockfile may exist.
- **Linting**: ruff with ALL selected rules and project ignores, mypy with typed
  function enforcement, yamllint, rumdl for authored Markdown, and Vale for
  documentation prose.
- **Prose linting exception**: Vale ships as a Go binary with no PyPI
  distribution, so it is the one tool exempt from the
  dependencies-in-`pyproject.toml` rule below. It MUST be pinned by version
  wherever it is installed, and its style packages MUST be synced rather than
  vendored.
- **Testing**: pytest with pytest-asyncio and the repository's configured test
  markers.
- Code MUST NOT introduce dependencies outside `pyproject.toml` and `uv.lock`
  without explicit rationale and validation.
- The uv override dependencies for `ariadne-codegen` and `click` MUST be
  preserved unless the Infrahub SDK constraint that requires them is removed.

## Development Workflow & Quality Gates

1. **Schema First**: Define or extend schemas before writing code that references
   new graph fields, nodes, or relationships.
2. **Schema Check**: Run `uv run infrahubctl schema check schemas/` or a targeted
   schema check before loading schema changes into an Infrahub branch.
3. **Regenerate Protocols**: Run `uv run infrahubctl protocols --schemas schemas
   --out src/solution_arista_avd/protocols.py` after schema changes.
4. **Implement**: Write generators, transforms, object data, documentation, or
   library code following the naming conventions above.
5. **Test Locally**: Add required tests and run `uv run pytest tests/unit` for
   local validation.
6. **Lint**: Run `uv run invoke lint`. Ruff, mypy, and yamllint MUST pass.
7. **Format**: Run `uv run invoke format` when formatting changes are needed.
8. **Integration Verify**: Use `$infrahub-run-integration-tests` for every
   Infrahub code change. The report MUST identify the tested branch and commit.
9. **Generator Idempotence Verify**: Use `$infrahub-test-generator-idempotence`
   for generator changes when live validation is allowed. The report MUST include
   the validation branch, generator scenario, snapshot scope, and no-diff result.

Quality gates before merge:
- All required unit tests pass.
- `$infrahub-run-integration-tests` passes for every Infrahub code change, or the
  pull request documents an explicit maintainer-approved exception.
- Generator changes include `$infrahub-test-generator-idempotence` evidence when
  live validation is permitted, or an approved documented alternative when it is
  not.
- All linters pass with zero unaddressed findings.
- No new TODO, FIXME, or XXX items are added without tracking context.
- Schema changes include schema-check and protocol-regeneration evidence.
- Dependency changes include rationale, lockfile updates, and validation results.

## Mandatory Validation Skills

- `$infrahub-run-integration-tests` MUST be used for Infrahub code changes. It
  owns required integration-suite execution in the project-designated validation
  environment and MUST report the tested branch and commit.
- `$infrahub-test-generator-idempotence` MUST be used for generator changes when
  live validation is permitted. It owns approval handling, environment
  preparation, branch selection, repeated generator execution, snapshot scope,
  and no-diff result reporting.
- If a validation skill or project safety rule prohibits a live validation
  scenario, the change MUST include an approved alternative validation plan and
  document why live validation was not run.
- Environment-specific hostnames, tokens, and lab command sequences MUST NOT be
  committed in the constitution, templates, or shared runtime guidance. They
  belong only in uncommitted local agent guidance or local validation-skill
  instructions.

## Governance

This constitution supersedes ad-hoc practices and MUST be consulted when
architectural decisions are made.

- **Amendments**: Changes to this constitution require documented rationale, a
  semantic version bump, and review of dependent templates, command files, and
  runtime guidance for consistency.
- **Versioning**: Semantic versioning is mandatory. MAJOR increments remove or
  redefine principles; MINOR increments add principles, sections, or materially
  expanded guidance; PATCH increments clarify wording or align non-principle
  details with the repository.
- **Compliance**: Pull requests MUST be verified against these principles.
  Violations MUST be justified in the pull request description with the accepted
  trade-off and follow-up plan.
- **Guidance**: Runtime development guidance is maintained in Codex `AGENTS.md`
  files, active agent- or environment-specific instructions, and reusable
  skills. Procedure details that belong to a skill MUST NOT be duplicated in
  shared guidance; local guidance SHOULD link or point to the skill instead.
  Environment-specific hostnames, tokens, and lab details MUST remain
  uncommitted. When guidance conflicts, the stricter project safety rule wins
  unless an explicit maintainer decision supersedes it.

**Version**: 1.2.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-08-11
