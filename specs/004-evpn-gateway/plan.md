# Implementation Plan: EVPN Gateway Domains

**Branch**: `feat/evpn-gateway` | **Date**: 2026-07-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-evpn-gateway/spec.md`

## Summary

Update the EVPN Gateway domain model so `EvpnDomain` owns local `EvpnGatewayGroup` children. `EvpnGatewayGroup.local_domain` becomes the required `Parent` relationship to `EvpnDomain`, `EvpnGatewayGroup.pod` becomes a required non-owning `Attribute` relationship to `NetworkPod`, and `EvpnGatewayGroup.remote_domain` remains a required `Attribute` relationship to another `EvpnDomain`. The hostvar generator must derive local D-PATH data from the group's parent local domain, validate that the selected Pod's `evpn_domain` matches that parent, reject same local/remote domain intent, and continue deriving deterministic EVPN Gateway remote peers from groups sharing the selected remote domain.

## Technical Context

**Language/Version**: Infrahub schema YAML `version: "1.0"`; Python `>=3.11,<3.14`; pyAVD `v6.3.0` from the repository constraint `pyavd>=6.3.0,<6.4.0`.

**Primary Dependencies**: Infrahub schema engine and repository loader, `infrahub-sdk>=1.19.0`, generated `src/solution_arista_avd/protocols.py`, generated GraphQL return models, existing `generate-avd-device-hostvar` generator, existing structured-config generator, pyAVD `validate_inputs()`, and the `border_leaf` role mapped to pyAVD `l3leaf`.

**Storage**: Infrahub graph data model loaded from `schemas/`; generated hostvars remain stored as `AvdHostvarFile` under `AvdArtifact`; no external datastore changes.

**Testing**: Schema contract tests, menu contract tests, hostvar generator tests, structured-config peer-resolution tests, hostvar ordering tests, pyAVD input validation tests, schema check/load on an explicit Infrahub branch, protocol regeneration, GraphQL return-type regeneration for `generators/avd_device_hostvar.gql`, `uv run invoke lint`, `$infrahub-run-integration-tests`, and `$infrahub-test-generator-idempotence` for the hostvar generator change when live validation is allowed.

**Target Platform**: Infrahub repository running through branch-based schema validation and the existing AVD hostvar/structured-config pipeline.

**Project Type**: Infrahub reference-design repository with schema-defined data model, Python generators, GraphQL queries, custom menus, object data, tests, and Docusaurus documentation.

**Performance Goals**: Not throughput-bound. Peer derivation must be deterministic, sorted by peer hostname, and resolved from the gateway group's `remote_domain.remote_gateway_groups` traversal without broad per-device follow-up API calls.

**Constraints**: `EvpnGatewayGroup` may have only one `Parent` relationship, and that parent must be `local_domain -> EvpnDomain`; `pod` must not own gateway groups; `NetworkPod.evpn_gateway_groups` must be a non-owning inverse relationship; `pod.evpn_domain` must match `local_domain`; `remote_domain` must differ from `local_domain`; all relationship peers use full kinds; bidirectional relationships use matching identifiers; uniqueness constraints use `__value` for attributes and bare relationship names for relationships; new custom-menu schema nodes use `include_in_menu: false`; no dedicated `EvpnGateway` node; no dedicated Infrahub check; no route-server or route-reflector model; no manually modeled peer objects; hostname-only remote peers require all gateway member hostvars to exist before structured-config generation; only `all_active_multihoming` is actionable in this phase.

**Scale/Scope**: Update the EVPN gateway schema, generated protocols, hostvar GraphQL query and generated model, hostvar generator validation, menu/domain relationship documentation, tests, quickstart, and validation evidence expectations. Existing object data, tests, and docs that still assume Pod-owned gateway groups must be corrected. Service-portal workflows, new generator definitions, dedicated checks, route-server/route-reflector behavior, a direct EVPN Gateway Groups menu entry, and non-all-active resiliency models are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Schema-Driven Architecture**: PASS. The plan changes schema ownership first and requires protocols/query models to be regenerated before Python code consumes the changed relationships.
- **Idempotent Operations**: PASS. The feature extends existing generator behavior and preserves deterministic hostvar output; repeated-run validation is required for the changed hostvar generator.
- **Type Safety**: PASS. The plan requires regenerated `protocols.py` and regenerated GraphQL return models before production code uses `local_domain`.
- **Test-Required Quality**: PASS. The plan includes schema, generator, pyAVD, unit, lint, integration, and generator idempotence validation.
- **Convention-Based Structure**: PASS. Planned files follow existing `schemas/evpn/`, `generators/`, `menus/`, `tests/unit/`, `objects/`, and `docs/docs/` conventions.

No constitution violations require complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-evpn-gateway/
+-- plan.md
+-- research.md
+-- data-model.md
+-- quickstart.md
+-- contracts/
|   +-- schema-contract.md
|   +-- hostvar-contract.md
|   +-- validation-contract.md
|   +-- menu-contract.md
+-- checklists/
    +-- requirements.md
```

