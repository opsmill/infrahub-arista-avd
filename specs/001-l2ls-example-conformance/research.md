# Phase 0 Research: L2LS Fabric Example Conformance (Schema cycle)

This document resolves the schema-design decisions needed to represent the AVD
`l2ls-fabric` example faithfully. Each decision records what was chosen, why, and
the alternatives considered. All findings are grounded in the current schema and
generator code and in the AVD example inputs/golden configs.

## Context recap

The AVD `l2ls-fabric` example is a **pure Layer-2** fabric: 2× `l2spine` (MLAG,
MSTP priority 4096), 4× `l2leaf` (MSTP priority 16384) in 2 MLAG racks, tenant
`MY_FABRIC` with l2vlans BLUE-NET(10)/GREEN-NET(20)/ORANGE-NET(30) scoped by tags,
server hosts on access ports, and a dual-homed FIREWALL trunk port-channel to both
spines. The golden `intended/configs/LEAF1.cfg` confirms **no** `interface Vxlan`,
`router bgp`, or EVPN address-family anywhere.

The repo already has: roles `l2spine`/`l2leaf`/`l3spine` (`dcim_extensions.yml`),
`underlay_routing_protocol: none` gating (`avd.py`), MLAG rendering for main-tier
roles, `NetworkSpanningTreePriority`, an AVD tag model (`Avd.Tag` → racks), a
connected-endpoint/adapter/LAG hostvar builder, and `scripts/compare_avd_examples.py`.

---

## Decision 1 — Spanning-tree priority roles for the L2LS tiers

**Decision**: Add `l2spine` (and `l3spine`, for campus symmetry) to the
`NetworkSpanningTreePriority.role` dropdown in `schemas/l3ls_extensions.yml`.

**Rationale**: The example sets spine MSTP priority 4096 and leaf 16384. The role
dropdown currently lists `super_spine`/`spine`/`leaf`/`l2leaf` only — there is no
role value to attach the spine-tier priority to for an `l2spine`. Without it, the
4096 spine priority cannot be modeled as a first-class object. `l3spine` is added
in the same change because the campus design (`Fabric-Campus`) has the same gap and
the enum edit is trivial and additive.

**Alternatives considered**:
- *Reuse `spine`*: rejected — the L2LS spine renders as node type `l2spine`; using
  the `spine` role couples STP priority to a different node-type key and is
  confusing/inaccurate.
- *Keep the deprecated fabric-level `spanning_tree_priority` scalar*: rejected —
  it is a single value and cannot express per-tier priorities (4096 vs 16384).

## Decision 2 — Overlay-free L2 services (no VNI / VXLAN / EVPN)

**Decision**: Make `EvpnTenant.mac_vrf_vni_base` **optional** and represent the
L2LS services as an overlay-free tenant with plain `EvpnL2Vlan` entries (no
`vni_override`). The generator (next cycle) omits `mac_vrf_vni_base` from AVD
hostvars when it is unset. Keep using the existing `EvpnTenant`/`EvpnL2Vlan`/
`IpamVLAN` model rather than inventing a new node.

**Rationale**: The AVD example models services as `tenants → l2vlans`, which maps
directly onto `EvpnTenant.l2vlans`. For pure-L2 nodes (`l2spine`/`l2leaf` are not
VTEPs and EVPN/BGP is already skipped for them), AVD renders only VLAN definitions
and no VXLAN — so the *structure* matches. The one real defect is that the schema
currently pushes a `mac_vrf_vni_base` (seed uses 20000) into the hostvars
(`generate_avd_device_hostvar.py:1265` emits it unconditionally); an overlay-free
tenant should carry no VNI base. Making the attribute optional is minimal,
additive, and lets both overlay (Fabric-A/B/C) and overlay-free (L2LS) tenants
coexist. This follows the schema skill's "design for the cheaper layer" —
reuse the existing generic instead of a bespoke L2-only node.

**Alternatives considered**:
- *New `Network.L2Service`/`Network.L2Vlan` node for L2LS only*: rejected — a new
  parallel VLAN model duplicates `EvpnL2Vlan`/`IpamVLAN` shape and forces the
  generator to branch on two service models; the schema skill's YAGNI guidance
  favors extending the existing generic.
- *Leave `mac_vrf_vni_base` required and rely on VTEP-gating alone*: rejected —
  the VNI base still flows into hostvars and misrepresents a pure-L2 design; the
  user explicitly flagged the EVPN/VNI modeling as a correctness gap.

**Verification note for the next cycle**: confirm rendered L2LS configs contain no
`interface Vxlan`, `router bgp`, or `vlan <id> ... vni` lines (SC-002).

## Decision 3 — Tag-based VLAN scoping to leaf pairs

**Decision**: Add `rack_tags` (peer `LocationRack`) and `avd_tags` (peer
`Avd.Tag`) relationships to `EvpnL2Vlan`, mirroring the pattern already on
`EvpnSvi`. The generator (next cycle) emits these as AVD `tenants[].l2vlans[].tags`
and emits matching `node.filter.tags` on each leaf so AVD scopes each VLAN to the
correct rack pair.

**Rationale**: The example scopes VLANs to leaves with tags (RACK1 = blue+green,
RACK2 = blue+orange). `EvpnSvi` already models exactly this dual mechanism
(`rack_tags` + `avd_tags`, `evpn_services.yml:120-135`) and the generator already
has `_build_svi_tags`/`_fetch_rack_avd_tags` helpers. Reusing the same relationship
shape on `EvpnL2Vlan` keeps the model and generator consistent and requires no new
tag concept — `Avd.Tag` already relates to racks.

