# Generator Specification: AVD Example Fabric Designs (Generator + Objects)

> **Workflow type**: Infrahub Generator (design-driven automation) **and** Object population.
> **Skills**: Use the `infrahub-managing-generators` skill for generator work and the `infrahub-managing-objects` skill for the per-scenario seed designs. Generator is the primary artifact type for this cycle; the seed objects are delivered in the same feature because a design cannot be demonstrated without both.

**Feature Branch**: `006-avd-example-designs`
**Created**: 2026-07-22
**Status**: Draft
**Input**: User description: "can you do the generator and object cycles please"

## Context

Feature `005-avd-example-fabrics` (schema cycle) added the schema surface for the seven AVD 6.2 example scenarios: new device roles (`l2spine`, `l3spine`, `p`, `pe`, `rr`, `wan_router`, `wan_rr`) with `ROLE_TO_AVD_TYPE` mappings, the `evpn_vlan_aware_bundles` fabric input, the `evpn_gateway` device flag, and the `none`/`isis-ldp` underlay choices. It deferred two things to this cycle:

1. **Generator consumption** — building the topology for the new designs and rendering the new inputs into PyAVD hostvars.
2. **Seed designs (objects)** — one loadable reference design per scenario, in the Fabric-C style (its own numbered `objects/` files), so each scenario is demonstrable end to end.

This feature delivers both. The goal is unchanged from `005`: **each of the seven scenarios has a demonstrable fabric design** that, from a clean load plus the generator chain, renders valid PyAVD EOS configuration matching the AVD example's intent, idempotently. Gaps are closed natively where reusable and via the `avd_custom_hostvars` escape hatch where niche (per the classification recorded in `005`).

## Generator Overview

**Design Object (Source)**: `NetworkFabric` (and its `NetworkPod` / `LocationRack` children) — the existing fabric design hierarchy, extended so its generators honor the new roles, underlay modes, and EVPN inputs. WAN/provider scenarios use directly-seeded devices rather than the leaf-spine topology generators (see Assumptions).

**Generated Objects (Targets)**: `DcimDevice`, `DcimInterface`, `NetworkLink`, and per-device `AvdHostvarFile` / `AvdStructuredConfigFile` content — as today, extended to the new roles and inputs.

**Target Groups**: existing `fabrics`, `pods`, `racks`, and `avd_devices` generator groups.

## Delivery model per scenario

| Scenario | Topology source | Generator work | Seed objects |
|----------|-----------------|----------------|--------------|
| 1 Single-DC L3LS | fabric/pod/rack generators | none (baseline) | curated seed design |
| 2 Multi-Pod 5-stage Clos | fabric/pod/rack generators | consume `evpn_vlan_aware_bundles`; derive super-spine `evpn_role: server` | seed design (2 pods + super-spines) |
| 3 Dual-DC L3LS | fabric/pod/rack generators + DCI links | render `evpn_gateway` next-hop-self | two fabrics + `dci` NetworkLinks |
| 4 L2LS (standalone) | fabric/pod/rack generators | L2LS branch: `l2spine`/`l3spine`, underlay `none` | seed design |
| 5 Campus | fabric/pod/rack generators | campus branch: `l3spine` core, hierarchical IDF, OSPF; escape-hatch access features | seed design + escape-hatch payloads |
| 6 ISIS-LDP IPVPN | directly-seeded devices | `p`/`pe`/`rr` node types + `isis-ldp` underlay; escape-hatch MPLS/VPN-IPv4 | seed devices + escape-hatch payloads |
| 7 CV-Pathfinder | directly-seeded devices | `wan_router`/`wan_rr` node types; escape-hatch SD-WAN | seed devices + escape-hatch payloads |

> Note: pyAVD 6.3 has no global `design.type`. Per-device behavior is driven by each node's `type` plus the built-in `node_type_keys` defaults (e.g. `p`/`pe`/`rr` default to isis-sr underlay, iBGP overlay, and MPLS roles; `l2spine` is non-routing; `wan_*` carry WAN defaults). The generators set the correct `type` (already mapped in `005`) and supply scenario inputs natively or via the escape hatch — no design-type switch is needed.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-DC L3LS seed design renders (Priority: P1)

