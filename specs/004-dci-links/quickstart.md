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
- `NetworkLink.role` supports `dci` with label `DCI`.
- `NetworkLink` keeps its existing physical endpoint behavior for ordinary and
  DCI-role links.
- `NetworkLink` directly defines only the allowed DCI-specific fields:
  `role`, `include_in_underlay_protocol`, and the two endpoint BGP ASN values.
- `NetworkFabric` exposes an optional `dci_pool` relationship to
  `CoreIPPrefixPool`.
- `NetworkFabric.dci_pool` is the authoritative DCI pool selector; no DCI prefix
  role metadata, direct DCI link pool field, or DCI-specific pool relationship is
  added for this feature.
- Existing non-DCI Network Link data remains valid.
- The stale standalone DCI link kind is absent from committed schemas.

## 2. Regenerate Generated Files

```bash
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
uv run infrahubctl graphql export-schema --destination schema.graphql
uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
```

Expected outcome:

- `src/solution_arista_avd/protocols.py` contains `NetworkLink` DCI fields and
  no stale standalone DCI link protocol classes.
- `generators/generate_avd_device_inputs_query.py` matches the updated
  hostvars query and sources DCI candidates from `NetworkLink`.
- No generated files were hand-edited.

## 3. Remove Stale References

```bash
rg "NetworkDciLink|DciLink" schemas generators transforms tests docs src menus .infrahub.yml schema.graphql
```

Expected outcome:

- The command returns no stale schema, query, menu, docs, tests, protocol, or
  generator references.
- The regenerated `schema.graphql` no longer exposes `NetworkDciLink` types or
  fields.
- Any remaining matches outside those implementation paths are feature-planning
  references that explicitly document the removal decision.

## 4. Model a Valid DCI Link

Create or update test data on the branch through the UI, GraphQL, or object
YAML:

1. Set two network devices to role `border_leaf`.
2. Ensure each device has one physical interface for DCI.
3. Connect the two interfaces through one `NetworkLink`.
4. Set `NetworkLink.role` to `dci`.
5. Set the two DCI BGP ASN values on the Network Link.
6. Assign a DCI IP pool to the parent fabric through `NetworkFabric.dci_pool`.
7. Leave `include_in_underlay_protocol` at its default `true`.

## 5. Generate and Validate Hostvars

Run the existing generation path for the affected AVD devices.

Expected outcome:

- Border Leaf devices map to PyAVD `l3leaf`.
- The generator considers only `NetworkLink` objects with `role = dci` for DCI
  output.
- Ordinary Network Links do not generate DCI intent.
- The generator allocates exactly one `/31` from the fabric DCI pool for each
  valid DCI-role link and reuses it on repeated runs.
- The generated hostvars include one deterministic `l3_edge.p2p_links[]` entry
  for each valid DCI-role Network Link.
- The entry includes endpoint nodes, interfaces, BGP ASNs, allocated IPs, and
  `include_in_underlay_protocol` directly on the link entry.
- The entry includes `speed` only when endpoint/interface speed can be resolved;
  when speed cannot be resolved, the generated DCI link entry omits the `speed`
  key.
- The generated hostvars do not include DCI `p2p_links_profiles[]` or `profile`
  references.
- Invalid DCI-role links are excluded from generated `l3_edge` intent and
  reported through the generator execution result or logs with the Network Link
  identifier and failed rule; they are not silently ignored.
- Re-running generation without data changes produces the same hostvars checksum
  and no duplicate DCI entries.

## 6. PyAVD Field Validation

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

Expected outcome for the pinned pyAVD 6.3.x environment:

- The command reports `violations=0` for both candidates.
- Generated hostvars emit only the supported profile-free
  `l3_edge.p2p_links[]` keys listed in the contracts.

## 7. Local Tests and Lint

```bash
uv run pytest tests/unit/test_avd.py
uv run pytest tests/unit/test_dci_schema_contract.py
uv run pytest tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py
uv run invoke lint
```

Expected outcome:

- `border_leaf` maps to `l3leaf`.
- Schema contract tests prove DCI is sourced from `NetworkLink.role = dci` and
  stale standalone DCI link schema is absent.
- DCI `l3_edge` extraction, allocation, validation, and ordering tests pass.
- PyAVD validation passes for generated hostvars with resolved speed and with
  omitted speed.
- Ruff, mypy, and yamllint pass.

## 8. Documentation Validation

If docs are updated:

```bash
cd docs
npm run typecheck
npm run build
```

Expected outcome:

- Supported capabilities mention DCI support scope.
- Role mapping docs list `border_leaf -> l3leaf`.
- Hostvars docs describe DCI `l3_edge` generation from Network Links with
  `role = dci`.
- Schema docs do not expose a standalone DCI link object.

## 9. Required Project Validation

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

Recorded during implementation:

- Active feature context was read directly from `specs/004-dci-links/`; this
  worktree does not include the stock `.specify/scripts/python/check_prerequisites.py`.
- Schema validation passed on branch `dci-links-validation`:
  `uv run infrahubctl schema check schemas/ --branch dci-links-validation` and
  `uv run infrahubctl schema load schemas/ --branch dci-links-validation`.
- Generated artifacts were refreshed from loaded schema/query data:
  `src/solution_arista_avd/protocols.py`, `schema.graphql`, and
  `generators/generate_avd_device_inputs_query.py`.
- Stale implementation reference validation passed for
  `NetworkDciLink|DciLink`; remaining references are limited to feature
  planning text documenting the removal.
- Local focused validation passed:
  `uv run pytest tests/unit/test_avd.py tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py tests/unit/test_dci_schema_contract.py`
  reported 89 passed.
- Local standard lint passed with generated docs dependencies outside the repo:
  `uv run invoke lint`.
- Documentation validation passed earlier in this implementation:
  `cd docs && npm run typecheck && npm run build`.
- Remote ordered e2e validation passed after syncing the implementation to the
  isolated integration worktree:
  `uv run pytest tests/integration/test_e2e_pipeline.py -x -s --tb=short -vv`
  reported 16 passed.
- Remote full integration validation passed in the same isolated worktree:
  `uv run pytest tests/integration` reported 29 passed.

Pending live gate:

- `$infrahub-test-generator-idempotence` was not run. The skill requires
  explicit approval to use and normally rebuild the shared live validation lab,
  and it expects a committed revision for checkout on that lab.
