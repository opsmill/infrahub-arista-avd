# Phase 1 Data Model: L2LS Fabric Example Conformance (Schema cycle)

This is the schema/data-model delta for representing the AVD `l2ls-fabric`
example. It lists only the **changes** to the existing model; unchanged nodes
(`NetworkFabric`, `NetworkPod`, `LocationRack`, `DcimDevice`, `MlagDomain`,
`Avd.Tag`, `IpamVLAN`) are referenced, not redefined. Attribute kinds and
relationship types follow Infrahub schema conventions per `infrahub-managing-schemas`.

Legend: **[NEW]** added, **[MOD]** modified, **[REUSE]** existing, relied upon.

---

## 1. Network.SpanningTreePriority  **[MOD]** (`schemas/l3ls_extensions.yml`)

Per-role spanning-tree priority, one row per (fabric, role).

| Field | Kind | Change | Notes |
|-------|------|--------|-------|
| `role` | Dropdown | **[MOD]** add choices `l2spine`, `l3spine` | Existing: `super_spine`, `spine`, `leaf`, `l2leaf`. Example uses `l2spine`=4096, `l2leaf`=16384 |
| `priority` | Number | [REUSE] | Multiple of 4096 (validation rule) |
| `fabric` (rel) | Parent → NetworkFabric | [REUSE] | `fabric__spanning_tree_priorities` |

**Validation rules**: `priority` MUST be a multiple of 4096; `(fabric, role)`
unique (existing uniqueness constraint); a role value MUST correspond to a device
role rendered in the fabric.

## 2. Evpn.Tenant  **[MOD]** (`schemas/evpn/evpn_services.yml`)

Service container. Made usable for overlay-free (pure-L2) fabrics.

| Field | Kind | Change | Notes |
|-------|------|--------|-------|
| `name` | Text (unique) | [REUSE] | Example: `MY_FABRIC` |
| `mac_vrf_vni_base` | Number | **[MOD]** `optional: true` | Unset ⇒ overlay-free tenant; generator omits it from hostvars |
| `l2vlans` (rel) | Component → EvpnL2Vlan | [REUSE] | |
| `fabrics` (rel) | Attribute → NetworkFabric | [REUSE] | Links tenant to `Fabric-L2LS` |
| `tags` (rel) | Attribute → BuiltinTag | [REUSE] | |

**Validation rules**: When `mac_vrf_vni_base` is unset, no VNI/VXLAN artifacts may
be derived for the tenant's VLANs. Existing overlay tenants (Fabric-A/B/C) keep a
value — backward compatible.

**State/behavior**: overlay-free ⇔ `mac_vrf_vni_base` is null.

## 3. Evpn.L2Vlan  **[MOD]** (`schemas/evpn/evpn_services.yml`)

Pure Layer-2 VLAN within a tenant, now scopable to leaf pairs by tag.

| Field | Kind | Change | Notes |
|-------|------|--------|-------|
| `name` | Text | [REUSE] | Example: BLUE-NET / GREEN-NET / ORANGE-NET |
| `vlan_id` | Number | [REUSE] | 10 / 20 / 30 |
| `vni_override` | Number (optional) | [REUSE] | Left unset for L2LS |
| `tenant` (rel) | Parent → EvpnTenant | [REUSE] | |
| `vlan` (rel) | Attribute → IpamVLAN | [REUSE] | Underlying VLAN object |
| `rack_tags` (rel) | Attribute → LocationRack, cardinality many, optional | **[NEW]** | Rack names emitted as AVD VLAN tags |
| `avd_tags` (rel) | Attribute → Avd.Tag, cardinality many, optional | **[NEW]** | AVD tag names emitted as AVD VLAN tags |

**Validation rules**: `(tenant, vlan_id)` unique (existing). A VLAN with tags MUST
only render on leaves whose node `filter.tags` include one of those tags; a VLAN
with no matching leaf MUST be surfaced (edge case), not silently dropped.

**Relationship parity**: `rack_tags`/`avd_tags` mirror `Evpn.Svi` exactly
(`evpn_services.yml:120-135`) so the generator's `_build_svi_tags` helper applies.

## 4. Connected-endpoint / port-profile intent  **[NEW/MOD]** (`schemas/objects/objects.yml` + endpoint model)

Support access/trunk switchport intent and a spine-attached firewall. Exact node
placement (on the adapter model vs. a dedicated port-profile node) is finalized in
the endpoint/generator cycle; the schema seams defined here are:

