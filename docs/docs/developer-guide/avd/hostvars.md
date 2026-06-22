---
title: Hostvars Reference
description: The pyAVD-compatible hostvars structure built per device role by Phase 1 of the pipeline.
audience: developer
sidebar_position: 2
---

# Hostvars Reference

:::info Developer Guide
This page is part of the developer guide. Hostvars structure is **pyAVD-version-sensitive** — see the [overview](./overview.md#pyavd-version) for the pinned version.
:::

This page documents the pyAVD hostvars dict that [`generate-avd-device-hostvar`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) produces for each `NetworkDevice`. The dict is serialised to JSON and stored as an `AvdHostvarFile` attached to the device's `AvdArtifact` (see [AvdArtifact & File Storage](./artifacts.md)).

## Top-level fields (all roles)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `type` | string | Role-mapped from `NetworkDevice.role.value` | See [Role Mapping](./role-mapping.md). |
| `fabric_name` | string | `NetworkFabric.name.value` | |
| `id` | int | `NetworkDevice.node_id.value` | Fabric-unique device identifier. |
| `bgp_as` | string | `NetworkDevice.bgp_asn.value` | Stringified; pyAVD expects a string. |
| `loopback_ipv4_address` | string | `NetworkDevice.loopback_ip` | Optional; stripped of CIDR. |
| `mgmt_ip` | string | `NetworkDevice.mgmt_ip` | Optional; includes CIDR (e.g. `10.255.0.11/24`). |
| `mgmt_gateway` | string | Fabric-level setting | Optional. |

The builder for these basics lives in [`generators/generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) as `_build_hostvars()`. (The role→AVD-type mapping it uses, `ROLE_TO_AVD_TYPE`, lives in [`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py).)

## Uplink fields — `spine`, `leaf`, `l2leaf`

Super-spines have no uplinks; all other roles do.

| Field | Type | Notes |
|-------|------|-------|
| `uplink_interfaces` | list[string] | Local interfaces, e.g. `["Ethernet1", "Ethernet2"]`. |
| `uplink_switches` | list[string] | Upstream device hostnames, matched 1:1 with `uplink_interfaces`. |
| `uplink_switch_interfaces` | list[string] | Upstream interface names, matched 1:1 with `uplink_interfaces`. |

These are derived from `NetworkInterface` objects on the device that carry `role = "uplink"`, plus their connected remote interfaces via `NetworkLink`.

### Uplink role by device role

Which *remote* role supplies the uplink depends on the local role:

| Local role | Uplink remote role |
|------------|-------------------|
| `super_spine` | none (top of fabric) |
| `spine` | `super_spine` |
| `leaf` | `spine` |
| `l2leaf` | `leaf` |

Enforced in [`generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py).

## Role-specific blocks

### `super_spine`

No additional fields beyond top-level. Super-spines sit at the top of the fabric and receive uplinks from spines; they have no own uplinks.

### `spine`

- Uplink block (above) with upstream `super_spine` devices.
- No leaf-level extensions (no MLAG, no virtual MAC).

### `leaf`

Leaves carry the richest hostvars:

| Field | Notes |
|-------|-------|
| Uplink block | Upstream `spine` devices. |
| `mlag_domain_id` | Derived from MLAG peer relationship if the leaf has a peer. |
| `mlag_peer` | Hostname of the MLAG peer leaf. |
| `mlag_peer_ipv4_address` | Peer link IP. |
| `virtual_router_mac_address` | Per-fabric VMAC used for SVI gateways. |
| `l3_interfaces` / SVIs | Emitted from `EvpnSvi` objects attached to VLANs on this leaf's L2 domain. |
| `connected_endpoints` | Per interface with `role = "server"` (see below). |
| EVPN tenants/VRFs/VLANs | Derived from `EvpnTenant` → `IpamVRF` → `EvpnSvi` → `IpamVLAN` chain filtered to this fabric. |

### `l2leaf`

L2 leaves are BGP-less layer-2 extenders. The hostvars builder **skips**:

- L3LS settings (no BGP peering section).
- EVPN tenants, VRFs, SVIs.
- MLAG (unless explicitly present).

It keeps:

- Top-level fields (id, role, loopback, mgmt).
- Uplink block (upstream `leaf` devices).
- `connected_endpoints` for `role = "server"` interfaces.

## `connected_endpoints` — server adapters

For every interface on the device whose `role.value == "server"`, an entry is emitted:

```json
{
  "name": "server-1",
  "adapters": [
    {
      "endpoint_ports": ["eth0"],
      "switch_ports": ["Ethernet10"],
      "switches": ["leaf-pod-A1-1"],
      "mode": "trunk",
      "vlans": "100-105"
    }
  ]
}
```

- `mode: "trunk"` + `vlans: "100-105"` for interfaces with multiple tagged VLANs (formatted via `netutils`).
- `mode: "access"` + a single `vlans: "100"` for access-only interfaces.
- `native_vlan: 100` added if an untagged VLAN is configured alongside tagged VLANs.

## Validation

Once the dict is built, Phase 1 calls `pyavd.validate_inputs()` on the whole hostvars object. Validation failures are non-recoverable — the generator returns a failure for that device and does **not** write the `AvdHostvarFile`.

Common validation failures:

- Missing required fields (`id`, `bgp_as`, `loopback_ipv4_address` for L3 roles).
- Invalid role name — must be one of the four values in the [Role Mapping](./role-mapping.md) table.
- Uplink mismatches (e.g. `uplink_interfaces` length ≠ `uplink_switches` length).

## Full leaf example

```json
{
  "type": "l3leaf",
  "fabric_name": "Fabric-A",
  "id": 1,
  "bgp_as": "65101",
  "loopback_ipv4_address": "10.255.1.1",
  "mgmt_ip": "10.255.0.11/24",
  "mgmt_gateway": "10.255.0.1",
  "uplink_interfaces": ["Ethernet1", "Ethernet2"],
  "uplink_switches": ["spine-A1-1", "spine-A1-2"],
  "uplink_switch_interfaces": ["Ethernet1", "Ethernet1"],
  "virtual_router_mac_address": "00:1C:73:00:00:11",
  "connected_endpoints": [
    {
      "name": "server-1",
      "adapters": [
        {
          "endpoint_ports": ["eth0"],
          "switch_ports": ["Ethernet10"],
          "switches": ["leaf-pod-A1-1"],
          "mode": "trunk",
          "vlans": "100-105"
        }
      ]
    }
  ]
}
```

## Tests

Unit tests cover the hostvars builder and the role→type mapping:

- [`tests/unit/test_hostvar_ordering.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_hostvar_ordering.py) — hostvars shape and deterministic ordering from `_build_hostvars()`.
- [`tests/unit/test_avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_avd.py) — the `ROLE_TO_AVD_TYPE` / `get_avd_type()` mapping.

Full hostvars generation is exercised by integration tests under `tests/integration/`.
