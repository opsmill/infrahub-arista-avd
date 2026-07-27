---
title: Hostvars Reference
description: The PyAVD-compatible hostvars structure built per device role by Phase 1 of the pipeline.
audience: developer
sidebar_position: 2
---

# Hostvars Reference

:::info Developer Guide
Hostvars structure is **PyAVD-version-sensitive** — see the [overview](./overview.md#pyavd-version) for the pinned version.
:::

[`generate-avd-device-hostvar`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) builds the PyAVD hostvars dict below for each `DcimDevice`. The dict is serialised to JSON and stored as an `AvdHostvarFile` attached to the device's `AvdArtifact` (see [AvdArtifact & File Storage](./artifacts.md)).

## Top-level fields (all roles)

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `type` | string | Role-mapped from `DcimDevice.role.value` | See [Role Mapping](./role-mapping.md). |
| `fabric_name` | string | `NetworkFabric.name.value` | |
| `id` | int | `DcimDevice.node_id.value` | Fabric-unique device identifier. |
| `bgp_as` | string | `DcimDevice.asn.node.asn.value` | Stringified; PyAVD expects a string. |
| `loopback_ipv4_address` | string | `DcimDevice.loopback_ip` | Optional; stripped of CIDR. |
| `vtep_loopback_ipv4_address` | string | `DcimDevice.vtep_loopback_ip` | Leaf and border-leaf only; stripped of CIDR. |
| `mgmt_ip` | string | `DcimDevice.mgmt_ip` | Optional; includes CIDR (e.g. `10.255.0.11/24`). |
| `mgmt_gateway` | string | Fabric-level setting | Optional. |
| `spanning_tree_settings.mode` | string | `NetworkFabric.spanning_tree_mode.value` | Optional; pyAVD 6.3 fabric-wide STP mode (`mstp`, `rstp`, `rapid-pvst`, or `none`). |

The builder for these basics lives in [`generators/generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) as `_build_hostvars()`. (The role→AVD-type mapping it uses, `ROLE_TO_AVD_TYPE`, lives in [`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py).)

Role-specific STP priorities are modeled as `NetworkSpanningTreePriority` child objects on the fabric. When a child exists for the device role, the hostvars builder emits it under the matching AVD node type defaults, for example `l3leaf.defaults.spanning_tree_priority: 8192`. The legacy fabric-level `spanning_tree_priority` field is still present for non-destructive migration compatibility but is ignored by hostvar generation.

## Uplink fields — `spine`, `leaf`, `border_leaf`, `l2leaf`

Super-spines have no uplinks; all other roles do.

| Field | Type | Notes |
|-------|------|-------|
| `uplink_interfaces` | list[string] | Local interfaces, e.g. `["Ethernet1", "Ethernet2"]`. |
| `uplink_switches` | list[string] | Upstream device hostnames, matched 1:1 with `uplink_interfaces`. |
| `uplink_switch_interfaces` | list[string] | Upstream interface names, matched 1:1 with `uplink_interfaces`. |

These are derived from `DcimInterface` objects on the device that carry `role = "uplink"`, plus their connected remote interfaces via `NetworkLink`.

### Uplink role by device role

Which *remote* role supplies the uplink depends on the local role:

| Local role | Uplink remote role |
|------------|-------------------|
| `super_spine` | none (top of fabric) |
| `spine` | `super_spine` |
| `leaf` | `spine` |
| `border_leaf` | `spine` |
| `l2leaf` | `leaf` |