As a reference-design consumer, I want a loadable Single-DC L3LS seed design so the baseline scenario is demonstrable end to end without manual authoring.

**Why this priority**: Lowest risk (no generator change), and it validates the load → generate → render demonstrability harness every other story reuses.

**Independent Test**: Load the Single-DC L3LS seed design on a clean branch, run the generator chain, and confirm EOS config renders for all devices with eBGP underlay and EVPN symmetric IRB.

**Acceptance Scenarios**:

1. **Given** a clean branch with schema loaded, **When** the seed design is loaded and the generator chain runs, **Then** every device produces valid EOS configuration with zero render errors.
2. **Given** the generated design, **When** generation is re-run with no changes, **Then** no artifact diffs are produced (idempotent).

---

### User Story 2 - Multi-Pod 5-stage Clos renders (Priority: P1)

As a network designer, I want a 5-stage Clos seed design where super-spines act as EVPN route servers and tenants render as vlan-aware bundles, so the multi-pod scenario is demonstrable.

**Why this priority**: The topology already generates; only two small render behaviors are missing. High value, low effort.

**Independent Test**: Load a two-pod fabric with super-spines and `evpn_vlan_aware_bundles` enabled, generate, and confirm super-spines render as EVPN route servers and tenants render as vlan-aware bundles.

**Acceptance Scenarios**:

1. **Given** a fabric with super-spines and two pods, **When** generation runs, **Then** super-spines render with an EVPN route-server role and spine↔super-spine eBGP underlay.
2. **Given** `evpn_vlan_aware_bundles` is enabled, **When** generation runs, **Then** tenant L2 services render as vlan-aware bundles with route targets.
3. **Given** re-run with no changes, **Then** no artifact diffs (idempotent).

---

### User Story 3 - Dual-DC L3LS with EVPN DC Gateway renders (Priority: P1)

As a network designer, I want a two-DC seed design connected by DCI links with EVPN DC Gateway behavior, so the dual-DC scenario is demonstrable.

**Why this priority**: DCI links already render; the remaining gaps are the reproducible multi-DC seed and gateway next-hop-self rendering.

**Independent Test**: Load two fabrics joined by `dci` NetworkLinks with `evpn_gateway` set on the gateway leaves, generate, and confirm inter-DC L3 edge and gateway next-hop-self render on those leaves.

**Acceptance Scenarios**:

1. **Given** two fabrics with border leaves joined by `dci` NetworkLinks, **When** generation runs, **Then** `l3_edge.p2p_links` render across the DCI.
2. **Given** `evpn_gateway` is set on gateway leaves, **When** generation runs, **Then** those leaves render EVPN DC Gateway next-hop-self behavior.
3. **Given** the seed design, **When** loaded from clean, **Then** both DCs and their DCI links are created reproducibly from seed data.

---

### User Story 4 - Standalone L2LS fabric renders (Priority: P2)

As a network designer, I want a standalone Layer-2 leaf-spine seed design (no EVPN/underlay) with an optional L3-on-spine variant, so the L2LS scenario is demonstrable.

**Why this priority**: Requires a new generator topology branch for `l2spine`/`l3spine` and underlay `none`; larger than the P1 stories, distinct from the existing L2-access tier.

**Independent Test**: Load an L2LS design (2 spines, 4 leaves, MLAG on both tiers), generate, and confirm pure-L2 EOS renders with VLAN tag filtering and no EVPN/underlay routing; switch spines to the L3 variant and confirm SVI routing renders.

**Acceptance Scenarios**:

1. **Given** an L2LS design with `l2spine`/`l2leaf` roles and underlay `none`, **When** generation runs, **Then** devices render Layer-2 config with MLAG and VLAN tag filtering and no EVPN/underlay routing.
2. **Given** the design switched to `l3spine`, **When** generation runs, **Then** spines render SVI L3 routing with virtual-router MAC.
3. **Given** existing L3LS designs, **When** generation runs, **Then** their output is unchanged.
4. **Given** re-run with no changes, **Then** no artifact diffs (idempotent).

---

### User Story 5 - Campus fabric renders (Priority: P2)

As a campus network designer, I want a three-tier campus seed design with OSPF to the WAN edge, a hierarchical IDF, and access features (dot1x/PoE/port-profiles/in-band management), so the campus scenario is demonstrable.

