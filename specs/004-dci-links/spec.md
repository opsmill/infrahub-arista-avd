# Schema Design Specification: DCI Links

> **This feature includes schema and generator scope.** The implementing agent MUST use the `infrahub-managing-schemas` skill for schema definitions and the `infrahub-managing-generators` skill for generator work.

**Feature Branch**: `feat/dci-links`
**Created**: 2026-07-19
**Status**: Draft
**Input**: User description: "Update the existing DCI Links feature: model DCI links as NetworkLink objects with role = dci instead of a separate NetworkDciLink node. Remove NetworkDciLink from schema, query, menu, docs, tests, protocols, and generator intent. Add/extend NetworkLink role support for dci while preserving existing NetworkLink behavior. Keep Border Leaf role mapping to l3leaf, NetworkFabric.dci_pool /31 allocation, PyAVD l3_edge output, deterministic ordering, invalid-link reporting, and no p2p_links_profiles. Include a decision/task to consolidate or explicitly justify the duplicate allocate_p2p_prefix_from_pool helpers."

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Classify Border Leafs (Priority: P1)

As a network designer, I need to classify selected leaf devices as Border Leafs so DCI links can target only devices intended to connect outside the fabric.

**Why this priority**: DCI links depend on a distinct border leaf role, and downstream generated intent must treat those devices as leaf-family devices.

**Independent Test**: Load the schema and create or update a network device with the Border Leaf role while confirming existing device roles remain available and Border Leaf maps to AVD l3leaf behavior.

**Acceptance Scenarios**:

1. **Given** a network device exists, **When** a user edits its role, **Then** "Border Leaf" is an available device role.
2. **Given** a device has the Border Leaf role, **When** AVD device classification is evaluated, **Then** the device is treated as l3leaf.
3. **Given** existing devices use Super Spine, Spine, Leaf, or L2 Leaf roles, **When** the schema is loaded, **Then** those devices remain valid.

---

### User Story 2 - Mark Network Links As DCI Links (Priority: P1)

As a network designer, I need to model each DCI connection as an existing Network Link with role `dci` so DCI intent reuses the standard physical link endpoint model instead of a separate link node.

**Why this priority**: Reusing Network Link preserves existing link behavior, avoids duplicate endpoint concepts, and removes the stale separate DCI link model.

**Independent Test**: Create a Network Link with two Border Leaf endpoint interfaces and role `dci`, then confirm ordinary Network Link behavior still works for non-DCI links.

**Acceptance Scenarios**:

1. **Given** two Border Leaf devices and one available physical interface on each, **When** a user creates a Network Link with role `dci`, **Then** the link represents one DCI connection using the existing Network Link connected endpoint behavior.
2. **Given** a Network Link has no role or a non-DCI role, **When** ordinary Network Link workflows run, **Then** existing behavior is unchanged.
3. **Given** a Network Link with role `dci` references fewer or more than two usable endpoint interfaces, **When** DCI generation evaluates it, **Then** the link is excluded and reported as invalid.
4. **Given** any repository artifact still references `NetworkDciLink`, **When** the feature is validated, **Then** that artifact is considered stale and must be removed or updated.

---

### User Story 3 - Capture DCI Settings And Addressing Source (Priority: P1)

As a network designer, I need DCI-role Network Links to carry underlay participation and endpoint BGP ASN values, and I need a fabric-level DCI IP pool to provide point-to-point addressing.

**Why this priority**: Generated L3 edge intent requires underlay participation, two ASN values, and one /31 allocation per valid DCI link.

**Independent Test**: Create DCI-role Network Links with default underlay participation, endpoint ASN values, and an available fabric DCI pool, then confirm the modeled and allocated values are unambiguous for generated intent.

**Acceptance Scenarios**:

1. **Given** a new DCI-role Network Link is created without an underlay override, **When** it is saved, **Then** underlay participation defaults to enabled.
2. **Given** a DCI-role Network Link has BGP ASN values for both endpoints, **When** AVD device intent is generated, **Then** those values are represented in the generated point-to-point link entry.
3. **Given** a DCI-role Network Link disables underlay participation, **When** AVD device intent is generated, **Then** the generated point-to-point link entry carries the modeled disabled value.
4. **Given** a fabric DCI IP pool is available, **When** a valid DCI-role Network Link is generated, **Then** exactly one /31 network is allocated from that pool for the link.

