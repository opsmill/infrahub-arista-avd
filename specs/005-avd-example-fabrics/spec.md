# Schema Design Specification: AVD Example Fabric Designs

> **This feature has schema-first scope but spans generator and object (seed design) work.** The implementing agent MUST use the `infrahub-managing-schemas` skill for schema definitions, the `infrahub-managing-generators` skill for topology generation, and the `infrahub-managing-objects` skill for the per-scenario seed designs. Schema is the first cycle; generator and objects follow in later `/speckit.specify` cycles.

**Feature Branch**: `005-avd-example-fabrics`
**Created**: 2026-07-22
**Status**: Draft
**Input**: User description: "lets ensure we have a fabric design for each of these scenarios and close the gaps either with native schema changes or using the escape hatch when it is needed."

## Context

The scenarios are the seven official Arista AVD 6.2 example designs:

1. **Single-DC L3LS** — 3-stage leaf-spine, eBGP underlay, EVPN/VXLAN symmetric IRB.
2. **Single-DC Multi-Pod L3LS (5-stage Clos)** — super-spine layer, EVPN route servers, vlan-aware-bundles.
3. **Dual-DC L3LS** — twin DCs joined by DCI, EVPN DC Gateway (next-hop-self at gateways).
4. **L2LS Fabric** — standalone Layer-2 leaf-spine, no underlay/overlay, optional L3 on spines.
5. **Campus Fabric** — three-tier MDF/IDF, OSPF underlay to WAN edge, dot1x/PoE/port-profiles/in-band management.
6. **ISIS-LDP IPVPN** — MPLS WAN core, ISIS-LDP underlay, BGP VPN-IPv4 overlay, P/PE/RR roles.
7. **CV-Pathfinder** — SD-WAN with CVaaS-driven path selection, DPS, application-aware virtual topologies.

A prior gap analysis established the current reference design supports scenario 1 fully, scenario 2 mostly (missing super-spine `evpn_role` and vlan-aware-bundle inputs), and scenario 3 partially (DCI links render but no multi-DC seed/generator and no EVPN DC Gateway). Scenarios 4–7 are unsupported: no standalone L2LS design, no campus roles/features, no ISIS/LDP/MPLS/VPN-IPv4, and no WAN/SD-WAN model. The underlay protocol choice is limited to `ebgp`/`ospf` and the overlay to BGP/EVPN.

The goal is that **each scenario has a demonstrable fabric design** in this repository — a loadable seed design that, after running the generator chain, renders valid PyAVD EOS configuration matching the intent of the corresponding AVD example. Gaps are closed by **native schema changes** where the capability is core and reusable, or by the **`avd_custom_hostvars` escape hatch** where a full native model would be disproportionate for a niche or one-off capability.

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

---

## Native vs. Escape Hatch Decision Principle *(applies to every story)*

Each gap-closing item MUST be classified as **native** or **escape hatch** using this principle, and the classification recorded:

- **Native schema change** is preferred when the capability is: reused across more than one scenario; a first-class topology/role/protocol concept operators select in the UI; or something that must be validated, allocated (pools), or generated deterministically.
- **`avd_custom_hostvars` escape hatch** is acceptable when the capability is: specific to a single scenario; a pass-through of PyAVD keys that need no allocation or cross-device derivation; or an area where a native model would be premature before real demand. Escape-hatch usage MUST be captured as reproducible seed data (not manual UI edits) so the design remains demonstrable and idempotent.

Escape-hatch use is a deliberate, documented choice per capability — not a default fallback to avoid modeling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-DC L3LS Reference Design (Priority: P1)

As a reference-design consumer, I need a canonical Single-DC L3LS seed design so the baseline EVPN/VXLAN scenario is demonstrable end to end without manual authoring.

**Why this priority**: This scenario is already supported by the schema and generators; the only gap is a curated, documented seed design that proves it. It is the lowest-risk, highest-confidence deliverable and validates the demonstrability harness the other stories depend on.

**Independent Test**: Load the Single-DC L3LS seed design onto a branch, run the generator chain, and confirm EOS configuration renders for spines, L3 leaves (MLAG pairs), and L2 leaves with eBGP underlay and EVPN symmetric IRB.

**Acceptance Scenarios**:

