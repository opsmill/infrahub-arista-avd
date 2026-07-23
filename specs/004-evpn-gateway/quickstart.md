# Quickstart: EVPN Gateway Domain Validation

## Prerequisites

- Dependencies installed with `uv sync --all-packages`.
- A reachable Infrahub instance configured through `.env`.
- The `border_leaf` role dependency from PR #74 / `feat/dci-links` is present before gateway-group implementation.
- EVPN Domain, EVPN Gateway Group, menu, and hostvar generator changes have been implemented.

Verify the Border Leaf dependency locally:

```bash
rg "border_leaf" schemas/dcim_extensions.yml src/solution_arista_avd/avd.py tests/unit/test_avd.py
```

Expected outcome:

- `DcimDevice.role` includes `border_leaf`.
- `ROLE_TO_AVD_TYPE` maps `border_leaf` to `l3leaf`.
- Unit tests cover the mapping.

Export local environment variables before running Infrahub CLI commands:

```bash
set -a
source .env
set +a
```

Verify connectivity:

```bash
uv run infrahubctl info
```

## Branch-First Schema Validation

Use an explicit Infrahub branch for schema validation and loading:

```bash
uv run infrahubctl branch create evpn-gateway-validation
uv run infrahubctl schema check schemas/ --branch evpn-gateway-validation
uv run infrahubctl schema load schemas/ --branch evpn-gateway-validation
```

Expected outcome:

- Schema check reports no validation errors.
- Schema load targets `evpn-gateway-validation`, not the default branch.
- Existing Fabric, Pod, and Device objects remain valid because extensions are additive.
- `EvpnDomain` and `EvpnGatewayGroup` are present.
- `EvpnGateway` is not present.
- `EvpnGatewayGroup` has no independently selected `local_domain` relationship and no computed or denormalized helper attribute exists solely to display the Pod-derived local EVPN Domain.

## Generated Types

Regenerate protocol classes after schema changes:

```bash
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```

Regenerate the hostvar query return type after updating `generators/avd_device_hostvar.gql`:

```bash
uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
```

Expected outcome:

- `src/solution_arista_avd/protocols.py` includes `EvpnDomain` and `EvpnGatewayGroup` protocols.
- The generated hostvar query model includes the target device's `evpn_gateway_group` relationship and the remote-domain gateway-group traversal.
- Generated files are not hand-edited.

## Repository and Menu Registration

After adding the menu item, load repository configuration artifacts on the validation branch:

```bash
uv run infrahubctl object load repository.yml --branch evpn-gateway-validation
uv run infrahubctl menu load menus/ --branch evpn-gateway-validation
```

Expected outcome:

- The repository reaches `in-sync`.
- The EVPN Services menu contains one Domains item linked to `EvpnDomain`.
- The EVPN Services menu contains no direct Gateways item linked to `EvpnGatewayGroup`.
- No menu item points to `EvpnGateway`.
- No duplicate automatic `EvpnDomain` or `EvpnGatewayGroup` sidebar entry appears.
- Opening an EVPN Domain shows the related gateway groups through the domain relationships.

## Acceptance Scenario: Domains Without Gateways

On the validation branch, model a Fabric with no EVPN Domains and existing Pods.

Expected outcome:

- The Fabric remains valid.
- Pods may have no `evpn_domain`.
- No Border Leaf receives EVPN Gateway hostvars just because it belongs to the Fabric or Pod.

## Acceptance Scenario: Shared Remote CORE Domain

On the validation branch, model this data through the UI or object-loading workflow:

- One Fabric.
- Three `EvpnDomain` objects in the Fabric: two Pod-local domains and one remote exchange domain named CORE.
- Two Pods, each assigned to exactly one local `evpn_domain`.
- Two `EvpnGatewayGroup` objects, one per Pod.
- Both gateway groups point to the CORE domain as `remote_domain`.
- Each group has one or more `DcimDevice` members with role `border_leaf`, and every member belongs to the group's Pod.
- Each group has shared all-active Ethernet Segment identifier and RT import values.

Expected outcome:

- Each group derives its local domain from its Pod.
- No group has a directly selected local domain.
- Each member Border Leaf is considered an EVPN Gateway through group membership.
- Full-mesh peer intent is derived from the two groups sharing CORE.
- No route-server or route-reflector model is selectable or required.

## Hostvar Generation Scenario

Run hostvar generation for one grouped Border Leaf and one ungrouped Leaf or Border Leaf:

