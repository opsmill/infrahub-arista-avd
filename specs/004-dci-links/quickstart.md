# Quickstart: Validate DCI Links

This guide validates the implementation that will be built from this plan. It
uses generic branch and token setup only; do not commit private lab hostnames or
tokens into feature artifacts.

## Prerequisites

- Python dependencies installed with `uv sync --all-packages`.
- A reachable Infrahub server and API token configured in your shell.
- Work on an Infrahub branch, not directly on main.

```bash
uv run infrahubctl info
uv run infrahubctl branch create dci-links-validation
```

## 1. Schema Validation

```bash
uv run infrahubctl schema check schemas/ --branch dci-links-validation
uv run infrahubctl schema load schemas/ --branch dci-links-validation
```

Expected outcome:

- `DcimDevice.role` includes `border_leaf` without removing existing roles.
- `NetworkDciLink` exists and reuses the `DcimConnector` physical endpoint
  behavior used by `NetworkLink`.
- `NetworkDciLink` directly defines only `include_in_underlay_protocol` and the
  two BGP ASN values required for generation.
- `NetworkFabric` exposes an optional `dci_pool` relationship to
  `CoreIPPrefixPool`.
- `NetworkFabric.dci_pool` is the authoritative DCI pool selector; no DCI prefix
  role metadata, direct DCI link pool field, or DCI-specific pool relationship is
  added for this feature.
- Existing non-DCI data remains valid.

## 2. Regenerate Generated Files

```bash
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
uv run infrahubctl graphql export-schema --destination schema.graphql
uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
```

Expected outcome:

- `src/solution_arista_avd/protocols.py` contains `NetworkDciLink`.
- `generators/generate_avd_device_inputs_query.py` matches the updated
  hostvars query.
- No generated files were hand-edited.

## 3. Model a Valid DCI Link

Create or update test data on the branch through the UI, GraphQL, or object
YAML:

1. Set two network devices to role `border_leaf`.
2. Ensure each device has one physical interface for DCI.
3. Connect the two interfaces through one `NetworkDciLink` using inherited link
   connected endpoint behavior.
4. Set the two DCI BGP ASN values.
5. Assign a DCI IP pool to the parent fabric through `NetworkFabric.dci_pool`.
6. Leave `include_in_underlay_protocol` at its default `true`.

## 4. Generate and Validate Hostvars

Run the existing generation path for the affected AVD devices.

Expected outcome:

- Border Leaf devices map to PyAVD `l3leaf`.
- The generator allocates exactly one `/31` from the fabric DCI pool for the DCI
  link and reuses it on repeated runs.
- The generated hostvars include one deterministic `l3_edge.p2p_links[]` entry
  for the modeled DCI link.
- The entry includes endpoint nodes, interfaces, BGP ASNs, allocated IPs, and
  `include_in_underlay_protocol` directly on the link entry.
- The entry includes `speed` only when endpoint/interface speed can be resolved;
  when speed cannot be resolved, the generated DCI link entry omits the `speed`
  key.
- The generated hostvars do not include DCI `p2p_links_profiles[]` or `profile`
  references.
- Invalid DCI links are excluded from generated `l3_edge` intent and reported
  through the generator execution result or logs with the DCI link identifier and
  failed rule; they are not silently ignored.
- Re-running generation without data changes produces the same hostvars checksum
  and no duplicate DCI entries.

## 5. PyAVD Field Validation

Verify the pinned PyAVD schema accepts generated DCI shapes with and without
`speed`:

```bash
uv run python - <<'PY'
from pyavd import validate_inputs

candidate_with_speed = {
    "fabric_name": "FABRIC",
    "l3_edge": {
        "p2p_links": [{
            "nodes": ["border1", "border2"],
            "interfaces": ["Ethernet1", "Ethernet1"],
            "as": [65101, 65201],
            "ip": ["10.0.0.0/31", "10.0.0.1/31"],
            "speed": "100g",
            "include_in_underlay_protocol": True,
        }]
    },
}

candidate_without_speed = {
    "fabric_name": "FABRIC",
    "l3_edge": {
        "p2p_links": [{
            "nodes": ["border1", "border2"],
            "interfaces": ["Ethernet1", "Ethernet1"],
            "as": [65101, 65201],
            "ip": ["10.0.0.0/31", "10.0.0.1/31"],
            "include_in_underlay_protocol": True,
        }]
    },
}

for name, candidate in {
    "with_speed": candidate_with_speed,
    "without_speed": candidate_without_speed,
}.items():
    violations = validate_inputs(candidate).validation_result.violations
    print(f"{name}: violations={len(violations)}")
    for violation in violations:
        print(violation.path, violation.message)
PY
```

