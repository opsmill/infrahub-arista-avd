# Schema Design Specification: Fabric Pool Management

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate all schema definitions.

**Feature Branch**: `emdash/supernet-pool-xo43k`
**Created**: 2026-07-28
**Status**: Draft
**Input**: User description: "Streamline Fabric pool Management by replacing type-specific fabric pool attributes with one role-driven fabric pool collection, adding role-based required-pool validation, supporting fabric-supernet allocation for missing required pools, modeling pod pool inheritance/subnet constraints, and defining MLAG pool defaults and reuse behavior."

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

This feature is expected to update existing schema files rather than introduce parallel fabric or pod nodes, and it must implement the active validation and generator behavior needed to protect users from invalid role-driven pool assignments immediately:

- `schemas/ipam_extensions.yml`: authoritative IP prefix role choices.
- `schemas/logical_design.yml`, `schemas/l3ls_extensions.yml`, and `schemas/dci.yml`: fabric and pod pool relationships.
- Existing object data and generated type files will need migration in this feature or explicitly sequenced follow-up tasks before legacy relationships stop being authoritative.
- Role-based required-pool validation, duplicate-role validation, mixed-role validation, pod subnet-containment validation, and deterministic fallback/default behavior are in scope for this feature and must not be left as user-enforced conventions.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Manage Fabric Pools Through One Role-Driven Collection (Priority: P1)

As a fabric designer, I want all fabric IP pools to be associated through a single fabric-level pool collection so that fabric addressing requirements are determined from IPAM pool and prefix roles instead of separate per-purpose fabric fields.

**Why this priority**: This is the core simplification. Without one authoritative fabric pool collection, operators still need to maintain separate relationships for loopback, VTEP, uplink, DCI, and management pools.

**Independent Test**: Can be tested by loading a fabric that references one pool collection containing role-tagged pools and confirming that every required fabric pool purpose can be resolved from the collection without using legacy type-specific relationships.

**Acceptance Scenarios**:

1. **Given** a fabric has management, overlay routing, underlay routing, and DCI requirements, **When** its pool collection contains pools backed by prefixes with the required roles, **Then** the fabric has all required pools represented through the single collection.
2. **Given** a fabric has no underlay routing protocol, **When** the fabric pool collection is evaluated, **Then** a Fabric Point-to-Point pool is not required for that fabric.
3. **Given** existing prefixes use Pod Leaf Spine or Pod Super Spine Spine roles, **When** the schema migration is applied, **Then** those roles are represented by the single Fabric Point-to-Point role.
4. **Given** existing fabrics still have legacy type-specific pool relationships before data migration, **When** the schema change is loaded through a compatible migration path, **Then** existing fabric objects remain valid.

---

### User Story 2 - Model Pod Pools With Fabric Containment Rules (Priority: P2)

As a fabric designer, I want pod-level pools to use the same role model as fabrics so that pod loopback, VTEP, and uplink pools are explicitly tied to the containing fabric pools while management addressing remains shared at the fabric level.

**Why this priority**: Pod pool boundaries need to be clear before generators can allocate pool resources consistently across multi-pod fabrics.

**Independent Test**: Can be tested by loading a fabric with pod pool collections and confirming that pod Loopback, Loopback VTEP, and Fabric Point-to-Point pools are modeled as subnet-scoped descendants of the matching fabric-level pools, while management resolves only from the fabric management pool.

**Acceptance Scenarios**:

1. **Given** a pod defines Loopback, Loopback VTEP, or Fabric Point-to-Point pools, **When** the pod is evaluated against its parent fabric, **Then** each pod pool must be a subnet of the matching fabric pool role.
2. **Given** a pod needs management addressing, **When** management pool resolution occurs, **Then** the pod uses the parent fabric Management pool and does not require a separate pod management pool.
3. **Given** a fabric uses overlay routing, **When** a pod defines pod-level Loopback or Loopback VTEP pools, **Then** those pools must match the corresponding role and be contained within the fabric's corresponding role pool.
4. **Given** a fabric uses underlay routing, **When** a pod defines a Fabric Point-to-Point pool, **Then** that pool must match the Fabric Point-to-Point role and be contained within the fabric's Fabric Point-to-Point pool.