**Why this priority**: Combines a reusable topology branch (campus roles, hierarchical IDF, OSPF underlay) with escape-hatch access features.

**Independent Test**: Load a campus design (core spines + IDF access leaves incl. an aggregation/edge tier), generate, and confirm OSPF underlay, spine SVI routing, and campus access features render.

**Acceptance Scenarios**:

1. **Given** a campus design with `l3spine` core and IDF access leaves, **When** generation runs, **Then** OSPF underlay and spine SVI L3 routing (Data/Voice/Guest VLANs, virtual-router MAC) render.
2. **Given** access ports configured for dot1x/PoE via escape-hatch payloads, **When** generation runs, **Then** the corresponding config renders.
3. **Given** a hierarchical IDF (aggregation feeding edge leaves), **When** generation runs, **Then** the aggregation-to-edge tier renders.
4. **Given** re-run with no changes, **Then** no artifact diffs (idempotent).

---

### User Story 6 - ISIS-LDP IPVPN WAN renders (Priority: P3)

As a WAN engineer, I want an MPLS core seed design with ISIS-LDP underlay and BGP VPN-IPv4 overlay, so the ISIS-LDP IPVPN scenario is demonstrable.

**Why this priority**: An entirely new routing domain delivered primarily via directly-seeded devices and the escape hatch; highest effort.

**Independent Test**: Load an ISIS-LDP IPVPN seed design (P/PE/RR devices), generate, and confirm ISIS-LDP underlay, MPLS L3VPN with VPN-IPv4 overlay, per-customer VRFs, and PE-CE routing render.

**Acceptance Scenarios**:

1. **Given** a seed design with `p`/`pe`/`rr` devices and `underlay_routing_protocol: isis-ldp`, **When** generation runs, **Then** ISIS-LDP underlay and LDP MPLS render.
2. **Given** per-customer VRFs on PEs via escape-hatch payloads, **When** generation runs, **Then** BGP VPN-IPv4 overlay with RR peering and PE-CE routing render.
3. **Given** re-run with no changes, **Then** no artifact diffs (idempotent).

---

### User Story 7 - CV-Pathfinder SD-WAN renders (Priority: P3)

As a WAN engineer, I want a CV-Pathfinder SD-WAN seed design with path groups, DPS, and application-aware virtual topologies, so the CV-Pathfinder scenario is demonstrable.

**Why this priority**: An entirely new SD-WAN domain delivered via directly-seeded devices and the escape hatch; highest effort and most external-dependency-bound.

**Independent Test**: Load a CV-Pathfinder seed design (pathfinders + edge/transit routers), generate, and confirm WAN roles, path groups (MPLS/INTERNET), DPS, and application-aware policies render offline.

**Acceptance Scenarios**:

1. **Given** a seed design with `wan_router`/`wan_rr` devices, **When** generation runs, **Then** CV-Pathfinder roles, path groups, and DPS render.
2. **Given** application-aware virtual topologies (VOICE/VIDEO/DATA) via escape-hatch payloads, **When** generation runs, **Then** the policies and their constraints render.
3. **Given** no live CloudVision/CVaaS is available, **When** generation runs, **Then** device configuration still renders offline.
4. **Given** re-run with no changes, **Then** no artifact diffs (idempotent).

### Edge Cases

- A seed design references a role that has no `ROLE_TO_AVD_TYPE` mapping — generation must fail loudly for that device, not silently skip it.
- A fabric selects underlay `none` but the generator still tries to allocate underlay pools or emit BGP underlay — must be suppressed cleanly.
- A device's `type` is not present in `node_type_keys` (custom or default), so PyAVD rejects it — every role must map to a valid node-type key (guarded since `005`).
- Escape-hatch payloads collide with generator-produced keys — deep-merge precedence (generated wins) must hold.
- Re-running any scenario's generator chain produces artifact churn (idempotence break).
- A campus hierarchical IDF has an aggregation leaf with no edge children, or an edge leaf with no aggregation parent.
- Seed object files load out of dependency order (e.g. devices before device types), causing unresolved references.
- Two scenarios reuse the same object names/human_friendly_ids, causing load collisions across designs.
- A WAN/provider device is added to the `fabrics`/`racks` groups by mistake and the leaf-spine generators try to process it.
- Loading all seven designs into one instance exhausts an addressing pool or collides on ASN allocation.

