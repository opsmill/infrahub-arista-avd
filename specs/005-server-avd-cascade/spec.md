# Feature Specification: Server AVD Cascade

**Feature Branch**: `005-server-avd-cascade`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "when the generator to add the server runs we need some way to ensure that the hostvars are updated and structured config runs etc."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic AVD Update After Server Cabling (Priority: P1)

When a server is added to a rack and the server cabling generator runs, the leaf switch configurations must automatically update to reflect the new server-facing interfaces. This means the AVD hostvars for affected leaf switches must be regenerated, followed by structured config regeneration and backfill, without any manual intervention.

**Why this priority**: Without this, adding a server results in stale leaf switch configurations that don't include the new server-facing interfaces and VLANs. The entire value of automated server cabling is lost if the downstream config pipeline doesn't run.

**Independent Test**: Can be fully tested by running the server cabling generator for a server in a rack with existing leaf switches, then verifying that the leaf switch AVD hostvars, structured config, and backfilled data all reflect the new server links.

**Acceptance Scenarios**:

1. **Given** a rack with two leaf switches that have existing AVD configurations, **When** a new server is added and the server cabling generator runs, **Then** the hostvar generator re-runs for the affected leaf switches and their hostvars include the new server-facing interface configurations.
2. **Given** the hostvar generator has completed after server cabling, **When** the hostvars are ready, **Then** the structured config generator automatically runs and produces updated EOS configurations that include the new server-facing interfaces.
3. **Given** the structured config generator has completed, **When** the structured config checksum changes, **Then** the backfill generator automatically runs and updates the modeled data (IP addresses, routing, etc.) to reflect the new configuration.

---

### User Story 2 - Idempotent Re-Run Safety (Priority: P2)

When the server cabling generator triggers the AVD cascade, re-running the cascade on devices whose configuration has not changed must not produce duplicate data or errors. The system must be idempotent.

**Why this priority**: Without idempotency, triggering the cascade could corrupt existing configurations or create duplicate objects.

**Independent Test**: Can be tested by running the server cabling generator twice for the same server and verifying the leaf switch configurations are identical after both runs.

**Acceptance Scenarios**:

1. **Given** a server that has already been cabled and the AVD cascade has completed, **When** the server cabling generator runs again for the same server, **Then** the resulting leaf switch configurations remain unchanged with no duplicate interfaces, links, or routing entries.

---

### Edge Cases

- What happens when the server cabling generator runs but no new links are actually created (all interfaces already connected)? The cascade should still trigger to ensure configs are current, but produce no changes.
- What happens when only one of the two leaf switches in a rack is affected by the new server cabling? Both leaf switch hostvars should regenerate since AVD needs a consistent view of all devices in the fabric.
- What happens if the hostvar generator is already running when the server cabling generator tries to trigger it? The system should handle concurrent execution gracefully.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server cabling generator MUST trigger AVD hostvar regeneration for the fabric after successfully creating server-to-leaf links.
- **FR-002**: The hostvar regeneration MUST cascade to structured config generation via the existing `avd_hostvars_ready` trigger mechanism.
- **FR-003**: The structured config generation MUST cascade to backfill via the existing `structured_config_checksum` trigger mechanism.
- **FR-004**: The cascade trigger MUST reset the fabric's `avd_hostvars_ready` flag to `False` before triggering hostvar regeneration, ensuring the structured config generator fires when hostvars complete.
- **FR-005**: The cascade MUST be idempotent - running the server cabling generator multiple times for the same server MUST produce the same final configuration state.
- **FR-006**: The cascade MUST work regardless of whether the server is the first or Nth server added to the rack.

### Key Entities

- **NetworkFabric**: Top-level entity that owns the `avd_hostvars_ready` flag controlling structured config generation.
- **NetworkDevice (leaf)**: Leaf switches whose hostvars must be regenerated to include new server-facing interfaces.
- **ComputePhysicalServer**: The server being cabled; its addition triggers the cascade.
- **AvdArtifact**: Stores hostvar and structured config data per device; checksum changes trigger downstream generators.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Adding a server and running the server cabling generator results in fully updated leaf switch configurations within a single automated pipeline run, with zero manual steps required after the initial generator execution.
- **SC-002**: All leaf switches in the affected rack have hostvars that include the newly created server-facing interfaces and VLAN assignments after the cascade completes.
- **SC-003**: Running the server cabling generator twice for the same server produces identical final configurations with no duplicate or orphaned data.
- **SC-004**: The existing fabric-level AVD cascade (hostvar → structured config → backfill) continues to function correctly for non-server-related changes.

## Assumptions

- The existing trigger mechanism (`avd_hostvars_ready` flag on `NetworkFabric`) is sufficient to trigger the structured config generator after hostvar regeneration. No new trigger rules are needed for the structured config or backfill stages.
- The server cabling generator has access to the fabric context (via the server's rack's pod's fabric relationship) to set the `avd_hostvars_ready` flag.
- The hostvar generator already handles server-facing interfaces correctly when they exist as links on leaf switch interfaces - only the trigger cascade is missing.
