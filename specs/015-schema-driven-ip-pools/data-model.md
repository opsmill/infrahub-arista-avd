# Phase 1 Data Model: Schema-Driven AVD IP Pools

All changes are made via the `extensions.nodes` block in `schemas/l3ls_extensions.yml`. No changes to `schemas/logical_design.yml`.

## Entities affected

### NetworkFabric (existing node — extended)

| Relationship | Action | Peer | Cardinality | Optional | identifier | order_weight | Notes |
|--------------|--------|------|-------------|----------|-----------|--------------|-------|
| `uplink_pool` | **modify** | `CoreIPPrefixPool` | one | `true` → **`false`** | `fabric__uplink_pool` (unchanged) | 10400 (unchanged) | Source for pyAVD `uplink_ipv4_pool`; replaces `10.250.0.0/16` |
| `vtep_pool` | **modify** | `CoreIPPrefixPool` | one | `true` → **`false`** | `fabric__vtep_pool` (unchanged) | 10500 (unchanged) | Source for pyAVD `vtep_loopback_ipv4_pool`; replaces `10.251.0.0/24` |
| `loopback_pool` | **add (new)** | `CoreIPPrefixPool` | one | **`false`** | `fabric__loopback_pool` | 10600 | Source for pyAVD `loopback_ipv4_pool`; replaces `10.255.0.0/24` (which collided with mgmt) |

All three carry `branch: aware`, a human `label`, and a `description`. Only `optional` and (for `loopback_pool`) the whole relationship are new — no existing identifier or order_weight is disturbed.

### NetworkPod (existing node — unchanged this cycle)

| Relationship | Action | Peer | Optional | Rationale |
|--------------|--------|------|----------|-----------|
| `mlag_peer_pool` | none | `CoreIPAddressPool` | stays `true` | Not every pod uses MLAG (FR-021) |
| `mlag_l3_pool` | none | `CoreIPAddressPool` | stays `true` | Same; name kept to avoid destructive rename (research R4) |

### Pool objects (seed data — `CoreIPPrefixPool` / `CoreIPAddressPool`)

New `CoreIPPrefixPool` objects and supporting `IpamPrefix` to satisfy the now-mandatory relationships:

| Pool object | Kind | Resource prefix | For |
|-------------|------|-----------------|-----|
| `Fabric-A-Loopback-Pool` | `CoreIPPrefixPool` | `10.255.2.0/24` | Fabric-A `loopback_pool` |
| `Fabric-B-Loopback-Pool` | `CoreIPPrefixPool` | `10.255.3.0/24` | Fabric-B `loopback_pool` |
| `Fabric-B-Uplink-Pool` | `CoreIPPrefixPool` | (new P2P prefix, e.g. `10.254.252.0/22`) | Fabric-B `uplink_pool` |
| `Fabric-B-VTEP-Pool` | `CoreIPPrefixPool` | (new loopback prefix, e.g. `10.254.1.0/27`) | Fabric-B `vtep_pool` |

`default_prefix_length`: `32` for loopback/VTEP pools, `31` for uplink (matching the existing `Fabric-A-*` pools). Prefixes chosen to avoid overlap with mgmt `10.255.0.0/24` and the existing Fabric-A allocations.

## Validation rules (from spec requirements)

- **FR-020 / SC-003**: `uplink_pool`, `vtep_pool`, `loopback_pool` are `optional: false` on `NetworkFabric` → the platform rejects saving a fabric without them.
- **FR-021**: `mlag_peer_pool`, `mlag_l3_pool` remain `optional: true` → a pod may omit them.
- **FR-015 / peer-kind rule**: prefix pools use `CoreIPPrefixPool`; address pools use `CoreIPAddressPool` — the relationship `peer` enforces the kind.
- **FR-016**: all relationship names snake_case; `loopback_pool` identifier `fabric__loopback_pool` is unique vs. existing `pod__loopback_pool`.
- **Loopback non-overlap (research R2)**: the loopback pool prefix MUST NOT intersect `10.255.0.0/24` (management).

## Seed-data references (`objects/10_fabric.yml`)

- **Fabric-A**: add `loopback_pool: "Fabric-A-Loopback-Pool"` (already has `uplink_pool`, `vtep_pool`).
- **Fabric-B**: add `uplink_pool: "Fabric-B-Uplink-Pool"`, `vtep_pool: "Fabric-B-VTEP-Pool"`, `loopback_pool: "Fabric-B-Loopback-Pool"` (currently has none — required once mandatory).
- Pod MLAG references unchanged.

## Out of scope (generator cycle)

- Removing the `10.250` / `10.251` / `10.255` literals in `generate_avd_device_hostvar.py`.
- Reading `fabric.loopback_pool` and raising a clear error when a required-but-empty pool is linked.
- Replacing the `mlag_l_3_pool`/`mlag_l3_pool` getattr dance with a typed accessor.
