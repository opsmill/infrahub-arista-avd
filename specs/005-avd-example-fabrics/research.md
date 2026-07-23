# Phase 0 Research: AVD Example Fabric Designs

This research resolves the one open question that governs the whole feature: for
each capability a scenario needs, is the gap closed with a **native schema
change** or the **`avd_custom_hostvars` escape hatch**? Each decision below
applies the spec's Decision Principle: native for reusable, first-class,
UI-selected, allocated, validated, or deterministically-generated capabilities;
escape hatch for niche, single-scenario, pass-through PyAVD keys.

Baseline facts (from the prior gap analysis of the current repo):

- Supported today: eBGP/OSPF underlay, BGP/EVPN overlay, roles
  `super_spine`/`spine`/`leaf`/`border_leaf`/`l2leaf`, MLAG, VRFs, route targets,
  L2/L3 VLAN services, LAG, DCI `NetworkLink` (role `dci`) rendering
  `l3_edge.p2p_links`, and the `avd_custom_hostvars` deep-merge escape hatch at
  fabric/pod/device scope (generated values win).
- `underlay_routing_protocol` choices are `ebgp`, `ospf`; `overlay_routing_protocol`
  choices are `ebgp`, `ibgp`.
- `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py` is the single source of
  truth mapping Infrahub roles to PyAVD `node_type`.

---

## Decision R1 — Single-DC L3LS: no schema change

**Decision**: Deliver this scenario with a curated seed design only (objects
cycle). No schema change.

**Rationale**: The scenario is fully supported today. Its value here is a
documented, reproducible reference design and validation of the demonstrability
harness (load → generate → render) the other scenarios reuse.

**Alternatives considered**: Adding polish attributes — rejected as scope creep;
the baseline already renders the example's intent.

## Decision R2 — 5-stage Clos: native vlan-aware-bundles + route-server derivation

**Decision**:
- Add a **native** fabric-level (or `Avd.Evpn`) input `evpn_vlan_aware_bundles`
  (Boolean, default preserving current behavior) that controls vlan-aware-bundle
  rendering for tenants.
- Render super-spines with an **EVPN route-server role** by **deriving** it in
  the hostvar generator from `role == super_spine` (generator cycle), with an
  optional native override attribute only if a real need to override appears.

**Rationale**: Both are reusable EVPN concepts, not one-offs. `evpn_vlan_aware_bundles`
is a first-class overlay input operators select. Route-server behavior is fully
determined by the existing super-spine role, so derivation avoids adding schema
surface; an override would be speculative (YAGNI).

**Alternatives considered**: Escape hatch for both — rejected because they recur
in real EVPN designs and benefit from UI selection and validation. A mandatory
`evpn_role` attribute on every device — rejected as unnecessary; role already
implies it.

## Decision R3 — Dual-DC: native EVPN DC Gateway flag, seed-data composition

**Decision**:
- Add a **native** EVPN DC Gateway capability as a small flag applied to
  designated gateway devices (e.g. a Boolean on the leaf/border-leaf, or a
  fabric-level setting naming the gateway role) that makes those devices render
  gateway next-hop-self behavior.
- Compose the two DCs and their DCI links from **seed data** (objects cycle),
  reusing the existing `NetworkLink` role `dci` model that already renders
  `l3_edge.p2p_links`.

**Rationale**: EVPN DC Gateway is the defining, reusable feature of the dual-DC
example and warrants first-class, validated modeling. Multi-DC composition needs
no new node — two fabrics plus DCI links already exist; only the gateway behavior
is missing.

**Alternatives considered**: Escape hatch for the gateway flag — acceptable
fallback if the PyAVD gateway keys prove to need per-device tuning beyond a flag,
recorded as the secondary option. A dedicated multi-DC container node — rejected
as premature; seed data composes existing fabrics adequately for the example.

## Decision R4 — L2LS: native l2spine/l3spine roles + "underlay: none" mode

**Decision**:
- Add **native** device roles `l2spine` and `l3spine`, each mapped in
  `ROLE_TO_AVD_TYPE` to the corresponding PyAVD node type.
- Add a **native** "underlay: none" mode so an L2LS fabric renders no
  EVPN/underlay routing. Implement as either an added `underlay_routing_protocol`
  choice (`none`) or an explicit fabric design-type; the data-model contract
  selects the minimal option that keeps existing L3LS data valid.

**Rationale**: Standalone L2LS is a distinct, reusable fabric design (not the
existing L2-access tier under L3LS). New roles and an underlay-none mode are
first-class topology concepts that must be UI-selectable and drive generator
branches. The L3-on-spine variant is served by the `l3spine` role.

**Alternatives considered**: Reusing `l2leaf`/`spine` with escape-hatch node_type
overrides — rejected because L2LS is common enough to model natively and needs
deterministic topology generation, not a per-device pass-through.

## Decision R5 — Campus: reuse roles, native OSPF, escape-hatch access features

**Decision**:
- **Reuse** `l3spine` (core) and `l2leaf` (access) from R4; add a native campus
  role only if node-type mapping genuinely requires one (default: reuse).
- OSPF underlay is **already native** (`underlay_routing_protocol: ospf`).
- Deliver dot1x/NAC, PoE, port profiles, and in-band management via the
  **escape hatch** initially.
- Model the hierarchical IDF (aggregation feeding edge leaves) with the existing
  parent/child rack/device relationships (generator cycle).

