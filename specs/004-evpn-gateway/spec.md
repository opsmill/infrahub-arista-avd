# Schema Design Specification: EVPN Gateway Domains

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate all schema definitions.

**Feature Branch**: `feat/evpn-gateway`
**Created**: 2026-07-20
**Status**: Draft
**Input**: User description: "Update EVPN Gateway specifications so a Fabric has zero or more EVPN Domains, Pods belong to one EVPN Domain or none when no Border Leaf has gateway behavior enabled, EVPN Domains contain groups of Border Leaf EVPN Gateways, gateway group members share resiliency, EVPN L2/L3, D-PATH, and all-active Ethernet Segment configuration, no dedicated EVPN Gateway object is created, gateways have local and remote EVPN Domains, gateways sharing a remote EVPN Domain use full-mesh BGP peering, route server and route reflector remote-domain models are out of scope, all-active settings should be shown only when the all-active resiliency model is selected if the UI supports it, all devices in an EVPN Gateway Group must be part of the same Pod, and a gateway group's local EVPN Domain is the EVPN Domain of the Pod where the group is defined. Clarification: the EVPN Services menu must contain a Domains tab for EVPN Domains; EVPN Gateway Groups do not need their own menu tab because users explore an EVPN Domain to reach its EVPN Gateway Groups."

## Clarifications

### Session 2026-07-22

- Q: Should `EvpnGatewayGroup` HFID/display add computed or denormalized helper attributes solely to show the Pod-derived local EVPN Domain? → A: No; use schema-valid native fields for identity/display, while local EVPN Domain remains derived from `pod.evpn_domain` for generator behavior and documentation.

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

The expected schema home for this feature is the EVPN service schema area. The data model must use EVPN Domain and EVPN Gateway Group concepts, plus extensions on existing Fabric, Pod, and Device nodes. A per-device `EvpnGateway` node is explicitly out of scope; a Border Leaf becomes an EVPN Gateway when it is a member of an EVPN Gateway Group. Each EVPN Gateway Group is defined for exactly one Pod, and its local EVPN Domain is the EVPN Domain assigned to that Pod. Gateway group identity and display must use schema-valid native fields and must not add computed or denormalized helper attributes solely to display the Pod-derived local EVPN Domain. In the EVPN Services menu, users navigate first to EVPN Domains and then inspect a Domain to find its related EVPN Gateway Groups.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Model EVPN Domains Across a Fabric (Priority: P1)

As a network designer, I need a Fabric to contain zero or more EVPN Domains and each Pod to belong to at most one EVPN Domain so that gateway intent has a clear domain boundary without forcing every Pod into EVPN Gateway behavior.

**Why this priority**: Domain membership is the foundation for all gateway grouping and peering. Without it, downstream gateway configuration cannot determine whether a Pod participates in an EVPN Domain.

**Independent Test**: Load the schema and model a Fabric with no EVPN Domains, then model the same Fabric with multiple EVPN Domains and Pods assigned to only one domain each.

**Acceptance Scenarios**:

1. **Given** a Fabric has no EVPN Gateway-enabled Border Leafs, **When** the Fabric is modeled, **Then** it may have zero EVPN Domains and its Pods may have no EVPN Domain relationship.
2. **Given** a Fabric has multiple EVPN Domains, **When** a Pod is assigned to a domain, **Then** the Pod is related to exactly one EVPN Domain and the Fabric can list all of its domains.
3. **Given** an operator attempts to assign a Pod to multiple EVPN Domains, **When** the intent is validated or reviewed, **Then** the model prevents or reports the invalid multi-domain Pod assignment.

---

### User Story 2 - Enable Gateways Through Border Leaf Groups (Priority: P2)

As a network designer, I need to group Border Leaf devices from the same Pod as EVPN Gateways so that all gateways in the group share the Pod's local domain, one remote domain, and one common configuration profile.

**Why this priority**: The latest design removes the dedicated EVPN Gateway object. Gateway activation and shared configuration must therefore come from group membership on Border Leaf devices.