1. **Given** a clean Infrahub instance, **When** the Single-DC L3LS seed design is loaded and generated, **Then** every device renders valid EOS configuration.
2. **Given** the rendered fabric, **When** its intent is compared to the AVD Single-DC L3LS example, **Then** it demonstrates eBGP underlay, EVPN/VXLAN symmetric IRB, MLAG leaf pairs, L2+L3 VLAN services, and server port-channels.
3. **Given** no schema changes are made for this story, **When** validation runs, **Then** the design relies only on existing capabilities.

---

### User Story 2 - Multi-Pod 5-Stage Clos Design (Priority: P1)

As a network designer, I need a 5-stage Clos design with super-spines acting as EVPN route servers and vlan-aware-bundle tenants so the multi-pod scenario is demonstrable.

**Why this priority**: The topology already generates; only two small, reusable inputs are missing (`evpn_role` on super-spines and a vlan-aware-bundles toggle). Closing these delivers a full scenario at low cost.

**Independent Test**: Load a two-pod fabric with super-spines, run generation, and confirm super-spines render as EVPN route servers and tenant VLANs render as vlan-aware-bundles with route targets.

**Acceptance Scenarios**:

1. **Given** a fabric with `amount_of_super_spines > 0` and two pods, **When** generated, **Then** spine-to-super-spine cabling and eBGP underlay across all tiers render.
2. **Given** super-spines in the design, **When** generated, **Then** each super-spine renders with an EVPN route-server role.
3. **Given** a tenant configured for vlan-aware-bundles, **When** generated, **Then** the tenant renders as a vlan-aware-bundle with correct route targets.

---

### User Story 3 - Dual-DC L3LS Design With EVPN DC Gateway (Priority: P1)

As a network designer, I need a two-DC design connected by DCI links with EVPN DC Gateway behavior so the dual-DC scenario is demonstrable end to end.

**Why this priority**: DCI links already render; the remaining gaps are a reproducible multi-DC seed design and the EVPN DC Gateway (next-hop-self at gateways) capability that distinguishes this scenario.

**Independent Test**: Load two fabrics with border leaves connected by `dci` Network Links and EVPN DC Gateway enabled, run generation, and confirm inter-DC L3 edge and gateway next-hop-self render on the gateway leaves.

**Acceptance Scenarios**:

1. **Given** two fabrics with border leaves joined by `dci` Network Links, **When** generated, **Then** `l3_edge.p2p_links` render across the DCI.
2. **Given** EVPN DC Gateway is enabled on gateway leaves, **When** generated, **Then** those leaves render next-hop-self / gateway behavior in the EVPN overlay.
3. **Given** the dual-DC seed design, **When** loaded, **Then** both DCs and their DCI links are created reproducibly from seed data, not manual UI edits.

---

### User Story 4 - Standalone L2LS Fabric Design (Priority: P2)

As a network designer, I need a standalone Layer-2 leaf-spine fabric (no EVPN/underlay) with an optional L3-on-spine variant so the L2LS scenario is demonstrable.

**Why this priority**: Requires new native roles (`l2spine`/`l3spine`) and an "underlay: none" mode; distinct from the L2-access tier that currently only attaches under an L3LS fabric. Reusable, but larger than the P1 stories.

**Independent Test**: Load an L2LS design (2 spines, 4 leaves, MLAG on both tiers), run generation, and confirm pure-L2 EOS renders with VLANs tag-filtered per leaf pair and no EVPN/BGP underlay; then convert spines to the L3 variant and confirm SVI routing renders.

**Acceptance Scenarios**:

1. **Given** an L2LS design with `l2spine` and `l2leaf` roles, **When** generated, **Then** devices render Layer-2 config with MLAG and VLAN tag filtering and no EVPN/underlay routing.
2. **Given** an L2LS design switched to the `l3spine` variant, **When** generated, **Then** spines render SVI L3 routing with virtual-router MAC.
3. **Given** the new roles are added, **When** existing L3LS designs are generated, **Then** their behavior is unchanged.

---

### User Story 5 - Campus Fabric Design (Priority: P2)

As a campus network designer, I need a three-tier campus design with OSPF to the WAN edge, dot1x/NAC, PoE, port profiles, and in-band management so the campus scenario is demonstrable.

**Why this priority**: Combines a reusable native concern (campus roles, OSPF-to-edge — OSPF underlay already exists) with several campus-specific features better suited to the escape hatch initially (dot1x, PoE, port profiles, in-band management SVI).

