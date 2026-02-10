# Feature Specification: Backfill AVD Attribute Source

**Feature Branch**: `003-backfill-avd-source`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "I want to update the backfill service to use the infrahub-sdk features of specifying a source for the attributes and set them from CoreAccountGroup with the name of AVD"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Attribute Source Tagging on Backfill (Priority: P1)

As an infrastructure operator, when the backfill structured config generator creates or updates nodes in Infrahub, every attribute written should be tagged with the "AVD" CoreAccountGroup as its source. This provides data lineage so operators can see which attribute values originated from AVD automation versus manual entry or other systems.

**Why this priority**: Source attribution is the core purpose of this feature. Without it, backfilled data is indistinguishable from manually entered data, making auditing and conflict resolution difficult.

**Independent Test**: Can be fully tested by running the backfill generator against a device with structured config, then querying the created nodes with `property=True` to verify that each attribute's `source` points to the "AVD" CoreAccountGroup.

**Acceptance Scenarios**:

1. **Given** a device with AVD structured config in the object store, **When** the backfill generator runs, **Then** all created IpamIPPrefix attributes have source set to the "AVD" CoreAccountGroup.
2. **Given** a device with AVD structured config, **When** the backfill generator creates IpamIPAddress nodes, **Then** the address and ip_prefix attributes have source set to "AVD".
3. **Given** a device with interfaces and MTU values in structured config, **When** the backfill generator updates MTU, **Then** the MTU attribute source is set to "AVD".
4. **Given** a device with BGP configuration, **When** the backfill generator creates BGP peer groups, neighbors, prefix lists, route maps, and static routes, **Then** all attributes on these nodes have source set to "AVD".

---

### User Story 2 - Source Group Lookup at Generator Initialization (Priority: P1)

The generator must look up the "AVD" CoreAccountGroup once at the start of execution and reuse it for all subsequent node saves, avoiding redundant API calls per node.

**Why this priority**: Efficient lookup is essential for generator performance. Looking up the group per-save would multiply API calls unnecessarily.

**Independent Test**: Can be tested by verifying the generator fetches CoreAccountGroup exactly once and passes it to all save operations.

**Acceptance Scenarios**:

1. **Given** the "AVD" CoreAccountGroup exists in Infrahub, **When** the backfill generator starts, **Then** it retrieves the group once and caches the reference for use across all saves.
2. **Given** the "AVD" CoreAccountGroup does not exist, **When** the backfill generator starts, **Then** it logs a clear warning and continues without setting source (graceful degradation).

---

### Edge Cases

- What happens when the "AVD" CoreAccountGroup is deleted or renamed between generator runs? The generator should handle a missing group gracefully with a warning log.
- What happens if a node attribute already has a different source set by another system? The backfill overwrites the source to "AVD" since it is re-asserting the value.
- How does the system behave if the CoreAccountGroup lookup fails due to a transient network error? Standard SDK error propagation applies; the generator fails as it would for any other API error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backfill generator MUST look up the CoreAccountGroup named "AVD" at the start of each `generate()` invocation and use it as the source for all attribute writes.
- **FR-002**: The source MUST be applied to all attributes on all node types created or updated by the backfill generator: IpamIPPrefix, IpamIPAddress, NetworkInterface (MTU), RoutingBGPPeerGroup, RoutingBGPNeighbor, RoutingPrefixList, RoutingPrefixListEntry, RoutingRouteMap, RoutingRouteMapEntry, RoutingStaticRoute.
- **FR-003**: If the "AVD" CoreAccountGroup cannot be found, the generator MUST log a warning and continue operating without source attribution (no failure).
- **FR-004**: The CoreAccountGroup lookup MUST happen once per `generate()` call, not once per node save.

### Key Entities

- **CoreAccountGroup ("AVD")**: The Infrahub account group representing the AVD automation system. Used as the `source` metadata property on attributes to provide data lineage.
- **Attribute Source**: An infrahub-sdk metadata property on each attribute that records which system or user created/modified the value.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of attributes written by the backfill generator have their source set to the "AVD" CoreAccountGroup when the group exists.
- **SC-002**: The generator makes exactly one API call to look up the CoreAccountGroup per execution, regardless of how many nodes are processed.
- **SC-003**: When the CoreAccountGroup is missing, the generator completes successfully with a logged warning and no source attribution.
- **SC-004**: All existing unit tests continue to pass with the source feature integrated.

## Assumptions

- The "AVD" CoreAccountGroup is pre-loaded into Infrahub via `objects/00_user_groups.yml` before the generator runs.
- The infrahub-sdk supports setting source metadata on attributes via the `NodeProperty` mechanism.
- Source attribution is additive metadata and does not affect the functional behavior of node creation or updates.
- Overwriting an existing source on an attribute is acceptable behavior (last-writer-wins).
