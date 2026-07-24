# Phase 0 Research: AVD Example Designs (Generator + Objects)

Decisions that resolve how the seven scenarios are built and rendered. All are
grounded in the current generators and the pinned pyAVD (`>=6.3.0,<6.4.0`).

## Decision R1 — No `design.type`; behavior is `type` + `node_type_keys`

**Decision**: Do **not** introduce or set an AVD `design.type`. Rely on each
device's PyAVD `type` (already mapped from the Infrahub role in `005`) plus the
built-in `node_type_keys` defaults, and supply scenario-specific inputs (underlay/
overlay protocol, EVPN, WAN/MPLS) natively or via the escape hatch.

**Rationale**: Verified against the pinned pyAVD — `EosDesigns` has **no**
top-level `design` field; a `design.type` input raises `KeyError`. The default
`node_type_keys` already includes every type this feature uses and encodes the
per-role behavior:

| type | underlay_router | default underlay | default overlay | evpn_role | mpls_overlay_role | vtep | mlag |
|------|:---:|---|---|---|---|:---:|:---:|
| `l3leaf` | yes | ebgp | ebgp | client | – | yes | yes |
| `l2spine` | no | ebgp | ebgp | none | – | no | yes |
| `l3spine` | yes | none | none | none | – | no | yes |
| `p` | yes | isis-sr | ibgp | none | none | no | no |
| `pe` | yes | isis-sr | ibgp | client | client | no | no |
| `rr` | yes | isis-sr | ibgp | server | server | no | no |
| `wan_router` | yes | none | none | none | – | yes | no |
| `wan_rr` | yes | none | none | none | – | yes | no |

So node-type validation and base behavior come for free from `type`; the work is
supplying the right *inputs* per scenario, not switching a design.

**Alternatives considered**: Setting `design.type` (as in older AVD/Ansible
examples) — rejected: it does not exist in pyAVD 6.3 and would raise a validation
error.

## Decision R2 — Delivery model per scenario

**Decision**:
- **Fabric-model** (Single-DC L3LS, 5-stage Clos, Dual-DC, L2LS, Campus): build
  topology via the existing `generate-fabric → generate-pod → generate-rack`
  chain, extended with role/underlay-aware branches; render via
  `generate-avd-device-hostvar`.
- **WAN/provider** (ISIS-LDP IPVPN, CV-Pathfinder): seed devices, interfaces, and
  links directly in `objects/`; render via the hostvar + structured-config
  generators plus escape-hatch payloads. Do not add WAN topology generators.

**Rationale**: L2LS and campus are leaf-spine variations that fit the existing
generator chain. WAN/provider topologies are not leaf-spine; a bespoke generator
would be speculative and low-reuse. Directly-seeded devices + escape hatch render
them today without new generator surface.

**Alternatives considered**: Dedicated WAN/campus generators now — rejected as
premature; revisit if these become core offerings.

## Decision R3 — L2LS underlay handling (`none`)

**Decision**: For a fabric with `underlay_routing_protocol: none`, the hostvar
generator MUST NOT emit `underlay_routing_protocol` and MUST NOT require underlay
pools; rely on the `l2spine`/`l2leaf` node behavior (`l2spine` is non-routing,
port-channel uplinks). The L3-on-spine variant uses `l3spine` (SVI routing).

**Rationale**: `none` is an Infrahub-side sentinel meaning "no fabric underlay
routing," not a PyAVD underlay value. Emitting it would fail validation. The node
types already encode the L2/L3 behavior.

**Alternatives considered**: Passing `none` through to PyAVD — rejected (invalid
value). Adding a separate design-mode field — unnecessary given node-type behavior.

## Decision R4 — ISIS-LDP underlay (`isis-ldp`)

**Decision**: For `underlay_routing_protocol: isis-ldp`, emit the PyAVD underlay
value for ISIS-LDP and let escape-hatch payloads supply MPLS/LDP and VPN-IPv4
specifics. `p`/`pe`/`rr` already default to isis-sr/ibgp/MPLS roles, so the
escape hatch overrides only what differs.

**Rationale**: The provider node types carry most MPLS behavior; the fabric
underlay input plus targeted escape-hatch keys complete it. Confirm the exact
PyAVD underlay string for ISIS-LDP against the pinned version during
implementation.

**Alternatives considered**: Full native MPLS/VPN model — rejected (large,
low-reuse; deferred per `005` R6).

## Decision R5 — Super-spine EVPN route-server derivation

**Decision**: In the hostvar generator, when `role == super_spine`, render the
device with `evpn_role: server` (route server) for the 5-stage Clos design.

**Rationale**: The 5-stage Clos example makes super-spines EVPN route servers;
this is fully determined by the role, so derive it rather than add schema.

**Alternatives considered**: A schema override attribute — deferred (YAGNI) per
`005` R2.

## Decision R6 — `evpn_vlan_aware_bundles` rendering

**Decision**: When `NetworkFabric.evpn_vlan_aware_bundles` is true, render tenant
L2 services as vlan-aware bundles (the PyAVD tenant/vrf setting), preserving
current behavior when false/unset.

**Rationale**: First-class reusable EVPN input added in `005`; the generator
consumes it in the tenant-rendering path.

## Decision R7 — `evpn_gateway` rendering

**Decision**: When `DcimDevice.evpn_gateway` is true, render EVPN DC Gateway
(next-hop-self at the gateway) for that device in the overlay, for the dual-DC
design. If per-device PyAVD gateway keys need more than a flag, supplement via
escape hatch (fallback recorded in `005` R3).

## Decision R8 — Campus hierarchical IDF

**Decision**: Model the campus hierarchical IDF (aggregation leaves feeding edge
leaves) using the existing rack/device parent relationships and uplink cabling,
with `l3spine` core and `l2leaf` access; deliver dot1x/PoE/port-profiles/in-band
management via escape-hatch payloads.

**Rationale**: OSPF underlay is already native; the topology reuses existing
relationships; access features are niche pass-through (per `005` R5).

## Decision R9 — Seed-design isolation

**Decision**: Each seed design gets its own numbered `objects/` file set
(Fabric-C convention) with its own pools, ASNs, and unique object names/
human_friendly_ids, so all seven designs can coexist in one instance without
collisions.

**Rationale**: Demonstrability requires loading designs together without pool
exhaustion or name clashes (spec SC-001/FR-022).

## Decision R10 — Idempotence for new objects and escape-hatch payloads

**Decision**: All generator writes use `allow_upsert=True` with stable natural
keys; escape-hatch payloads are static seed data; the existing checksum-based
change detection guards re-runs. Validate with
`$infrahub-test-generator-idempotence` for every design.

**Rationale**: The highest-risk area (Constitution II) — many new objects across
seven designs. Repeated-run validation is mandatory before merge.

## Cross-cutting

- **Backward compatibility**: existing L3LS/Fabric-A/B/C output must not change;
  new branches are gated on the new roles/underlay values.
- **Fail loud**: a device whose role has no node-type mapping must abort its
  generation with an actionable error, not be skipped (spec FR-010).
- **Regeneration**: any changed GraphQL query has its typed model regenerated;
  generated files are never hand-edited.
- **pyAVD confirmation**: every native input value and escape-hatch key is
  validated against the pinned pyAVD before a design is considered done.
