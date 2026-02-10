# Feature Specification: Server Cabling Service

**Feature Branch**: `004-server-cabling-service`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "I have the concept of servers in the schema and we can cable these servers up to a leaf device with vlans on the interfaces. I want a service that we can specify a new server and it will go and cable the server up to a leaf in the same rack and add the required vlans on it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create Server and Cable to Leaf (Priority: P1)

As an infrastructure operator, when I create a new server in a rack using a server template, the system should automatically find leaf switches in the same rack and cable the server's interfaces to available leaf interfaces. The server template defines the number of interfaces (1 for single-homed, 2 for dual-homed), and the generator distributes connections across available leaf switches. Interface profiles on the server interfaces define which VLANs should be applied to the corresponding leaf-side ports.

**Why this priority**: This is the core automation. Without it, operators must manually create links and assign VLANs for every server, which is error-prone and time-consuming.

**Independent Test**: Can be fully tested by creating a server from a template in a rack with leaf switches, then verifying that network links are created and VLANs from the server interface profiles are assigned to the leaf-side interfaces.

**Acceptance Scenarios**:

1. **Given** a rack with leaf switches that have available server-role interfaces, **When** a single-homed server (1 interface) is created from a template, **Then** the system creates one network link between the server interface and a leaf interface.
2. **Given** a rack with two leaf switches, **When** a dual-homed server (2 interfaces) is created from a template, **Then** the system creates two network links distributing one interface to each leaf switch.
3. **Given** a server interface with a profile that specifies tagged VLANs, **When** the server is cabled, **Then** those VLANs are assigned as tagged VLANs on the corresponding leaf-side interface.
4. **Given** a server with interfaces, **When** the cabling is complete, **Then** both server and leaf interfaces are set to "active" status and the link has a descriptive name and medium.

---

### User Story 2 - Server Templates and Interface Profiles (Priority: P1)

The system provides pre-defined server templates (object templates) for common server types. Each template specifies the server's role, number of interfaces, and interface profiles. Interface profiles define VLANs and MTU settings, so operators only need to select a template when provisioning a server.

**Why this priority**: Templates and profiles are the input mechanism for the generator. Without them, there is no way to define what VLANs a server needs.

**Independent Test**: Can be tested by loading the server templates and profiles into the system and verifying they can be used to create server instances with the correct interfaces and VLAN assignments.

**Acceptance Scenarios**:

1. **Given** a compute server template with 2 interfaces and a compute VLAN profile, **When** a server is created from this template, **Then** it has 2 interfaces with the correct profile (role, MTU, VLANs) applied.
2. **Given** a GPU server template with 1 interface and a GPU VLAN profile, **When** a server is created from this template, **Then** it has 1 interface with the appropriate VLANs.
3. **Given** a server interface profile that includes tagged VLANs for Servers and Storage, **When** the profile is applied to an interface, **Then** the interface has those VLANs configured.

---

### User Story 3 - Leaf Interface Availability Validation (Priority: P2)

The service must verify that the target leaf switches have enough available (unlinked) server-role interfaces before attempting to cable a server. If insufficient interfaces are available, the service should report a clear warning rather than partially provisioning.

**Why this priority**: Without availability checking, the service could fail mid-provisioning, leaving the data model in an inconsistent state.

**Independent Test**: Can be tested by attempting to provision a server in a rack where all leaf interfaces are already in use, and verifying an appropriate warning is logged.

**Acceptance Scenarios**:

1. **Given** a leaf switch with no available server-role interfaces, **When** a server provisioning is attempted, **Then** the service logs a clear warning and skips cabling for that server.
2. **Given** a rack with two leaf switches where only one has available interfaces, **When** a dual-homed server is requested, **Then** the service warns about insufficient interfaces for full dual-homing.

---

### User Story 4 - Idempotent Re-runs (Priority: P2)

The service should be idempotent. Running it again for a server that is already cabled should not create duplicate links or reassign VLANs. This allows safe re-execution when the generator is triggered by data changes.

**Why this priority**: Generators in this system are triggered by data changes and may re-run. Idempotency prevents data corruption.

**Independent Test**: Can be tested by running the service twice for the same server and verifying no duplicate links or VLAN assignments are created.

**Acceptance Scenarios**:

1. **Given** a server that is already fully cabled and has VLANs assigned, **When** the generator runs again, **Then** no new links are created and existing VLAN assignments remain unchanged.