**Rationale**: The campus topology maps onto existing/near-existing roles and the
already-supported OSPF underlay. The access features are numerous, campus-specific,
and pass-through PyAVD keys with no cross-device allocation — the textbook
escape-hatch case. Promoting the most-reused ones (e.g. port profiles, dot1x) to
native is a good later increment once demand is proven.

**Alternatives considered**: Native schema for dot1x/PoE/port-profiles now —
rejected as premature and disproportionate for a single scenario; would add large
schema surface before demand is established.

## Decision R6 — ISIS-LDP IPVPN: native isis-ldp underlay + minimal roles, escape-hatch MPLS/VPN

**Decision**:
- Add a **native** `isis-ldp` value to `underlay_routing_protocol`, handled
  explicitly by the hostvar generator (never silently defaulted).
- Add **minimal native** provider roles `p`, `pe`, `rr` mapped in
  `ROLE_TO_AVD_TYPE` to the appropriate PyAVD node types.
- Deliver MPLS/LDP, BGP VPN-IPv4 overlay, per-customer VRF-on-PE specifics,
  routed subinterfaces, and PE-CE OSPF via the **escape hatch**.

**Rationale**: The underlay selector and node roles are first-class anchors that
must be selectable and mapped. The MPLS/VPN-IPv4 machinery is an entire domain
unlikely to be reused by the DC scenarios; modeling it natively now is
disproportionate. The escape hatch renders the example while keeping the schema
lean.

**Alternatives considered**: Full native MPLS/VPN-IPv4 model — rejected for this
cycle as very large and low-reuse; revisit if IPVPN becomes a core offering.

## Decision R7 — CV-Pathfinder: native WAN roles, escape-hatch SD-WAN surface

**Decision**:
- Add **minimal native** roles `wan_router` and `wan_rr` mapped in
  `ROLE_TO_AVD_TYPE` to the PyAVD WAN node types.
- Deliver path groups (MPLS/INTERNET), DPS/flow-tracking, application-aware
  virtual topologies, WAN HA, STUN, and CVaaS integration via the **escape
  hatch**.

**Rationale**: The WAN roles are the only first-class anchors needed for topology
and node-type mapping. The rest is a large, external-dependency-bound SD-WAN
surface specific to this scenario — escape hatch renders it offline without
committing a big native model prematurely.

**Alternatives considered**: Native SD-WAN model — rejected as the largest,
most external-dependency-bound domain; not justified before demand.

## Decision R8 — Phasing recommendation for scenarios 6 and 7

**Decision**: Keep scenarios 6 and 7 **in scope** for this feature at the level
of their native anchors (roles + underlay choice) and an escape-hatch-rendered
seed design, but **recommend** their full generator/objects work be split into a
dedicated follow-on feature.

**Rationale**: They are whole new routing/WAN domains. Their minimal schema
anchors belong with the other role additions (one protocol regeneration), but
their generator and seed-design depth dwarfs the P1/P2 scenarios and would
unbalance this feature's later cycles.

**Alternatives considered**: Dropping 6–7 entirely — rejected; the user asked for
a design per scenario. Full native implementation now — rejected per R6/R7.

## Decision R9 — Escape-hatch content lives in seed data

**Decision**: All escape-hatch usage is captured as `avd_custom_hostvars` in
committed seed objects (fabric/pod/device scope), never as manual UI edits.

**Rationale**: Demonstrability and idempotence (SC-002, SC-006) require the
designs to be reproducible from a clean load. The existing deep-merge precedence
(generated values win) is preserved unchanged.

**Alternatives considered**: Documenting manual UI steps — rejected; not
reproducible and breaks idempotence guarantees.

## Cross-cutting decisions

- **Backward compatibility**: every new attribute on an existing node is optional
  or defaulted; new role/underlay choices are additive; existing role machine
  values are unchanged. This preserves the Single-DC L3LS scenario (SC-003).
- **Node-type mapping completeness**: every new role gets a `ROLE_TO_AVD_TYPE`
  entry in the same change; a unit test asserts no role resolves to a missing
  node type (SC-005).
- **pyAVD validation**: all new native inputs and every escape-hatch key are
  validated against `pyavd>=6.3.0,<6.4.0` before a design is considered done
  (SC-007).
- **Regeneration**: protocols and GraphQL return types are regenerated after
  schema/query changes; generated files are never hand-edited.

## Confirmed pyAVD node types (T006)

Verified against the pinned pyAVD via `EosDesigns._from_dict({}).node_type_keys`.
All seven target node types exist in the default `node_type_keys`, so every new
role maps to a valid AVD `type`:

| Role | AVD `type` | Confirmed |
|------|-----------|-----------|
| `l2spine` | `l2spine` | ✅ |
| `l3spine` | `l3spine` | ✅ |
| `p` | `p` | ✅ |
| `pe` | `pe` | ✅ |
| `rr` | `rr` | ✅ |
| `wan_router` | `wan_router` | ✅ |
| `wan_rr` | `wan_rr` | ✅ |

Note: several of these `type`s are only meaningful under specific AVD `design.type`
selections (e.g. `l2spine`/`l3spine` under `l2ls`, `p`/`pe`/`rr` under `mpls`,
`wan_*` under `cv-pathfinder`/`autovpn`). Selecting the correct design type per
scenario is generator/objects-cycle work; the roles and their type mappings are
valid schema anchors regardless.
