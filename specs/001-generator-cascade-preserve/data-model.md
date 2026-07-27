# Data Model: Generator Cascade Preservation

No new schema entities are planned. This feature defines reconciliation behavior and field ownership over existing Infrahub kinds.

## NetworkFabric

**Purpose**: The operator-selected root of a generation run.

**Existing fields used**:
- `name`: generator target parameter and human-readable identifier.
- `avd_hostvars_ready`: set `False` when upstream topology changes or reconciliation starts; set `True` after hostvars exist for every fabric device.
- Pool relationships: `asn_pool`, `node_id_pool`, `mgmt_pool`, `vtep_pool`, and existing addressing pools used by downstream generators.

**Relationships**:
- Parents `NetworkPod` children.
- Owns fabric-level AVD artifact targets through existing artifact relationships.

**Rules**:
- Running `generate-fabric` must identify all child pods for the selected fabric.
- The generator must not require deleting pre-existing child data before reconciliation.

## NetworkPod

**Purpose**: Downstream generator target for pod-level devices and rack trigger continuation.

**Existing fields used**:
- `name`: generator target parameter.
- `checksum`: trigger signal and idempotence marker.
- `role`: `fabric` pods are handled by the fabric generator and skipped by `PodGenerator`.
- `loopback_pool` and `prefix_pool`: filled by pod generation where absent.

**Relationships**:
- Parent is `NetworkFabric`.
- Has rack children through `LocationRack.pod`.
- Has generated spine devices through the existing device relationship.

**Rules**:
- If a pod checksum changes, the existing trigger rule may run `generate-pod`.
- If a pod checksum is already current, `generate-fabric` must still explicitly continue to `generate-pod` for that pod unless the pod role is excluded.
- Pod reconciliation must preserve non-empty existing pod fields unless they are intentionally generated-owned and missing.

## LocationRack

**Purpose**: Downstream generator target for rack devices, cabling, completion state, and hostvar kickoff.

**Existing fields used**:
- `name`: generator target parameter.
- `checksum`: trigger signal and idempotence marker.
- `generation_complete`: reset to `False` at rack run start and set to `True` after rack generation finishes.
- `amount_of_leafs`, `amount_of_l2leafs`, `mlag`, templates, and interface sorting methods: existing design inputs.

**Relationships**:
- Linked to a `NetworkPod`.
- Contains generated leaf and l2leaf devices.

**Rules**:
- If a rack checksum changes, the existing trigger rule may run `generate-rack`.
- If a rack checksum is already current, `generate-pod` must still explicitly continue to `generate-rack`.
- Rack completion remains the gate that allows hostvars to run for the fabric.

## DcimDevice

**Purpose**: A network device that may be fully generated or pre-seeded by an operator before the cascade runs.

**Existing fields used**:
- Operator-provided or externally managed: `serial`, `description`, `os_version`, existing non-empty `mgmt_ip`.
- Generator-owned when missing: `status`, `role`, `index`, `object_template`, `pod`, `rack`, `member_of_groups` including `avd_devices`, `node_id`, `loopback_ip`, `vtep_loopback_ip`, `asn`.

**Relationships**:
- Belongs to a `NetworkPod`, optionally a `LocationRack`, and the `avd_devices` group.
- Links to `IpamIPAddress` nodes for management, loopback, and VTEP addressing.
- Links to `RoutingAsn` for BGP ASN.
- Has generated `InterfaceVirtual` loopback interfaces.

**Validation rules**:
- A non-empty existing `serial` must not be changed by standard generation.
- A non-empty existing `mgmt_ip` must not be replaced by standard generation.
- Missing generator-owned values must be populated when the source intent exists.
- AVD group membership must be additive and must not remove unrelated group memberships.
- Re-running reconciliation must not create duplicate devices, duplicate ASNs, duplicate loopback interfaces, duplicate IP addresses, or duplicate artifacts.

## AvdArtifact and File Nodes

**Purpose**: Store per-device generated hostvars and structured configs.

**Existing fields used**:
- `AvdArtifact.name`: device hostname anchor.
- `hostvar_file`: child `AvdHostvarFile`.
- `structured_config_file`: child `AvdStructuredConfigFile`.
- Child file checksums from `CoreFileObject`.

**Rules**:
- If any fabric device is missing hostvars after rack generation, hostvar generation targets the whole fabric.
- If existing hostvars are present for all fabric devices, targeted rack regeneration may invalidate and refresh only affected devices.
- Structured config remains triggered by `NetworkFabric.avd_hostvars_ready` changing from `False` to `True`.

## Generation Run

**Purpose**: Existing operational action, not a new stored entity.

**States**:
- `started`: operator invokes `generate-fabric` for a target fabric.
- `fabric reconciled`: fabric-owned pools/devices are present and child pod continuation has been scheduled.
- `pods reconciled`: pod-owned pools/devices are present and child rack continuation has been scheduled.
- `racks reconciled`: rack devices/cabling are present and all relevant racks report `generation_complete=True`.
- `hostvars ready`: all fabric devices have hostvar files and `avd_hostvars_ready=True`.
- `structured configs ready`: all fabric devices have structured config files.

**Failure behavior**:
- A generator failure must leave existing non-empty operator values intact.
- A repeated run after a partial failure must be able to continue from existing objects.
- Partial artifacts may be invalidated only for targeted devices before regeneration.
