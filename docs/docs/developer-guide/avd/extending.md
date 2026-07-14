---
title: Extending the Pipeline
description: Worked examples for adding a device role, adding a transform output, or adding a hostvar field.
audience: developer
sidebar_position: 6
---

# Extending the Pipeline

:::info Developer Guide
This page is part of the developer guide. The touch-point lists below give you the exact files to edit for the three most common extensions.
:::

## Add a new device role

Scenario: you want to support a new Infrahub role (e.g. `border-leaf`) that maps to a pyAVD type.

**Touch points:**

1. **Schema** — add the role value to the `DcimDevice` `role` dropdown in [`schemas/dcim_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/dcim_extensions.yml) (the single authoritative device-role list).
2. **Reload the schema and regenerate generated files** — none of these files should be hand-edited:
   ```bash
   uv run invoke load-schema                                             # push schema to Infrahub
   uv run infrahubctl graphql export-schema --out schema.graphql         # refresh the local GraphQL SDL
   uv run infrahubctl protocols --out src/solution_arista_avd/protocols.py    # refresh typed protocol classes
   ```
3. **Role map** — add the mapping in [`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py):
   ```python
   ROLE_TO_AVD_TYPE: dict[str, str] = {
       ...,
       "border_leaf": "l3leaf",   # or whatever pyAVD type fits
   }
   ```
4. **Hostvars generator** — add a branch for the new role in [`generators/generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) for any role-specific fields (uplink role, MLAG, EVPN data).
5. **Upstream generator** — whichever generator creates devices of this role (fabric/pod/rack/custom) needs to set the `role` attribute correctly and add the device to the `avd_devices` group.
6. **Tests** — add a case in [`tests/unit/test_avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_avd.py) covering `get_avd_type("border_leaf")`.
7. **Docs** — update [Role Mapping](./role-mapping.md) and, if the role implies new hostvar fields, [Hostvars Reference](./hostvars.md).

## Add a new transform output

Scenario: you want an additional artifact per device or per fabric (e.g. a JSON summary, a CSV inventory).

**Touch points:**

1. **GraphQL query** — write the `.gql` query under `transforms/`. Example: `transforms/avd_inventory.gql`.
2. **Pydantic query model** — **do not write this by hand.** Generate it with:
   ```bash
   uv run infrahubctl graphql generate-return-types transforms/avd_inventory.gql
   ```
   This reads `schema.graphql` (checked in at the repo root) and emits `transforms/avd_inventory_query.py` alongside the query. Re-run whenever the query or the schema changes. If the schema is stale, regenerate it first with `uv run infrahubctl graphql export-schema` (requires a running Infrahub).
3. **Transform class** — implement the transform in `transforms/avd_inventory.py` as a subclass of the Infrahub Python transform base class. Typical structure:
   ```python
   class AvdInventoryTransform(InfrahubTransform):
       query = "avd_inventory"

       async def transform(self, data: dict) -> str:
           parsed = AvdInventoryQuery.model_validate(data)
           # ... your logic here
           return output
   ```
4. **Register in `.infrahub.yml`**:
   ```yaml
   queries:
     - name: avd_inventory
       file_path: "./transforms/avd_inventory.gql"

   python_transforms:
     - name: avd_inventory
       class_name: AvdInventoryTransform
       file_path: "./transforms/avd_inventory.py"

   artifact_definitions:
     - name: avd_inventory_csv
       targets: fabrics          # or avd_devices, depending on scope
       transformation: avd_inventory
   ```
5. **Tests** — add a unit test under `tests/unit/` exercising `transform()` on a fixture, plus optionally an integration test that hits a running Infrahub.

After merge, operators can open the new artifact from the target node's **Artifacts** tab.

## Add a new field to hostvars

Scenario: you want pyAVD to receive an additional input field (e.g. a per-device SNMP location string) that currently isn't populated.

**Touch points:**

1. **Schema** — if the field isn't already represented, add it to the relevant schema (`NetworkDevice`, `NetworkFabric`, etc.) in [`schemas/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/schemas).
2. **Reload the schema and regenerate generated files**:
   ```bash
   uv run invoke load-schema                                             # push schema to Infrahub
   uv run infrahubctl graphql export-schema --out schema.graphql         # refresh the local GraphQL SDL
   uv run infrahubctl protocols --out src/solution_arista_avd/protocols.py    # refresh typed protocol classes
   ```
3. **GraphQL query** — update [`generators/avd_device_hostvar.gql`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/avd_device_hostvar.gql) to pull the new field.
4. **Pydantic query model** — regenerate, don't hand-edit:
   ```bash
   uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
   ```
   This rewrites `generators/generate_avd_device_inputs_query.py` from the query and the refreshed schema.
5. **Hostvars builder** — map the new attribute into the pyAVD hostvars dict in [`generators/generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py):
    - Device-level, role-independent field → add it in `_build_hostvars()` (where `type`, `fabric_name`, `bgp_as`, loopback/mgmt basics are assembled).
    - Role-specific or multi-attribute field → add the logic in the appropriate role branch of the same file.
6. **Validation** — pyAVD's `validate_inputs()` will flag unknown fields as errors. Confirm the field is in the pyAVD input schema for the version pinned (see [overview](./overview.md#pyavd-version)). If it isn't a standard pyAVD field, look at using `custom_structured_configuration_prefix` or `structured_config` pass-through instead.
7. **Tests** — add a case in [`tests/unit/test_hostvar_ordering.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_hostvar_ordering.py) for any hostvars logic added to the generator. (`tests/unit/test_avd.py` covers only the role→type mapping in `src/solution_arista_avd/avd.py`.)
8. **Docs** — update [Hostvars Reference](./hostvars.md) with the new field and its Infrahub source.

## Checklist: what to run before opening a PR

- `uv run invoke lint` — ruff, mypy, yamllint must all pass.
- `uv run pytest tests/unit` — all unit tests pass.
- `uv run pytest tests/integration` — integration tests pass (requires a running Infrahub).
- On a feature branch in a live Infrahub, trigger the affected generator(s) twice and confirm idempotence — the second run should be a no-op per [Debugging the Pipeline → checksum-based skipping](./debugging.md#checksum-based-change-detection).