```bash
uv run infrahubctl generator run generate-avd-device-hostvar --target <border-leaf-device-id> --branch evpn-gateway-validation
uv run infrahubctl generator run generate-avd-device-hostvar --target <unlinked-device-id> --branch evpn-gateway-validation
```

Expected outcome:

- The grouped Border Leaf hostvars include `l3leaf.nodes[0].evpn_gateway`.
- The payload uses `remote_peers`, `evpn_l2`, `evpn_l3`, `d_path`, and `all_active_multihoming.evpn_ethernet_segment`.
- `d_path.local_domain_id` is derived from `EvpnGatewayGroup.pod.evpn_domain.domain_id`.
- `d_path.remote_domain_id` is derived from `EvpnGatewayGroup.remote_domain.domain_id`.
- `remote_peers[].hostname` is derived from other valid gateway-group member Border Leafs sharing the same remote domain.
- The payload does not include deprecated `all_active_multihoming.enable_d_path`, `evpn_domain_id_local`, or `evpn_domain_id_remote`.
- The ungrouped device hostvars do not include `evpn_gateway`.
- The generator validates the final hostvars with pyAVD before writing `AvdHostvarFile`.

## Structured Config Peer Resolution Scenario

After every gateway member device in the Fabric has a stored hostvar file, run the structured-config generator for the Fabric:

```bash
uv run infrahubctl generator run generate-avd-device-structured-config --target <fabric-id> --branch evpn-gateway-validation
```

Expected outcome:

- The structured-config generator fetches all Fabric hostvar files and passes the complete mapping to pyAVD.
- `pyavd.get_avd_facts()` resolves hostname-only `evpn_gateway.remote_peers` from the remote gateway devices' generated hostvars.
- `pyavd.get_device_structured_config()` succeeds for each grouped Border Leaf.
- If a remote peer hostname is missing from the aggregated hostvars, generation fails with an actionable peer-resolution error instead of requiring manually modeled peer IP or BGP ASN fields.

## Negative Scenarios

Use object data to verify generator-side failures:

- Add a regular `leaf` as an `EvpnGatewayGroup.members` device.
- Add a `border_leaf` member from a different Pod.
- Create a gateway group for a Pod with no `evpn_domain`.
- Set the group `remote_domain` to the same domain as the Pod-derived local domain.
- Create a gateway group without members.
- Model unsupported route-server or route-reflector behavior if any draft field exists.
- Remove Ethernet Segment identifier or RT import values from an all-active group.

Expected outcome:

- Hostvar generation either omits gateway fields for ineligible ungrouped devices or fails before writing hostvars when grouped gateway data is invalid.

## Local Quality Gates

Run focused validation after implementation:

```bash
uv run pytest tests/unit/test_avd.py
uv run pytest tests/unit/test_evpn_gateway_schema_contract.py
uv run pytest tests/unit/test_evpn_gateway_menu_contract.py
uv run pytest tests/unit/test_generate_avd_device_hostvar.py
uv run pytest tests/unit/test_hostvar_ordering.py
uv run invoke lint
```

Expected outcome:

- Unit tests pass.
- pyAVD hostvar validation tests pass against AVD `v6.3.0`.
- Ruff, mypy, and yamllint pass.

## Required Project Validation

Use the required Infrahub integration validation skill before merge:

```text
$infrahub-run-integration-tests
```

Expected report:

- Tested branch and commit are recorded.
- Repository load, schema, menu, generator, and hostvar artifact behavior pass.

Because the existing hostvar generator and query change, use generator idempotence validation when live validation is allowed:

```text
$infrahub-test-generator-idempotence
```

Expected report:

- The affected `generate-avd-device-hostvar` scenario runs twice.
- The second run produces no owned-state diff.
- The report includes branch, generator scenario, snapshot scope, and no-diff result.

## Implementation Evidence

Validation performed on 2026-07-22:

- Confirmed AVD schema references against local AVD `v6.3.0`.
- Regenerated `src/solution_arista_avd/protocols.py` from `schemas/`.
- Regenerated `generators/generate_avd_device_inputs_query.py` from `generators/avd_device_hostvar.gql`.
- Checked and loaded schema on Infrahub branch `evpn-gateway-validation`.
- Loaded `menus/menu.yml` on `evpn-gateway-validation`; the `Evpn__Domains` menu node was created.
- Loaded `repository.yml` on `evpn-gateway-validation`.
- Exported `schema.graphql` from Infrahub with `INFRAHUB_BRANCH=evpn-gateway-validation`.
- Ran `uv run pytest tests/unit`: 316 passed.
- Ran `uv run invoke lint`: yamllint, ruff, ruff format check, and mypy passed.
- Ran docs validation from `docs/`: `npm run typecheck` and `npm run build` passed.
- Ran remote integration validation against a copied working-tree snapshot in
  `~/git/infrahub-worktrees/feat-evpn-gateway-snapshot` based on commit
  `fa9525d188cf28e33dccf374ac4f19eaecdad52c` with local modified and untracked
  files overlaid. Command: `uv run pytest tests/integration` with
  `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd`,
  `INFRAHUB_TESTING_IMAGE_VER=1.10.1`,
  `INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1`, and
  `GIT_CONFIG_GLOBAL=/dev/null`. Result: 29 passed, 31 warnings in 1033.03s
  (0:17:13).