---

### User Story 3 - Represent MLAG Pool Requirements and Defaults (Priority: P3)

As a fabric designer, I want MLAG peer and MLAG L3 peering pools represented with explicit roles and default behavior so that L2 fabrics and MLAG-enabled pods can be generated without each rack requiring unique manually supplied pools.

**Why this priority**: MLAG pool behavior is conditional and intentionally allows shared /31 addressing, so it needs a distinct contract from the fabric-wide pools.

**Independent Test**: Can be tested by loading pods with and without explicit MLAG pools and confirming that required MLAG roles, default values, and /31 reuse semantics are unambiguous.

**Acceptance Scenarios**:

1. **Given** a fabric has no underlay routing protocol, **When** a pod is evaluated, **Then** the pod requires an MLAG Peer pool role.
2. **Given** any rack in a pod has MLAG enabled, **When** the pod is evaluated, **Then** the pod requires an MLAG Peer pool role.
3. **Given** a pod requires an MLAG Peer pool and the parent fabric has an underlay routing protocol, **When** the pod is evaluated, **Then** the pod also requires an MLAG L3 Peering pool role.
4. **Given** a pod does not define required MLAG pools, **When** default MLAG pool behavior is applied in generator work, **Then** default persisted pool objects are created with MLAG-Peer-Subnet `169.254.0.0/31` and MLAG-L3-Peering-Subnet `192.0.0.0/31`.

---

### User Story 4 - Preserve Existing Data Through a Compatible Migration (Priority: P4)

As an operator with existing fabrics, I want current pool assignments to remain valid during migration so that the schema can move to role-driven pool collections without breaking deployed examples or loaded branches.

**Why this priority**: The repository already stores fabrics using type-specific pool relationships and legacy prefix roles. A schema-only change that invalidates existing objects would block adoption.

**Independent Test**: Can be tested by loading current seed data, applying the schema migration path, and confirming that existing fabrics, pods, pools, and prefixes remain valid and can be mapped to the new pool collection contract.

**Acceptance Scenarios**:

1. **Given** a fabric currently uses `mgmt_pool`, `uplink_pool`, `vtep_pool`, `loopback_pool`, or `dci_pool`, **When** migration is complete, **Then** those assignments are represented in the fabric pool collection by role.
2. **Given** a pod currently uses `mlag_peer_pool` or `mlag_l3_pool`, **When** migration is complete, **Then** those assignments are represented in the pod pool collection by role.
3. **Given** existing prefixes use `technical` for DCI or MLAG pool resources, **When** migration is complete, **Then** DCI and MLAG resources use explicit DCI, MLAG, or MLAG Peering roles.

---

### Edge Cases

- A fabric has overlay routing configured but only one of the Loopback or Loopback VTEP roles is present.
- A fabric has underlay routing set to `none`, so Fabric Point-to-Point is not required even if legacy data still has an uplink pool.
- A fabric has a DCI-role connection for a device in the fabric but lacks a DCI pool and lacks a Fabric Supernet pool.
- A fabric has a Fabric Supernet pool but it cannot provide enough space for all missing required pools.
- A pool collection contains two pools that both resolve to the same role for the same fabric or pod.
- A pool resource contains prefixes with mixed roles, making the pool purpose ambiguous.
- A pod defines a Loopback, Loopback VTEP, or Fabric Point-to-Point pool that is not a subnet of the corresponding fabric pool.
- A pod omits MLAG pools while an MLAG Peer pool is required.
- A pod-level MLAG pool is a /31 and is intentionally reused across all racks in the pod.
- Existing prefixes still use Pod Leaf Spine, Pod Super Spine Spine, Supernet, or Technical roles during migration.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST extend the existing `NetworkFabric` and `NetworkPod` data model rather than creating replacement fabric or pod nodes.
- **FR-002**: Schema MUST preserve the existing `NetworkFabric` -> `NetworkPod` -> `LocationRack` hierarchy.
- **FR-003**: Schema MUST use an IP-pool relationship target that can represent both IP prefix pools and IP address pools in one pool collection.
- **FR-004**: Schema MUST NOT introduce new mandatory attributes on existing fabric, pod, pool, or prefix nodes without a compatibility path for existing loaded data.
- **FR-005**: Schema MUST keep existing human-friendly identifiers for fabric, pod, rack, pool, and prefix objects stable.

