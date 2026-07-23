# Schema Design Specification: EVPN Gateway Domains

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate all schema definitions.

**Feature Branch**: `feat/evpn-gateway`
**Created**: 2026-07-20
**Status**: Draft
**Input**: User description: "Update the EVPN Gateway model so EvpnDomain owns local EvpnGatewayGroup children. EvpnGatewayGroup.local_domain is the Parent relationship to EvpnDomain, EvpnGatewayGroup.remote_domain remains an Attribute relationship to another EvpnDomain, and EvpnGatewayGroup.pod becomes an Attribute relationship to NetworkPod. The group local domain is its parent EvpnDomain. The group pod must have the same evpn_domain as the group local_domain. The remote_domain must differ from local_domain. Update schema, generated protocols, hostvar query/model, generator validation, menu/domain relationship docs, tests, quickstart, and validation evidence accordingly."

## Clarifications

### Session 2026-07-22

- Q: Should `EvpnGatewayGroup` HFID/display add computed or denormalized helper attributes solely to show the local EVPN Domain? -> A: No; use schema-valid native fields for identity/display.

### Session 2026-07-23

- Q: What is the source of truth for a gateway group's local EVPN Domain? -> A: `EvpnGatewayGroup.local_domain` is the required Parent relationship to `EvpnDomain`; the local domain is the parent domain, not an independently selected attribute and not only inferred from the selected Pod.
- Q: How must the selected Pod relate to the local domain? -> A: `EvpnGatewayGroup.pod` is a required Attribute relationship to `NetworkPod`, and that Pod's `evpn_domain` must match the group's parent `local_domain`.
- Q: Can a group use its local EVPN Domain as the remote EVPN Domain? -> A: No; `EvpnGatewayGroup.remote_domain` remains a required Attribute relationship to another `EvpnDomain` and must differ from `local_domain`.

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

The expected schema home for this feature is the EVPN service schema area. The data model must use EVPN Domain and EVPN Gateway Group concepts, plus extensions on existing Fabric, Pod, and Device nodes. A per-device `EvpnGateway` node is explicitly out of scope; a Border Leaf becomes an EVPN Gateway when it is a member of an EVPN Gateway Group.

`EvpnDomain` owns local `EvpnGatewayGroup` children. `EvpnGatewayGroup.local_domain` is the group's Parent relationship to `EvpnDomain`, `EvpnGatewayGroup.remote_domain` is an Attribute relationship to another `EvpnDomain`, and `EvpnGatewayGroup.pod` is an Attribute relationship to `NetworkPod`. The selected Pod must have the same `evpn_domain` as the group's parent `local_domain`, and the selected `remote_domain` must differ from `local_domain`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Model EVPN Domains Across a Fabric (Priority: P1)

As a network designer, I need a Fabric to contain zero or more EVPN Domains and each Pod to belong to at most one EVPN Domain so that gateway intent has a clear domain boundary without forcing every Pod into EVPN Gateway behavior.

**Why this priority**: Domain membership is the foundation for gateway grouping, local-domain ownership, and inter-domain peering.

**Independent Test**: Load the schema and model a Fabric with no EVPN Domains, then model the same Fabric with multiple EVPN Domains and Pods assigned to only one domain each.

**Acceptance Scenarios**:

1. **Given** a Fabric has no EVPN Gateway-enabled Border Leafs, **When** the Fabric is modeled, **Then** it may have zero EVPN Domains and its Pods may have no EVPN Domain relationship.
2. **Given** a Fabric has multiple EVPN Domains, **When** a Pod is assigned to a domain, **Then** the Pod is related to exactly one EVPN Domain and the Fabric can list all of its domains.
3. **Given** an operator attempts to assign a Pod to multiple EVPN Domains, **When** the intent is validated or reviewed, **Then** the model prevents or reports the invalid multi-domain Pod assignment.

---

### User Story 2 - Own Gateway Groups From Local Domains (Priority: P2)

As a network designer, I need each EVPN Domain to own its local EVPN Gateway Groups so that users can start from a domain and see the gateway groups that originate from that domain.

**Why this priority**: Local-domain ownership is the core relationship model for this update. Downstream gateway configuration, validation, generated types, documentation, and navigation must align with this ownership direction.

**Independent Test**: Model one EVPN Domain with two local EVPN Gateway Group children. Confirm each group has that EVPN Domain as its parent `local_domain`, each group still selects a Pod as context, and no group is owned by a Pod.