---

### Edge Cases

- What happens when a rack has no leaf switches at all? The generator should log a warning and skip provisioning.
- What happens when a server has zero interfaces? The generator should log a warning and skip cabling.
- How does the system handle a server that is already partially cabled (some interfaces linked, some not)? The generator should cable only the unlinked interfaces.
- What happens if VLANs referenced in a profile do not exist in the system? The generator should log a warning for missing VLANs and continue with VLANs that do exist.
- What happens when a rack has only one leaf but a dual-homed server is requested? The generator should connect both interfaces to the single leaf and log a notice.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST be implemented as a generator triggered automatically when a PhysicalServer is created or changed, following the existing generator pattern (target group, checksum-based change detection).
- **FR-002**: The service MUST find all leaf switches in the same rack as the target server by querying devices in the rack with the "leaf" role.
- **FR-003**: The service MUST identify available (unlinked) server-role or storage-role interfaces on the leaf switches for cabling.
- **FR-004**: The service MUST create a network link between each server interface and a leaf interface, assigning a descriptive link name and appropriate medium.
- **FR-005**: The service MUST read VLANs from the server interface profiles and assign them as tagged VLANs on the corresponding leaf-side interfaces.
- **FR-006**: The service MUST support both single-homed (1 interface to 1 leaf) and dual-homed (2 interfaces to 2 different leaves) server configurations, determined by the number of interfaces on the server.
- **FR-007**: The service MUST distribute server interfaces across available leaf switches when more than one leaf exists in the rack (round-robin across leaves).
- **FR-008**: The service MUST be idempotent - re-running for an already-cabled server creates no duplicates.
- **FR-009**: The service MUST validate that sufficient leaf interfaces are available before beginning provisioning, and skip the server with a warning if not.
- **FR-010**: The service MUST set interface status to "active" on both the server and leaf interfaces after cabling.
- **FR-011**: Server templates (object templates) MUST be provided for common server types (compute single-homed, compute dual-homed, GPU single-homed).
- **FR-012**: Interface profiles MUST be provided for server interfaces that define role, MTU, and allowed VLANs.

### Key Entities

- **PhysicalServer**: A compute node in a rack with network interfaces. Has a role (compute/gpu), status, and rack assignment. Created from object templates.
- **NetworkInterface**: A port on a device. Has a role (server/storage for leaf-side ports), status, and VLAN assignments (tagged/untagged). Configuration comes from profiles.
- **NetworkLink**: A bidirectional cable between two interfaces. Has a name and medium (copper/fibre).
- **LocationRack**: Contains both leaf switches and servers. Has an index and rack type (compute/storage).
- **VLAN**: Network segmentation. Assigned to interfaces as tagged or untagged.
- **Object Template**: Pre-defined server configurations (interface count, interface profiles) for rapid provisioning.
- **Interface Profile**: Defines role, MTU, and VLAN assignments for server interfaces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every server provisioned in a rack with available leaf interfaces is fully cabled within a single generator execution with zero manual intervention.
- **SC-002**: 100% of server-to-leaf connections include proper VLAN assignments on the leaf-side interfaces matching the server interface profiles.
- **SC-003**: The generator can be re-run any number of times for the same server without creating duplicate links or VLAN assignments.
- **SC-004**: When a rack has no available leaf interfaces, the operator receives a clear, actionable warning message within the generator logs.
- **SC-005**: Server interfaces are distributed across leaf switches in the rack (one per leaf for dual-homed, any available for single-homed).
- **SC-006**: At least 3 server templates are available covering common deployment patterns (compute single-homed, compute dual-homed, GPU).

## Assumptions

- Leaf switches are already provisioned in the rack before servers are added (via the existing RackGenerator).
- Server instances are created from object templates that define the number and type of interfaces.
- VLANs to assign are defined on server interface profiles (tagged_vlan/untagged_vlan relationships on the profile).
- Leaf switches have pre-configured interface profiles that designate which ports are for server connections (role: "server" or "storage").
- The link medium for server-to-leaf connections is "copper" by default.
- Each server interface maps to exactly one leaf interface (1:1 cabling, no LAG/port-channel abstraction at this stage).
- PhysicalServer will need to inherit from GeneratorTarget to support the generator pattern with checksum-based change detection.
- Server interface profiles need to be extended to include VLAN relationships (tagged_vlan, untagged_vlan).
