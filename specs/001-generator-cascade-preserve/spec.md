# Schema Design Specification: Generator Cascade Preservation

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate any schema definitions if planning determines schema changes are required.

**Feature Branch**: `emdash/pre-seed-devices-b7sa2`
**Created**: 2026-07-27
**Status**: Draft
**Input**: User description: "Running generate-fabric on an already deployed Fabric, or on a Fabric that contains DcimDevice objects with already populated attributes such as serial or mgmt_ip, currently prevents the generator cascade from continuing through generate-pod, generate-rack, and hostvars generation. The cascade must still occur so fabric, pod, rack, device, and pyAVD hostvars data is fully populated. Existing populated fields must not be overwritten by default. If possible, provide an explicit override option."

## Clarifications

### Session 2026-07-27

- Q: How should standard generate-fabric handle existing conflicting connection, interface, or IP values while populating missing uplinks and related attributes? → A: Preserve existing non-empty conflicting values; populate only missing values and expose skipped conflicts.

## Schema Files

No new schema files are expected as the default outcome for this feature. The required business behavior is that existing fabric, pod, rack, device, and hostvars records can coexist with operator-provided device attributes and still be reconciled by the generator cascade.

If planning proves that the current schema contract blocks this behavior, any schema change must preserve existing data compatibility: new attributes on existing nodes must not make already-loaded fabrics or devices invalid, and any relationship changes must keep existing fabric-to-pod-to-rack-to-device navigation intact.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reconcile a Pre-Existing Fabric (Priority: P1)

As a fabric operator, I want to run generate-fabric on an already deployed fabric so that the full downstream generator cascade completes and every expected fabric, pod, rack, device, and hostvars record is brought to the required populated state.

**Why this priority**: This is the reported failure mode. Without it, a fabric containing partially populated devices cannot be reconciled into a usable pyAVD hostvars state.

**Independent Test**: Can be tested by reproducing a fabric where racks report updated checksums while downstream devices remain partial, then running the fabric generation workflow and verifying that all expected downstream objects and hostvars data are populated.

**Acceptance Scenarios**:

1. **Given** an already deployed fabric with existing racks and partially populated devices, **When** the operator runs generate-fabric for that fabric, **Then** the pod, rack, and hostvars generation steps all complete for the target fabric.
2. **Given** a fabric where rack generation reports updated checksums, **When** generate-fabric completes, **Then** no expected device remains in a partial state solely because it had a pre-existing attribute value.
3. **Given** a target fabric contains pre-existing devices with missing generated uplinks, connection relationships, interfaces, or IP attributes, **When** generate-fabric completes, **Then** all missing generated-owned connectivity data is populated when the required source intent exists.

---

### User Story 2 - Preserve Operator-Provided Device Values (Priority: P2)

As a fabric operator, I want pre-seeded device values such as serial and mgmt_ip to be preserved so that generator reconciliation fills missing data without destroying values I already supplied.

**Why this priority**: Operators often pre-populate inventory or management details before running generation. Losing those values would make reconciliation unsafe.

**Independent Test**: Can be tested by setting known values on a device before generation, running the cascade, and confirming that missing generated fields are populated while the known pre-existing values remain unchanged.

**Acceptance Scenarios**:

1. **Given** a device has serial and mgmt_ip populated before generation, **When** generate-fabric runs without override, **Then** those values are unchanged after the cascade completes.
2. **Given** a device has some required generated attributes missing, **When** generate-fabric runs without override, **Then** the missing generated attributes are populated while already-present attributes are preserved.
3. **Given** a device has non-empty connection, interface, or IP values that conflict with generated topology intent, **When** generate-fabric runs without override, **Then** those conflicting values are unchanged and are visible as skipped conflicts in the completed run outcome.

---

### User Story 3 - Preserve the External Contract Boundary (Priority: P3)

As a fabric operator, I want standard generation to have no hidden override mode so that pre-existing values are preserved unless a future explicit override contract is designed and accepted.

