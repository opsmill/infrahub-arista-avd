# Schema Design Specification: Normalized Device Design Entities

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate all schema definitions.

**Feature Branch**: `005-device-design-entities`
**Created**: 2026-07-24
**Status**: Draft
**Input**: User description: "each design object has like spines -> template object and then a quantity. Maybe we should move the device designs to like a design entity relationship of many and then you can have a number of device relationships per rack like leaf object template and then a quantity. Rack -> RackDeviceDesignEntity; device_template -> template (cardinality one); device_quantity -> 2"

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

---

## Context

Today each fabric container embeds its device design as a **paired** set of fields — one template relationship plus one quantity attribute, per device role — hard-coded onto the container node:

| Tier (node) | Template relationship (cardinality one) | Quantity attribute |
|-------------|------------------------------------------|--------------------|
| `NetworkFabric` | `super_spine_switch_template` | `amount_of_super_spines` |
| `NetworkPod` | `spine_switch_template` | `amount_of_spines` |
| `LocationRack` | `leaf_switch_template`, `l2leaf_switch_template` | `amount_of_leafs`, `amount_of_l2leafs` |

Adding a new device role/type at any tier (or a second design of the same role) requires a **schema change** — a new relationship and a new attribute — plus a matching generator and query-model change. This spec normalizes the pattern into a reusable **device design entity**: a child object that pairs one object template with a quantity and a role, related *many* from its container. New device types then become **data**, not schema.

The user's literal example (`Rack -> RackDeviceDesignEntity`, `device_template` cardinality one, `device_quantity` = 2) is the rack-tier instance of this pattern; the decided scope applies the same pattern uniformly to all three tiers.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Normalize rack device designs (leaf + L2 leaf) (Priority: P1)

Replace the rack's paired leaf/L2-leaf design fields (`leaf_switch_template`/`amount_of_leafs` and `l2leaf_switch_template`/`amount_of_l2leafs`) with a *many* relationship of device design entities. Each entity pairs one object template with a quantity and an explicit role, so a rack can express "2 × leaf from template X" and "1 × l2leaf from template Y" as two design rows rather than four fixed fields.

**Why this priority**: This is the concrete case in the user's request and the tier that already carries more than one device role, so it delivers the clearest value and exercises the full pattern (multiple designs per container) on its own.

**Independent Test**: Load the schema with `infrahubctl schema check schemas/` (zero errors), then in the UI create a `LocationRack` and attach two device design entities (leaf ×2, l2leaf ×1); confirm the rack renders its designs and rejects a duplicate design for the same role.

**Acceptance Scenarios**:

1. **Given** the schema is loaded, **When** an operator opens a `LocationRack`, **Then** it exposes a *many* relationship of device design entities instead of the fixed leaf/L2-leaf template and quantity fields.
2. **Given** a rack with no designs, **When** an operator adds a design entity with a template, a role of `leaf`, and a quantity of 2, **Then** the entity is created, owned by the rack, and displayed with a readable identifier.
3. **Given** a rack that already has a `leaf` design, **When** an operator adds a second `leaf` design to the same rack, **Then** the uniqueness constraint rejects it (one design per role per container).
4. **Given** a rack with device designs, **When** the rack is deleted, **Then** its device design entities are deleted with it (owned children).

---

### User Story 2 - Apply the same pattern to pod (spines) and fabric (super-spines) (Priority: P2)

Extend the normalized device-design pattern to `NetworkPod` (spine designs) and `NetworkFabric` (super-spine designs), replacing `spine_switch_template`/`amount_of_spines` and `super_spine_switch_template`/`amount_of_super_spines` with the same *many* device-design relationship, so all three tiers share one consistent model.

**Why this priority**: Uniformity across tiers is the goal the user articulated ("each design object has like spines"), but it depends on the pattern proven at the rack tier in US1 and touches more consumers, so it follows P1.

**Independent Test**: With the schema loaded, create a `NetworkFabric` and `NetworkPod`, attach a `super_spine` design to the fabric and a `spine` design to the pod, and confirm both render through the same entity shape and pass `infrahubctl schema check`.

**Acceptance Scenarios**:

