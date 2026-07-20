# Infrahub Feature Specification: DCI Links

> **This feature includes schema and generator scope.** The implementing agent MUST use the `infrahub-managing-schemas` skill for schema definitions and the `infrahub-managing-generators` skill for generator work.

**Feature Branch**: `feat/dci-links`
**Created**: 2026-07-19
**Status**: Draft
**Input**: User description: "This feature must implement DCI links in the InfraHub schema, and required generators to emit pyAVD l3_edge artifacts to configure DCI links. A new leaf role must be created 'Border Leaf'. This role connects to the DCI links and all external networks (not part of this PR). It can also be configured as EVPN Gateway (not part of this PR). A 'Border Leaf' is mapped to a pyAVD l3leaf. A DCI link must connect 2 border leafs. A DCI link will default be part of the underlay protocol. NetworkDciLink must be a concrete Network node that inherits the same DcimConnector generic as NetworkLink, reusing the existing physical endpoint model while adding DCI-specific attributes. In Infrahub, DCI links support only include_in_underlay_protocol and the BGP ASN values required for underlay routing. Endpoint devices, endpoint interfaces, and details come from shared link behavior. Point-to-point addressing must come from a DCI IP Pool in Infrahub, with one /31 network allocated for each DCI link. Do not add DCI-specific enabled, endpoint A/B device/interface, subnet, p2p_pool, p2p_link_id, endpoint IP, endpoint description, BFD, MTU, or protocol selection fields. The same phase must implement generators to emit PyAVD l3_edge; generator output must not use p2p_links_profiles and must emit speed and include_in_underlay_protocol directly under each p2p_links entry with nodes, interfaces, as, and ip. A dedicated check implementation is not required when constraints can be handled in schema and generators."

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Identify Border Leafs (Priority: P1)

As a network designer, I need to classify selected leaf devices as Border Leafs so DCI links can target only the devices intended to connect outside the fabric.

**Why this priority**: DCI links depend on a distinct border leaf role. Without the role, downstream artifacts cannot distinguish standard leaf devices from edge devices.

**Independent Test**: Can be validated by loading the schema and creating or updating a network device with the Border Leaf role while confirming existing leaf roles remain available.

**Acceptance Scenarios**:

1. **Given** a network device exists, **When** a user edits its role, **Then** "Border Leaf" is an available device role.
2. **Given** a device has the Border Leaf role, **When** AVD device classification is evaluated, **Then** the device remains in the leaf family and is eligible for l3leaf output.

---

### User Story 2 - Specialize Existing Links As DCI Links (Priority: P1)

As a network designer, I need to model a DCI link as a concrete Network node that reuses the existing Network Link physical endpoint model through `DcimConnector` so DCI intent does not duplicate endpoint data.

**Why this priority**: The DCI link entity is the core data model required before any generator can emit point-to-point L3 edge artifacts.

**Independent Test**: Can be validated by creating one DCI link from the shared `DcimConnector` endpoint behavior used by Network Link and confirming the DCI object shares physical endpoints and stable link identity while only adding DCI-specific protocol attributes.

**Acceptance Scenarios**:

1. **Given** two devices with role Border Leaf and one available physical interface on each, **When** a user creates a DCI link, **Then** the link uses shared connected endpoint behavior to identify both devices and both interfaces.
2. **Given** a DCI link references fewer or more than two endpoint devices, **When** the link is validated, **Then** it is rejected or reported as incomplete.
3. **Given** a DCI link endpoint references a non-Border Leaf device, **When** the link is validated for use, **Then** it is rejected or reported as ineligible for DCI generation.
4. **Given** a DCI link is reviewed in the schema, **When** its direct DCI-specific fields are listed, **Then** only underlay protocol participation and BGP ASN values appear as DCI-specific additions.

---

### User Story 3 - Capture DCI BGP Settings And Addressing Source (Priority: P1)

As a network designer, I need to control whether each DCI link participates in underlay routing, record the BGP ASN values for both DCI endpoints, and use a DCI IP Pool as the source for point-to-point addressing so generated L3 edge intent matches the intended DCI behavior.

**Why this priority**: DCI links default to underlay participation. BGP ASN values and a DCI IP Pool are required before the generator can emit complete point-to-point L3 edge entries with `as` and `ip` values.

**Independent Test**: Can be validated by creating DCI links with default underlay participation, BGP ASN values, and an available DCI IP Pool, then confirming the modeled or allocated values are visible and unambiguous in generated DCI intent.

**Acceptance Scenarios**:

