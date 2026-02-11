# Feature Specification: Fix Hostvar Interface Ordering

**Feature Branch**: `006-fix-hostvar-interface-order`
**Created**: 2026-02-10
**Status**: Draft
**Input**: Fix non-deterministic interface ordering in AVD hostvar generation that causes P2P link IP addresses to change when servers are added

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stable P2P IPs After Server Addition (Priority: P1)

When an operator adds a server to a leaf switch and regenerates AVD hostvars, the P2P link IP addresses for existing uplinks must remain unchanged. Currently, adding a server causes Neo4j to return interfaces in a different order, which shifts the uplink list positions and causes pyAVD to assign different IPs.

**Why this priority**: This is the core bug. Unstable P2P IPs break routing adjacencies and cause configuration drift across the fabric.

**Independent Test**: Can be tested by generating hostvars for a device with uplinks in shuffled order and verifying the output uplink lists are always sorted identically regardless of input order.

**Acceptance Scenarios**:

1. **Given** a leaf device with uplink interfaces [Ethernet3, Ethernet1, Ethernet2] returned from GraphQL in arbitrary order, **When** hostvars are generated, **Then** `uplink_interfaces` is `["Ethernet1", "Ethernet2", "Ethernet3"]` with corresponding `uplink_switches` and `uplink_switch_interfaces` sorted in lockstep.
2. **Given** a leaf device with existing hostvars, **When** a new server interface is added and hostvars are regenerated, **Then** the `uplink_interfaces`, `uplink_switches`, and `uplink_switch_interfaces` lists are identical to the previous generation.

---

### User Story 2 - Stable Connected Endpoint Ordering (Priority: P2)

When multiple servers are connected to a leaf switch, the connected endpoints section of the hostvars must also be deterministically ordered. While this doesn't directly affect P2P IP allocation, non-deterministic server ordering can cause unnecessary structured config changes and checksum churn.

**Why this priority**: Prevents unnecessary regeneration cycles and ensures idempotent config generation end-to-end.

**Independent Test**: Can be tested by providing server interfaces in randomized order and verifying the `servers` list in hostvars is always in the same deterministic order.

**Acceptance Scenarios**:

1. **Given** a leaf device with server interfaces [Ethernet51, Ethernet49, Ethernet50] returned in arbitrary order, **When** hostvars are generated, **Then** the `servers` list entries have adapters ordered by switch port name.
2. **Given** server adapters within a single server, **When** hostvars are generated, **Then** adapters are ordered by their `switch_ports` value.

---

### Edge Cases

- What happens when a device has zero uplink interfaces? The sorted list should remain empty, preserving current behavior.
- What happens when interface names use mixed formats (e.g., "Ethernet1" vs "ethernet1")? `netutils.sort_interface_list()` handles case normalization.
- What happens when a device has uplinks but no server interfaces? Only uplink sorting applies; server section is omitted as before.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `extract_uplinks_from_dict()` function MUST sort the three uplink lists (`uplink_interfaces`, `uplink_switches`, `uplink_switch_interfaces`) by local interface name before returning.
- **FR-002**: The three uplink lists MUST remain in lockstep after sorting — the switch name and switch interface at index N must correspond to the local interface at index N.
- **FR-003**: The `extract_connected_endpoints()` function MUST return servers in a deterministic order (sorted by server name), with adapters within each server sorted by switch port name.
- **FR-004**: All existing unit tests MUST continue to pass after the change.
- **FR-005**: New unit tests MUST verify that shuffled input produces identical sorted output for both uplink extraction and connected endpoint extraction.

### Key Entities

- **UplinkData**: Three parallel lists (uplink_interfaces, uplink_switches, uplink_switch_interfaces) that must remain in lockstep order.
- **ServerEndpoint**: Server name with a list of adapter configurations, each referencing switch ports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Generating hostvars for the same device twice (with interfaces returned in different orders) produces byte-identical JSON output 100% of the time.
- **SC-002**: All existing tests pass without modification.
- **SC-003**: New tests cover both uplink sorting and connected endpoint sorting with randomized inputs.
- **SC-004**: No increase in generator execution complexity — sorting adds negligible overhead.

## Assumptions

- `netutils.interface.sort_interface_list()` is already a project dependency and used in other generators (`sorting.py`), so it is the correct tool for interface name sorting.
- Interface names within a single device are always unique.
- The existing `sorting.py` module's `create_sorted_device_interface_map()` pattern is not directly reusable here because the hostvar generator works with GraphQL Pydantic models (not protocol objects), but the same `sort_interface_list()` function applies.