**Acceptance Scenarios**:

1. **Given** an EVPN Domain exists, **When** a local gateway group is created under that domain, **Then** the group has that EVPN Domain as its required `local_domain`.
2. **Given** a gateway group exists, **When** a reviewer inspects its local domain, **Then** the value is the group's parent EVPN Domain and not a separately selected attribute.
3. **Given** an existing draft model where the Pod owns gateway groups, **When** the model is updated, **Then** ownership moves to EVPN Domain while the selected Pod remains available as non-owning context.

---

### User Story 3 - Validate Gateway Pod and Domain Consistency (Priority: P3)

As a network designer, I need the gateway group's selected Pod to match the group's parent local EVPN Domain so that generated gateway intent cannot combine a local domain with an unrelated Pod.

**Why this priority**: A gateway group is valid only when its parent local domain and selected Pod agree. This prevents invalid D-PATH local-domain values and misleading domain navigation.

**Independent Test**: Model a Pod assigned to EVPN Domain A. Create a gateway group under Domain A with that Pod and confirm it is valid. Attempt to use the same Pod under Domain B and confirm the invalid relationship is rejected or reported before gateway hostvars are accepted.

**Acceptance Scenarios**:

1. **Given** a Pod belongs to the same EVPN Domain that owns a gateway group, **When** the gateway group is validated, **Then** the group is accepted as locally consistent.
2. **Given** a Pod belongs to a different EVPN Domain than the one owning the gateway group, **When** the gateway group is validated, **Then** the group is rejected or reported with an actionable error.
3. **Given** a Pod has no EVPN Domain, **When** it is selected for a gateway group, **Then** validation reports that the Pod must belong to the group's local domain.

---

### User Story 4 - Keep Remote Domains Separate and Derive Peers (Priority: P4)

As a network designer, I need the gateway group's remote EVPN Domain to remain a separate relationship to another EVPN Domain so that inter-domain peering is always between distinct domains.

**Why this priority**: Same-domain gateway groups would produce invalid local and remote domain IDs and incorrect peer derivation.

**Independent Test**: Create a gateway group under local Domain A. Select Domain B as remote and confirm it is valid. Select Domain A as remote and confirm validation reports the conflict. Model multiple gateway groups that share remote Domain B and confirm peer intent derives from the shared remote domain.

**Acceptance Scenarios**:

1. **Given** a gateway group is owned by local Domain A, **When** remote Domain B is selected, **Then** the group can derive distinct local and remote domain IDs.
2. **Given** a gateway group is owned by local Domain A, **When** local Domain A is also selected as the remote domain, **Then** the configuration is rejected or reported as invalid.
3. **Given** multiple valid gateway groups share the same remote EVPN Domain, **When** peer intent is derived, **Then** peers are selected from valid groups sharing that remote domain while preserving each group's own local parent domain.
4. **Given** an operator attempts to model route servers or route reflectors in the remote EVPN Domain, **When** the intent is reviewed, **Then** the feature reports that only full-mesh gateway peering is supported in this phase.

---

### User Story 5 - Align Generated Data, Navigation, and Evidence (Priority: P5)

As a reviewer, I need generated model surfaces, gateway validation, domain relationship documentation, quickstart steps, tests, and validation evidence to reflect the new ownership model so that future changes do not regress to Pod-owned local gateway groups.

**Why this priority**: The schema change is incomplete unless consumers and evidence use the same relationship semantics.

**Independent Test**: Review generated type surfaces, hostvar data retrieval, validation behavior, domain relationship documentation, quickstart evidence, and tests. Confirm each refers to `local_domain` parent ownership and no longer treats `pod` as the group parent.

**Acceptance Scenarios**:

1. **Given** generated model surfaces are refreshed, **When** a reviewer inspects gateway group relationships, **Then** `local_domain`, `remote_domain`, and `pod` have the expected ownership and attribute semantics.
2. **Given** gateway hostvars are derived, **When** a grouped Border Leaf is processed, **Then** the local EVPN Domain comes from the group's parent domain and validation confirms the selected Pod belongs to that same domain.
3. **Given** the custom EVPN Services menu is loaded, **When** a user opens an EVPN Domain, **Then** the user can discover both local gateway group children and remote gateway group references from the domain perspective.
4. **Given** repository documentation and quickstart evidence are reviewed, **When** the EVPN Gateway workflow is followed, **Then** domain-first navigation and validation examples match the updated model.

### Edge Cases

