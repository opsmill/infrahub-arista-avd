# Phase 1 Data Model: AVD Example Fabric Designs

This feature adds the minimal schema surface the seven AVD example scenarios
need. Additions are additive and optional/defaulted so existing L3LS data stays
valid. Scenario-specific, pass-through behavior is delivered through the existing
`avd_custom_hostvars` escape hatch and is described in
[contracts/escape-hatch.md](./contracts/escape-hatch.md).

## Entity: Device Roles (new choices)

**Kind**: existing `DcimDevice.role` dropdown choices
**File**: `schemas/dcim_extensions.yml`
**Mapping source of truth**: `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`

| Machine name | Label | AVD `node_type` | Scenario(s) |
|--------------|-------|-----------------|-------------|
| `l2spine` | L2 Spine | `l2spine` | L2LS (4) |
| `l3spine` | L3 Spine | `l3spine` | L2LS L3 variant (4), Campus core (5) |
| `p` | Provider (P) | `p` | ISIS-LDP IPVPN (6) |
| `pe` | Provider Edge (PE) | `pe` | ISIS-LDP IPVPN (6) |
| `rr` | Route Reflector (RR) | `rr` | ISIS-LDP IPVPN (6) |
| `wan_router` | WAN Router | `wan_router` | CV-Pathfinder (7) |
| `wan_rr` | WAN Route Reflector (Pathfinder) | `wan_rr` | CV-Pathfinder (7) |

> AVD `node_type` values above are the intended targets; each MUST be confirmed
> against the pinned pyAVD `node_type_keys` before the mapping is finalized. Where
> pyAVD names differ, the mapping value changes but the Infrahub machine name and
> label stay as listed.

### Validation Rules

- Existing role choices remain available and unchanged:
  `super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`.
- Every new role MUST have a `ROLE_TO_AVD_TYPE` entry; unmapped roles MUST raise
  `ValueError` (no silent default).
- A unit test MUST assert every schema role choice resolves to a non-empty AVD
  node type.
- Adding roles MUST NOT change the AVD type or behavior of existing roles.

## Entity: EVPN vlan-aware-bundles input

**Kind**: new attribute on `NetworkFabric` (or `Avd.Evpn` settings)
**File**: `schemas/l3ls_extensions.yml` or `schemas/avd/avd.yml`

| Field | Value |
|-------|-------|
| Name | `evpn_vlan_aware_bundles` |
| Kind | `Boolean` |
| Optional/default | Optional; default preserves current rendering behavior |
| Scenario | 5-stage Clos (2) |

### Validation Rules

- Default MUST NOT change existing fabrics' rendered output.
- When `true`, tenants render as vlan-aware-bundles with route targets.

## Entity: Super-spine EVPN route-server behavior (derived)

**Kind**: generator-derived behavior, not a stored attribute (this cycle)
**Source**: `role == super_spine`

| Aspect | Value |
|--------|-------|
| Derivation | Super-spine devices render with an EVPN route-server role |
| Schema surface | None added this cycle (derivation only) |
| Optional override | Deferred (YAGNI) until a real override need appears |
| Scenario | 5-stage Clos (2) |

### Validation Rules

- Derivation MUST be handled in the hostvar generator (generator cycle), not
  silently defaulted by PyAVD.
- Non-super-spine devices MUST be unaffected.

## Entity: EVPN DC Gateway flag

**Kind**: new attribute on the gateway device (leaf/border-leaf) or a
fabric-level setting naming the gateway
**File**: `schemas/l3ls_extensions.yml`

| Field | Value |
|-------|-------|
| Name | `evpn_gateway` (device Boolean) — final placement chosen in the schema contract |
| Kind | `Boolean` (device) |
| Optional/default | Optional; default `false` |
| Scenario | Dual-DC (3) |

### Validation Rules

- Default `false` MUST preserve existing behavior.
- When enabled on a device, that device renders EVPN DC Gateway next-hop-self
  behavior in the overlay.
- Fallback: if per-device tuning beyond a flag is required by pyAVD, this
  capability moves to the escape hatch (recorded in research.md R3).

## Entity: Underlay mode / protocol (extended)

**Kind**: extended `underlay_routing_protocol` choices (and/or a fabric design
mode)
**File**: `schemas/l3ls_extensions.yml`

| Machine name | Label | Meaning | Scenario |
|--------------|-------|---------|----------|
| `ebgp` (existing) | eBGP | eBGP underlay | 1, 2, 3, 7(sites) |
| `ospf` (existing) | OSPF | OSPF underlay | 5 |
| `none` (new) | None (L2 only) | No underlay/EVPN routing | 4 |
| `isis-ldp` (new) | ISIS-LDP | ISIS IGP + LDP MPLS | 6 |

### Validation Rules

- New values MUST be handled explicitly in the hostvar generator; an unhandled
  value MUST NOT silently fall back to a default.
- Existing fabrics keep their current value; the default is unchanged.
- `none` MUST NOT require underlay-only pools/settings to be populated.

## Entity: Escape-Hatch Payload

**Kind**: existing `avd_custom_hostvars` (JSON) at fabric/pod/device scope
**File**: no schema change (already present)

| Aspect | Value |
|--------|-------|
| Merge behavior | Deep-merge with generated hostvars; generator-produced values win (unchanged) |
| Source | Committed seed objects only (never manual UI edits) |
| pyAVD | Every key MUST be accepted by `pyavd>=6.3.0,<6.4.0` |
| Scenarios | Campus access features (5), MPLS/VPN-IPv4 (6), CV-Pathfinder SD-WAN surface (7) |

### Validation Rules

- Escape-hatch keys MUST NOT rely on changing the deep-merge precedence.
- Escape-hatch content MUST be reproducible and idempotent across regeneration.

## State (per scenario design)

| State | Meaning | Transition |
|-------|---------|------------|
| Schema-ready | Roles/choices/flags this scenario needs exist and validate | Generator cycle can create devices/cabling |
| Modeled | Seed design (objects + escape hatch) loaded | Generator chain can run |
| Generated | Hostvars + structured config produced, PyAVD validation passes | Renders EOS config artifacts |
| Demonstrated | All devices render valid EOS config matching the example's intent | Scenario counted as supported |

## Backward-compatibility summary

- All new node attributes are optional or defaulted.
- All new role/underlay choices are additive; no existing machine value changes.
- Border Leaf continues to map to `l3leaf`.
- The Single-DC L3LS scenario's rendered output is unchanged (regression-tested).