**Independent Test**: Assign a Pod to a local EVPN Domain, create a remote EVPN Domain, and create an EVPN Gateway Group for that Pod containing one or more Border Leaf devices from the same Pod. Verify that the group derives its local EVPN Domain from the Pod, group members inherit the shared gateway settings, and non-members remain normal Border Leafs.

**Acceptance Scenarios**:

1. **Given** Border Leaf devices in a Pod that belongs to an EVPN Domain, **When** those devices are added to an EVPN Gateway Group defined for that same Pod with a remote EVPN Domain, **Then** those Border Leafs are considered EVPN Gateways and share the group's resiliency, EVPN L2/L3, D-PATH, and all-active Ethernet Segment settings.
2. **Given** a Border Leaf device is not a member of any EVPN Gateway Group, **When** hostvar intent is derived, **Then** the Border Leaf remains a non-gateway Border Leaf and receives no EVPN Gateway-specific intent.
3. **Given** a device role is not `border_leaf`, **When** an operator attempts to add it to an EVPN Gateway Group, **Then** the feature provides enough schema and validation context to reject or report the device as ineligible.
4. **Given** Border Leaf devices are from different Pods, **When** an operator attempts to add them to the same EVPN Gateway Group, **Then** the feature prevents or reports the group as invalid because all members must belong to the group's Pod.
5. **Given** a Pod has no EVPN Domain assignment, **When** an operator attempts to define an EVPN Gateway Group for that Pod, **Then** the feature prevents or reports the group as invalid because the group's local EVPN Domain must be derived from the Pod.

---

### User Story 3 - Derive Full-Mesh Peering from Remote Domains (Priority: P3)

As a network designer, I need EVPN Gateways that share the same remote EVPN Domain to peer with each other automatically so that route exchange is derived from domain intent instead of manually modeled peer objects.

**Why this priority**: Remote-domain membership is the required source of truth for inter-domain BGP peering in this phase.

**Independent Test**: Model two or more EVPN Gateway Groups with different local EVPN Domains and the same remote EVPN Domain named CORE. Verify that every gateway Border Leaf sharing CORE has every other gateway Border Leaf sharing CORE in its full-mesh peer set.

**Acceptance Scenarios**:

1. **Given** gateway groups from different local EVPN Domains share the same remote EVPN Domain, **When** peer intent is derived, **Then** each gateway Border Leaf has a full-mesh peer relationship with every other enabled gateway Border Leaf sharing that remote EVPN Domain.
2. **Given** a gateway group points to a remote EVPN Domain that no other gateway group uses, **When** peer intent is reviewed, **Then** the model exposes that the group has no remote exchange peers for that remote domain.
3. **Given** an operator attempts to model route servers or route reflectors in the remote EVPN Domain, **When** the intent is reviewed, **Then** the feature reports that only full-mesh gateway peering is supported in this phase.

---

### User Story 4 - Discover Gateway Groups Through EVPN Domains (Priority: P4)

As an operator, I need the EVPN Services menu to provide a Domains tab so that I can start from an EVPN Domain and then inspect the EVPN Gateway Groups connected to that domain.

**Why this priority**: EVPN Domains are the primary service boundary. Navigating through domains matches the data model and avoids presenting gateway groups as a separate top-level service.

**Independent Test**: Load the menu and confirm the EVPN Services section contains a Domains tab for EVPN Domains, contains no Gateways tab for EVPN Gateway Groups, and allows a user viewing an EVPN Domain to see related gateway groups.

**Acceptance Scenarios**:

1. **Given** the custom EVPN Services menu is loaded, **When** a user opens the EVPN Services section, **Then** a Domains tab is available and it opens the EVPN Domains list.
2. **Given** an EVPN Domain has related EVPN Gateway Groups, **When** a user opens that domain, **Then** the user can discover the gateway groups through the domain's related local or remote gateway group relationships.
3. **Given** the custom EVPN Services menu is loaded, **When** a user opens the EVPN Services section, **Then** there is no direct Gateways or EVPN Gateway Groups tab.

---

### User Story 5 - Scope All-Active Settings to the Selected Resiliency Model (Priority: P5)

