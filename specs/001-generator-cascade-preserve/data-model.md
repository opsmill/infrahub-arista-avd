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

## InterfacePhysical / DcimInterface

**Purpose**: Existing device interfaces that carry generated uplinks, MLAG peer links, L2 leaf uplinks, server-facing links, and loopback/virtual interface relationships used by AVD hostvars.

**Existing fields used**:
- `name`: interface identifier and part of the `DcimInterface` human-friendly ID.
- `device`: owning device and part of the `DcimInterface` human-friendly ID.
- `role`: generator-owned role when missing or when a specific generated role is required for a generated interface.
- `status`: generated active state for interfaces attached by the topology generator when missing.
- `connector`: relationship to `NetworkLink`.
- `ip_address`: single generated IP relationship used by current interface extension behavior.
- `ip_addresses`: many-address Layer 3 relationship inherited from the base interface generic.

**Relationships**:
- Belongs to one `DcimDevice`.
- May connect to a `NetworkLink` through `DcimEndpoint.connector`.
- May reference one or more `IpamIPAddress` nodes.

**Rules**:
- Existing non-empty connector relationships must not be replaced by standard generation.
- If an expected generated interface has no connector, generation may attach it to the expected generated `NetworkLink`.
- Existing non-empty IP relationships must not be replaced by standard generation.
- If an expected generated interface lacks required IP data, generation may populate the missing generated IP relationship.
- Connectivity decisions must be visible in logs or another completed-run artifact as populated, preserved, or skipped.

## NetworkLink

**Purpose**: Existing connector node that links generated physical endpoints.

**Existing fields used**:
- `name`: deterministic generated connection identifier derived from endpoint device/interface names.
- `medium`: generated medium, currently `copper` for the existing cabling helper.
- Optional role/include fields inherited by schema extensions where present.

**Relationships**:
- Connected endpoints are the physical interfaces that reference the link through `connector`.

**Rules**:
- Generation must use deterministic names and `allow_upsert=True` so re-runs reuse the same expected link.
- If the expected link exists and one endpoint is missing a connector, generation may attach the missing endpoint.
- If an endpoint already references a different non-empty connector, generation must preserve that connector and report the skipped conflict.
- Re-running generation must not create duplicate links for the same expected endpoint pair.

## IpamIPAddress for Generated Connectivity

**Purpose**: Existing IPAM address nodes allocated for loopbacks, VTEPs, management addresses, and point-to-point routed uplinks.

**Existing fields used**:
- `address`: allocated host address with prefix length.
- IP namespace and pool-derived allocation metadata from existing Infrahub pool primitives.

**Relationships**:
- May be linked from `DcimDevice.mgmt_ip`, `DcimDevice.loopback_ip`, `DcimDevice.vtep_loopback_ip`, or interface IP relationships.

**Rules**:
- Existing non-empty device or interface IP relationships are authoritative in standard generation.
- Missing generated-owned IP relationships may be allocated or attached when the required source pool and topology intent exist.
- Generated point-to-point allocations must be idempotent by stable identifiers derived from the endpoint pair.
- Conflicting non-empty IP values must be preserved and reported as skipped conflicts.

## Uplink Connection

**Purpose**: A derived relationship set, not a new stored kind, representing the expected generated connectivity between two fabric devices.

**Fields derived from source intent**:
- Source device and source interface.
- Destination device and destination interface.
- Expected `NetworkLink` name.
- Optional point-to-point prefix/IP assignments.

**Rules**:
- Missing links, connector relationships, interface attributes, and IP relationships must be populated when source intent is complete.
- Non-empty conflicts must be preserved rather than overwritten.
- Hostvar generation must see a complete enough graph to derive `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` for every expected device.

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
