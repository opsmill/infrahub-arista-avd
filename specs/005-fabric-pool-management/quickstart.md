# Quickstart: Validate Fabric Pool Management Schema

## Prerequisites

- Install project dependencies:

```bash
uv sync --all-packages
```

- Source `.env` before local `infrahubctl` commands if using the CLI against the shared Infrahub instance:

```bash
set -a; source .env; set +a
```

## Focused Schema Contract Tests

After implementation, run the focused tests for the schema contract:

```bash
uv run pytest tests/unit/test_fabric_pool_schema_contract.py tests/unit/test_dci_schema_contract.py tests/unit/test_l3ls_pools.py
```

Expected outcomes:

- `IpamPrefix.role` includes `fabric_supernet`, `fabric_point_to_point`, `dci`, `mlag`, and `mlag_peering`.
- Legacy role choices remain valid during migration.
- `NetworkFabric.fabric_ip_pools` and `NetworkPod.pod_ip_pools` exist as many-valued Attribute relationships.
- Legacy fabric and pod pool relationships remain present and compatible.
- No replacement fabric or pod schema node is introduced.

## Schema Validation

Run a schema check before loading changes:

```bash
uv run infrahubctl schema check schemas/
```

Expected outcome: schema check completes with zero validation errors and shows only the intended role-choice and relationship changes.

## Protocol Regeneration

Regenerate protocol classes after schema changes:

```bash
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

Expected outcome: `src/solution_arista_avd/protocols.py` reflects the new `NetworkFabric` and `NetworkPod` relationships and is not hand-edited.

## Object Compatibility Smoke Test

After the schema implementation and dual-populated object migration, validate that current object data still loads on a feature branch:

```bash
uv run infrahubctl branch create fabric-pool-management-validation
uv run infrahubctl schema load schemas --branch fabric-pool-management-validation
uv run infrahubctl object load objects/ --branch fabric-pool-management-validation
```

Expected outcomes:

- Current seed objects using legacy pool relationships remain valid.
- Legacy fabric pool assignments are also present in `fabric_ip_pools`.
- Legacy pod MLAG pool assignments are also present in `pod_ip_pools`.
- Migrated fabric, DCI, and MLAG pool prefixes use explicit role values such as `fabric_supernet`, `fabric_point_to_point`, `dci`, `mlag`, and `mlag_peering`.

## Full Local Quality Gates

Run the standard local gates before integration validation:

```bash
uv run pytest tests/unit
uv run invoke lint
```

Expected outcome: all unit tests and linters pass.

## Integration Validation

For the schema and object-loading change, use the required project integration validation skill:

```text
$infrahub-run-integration-tests
```

The validation report must include the tested branch and commit.

## Generator Idempotence Validation

This feature changes generator code, generator GraphQL queries, generated fallback pool creation, and object data. Run:

```text
$infrahub-test-generator-idempotence
```

Expected outcome: repeated generator runs produce no duplicate pools, prefixes, IP addresses, relationships, hostvars, or structured configs.