#### Attributes

- **FR-010**: `IpamPrefix.role` MUST include explicit role choices for Fabric Supernet, Loopback, Loopback VTEP, Fabric Point-to-Point, DCI, Management, MLAG, and MLAG Peering.
- **FR-011**: The Fabric Point-to-Point role MUST replace both current Pod Leaf Spine and Pod Super Spine Spine semantics.
- **FR-012**: The Fabric Supernet role MUST be available to identify a pool that can supply missing required fabric pools.
- **FR-013**: The DCI role MUST identify prefixes used for DCI point-to-point allocation and MUST no longer rely on the generic Technical role for DCI intent.
- **FR-014**: The MLAG and MLAG Peering roles MUST identify prefixes used by MLAG Peer and MLAG L3 Peering pools and MUST no longer rely on the generic Technical role for MLAG intent.
- **FR-015**: Existing non-fabric-specific roles such as Backfill MAY remain available, but they MUST NOT satisfy fabric or pod pool requirements.
- **FR-016**: Role choices that are superseded by this feature MUST have a migration path before they are removed or made unavailable for new pool assignments.

#### Relationships

- **FR-020**: `NetworkFabric` MUST expose a single authoritative fabric-level pool collection relationship for fabric IP pools.
- **FR-021**: The fabric-level pool collection MUST be an Attribute relationship with many-cardinality semantics.
- **FR-022**: The fabric-level pool collection MUST be able to include Management, Loopback, Loopback VTEP, Fabric Point-to-Point, DCI, and Fabric Supernet pools.
- **FR-023**: `NetworkPod` MUST expose a single authoritative pod-level pool collection relationship for pod IP pools.
- **FR-024**: The pod-level pool collection MUST be able to include Loopback, Loopback VTEP, Fabric Point-to-Point, MLAG, and MLAG Peering pools.
- **FR-025**: Management IP pools MUST be resolved from the parent fabric pool collection and MUST NOT require a separate pod management pool assignment.
- **FR-026**: Legacy fabric relationships `mgmt_pool`, `uplink_pool`, `vtep_pool`, `loopback_pool`, and `dci_pool` MUST stop being authoritative after migration to the pool collection model.
- **FR-027**: Legacy pod relationships `mlag_peer_pool` and `mlag_l3_pool` MUST stop being authoritative after migration to the pod pool collection model.
- **FR-028**: A fabric or pod MUST NOT have more than one authoritative pool satisfying the same role in the same scope.
- **FR-029**: A pool MUST satisfy exactly one fabric or pod pool role based on its backing prefix resources; pools with mixed-purpose backing prefixes MUST be treated as invalid for role-based resolution.

#### Required Pool Semantics

- **FR-030**: A fabric MUST have a Management pool available in the fabric pool collection for every fabric.
- **FR-031**: A fabric MUST have Loopback and Loopback VTEP pools available when an overlay routing protocol is defined for the fabric.
- **FR-032**: A fabric MUST have a Fabric Point-to-Point pool available when an underlay routing protocol is defined for the fabric.
- **FR-033**: A fabric MUST have a DCI pool available when any DCI-role connection exists for a device in that fabric.
- **FR-034**: If any required fabric pool is missing, the fabric MUST have a Fabric Supernet pool available in the fabric pool collection.
- **FR-035**: A Fabric Supernet pool MUST be represented as a fabric-level pool role and MUST be distinct from Management, Loopback, Loopback VTEP, Fabric Point-to-Point, and DCI roles.
- **FR-036**: A pod-defined Loopback, Loopback VTEP, or Fabric Point-to-Point pool MUST be a subnet of the parent fabric pool with the same role.
- **FR-037**: A pod MUST require an MLAG Peer pool when the parent fabric has no underlay routing protocol or when any rack in the pod has MLAG enabled.
- **FR-038**: A pod MUST require an MLAG L3 Peering pool when an underlay routing protocol is defined and the pod requires an MLAG Peer pool because MLAG is configured in the pod.
- **FR-039**: Rack-level MLAG Peer and MLAG L3 Peering allocations MUST be /31 networks and MAY be reused across racks and fabrics.