Expected outcome for the current pinned PyAVD 6.3.0 environment:

- The command reports `violations=0` for both candidates.
- Generated hostvars emit only the supported profile-free
  `l3_edge.p2p_links[]` keys listed in the contracts.

## 6. Local Tests and Lint

```bash
uv run pytest tests/unit/test_avd.py
uv run pytest tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py
uv run invoke lint
```

Expected outcome:

- `border_leaf` maps to `l3leaf`.
- DCI `l3_edge` extraction, allocation, validation, and ordering tests pass.
- PyAVD validation passes for generated hostvars with resolved speed and with
  omitted speed.
- Ruff, mypy, and yamllint pass.

## 7. Documentation Validation

If docs are updated:

```bash
cd docs
npm run typecheck
npm run build
```

Expected outcome:

- Supported capabilities mention DCI support scope.
- Role mapping docs list `border_leaf -> l3leaf`.
- Hostvars docs describe DCI `l3_edge` generation and the supported field
  boundary.

## 8. Required Project Validation

For implementation changes, run the required validation skills:

```text
$infrahub-run-integration-tests
$infrahub-test-generator-idempotence
```

Expected outcome:

- Integration validation reports the tested branch and commit.
- Generator idempotence validation reports repeated-run no-op behavior for the
  DCI `l3_edge` scenario.

## Implementation Evidence

Recorded during local implementation:

- Active feature context was read directly from `specs/004-dci-links/` because
  this worktree does not include `.specify/scripts/python/check_prerequisites.py`.
- Schema branch used for validation: `dci-links-validation`.
- `uv run infrahubctl schema check schemas/ --branch dci-links-validation` passed.
- `uv run infrahubctl schema load schemas/ --branch dci-links-validation` passed.
- `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py` ran, but the local schema-file path emitted incomplete extension protocol fields with this CLI version; `uv run infrahubctl protocols --branch dci-links-validation --out src/solution_arista_avd/protocols.py` was used for the committed protocol refresh after schema load.
- `INFRAHUB_DEFAULT_BRANCH=dci-links-validation uv run infrahubctl graphql export-schema --destination schema.graphql` passed.
- `INFRAHUB_DEFAULT_BRANCH=dci-links-validation uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql` passed.
- `uv run pytest tests/unit/test_avd.py tests/unit/test_dci_schema_contract.py tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py` passed: 86 tests.
- `uv run ruff check` on touched hand-written Python, integration coverage, and unit tests passed.
- PyAVD 6.3.0 accepted DCI `l3_edge.p2p_links` shapes with and without `speed`
  with zero validation violations.
- `cd docs && npm run typecheck` passed after installing docs dependencies.
- `cd docs && npm run build` passed after installing docs dependencies.
- `uv run invoke lint` passed after excluding generated GraphQL return-type
  model files from ruff, matching the generated-file rule for those files.
- Integration coverage was added in `tests/integration/test_e2e_pipeline.py` for
  a complete `NetworkDciLink` between two Border Leafs through shared connector
  relationships, with assertions against stored `l3_edge.p2p_links` hostvars.
- `uv run python -m py_compile tests/integration/test_e2e_pipeline.py` passed.
- Changed feature specs/docs were scanned for private hostnames, tokens, and
  environment-specific command sequences; only generic localhost documentation
  and the no-private-data requirement text were found.

Remote/live gates still required before merge:

- `$infrahub-run-integration-tests`: blocked in this session because the branch
  is not committed/pushed for the remote integration worktree to test an exact
  commit.
- `$infrahub-test-generator-idempotence`: blocked pending explicit approval to
  use and rebuild the shared live validation lab.