1. **Given** the schema is loaded, **When** an operator opens a `NetworkPod`, **Then** it exposes a *many* device-design relationship in place of the fixed spine template and quantity fields.
2. **Given** the schema is loaded, **When** an operator opens a `NetworkFabric`, **Then** it exposes a *many* device-design relationship in place of the fixed super-spine template and quantity fields.
3. **Given** a fabric, pod, and rack, **When** their device designs are inspected, **Then** every tier presents device designs through the same entity shape (template + quantity + role).

---

### User Story 3 - Add a new device type without a schema change (Priority: P3)

An operator can introduce an additional device role/type at any tier (for example a second leaf template, or a future role) by adding a device design entity as **data**, with no new relationship or attribute added to the container node and no schema reload required beyond the initial rollout.

**Why this priority**: This is the payoff of the normalization and validates that the model met its intent, but it is an outcome of US1/US2 rather than separate structure.

**Independent Test**: On a loaded schema with no further schema edits, add a new device design entity of a supported role to a container via the object/data layer and confirm it is accepted and displayed.

**Acceptance Scenarios**:

1. **Given** a loaded, unchanged schema, **When** an operator adds a device design entity for a supported role that the container does not yet have, **Then** it is accepted with no schema modification.
2. **Given** a device design entity, **When** its `device_quantity` is changed, **Then** the new value is stored without any schema change.

---

### Edge Cases

- **Quantity bounds**: What is the minimum/maximum `device_quantity`? Leaf designs currently cap at 2 (MLAG pairing). See Assumptions — the generic enforces a minimum of 1; role- or tier-specific maxima are deferred to generator/validation logic rather than the schema.
- **Missing designs**: What happens when a container has zero device designs (previously implied by a quantity of 0, e.g. `amount_of_l2leafs: 0`)? Absence of a design row is the new representation of "none of that role".
- **Role/template mismatch**: What if a design's `role` does not match the referenced object template's own role? The design's explicit `role` is authoritative for generation; template role values are not relied upon (see Assumptions).
- **Duplicate role**: Two designs of the same role in one container are rejected by the uniqueness constraint.
- **Migration with existing data**: How are the current per-tier template/quantity values carried into device design entities without data loss? Removed attributes/relationships use `state: absent`, and existing values must be migrated into design entities before the old fields are removed (see FR-060..FR-063).
- **Cross-file relationships**: Rack lives in the `Location` namespace while fabric/pod live in `Network`; the design-entity relationships added to `LocationRack` must be defined through the `extensions` block with matching identifiers.
- **Cascade on delete**: Deleting a container deletes its owned design entities; deleting a design entity must not delete the shared object template it references.

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: Schema MUST define a generic `NetworkDeviceDesign` (namespace `Network`) that holds the shared shape of a device design: the object-template relationship, the quantity attribute, and the role attribute.
- **FR-002**: Schema MUST define one concrete design node per tier — for the fabric, pod, and rack tiers respectively — each inheriting from `NetworkDeviceDesign`, so that each can be a typed child of its specific container. (Per-tier concrete nodes are required because an Infrahub `Parent` relationship targets a single kind; the three container kinds do not share a common parent generic.)
- **FR-003**: Each concrete design node MUST inherit from `NetworkDeviceDesign` via `inherit_from` and MUST NOT redefine the shared attributes/relationship it inherits.
- **FR-004**: All node names MUST be PascalCase (pattern: `^[A-Z][a-zA-Z0-9]+$`, 2-32 chars).
- **FR-005**: All namespaces MUST start with an uppercase letter followed by lowercase (pattern: `^[A-Z][a-z0-9]+$`, 3-32 chars).

#### Attributes

- **FR-010**: `NetworkDeviceDesign` MUST define `device_quantity` of kind `Number`, `optional: false`, with a minimum value of 1 (parameters `min_value: 1`).
- **FR-011**: `NetworkDeviceDesign` MUST define `role` of kind `Dropdown`, `optional: false`, whose choices are the supported device roles: `super_spine`, `spine`, `leaf`, `l2leaf` (mirroring the roles already enumerated on `NetworkSpanningTreePriority`).
- **FR-012**: All `Dropdown` attributes MUST include a `choices` list with at least `name` for each choice.
- **FR-013**: Mandatory attributes MUST either be `optional: false` (default) or provide a `default_value`.
- **FR-014**: All attribute names MUST be snake_case (pattern: `^[a-z0-9\_]+$`, 3-32 chars).
- **FR-015**: Attribute kinds MUST use valid kinds (Text, Number, Boolean, Dropdown, …) and MUST NOT use the deprecated `String` kind.