#### MLAG Defaults

- **FR-040**: If a required pod-level MLAG Peer pool is not provided, the implementation MUST create an idempotent persisted default pool object named MLAG-Peer-Subnet using `169.254.0.0/31`.
- **FR-041**: If a required pod-level MLAG L3 Peering pool is not provided, the implementation MUST create an idempotent persisted default pool object named MLAG-L3-Peering-Subnet using `192.0.0.0/31`.
- **FR-042**: If a pod-level MLAG pool is a /31, that /31 MUST be treated as intentionally reusable by every rack in the pod.
- **FR-043**: If a pod-level MLAG pool is larger than /31, rack-level /31 MLAG allocations MUST be contained by that pod-level pool.
- **FR-044**: Persisted default MLAG pool objects MUST use stable natural keys or repository-supported upsert behavior so repeated generator runs do not create duplicate pools.

#### Display & Identification

- **FR-050**: The fabric pool collection MUST have an operator-readable label that communicates it contains all fabric IP pools.
- **FR-051**: The pod pool collection MUST have an operator-readable label that communicates it contains pod-specific IP pools.
- **FR-052**: Pool and prefix display labels MUST allow an operator to identify the pool name, backing prefix, and role without using internal IDs.
- **FR-053**: Any new relationship names MUST be snake_case and at least three characters long.
- **FR-054**: Any new relationship peers MUST use full Infrahub kind names.

#### Uniqueness Constraints

- **FR-060**: The implementation MUST actively prevent duplicate authoritative pools for the same role within a single fabric through schema constraints, proposed-change validation, generator validation, or another repository-supported enforcement path.
- **FR-061**: The implementation MUST actively prevent duplicate authoritative pools for the same role within a single pod through schema constraints, proposed-change validation, generator validation, or another repository-supported enforcement path.
- **FR-062**: Existing pool names and prefix identifiers MUST remain unique according to their current model.

#### Migration

- **FR-070**: Existing Fabric Supernet data using the current Supernet role MUST have a migration path to the Fabric Supernet role.
- **FR-071**: Existing Pod Leaf Spine and Pod Super Spine Spine prefixes MUST have a migration path to the Fabric Point-to-Point role.
- **FR-072**: Existing DCI pool resources using the Technical role MUST have a migration path to the DCI role.
- **FR-073**: Existing MLAG pool resources using the Technical role MUST have a migration path to MLAG or MLAG Peering roles.
- **FR-074**: Legacy type-specific pool relationships MUST remain load-compatible until data migration has populated the new pool collection relationships.
- **FR-075**: Removed legacy relationships MUST use the repository's approved schema migration pattern instead of being deleted abruptly.

### Key Entities

- **NetworkFabric**: The fabric that owns the authoritative fabric pool collection and determines which pool roles are required from routing and DCI intent.
- **NetworkPod**: A pod under a fabric that may define pod-scoped pool collections and MLAG pool requirements.
- **LocationRack**: A rack under a pod whose MLAG setting can make pod-level MLAG pools required.
- **IpamPrefix**: The prefix resource whose role identifies the purpose of the pool that consumes it.
- **CoreResourcePool**: The concrete shared relationship peer used for fabric and pod pool collections; validation must restrict collection members to IP pool kinds.
- **CoreIPPrefixPool**: A pool used for prefix allocation, including Fabric Supernet, Fabric Point-to-Point, DCI, Loopback, and Loopback VTEP pool purposes.
- **CoreIPAddressPool**: A pool used for address allocation, including Management, MLAG, and MLAG Peering pool purposes.
- **NetworkLink**: A connection whose DCI role can make a fabric DCI pool required.