**Why this priority**: Preservation must be the safe default, and the current generator-run contract has no operator-visible runtime option for overwrite behavior.

**Independent Test**: Can be tested by verifying that no generator runtime input, service portal control, environment variable, or branch-name convention enables overwrite behavior.

**Acceptance Scenarios**:

1. **Given** a standard generate-fabric run, **When** the operator starts generation, **Then** preservation mode is the only externally available behavior.
2. **Given** a future override need, **When** the current slice is implemented, **Then** no hidden runtime switch or undocumented API path enables overwrite behavior.

---

### Edge Cases

- A device has a mix of populated values, missing values, and empty values before generation.
- A fabric has multiple pods or racks and only some racks contain pre-populated devices.
- A device has serial or mgmt_ip populated before generation while other generated-required device fields are absent.
- A downstream generator stage has no object changes but must still continue so later stages can reconcile missing data.
- Re-running the cascade after a successful reconciliation should not create duplicate objects or relationships.
- A stale generated-owned value exists, but the current external contract has no explicit override mode.
- The target fabric contains devices whose existing relationships to pods, racks, interfaces, or hostvars artifacts are incomplete.
- The target fabric contains devices with missing uplinks, missing connection relationships, or missing interface and IP attributes required by the generated topology.
- Existing non-empty connection, interface, or IP values conflict with generated topology intent during a standard generate-fabric run.

## Requirements *(mandatory)*

### Functional Requirements

#### Existing Nodes & Generics

- **FR-001**: The system MUST support reconciliation of the existing fabric hierarchy from NetworkFabric through NetworkPod, LocationRack, DcimDevice, and hostvars-related records without requiring operators to remove pre-existing device attributes.
- **FR-002**: The system MUST NOT require a new node or generic for this behavior unless planning identifies a missing data concept that cannot be represented by the current model.
- **FR-003**: If schema changes are required, existing deployed fabrics and devices MUST remain valid after the change.

#### Attributes

- **FR-010**: The system MUST treat non-empty pre-existing device attributes as authoritative by default during generator reconciliation.
- **FR-011**: The system MUST populate missing attributes that the generator cascade is responsible for producing, even when other attributes on the same object are already populated.
- **FR-012**: The system MUST NOT overwrite pre-existing serial, mgmt_ip, or equivalent operator-provided values during a standard generate-fabric run.
- **FR-013**: Empty or absent values MUST be eligible for population by the generator cascade.
- **FR-014**: If any new required schema attribute is introduced on an existing node, the schema change MUST include a compatibility path so existing objects are not invalidated by missing values.

#### Relationships

- **FR-020**: Running generate-fabric for a target fabric MUST continue through the dependent pod, rack, and hostvars generation steps even when related devices already have populated attributes.
- **FR-021**: The cascade MUST reconcile all expected relationships among the target fabric, pods, racks, devices, and generated hostvars artifacts.
- **FR-022**: Repeated runs MUST NOT create duplicate devices, racks, artifacts, or relationships.
- **FR-023**: A downstream stage that detects no direct changes for its own objects MUST still allow later required cascade stages to run when those later stages have missing data to populate.
- **FR-024**: The cascade MUST populate all missing generated uplinks, connection relationships, device interfaces, interface attributes, and IP address attributes required by the target fabric topology when the required source intent exists.
- **FR-025**: If an expected uplink, connection, interface, or IP relationship already exists but is incomplete, the cascade MUST populate its missing generated-owned attributes without replacing non-empty existing values.
- **FR-026**: Existing non-empty connection, interface, or IP values that conflict with generated topology intent MUST be preserved during a standard generate-fabric run and reported as skipped conflicts in the completed run outcome.

#### Preservation and Override Behavior

