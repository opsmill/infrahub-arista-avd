# Arista AVD Reference Design

## Project context

This repository is the Arista AVD Reference Design for Infrahub. It models datacenter
fabric intent, topology, addressing pools, EVPN services, and per-device AVD data in
Infrahub, then renders EOS configurations and documentation through PyAVD.

Key docs to read before larger changes:

- `README.md` and `docs/docs/home.md` for the current product overview.
- `docs/docs/quick-start.md` for stack/load commands.
- `docs/docs/supported-capabilities.md` before assuming a feature is supported.
- `docs/docs/developer-guide/architecture.md` for the data model and generator chain.
- `docs/docs/developer-guide/schemas.md` for schema kinds and dropdown values.
- `docs/docs/developer-guide/generators.md` for generator structure and execution order.
- `docs/docs/developer-guide/transforms.md` for transform structure and artifacts.
- `docs/docs/developer-guide/avd/overview.md` for the two-phase AVD pipeline.
- `docs/docs/developer-guide/avd/extending.md` for extension workflows.
- `docs/docs/developer-guide/avd/debugging.md` for pipeline debugging.

## Repository layout

- `src/solution_arista_avd/` - core Python library: AVD helpers, cabling,
  addressing, sorting, generator utilities, and generated protocols.
- `generators/` - Infrahub generators and their GraphQL queries / generated
  query models.
- `transforms/` - Python transforms, GraphQL queries, generated query models,
  and templates.
- `checks/` - proposed-change checks (CloudVision validation and its workspace
  lifecycle helpers).
- `ansible/` - playbooks Semaphore runs, including ContainerLab deployment.
- `schemas/` - Infrahub schema definitions, split between base schemas and
  project/feature extensions.
- `objects/` - seed data loaded in filename order.
- `menus/` - Infrahub UI menu definitions.
- `docs/` - Docusaurus documentation.
- `lab/` - ContainerLab artifact/deployment helpers.
- `.infrahub.yml` - menus, queries, generators, transforms, and artifact
  definitions.
- `repository.yml` - CoreRepository definition.
- `tasks.py` - Invoke task definitions.

## Architecture summary

- Data model hierarchy: `NetworkFabric` -> `NetworkPod` -> `LocationRack` ->
  `DcimDevice` -> `DcimInterface` / `NetworkLink` / `IpamIPAddress`.
- The fabric generator chain is `generate-fabric` -> `generate-pod` ->
  `generate-rack` -> `generate-avd-device-hostvar` ->
  `generate-avd-device-structured-config`.
- Hostvars are stored as `AvdHostvarFile` nodes under `AvdArtifact`; structured
  configs are stored as `AvdStructuredConfigFile` nodes under the same artifact.
- AVD transforms render artifacts from the stored files: EOS config, device docs,
  fabric docs, cabling plan, ANTA catalog, and computed interface descriptions.
- PyAVD is version-sensitive; the project targets `pyavd>=6.3.0,<6.4.0`.
- The service portal is a Streamlit app for day-2 workflows; every workflow should
  operate on an Infrahub branch and produce a proposed change for review.

## Generator and transform inventory

Current generator definitions are registered in `.infrahub.yml`:
`generate-fabric`, `generate-pod`, `generate-rack`, `generate-server-cabling`,
`generate-avd-device-hostvar`, `generate-avd-device-structured-config`, and
`backfill-structured-config`.

Current Python transforms are: `computed_interface_description`, `cabling_plan`,
`avd_eos_config`, `avd_fabric_doc`, `avd_device_doc`, `avd_anta_catalog`,
`containerlab_topology`, and `cv_workspace_submission_webhook_payload`.

The only check definition is `cv-config-validation` (`checks/cv_config_check.py`),
with its workspace lifecycle and helpers in `checks/cv_workspace_lifecycle.py` and
`checks/cv_helpers.py`.

## Development workflow

1. Prefer schema-first changes: add or update YAML under `schemas/` before code uses
   new nodes, attributes, relationships, or dropdown values.
2. Regenerate generated files rather than hand-editing them:
   - `src/solution_arista_avd/protocols.py` is generated.
   - `*_query.py` Pydantic models next to `.gql` files are generated.
3. Implement generators, transforms, object data, menus, checks, or docs using the
   matching local Infrahub skills when a task touches those artifact types.
4. Keep generators idempotent: use upserts/natural keys, deterministic ordering,
   checksum comparisons, and repeated-run validation.
5. Keep GraphQL responses typed: update `.gql`, regenerate return types, and use the
   generated Pydantic models in production code.
6. Add or update unit tests for changed generator, transform, hostvars, role mapping,
   or utility behavior.
7. Run local unit/lint validation, integration tests and generator idempotence test as applicable.

## Naming conventions