As an operator, I need all-active multihoming and Ethernet Segment settings to appear only when they apply so that gateway groups do not show irrelevant configuration fields for unsupported or future resiliency models.

**Why this priority**: This improves the operator workflow, but it depends on having the domain and group model in place first.

**Independent Test**: Review the EVPN Gateway Group fields with the all-active multihoming resiliency model selected and confirm that all-active fields are available and clearly tied to that model.

**Acceptance Scenarios**:

1. **Given** an EVPN Gateway Group uses the all-active multihoming resiliency model, **When** the group is edited or reviewed, **Then** the all-active multihoming and Ethernet Segment settings are visible and required as applicable.
2. **Given** a future or unsupported resiliency model is not all-active multihoming, **When** gateway group fields are presented, **Then** all-active settings are hidden if conditional visibility is available, or clearly marked as not applicable if conditional visibility is not available.

### Edge Cases

- A Fabric has zero EVPN Domains and existing Pods remain valid.
- A Pod is assigned to more than one EVPN Domain.
- A Pod has Border Leaf devices in an EVPN Gateway Group but has no EVPN Domain assignment.
- An EVPN Gateway Group contains Border Leaf devices from different Pods or from a Pod outside the group's local EVPN Domain.
- An EVPN Gateway Group is defined for one Pod but includes a Border Leaf device from another Pod.
- An EVPN Gateway Group attempts to set or imply a local EVPN Domain that differs from the EVPN Domain assigned to its Pod.
- A non-Border Leaf device is added to an EVPN Gateway Group.
- A Border Leaf is added to more than one EVPN Gateway Group in this phase.
- An EVPN Gateway Group has no Border Leaf members.
- An EVPN Gateway Group has the same local and remote EVPN Domain.
- Multiple gateway groups share a remote EVPN Domain and must derive a deterministic full-mesh peer set.
- A remote EVPN Domain exists without any Pods, such as a CORE domain used only for inter-domain route exchange.
- The EVPN Services menu contains a direct EVPN Gateway Groups or Gateways tab instead of requiring Domain-first navigation.
- The EVPN Services menu omits the Domains tab, preventing users from reaching EVPN Domains from service navigation.
- A remote EVPN Domain is modeled with route server or route reflector behavior.
- All-active Ethernet Segment values are missing, duplicated where uniqueness is required, or present when the resiliency model is not all-active multihoming.
- Existing Fabric, Pod, Device, and EVPN service data is present when the new schema is loaded.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST define `EvpnDomain` and `EvpnGatewayGroup` as concrete nodes under the `Evpn` namespace.
- **FR-002**: Schema MUST NOT define or require a dedicated `EvpnGateway` node; an EVPN Gateway is a `DcimDevice` with role `border_leaf` that belongs to an EVPN Gateway Group.
- **FR-003**: `EvpnDomain` MUST represent a named EVPN Domain inside a Fabric. A domain can be used as a local Pod domain, as a remote exchange domain, or both depending on gateway group relationships.
- **FR-004**: `EvpnGatewayGroup` MUST represent a group of Border Leaf devices from one Pod that share one gateway configuration profile, a local EVPN Domain derived from that Pod, and one remote EVPN Domain.
- **FR-005**: No new generic is required unless planning identifies reusable domain or gateway group attributes shared by more than one future EVPN service kind.
- **FR-006**: All node names MUST be PascalCase and all namespaces MUST follow the existing project namespace conventions.

#### Attributes