1. **Given** a new DCI link is created without an underlay participation override, **When** the link is saved, **Then** underlay participation is enabled by default.
2. **Given** a DCI link has BGP ASN values for both shared endpoints, **When** AVD device intent is generated, **Then** those values are represented in the generated point-to-point link entry.
3. **Given** a DCI link disables underlay participation, **When** AVD device intent is generated, **Then** the generated point-to-point link entry carries the modeled underlay participation value.
4. **Given** a DCI IP Pool is available, **When** a valid DCI link is generated, **Then** exactly one /31 network is allocated from that pool for the DCI link point-to-point addressing.

---

### User Story 4 - Generate L3 Edge Intent (Priority: P1)

As a network operator, I need modeled DCI links between Border Leafs to appear in generated AVD intent so the resulting device artifacts include the required point-to-point L3 edge configuration.

**Why this priority**: The schema alone does not deliver usable DCI configuration. Generator output for `l3_edge` is part of this phase and is required for the feature to be complete.

**Independent Test**: Can be validated by modeling DCI links from one Border Leaf to two remote Border Leafs, running the relevant generation workflow, and confirming the generated device intent includes complete `l3_edge` point-to-point entries with both endpoints, modeled underlay participation, and `speed` only when endpoint/interface data provides a resolvable speed.

**Acceptance Scenarios**:

1. **Given** two Border Leaf devices are connected by a valid DCI link, **When** AVD device intent is generated, **Then** the generated output contains an `l3_edge` entry representing that DCI link.
2. **Given** one Border Leaf has two valid DCI links to remote Border Leafs, **When** AVD device intent is generated for that node, **Then** the generated `l3_edge.p2p_links` list contains one entry per DCI link with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and `speed` only when endpoint/interface data provides a resolvable speed.
3. **Given** DCI links have per-link operational settings, **When** AVD device intent is generated, **Then** no shared point-to-point link profile is emitted for DCI links.
4. **Given** a DCI link keeps the default underlay behavior, **When** AVD device intent is generated, **Then** the generated point-to-point link entry includes underlay participation as enabled.
5. **Given** a DCI link is incomplete or uses a non-Border Leaf endpoint, **When** AVD device intent is generated, **Then** the generator excludes the invalid link and reports actionable context without requiring a separate check implementation.

---

### Edge Cases

- A DCI link endpoint references a device without the Border Leaf role.
- A DCI link endpoint references an interface that does not belong to the selected endpoint device.
- Both endpoints reference the same Border Leaf device or the same interface.
- Two DCI links use the same endpoint interface pair.
- Multiple parallel DCI links connect the same pair of Border Leaf devices.
- A DCI link has no DCI IP Pool available for /31 point-to-point allocation.
- A DCI IP Pool does not have enough available /31 networks for all valid DCI links.
- A DCI link attempts to define DCI-specific endpoint A/B device/interface, subnet, `p2p_pool`, link ID, endpoint IP, endpoint description, BFD, MTU, protocol selection, or enabled fields instead of relying on shared endpoint data, DCI ASN fields, and pool allocation.
- Existing devices already using the leaf role must remain valid after the Border Leaf choice is added.
- External network and EVPN Gateway use cases must not be required to create or validate a DCI link in this feature.
- DCI is not yet listed as a supported capability in the project capability matrix, so planning must include the documentation change needed to make the new support boundary visible to operators.
- DCI link data is valid in the schema but lacks BGP ASN values or an allocated /31 network for a complete generated L3 edge entry.
- Multiple DCI links affect the same pair of Border Leafs and must result in deterministic generated ordering.
- Generator-side eligibility rules reject a DCI link that schema constraints allow because the rule depends on derived endpoint or role data.
- A dedicated check implementation is requested by downstream planning even though the same constraint can be enforced by schema or generator behavior.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST add a Border Leaf device role choice to the existing network device role model without removing existing choices: Super Spine, Spine, Leaf, and L2 Leaf.
- **FR-002**: Schema MUST treat Border Leaf as a leaf-family device role for downstream AVD classification, mapping it to l3leaf behavior.
- **FR-003**: Schema MUST define a concrete DCI link entity under the Network namespace to represent one point-to-point DCI connection.
- **FR-004**: The DCI link entity MUST be suitable for user-facing object creation, review, and selection in Infrahub.
- **FR-005**: The DCI link model MUST support multiple distinct DCI links between the same pair of Border Leaf devices when they use distinct identifiers or endpoint interfaces.
- **FR-006**: The Border Leaf role MUST be represented consistently across the source-of-truth role list, AVD role mapping, hostvars eligibility, and generated artifact targeting.
- **FR-007**: The DCI link entity MUST be modeled as a concrete `NetworkDciLink` node inheriting the same `DcimConnector` generic used by `NetworkLink`, so physical endpoint behavior remains consistent with other links.