- **FR-030**: Preservation mode MUST be the default behavior for generate-fabric and all dependent cascade stages.
- **FR-031**: The system MUST NOT expose an override mode in this slice.
- **FR-032**: The system MUST NOT introduce hidden overwrite behavior through runtime inputs, environment variables, branch naming, or service portal controls.
- **FR-033**: Any future override mode MUST require a separate explicit operator-visible contract and MUST only replace generator-owned fields.
- **FR-034**: The outcome of a generation run MUST expose preserved, populated, and skipped field decisions through generator logging or another completed-run artifact visible during validation.

#### Display & Identification

- **FR-040**: Existing human-readable identifiers for fabric, pod, rack, device, and hostvars-related records MUST remain stable unless an explicit schema migration is planned and accepted.
- **FR-041**: Operators MUST be able to identify which fabric and devices were reconciled after generation completes.

### Key Entities

- **NetworkFabric**: The fabric selected by the operator for generation and reconciliation.
- **NetworkPod**: A pod under the target fabric that must continue to be reconciled during the cascade.
- **LocationRack**: A rack under the target fabric or pod whose generated state and downstream device generation must continue even when rack-level checksums indicate no direct change.
- **DcimDevice**: A device that may already contain operator-provided values such as serial or mgmt_ip and must receive missing generated values without losing existing ones.
- **Hostvars Artifact**: The generated pyAVD hostvars data required for a complete device configuration workflow.
- **Generation Run**: A user-triggered or automated execution of generate-fabric and its dependent cascade stages for a target fabric.
- **Uplink Connection**: A generated physical or logical connectivity record between fabric devices, including required device interfaces and IP address attributes derived from fabric topology intent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the reproduced pre-seeded-device scenario, 100% of expected downstream pod, rack, device, hostvars, and structured-config generation outcomes are completed after one generate-fabric run.
- **SC-002**: In preservation mode, 100% of pre-existing non-empty serial and mgmt_ip values remain unchanged after the generator cascade completes.
- **SC-003**: 100% of missing generator-owned required attributes on target fabric devices are populated when the required source intent exists.
- **SC-004**: Re-running generation on an already reconciled fabric produces no duplicate objects or duplicate relationships.
- **SC-005**: Contract validation confirms that no external override input, hidden runtime switch, environment variable, or branch-name convention can enable overwrite behavior in this slice.
- **SC-006**: Operators can verify from the completed run outcome whether the cascade preserved, populated, or skipped values for the target fabric.
- **SC-007**: In a pre-seeded-device scenario with missing generated uplinks, connections, interfaces, and IP attributes, 100% of missing generated-owned connectivity data is populated after one generate-fabric run when the required source intent exists.
- **SC-008**: In a standard generate-fabric run with conflicting non-empty connection, interface, or IP values, 100% of those conflicting values remain unchanged and are visible as skipped conflicts in the completed run outcome.

## Assumptions

- Pre-existing non-empty values are considered operator-provided unless they are clearly owned by the generator cascade and a future explicit override contract is implemented.
- Preservation mode is the required default for both manual and triggered generation runs.
- The current data model is expected to be sufficient; schema work is only in scope if planning identifies a compatibility gap that blocks reconciliation.
- The known live reproduction on branch `gen-fab-c` is representative of the failure mode and should be used as validation evidence during later phases where appropriate.
- Future override behavior may only apply to fields that the generator cascade is responsible for deriving from fabric intent.

## Field Ownership Semantics

- **Always preserve when non-empty**: `serial`, existing `mgmt_ip`, and unrelated operator-managed relationships.
- **Populate when missing**: role, object template, pod, rack, index, AVD group membership, node ID, management IP, loopback IP, VTEP IP, and ASN.
- **Connectivity populate when missing**: generated uplinks, connection relationships, device interfaces, interface attributes, peer interface references, point-to-point IP addresses, and related IP attributes.
- **Connectivity conflicts**: existing non-empty connection, interface, or IP values must be preserved during standard generate-fabric runs and reported as skipped conflicts.
- **Additive relationships**: `avd_devices` group membership must be added without removing unrelated groups.
- **Future override scope**: only fields derived by the generator cascade from fabric intent may be considered for overwrite in a future explicit override contract.