Enforced in [`generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py).

## Role-specific blocks

### `super_spine`

No additional fields beyond top-level. Super-spines sit at the top of the fabric and receive uplinks from spines; they have no own uplinks.

### `spine`

- Uplink block (above) with upstream `super_spine` devices.
- No leaf-level extensions (no MLAG, no virtual MAC).

### `leaf` and `border_leaf`

Leaves and Border Leafs map to PyAVD `l3leaf` and carry the richest hostvars:

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

Border Leafs additionally consume valid `NetworkLink` objects with `role=dci` and emit PyAVD `l3_edge.p2p_links` entries. Each DCI link must have exactly two inherited physical endpoints, both endpoint devices must use role `border_leaf`, and both endpoint interfaces must use role `peering`. When the fabric underlay routing protocol is **eBGP**, both endpoint devices must have a BGP ASN assigned and each end's `as` is taken from the endpoint device's own `asn`; with a non-BGP underlay (e.g. OSPF) the link is still emitted for reachability, `as` is omitted, and no ASN is required. Point-to-point addresses are allocated as one `/31` per link; the pool is taken deterministically from the sorted-first endpoint's `NetworkFabric.dci_pool` (falling back to the peer's), so both border leafs — even in different fabrics — allocate the same prefix. Endpoint IPs are not stored as DCI-specific link fields.

Generated DCI entries are self-contained and do not use `l3_edge.p2p_links_profiles` or per-link `profile` references:

```json
{
  "l3_edge": {
    "p2p_links": [
      {
        "nodes": ["ih-dc1-leaf1a", "ih-dc2-leaf1a"],
        "interfaces": ["Ethernet5", "Ethernet5"],
        "as": [65101, 65201],
        "ip": ["172.16.0.0/31", "172.16.0.1/31"],
        "include_in_underlay_protocol": true,
        "speed": "100g"
      }
    ]
  }
}
```

`speed` is emitted only when endpoint/interface data provides a resolvable speed. When it cannot be resolved, the key is omitted and pyAVD uses its normal behavior.

Border Leafs are also the only role eligible for modeled EVPN Multi-Domain Gateway hostvars.
A target Border Leaf that is a member of an `EvpnGatewayGroup` emits `l3leaf.nodes[].evpn_gateway`:

```json
{
  "remote_peers": [{"hostname": "remote-border-leaf"}],
  "evpn_l2": {"enabled": true},
  "evpn_l3": {"enabled": true, "inter_domain": true},
  "d_path": {
    "enabled": true,
    "local_domain_id": "65100:1",
    "remote_domain_id": "65200:1"
  },
  "all_active_multihoming": {
    "enabled": true,
    "evpn_ethernet_segment": {
      "identifier": "0000:0000:0000:0001:0001",
      "rt_import": "00:00:00:00:00:01"
    }
  }
}
```

The generator derives the local D-PATH domain ID from `EvpnGatewayGroup.local_domain`, validates that the selected `EvpnGatewayGroup.pod.evpn_domain` matches that parent domain, derives the remote D-PATH domain ID from `EvpnGatewayGroup.remote_domain`, and derives `remote_peers[].hostname` from other valid Border Leaf members in gateway groups that share the same remote EVPN Domain. It does not emit deprecated pyAVD 6.3.0 keys under `all_active_multihoming` such as `enable_d_path`, `evpn_domain_id_local`, or `evpn_domain_id_remote`.

Gateway group intent fails before writing the hostvar file when the target or any member is not a Border Leaf, the group has no `local_domain`, the selected Pod has no matching EVPN Domain, the remote domain is missing or conflicts with the local domain, a member is outside the group Pod, or required All-Active Ethernet Segment values are missing. Hostname-only remote peers depend on the structured-config generator aggregating every gateway member's stored hostvars before `pyavd.get_avd_facts()` runs.

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
- For bonded servers, server `Bond1` is the primary VLAN source. Switch `Port-Channel<ID>` VLANs are used when the Bond has no VLAN relationships, and member Ethernet VLANs are only a compatibility fallback.

## AVD custom hostvars escape hatch

`avd_custom_hostvars` is an optional JSON attribute on `NetworkFabric`, `NetworkPod`, and `DcimDevice`. It is intended as an escape hatch for pyAVD hostvars that are not yet modeled by the Infrahub schemas and hostvar generator.

Custom hostvars are merged in this order:

1. `NetworkFabric.avd_custom_hostvars`
2. `NetworkPod.avd_custom_hostvars`
3. `DcimDevice.avd_custom_hostvars`
4. Generated hostvars from Infrahub-modeled data

That means device-level custom values override pod-level custom values, pod-level custom values override fabric-level custom values, and generated hostvars override all custom values. Custom hostvars are fill-only relative to modeled data: they can add keys the generator does not produce, but they cannot replace generated values such as `fabric_name`, role-specific `nodes`, generated tenant data, or generated connected endpoints.

Dictionaries merge recursively. Lists and scalar values replace the lower-precedence value as a whole; there is no element-wise list merge. Missing, `null`, or empty custom values are ignored. Non-empty custom values must be mappings; a list or scalar raises `TypeError` before pyAVD validation runs.

Example:

```json
{
  "fabric_name": "ignored-custom-name",
  "custom_structured_configuration_prefix": ["custom"],
  "l3leaf": {
    "defaults": {
      "platform": "7280R3"
    },
    "nodes": [
      {
        "name": "ignored-custom-node"
      }
    ]
  }
}
```

In the final hostvars, `custom_structured_configuration_prefix` and `l3leaf.defaults.platform` survive if the generator does not set them. The generated `fabric_name` and generated `l3leaf.nodes` still win.

The escape hatch is the delivery mechanism for capabilities the AVD example scenarios need but that are not modeled natively — for example campus dot1x/PoE/port-profiles/in-band management and MPLS/VPN-IPv4 for ISIS-LDP IPVPN. See [Extending the Pipeline → Native schema vs. the escape hatch](./extending.md#native-schema-vs-the-escape-hatch) for when to use it instead of a native schema change.

## Native inputs for the AVD example scenarios

The following native schema inputs anchor the AVD example scenarios. They are optional and default to backward-compatible values, so existing designs are unaffected:

| Input | Node | Scenario |
|-------|------|----------|
| `evpn_vlan_aware_bundles` (Boolean) | `NetworkFabric` | Multi-Pod 5-stage Clos |
| `underlay_routing_protocol` values `none`, `isis-ldp` | `NetworkFabric` | Standalone L2LS (`none`), ISIS-LDP IPVPN (`isis-ldp`) |
| Roles `l2spine`, `l3spine`, `p`, `pe`, `rr` | `DcimDevice` | L2LS, campus, ISIS-LDP IPVPN — see [Role Mapping](./role-mapping.md) |

Generator consumption of these inputs (route-server derivation, standalone L2LS and campus topology generation) is delivered alongside the per-scenario seed designs.

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
  "spanning_tree_settings": {
    "mode": "mstp"
  },
  "l3leaf": {
    "defaults": {
      "spanning_tree_priority": 8192
    }
  },
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
