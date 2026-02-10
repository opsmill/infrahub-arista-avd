# Feature Specification: Enforce Protocol-Typed Access Across Generators and Transforms

**Feature Branch**: `001-enforce-protocols`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "I need to ensure all generators and transforms use protocols generated from infrahubctl protocols --out src/solution_ai_dc/protocols.py"

## Clarifications

### Session 2026-02-10

- Q: Should transforms with untyped query-data access (raw dicts instead of Pydantic models) be updated as part of this feature, even though the fix is adding Pydantic query models — not protocol classes? → A: Yes, in scope. Update transforms with raw dict access to use Pydantic query models to achieve full typed access in one pass.
- Q: Should AVD generators that already use protocol classes be considered compliant, or should compliance be explicitly audited and documented? → A: Audit and confirm. Explicitly verify each generator's client operations and document compliance status.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Protocol Usage in All Generators (Priority: P1)

As a developer maintaining the Infrahub repository solution, I want all generators to use the protocol classes from `protocols.py` for creating, fetching, and manipulating nodes so that node attribute access is type-safe and consistent across the codebase.

**Why this priority**: Generators are the primary mechanism for creating and managing infrastructure data. Inconsistent node access patterns lead to runtime errors that are hard to catch, especially when schema changes occur. Protocol classes provide compile-time-like safety via static analysis tools.

**Independent Test**: Can be verified by confirming all generator files import and use protocol classes for node operations, and that static analysis (mypy) passes without type errors on node attribute access.

**Compliance Audit** (verified via source grep):

| Generator | Status | Details |
| --------- | ------ | ------- |
| `generate_fabric.py` | Compliant | All `kind=` params use protocol classes (`CoreNumberPool`, `CoreIPAddressPool`, `CoreIPPrefixPool`, `NetworkPod`) |
| `generate_pod.py` | Compliant | All `kind=` params use protocol classes; `client.create(NetworkDevice, ...)` uses positional protocol |
| `generate_rack.py` | Compliant | All `kind=` params use protocol classes; `client.create(NetworkDevice, ...)` uses positional protocol |
| `generate_avd_device_hostvar.py` | Partial | 1 string-kind call: `kind="NetworkPod"` (line 27). `client.create(AvdArtifact, ...)` is compliant |
| `generate_avd_device_structured_config.py` | Compliant | Uses `client.create(AvdArtifact, ...)` protocol class; no string-kind calls |
| `backfill_structured_config.py` | Non-compliant | 10 string-kind calls: `kind="IpamIPPrefix"`, `kind="IpamIPAddress"`, `kind="RoutingBGPPeerGroup"`, `kind="RoutingBGPNeighbor"`, `kind="RoutingPrefixList"`, `kind="RoutingPrefixListEntry"`, `kind="RoutingRouteMap"`, `kind="RoutingRouteMapEntry"`, `kind="RoutingStaticRoute"`. 2 calls use `NetworkInterface` protocol (compliant) |

**Acceptance Scenarios**:

1. **Given** the backfill generator with 10 string-kind `client.create()` calls, **When** updated, **Then** all calls use protocol class references (requires regenerating `protocols.py` to include IPAM and Routing types).
2. **Given** the AVD hostvar generator with 1 string-kind `client.filters()` call, **When** updated, **Then** it uses the `NetworkPod` protocol class import.
3. **Given** compliant generators (fabric, pod, rack, AVD structured config), **When** audited, **Then** no changes are needed — compliance is documented.

---

### User Story 2 - Typed Access in All Transforms (Priority: P2)

As a developer, I want all transforms to use typed access — protocol classes for client node operations and Pydantic query models for GraphQL response traversal — so that attribute references are validated by static analysis and consistent with the rest of the codebase.

**Why this priority**: Transforms produce artifacts (configs, docs, cabling plans) from node data. Dict-based or untyped access is fragile — schema renames or attribute removals silently break transforms at runtime. Typed access catches these issues earlier.

**Independent Test**: Can be verified by confirming all transform files use typed access (protocol classes for client operations, Pydantic query models for query data), and that static analysis passes.

**Compliance Audit** (verified via source grep):

| Transform | Status | Details |
| --------- | ------ | ------- |
| `cabling_plan.py` | Compliant | Uses protocol classes (`NetworkLink`, `NetworkDevice`, `NetworkInterface`, `LocationRack`) for `client.filters()` calls |
| `avd_eos_config.py` | Compliant | Uses Pydantic query models for attribute access; only client op is `object_store.get()` |
| `avd_device_doc.py` | Compliant | Uses Pydantic query models for attribute access; only client op is `object_store.get()` |
| `computed_interface_description.py` | Compliant | Uses Pydantic query models; no client node operations |
| `avd_fabric_doc.py` | Non-compliant | Uses raw dict access for GraphQL query data (e.g., `device["hostname"]["value"]`); no Pydantic query model; no client node operations |

**Acceptance Scenarios**:

1. **Given** `avd_fabric_doc.py` accesses GraphQL query data via raw dict keys, **When** updated, **Then** it uses a Pydantic query model for typed attribute access.
2. **Given** compliant transforms (cabling_plan, avd_eos_config, avd_device_doc, computed_interface_description), **When** audited, **Then** no changes are needed — compliance is documented.