#### Attributes

- **FR-010**: The DCI link entity MUST add only direct DCI-specific attributes for `include_in_underlay_protocol` and the BGP ASN values required to build the generated `as` list.
- **FR-011**: The DCI link entity MUST have an `include_in_underlay_protocol` Boolean flag that defaults to enabled.
- **FR-012**: The DCI link entity MUST support the BGP ASN values required for both shared endpoints when underlay participation is enabled.
- **FR-013**: The DCI link entity MUST NOT define a user-selectable underlay protocol field; this feature supports BGP underlay behavior for generated DCI links.
- **FR-014**: The DCI link entity MUST NOT define DCI-specific `enabled`, endpoint A/B device/interface, subnet, `p2p_pool`, `p2p_link_id`, endpoint IP, endpoint description, BFD, MTU, name, or description attributes.
- **FR-015**: Base link identity and any base link descriptive fields MUST remain compatible with the existing Network Link behavior.
- **FR-016**: Point-to-point addressing intent MUST come from a DCI IP Pool in Infrahub; one /31 network MUST be allocated for each generated DCI link.
- **FR-016a**: Allocated point-to-point IP values MUST NOT be stored as direct DCI-specific endpoint IP attributes on the DCI link.
- **FR-017**: New attributes added to existing nodes MUST be optional or have safe defaults so existing data remains valid after schema load.
- **FR-018**: All new Dropdown attributes MUST define explicit choices with stable machine names and readable labels.

#### Relationships

- **FR-020**: A DCI link MUST use the same `DcimConnector.connected_endpoints` relationship model as Network Link to resolve exactly two endpoint devices.
- **FR-021**: Both DCI link endpoint devices MUST be network devices with the Border Leaf role before the link is eligible for DCI artifact generation.
- **FR-022**: A DCI link MUST use the same `DcimConnector.connected_endpoints` relationship model as Network Link to resolve exactly two endpoint interfaces.
- **FR-023**: Each endpoint interface MUST belong to its corresponding endpoint device before the link is eligible for DCI artifact generation.
- **FR-024**: The DCI link entity MUST NOT introduce DCI-specific endpoint device, endpoint interface, or addressing relationships.
- **FR-025**: The DCI link model MUST allow the downstream generator to derive the two node names, two interface names, BGP ASN values, and point-to-point addressing data from shared endpoint behavior, DCI ASN fields, and DCI IP Pool allocation.
- **FR-026**: The DCI link model MUST avoid making external network or EVPN Gateway relationships mandatory in this feature.

#### Generator Output

- **FR-030**: The feature MUST implement generator behavior in this phase that emits AVD `l3_edge` intent for valid DCI links.
- **FR-031**: Generated `l3_edge` intent MUST include both Border Leaf endpoints, their endpoint interfaces, BGP ASN values, and point-to-point addressing allocated from the DCI IP Pool.
- **FR-032**: Generated `l3_edge` intent MUST explicitly emit `include_in_underlay_protocol` for every DCI link, using the modeled value and the default enabled behavior when no override is set.
- **FR-033**: Generated DCI `l3_edge` intent MUST NOT emit or rely on `l3_edge.p2p_links_profiles`.
- **FR-034**: Generated DCI `l3_edge.p2p_links` entries MUST carry all DCI operational settings directly on each link entry.
- **FR-035**: Generated DCI `l3_edge.p2p_links` entries MUST emit `include_in_underlay_protocol` and MUST emit `speed` when it can be resolved from endpoint/interface data.
- **FR-036**: Generated `l3_edge.p2p_links` entries for DCI links MUST emit `nodes`, `interfaces`, `as`, `ip`, and `include_in_underlay_protocol`; they MUST omit `speed` when no endpoint/interface speed can be resolved.
- **FR-037**: Generated DCI `l3_edge.p2p_links` entries MUST NOT emit `profile` solely to reference a shared DCI profile.
- **FR-038**: Generated `nodes`, `interfaces`, `as`, and `ip` lists MUST preserve endpoint ordering consistently so each list position describes the same side of the DCI link.
- **FR-039**: Generator behavior MUST treat Border Leaf devices as AVD l3leaf devices when selecting targets and building generated intent.
- **FR-040**: Generator behavior MUST validate DCI eligibility rules that depend on derived data, including exactly two Border Leaf endpoint devices, endpoint interface ownership, no same-device endpoint pair, BGP ASN availability, and successful /31 allocation from a DCI IP Pool.
- **FR-041**: Generator behavior MUST be idempotent: repeated generation from unchanged DCI link data must produce the same generated intent without duplicate or stale entries.
- **FR-042**: Generator behavior MUST use deterministic ordering for generated DCI links so artifact diffs are stable across repeated runs.
- **FR-043**: Generator behavior MUST report incomplete or ineligible DCI links with enough context for operators to correct the source data.
- **FR-044**: This phase MUST NOT require a dedicated check implementation when schema constraints and generator-side eligibility rules can enforce or report the required behavior.
- **FR-045**: Generator-side DCI eligibility failures MUST be reported through the generator execution result or logs with the DCI link identifier and the failed rule, while excluding the invalid link from generated `l3_edge` intent.

