# Data Model: Fabric Pool Management

This feature extends existing Infrahub schema entities. It does not introduce replacement fabric, pod, pool, or prefix nodes.

## NetworkFabric

**Purpose**: Existing fabric root that owns the authoritative fabric-scope IP pool collection.

**Existing fields retained**:
- `name`: human-friendly fabric identifier.
- `underlay_routing_protocol`: determines whether Fabric Point-to-Point pools are required.
- `overlay_routing_protocol`: determines whether Loopback and Loopback VTEP pools are required.
- `mgmt_pool`: legacy Management pool relationship; retained during migration.
- `uplink_pool`: legacy Fabric Point-to-Point pool relationship; retained during migration and made optional before Fabric Supernet fallback is authoritative.
- `vtep_pool`: legacy Loopback VTEP pool relationship; retained during migration and made optional.
- `loopback_pool`: legacy Loopback pool relationship; retained during migration and made optional.
- `dci_pool`: legacy DCI pool relationship; retained during migration.

**New relationship**:
- `fabric_ip_pools`: many-valued Attribute relationship labeled `Fabric IP Pools`, targeting `CoreResourcePool` so the collection can include `CoreIPPrefixPool` and `CoreIPAddressPool` members.

**Validation rules**:
- Must include exactly one authoritative Management pool, either explicitly or via compatible migration state.
- Requires Loopback and Loopback VTEP pools when `overlay_routing_protocol` is non-empty.
- Requires Fabric Point-to-Point pool when `underlay_routing_protocol` is non-empty and not `none`.
- Requires DCI pool when any fabric device participates in a `NetworkLink` with `role=dci`.
- If any required fabric pool is missing, a Fabric Supernet pool must be available.
- No two pools in the same fabric scope may satisfy the same role.
- Non-IP resource pools must not be accepted as authoritative fabric IP pools.

## NetworkPod

**Purpose**: Existing pod under a fabric that owns pod-specific pool boundaries and MLAG pool intent.

**Existing fields retained**:
- `name`: pod identifier.
- `role`: distinguishes fabric, CPU, and storage pods.
- Parent relationship to `NetworkFabric`.
- `mlag_peer_pool`: legacy MLAG Peer pool relationship; retained during migration.
- `mlag_l3_pool`: legacy MLAG L3 Peering pool relationship; retained during migration.

**New relationship**:
- `pod_ip_pools`: many-valued Attribute relationship labeled `Pod IP Pools`, targeting `CoreResourcePool` so the collection can include `CoreIPPrefixPool` and `CoreIPAddressPool` members.

**Validation rules**:
- May include Loopback, Loopback VTEP, Fabric Point-to-Point, MLAG, and MLAG Peering pools.
- Must not require a Management pool; management resolves from the parent fabric.
- Pod Loopback, Loopback VTEP, and Fabric Point-to-Point pools must be subnets of the matching parent fabric pool role.
- Requires MLAG pool when the parent fabric has no underlay routing protocol or any rack in the pod has MLAG enabled.
- Requires MLAG Peering pool when underlay routing is defined and MLAG is configured in the pod.
- No two pools in the same pod scope may satisfy the same role.
- Non-IP resource pools must not be accepted as authoritative pod IP pools.

## LocationRack

**Purpose**: Existing rack under a pod whose MLAG settings influence pod-level required pools.

**Existing fields used**:
- Parent relationship to `NetworkPod`.
- Existing MLAG-related design fields used by generators and checks.

**Validation rules**:
- Any rack with MLAG enabled makes the parent pod require MLAG pool role.
- Rack-level MLAG Peer and MLAG L3 Peering allocations are /31 networks.
- A pod-level /31 MLAG pool is intentionally reusable by every rack in the pod.
- A pod-level MLAG pool larger than /31 must contain rack-level /31 allocations.

## IpamPrefix

**Purpose**: Prefix resource whose role identifies the purpose of the pool consuming it.

**Existing attribute**:
- `role`: required Dropdown attribute in `schemas/ipam_extensions.yml`.

**Role choices after schema change**:
- Existing retained values: `supernet`, `pod_super_spine_spine`, `pod_leaf_spine`, `loopback`, `loopback-vtep`, `technical`, `management`, `backfill`.
- New values: `fabric_supernet`, `fabric_point_to_point`, `dci`, `mlag`, `mlag_peering`.

**Validation rules**:
- A pool must resolve to exactly one authoritative fabric or pod role from its backing prefix resources.
- Mixed-purpose backing prefixes make the pool invalid for role-based resolution.
- `backfill` and other non-fabric-specific roles do not satisfy fabric or pod pool requirements.
- Superseded values remain valid only for compatibility until migration maps them to new role choices.