---

### User Story 3 - Protocol Types in Core Utility Modules (Priority: P3)

As a developer, I want shared utility modules (particularly `avd.py`) to use protocol class type annotations instead of `Any` types so that callers receive type safety benefits throughout the call chain.

Currently, `avd.py` uses `Sequence[Any]` for parameters that represent network interfaces and devices. Replacing these with protocol class types provides end-to-end type safety from generators through utilities.

**Why this priority**: Utility modules are shared across multiple generators and transforms. Improving their type signatures multiplies the benefit across all consumers, but requires the higher-priority generator and transform work to be aligned first.

**Independent Test**: Can be verified by running mypy against `src/solution_ai_dc/avd.py` and confirming protocol-typed function signatures pass without errors.

**Acceptance Scenarios**:

1. **Given** a utility function accepting `Sequence[Any]` for node parameters, **When** updated, **Then** it uses the appropriate protocol class type (e.g., `Sequence[NetworkInterface]`).
2. **Given** callers of the utility module, **When** they pass protocol-typed objects, **Then** mypy validates the call without requiring casts or `# type: ignore` comments.

---

### Edge Cases

- What happens when protocol classes do not yet exist for certain schema node types (e.g., Routing namespace nodes)? **Resolution**: FR-003 requires regenerating `protocols.py` to include all schema-defined types before other changes.
- How should GraphQL query response data (Pydantic models from ariadne-codegen) coexist with protocol classes? **Resolution**: They serve complementary purposes — Pydantic query models for GraphQL response parsing, protocol classes for client node operations. Both are "typed access" mechanisms.
- What happens when a transform only reads data via GraphQL and never calls `client.create/get/filters`? **Resolution**: It must still use Pydantic query models (not raw dicts) for typed access. Transforms using raw dict access to query data are in scope for conversion to Pydantic query models.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All generators MUST use protocol classes from `protocols.py` for `client.create()`, `client.get()`, and `client.filters()` calls instead of string-based kind references.
- **FR-002**: All transforms that perform Infrahub client node operations MUST use protocol classes for those operations.
- **FR-003**: The `protocols.py` file MUST be regenerated to include protocol classes for all schema-defined node types, including Routing namespace nodes (`RoutingBGPPeerGroup`, `RoutingBGPNeighbor`, `RoutingPrefixList`, `RoutingPrefixListEntry`, `RoutingRouteMap`, `RoutingRouteMapEntry`, `RoutingStaticRoute`) and IPAM types (`IpamIPPrefix`, `IpamIPAddress`).
- **FR-004**: Core utility modules (`avd.py`) MUST replace `Any` type annotations with appropriate protocol class types for node parameters.
- **FR-005**: Pydantic query models (generated by ariadne-codegen) MUST continue to be used for GraphQL response parsing — protocol adoption applies only to Infrahub client node operations.
- **FR-006**: All existing unit and integration tests MUST continue to pass after protocol adoption changes.
- **FR-007**: Static analysis (mypy) MUST pass on all modified files without new `# type: ignore` suppressions related to protocol usage.
- **FR-008**: Transforms that access GraphQL query data via raw dict keys MUST be updated to use Pydantic query models for typed attribute access.

### Key Entities

- **Protocol Class**: A generated Python class that provides typed attribute access for a specific Infrahub schema node type (e.g., `NetworkDevice`, `NetworkInterface`, `IpamIPPrefix`). Used as the type parameter for Infrahub client operations.
- **Pydantic Query Model**: An auto-generated model (from ariadne-codegen) that represents the shape of a GraphQL query response. Used for parsing and traversing query results — distinct from protocol classes.
- **Generator**: An Infrahub component that creates and manages infrastructure nodes. Uses GraphQL queries for input and Infrahub client operations for node creation/updates.
- **Transform**: An Infrahub component that reads node data and produces artifacts (configs, documentation, reports). May use client operations to fetch additional data beyond the initial query.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generators use protocol classes for all Infrahub client node operations (create, get, filters) — zero string-based kind references remain.
- **SC-002**: 100% of transforms that perform Infrahub client node operations use protocol classes for those operations.
- **SC-003**: All schema-defined node types have corresponding protocol classes in `protocols.py`, including Routing namespace and IPAM types.
- **SC-004**: Static analysis passes on all generator, transform, and utility files without new type suppressions.
- **SC-005**: All existing tests (unit and integration) pass without modification to test assertions, confirming behavioral equivalence.
- **SC-006**: Zero transforms use raw dict access for GraphQL query data — all use Pydantic query models.

## Assumptions

- The `infrahubctl protocols` command can generate protocol classes for all node types defined in the project schemas, including the Routing namespace.
- Pydantic query models and protocol classes serve complementary purposes and do not need to be unified — query models parse GraphQL responses, protocols type node operations.
- The `ComputedInterfaceDescription` transform operates purely on GraphQL query data via Pydantic query models and does not perform client node operations, so it requires no changes (already compliant).
- SDK-provided protocol classes (`CoreNumberPool`, `CoreIPAddressPool`, `CoreIPPrefixPool` from `infrahub_sdk.protocols`) are already in use by compliant generators and do not need regeneration.