### Source Code (repository root)

```text
schemas/
+-- evpn/
|   +-- evpn_gateway.yml
+-- dcim_extensions.yml

generators/
+-- avd_device_hostvar.gql
+-- generate_avd_device_hostvar.py
+-- generate_avd_device_inputs_query.py
+-- generate_avd_device_structured_config.py

src/solution_arista_avd/
+-- avd.py
+-- protocols.py

menus/
+-- menu.yml

objects/
+-- *.yml

tests/
+-- unit/
    +-- test_avd.py
    +-- test_evpn_gateway_schema_contract.py
    +-- test_evpn_gateway_menu_contract.py
    +-- test_evpn_gateway_docs_contract.py
    +-- test_generate_avd_device_hostvar.py
    +-- test_generate_avd_device_structured_config.py
    +-- test_hostvar_ordering.py

docs/docs/
+-- supported-capabilities.md
+-- developer-guide/
    +-- schemas.md
    +-- generators.md
    +-- avd/
        +-- hostvars.md
        +-- role-mapping.md
```

**Structure Decision**: Keep the model in `schemas/evpn/evpn_gateway.yml`, but change ownership from Pod-first to Domain-first. Extend the existing per-device hostvar generator instead of adding a generator definition. Use schema constraints plus generator-side validation instead of a dedicated Infrahub check. Keep one custom EVPN Services Domains menu entry for `EvpnDomain`; `EvpnGatewayGroup` remains discoverable from EVPN Domain local/remote relationship views rather than from its own sidebar item.

## Complexity Tracking

No constitution violations are present.

## Phase 0 Research

Completed in [research.md](research.md). All technical-context questions are resolved with concrete decisions and no remaining clarification markers.

## Phase 1 Design

Completed artifacts:

- [data-model.md](data-model.md): schema entities, relationships, validation states, and derived hostvar values.
- [contracts/schema-contract.md](contracts/schema-contract.md): schema kinds, attributes, relationships, display, uniqueness, and migration contract.
- [contracts/hostvar-contract.md](contracts/hostvar-contract.md): GraphQL and pyAVD hostvar emission contract for Border Leaf gateway-group members.
- [contracts/validation-contract.md](contracts/validation-contract.md): no-dedicated-check scope and generator-side validation contract.
- [contracts/menu-contract.md](contracts/menu-contract.md): EVPN Services Domains menu contract.
- [quickstart.md](quickstart.md): branch-first validation guide and end-to-end acceptance scenarios.

## Constitution Check Re-Evaluation

- **Schema-Driven Architecture**: PASS. Design artifacts define the Domain-owned relationship model before generator consumers and menu exposure.
- **Idempotent Operations**: PASS. Hostvar generation remains in the existing stored-artifact flow and must be validated with repeated-run/idempotence checks.
- **Type Safety**: PASS. The contracts require protocol and GraphQL return-type regeneration before code changes are considered complete.
- **Test-Required Quality**: PASS. Quickstart includes schema validation, generator-side validation, pyAVD/unit validation, lint, integration validation, and generator idempotence validation.
- **Convention-Based Structure**: PASS. Planned file locations, names, kinds, dropdown choices, relationship identifiers, menu structure, and docs match repository conventions.

No unresolved clarifications or gate failures remain.