## Requirements *(mandatory)*

### Functional Requirements

**Generator behavior**

- **FR-001**: Generators MUST inherit from `infrahub_sdk.generator.InfrahubGenerator` and keep the existing `generate()` structure of the fabric/pod/rack/hostvar generators.
- **FR-002**: The fabric/pod/rack generators MUST create devices, interfaces, and cabling for the new topology types (standalone L2LS, campus hierarchical IDF) driven by the new roles and underlay modes, without changing behavior for existing L3LS designs.
- **FR-003**: The hostvar generator MUST rely on each device's PyAVD `type` plus the built-in `node_type_keys` defaults for base per-role behavior (pyAVD 6.3 has no `design.type`), and MUST supply the scenario-appropriate inputs (underlay/overlay protocol, EVPN, WAN/MPLS settings) natively or via the escape hatch. Every device's `type` MUST be a valid `node_type_keys` entry.
- **FR-004**: The hostvar generator MUST consume `NetworkFabric.evpn_vlan_aware_bundles` and render tenant L2 services as vlan-aware bundles when enabled.
- **FR-005**: The hostvar generator MUST render super-spine devices with an EVPN route-server role (derived from `role == super_spine`).
- **FR-006**: The hostvar generator MUST render `DcimDevice.evpn_gateway` devices with EVPN DC Gateway (next-hop-self) behavior.
- **FR-007**: When `underlay_routing_protocol` is `none`, the generator MUST render no underlay/EVPN routing and MUST NOT require underlay-only pools.
- **FR-008**: When `underlay_routing_protocol` is `isis-ldp`, the generator MUST render ISIS-LDP underlay (with escape-hatch supplying MPLS/VPN specifics).
- **FR-009**: All generator `save()` calls MUST use `allow_upsert=True`; generation MUST be idempotent and use deterministic ordering (checksum-based skipping preserved).
- **FR-010**: Generators MUST fail loudly (not silently skip) when a device role has no AVD node-type mapping or when required scenario data is missing.
- **FR-011**: `avd_custom_hostvars` deep-merge precedence (generator-produced values win) MUST be preserved for all escape-hatch payloads.

**Seed designs (objects)**

- **FR-020**: Each of the seven scenarios MUST have a loadable seed design under `objects/`, using numeric filename prefixes so dependency load order is deterministic (Fabric-C style: manufacturer, device types, pools, management, templates, fabric, racks, services per design).
- **FR-021**: Seed object files MUST use `apiVersion: infrahub.app/v1`, `kind: Object`, reference relationships by `human_friendly_id`, and use Dropdown choice `name` values (not labels).
- **FR-022**: Seed designs MUST NOT collide on object names/human_friendly_ids across scenarios, and MUST NOT exhaust or collide on shared addressing/ASN pools when loaded together.
- **FR-023**: WAN/provider scenarios (ISIS-LDP IPVPN, CV-Pathfinder) MUST seed their devices directly (not via the leaf-spine topology generators) and MUST NOT be added to the `fabrics`/`racks` topology groups in a way that triggers leaf-spine generation.
- **FR-024**: Escape-hatch capabilities (campus dot1x/PoE/port-profiles/in-band management; MPLS/VPN-IPv4; CV-Pathfinder SD-WAN surface) MUST be captured as `avd_custom_hostvars` payloads within the seed data, and every key MUST be accepted by the pinned pyAVD version.
- **FR-025**: Each seed design MUST place its devices in the `avd_devices` group so the hostvar and structured-config generators and artifact definitions run against them.

**Registration & regeneration**

- **FR-030**: Any new generator or query MUST be registered in `.infrahub.yml` (`generator_definitions`, `queries`) with correct `targets`, `class_name`, and `parameters`; any changed GraphQL query MUST have its typed return model regenerated (not hand-edited).
- **FR-031**: Protocol classes and GraphQL return types MUST be regenerated after any schema/query change; generated files MUST NOT be hand-edited.

**Documentation**