- A Fabric has zero EVPN Domains and existing Pods remain valid.
- A Pod is assigned to more than one EVPN Domain.
- A gateway group exists under an EVPN Domain but its selected Pod has no EVPN Domain.
- A gateway group exists under an EVPN Domain but its selected Pod belongs to a different EVPN Domain.
- A gateway group selects its parent local EVPN Domain as its remote EVPN Domain.
- A remote EVPN Domain is used by gateway groups from multiple different local EVPN Domains.
- Existing object data, tests, or docs still assume gateway groups are Pod-owned children.
- Domain relationship views expose remote gateway groups but omit local gateway group children.
- Generated hostvar inputs still traverse only the Pod path for local-domain ownership.
- Generated protocol or query-model surfaces still describe `pod` as a Parent relationship.
- A non-Border Leaf device is added to an EVPN Gateway Group.
- A Border Leaf is added to more than one EVPN Gateway Group in this phase.
- An EVPN Gateway Group has no Border Leaf members.
- Multiple gateway groups share a remote EVPN Domain and must derive a deterministic full-mesh peer set.
- A remote EVPN Domain exists without any Pods, such as a CORE domain used only for inter-domain route exchange.
- The EVPN Services menu contains a direct EVPN Gateway Groups or Gateways tab instead of requiring Domain-first navigation.
- A remote EVPN Domain is modeled with route server or route reflector behavior.
- Existing Fabric, Pod, Device, and EVPN service data is present when the schema relationship ownership changes.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST continue to define `EvpnDomain` and `EvpnGatewayGroup` as concrete nodes under the `Evpn` namespace.
- **FR-002**: Schema MUST NOT define or require a dedicated `EvpnGateway` node; an EVPN Gateway is a `DcimDevice` with role `border_leaf` that belongs to an EVPN Gateway Group.
- **FR-003**: `EvpnDomain` MUST represent a named EVPN Domain inside a Fabric. A domain can be used as a local Pod domain, as an owner of local gateway groups, as a remote exchange domain, or any valid combination of those roles.
- **FR-004**: `EvpnGatewayGroup` MUST represent a group of Border Leaf devices that share one gateway configuration profile, one local parent EVPN Domain, one selected Pod, and one remote EVPN Domain.
- **FR-005**: No new generic is required unless planning identifies reusable domain or gateway group attributes shared by more than one future EVPN service kind.
- **FR-006**: All node names MUST be PascalCase and all namespaces MUST follow the existing project namespace conventions.

#### Attributes

- **FR-010**: `EvpnDomain` MUST have a required `name` Text attribute and a required `domain_id` Text attribute.
- **FR-011**: `EvpnDomain.domain_id` MUST accept colon-delimited values used for EVPN domain identifiers and MUST be unique within the related Fabric.
- **FR-012**: `EvpnGatewayGroup` MUST have a required `name` Text attribute.
- **FR-013**: `EvpnGatewayGroup` MUST have a `resiliency_model` Dropdown attribute. The supported actionable value for this phase is `all_active_multihoming`.
- **FR-014**: `EvpnGatewayGroup` MUST carry the shared EVPN gateway enablement settings required by all member Border Leafs:
  `evpn_l2.enabled`, `evpn_l3.enabled`, `evpn_gateway.enabled`, and D-PATH enabled. BGP peering between EVPN Gateway
  (`pyavd` hostvars `l3leaf.nodes[].evpn_gateway.remote_peers`) for this phase is derived by gateway membership and the
  selected `remote_domain`: an EVPN Gateway MUST have BGP peering with all other EVPN Gateways in that remote domain that
  are not part of the same `EvpnGatewayGroup`. No separate route-server, route-reflector, peer IP, or peer ASN setting is supported.
- **FR-015**: `EvpnGatewayGroup` MUST carry shared all-active multihoming settings, including Ethernet Segment identifier and Ethernet Segment route-target import value.
- **FR-016**: All-active multihoming and Ethernet Segment settings MUST be modeled so they are applicable only when `resiliency_model` is `all_active_multihoming`.
- **FR-017**: New attributes added to existing nodes MUST be optional or provide defaults so existing loaded data remains valid after schema migration.
- **FR-018**: All attribute names MUST be snake_case and all attribute kinds MUST use current Infrahub kinds such as Text, Boolean, Dropdown, and Number.

#### Relationships