#### Relationships

- **FR-020**: `NetworkDeviceDesign` MUST define a relationship `device_template` to `CoreObjectTemplate` with `kind: Attribute`, `cardinality: one`, `optional: false`.
- **FR-021**: Each concrete design node MUST define a `Parent` relationship (cardinality one, `optional: false`) to its container (`NetworkFabric`, `NetworkPod`, or `LocationRack`), and each container MUST define the matching `Component` relationship `device_designs` (cardinality many) with a matching `identifier` on both sides.
- **FR-022**: All relationship `peer` values MUST use the full kind (Namespace + Name, e.g. `CoreObjectTemplate`, `NetworkPod`).
- **FR-023**: All relationship names MUST be snake_case (pattern: `^[a-z0-9\_]+$`, 3-32 chars).
- **FR-024**: The `device_designs` relationship on `LocationRack` MUST be added through the `extensions` block (Rack is defined in `location_extensions.yml` / `l3ls_extensions.yml`); fabric and pod `device_designs` relationships MUST be added to their nodes in `logical_design.yml`.
- **FR-025**: Deleting a container MUST cascade-delete its owned device design entities; deleting a device design entity MUST NOT delete the referenced `CoreObjectTemplate` (`on_delete` configured so the template survives).

#### Display & Identification

- **FR-040**: Each concrete design node MUST define `human_friendly_id` combining its container and role (e.g. `["<container>__name__value", "role__value"]`) so instances are uniquely and readably identified.
- **FR-041**: Each design node MUST define `display_label` (attribute name or Jinja2 template) rendering a readable label such as the role and quantity.
- **FR-042**: Attributes MUST use `order_weight` following the repo convention (900-999 primary relationships, 1000-1099 identifiers, 1100+ secondary).
- **FR-043**: Design nodes SHOULD set `include_in_menu: false`, consistent with the container nodes, unless a dedicated menu entry is added.

#### Uniqueness Constraints

- **FR-050**: Each concrete design node MUST define `uniqueness_constraints` of `[[<container>, "role__value"]]` so a container has at most one device design per role.
- **FR-051**: Uniqueness constraints MUST use the `__value` suffix for attribute references and bare names for relationship references.

#### Migration (modifying existing schema)

- **FR-060**: The existing template relationships (`NetworkFabric.super_spine_switch_template`, `NetworkPod.spine_switch_template`, `LocationRack.leaf_switch_template`, `LocationRack.l2leaf_switch_template`) MUST be removed using `state: absent` rather than deleted outright.
- **FR-061**: The existing quantity attributes (`NetworkFabric.amount_of_super_spines`, `NetworkPod.amount_of_spines`, `LocationRack.amount_of_leafs`, `LocationRack.amount_of_l2leafs`) MUST be removed using `state: absent` rather than deleted outright.
- **FR-062**: The new `device_designs` relationships MUST be introduced (and existing data migrated into device design entities) **before** the old fields are removed, so no existing container loses its design information.
- **FR-063**: The schema change MUST be rolled out on a dedicated branch (`infrahubctl branch create` → `schema check --branch` → `schema load --branch`) and merged via a proposed change, never loaded directly onto the default branch.

### Key Entities

- **NetworkDeviceDesign** (generic): The reusable shape of a device design. Attributes: `device_quantity` (Number, ≥1), `role` (Dropdown: super_spine/spine/leaf/l2leaf). Relationship: `device_template` → `CoreObjectTemplate` (Attribute, one, required). Not instantiated directly.
- **Fabric device design** (concrete, inherits `NetworkDeviceDesign`): Child of `NetworkFabric`; carries super-spine designs. Uniqueness: (fabric, role).
- **Pod device design** (concrete, inherits `NetworkDeviceDesign`): Child of `NetworkPod`; carries spine designs. Uniqueness: (pod, role).
- **Rack device design** (concrete, inherits `NetworkDeviceDesign`): Child of `LocationRack`; carries leaf and L2-leaf designs. Uniqueness: (rack, role). This is the user's `RackDeviceDesignEntity`.
- **NetworkFabric / NetworkPod / LocationRack** (existing, modified): Each gains a `device_designs` Component relationship (many) to its concrete design node and loses its per-role template relationships and quantity attributes (via `state: absent`).
- **CoreObjectTemplate** (existing built-in, referenced): The template each design points to; unchanged, and never deleted when a design is removed.