---

### User Story 4 - Generate L3 Edge Intent (Priority: P1)

As a network operator, I need valid DCI-role Network Links between Border Leafs to appear in generated AVD intent so device artifacts include the required point-to-point L3 edge configuration.

**Why this priority**: The modeled data only delivers value when generated hostvars include complete L3 edge intent.

**Independent Test**: Model multiple DCI-role Network Links from one Border Leaf to remote Border Leafs, run generation, and confirm deterministic `l3_edge.p2p_links` output with invalid links reported and excluded.

**Acceptance Scenarios**:

1. **Given** two Border Leaf devices are connected by a valid Network Link with role `dci`, **When** AVD device intent is generated, **Then** the generated output contains one `l3_edge.p2p_links` entry for that link.
2. **Given** one Border Leaf has multiple valid DCI-role Network Links, **When** AVD device intent is generated for that node, **Then** generated DCI entries are deterministic and complete.
3. **Given** DCI links have per-link operational settings, **When** AVD device intent is generated, **Then** no shared point-to-point link profile is emitted for DCI links.
4. **Given** a DCI-role Network Link is incomplete or uses a non-Border Leaf endpoint, **When** AVD device intent is generated, **Then** the generator excludes it and reports actionable context.

### Edge Cases

- A DCI-role Network Link endpoint references a device without the Border Leaf role.
- A DCI-role Network Link endpoint references an interface that does not belong to the selected endpoint device.
- Both endpoints reference the same Border Leaf device or the same interface.
- Two DCI-role Network Links use the same endpoint interface pair.
- Multiple parallel DCI-role Network Links connect the same pair of Border Leaf devices.
- A DCI-role Network Link has no fabric DCI IP pool available for /31 point-to-point allocation.
- A fabric DCI IP pool does not have enough available /31 networks for all valid DCI links.
- A Network Link has role `dci` but lacks one or both BGP ASN values required for complete generated L3 edge intent.
- Existing ordinary Network Link objects must remain valid and must not be treated as DCI links unless their role is `dci`.
- Any `NetworkDciLink` schema, query, menu, documentation, test, generated protocol, or generator reference remains after this update.
- Multiple DCI-role Network Links affect the same pair of Border Leafs and must result in deterministic generated ordering.
- Generator-side eligibility rules reject a DCI-role Network Link that schema constraints allow because the rule depends on derived endpoint or role data.
- Duplicate `allocate_p2p_prefix_from_pool` helper implementations remain without an explicit consolidation or justification decision.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST add a Border Leaf device role choice to the existing network device role model without removing existing choices: Super Spine, Spine, Leaf, and L2 Leaf.
- **FR-002**: Border Leaf MUST map to AVD l3leaf behavior for downstream artifact generation.
- **FR-003**: DCI links MUST be modeled as existing Network Link objects with role `dci`.
- **FR-004**: The feature MUST NOT define, expose, or depend on a separate `NetworkDciLink` node.
- **FR-005**: Existing Network Link behavior for non-DCI links MUST remain unchanged.
- **FR-006**: The Network Link role model MUST support a stable machine value `dci` with a readable DCI label.
- **FR-007**: The DCI role on Network Link MUST preserve the existing connected endpoint model and compatible Network Link identity/display behavior.

#### Attributes

- **FR-010**: DCI-specific direct attributes on Network Link MUST be limited to role `dci`, `include_in_underlay_protocol`, and the BGP ASN values required to build the generated `as` list.
- **FR-011**: `include_in_underlay_protocol` MUST default to enabled for DCI-role Network Links.
- **FR-012**: DCI-role Network Links MUST support the BGP ASN values required for both endpoints.
- **FR-013**: DCI-role Network Links MUST NOT define a DCI-specific user-selectable underlay protocol field; this feature supports BGP underlay behavior for generated DCI links.
- **FR-014**: DCI-role Network Links MUST NOT define DCI-specific `enabled`, endpoint A/B device/interface, subnet, `p2p_pool`, `p2p_link_id`, endpoint IP, endpoint description, BFD, MTU, name, or description attributes.
- **FR-015**: Point-to-point addressing intent MUST come from `NetworkFabric.dci_pool`; one /31 network MUST be allocated for each generated DCI-role Network Link.
- **FR-016**: Allocated point-to-point IP values MUST NOT be stored as direct DCI-specific endpoint IP attributes on Network Link.
- **FR-017**: New attributes added to existing nodes MUST be optional or have safe defaults so existing data remains valid after schema load.
- **FR-018**: All new Dropdown attributes MUST define explicit choices with stable machine names and readable labels.