**Independent Test**: Load a campus design (spine core + IDF access leaves incl. a hierarchical aggregation/edge tier), run generation, and confirm OSPF underlay, spine SVI routing, and campus access features render.

**Acceptance Scenarios**:

1. **Given** a campus design with core spines and IDF access leaves, **When** generated, **Then** OSPF underlay and spine SVI L3 routing (Data/Voice/Guest VLANs, virtual-router MAC) render.
2. **Given** access ports configured for dot1x and PoE, **When** generated, **Then** the corresponding dot1x and PoE configuration renders (via native fields or escape hatch, per the decision principle).
3. **Given** a hierarchical IDF (aggregation feeding edge leaves), **When** generated, **Then** the aggregation-to-edge tier renders correctly.

---

### User Story 6 - ISIS-LDP IPVPN WAN Design (Priority: P3)

As a WAN engineer, I need an MPLS core design with ISIS-LDP underlay and BGP VPN-IPv4 overlay so the ISIS-LDP IPVPN scenario is demonstrable.

**Why this priority**: An entirely new routing domain (ISIS, LDP, MPLS, VPN-IPv4, P/PE/RR roles, routed subinterfaces, PE-CE OSPF). Highest effort; primarily escape-hatch-driven with minimal native anchors (roles and the ISIS-LDP underlay selector).

**Independent Test**: Load an ISIS-LDP IPVPN design (P, PE, RR devices) and confirm it renders ISIS-LDP underlay, MPLS L3VPN with VPN-IPv4 overlay, per-customer VRFs, and PE-CE routing.

**Acceptance Scenarios**:

1. **Given** a WAN design with P/PE/RR devices, **When** generated, **Then** ISIS-LDP underlay and LDP MPLS label distribution render.
2. **Given** per-customer VRFs on PEs, **When** generated, **Then** BGP VPN-IPv4 overlay with RR peering and per-VRF PE-CE routing render.
3. **Given** the ISIS-LDP underlay selector is added, **When** an existing eBGP/OSPF design is generated, **Then** its underlay behavior is unchanged.

---

### User Story 7 - CV-Pathfinder SD-WAN Design (Priority: P3)

As a WAN engineer, I need a CV-Pathfinder SD-WAN design with path groups, DPS, and application-aware virtual topologies so the CV-Pathfinder scenario is demonstrable.

**Why this priority**: An entirely new SD-WAN domain (wan_rr/wan_router roles, CV-Pathfinder/AutoVPN, DPS, path groups, virtual topologies, WAN HA, STUN, CVaaS integration). Highest effort and most external-dependency-bound; primarily escape-hatch-driven.

**Independent Test**: Load a CV-Pathfinder design (pathfinders + edge/transit routers across sites) and confirm it renders WAN roles, path groups (MPLS/INTERNET), DPS, and application-aware policies.

**Acceptance Scenarios**:

1. **Given** a design with pathfinder and WAN edge/transit routers, **When** generated, **Then** CV-Pathfinder roles, path groups, and DPS render.
2. **Given** application-aware virtual topologies (VOICE/VIDEO/DATA), **When** generated, **Then** the policies and their constraints render.
3. **Given** a site with EVPN gateway or WAN HA, **When** generated, **Then** the corresponding overlay/HA behavior renders.

### Edge Cases

- A new device role (`l2spine`, `l3spine`, campus, P/PE/RR, wan_rr/wan_router) is added but has no `ROLE_TO_AVD_TYPE` mapping, producing devices with no valid AVD node type.
- A design selects an underlay of "none" (L2LS) but references underlay-only pools or settings that then have no meaning.
- A new underlay protocol value (e.g. `isis-ldp`) is added but the hostvar generator has no branch to emit it, silently falling back to a default.
- Escape-hatch `avd_custom_hostvars` supplies keys the pinned PyAVD version does not accept, causing render failure.
- Escape-hatch keys collide with generator-produced keys; deep-merge precedence must remain deterministic (generated values win, per existing behavior).
- A scenario seed design is added but no idempotence guarantee exists, so re-running generation produces churn.
- Adding new role choices changes existing devices' behavior because a generator keys on role membership.
- A multi-DC design reuses fabric-scoped names across DCs, causing human-friendly-id or uniqueness collisions.
- A campus hierarchical IDF has an aggregation leaf with no edge children, or an edge leaf with no aggregation parent.
- A WAN/SD-WAN design depends on CloudVision/CVaaS that is unavailable in the demonstration environment; the design must still render device configuration offline.
- New mandatory attributes on existing nodes have no default, invalidating already-loaded L3LS data.