## Assumptions

- **Explicit role is authoritative.** Role is a first-class `Dropdown` attribute on the design entity (decided with the user). The downstream generators drive naming, cabling interface-role filters, MLAG pairing, and the underlay-based role switch (`LEAF_ROLE_BY_UNDERLAY` / `SPINE_ROLE_BY_UNDERLAY`) off this role. Object-template role values are not relied upon for generation.
- **Role choice set.** The supported roles are exactly those already modeled on `NetworkSpanningTreePriority`: `super_spine`, `spine`, `leaf`, `l2leaf`. New roles are added by extending this dropdown (a schema change), while new *designs* of existing roles are data-only.
- **One design per role per container.** Matches current behavior (a single template per role today). Multiple designs of the *same* role in one container are out of scope and rejected by the uniqueness constraint.
- **Quantity bounds.** The schema enforces a minimum of 1. Role/tier-specific maxima (e.g. the current leaf cap of 2 for MLAG) are enforced in generator/validation logic, not the schema generic, to keep the shared shape uniform. A design row is created only for roles that exist; "zero of a role" is represented by the absence of a design (replacing today's `amount_of_*: 0`).
- **Per-tier concrete nodes over a single shared node.** Chosen because an Infrahub `Parent` relationship targets exactly one kind and the three containers share no common parent generic; a single shared design node would require introducing an invasive new container generic across `Network` and `Location` namespaces.
- **Migration on a branch.** This is a modification of loaded schema/data, so it follows the branch-first rollout and `state: absent` removal rules from the `infrahub-managing-schemas` skill.

## Dependencies & Out of Scope

This is a **schema-only** cycle (schema-first principle). The following are required to complete the end-to-end change but are handled in **separate `/speckit-specify` cycles** and are out of scope here:

- **Generators** — `generate_fabric.py`, `generate_pod.py`, `generate_rack.py` and their `.gql` queries + generated `*_query.py` models must be updated to read the new `device_designs` relationship (per role) instead of the removed template/quantity fields, preserving idempotence and deterministic ordering. (Follow-on Generator cycle.)
- **Object/seed data** — `objects/10_fabric.yml`, `objects/10a_fabric_c_fabric.yml`, `objects/11_rack.yml`, `objects/11a_fabric_c_rack.yml`, `objects/13a_fabric_l2ls.yml`, `objects/13b_fabric_campus.yml`, `objects/13c_fabric_isis_ldp.yml`, and any other seed files must be migrated from the paired fields to device design entities. (Follow-on Objects cycle.)
- **Generated protocols** — `src/solution_arista_avd/protocols.py` must be regenerated after the schema loads.
- **Docs** — developer-guide schema/architecture docs must be updated to describe the new entity.

These are noted as coordination requirements (see FR-062) but are not delivered by this schema spec.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `infrahubctl schema check schemas/` passes with zero validation errors.
- **SC-002**: The `NetworkDeviceDesign` generic and its three concrete tier nodes load successfully and appear (or are correctly hidden via `include_in_menu: false`) in the Infrahub UI.
- **SC-003**: `human_friendly_id` renders a readable identifier for each design instance (e.g. "rack-01 / leaf").
- **SC-004**: The uniqueness constraint prevents a second device design of the same role within one container.
- **SC-005**: Deleting a container cascades to its device designs, while the referenced `CoreObjectTemplate` remains.
- **SC-006**: A fabric, a pod, and a rack can each express their device designs (super_spine, spine, leaf, l2leaf) entirely through device design entities, with the previous per-role template relationships and quantity attributes no longer present on the container nodes.
- **SC-007**: A new device design of a supported role can be added to a container at the data layer with no further schema change.