#### Relationships

- **FR-020**: A DCI-role Network Link MUST use the existing Network Link connected endpoint relationship model to resolve exactly two endpoint devices and two endpoint interfaces.
- **FR-021**: Both endpoint devices of a DCI-role Network Link MUST be network devices with the Border Leaf role before the link is eligible for DCI artifact generation.
- **FR-022**: Each endpoint interface MUST belong to its corresponding endpoint device before the link is eligible for DCI artifact generation.
- **FR-023**: DCI-role Network Links MUST NOT introduce DCI-specific endpoint device, endpoint interface, or addressing relationships.
- **FR-024**: The DCI model MUST allow the generator to derive node names, interface names, ASN values, and point-to-point addressing from Network Link endpoints, DCI-specific Network Link fields, and `NetworkFabric.dci_pool`.
- **FR-025**: External network and EVPN Gateway relationships MUST NOT be mandatory for DCI links in this feature.

#### Generator Output

- **FR-030**: Generator behavior MUST emit AVD `l3_edge` intent for valid Network Links with role `dci`.
- **FR-031**: Generated `l3_edge` intent MUST include both Border Leaf endpoints, their endpoint interfaces, BGP ASN values, and point-to-point addressing allocated from `NetworkFabric.dci_pool`.
- **FR-032**: Generated `l3_edge` intent MUST explicitly emit `include_in_underlay_protocol` for every DCI-role Network Link.
- **FR-033**: Generated DCI `l3_edge` intent MUST NOT emit or rely on `l3_edge.p2p_links_profiles`.
- **FR-034**: Generated DCI `l3_edge.p2p_links` entries MUST carry DCI operational settings directly on each link entry.
- **FR-035**: Generated DCI `l3_edge.p2p_links` entries MUST emit `nodes`, `interfaces`, `as`, `ip`, and `include_in_underlay_protocol`; they MUST emit `speed` only when endpoint/interface data provides a resolvable speed.
- **FR-036**: Generated DCI `l3_edge.p2p_links` entries MUST NOT emit `profile` solely to reference a shared DCI profile.
- **FR-037**: Generated `nodes`, `interfaces`, `as`, and `ip` lists MUST preserve endpoint ordering consistently so each list position describes the same side of the DCI link.
- **FR-038**: Generator behavior MUST validate DCI eligibility rules that depend on derived data, including exactly two Border Leaf endpoint devices, endpoint interface ownership, no same-device endpoint pair, BGP ASN availability, and successful /31 allocation from `NetworkFabric.dci_pool`.
- **FR-039**: Generator behavior MUST be idempotent: repeated generation from unchanged DCI-role Network Link data must produce the same generated intent without duplicate or stale entries.
- **FR-040**: Generator behavior MUST use deterministic ordering for generated DCI links so artifact diffs are stable across repeated runs.
- **FR-041**: Generator behavior MUST report incomplete or ineligible DCI-role Network Links with enough context for operators to correct source data.
- **FR-042**: This phase MUST NOT require a dedicated check implementation when schema constraints and generator-side eligibility rules can enforce or report required behavior.

#### Removal & Migration

