# Implementation Plan: EVPN Gateway Domains

**Branch**: `feat/evpn-gateway` | **Date**: 2026-07-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-evpn-gateway/spec.md`

## Summary

Replace the earlier per-device `EvpnGateway` draft with a schema-first EVPN Domain and EVPN Gateway Group model. A `NetworkFabric` owns zero or more `EvpnDomain` objects, each `NetworkPod` belongs to zero or one local EVPN Domain, and an `EvpnGatewayGroup` defined for one Pod activates gateway behavior for its member `border_leaf` devices. The hostvar generator derives each member Border Leaf's local domain from the group's Pod, remote domain from the group, shared EVPN L2/L3, D-PATH, and all-active Ethernet Segment settings from the group, and a deterministic full-mesh remote peer list from all gateway groups sharing the same remote EVPN Domain. No dedicated `EvpnGateway` node and no dedicated Infrahub check are part of this design.

## Technical Context

**Language/Version**: Infrahub schema YAML `version: "1.0"`; Python `>=3.11,<3.14`; pyAVD `v6.3.0` from the repository constraint `pyavd>=6.3.0,<6.4.0`.

**Primary Dependencies**: Infrahub schema engine and repository loader, `infrahub-sdk>=1.19.0`, generated `src/solution_arista_avd/protocols.py`, generated GraphQL return models, existing `generate-avd-device-hostvar` generator, pyAVD `validate_inputs()`, and the `border_leaf` role from PR #74 / `feat/dci-links`.

**Storage**: Infrahub graph data model loaded from `schemas/`; generated hostvars continue to be stored as `AvdHostvarFile` under `AvdArtifact`; no external datastore changes.

**Testing**: Schema contract tests, menu contract tests, hostvar generator tests, hostvar ordering tests, pyAVD input validation tests, a fabric-level pyAVD smoke path that proves hostname-only EVPN Gateway remote peers resolve through aggregated hostvars, schema check/load on an explicit Infrahub branch, protocol regeneration, GraphQL return-type regeneration for `generators/avd_device_hostvar.gql`, `uv run invoke lint`, `$infrahub-run-integration-tests`, and `$infrahub-test-generator-idempotence` for the hostvar generator change when live validation is allowed.

**Target Platform**: Infrahub repository running through branch-based schema validation and the existing AVD hostvar/structured-config pipeline.

**Project Type**: Infrahub reference-design repository with schema-defined data model, Python generators, GraphQL queries, custom menus, and Docusaurus documentation.

**Performance Goals**: Not throughput-bound. Full-mesh peer derivation must be deterministic, sorted by peer hostname, and derived from the target device's gateway group plus that group's remote-domain inverse relationships without broad per-device follow-up API calls.

**Constraints**: Additive schema migration for existing Fabric, Pod, and Device data; remove/replace any earlier `EvpnGateway` node draft; reuse `border_leaf` exactly as defined by PR #74 and map it to pyAVD `l3leaf`; no route-server or route-reflector remote-domain model; no manually modeled peer objects; hostname-only remote peers require every gateway member hostvar to exist before structured-config generation; one remote EVPN Domain per gateway group; only `all_active_multihoming` is actionable in this phase; gateway group identity/display must not add computed or denormalized helper attributes solely to expose the Pod-derived local EVPN Domain; all relationship peers use full kinds; bidirectional relationships use matching identifiers; custom-menu nodes use `include_in_menu: false`.

**Scale/Scope**: Two concrete EVPN nodes, three existing-node relationship extensions, one existing generator query/class extension, generated models/protocols, one EVPN Services Domains menu entry, focused tests, and related developer documentation. Dedicated Infrahub checks, service-portal workflows, object seed data, route-server/route-reflector behavior, a direct EVPN Gateway Groups menu entry, and non-all-active resiliency models are out of scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Schema-Driven Architecture**: PASS. The plan defines `EvpnDomain`, `EvpnGatewayGroup`, and required extensions before generators, menus, or docs consume them.
- **Idempotent Operations**: PASS. The feature extends the existing hostvar generator and stored-file update path. Generator changes require deterministic ordering and repeated-run validation; no new mutable generator target is introduced.
- **Type Safety**: PASS. Schema changes require regenerated protocols, and GraphQL query changes require regenerated `*_query.py` models before production code consumes new fields.
- **Test-Required Quality**: PASS. The plan includes schema, generator, pyAVD, unit, lint, integration, and generator idempotence validation.
- **Convention-Based Structure**: PASS. Planned files follow existing `schemas/evpn/`, `generators/`, `menus/`, `tests/unit/`, and `docs/docs/` conventions.

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
|   +-- evpn_services.yml
|   +-- evpn_gateway.yml          # replace stale EvpnGateway draft with EvpnGatewayGroup model
+-- dcim_extensions.yml           # dependency source for border_leaf from feat/dci-links

generators/
+-- avd_device_hostvar.gql
+-- generate_avd_device_hostvar.py
+-- generate_avd_device_inputs_query.py

src/solution_arista_avd/
+-- avd.py
+-- protocols.py

menus/
+-- menu.yml

tests/
+-- unit/
    +-- test_avd.py
    +-- test_evpn_gateway_schema_contract.py
    +-- test_evpn_gateway_menu_contract.py
    +-- test_generate_avd_device_hostvar.py
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

**Structure Decision**: Implement the model in `schemas/evpn/evpn_gateway.yml` to keep EVPN gateway-domain intent next to the existing EVPN service schemas, but replace the earlier `EvpnGateway` node with `EvpnGatewayGroup`. Extend the existing per-device hostvar generator instead of adding a new generator definition. Use schema constraints plus generator-side validation instead of adding an Infrahub check. Add one custom menu item for `EvpnDomain` under EVPN Services and keep `EvpnGatewayGroup` discoverable from EVPN Domain relationship views rather than from its own menu entry.

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

- **Schema-Driven Architecture**: PASS. Design artifacts define schema nodes and extensions before generator consumers and menu exposure.
- **Idempotent Operations**: PASS. Hostvar generation remains in the existing stored-artifact flow and must be validated with repeated-run/idempotence checks.
- **Type Safety**: PASS. The contracts require protocol and GraphQL return-type regeneration before code changes are considered complete.
- **Test-Required Quality**: PASS. Quickstart includes schema validation, generator-side validation, pyAVD/unit validation, lint, integration validation, and generator idempotence validation.
- **Convention-Based Structure**: PASS. Planned file locations, names, kinds, dropdown choices, relationship identifiers, menu structure, and docs match repository conventions.

No unresolved clarifications or gate failures remain.