- **FR-020**: `NetworkFabric` MUST be able to relate to zero or more `EvpnDomain` objects.
- **FR-021**: Each `EvpnDomain` MUST relate to exactly one `NetworkFabric`.
- **FR-022**: `NetworkPod` MUST relate to zero or one `EvpnDomain`.
- **FR-023**: Each `EvpnDomain` MUST be able to list the Pods that are assigned to that domain.
- **FR-024**: `EvpnGatewayGroup.local_domain` MUST be a required cardinality-one Parent relationship to `EvpnDomain`.
- **FR-025**: The inverse relationship from `EvpnDomain` to local gateway groups MUST identify gateway groups owned by that domain as children.
- **FR-026**: `EvpnGatewayGroup.remote_domain` MUST remain a required cardinality-one Attribute relationship to `EvpnDomain`.
- **FR-027**: The inverse relationship from `EvpnDomain` to remote gateway groups MUST continue to identify gateway groups that use the domain as their remote exchange domain.
- **FR-028**: `EvpnGatewayGroup.pod` MUST be a required cardinality-one Attribute relationship to `NetworkPod`.
- **FR-029**: The inverse relationship from `NetworkPod` to gateway groups MUST be a non-owning relationship that reflects selected group context, not child ownership.
- **FR-030**: The `NetworkPod` selected by an `EvpnGatewayGroup` MUST have the same `evpn_domain` as the group's parent `local_domain`.
- **FR-031**: The `remote_domain` selected by an `EvpnGatewayGroup` MUST differ from the group's parent `local_domain`.
- **FR-032**: `EvpnGatewayGroup` MUST relate to one or more `DcimDevice` members that act as EVPN Gateways.
- **FR-033**: Member devices of an `EvpnGatewayGroup` MUST be eligible only when their role is `border_leaf`.
- **FR-034**: All member devices of an `EvpnGatewayGroup` MUST belong to the group's selected `pod`.
- **FR-035**: A `DcimDevice` MUST be able to expose whether it belongs to an EVPN Gateway Group so gateway activation can be derived from device membership.
- **FR-036**: A Border Leaf MUST belong to at most one EVPN Gateway Group in this phase.
- **FR-037**: EVPN Gateway full-mesh peer sets MUST be derivable from enabled Border Leaf member devices whose gateway groups share the same `remote_domain`, excluding devices in the same `EvpnGatewayGroup` as the target gateway. An enabled Border Leaf gateway means a `DcimDevice` with role `border_leaf` that is a member of exactly one valid `EvpnGatewayGroup` and passes generator-side gateway eligibility validation.
- **FR-038**: The schema MUST NOT require manually modeled remote peer relationships between individual gateways for this phase.
- **FR-039**: All bidirectional relationships MUST use matching `identifier` values on both sides, and all relationship `peer` values MUST use full schema kinds such as `NetworkFabric`, `NetworkPod`, `DcimDevice`, and `EvpnDomain`.

#### Display & Identification

- **FR-040**: `EvpnDomain` MUST define a human-friendly identifier and display label that let operators distinguish domains by Fabric and domain ID.
- **FR-041**: `EvpnDomain` display and relationship views MUST make both local gateway group children and remote gateway group references discoverable.
- **FR-042**: `EvpnGatewayGroup` MUST define schema-valid identity and display surfaces that distinguish the selected Pod, remote domain, and group name in HFID/display metadata, and MUST make the local parent domain distinguishable through the `EvpnDomain.local_gateway_groups` relationship view when Infrahub HFID constraints prevent using the parent domain directly.
- **FR-043**: Gateway group identity and reviewer navigation MUST no longer depend on Pod ownership; the parent `local_domain` relationship is authoritative even when the HFID/display fallback uses Pod, remote domain, and group name.
- **FR-044**: The EVPN Services menu MUST contain a Domains tab linked to `EvpnDomain`.
- **FR-045**: The EVPN Services menu MUST NOT contain a direct Gateways or EVPN Gateway Groups tab linked to `EvpnGatewayGroup`; users MUST explore an EVPN Domain to reach its local and remote EVPN Gateway Groups.
- **FR-046**: `EvpnDomain` and `EvpnGatewayGroup` MUST avoid duplicate automatic menu entries when the custom EVPN Services menu is used.
- **FR-047**: Documentation explaining EVPN Domains and gateway group relationships MUST distinguish local-domain ownership from remote-domain reference usage.
- **FR-048**: Attributes and relationships MUST use order weights consistent with the existing EVPN service schemas so Fabric, domain, group, Pod, member, resiliency, and Ethernet Segment fields appear in a predictable order.