- **FR-050**: `NetworkDciLink` MUST be removed from schema definitions, generated protocols, generated GraphQL schema, generator queries, generated query models, generator logic, menus, documentation, and tests.
- **FR-051**: Planning MUST include a migration decision for any existing DCI data: either convert it to Network Link role `dci` or document that no persistent `NetworkDciLink` data exists to migrate.
- **FR-052**: Protocol classes MUST be regenerated after schema changes and MUST no longer include `NetworkDciLink` classes.
- **FR-053**: GraphQL schema and return types MUST be regenerated after query/schema changes and MUST no longer include `NetworkDciLink` query models.
- **FR-054**: Tests MUST assert that DCI behavior is sourced from Network Link role `dci` and that stale `NetworkDciLink` references are absent.
- **FR-055**: Documentation MUST describe DCI as Network Link role `dci`, not as a separate DCI link object.
- **FR-056**: Menus MUST NOT expose a `NetworkDciLink` item; existing Network Link navigation must remain suitable for DCI-role links.
- **FR-057**: Planning/tasks MUST include a decision to consolidate duplicate `allocate_p2p_prefix_from_pool` helpers or explicitly justify why both helpers must remain.

### Key Entities

- **Border Leaf Role**: A network device role choice for leaf-family devices that connect to DCI links and map to AVD l3leaf behavior.
- **Network Link**: The existing physical link entity. A link with role `dci` represents one point-to-point DCI connection between two Border Leaf devices.
- **Network Link Role**: A role discriminator on Network Link. The `dci` value selects DCI generation behavior while preserving ordinary Network Link behavior for all other values.
- **DCI IP Pool**: The IPAM allocation source assigned through `NetworkFabric.dci_pool`; each generated DCI-role Network Link receives exactly one /31 network from this pool.
- **Generated L3 Edge Intent**: The generated AVD data derived from valid DCI-role Network Links, with one self-contained `p2p_links` entry per valid DCI link.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Schema validation passes with zero errors after the Network Link role and DCI pool changes.
- **SC-002**: Existing device role choices remain available, and Border Leaf appears as an additional role choice.
- **SC-003**: Existing ordinary Network Link data remains valid and does not generate DCI intent unless role is `dci`.
- **SC-004**: A user can model a complete DCI link between two Border Leaf devices by creating a Network Link with role `dci` and two endpoint interfaces.
- **SC-005**: Repository validation finds zero remaining `NetworkDciLink` references in schema, query, menu, docs, tests, generated protocols, and generator intent.
- **SC-006**: For each valid DCI-role Network Link, generated L3 edge input resolves both node names, both interface names, both BGP ASN values, both point-to-point IP values, optional link speed when endpoint/interface data provides it, and underlay participation.
- **SC-007**: Duplicate active DCI-role Network Links using the same endpoint interface pair are prevented by schema constraints or reported before artifact generation.
- **SC-008**: For a valid DCI-role Network Link between two Border Leafs, generated device intent includes exactly one corresponding `l3_edge.p2p_links` entry with `nodes`, `interfaces`, `as`, `ip`, `include_in_underlay_protocol`, and `speed` only when resolvable.
- **SC-009**: Re-running generation against unchanged DCI-role Network Link data produces no duplicate DCI entries and no unexpected changes in generated artifacts.
- **SC-010**: Invalid DCI-role Network Links are either blocked by schema constraints or excluded by generator behavior with actionable reporting.
- **SC-011**: Generated device intent does not include DCI `l3_edge.p2p_links_profiles`, `profile`, or shared DCI profile references.
- **SC-012**: The duplicate `allocate_p2p_prefix_from_pool` helper situation is resolved by consolidation or by a documented justification with tests covering the chosen behavior.

## Assumptions

- The stable machine value for the Border Leaf role remains `border_leaf`, with display label "Border Leaf".
- Border Leaf maps to AVD l3leaf behavior for downstream artifact generation.
- The stable machine value for the Network Link DCI role is `dci`, with display label "DCI".
- External network modeling is out of scope for this feature.
- EVPN Gateway configuration is out of scope for this feature.
- `NetworkFabric.dci_pool` is the authoritative DCI IP pool selector for this phase.
- A pool is considered DCI-dedicated by assignment to `NetworkFabric.dci_pool`; this feature does not add DCI prefix role metadata, a direct DCI link pool field, or DCI-specific pool relationships.
- DCI link speed is inferred from endpoint/interface data when available. If no speed can be resolved, the generator omits the `speed` key from the generated DCI `p2p_links` entry.
- Validation of role/interface consistency should be handled by schema constraints where possible and generator-side eligibility rules where derived data is required.
- The project targets pyAVD 6.3.x, so generated DCI-related fields must be confirmed against that pinned version.
