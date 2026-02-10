# Feature Specification: Enforce GraphQL Query Return Types Everywhere

**Feature Branch**: `002-enforce-gql-types`
**Created**: 2026-02-10
**Status**: Implemented
**Input**: User description: "ensure we are using graphql query return types everywhere"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer Gets Type Errors for Invalid Query Data Access (Priority: P1)

A developer working on generators or transforms receives immediate feedback from type checkers (mypy) when they access GraphQL query result fields incorrectly. Instead of runtime KeyError or AttributeError, the type system catches mismatches during development.

**Why this priority**: Type safety on GraphQL query results is the core ask. Catching errors at dev time prevents runtime failures in production generators/transforms.

**Independent Test**: Can be verified by running `mypy` across the codebase and confirming that all generator and transform methods use Pydantic query types for parameters and intermediate variables.

**Acceptance Scenarios**:

1. **Given** a generator's `generate()` method receives GraphQL query data, **When** the method processes the data, **Then** all method parameters and local variables that hold query data use the specific Pydantic query model types (not generic `dict` or `dict[str, Any]`).
2. **Given** a transform's `transform()` method receives GraphQL query data, **When** the method processes the data, **Then** the method parameter is annotated with the correct Pydantic query type.
3. **Given** a helper function receives a portion of the GraphQL query result, **When** the function signature is defined, **Then** the parameter and return types use specific Pydantic sub-types or TypedDict rather than generic dicts.

---

### User Story 2 - Developer Uses Structured Return Types from Helper Functions (Priority: P2)

Helper functions that extract and return structured data from query results return TypedDict or dataclass types instead of generic `dict[str, list[str]]` or `list[dict]`. Callers get autocomplete and type checking on the returned data.

**Why this priority**: Helper functions are reused across the codebase. Weak return types propagate untyped data to all callers.

**Independent Test**: Can be verified by checking that helper functions like `extract_uplinks_from_dict()` and `extract_connected_endpoints()` use TypedDict return types, and callers access fields with typed attribute patterns.

**Acceptance Scenarios**:

1. **Given** `extract_uplinks_from_dict()` returns uplink data, **When** the return type is inspected, **Then** it uses a TypedDict with explicit keys (`uplink_interfaces`, `uplink_switches`, `uplink_switch_interfaces`).
2. **Given** `extract_connected_endpoints()` returns server endpoint data, **When** the return type is inspected, **Then** it uses a TypedDict or list of TypedDict instead of `list[dict]`.

---

### User Story 3 - All Type Annotations Are Correct (Priority: P3)

All type annotations in generators and transforms use correct Python typing syntax. No typos like `dict[str, any]` (lowercase) exist.

**Why this priority**: Incorrect annotations silently break type checking without any visible error.

**Independent Test**: Can be verified by running mypy and confirming zero type errors related to annotation syntax.

**Acceptance Scenarios**:

1. **Given** a type annotation uses `any` (lowercase), **When** the code is reviewed, **Then** it is corrected to `Any` (from `typing`).
2. **Given** a transform method has a redundant re-annotation (e.g., parameter already typed correctly), **When** the code is reviewed, **Then** the redundant re-annotation is removed.

---

### Edge Cases

- What happens when the Infrahub SDK base class constrains the `generate()` method signature to `data: dict`? The re-annotation pattern inside the method body is acceptable as a workaround.
- What happens when structured config data comes from `json.loads()` (object store) rather than GraphQL? This data is not from GraphQL queries and has no Pydantic query models available; it is out of scope for this feature.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: All transform and generator `transform()`/`generate()` methods MUST use `dict[str, Any]` or `dict` as the parameter type (honest about SDK runtime behavior), immediately re-annotating to the specific Pydantic query type on the first line of the method body.
- **FR-002**: Helper functions that receive portions of GraphQL query results MUST use the specific Pydantic sub-type for parameters (e.g., `GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces`).
- **FR-003**: Helper functions that return structured data extracted from queries MUST use TypedDict return types instead of generic `dict[str, list[str]]` or `list[dict]`.
- **FR-004**: All type annotations MUST use correct Python typing syntax (`Any` from `typing`, not lowercase `any`).
- **FR-005**: Weak dict annotations (bare `dict`, `dict[str, dict]`, `list[dict]`) MUST be replaced with properly parameterized types (`dict[str, Any]`, `dict[str, ServerEndpoint]`, `list[ServerEndpoint]`).

### Key Entities

- **Pydantic Query Models**: Auto-generated models in `*_query.py` files that provide type-safe access to GraphQL query results. Each generator/transform has a corresponding query model.
- **TypedDict**: Python typing construct for dictionaries with known string keys and specific value types. Used for helper function return types where full Pydantic models are unnecessary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All transform and generator methods use the consistent pattern: `dict[str, Any]`/`dict` parameter with immediate Pydantic re-annotation.
- **SC-002**: All helper function return types use TypedDict or specific types instead of generic dict patterns (0 instances of `list[dict]` or `dict[str, list[str]]` as return types for query-related helpers).
- **SC-003**: Zero type annotation typos remain (no instances of `dict[str, any]` with lowercase `any`).
- **SC-004**: All existing tests continue to pass after the changes (80/80 passing).
- **SC-005**: mypy error count reduced (61 → 51, improvement of 10 fewer errors).

## Assumptions

- The Infrahub SDK base class `InfrahubGenerator.generate()` requires `data: dict` as the method signature. This cannot be changed, so the re-annotation pattern inside the method body is the accepted workaround.
- Structured config data from `json.loads()` (object store) is out of scope. This data represents AVD configuration, not GraphQL query results, and would require pyAVD-specific Pydantic models.
- The backfill generator's routing config processing methods (BGP, prefix lists, route maps, static routes) operate on JSON-parsed AVD data, not on GraphQL query results. These are out of scope.
- No changes to `.gql` files or auto-generated `*_query.py` files are needed.