#### Expected AVD L3 Edge Shape

For a device with multiple valid DCI links, generated intent MUST follow this shape:

```yaml
l3_edge:
  p2p_links:
    - nodes: [ih-dc1-leaf1a, ih-dc2-leaf1a]
      interfaces: [Ethernet5, Ethernet5]
      as: [65101, 65201]
      ip: [172.16.0.0/31, 172.16.0.1/31]
      speed: 100g
      include_in_underlay_protocol: true
    - nodes: [ih-dc1-leaf1a, ih-dc2-leaf1b]
      interfaces: [Ethernet6, Ethernet6]
      as: [65101, 65202]
      ip: [172.16.0.2/31, 172.16.0.3/31]
      speed: 100g
      include_in_underlay_protocol: true
```

The DCI link schema MUST NOT add direct DCI-specific `speed`, endpoint, subnet,
`p2p_pool`, or endpoint IP fields solely to satisfy this output shape. Endpoint
values must come from shared link behavior, `as` values must come from DCI BGP
ASN fields, and `ip` values must come from /31 DCI IP Pool allocation. `speed`
must come from endpoint/interface data when available; when no speed can be
resolved, the generator must omit the `speed` key from the DCI `p2p_links`
entry.

#### Display & Identification

- **FR-050**: The DCI link entity MUST use compatible Network Link identity so it remains readable in object files and review output.
- **FR-051**: The DCI link entity MUST use compatible Network Link display behavior suitable for operators reviewing DCI topology.
- **FR-052**: New DCI link attributes and relationships MUST use order weights consistent with the existing schema conventions.
- **FR-053**: The Border Leaf role label MUST be human-readable as "Border Leaf" while using a stable value suitable for automation.

#### Uniqueness Constraints

- **FR-060**: DCI link identifiers MUST be unique.
- **FR-061**: The schema MUST prevent or make detectable duplicate DCI links that use the same two endpoint interfaces.
- **FR-062**: Uniqueness constraints MUST use attribute `__value` suffixes and bare relationship names according to Infrahub schema rules.

#### Migration

- **FR-070**: Existing network device role data MUST remain valid after adding the Border Leaf role.
- **FR-071**: Existing Network Link, interface, rack, pod, and fabric objects MUST remain valid without requiring DCI link data.
- **FR-072**: Schema planning MUST include protocol class regeneration after schema changes.
- **FR-073**: Planning MUST include generated GraphQL schema and return-type refresh steps for any generator query that reads Border Leaf or DCI link data.
- **FR-074**: Planning MUST include documentation updates for role mapping, hostvars behavior, and supported capability status.
- **FR-075**: Shared specifications and committed documentation MUST NOT include private lab hostnames, tokens, or environment-specific validation commands.
- **FR-076**: Planning MUST include generator implementation, generator query updates, generated return-type refresh, hostvars or structured-config integration points, unit tests, integration tests, and generator idempotence validation for the `l3_edge` output path.
- **FR-077**: Planning MUST treat a dedicated check implementation as out of scope unless a documented rule cannot be implemented or reported through schema constraints and generator behavior.

### Key Entities

