<!--
Sync Impact Report
==================
Version change: (none) -> 1.0.0 (initial ratification)

Modified principles: N/A (initial creation)

Added sections:
  - Core Principles (5): Schema-Driven Architecture, Idempotent Operations,
    Type Safety, Test-Required Quality, Convention-Based Structure
  - Technology Stack & Constraints
  - Development Workflow & Quality Gates
  - Governance

Removed sections: N/A

Templates requiring updates:
  - .specify/templates/plan-template.md: Constitution Check is generic,
    dynamically filled per feature. No update needed.
  - .specify/templates/spec-template.md: No constitution-specific
    references. No update needed.
  - .specify/templates/tasks-template.md: No constitution-specific
    references. No update needed.
  - .specify/templates/commands/: No command files exist.

Follow-up TODOs: None
-->

# AVD Workshop Constitution

## Core Principles

### I. Schema-Driven Architecture

All infrastructure modeling MUST begin with Infrahub YAML schema
definitions. Schemas are the single source of truth for the data model.

- Every new entity, relationship, or attribute MUST be defined in a
  schema file under `schemas/` before any generator, transform, or
  library code references it.
- Schema changes MUST trigger regeneration of protocol classes via
  `infrahubctl protocols`.
- Node namespaces MUST follow established conventions: `Network.*`,
  `Location.*`, `Organization.*`, `Ipam.*`, `Avd.*`, `Routing.*`.
- Schema extensions MUST be used to add relationships to existing nodes
  rather than modifying their original YAML files.

**Rationale**: The Infrahub platform enforces schema-first design. Code
that references undefined schema elements will fail at runtime. Keeping
schemas as the authoritative source prevents drift between the data
model and implementation.

### II. Idempotent Operations

All generators and data mutations MUST be idempotent. Running the same
operation multiple times MUST produce the same result without side
effects.

- Generators MUST use `allow_upsert=True` for all node creation to
  enable safe re-execution.
- Generators MUST use HFID-based deduplication to prevent duplicate
  nodes.
- Checksum-based change detection (`GeneratorMixin.calculate_checksum()`)
  MUST be used to avoid unnecessary regeneration.
- Interface relationships MUST be re-fetched with `include=["link"]`
  before assignment to ensure consistency.

**Rationale**: Generators execute in response to triggers and may run
multiple times for the same input. Non-idempotent operations create
duplicate data, broken relationships, and unpredictable state.

### III. Type Safety

All code interfacing with Infrahub data MUST use typed models. Untyped
dictionary access to GraphQL responses is prohibited in production code.

- All GraphQL query responses MUST have corresponding Pydantic models
  in `*_query.py` files.
- Protocol classes (`protocols.py`) MUST be used for type-safe Infrahub
  node access in generators and transforms.
- mypy MUST pass with `disallow_untyped_defs = true` on all Python
  source files.
- Helper functions MUST use explicit type annotations for parameters
  and return values.

**Rationale**: The Infrahub SDK returns deeply nested data structures.
Without typed models, field access errors surface only at runtime,
making debugging expensive and generators unreliable.

### IV. Test-Required Quality

All generators, transforms, and library modules MUST have corresponding
tests. Tests may be written before, alongside, or after implementation
but MUST exist before code is merged.

- Unit tests MUST cover all generator logic, transform behavior, and
  utility functions.
- Integration tests SHOULD cover end-to-end Infrahub interactions for
  critical paths.
- All linters (`ruff`, `mypy`, `yamllint`) MUST pass before merge.
  The `inv lint` command validates all three.
- Ruff complexity limit is C901 max-complexity=17. Functions exceeding
  this MUST be split into smaller methods.
- Schema YAML files MUST NOT be included in ruff targets.

**Rationale**: Generators create infrastructure at scale. A bug in a
generator can produce hundreds of misconfigured nodes. Tests catch
regressions before they propagate to production infrastructure.

### V. Convention-Based Structure

All files MUST follow established naming conventions and directory
organization. Deviation from conventions MUST be justified.

- Generators: `generate_<entity>.py` with matching
  `<entity>_generator_query.py` and `generate_<entity>.gql`.
- Transforms: `<transform>.py` with matching `<transform>_query.py`
  and `<transform>.gql`.
- Object data files: numbered YAML files (`01_*.yml`, `02_*.yml`, ...)
  loaded in sequence order.
- Seed data MUST be added to existing numbered files or use the next
  available number in the sequence.
- GraphQL queries MUST be in `.gql` files co-located with their
  Python consumers.

**Rationale**: The Infrahub framework and `.infrahub.yml` configuration
rely on predictable file locations and naming. Inconsistent naming
breaks auto-discovery, makes cross-referencing difficult, and
increases onboarding friction.

## Technology Stack & Constraints

- **Language**: Python >=3.11, <3.14
- **Platform**: Infrahub (Neo4j, PostgreSQL, Redis, RabbitMQ)
- **Key Dependencies**: `infrahub-sdk==1.18.1`, `pyavd>=5.0.0`
- **Package Manager**: `uv` with `hatchling` build backend
- **Linting**: ruff (ALL rules, line-length=120), mypy (strict),
  yamllint
- **Testing**: pytest with pytest-asyncio (`asyncio_mode = "auto"`)
- **Infrastructure**: Docker Compose for local development
- Code MUST NOT introduce dependencies outside the versions pinned in
  `pyproject.toml` without explicit justification.
- The `ariadne-codegen` override in `[tool.uv]` MUST be preserved
  due to infrahub-sdk pinning constraints.

## Development Workflow & Quality Gates

1. **Schema First**: Define or extend schemas before writing code.
2. **Regenerate Protocols**: Run `infrahubctl protocols` after schema
   changes.
3. **Implement**: Write generators, transforms, or library code
   following naming conventions.
4. **Test**: Write unit tests; run `pytest tests/unit`.
5. **Lint**: Run `inv lint` (ruff + mypy + yamllint). All MUST pass.
6. **Format**: Run `inv format` to auto-fix formatting issues.
7. **Integration Verify**: For generator/transform changes, run
   `pytest tests/integration` against a running Infrahub instance.

Quality gates before merge:
- All unit tests pass
- All linters pass (zero warnings)
- No new TODO items without tracking
- Generator changes tested with idempotent re-runs

## Governance

This constitution supersedes ad-hoc practices and MUST be consulted
when architectural decisions are made.

- **Amendments**: Changes to this constitution require documentation
  of the rationale, a version bump, and review of all dependent
  templates for consistency.
- **Versioning**: Semantic versioning (MAJOR.MINOR.PATCH). MAJOR for
  principle removal or redefinition; MINOR for new principles or
  material expansion; PATCH for wording clarifications.
- **Compliance**: All pull requests SHOULD be verified against these
  principles. Violations MUST be justified in the PR description.
- **Guidance**: Runtime development guidance is maintained in
  `CLAUDE.md` at the repository root.

**Version**: 1.0.0 | **Ratified**: 2026-02-10 | **Last Amended**: 2026-02-10