**Alternatives considered**:
- *Tags on the underlying `IpamVLAN`*: rejected — service scoping is a
  service-model concern; `EvpnL2Vlan` is the tenant-scoped service object and is
  where `EvpnSvi` already carries tags, so parity lives there.
- *Per-rack VLAN membership via explicit rack↔vlan relationship*: rejected — AVD's
  native mechanism is tag filtering; modeling it any other way would force the
  transform to reconstruct AVD tags anyway.

## Decision 4 — Connected endpoints & the dual-homed firewall

**Decision**: Two-part, staged within the endpoint model:
1. **Hosts (access)**: reuse the existing connected-endpoint / adapter / LAG model.
   Add the switchport intent needed for access ports — per-adapter **mode**
   (access/trunk), **access VLAN** / **trunk VLANs**, and **edge portfast** — as
   native attributes on the endpoint/adapter schema if not already expressible.
2. **Firewall (trunk to spines)**: allow a connected endpoint to attach to
   **spine** devices (today server cabling targets rack leaves only) and render as
   a trunk Port-Channel allowing VLANs 10/20/30. Model natively where the adapter
   schema already supports port-channels; if native spine-attached-endpoint
   modeling proves disproportionate for this single scenario, fall back to the
   documented `avd_custom_hostvars` escape hatch on the two spines for the firewall
   `connected_endpoints`/`port_profiles` block.

**Rationale**: The generator already builds `servers` with `adapters`,
`switch_ports`, and `port_channel` (LACP) data, so hosts and port-channels are
largely covered; the missing piece is explicit switchport mode/VLAN/portfast
intent to match the example's PP-BLUE/GREEN/ORANGE (access) and PP-FIREWALL
(trunk) profiles. The firewall is the one structurally new pattern (endpoint on
the spine tier). The repo's documented native-vs-escape-hatch guidance
(`supported-capabilities.md`, `developer-guide/avd/extending.md`) explicitly
reserves `avd_custom_hostvars` for niche, single-scenario pass-through — the
firewall trunk-to-spine qualifies as a candidate if native modeling is heavy.
This keeps the P3 endpoint scope from blocking the P1/P2 topology and services.

**Alternatives considered**:
- *Model everything via escape hatch*: rejected for the hosts — access
  port-profiles are reusable and first-class (the schema-first principle), so hosts
  should be native; only the firewall-to-spine edge is a defensible escape-hatch
  candidate.
- *Model everything natively now*: acceptable but risks over-building a full
  port-profile object model in the schema cycle; the decision defers the exact
  native depth to the endpoint/generator cycle while fixing the schema seams here.

**Open item carried to the next cycle**: choose native vs. escape hatch for the
firewall after prototyping the spine-attached-endpoint generator path; record the
choice in `supported-capabilities.md` (FR-019).

## Decision 5 — Seed-data shape (mirror the example) vs. keep current

**Decision**: Reshape the existing `Fabric-L2LS` seed (`objects/13a`, `13e`,
`13h`) in place to mirror the example: 2 MLAG spines, 2 MLAG racks (LEAF1/2,
LEAF3/4), STP priority objects (spine 4096 / leaf 16384), overlay-free tenant
`MY_FABRIC` with BLUE/GREEN/ORANGE VLANs and tag scoping, host endpoints, and the
firewall. Do not add a second parallel fabric.

**Rationale**: The requester chose *golden-config parity* (not "both golden +
variant"), so the single `Fabric-L2LS` should represent the example. Device
hostnames (`SPINE1`/`LEAF1`…) are produced by the generator naming cycle; the seed
sets the fabric/pod/rack/service/endpoint intent. Management/underlay addressing
that is environment-specific is mapped onto the fabric's existing pools; the
comparison harness normalizes values that cannot be reproduced (documented).

**Alternatives considered**:
- *Add a new golden fabric alongside Fabric-L2LS*: rejected per the confirmed
  scope answer (would be the "Both" option, which was not selected).

## Decision 6 — Backward compatibility & rollout

**Decision**: All schema edits are additive (new enum values; an attribute made
optional; new optional relationships). Roll out on a branch:
`schema check` → `schema load --branch` → regenerate `protocols.py` →
`object load` → verify no regression on existing fabrics → merge via proposed
change. Making `mac_vrf_vni_base` optional does not affect existing tenants that
set it.

**Rationale**: Constitution I/III require branch-first schema changes and protocol
regeneration; the existing EVPN/L3LS fabrics must not regress (Technical Context
constraint). Additive-only changes avoid data migrations on loaded overlay
tenants.

**Alternatives considered**:
- *Edit on the default branch*: rejected — schema load runs migrations
  immediately with no preview/undo (schema skill `workflow-branch-first`).

---

## Resolved unknowns

- No `[NEEDS CLARIFICATION]` remain. The two scope decisions (golden parity; full
  topology) were resolved with the requester during `/speckit-specify`; the
  integration-test selectability requirement was added mid-cycle (FR-020–024).
- Whether AVD accepts overlay-free tenants for L2LS: confirmed by the golden
  `LEAF1.cfg` (VLANs present, no VXLAN/BGP), so the structure is valid input.
- Node-type keys: PyAVD's built-in `node_type_keys` cover `l2spine`/`l2leaf`; no
  custom `node_type_keys` needed (verified in `avd.py` and the hostvar generator).
  Whether an explicit `design.type: l2ls` must also be emitted is a generator/
  transform-cycle verification item (FR-013), not a schema change.