- **Border Leaf Role**: A new network device role choice for leaf-family devices that connect to DCI links and, in future work, external networks or EVPN Gateway behavior.
- **DCI Link**: A user-facing concrete `NetworkDciLink` node that inherits `DcimConnector` to share Network Link physical endpoint behavior, representing one point-to-point DCI connection between two Border Leaf devices while adding only underlay participation and BGP ASN values as direct DCI-specific settings.
- **DCI IP Pool**: An Infrahub IPAM allocation source dedicated to DCI point-to-point addressing by assignment to `NetworkFabric.dci_pool`; each generated DCI link receives exactly one /31 network from this pool.
- **Generated L3 Edge Intent**: The generated AVD data derived from valid DCI links that describes the point-to-point L3 edge connection between Border Leafs, including one self-contained `p2p_links` entry per valid DCI link.
- **Endpoint Device**: A network device with the Border Leaf role participating in one side of a DCI link.
- **Endpoint Interface**: A physical interface on an endpoint device used by one side of a DCI link.
- **Point-to-Point Addressing Source**: The DCI IP Pool used to allocate one /31 network per DCI link without storing DCI-specific endpoint IP fields on the link.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema validation passes with zero errors after adding the DCI schema changes.
- **SC-002**: Existing device role choices remain available, and Border Leaf appears as an additional role choice.
- **SC-003**: A user can model a complete DCI link between two Border Leaf devices with two endpoint interfaces in one object workflow.
- **SC-004**: For each valid DCI link, generated L3 edge input can resolve both node names, both interface names, both BGP ASN values, both point-to-point IP values, optional link speed when endpoint/interface data provides it, and underlay participation from DCI direct attributes, shared link endpoints, related endpoint/interface objects, or DCI IP Pool allocation.
- **SC-005**: Duplicate active DCI links using the same endpoint interface pair are prevented by schema constraints or reported by planned validation before artifact generation.
- **SC-006**: Existing non-DCI objects load without requiring any new DCI-specific values.
- **SC-007**: The schema exposes explicit underlay protocol participation and BGP ASN values for every DCI link.
- **SC-008**: Role mapping, hostvars behavior, and supported capability documentation identify Border Leaf and DCI support clearly enough that operators can determine what is included and what remains out of scope.
- **SC-009**: For a valid DCI link between two Border Leafs, generated device intent includes exactly one corresponding `l3_edge.p2p_links` entry with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and `speed` only when endpoint/interface data provides a resolvable speed.
- **SC-010**: Re-running generation against unchanged DCI link data produces no duplicate DCI entries and no unexpected changes in generated artifacts.
- **SC-011**: Invalid DCI links are either blocked by schema constraints or excluded by generator behavior with actionable reporting; no separate check implementation is required for the planned constraints.
- **SC-012**: For multiple valid DCI links, generated device intent does not include a DCI `l3_edge.p2p_links_profiles` entry; each generated DCI link carries its own `include_in_underlay_protocol` value and resolved `speed` value, when available, directly under `l3_edge.p2p_links`.

## Assumptions

- The stable machine value for the Border Leaf role will be `border_leaf`, with display label "Border Leaf".
- Border Leaf maps to AVD l3leaf behavior for downstream artifact generation.
- External network modeling is out of scope for this feature.
- EVPN Gateway configuration is out of scope for this feature.
- This feature phase includes both the schema/data model and the generator work required to emit PyAVD `l3_edge` intent.
- `NetworkDciLink` inherits the same `DcimConnector` generic as `NetworkLink`; endpoint and detail values are not modeled as DCI-specific direct fields.
- Point-to-point addressing is allocated from a DCI IP Pool in Infrahub, with one /31 network per generated DCI link.
- `NetworkFabric.dci_pool` is the authoritative DCI IP Pool selector for this phase. A pool is considered DCI-dedicated by assignment to this fabric relationship; this feature does not add DCI prefix role metadata, a direct DCI link pool field, or DCI-specific pool relationships.
- The local AVD reference shows native l3_edge point-to-point link support, including `p2p_links`, `speed`, `include_in_underlay_protocol`, `nodes`, `interfaces`, `as`, and `ip`.
- DCI link speed is inferred from endpoint/interface data when available. If no speed can be resolved, the generator omits the `speed` key from the generated DCI `p2p_links` entry; it does not synthesize a speed default and does not add a direct DCI-specific speed attribute on `NetworkDciLink`.
- Validation of role/interface consistency should be handled by schema constraints where possible and generator-side eligibility rules where derived data is required; a dedicated check implementation is out of scope unless planning documents an unavoidable gap.
- The project targets pyAVD 6.3.x, so generator planning must confirm every emitted DCI-related field against that pinned version.
- The existing AVD pipeline documentation describes role mapping, hostvars generation, and extension touch points; those references should be updated as part of this feature when behavior changes.