#### Uniqueness Constraints

- **FR-050**: `EvpnDomain` MUST prevent duplicate domain names within the same Fabric.
- **FR-051**: `EvpnDomain` MUST prevent duplicate `domain_id` values within the same Fabric.
- **FR-052**: `EvpnGatewayGroup` MUST prevent duplicate group names within the same selected Pod and local EVPN Domain.
- **FR-053**: The model MUST prevent or report a Border Leaf being assigned to more than one EVPN Gateway Group in this phase.
- **FR-054**: Uniqueness constraints MUST use `__value` suffixes for attribute references and bare relationship names for relationship references.

#### Migration

- **FR-060**: Schema changes MUST be additive for existing Fabric, Pod, Device, and EVPN service data whenever possible.
- **FR-061**: Existing draft schema, object data, tests, and documentation that model `EvpnGatewayGroup.pod` as the Parent relationship MUST be updated to the new local-domain parent model.
- **FR-062**: Existing gateway groups can be migrated only when their selected Pod has an EVPN Domain and that domain can become the group's parent `local_domain`.
- **FR-063**: Any gateway group whose selected Pod has no EVPN Domain, whose selected Pod belongs to a different local domain, or whose remote domain equals its local domain MUST be reported as invalid before generated gateway intent is accepted.
- **FR-064**: Schema validation and protocol regeneration MUST be part of the implementation plan after the schema relationship ownership changes.

#### Hostvars & Generated Model Scope

- **FR-070**: EVPN Gateway hostvars MUST be emitted only for devices with role `border_leaf` that are members of a valid EVPN Gateway Group.
- **FR-071**: Devices with role `leaf`, `l2leaf`, `spine`, or `super_spine` MUST NOT receive EVPN Gateway hostvars even when they share the same Pod, Fabric, local EVPN Domain, or remote EVPN Domain.
- **FR-072**: Every Border Leaf in an EVPN Gateway Group MUST receive the group's shared EVPN L2/L3, D-PATH, resiliency, and all-active Ethernet Segment values.
- **FR-073**: Hostvar data retrieval MUST include the gateway group's parent `local_domain`, selected `remote_domain`, selected `pod`, Pod EVPN Domain, member devices, and remote-domain peer candidate groups.
- **FR-074**: Generated query models MUST expose the updated relationship semantics without stale Pod-parent ownership assumptions.
- **FR-075**: Every Border Leaf in an EVPN Gateway Group MUST resolve its local EVPN Domain from `EvpnGatewayGroup.local_domain`.
- **FR-076**: Gateway hostvar validation MUST confirm `EvpnGatewayGroup.pod.evpn_domain` matches `EvpnGatewayGroup.local_domain` before writing gateway-specific intent.
- **FR-077**: Gateway hostvar validation MUST confirm `EvpnGatewayGroup.remote_domain` differs from `EvpnGatewayGroup.local_domain` before writing gateway-specific intent.
- **FR-078**: Every Border Leaf in an EVPN Gateway Group MUST derive its remote peer hostname list from enabled Border Leaf gateways whose groups share the same `remote_domain` and are not part of the same `EvpnGatewayGroup`.
- **FR-079**: Border Leaf devices that are not members of an EVPN Gateway Group MUST continue to generate their existing Border Leaf hostvars without EVPN Gateway-specific fields.
- **FR-080**: Route server and route reflector models in the remote EVPN Domain MUST NOT be supported in this phase; only full-mesh gateway peering is supported.

#### Validation & Evidence Scope

- **FR-090**: This feature MUST NOT require a dedicated Infrahub check when schema constraints and generator-side eligibility rules can enforce or report the required behavior.
- **FR-091**: Generator-side eligibility rules MUST report actionable errors for gateway intent that cannot be fully constrained by schema relationships or attribute definitions before EVPN Gateway-specific hostvars are emitted.
- **FR-092**: Validation or generation MUST report Pods without EVPN Domain assignment, Pod/domain mismatches, local and remote domain conflicts, non-Border Leaf members, members from a different Pod than the gateway group, unsupported route-server models, and gateway groups without member devices.
- **FR-093**: Unit tests MUST cover schema relationship kinds, relationship identifiers, uniqueness, display and navigation assumptions, generated model expectations, hostvar local-domain derivation, Pod/domain mismatch validation, and same local/remote domain validation.
- **FR-094**: Quickstart instructions MUST include a positive validation scenario where a gateway group's parent local domain matches its selected Pod EVPN Domain.
- **FR-095**: Quickstart instructions MUST include negative validation scenarios for Pod/domain mismatch and identical local/remote domains.
- **FR-096**: Validation evidence MUST record schema validation, protocol regeneration, generated query-model refresh, focused unit tests, repository linting, required Infrahub integration testing, and generator idempotence validation when live validation is permitted.