- Re-ran branch-first quickstart validation on `evpn-gateway-validation`:
  schema check/load completed with zero validation errors; `repository.yml`,
  `menus/menu.yml`, and `objects/` loaded successfully; the EVPN Services menu
  created `Evpn__Domains`; `generate-fabric`, `generate-pod`, and
  `generate-rack` produced the Fabric-C device topology; transient validation
  data created three `EvpnDomain` objects (`DC1`, `DC2`, `CORE`), assigned
  `infrahub-dc1` and `infrahub-dc2` local domains, promoted one border leaf per
  domain to `border_leaf`, and created `dc1-core` / `dc2-core`
  `EvpnGatewayGroup` objects sharing the CORE remote domain. Hostvar generation
  updated `leaf-infrahub-dc1-1-1` and `leaf-infrahub-dc2-1-1`; the ungrouped
  `leaf-infrahub-dc1-2-1` hostvars were unchanged; structured-config generation
  for `Fabric-C` found 12 devices with hostvars, validated all 12 inputs,
  generated facts for 12 devices, and completed with `0 updated, 12 unchanged,
  0 failed`.
- Added a regression test for generated GraphQL return-type aliases where
  `evpn_l2_enabled`, `evpn_l3_enabled`, and `evpn_l3_inter_domain` are exposed
  on the generated model as `evpn_l_2_enabled`, `evpn_l_3_enabled`, and
  `evpn_l_3_inter_domain`; `uv run pytest
  tests/unit/test_generate_avd_device_hostvar.py` passed with 87 tests.
- Ran required committed-branch integration validation for
  `feat/evpn-gateway` at commit
  `3686b19ebf4d23896eb43a1fc7529baaae1d0216` in isolated remote worktree
  `~/git/infrahub-worktrees/feat-evpn-gateway`. Command:
  `uv run pytest tests/integration` with
  `INFRAHUB_TESTING_DOCKER_IMAGE=opsmill/infrahub-solution-arista-avd`,
  `INFRAHUB_TESTING_IMAGE_VER=1.10.1`,
  `INFRAHUB_TESTING_TASKMGR_BACKGROUND_SVC_REPLICAS=1`, and
  `GIT_CONFIG_GLOBAL=/dev/null`. Result: 29 passed, 31 warnings in 1057.83s
  (0:17:37). This satisfies the required integration validation gate for the
  committed feature revision.
- Ran required generator idempotence validation for
  `generate-avd-device-hostvar` against commit
  `3686b19ebf4d23896eb43a1fc7529baaae1d0216` in the shared live validation lab.
  The lab was rebuilt to a known state, the repository default branch was set to
  `feat/evpn-gateway`, and the task worker-visible `/upstream` commit matched
  the target commit. Validation branch:
  `idempotence-hostvar-20260723-0919`. Scenario: generated Fabric-C topology,
  created `DC1`, `DC2`, and `CORE` `EvpnDomain` objects, assigned local domains
  to `infrahub-dc1` and `infrahub-dc2`, promoted
  `leaf-infrahub-dc1-1-1` and `leaf-infrahub-dc2-1-1` to `border_leaf`, and
  created `dc1-core` / `dc2-core` `EvpnGatewayGroup` objects sharing CORE.
  Snapshot scope: normalized `AvdArtifact` / `AvdHostvarFile` relationship
  identity plus parsed hostvar JSON for `leaf-infrahub-dc1-1-1`,
  `leaf-infrahub-dc2-1-1`, and ungrouped control leaf
  `leaf-infrahub-dc1-2-1`. Result: first corrected run updated the two grouped
  border-leaf hostvars with `evpn_l2.enabled=true`,
  `evpn_l3.enabled=true`, and `evpn_l3.inter_domain=true`; second run reported
  all three hostvars unchanged and the normalized snapshots matched exactly.
