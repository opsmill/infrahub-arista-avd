# Quickstart: EVPN Gateway Domain Validation

## Prerequisites

- Dependencies installed with `uv sync --all-packages`.
- A reachable Infrahub instance configured through `.env`.
- The `border_leaf` role dependency is present before gateway-group implementation.
- EVPN Domain, EVPN Gateway Group, menu, generated protocol, hostvar query/model, and hostvar generator changes have been implemented.

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
- Existing Fabric, Pod, and Device objects remain valid because their extensions are optional.
- `EvpnDomain` and `EvpnGatewayGroup` are present.
- `EvpnGateway` is not present.
- `EvpnDomain.local_gateway_groups` is the Component side of `EvpnGatewayGroup.local_domain`.
- `EvpnGatewayGroup.local_domain` is a required Parent relationship to `EvpnDomain`.
- `EvpnGatewayGroup.pod` is a required Attribute relationship to `NetworkPod`.
- `NetworkPod.evpn_gateway_groups` is an Attribute inverse, not a Component relationship.
- `EvpnGatewayGroup` has no computed or denormalized helper attribute solely to display local-domain data.

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

- `src/solution_arista_avd/protocols.py` includes `EvpnDomain.local_gateway_groups` and `EvpnGatewayGroup.local_domain`.
- The generated hostvar query model includes the target device's `evpn_gateway_group.local_domain`, `evpn_gateway_group.pod.evpn_domain`, `evpn_gateway_group.remote_domain`, and the remote-domain gateway-group traversal.
- Generated files are not hand-edited.

## Repository and Menu Registration

After adding or confirming the menu item, load repository configuration artifacts on the validation branch:

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
- Opening an EVPN Domain shows local gateway group children and remote gateway group references through domain relationships.

## Acceptance Scenario: Domains Without Gateways

On the validation branch, model a Fabric with no EVPN Domains and existing Pods.

Expected outcome:

- The Fabric remains valid.
- Pods may have no `evpn_domain`.
- No Border Leaf receives EVPN Gateway hostvars just because it belongs to the Fabric or Pod.

## Acceptance Scenario: Domain-Owned Gateway Groups

On the validation branch, model this data through the UI or object-loading workflow:

- One Fabric.
- Three `EvpnDomain` objects in the Fabric: two local domains and one remote exchange domain named CORE.
- Two Pods, each assigned to exactly one local `evpn_domain`.
- Two `EvpnGatewayGroup` objects, each created under its parent local `EvpnDomain` through `local_domain`.
- Each gateway group selects the Pod whose `evpn_domain` equals the group's parent `local_domain`.
- Both gateway groups point to the CORE domain as `remote_domain`.
- Each group has one or more `DcimDevice` members with role `border_leaf`, and every member belongs to the group's selected Pod.
- Each group has shared all-active Ethernet Segment identifier and RT import values.

Expected outcome:

- Each group local domain is its parent `EvpnDomain`.
- The selected Pod is context only and does not own the group.
- Each group validates that `pod.evpn_domain` matches `local_domain`.
- Each member Border Leaf is considered an EVPN Gateway through group membership.
- Full-mesh peer intent is derived from valid groups sharing CORE.
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
- `d_path.local_domain_id` is derived from `EvpnGatewayGroup.local_domain.domain_id`.
- `d_path.remote_domain_id` is derived from `EvpnGatewayGroup.remote_domain.domain_id`.
- `remote_peers[].hostname` is derived from valid gateway-group member Border Leafs sharing the same remote domain, excluding members of the target device's own `EvpnGatewayGroup`.
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
- Create a gateway group whose selected Pod has no `evpn_domain`.
- Create a gateway group under local Domain A while selecting a Pod assigned to Domain B.
- Set the group `remote_domain` to the same object as the parent `local_domain`.
- Set the group `remote_domain` to a domain with the same `domain_id` in the same Fabric.
- Create a gateway group without members.
- Model unsupported route-server or route-reflector behavior if any draft field exists.
- Remove Ethernet Segment identifier or RT import values from an all-active group.

Expected outcome:

- Hostvar generation either omits gateway fields for ineligible ungrouped devices or fails before writing hostvars when grouped gateway data is invalid.
- Error messages include the target device, gateway group, failing field or relationship, expected value, and suggested model correction.

## Local Quality Gates

Run focused validation after implementation:

```bash
uv run pytest tests/unit/test_avd.py
uv run pytest tests/unit/test_evpn_gateway_schema_contract.py
uv run pytest tests/unit/test_evpn_gateway_menu_contract.py
uv run pytest tests/unit/test_generate_avd_device_hostvar.py
uv run pytest tests/unit/test_generate_avd_device_structured_config.py
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

## Validation Evidence To Record

Record updated evidence for the Domain-owned model after implementation:

- AVD schema reference version used: `v6.3.0`.
- Schema check/load branch and result.
- Protocol regeneration command and result.
- Hostvar query return-type regeneration command and result.
- Menu load branch and result.
- Positive object scenario showing `EvpnDomain.local_gateway_groups` and `EvpnGatewayGroup.local_domain`.
- Negative object scenarios for Pod/local mismatch and same local/remote domain.
- Focused unit-test commands and results.
- `uv run invoke lint` result.
- Required integration validation report from `$infrahub-run-integration-tests`.
- Required generator idempotence report from `$infrahub-test-generator-idempotence` when live validation is permitted.

Use this format for required validation evidence:

```markdown
- Integration validation: `$infrahub-run-integration-tests`
  - Branch:
  - Commit:
  - Result:
  - Date:

- Generator idempotence validation: `$infrahub-test-generator-idempotence`
  - Branch:
  - Commit:
  - Generator:
  - Snapshot scope:
  - Result:
  - Date:
```

If live idempotence cannot run, document the approved exception:

```markdown
- Generator idempotence validation exception:
  - Reason live validation was not allowed:
  - Approver:
  - Alternative repeated-run evidence:
  - Result:
```

Any validation evidence captured before the 2026-07-23 clarification that derived local domain from `pod.evpn_domain` is superseded and must not be treated as final evidence for this updated model.

## Implementation Evidence

Local and branch-first validation captured on 2026-07-23:

- AVD schema reference version used: `v6.3.0`.
- Checklist validation: `requirements.md` passed with 16/16 items complete.
- Schema validation branch: `evpn-gateway-validation` created successfully.
- Schema check: `uv run infrahubctl schema check schemas/ --branch evpn-gateway-validation` passed.
- Schema load: `uv run infrahubctl schema load schemas/ --branch evpn-gateway-validation` loaded 22 schemas successfully.
- Protocol regeneration: `uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py` succeeded.
- GraphQL schema export: `INFRAHUB_DEFAULT_BRANCH=evpn-gateway-validation uv run infrahubctl graphql export-schema --destination schema.graphql` succeeded.
- Hostvar query return-type regeneration: `uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql --schema schema.graphql` succeeded.
- Menu load: `uv run infrahubctl menu load menus/ --branch evpn-gateway-validation` succeeded and included `Evpn__Domains`.
- Repository load: `uv run infrahubctl object load repository.yml --branch evpn-gateway-validation` succeeded.
- Fabric-C live validation setup: `generate-fabric`, `generate-pod`, and `generate-rack` produced 12 Fabric-C devices on `evpn-gateway-validation`; border rack leaves were updated to `border_leaf` for gateway validation.
- Positive object scenario: created Fabric-C EVPN Domains DC1 (`65100:1`), DC2 (`65100:2`), and CORE (`65200:100`); assigned `infrahub-dc1` to DC1 and `infrahub-dc2` to DC2; created domain-owned gateway groups `DC1-GW` and `DC2-GW` with CORE as the shared `remote_domain`.
- Negative object scenarios: a temporary gateway group owned by DC1 while selecting `infrahub-dc2` failed hostvar generation with `selected pod evpn_domain must match gateway group local_domain`; a temporary gateway group with both `local_domain` and `remote_domain` set to DC1 failed hostvar generation with `remote_domain must differ from local_domain`. Temporary invalid groups were deleted after validation and temporary access-leaf role changes were reverted.
- Hostvar generation: `generate-avd-device-hostvar` succeeded for all four gateway Border Leafs and an ungrouped access leaf. Stored hostvars for `leaf-infrahub-dc1-1-1` included `evpn_gateway` with `d_path.local_domain_id: "65100:1"`, `d_path.remote_domain_id: "65200:100"`, and remote peers `leaf-infrahub-dc2-1-1` and `leaf-infrahub-dc2-1-2`; stored hostvars for ungrouped `leaf-infrahub-dc1-2-1` had no `evpn_gateway` payload.
- Structured-config generation: `uv run infrahubctl generator generate-avd-device-structured-config name=Fabric-C --branch evpn-gateway-validation` found 12 hostvar files, validated all 12 devices, generated AVD facts for 12 devices, and completed with `0 updated, 12 unchanged, 0 failed`.
- Gateway group HFID note: Infrahub rejected local-domain peer attributes in `EvpnGatewayGroup.human_friendly_id` because `EvpnDomain` identifiers are unique per Fabric rather than globally unique; display, ordering, uniqueness, query, and generator validation still use `local_domain`.
- Focused EVPN tests: `uv run pytest tests/unit/test_evpn_gateway_schema_contract.py tests/unit/test_evpn_gateway_menu_contract.py tests/unit/test_evpn_gateway_docs_contract.py tests/unit/test_generate_avd_device_hostvar.py tests/unit/test_hostvar_ordering.py tests/unit/test_generate_avd_device_structured_config.py` passed with 134 tests.
- Full unit suite: `uv run pytest tests/unit` passed with 323 tests.
- Lint suite: `uv run invoke lint` passed.
- Docs typecheck: `npm run typecheck` from `docs/` passed.
- Docs build: `npm run build` from `docs/` passed.
- Remote integration validation and live generator idempotence remain pending until this work is available as a committed branch for the remote validation worktree and idempotence is explicitly approved.