| Concept | Kind | Change | Notes |
|---------|------|--------|-------|
| adapter/switchport `mode` | Dropdown (access/trunk) | **[NEW]** | Access for hosts, trunk for firewall |
| `access_vlan` | Number (optional) | **[NEW]** | Host access VLAN (10/20/30) |
| `trunk_vlans` | Text/List (optional) | **[NEW]** | Firewall allowed VLANs (10,20,30) |
| `portfast` | Dropdown/Boolean (optional) | **[NEW]** | `edge` for host access ports |
| endpoint → spine attachment | relationship reuse | **[MOD]** | Allow a connected endpoint (firewall) to cable to `l2spine` devices, not only rack leaves |
| port-channel (LACP) | [REUSE] | — | `Interface.Lag` + adapter `port_channel` already modeled |

**Decision gate**: hosts are modeled natively (reusable, first-class); the firewall
trunk-to-spine is native if the spine-attached-endpoint path is cheap, otherwise via
`avd_custom_hostvars` on the two spines (documented). See research Decision 4.

## 5. Reused, unchanged (relied upon by the seed reshape)

- **NetworkFabric** — `underlay_routing_protocol: none`, `spanning_tree_mode: mstp`,
  pools, `dns_servers`/`ntp_servers`/`local_users`, `spanning_tree_priorities`.
- **NetworkPod** — `amount_of_spines: 2`, `mlag_peer_pool`, spine template.
- **LocationRack** — `amount_of_leafs`, `mlag: true`, `leaf_switch_template`,
  `avd_tags` (inverse of `Avd.Tag.racks`).
- **DcimDevice** — roles `l2spine`/`l2leaf` (already present); names produced by the
  generator naming cycle to match SPINE1-2/LEAF1-4.
- **Avd.Tag** — `racks` relationship (tag→rack scoping) used to build blue/green/
  orange zones.
- **MlagDomain / Mlag.Domain / Mlag.Interface** — spine-pair and leaf-pair MLAG.
- **Interface.Lag** — uplink and endpoint port-channels.

---

## Entity relationship summary (L2LS-relevant slice)

```text
NetworkFabric (Fabric-L2LS, underlay=none, stp=mstp)
├── spanning_tree_priorities → Network.SpanningTreePriority [l2spine=4096, l2leaf=16384]   (role enum extended)
├── pods → NetworkPod (2 spines, mlag_peer_pool)
│         └── racks → LocationRack (RACK1: LEAF1/2, RACK2: LEAF3/4; mlag=true)
│                       └── devices → DcimDevice (role l2spine / l2leaf)
│                       └── avd_tags ← Avd.Tag (bluezone / greenzone / orangezone)
└── (services) Evpn.Tenant (MY_FABRIC, mac_vrf_vni_base = null → overlay-free)
              └── l2vlans → Evpn.L2Vlan (BLUE 10 / GREEN 20 / ORANGE 30)
                            ├── vlan → Ipam.VLAN
                            └── rack_tags / avd_tags → (scope to leaf pairs)     (NEW)

Connected endpoints:
  Compute.PhysicalServer (HostA-C, Host2) → adapters (mode=access, access_vlan, portfast=edge) → l2leaf ports
  Firewall endpoint → adapters (mode=trunk, trunk_vlans=10,20,30, port-channel) → BOTH l2spine devices   (NEW spine attach)
```

## Traceability (spec FR → model change)

| FR | Model change |
|----|--------------|
| FR-004 (STP priorities) | Decision 1 / §1 role enum + priority objects |
| FR-006 (standalone L2, no overlay) | §5 `underlay_routing_protocol: none` (reused) |
| FR-007 (3 VLANs, tenant) | §2/§3 tenant + l2vlans |
| FR-008 (no EVPN/VXLAN/BGP) | §2 optional `mac_vrf_vni_base` (overlay-free) |
| FR-009 (tag scoping) | §3 `rack_tags`/`avd_tags` |
| FR-010 (host access profiles) | §4 mode/access_vlan/portfast |
| FR-011 (firewall trunk PC to spines) | §4 trunk_vlans + spine attach |
| FR-012 (single/dual-homed) | §4 + reused LAG |
| FR-001/002/003/005 (topology/MLAG/uplinks) | §5 reused nodes + seed reshape (Decision 5) |