## CoreIPPrefixPool

**Purpose**: Existing Infrahub pool kind used for prefix allocation.

**Fabric roles**:
- Loopback
- Loopback VTEP
- Fabric Point-to-Point
- DCI
- Fabric Supernet

**Pod roles**:
- Loopback
- Loopback VTEP
- Fabric Point-to-Point

**Validation rules**:
- Backing resources must be `IpamPrefix` objects with a role matching the intended pool purpose.
- Prefix-pool roles in pod scope must be contained by the matching fabric prefix pool.
- Fabric Supernet can supply missing required fabric pools in later generator work but must remain a distinct role.

## CoreIPAddressPool

**Purpose**: Existing Infrahub pool kind used for address allocation.

**Fabric roles**:
- Management

**Pod roles**:
- MLAG
- MLAG Peering

**Validation rules**:
- Management pools are fabric-scoped only.
- MLAG and MLAG Peering pools are pod-scoped.
- MLAG /31 pool resources may be intentionally reused across racks in the pod.

## Fabric Pool Role Resolution

**Purpose**: Derived contract used by future checks and generators; not a stored schema node.

**Inputs**:
- `NetworkFabric.fabric_ip_pools`
- Backing `IpamPrefix.role` values for each pool resource
- Fabric routing attributes
- DCI-role `NetworkLink` participation
- Legacy relationships during migration

**Outputs**:
- Required-role set for the fabric.
- Missing-role set.
- Duplicate-role errors.
- Mixed-role pool errors.
- Fabric Supernet fallback eligibility.

**Rules**:
- The collection is authoritative after migration.
- Legacy relationships can be used only as compatibility inputs until object and generator migration is complete.
- Required roles are evaluated from fabric intent, not from pool names.

## Pod Pool Role Resolution

**Purpose**: Derived contract used by future checks and generators; not a stored schema node.

**Inputs**:
- `NetworkPod.pod_ip_pools`
- Parent `NetworkFabric.fabric_ip_pools`
- Backing `IpamPrefix.role` values for each pool resource
- Parent fabric routing attributes
- Rack MLAG settings
- Legacy MLAG relationships during migration

**Outputs**:
- Required-role set for the pod.
- Missing-role set.
- Duplicate-role errors.
- Mixed-role pool errors.
- Subnet containment errors.
- MLAG default intent requirements.

**Rules**:
- Pod management pools are invalid as authoritative pod pool requirements.
- Pod prefix pools must be subnets of matching fabric prefix pools.
- Missing required MLAG pools trigger deterministic default intent in later generator work.

## Migration Mapping

**Purpose**: Compatibility mapping from current data to the role-driven collection model.

**Fabric relationship mapping**:
- `mgmt_pool` -> `fabric_ip_pools` member with backing prefix role `management`.
- `uplink_pool` -> `fabric_ip_pools` member with backing prefix role `fabric_point_to_point`.
- `vtep_pool` -> `fabric_ip_pools` member with backing prefix role `loopback-vtep`.
- `loopback_pool` -> `fabric_ip_pools` member with backing prefix role `loopback`.
- `dci_pool` -> `fabric_ip_pools` member with backing prefix role `dci`.

**Pod relationship mapping**:
- `mlag_peer_pool` -> `pod_ip_pools` member with backing prefix role `mlag`.
- `mlag_l3_pool` -> `pod_ip_pools` member with backing prefix role `mlag_peering`.

**Role value mapping**:
- `supernet` -> `fabric_supernet`.
- `pod_leaf_spine` -> `fabric_point_to_point`.
- `pod_super_spine_spine` -> `fabric_point_to_point`.
- `technical` -> `dci`, `mlag`, or `mlag_peering` based on the legacy relationship and pool use.

**State transitions**:
- `compatibility`: new collections exist, legacy relationships remain present.
- `dual_populated`: current seed object data populates both collection relationships and legacy relationships.
- `collection_authoritative`: generators/checks consume the collections first and treat legacy relationships as fallback only.
- `legacy_absent`: a later schema migration removes legacy relationships using the repository-approved `state: absent` pattern.

Current repository seed data is in the `dual_populated` state for the migrated example fabrics: every legacy fabric pool relationship has a matching `fabric_ip_pools` entry, every legacy pod MLAG relationship has a matching `pod_ip_pools` entry, and legacy prefix role values used for fabric, DCI, and MLAG pool purposes have explicit replacement roles.