- **FR-010**: `EvpnDomain` MUST have a required `name` Text attribute and a required `domain_id` Text attribute.
- **FR-011**: `EvpnDomain.domain_id` MUST accept colon-delimited values used for EVPN domain identifiers and MUST be unique within the related Fabric.
- **FR-012**: `EvpnGatewayGroup` MUST have a required `name` Text attribute.
- **FR-013**: `EvpnGatewayGroup` MUST have a `resiliency_model` Dropdown attribute. The supported actionable value for this phase is `all_active_multihoming`.
- **FR-014**: `EvpnGatewayGroup` MUST carry the shared EVPN gateway enablement settings required by all member Border Leafs: EVPN L2 enabled, EVPN L3 enabled, EVPN inter-domain behavior, and D-PATH enabled.
- **FR-015**: `EvpnGatewayGroup` MUST carry shared all-active multihoming settings, including Ethernet Segment identifier and Ethernet Segment route-target import value.
- **FR-016**: All-active multihoming and Ethernet Segment settings MUST be modeled so they are applicable only when `resiliency_model` is `all_active_multihoming`.
- **FR-017**: New attributes added to existing nodes MUST be optional or provide defaults so existing loaded data remains valid after schema migration.
- **FR-018**: All attribute names MUST be snake_case and all attribute kinds MUST use current Infrahub kinds such as Text, Boolean, Dropdown, and Number.

#### Relationships

- **FR-020**: `NetworkFabric` MUST be able to relate to zero or more `EvpnDomain` objects.
- **FR-021**: Each `EvpnDomain` MUST relate to exactly one `NetworkFabric`.
- **FR-022**: `NetworkPod` MUST relate to zero or one `EvpnDomain`.
- **FR-023**: Each `EvpnDomain` MUST be able to list the Pods that are part of that domain.
- **FR-024**: `EvpnGatewayGroup` MUST relate to exactly one `NetworkPod` for which the group is defined.
- **FR-025**: The `NetworkPod` for an `EvpnGatewayGroup` MUST belong to exactly one `EvpnDomain`; this Pod EVPN Domain is the gateway group's local EVPN Domain.
- **FR-026**: `EvpnGatewayGroup` MUST NOT allow an independently selected local EVPN Domain that can differ from the EVPN Domain assigned to its Pod.
- **FR-027**: `EvpnGatewayGroup` MUST relate to exactly one remote `EvpnDomain`.
- **FR-028**: The remote EVPN Domain on an `EvpnGatewayGroup` MUST be distinct from the local EVPN Domain derived from the group's Pod.
- **FR-029**: `EvpnGatewayGroup` MUST relate to one or more `DcimDevice` members that act as EVPN Gateways.
- **FR-030**: Member devices of an `EvpnGatewayGroup` MUST be eligible only when their role is `border_leaf`.
- **FR-031**: All member devices of an `EvpnGatewayGroup` MUST be mutually consistent by belonging to one shared `NetworkPod`.
- **FR-032**: The shared `NetworkPod` for all member devices of an `EvpnGatewayGroup` MUST be the exact `NetworkPod` for which the group is defined.
- **FR-033**: A `DcimDevice` MUST be able to expose whether it belongs to an EVPN Gateway Group so gateway activation can be derived from device membership.
- **FR-034**: A Border Leaf MUST belong to at most one EVPN Gateway Group in this phase.
- **FR-035**: EVPN Gateway full-mesh peer sets MUST be derivable from all enabled Border Leaf member devices whose gateway groups share the same remote EVPN Domain. An enabled Border Leaf gateway means a `DcimDevice` with role `border_leaf` that is a member of exactly one valid `EvpnGatewayGroup` and passes generator-side gateway eligibility validation.
- **FR-036**: The schema MUST NOT require manually modeled remote peer relationships between individual gateways for this phase.
- **FR-037**: All bidirectional relationships MUST use matching `identifier` values on both sides.
- **FR-038**: Relationship `peer` values MUST use full schema kinds such as `NetworkFabric`, `NetworkPod`, `DcimDevice`, and `EvpnDomain`.

#### Display & Identification