### Pool Role Matrix

| Role Label | Required Scope | Required When | Pool Kind |
|------------|----------------|---------------|-----------|
| Management | Fabric | Always | IP address pool |
| Loopback | Fabric and optional pod subnet | Overlay routing protocol is defined | IP prefix pool |
| Loopback VTEP | Fabric and optional pod subnet | Overlay routing protocol is defined | IP prefix pool |
| Fabric Point-to-Point | Fabric and optional pod subnet | Underlay routing protocol is defined | IP prefix pool |
| DCI | Fabric | Any DCI-role connection exists for a device in the fabric | IP prefix pool |
| Fabric Supernet | Fabric | Any required fabric pool is missing | IP prefix pool |
| MLAG | Pod | Fabric has no underlay routing protocol or any rack in the pod has MLAG enabled | IP address pool |
| MLAG Peering | Pod | Underlay routing protocol is defined and MLAG is configured in the pod | IP address pool |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `infrahubctl schema check schemas/` passes with zero validation errors after the schema change is implemented.
- **SC-002**: 100% of required pool purposes in the Pool Role Matrix can be represented through the fabric or pod pool collection model.
- **SC-003**: 100% of current fabric pool assignments in seed data have a defined migration target in the new fabric pool collection.
- **SC-004**: 100% of current pod MLAG pool assignments in seed data have a defined migration target in the new pod pool collection.
- **SC-005**: The current Pod Leaf Spine and Pod Super Spine Spine prefix-role semantics are represented by exactly one Fabric Point-to-Point role.
- **SC-006**: A fabric with management, overlay, underlay, and DCI requirements can be evaluated for missing pools using only the fabric pool collection and prefix roles.
- **SC-007**: A pod with Loopback, Loopback VTEP, and Fabric Point-to-Point pools can be evaluated so that 100% of those pod pools are confirmed as subnets of matching fabric pools.
- **SC-008**: A pod requiring MLAG pools but defining none has deterministic default intents for both required MLAG roles.
- **SC-009**: Existing loaded fabric and pod objects remain schema-valid throughout the planned migration sequence.

## Assumptions

- "Overlay routing protocol is defined" means the fabric has a non-empty overlay routing protocol value.
- "Underlay routing protocol is defined" means the fabric has a non-empty underlay routing protocol value other than `none`.
- A DCI pool is required for each fabric that contains a device participating in at least one `NetworkLink` with role `dci`.
- A pod-level /31 MLAG pool is intentionally reusable by all racks in that pod.
- Pool object names are operator-facing labels, not the source of pool purpose; backing prefix roles are the source of truth for pool purpose.
- This specification covers the schema contract plus the immediate enforcement needed to protect users. Generator allocation from Fabric Supernet, role-based validation checks, object migrations, generated query updates, and documentation updates are part of this feature unless a requirement is explicitly split into a separately tracked follow-up before implementation begins.

### Fabric Supernet Allocation Contract

When a required fabric prefix-pool role is missing and a Fabric Supernet pool is available, generators MUST allocate deterministic child prefixes from the Fabric Supernet pool before failing validation. Allocation MUST be stable across repeated runs, MUST avoid overlap with existing child prefixes, and MUST fail with a clear validation error when no suitable space remains.

Default child prefix sizes are:

- Loopback: /27
- Loopback VTEP: /27
- Fabric Point-to-Point: /24
- DCI: /24

Allocation order MUST be deterministic: Loopback, Loopback VTEP, Fabric Point-to-Point, then DCI. For each missing role, the allocator MUST select the first available child prefix of the required size in ascending prefix order, skipping existing children and any overlapping prefix already assigned in the fabric. If no suitable child prefix exists for a required role, validation MUST fail before generator output is persisted and the error MUST identify the fabric, missing role, requested prefix size, and Fabric Supernet pool.

Generated fallback pool names MUST be derived from the fabric name and role label, for example `<fabric>-Loopback-Pool`, and MUST use existing repository upsert or natural-key behavior.