- **FR-040**: Each seed design MUST be documented (how to load and generate it, its native-vs-escape-hatch classification) and `docs/docs/supported-capabilities.md` MUST be updated to mark each scenario supported once it renders.

### Key Entities

- **NetworkFabric / NetworkPod / LocationRack**: the existing design hierarchy that drives topology generation, now honoring new roles, underlay modes, and EVPN inputs.
- **DcimDevice**: devices created by generators (fabric-model scenarios) or seeded directly (WAN scenarios), each with a role that maps to an AVD node type; may carry `evpn_gateway` and `avd_custom_hostvars`.
- **NetworkLink (role `dci`)**: inter-DC links for the dual-DC design (existing behavior).
- **AvdHostvarFile / AvdStructuredConfigFile**: per-device generated PyAVD inputs and structured config that render into EOS artifacts.
- **Seed design (per scenario)**: the numbered `objects/` file set (plus escape-hatch payloads) that makes one scenario reproducible from a clean load.

### Key Files

| File | Purpose |
|------|---------|
| `generators/generate_fabric.py`, `generate_pod.py`, `generate_rack.py` | Topology generation, extended for L2LS/campus branches |
| `generators/generate_avd_device_hostvar.py` | Render new inputs: design type, vlan-aware bundles, route-server, gateway, underlay modes |
| `generators/*_query.py`, `*.gql` | Queries and regenerated typed models for any new fields |
| `objects/NN*_<scenario>_*.yml` | Per-scenario seed designs (Fabric-C style) |
| `.infrahub.yml` | Registration of any new generator/query definitions |
| `docs/docs/supported-capabilities.md`, `docs/docs/developer-guide/avd/*` | Status and how-to per scenario |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All seed object files load without errors on a clean branch (no missing references, no schema validation failures).
- **SC-002**: For each of the seven scenarios, running the generator chain produces valid PyAVD EOS configuration for every device with zero render errors.
- **SC-003**: Each scenario's rendered output demonstrates that scenario's defining capabilities (per its acceptance scenarios).
- **SC-004**: Re-running the generator chain against unchanged seed data produces no artifact diffs for all seven designs (idempotence).
- **SC-005**: Existing designs (Fabric-A/B/C and Single-DC L3LS) render identically after this feature — no regression.
- **SC-006**: Every device across all designs resolves to a valid AVD node type; no device is silently skipped.
- **SC-007**: 100% of `avd_custom_hostvars` keys used by any seed design are accepted by the pinned pyAVD version.
- **SC-008**: Each scenario can be validated locally with `infrahubctl generator <name> --target <fabric-or-device>` and the artifact endpoints, and the steps are documented.
- **SC-009**: `docs/docs/supported-capabilities.md` marks all seven scenarios supported.

## Assumptions

- The seven scenarios and their native-vs-escape-hatch classification are inherited from `005-avd-example-fabrics` (research decisions R1–R9).
- Fabric-model scenarios (Single-DC L3LS, 5-stage Clos, Dual-DC, L2LS, Campus) build their topology through the existing `generate-fabric → generate-pod → generate-rack` chain, extended with role/underlay-aware branches. WAN/provider scenarios (ISIS-LDP IPVPN, CV-Pathfinder) seed devices directly and rely only on the hostvar and structured-config generators plus escape-hatch payloads.
- pyAVD 6.3 has no global `design.type`; per-role behavior comes from each node's `type` and the built-in `node_type_keys` defaults, so the generator sets `type` and supplies scenario inputs rather than switching a design type.
- "Renders" means valid EOS config offline; live deployment to hardware or CloudVision/CVaaS is not required, including for the WAN/SD-WAN scenarios.
- Seed designs follow the Fabric-C convention (own suffixed numbered files) and are additive to the existing Fabric-A/B/C seed data.
- The project targets pyAVD 6.3.x; all rendered intent and escape-hatch keys are confirmed against that pinned version.
- Priorities (P1 = scenarios 1–3, P2 = 4–5, P3 = 6–7) reflect effort and dependency, not desirability; scenarios 6–7 may still be split into a dedicated follow-on feature if their depth warrants it (per `005` R8).
- This feature depends on the `005` schema cycle being present (roles, inputs, underlay modes); it does not re-add schema.