- **FR-040**: `EvpnDomain` MUST define a human-friendly identifier and display label that let operators distinguish domains by Fabric and domain ID.
- **FR-041**: `EvpnGatewayGroup` MUST define a schema-valid human-friendly identifier and display label using native fields such as Pod and group name, and SHOULD include remote EVPN Domain fields when Infrahub accepts those fields for identity/display. It MUST NOT add computed or denormalized helper attributes solely to show the Pod-derived local EVPN Domain; that local domain remains derived from `pod.evpn_domain` for validation, documentation, and hostvar generation.
- **FR-042**: The EVPN Services menu MUST contain a Domains tab linked to `EvpnDomain`.
- **FR-043**: The EVPN Services menu MUST NOT contain a direct Gateways or EVPN Gateway Groups tab linked to `EvpnGatewayGroup`; users MUST explore an EVPN Domain to reach its related EVPN Gateway Groups.
- **FR-044**: `EvpnDomain` and `EvpnGatewayGroup` MUST avoid duplicate automatic menu entries when the custom EVPN Services menu is used.
- **FR-045**: Attributes and relationships MUST use order weights consistent with the existing EVPN service schemas so Fabric, domain, group, member, resiliency, and Ethernet Segment fields appear in a predictable order.
- **FR-046**: All-active multihoming and Ethernet Segment settings SHOULD be hidden unless `resiliency_model` is `all_active_multihoming` when conditional field visibility is available; otherwise, field labels or descriptions MUST make the applicability clear.

#### Uniqueness Constraints

- **FR-050**: `EvpnDomain` MUST prevent duplicate domain names within the same Fabric.
- **FR-051**: `EvpnDomain` MUST prevent duplicate `domain_id` values within the same Fabric.
- **FR-052**: `EvpnGatewayGroup` MUST prevent duplicate group names within the same Pod.
- **FR-053**: The model MUST prevent or report a Border Leaf being assigned to more than one EVPN Gateway Group in this phase.
- **FR-054**: Uniqueness constraints MUST use `__value` suffixes for attribute references and bare relationship names for relationship references.

#### Migration

- **FR-060**: Schema changes MUST be additive for existing Fabric, Pod, Device, and EVPN service data whenever possible.
- **FR-061**: Any relationship added to `NetworkFabric`, `NetworkPod`, or `DcimDevice` MUST be optional on existing objects unless populated by a controlled migration in a later implementation phase.
- **FR-062**: If earlier draft work introduced an `EvpnGateway` schema object, the implementation plan MUST replace it with the `EvpnGatewayGroup` plus Border Leaf membership model before planning proceeds.
- **FR-063**: Schema validation and protocol regeneration MUST be part of the implementation plan after the schema is written.

#### Hostvars & Configuration Scope

- **FR-070**: EVPN Gateway hostvars MUST be emitted only for devices with role `border_leaf` that are members of an EVPN Gateway Group.
- **FR-071**: Devices with role `leaf`, `l2leaf`, `spine`, or `super_spine` MUST NOT receive EVPN Gateway hostvars even when they share the same Pod, Fabric, local EVPN Domain, or remote EVPN Domain.
- **FR-072**: Every Border Leaf in an EVPN Gateway Group MUST receive the group's shared EVPN L2/L3, D-PATH, resiliency, and all-active Ethernet Segment values.
- **FR-073**: Every Border Leaf in an EVPN Gateway Group MUST resolve its local EVPN Domain from the EVPN Domain assigned to the group's Pod and its remote EVPN Domain from the group's remote-domain relationship.
- **FR-074**: Every Border Leaf in an EVPN Gateway Group MUST derive its remote peer hostname list from all other enabled Border Leaf gateways whose groups share the same remote EVPN Domain.
- **FR-075**: Border Leaf devices that are not members of an EVPN Gateway Group MUST continue to generate their existing Border Leaf hostvars without EVPN Gateway-specific fields.
- **FR-076**: Route server and route reflector models in the remote EVPN Domain MUST NOT be supported in this phase; only full-mesh gateway peering is supported. This is enforced by not modeling dedicated schema fields or dropdown values for those modes, and by generator-side validation that reports any stale or draft route-server or route-reflector input if present.

#### Validation & Enforcement Scope

- **FR-080**: This feature MUST NOT require a dedicated Infrahub check when schema constraints and generator-side eligibility rules can enforce or report the required behavior.
- **FR-081**: Generator-side eligibility rules MUST report actionable errors for gateway intent that cannot be fully constrained by schema relationships or attribute definitions before EVPN Gateway-specific hostvars are emitted.
- **FR-082**: Validation or generation MUST report Pods without EVPN Domain assignment, local and remote domain conflicts, non-Border Leaf members, members from a different Pod than the gateway group, unsupported route-server models, and gateway groups without member devices.

