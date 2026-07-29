# Contract: Fabric Pool Schema

This contract defines the schema-facing interface that later object migrations, checks, generators, and documentation must consume.

## Schema Relationships

### NetworkFabric.fabric_ip_pools

- Kind: relationship on `NetworkFabric`.
- Name: `fabric_ip_pools`.
- Label: `Fabric IP Pools`.
- Relationship kind: `Attribute`.
- Cardinality: `many`.
- Optional: `true` during migration.
- Peer: `CoreResourcePool`, the common core pool kind available in the current generated protocols for `CoreIPPrefixPool` and `CoreIPAddressPool` members.
- Identifier: `fabric__ip_pools`.
- Authoritative after migration for these roles:
  - Management
  - Loopback
  - Loopback VTEP
  - Fabric Point-to-Point
  - DCI
  - Fabric Supernet

### NetworkPod.pod_ip_pools

- Kind: relationship on `NetworkPod`.
- Name: `pod_ip_pools`.
- Label: `Pod IP Pools`.
- Relationship kind: `Attribute`.
- Cardinality: `many`.
- Optional: `true` during migration.
- Peer: `CoreResourcePool`, the common core pool kind available in the current generated protocols for `CoreIPPrefixPool` and `CoreIPAddressPool` members.
- Identifier: `pod__ip_pools`.
- Authoritative after migration for these roles:
  - Loopback
  - Loopback VTEP
  - Fabric Point-to-Point
  - MLAG
  - MLAG Peering

## Prefix Role Values

The `IpamPrefix.role` Dropdown must include these new role names:

| Name | Label | Purpose |
|------|-------|---------|
| `fabric_supernet` | Fabric Supernet | Fabric-level pool that can supply missing required fabric pools. |
| `fabric_point_to_point` | Fabric Point-to-Point | Underlay routed point-to-point pool role. |
| `dci` | DCI | DCI point-to-point allocation role. |
| `mlag` | MLAG | MLAG peer-link address pool role. |
| `mlag_peering` | MLAG Peering | MLAG L3 peering address pool role. |

The dropdown must retain these existing role names during migration:

| Name | Migration target |
|------|------------------|
| `supernet` | `fabric_supernet` |
| `pod_leaf_spine` | `fabric_point_to_point` |
| `pod_super_spine_spine` | `fabric_point_to_point` |
| `technical` | `dci`, `mlag`, or `mlag_peering` based on current use |
| `loopback` | unchanged |
| `loopback-vtep` | unchanged |
| `management` | unchanged |
| `backfill` | unchanged, but never satisfies fabric/pod pool requirements |

## Pool Role Resolution

A pool resolves to a role by inspecting the roles of its backing `IpamPrefix` resources.

- A pool with zero backing resources is invalid for authoritative role resolution.
- A pool with backing resources that map to more than one authoritative role is invalid.
- A pool with only non-fabric roles, such as `backfill`, does not satisfy any fabric or pod pool requirement.
- Pool names are labels only; names must not be used as the source of role truth.

## Required Fabric Roles

For a `NetworkFabric`:

- Management is always required.
- Loopback and Loopback VTEP are required when `overlay_routing_protocol` is non-empty.
- Fabric Point-to-Point is required when `underlay_routing_protocol` is non-empty and not `none`.
- DCI is required when a fabric device participates in a `NetworkLink` whose role is `dci`.
- Fabric Supernet is required when any other required fabric pool is missing.
- No role may be satisfied by more than one pool in the same fabric.

## Required Pod Roles

For a `NetworkPod`:

- Management must resolve from the parent fabric and is not a pod pool requirement.
- Loopback, Loopback VTEP, and Fabric Point-to-Point pools are valid only when they are subnets of the matching parent fabric role pool.
- MLAG is required when the parent fabric has no underlay routing protocol or any rack in the pod has MLAG enabled.
- MLAG Peering is required when underlay routing is defined and MLAG is configured in the pod.
- No role may be satisfied by more than one pool in the same pod.

## MLAG Defaults

If a required pod MLAG pool is missing, later generator work must use deterministic default intent:

| Role | Default name | Default prefix |
|------|--------------|----------------|
| MLAG | `MLAG-Peer-Subnet` | `169.254.0.0/31` |
| MLAG Peering | `MLAG-L3-Peering-Subnet` | `192.0.0.0/31` |

If the pod-level MLAG pool is exactly /31, that /31 may be reused by every rack in the pod. If the pod-level MLAG pool is larger than /31, rack-level /31 allocations must be contained by that pool.

## Legacy Compatibility

Legacy relationships remain valid during migration:

- `NetworkFabric.mgmt_pool`
- `NetworkFabric.uplink_pool`
- `NetworkFabric.vtep_pool`
- `NetworkFabric.loopback_pool`
- `NetworkFabric.dci_pool`
- `NetworkPod.mlag_peer_pool`
- `NetworkPod.mlag_l3_pool`

During migration, collection relationships are the target model and legacy relationships are compatibility inputs. A later schema migration may remove legacy relationships only after object data, generated query models, generators, transforms, checks, and docs no longer require them.

## Contract Tests

Schema contract tests must verify:

- New role values exist and legacy role values remain.
- `fabric_ip_pools` and `pod_ip_pools` use many-cardinality Attribute relationships.
- The relationship peer is the full Infrahub kind `CoreResourcePool` and can hold the IP pool kinds used by the repository.
- Legacy relationships remain present and optional where compatibility requires it.
- No replacement `NetworkFabric` or `NetworkPod` node exists.
- Role mapping tables in this contract stay aligned with schema choices.
