# Phase 1 Data Model: L2LS Generator Capabilities

This cycle changes **generator behavior**, not the schema (schema is feature 001).
The "data model" here is (a) the objects the generators create and (b) the AVD
hostvar shapes they emit. Legend: **[NEW]** added this cycle, **[MOD]** changed,
**[REUSE]** existing.

## A. Objects created/updated by generators

| Object | Generator | Change | Notes |
|--------|-----------|--------|-------|
| `Mlag.Domain` (spine pair) | `generate_pod.py` | **[NEW]** | l2spine MLAG pair when underlay `none`; domain id deterministic from pod/pair |
| `Dcim.Interface` role `mlag_peer` (spine) | `generate_pod.py` | **[NEW]** | Peer-link interfaces carved on the l2spine model (highest ports), idempotent |
| `Mlag.Domain` (leaf pair) | `generate_rack.py` | **[REUSE]** | Existing l2leaf MLAG pair + carving |
| `Interface.Lag` uplink port-channel | `generate_rack.py` | **[REUSE]** | Leaf uplinks aggregated to spines |
| Firewall endpoint cabling to spines | server-cabling path | **[NEW]** | Endpoint attached to both spines (trunk PC); or `avd_custom_hostvars` fallback |
| Host endpoint cabling to leaves | `generate_server_cabling.py` | **[REUSE]** | Access-port hosts |

## B. AVD hostvar shapes emitted (`generate_avd_device_hostvar.py`)

### B1. Tenant / l2vlans — **[MOD]** `_build_tenants_hostvars`

```jsonc
{
  "name": "MY_FABRIC",
  // mac_vrf_vni_base: OMITTED when the tenant has no base (overlay-free)   [MOD]
  "l2vlans": [
    { "id": 10, "name": "BLUE-NET",   "tags": ["bluezone"] },   // tags: NEW
    { "id": 20, "name": "GREEN-NET",  "tags": ["greenzone"] },
    { "id": 30, "name": "ORANGE-NET", "tags": ["orangezone"] }
  ]
}
```
- **Rule**: `mac_vrf_vni_base` present ⇔ tenant value not `None`.
- **Rule**: `l2vlans[].tags` = rack names (`rack_tags`) + AVD tag names (`avd_tags`).

### B2. Node config — **[MOD]** node-config builder

```jsonc
{
  "name": "<generated hostname>",   // convention name; parity is feature-level
  "id": <node_id>,
  "filter": { "tags": ["bluezone", "greenzone"] }   // NEW: leaf's rack avd_tags (+rack name)
  // ...existing loopback/mgmt/uplink keys unchanged
}
```
- **Rule**: `filter.tags` emitted for leaf nodes from their rack's `avd_tags`
  (and rack name), so AVD scopes VLANs whose tags intersect.

### B3. MLAG (both tiers) — **[MOD]/[REUSE]**

- l2spine and l2leaf main-tier devices render node-group / `mlag_domain_id` /
  peer-link (existing `renders_mlag` path), now backed by the spine MLAG domain
  created in `generate_pod.py`.

### B4. Connected endpoints — **[MOD]**

- Host adapters carry `mode: access`, the access VLAN, and
  `spanning_tree_portfast: edge` (new schema attr).
- Firewall adapter: `mode: trunk`, allowed VLANs 10/20/30, `port_channel` (LACP),
  attached to both spines.

## C. Pure-Layer-2 invariant

- No `mac_vrf_vni_base`, no `vni_override`, non-VTEP roles ⇒ PyAVD emits **no**
  `interface Vxlan`, `router bgp`, or EVPN address-family for L2LS devices.

## D. Reused, unchanged

- `src/solution_arista_avd/avd.py` role/underlay constants (`SPINE_ROLE_BY_UNDERLAY`
  `none→l2spine`, `LEAF_ROLE_BY_UNDERLAY` `none→l2leaf`, `MLAG_MAIN_TIER_ROLES`,
  `NON_EMITTED_UNDERLAYS`).
- Feature-001 schema (STP roles, optional VNI base, L2-VLAN tags, PortFast).

## Traceability (spec FR → generator change)

| FR | Change |
|----|--------|
| FR-001 | §D role mapping (reuse) |
| FR-002/FR-003 | §A spine MLAG domain + carved peer interfaces (both tiers) |
| FR-004 | §A leaf uplink port-channel (reuse) |
| FR-005 | §B3 MSTP per-tier priorities rendered |
| FR-006 | §B1 VNI base omission |
| FR-007 | §B1 l2vlan tags + §B2 node filter.tags |
| FR-008 | §C pure-L2 invariant |
| FR-009 | VNI omission gated on tenant value (overlay tenants unchanged) |
| FR-010 | §B4 host access ports + PortFast |
| FR-011 | §A/§B4 firewall trunk PC to both spines |
| FR-012 | §A single/dual-homed cabling |
| FR-013/FR-014/FR-015 | §C + quickstart harness + idempotence gate |
| FR-016 | convention hostnames retained (feature-level parity) |