### Key Entities

- **EvpnDomain**: Represents one EVPN Domain inside a Fabric. Key data includes name, domain ID, Fabric relationship, optional Pod membership, local gateway groups, and remote gateway groups.
- **EvpnGatewayGroup**: Represents a group of Border Leaf devices from one Pod acting as EVPN Gateways. Key data includes name, Pod, Pod-derived local EVPN Domain, remote EVPN Domain, Border Leaf members, shared resiliency model, EVPN L2/L3 and D-PATH settings, and all-active Ethernet Segment values.
- **NetworkFabric**: Existing Fabric entity that owns zero or more EVPN Domains.
- **NetworkPod**: Existing Pod entity that may belong to one EVPN Domain. A Pod with an EVPN Gateway Group must belong to one EVPN Domain, and that domain is the local EVPN Domain for the group.
- **DcimDevice**: Existing device entity. A device becomes an EVPN Gateway only when it has role `border_leaf` and belongs to an EVPN Gateway Group.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema validation completes with zero errors after the EVPN Domain and EVPN Gateway Group model is added.
- **SC-002**: A reviewer can model a Fabric with zero EVPN Domains and confirm existing Pods remain valid without gateway intent.
- **SC-003**: A reviewer can model one Fabric with at least three EVPN Domains, including two Pod-local domains and one shared remote CORE domain, without assigning any Pod to more than one domain.
- **SC-004**: A reviewer can model at least two EVPN Gateway Groups for different Pods in different local EVPN Domains that share the same remote CORE domain, with each group containing one or more Border Leaf devices from its own Pod and one shared configuration profile.
- **SC-005**: The model clearly distinguishes Border Leafs that are EVPN Gateways through group membership, Border Leafs that are not gateways, and non-Border Leaf devices that must never receive gateway configuration.
- **SC-006**: For every modeled gateway group sharing a remote EVPN Domain, the full-mesh peer set can be resolved as all other enabled Border Leaf gateways sharing that remote domain.
- **SC-007**: Route server and route reflector remote-domain models are not selectable or accepted as supported behavior in this phase.
- **SC-008**: All-active multihoming and Ethernet Segment fields are visible and applicable for the all-active resiliency model, and are hidden or clearly marked not applicable for non-all-active models if such models become visible.
- **SC-009**: Generated hostvars for gateway-group member Border Leafs contain EVPN Gateway-specific fields, while regular Leafs and ungrouped Border Leafs do not.
- **SC-010**: A reviewer cannot successfully model or approve an EVPN Gateway Group whose member devices span multiple Pods or whose Pod has no EVPN Domain assignment.
- **SC-011**: The EVPN Services menu contains exactly one Domains tab for EVPN Domains, contains no direct Gateways or EVPN Gateway Groups tab, and lets a reviewer reach gateway group relationships from an EVPN Domain view.

## Assumptions

- The `border_leaf` device role from PR#74 on `feat/dci-links` is available before this feature is implemented and maps to the same downstream device family as L3 Leaf behavior.
- This phase continues to support all-active multihoming as the only actionable resiliency model.
- A gateway group is defined for one Pod; its local EVPN Domain is the EVPN Domain assigned to that Pod.
- A shared remote domain such as CORE may be part of a Fabric without having any Pods directly assigned to it.
- Full-mesh peering means every enabled Border Leaf gateway sharing a remote EVPN Domain peers with every other enabled Border Leaf gateway sharing that same remote EVPN Domain.
- Conditional field visibility may depend on Infrahub UI capabilities. If conditional visibility is not available, the model must still make all-active field applicability clear and enforce it during validation or generation.
- Generator hostvar behavior and the EVPN Services Domains menu remain in scope after the schema model is updated.
- EVPN Gateway Groups remain discoverable from EVPN Domain relationship views rather than from a dedicated EVPN Services menu tab.
- Infrahub schema identity/display constraints may prevent embedding the Pod-derived local EVPN Domain directly in `EvpnGatewayGroup` HFID/display; the schema must not introduce helper attributes solely for that display purpose.