## Requirements *(mandatory)*

### Functional Requirements

#### Scenario Coverage

- **FR-001**: The reference design MUST provide a demonstrable fabric design for each of the seven AVD example scenarios listed in Context.
- **FR-002**: Each scenario design MUST be reproducible from loadable seed data (objects and, where used, `avd_custom_hostvars`), not from manual UI edits.
- **FR-003**: Each scenario design MUST, after running the generator chain, render valid PyAVD EOS configuration for every device it defines.
- **FR-004**: Each scenario design's rendered intent MUST demonstrate the defining capabilities of the corresponding AVD example (as enumerated per user story).
- **FR-005**: Every gap-closing item MUST be classified as native or escape hatch per the Decision Principle, and the classification MUST be recorded in the design's documentation.

#### Nodes, Generics & Roles

- **FR-010**: Schema MUST add device role choices required by unsupported scenarios without removing existing choices (`super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`).
- **FR-011**: Each new device role MUST have a corresponding `ROLE_TO_AVD_TYPE` mapping so every device resolves to a valid AVD node type.
- **FR-012**: L2LS MUST be supported as a standalone fabric design via `l2spine` and `l3spine` roles (distinct from the existing L2-access tier under an L3LS fabric).
- **FR-013**: Campus, ISIS-LDP IPVPN, and CV-Pathfinder roles MUST be added only where a native role is required for topology generation or AVD node-type mapping; scenario-specific behavior beyond role/type MAY use the escape hatch.
- **FR-014**: All new role machine values MUST be snake_case with stable values and readable labels, and MUST NOT alter the machine values of existing roles.

#### Attributes & Protocols

- **FR-020**: Schema MUST allow super-spines to render an EVPN route-server role for the 5-stage Clos scenario.
- **FR-021**: Schema MUST provide an input controlling vlan-aware-bundle rendering for tenants used by the 5-stage Clos scenario.
- **FR-022**: Schema MUST support an EVPN DC Gateway capability (next-hop-self at gateway leaves) for the dual-DC scenario, applied to designated gateway devices.
- **FR-023**: Schema MUST support an "underlay: none" mode for the standalone L2LS scenario so no EVPN/underlay routing is required.
- **FR-024**: The `underlay_routing_protocol` choice set MUST be extended to cover new scenarios only where native (e.g. ISIS-LDP), with each new value handled by the hostvar generator rather than silently defaulted.
- **FR-025**: New attributes added to existing nodes MUST be optional or carry safe defaults so existing L3LS data remains valid after schema load.
- **FR-026**: All new Dropdown attributes MUST define explicit `choices` with stable machine names and readable labels.
- **FR-027**: Attribute types MUST use valid kinds (Text, Number, Boolean, Dropdown, IPHost, IPNetwork, JSON, etc.) and MUST NOT use the deprecated `String` kind.

#### Escape Hatch

- **FR-030**: Capabilities classified as escape hatch MUST be delivered through the existing `avd_custom_hostvars` mechanism at fabric, pod, or device scope.
- **FR-031**: Escape-hatch content MUST deep-merge with generated hostvars using the existing precedence (generator-produced values win) and MUST NOT require changes to that precedence.
- **FR-032**: Escape-hatch keys used by any scenario design MUST be accepted by the pinned PyAVD version.
- **FR-033**: Escape-hatch usage MUST be captured in seed data so the scenario remains demonstrable and idempotent across repeated generation.

#### Relationships & Topology Generation

- **FR-040**: New roles that participate in topology MUST integrate with the generator chain so devices, cabling, and group membership are created for their scenario.
- **FR-041**: The dual-DC scenario MUST be able to represent two fabrics and their DCI links from seed data; if a generator assists multi-DC/DCI creation, it MUST be idempotent and deterministic.
- **FR-042**: The campus scenario MUST support a hierarchical access tier (aggregation leaves feeding edge leaves) within an IDF.
- **FR-043**: All relationship `peer` values MUST use the full kind (Namespace + Name) and all Component/Parent pairs MUST use matching `identifier` values on both sides.