- Generators: `generate_<entity>.py`.
- Generator GraphQL queries: matching `.gql` files.
- Generated query models: `*_query.py`; regenerate them from `.gql` files rather
  than hand-editing.
- Node namespaces commonly used here: `Network.*`, `Location.*`,
  `Organization.*`, `Ipam.*`, `Dcim.*`, `Avd.*`, `Routing.*`, `Evpn.*`,
  `Interface.*`, `Compute.*`.

## Extension checklist

When adding a device role:

1. Add the role value in `schemas/dcim_extensions.yml`.
2. Load/check schema and regenerate generated files.
3. Update `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`.
4. Update `generators/generate_avd_device_hostvar.py` for role-specific fields.
5. Update whichever upstream generator creates devices of that role and group membership.
6. Add tests, especially `tests/unit/test_avd.py` and hostvars tests when needed.
7. Update `docs/docs/developer-guide/avd/role-mapping.md` and hostvars docs.

When adding a transform output:

1. Add the `.gql` query under `transforms/`.
2. Regenerate the matching `*_query.py`; do not hand-write it.
3. Implement the transform class in `transforms/`.
4. Register the query, transform, and artifact definition in `.infrahub.yml`.
5. Add unit tests and integration coverage when appropriate.

When adding a hostvars field:

1. Add schema if the source data is not already represented.
2. Reload/check schema and regenerate protocols / GraphQL schema / return types.
   Use `graphql export-schema --destination schema.graphql` with the current CLI.
3. Update `generators/avd_device_hostvar.gql`.
4. Map the field in `generators/generate_avd_device_hostvar.py`.
5. Confirm the field is accepted by the pinned PyAVD version.
6. Add tests and update `docs/docs/developer-guide/avd/hostvars.md`.

## Commands agents may use

Install and discovery:

```bash
uv sync --all-packages
uv run invoke --list
```

Invoke tasks:

```bash
uv run invoke build
uv run invoke start
uv run invoke stop
uv run invoke destroy
uv run invoke restart
uv run invoke restart --component=infrahub-server
uv run invoke restart --component=service-catalog
uv run invoke load
uv run invoke load-schema
uv run invoke load-menu
uv run invoke init-semaphore
uv run invoke test
uv run invoke lint
uv run invoke lint-ruff
uv run invoke lint-yaml
uv run invoke lint-mypy
uv run invoke lint-markdown
uv run invoke lint-prose
uv run invoke format
uv run invoke docs
```

Local tests and linters:

```bash
uv run pytest tests/unit
uv run pytest tests/unit/test_avd.py
uv run pytest tests/unit/test_hostvar_ordering.py
uv run ruff check .
uv run ruff format --check .
uv run ruff format .
uv run mypy --show-error-codes src/solution_arista_avd
uv run yamllint .
uv run rumdl check README.md AGENTS.md docs/ lab/README.md schemas/
uv run rumdl fmt README.md AGENTS.md docs/ lab/README.md schemas/
```

Markdown linting covers authored files only; vendored agent content, `specs/`, and
PyAVD-rendered output under `lab/avd/` are excluded in `[tool.rumdl]`.

Prose linting uses Vale, which is a Go binary rather than a `uv` dependency. Install the
pinned version before running `invoke lint-prose`:

```bash
curl -sL "https://github.com/errata-ai/vale/releases/download/v3.17.1/vale_3.17.1_Linux_64-bit.tar.gz" \
  -o /tmp/vale.tar.gz && tar -xzf /tmp/vale.tar.gz -C ~/.local/bin vale
vale sync
```

Use local `uv run pytest tests/integration` only for ad-hoc local/lab debugging when explicitly
appropriate.

`infrahubctl` examples:

```bash
uv run infrahubctl branch list
uv run infrahubctl branch create <branch-name>
uv run infrahubctl schema check schemas/ --branch <branch-name>
uv run infrahubctl schema load schemas --branch <branch-name>
uv run infrahubctl menu load menus/ --branch <branch-name>
uv run infrahubctl object load objects/ --branch <branch-name>
uv run infrahubctl object load repository.yml --branch <branch-name>
uv run infrahubctl object load triggers.yml --branch <branch-name>
uv run infrahubctl graphql export-schema --destination schema.graphql
uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
uv run infrahubctl graphql generate-return-types transforms/<query>.gql
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

For repeated `infrahubctl` calls, define a temporary shell alias in the current session only:

```bash
alias ihctl='uv run infrahubctl'
```

The documentation site uses pnpm, not npm. Prefer `uv run invoke docs`, which runs the same
commands CI runs. To work inside `docs/` directly:

```bash
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
```

pnpm settings for the site live in `docs/pnpm-workspace.yaml`, not in `docs/package.json` -
pnpm no longer reads the `pnpm` field there, so overrides placed in it are ignored.