### Key Entities

- **EvpnDomain**: Represents one EVPN Domain inside a Fabric. Key data includes name, domain ID, Fabric relationship, optional Pod membership, local gateway group children, and remote gateway group references.
- **EvpnGatewayGroup**: Represents a group of Border Leaf devices acting as EVPN Gateways. Key data includes name, parent local EVPN Domain, selected Pod, remote EVPN Domain, Border Leaf members, shared resiliency model, EVPN L2/L3 and D-PATH settings, and all-active Ethernet Segment values.
- **NetworkFabric**: Existing Fabric entity that owns zero or more EVPN Domains.
- **NetworkPod**: Existing Pod entity that may belong to one EVPN Domain. A Pod selected by an EVPN Gateway Group must belong to the group's parent local EVPN Domain.
- **DcimDevice**: Existing device entity. A device becomes an EVPN Gateway only when it has role `border_leaf` and belongs to a valid EVPN Gateway Group.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema validation completes with zero errors after the gateway group owner changes from Pod to EVPN Domain.
- **SC-002**: A reviewer can model a Fabric with zero EVPN Domains and confirm existing Pods remain valid without gateway intent.
- **SC-003**: A reviewer can model one Fabric with at least three EVPN Domains, including two local domains and one shared remote CORE domain, without assigning any Pod to more than one domain.
- **SC-004**: A reviewer can create at least two EVPN Gateway Groups under one local EVPN Domain and confirm both appear as local children of that domain.
- **SC-005**: A reviewer can select a Pod for a gateway group only when validation confirms the Pod's EVPN Domain matches the group's parent local domain.
- **SC-006**: A reviewer cannot approve or generate gateway intent for a gateway group whose remote domain equals its local parent domain.
- **SC-007**: Generated gateway hostvars for valid Border Leaf members use the group's parent local domain ID for local D-PATH behavior and the selected remote domain ID for remote D-PATH behavior.
- **SC-008**: The model clearly distinguishes Border Leafs that are EVPN Gateways through group membership, Border Leafs that are not gateways, and non-Border Leaf devices that must never receive gateway configuration.
- **SC-009**: For every modeled gateway group sharing a remote EVPN Domain, the full-mesh peer set can be resolved as enabled Border Leaf gateways sharing that remote domain, excluding members of the same `EvpnGatewayGroup`.
- **SC-010**: Tests fail against the old Pod-parent relationship model and pass against the EVPN Domain-parent model.
- **SC-011**: Domain relationship documentation and quickstart examples show both local gateway group children and remote gateway group references from the EVPN Domain perspective.
- **SC-012**: The EVPN Services menu contains exactly one Domains tab for EVPN Domains, contains no direct Gateways or EVPN Gateway Groups tab, and lets a reviewer reach gateway group relationships from an EVPN Domain view.
- **SC-013**: Validation evidence covers schema validation, regenerated model surfaces, hostvar behavior, unit tests, linting, integration testing, generator idempotence, and the branch or change validated.

## Assumptions

- The `border_leaf` device role from PR#74 on `feat/dci-links` is available before this feature is implemented and maps to the same downstream device family as L3 Leaf behavior.
- This phase continues to support all-active multihoming as the only actionable resiliency model.
- A gateway group's local EVPN Domain is its parent `EvpnDomain` through `EvpnGatewayGroup.local_domain`.
- A gateway group's selected Pod remains required context and must have the same `evpn_domain` as the group parent `local_domain`.
- A shared remote domain such as CORE may be part of a Fabric without having any Pods directly assigned to it.
- Full-mesh peering means every enabled Border Leaf gateway sharing a remote EVPN Domain peers with enabled Border Leaf gateways sharing that same remote EVPN Domain, excluding members of its own `EvpnGatewayGroup`.
- Generator hostvar behavior and the EVPN Services Domains menu remain in scope after the schema model is updated.
- EVPN Gateway Groups remain discoverable from EVPN Domain relationship views rather than from a dedicated EVPN Services menu tab.