#### Idempotence, Migration & Regeneration

- **FR-050**: Re-running the generator chain against unchanged scenario seed data MUST produce no churn (checksum-based change detection preserved).
- **FR-051**: Removed attributes MUST use `state: absent` rather than being deleted from the YAML.
- **FR-052**: Generated protocol classes and GraphQL return types MUST be regenerated after schema/query changes; generated files MUST NOT be hand-edited.
- **FR-053**: Adding roles or attributes MUST NOT change the behavior or rendered output of the already-supported Single-DC L3LS scenario except where explicitly intended.

#### Documentation

- **FR-060**: `docs/docs/supported-capabilities.md` MUST be updated to reflect the status of each of the seven scenarios after this feature.
- **FR-061**: Each scenario design MUST have documentation stating its native-vs-escape-hatch classification and how to load and generate it.

### Key Entities

- **Fabric Design (per scenario)**: A reproducible set of seed objects (and any `avd_custom_hostvars`) representing one AVD example scenario, sufficient to render EOS config for all its devices.
- **Device Role**: The role discriminator on network devices; new values (`l2spine`, `l3spine`, campus, P/PE/RR, wan_rr/wan_router) extend the existing set and each maps to an AVD node type.
- **Underlay Mode / Protocol**: The fabric underlay selection, extended to include "none" (L2LS) and, where native, ISIS-LDP; drives generator branches.
- **EVPN Route Server / DC Gateway Capability**: Fabric/device-level EVPN behaviors enabling super-spine route servers (5-stage Clos) and gateway next-hop-self (dual-DC).
- **Escape-Hatch Payload (`avd_custom_hostvars`)**: Scenario-specific PyAVD keys supplied at fabric/pod/device scope, deep-merged with generated hostvars, used where a native model is disproportionate.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `infrahubctl schema check schemas/` passes with zero validation errors after all schema changes.
- **SC-002**: All seven AVD example scenarios have a loadable seed design in the repository; loading and generating each produces valid EOS configuration for every device with zero render errors.
- **SC-003**: Existing device role choices and existing Single-DC L3LS designs remain valid and unchanged after schema load and regeneration.
- **SC-004**: For each scenario, the rendered output demonstrates the scenario's defining capabilities (per that story's acceptance scenarios).
- **SC-005**: Every new device role resolves to a valid AVD node type; no generated device is left without a node-type mapping.
- **SC-006**: Re-running generation against unchanged scenario seed data produces no diffs in generated artifacts (idempotence holds for all seven designs).
- **SC-007**: Every gap-closing item is documented as native or escape hatch, and 100% of escape-hatch keys are accepted by the pinned PyAVD version.
- **SC-008**: Generated protocol classes and GraphQL return types are regenerated and contain the new roles/attributes with no hand edits.
- **SC-009**: `docs/docs/supported-capabilities.md` reflects the post-feature status of all seven scenarios.

## Assumptions

- The seven scenarios are exactly the AVD 6.2 examples: single-dc-l3ls, single-dc-multipod-l3ls (5-stage Clos), dual-dc-l3ls, l2ls-fabric, campus-fabric, isis-ldp-ipvpn, cv-pathfinder.
- "A fabric design exists" means a reproducible seed design that renders valid EOS config offline; it does not require live deployment to hardware or CloudVision/CVaaS for the WAN/SD-WAN scenarios.
- Native schema changes are preferred for reusable, first-class, or allocation/validation-bearing capabilities; the `avd_custom_hostvars` escape hatch is the deliberate choice for niche, single-scenario, pass-through capabilities.
- The project targets pyAVD 6.3.x; all rendered scenario intent and escape-hatch keys must be confirmed against that pinned version.
- Scenarios 1–3 are P1 (fully or mostly supported today), 4–5 are P2 (new native roles/modes), 6–7 are P3 (new domains, escape-hatch-led), reflecting effort and dependency, not desirability.
- This spec is the schema-first cycle; the generator paths (standalone L2LS, campus tiers, multi-DC assistance) and the per-scenario seed objects are delivered in subsequent `/speckit.specify` cycles for generator and objects, informed by the schema decisions made here.
- Border Leaf continues to map to AVD l3leaf; no existing role machine value changes.
