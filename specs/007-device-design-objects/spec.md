# Object Population Specification: Device-Design Seed Data Migration

> **Workflow**: This spec targets Infrahub object data population. The implementing agent MUST use the `infrahub-managing-objects` skill to generate all object files.

**Feature Branch**: `007-device-design-objects`
**Created**: 2026-07-24
**Status**: Draft
**Input**: User description: "Migrate the numbered seed object files that define fabrics, pods, and racks from the legacy per-role template/quantity fields to `device_designs` child entities (role, device_quantity, device_template), so the refactored generators have populated designs to read. Preserve load order and idempotent re-load; absence of a role means no design entry."

## Context

This is the **Objects** cycle — the co-requisite to `006-device-design-generators`. The generators now read each container's `device_designs` relationship (per role) instead of the legacy `amount_of_<role>s` / `<role>_switch_template` fields. This cycle migrates the numbered seed files so every `NetworkFabric`, `NetworkPod`, and `LocationRack` carries `device_designs` entries expressing the same intent, and removes the legacy fields from the seed data.

Populated designs are what make the hard cutover work: without this migration the generators would read an empty `device_designs` and generate nothing.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Populate rack device designs (leaf + L2 leaf) (Priority: P1)

As an infrastructure engineer, I need every seeded rack to express its leaf and L2-leaf switches as `device_designs` entries (role `leaf` × N, role `l2leaf` × M) instead of `amount_of_leafs`/`leaf_switch_template` and `amount_of_l2leafs`/`l2leaf_switch_template`, so the rack generator produces the same switches from the normalized data.

**Why this priority**: Racks are the busiest tier (two device roles) and the most numerous seeded objects; getting them right unblocks the MVP rack generation and exercises the multi-role-per-container case.

**Independent Test**: Load the migrated rack seed files onto a branch and query `NetworkRackDeviceDesign` — each rack has one `leaf` design (and an `l2leaf` design where it previously had L2 leaves) with the same template and quantity as the legacy fields.

**Acceptance Scenarios**:

1. **Given** the schema (with `device_designs`) is loaded, **When** the migrated rack files load, **Then** each rack that had `amount_of_leafs: N` + `leaf_switch_template: T` has a `device_designs` entry `{role: leaf, device_quantity: N, device_template: T}`.
2. **Given** a rack that previously had `amount_of_l2leafs: M` + `l2leaf_switch_template: T2`, **When** it loads, **Then** it also has `{role: l2leaf, device_quantity: M, device_template: T2}`.
3. **Given** a rack that had no L2 leaves (no `amount_of_l2leafs` or `0`), **When** it loads, **Then** it has **no** `l2leaf` design entry (absence-means-none).
4. **Given** the migrated files, **When** loaded twice, **Then** the second load is idempotent (no duplicate designs).

---

### User Story 2 - Populate pod and fabric device designs (spine, super-spine) (Priority: P2)

As an infrastructure engineer, I need every seeded pod and fabric to express its spines / super-spines as `device_designs` entries, with any previously-implicit counts made explicit, so the pod and fabric generators produce the same devices.

**Why this priority**: Completes the tier coverage; depends on the rack pattern proven in US1 and requires care because some pods/fabrics relied on schema **default** counts that must become explicit.

**Independent Test**: Load the migrated fabric/pod files and query `NetworkPodDeviceDesign` / `NetworkFabricDeviceDesign` — each non-fabric-role pod has a `spine` design and each multi-tier fabric a `super_spine` design, matching prior effective counts and templates.

**Acceptance Scenarios**:

1. **Given** a pod with `spine_switch_template: T` and an explicit or default `amount_of_spines`, **When** it loads, **Then** it has `{role: spine, device_quantity: <effective count>, device_template: T}` — the default (4) materialized as an explicit value where it was implicit.
2. **Given** a fabric with `amount_of_super_spines: N > 0` + `super_spine_switch_template: T`, **When** it loads, **Then** it has `{role: super_spine, device_quantity: N, device_template: T}`.
3. **Given** a single-tier fabric that had `amount_of_super_spines: 0`, **When** it loads, **Then** it has **no** `super_spine` design (absence-means-none).
4. **Given** the fabric-role pod (which holds no spines of its own), **When** it loads, **Then** it has **no** `spine` design.

---

### User Story 3 - Remove legacy fields and preserve end-to-end parity (Priority: P3)

As an infrastructure engineer, I need the legacy per-role fields removed from the seed files so `device_designs` is the single source of design intent, and the full generated fabric to match what the pre-migration seed data produced.

**Why this priority**: The clean end-state and the correctness guarantee; depends on US1/US2 and on the schema no longer requiring the legacy fields.

**Independent Test**: With the legacy fields removed from the schema (005 Stage-3) and from the seed files, load the full `objects/` set and run the generator chain — the produced devices match the pre-migration baseline.

**Acceptance Scenarios**:

1. **Given** the migrated seed files, **When** inspected, **Then** no `amount_of_*` or `*_switch_template` legacy field remains on any fabric/pod/rack object.
2. **Given** the full `objects/` set loads in filename order, **When** the generators run, **Then** the same devices (names, roles, templates, counts) are produced as before the migration.

### Edge Cases

- **Implicit default counts**: pods/fabrics that omitted `amount_of_spines`/`amount_of_super_spines` relied on the schema default (4). The migration MUST materialize the *effective* count explicitly — `device_quantity` has no default and requires ≥1.
- **Zero-count roles**: `amount_of_*: 0` (single-tier fabrics, no-L2-leaf racks) becomes the **absence** of that role's design, not a zero-quantity entry.
- **Fabric-role pod**: the pod with `role: fabric` holds no spines; it gets no `spine` design.
- **Template reference**: `device_template` references a `CoreObjectTemplate` by its human_friendly_id (the `template_name`, e.g. `leaf-switch-compute`); the template files load earlier (`06_device_template.yml`) so references resolve.
- **Required legacy relationships**: pod `spine_switch_template` and rack `leaf_switch_template` are **required** in the Stage-1 schema; removing them from seed data requires the schema to no longer require them (see Dependencies).
- **Nested containers**: pods are seeded as inline `children` of their fabric, so pod `device_designs` nest one level under the fabric; racks are top-level objects, so rack `device_designs` nest directly under each rack.
- **Load order**: device designs reference templates and belong to containers defined in the same or earlier files; the existing numeric file ordering must be preserved.

## Requirements *(mandatory)*

### Functional Requirements

**File Format & Structure**

- **FR-001**: Every migrated file MUST retain `apiVersion: infrahub.app/v1` and `kind: Object`.
- **FR-002**: Each container object MUST express its device designs via the `device_designs` component relationship nested inline with a `data` list of `{role, device_quantity, device_template}` entries.
- **FR-003**: Multiple YAML documents per file MUST remain separated by `---`.

**Device-design entries**

- **FR-004**: Each `device_designs` entry MUST set `role` to a valid choice (`super_spine`, `spine`, `leaf`, `l2leaf`) using the choice `name`, `device_quantity` (integer ≥1), and `device_template` referencing a `CoreObjectTemplate` by human_friendly_id.
- **FR-005**: Fabrics MUST carry a `super_spine` design iff they previously had `amount_of_super_spines > 0`; pods (non-fabric-role) a `spine` design; racks a `leaf` design and, where they had L2 leaves, an `l2leaf` design.
- **FR-006**: Where the prior count was implicit (schema default), the migration MUST write the effective count explicitly; where the prior count was `0`, no design entry is created.

**Legacy field removal**

- **FR-007**: The legacy fields (`amount_of_super_spines`, `super_spine_switch_template`, `amount_of_spines`, `spine_switch_template`, `amount_of_leafs`, `leaf_switch_template`, `amount_of_l2leafs`, `l2leaf_switch_template`) MUST be removed from every migrated fabric/pod/rack object.
- **FR-008**: Removal MUST be coordinated with the schema no longer requiring those fields (005 Stage-3), so the load does not fail on the required pod/rack template relationships (see Dependencies).

**File Organization & Load Order**

- **FR-009**: Migrated files MUST keep their existing names and numeric ordering under `objects/`; no new load-order dependency is introduced (templates already load earlier in `06_device_template.yml`).
- **FR-010**: All template human_friendly_id references MUST resolve to `CoreObjectTemplate` objects defined in earlier-sorting files.

**Data Integrity**

- **FR-011**: `role` values MUST use the choice `name`, not a display label.
- **FR-012**: Re-loading the migrated files MUST be idempotent (designs keyed by `(container, role)` — no duplicates).
- **FR-013**: For an equivalent design, the migrated data MUST reproduce the same generated device set as the pre-migration seed data (parity).

**Population-Specific Requirements**

- **FR-014**: Every seed file that currently sets a legacy field MUST be migrated: `10_fabric.yml`, `10a_fabric_c_fabric.yml`, `11_rack.yml`, `11a_fabric_c_rack.yml`, `13a_fabric_l2ls.yml`, `13b_fabric_campus.yml`, `13c_fabric_isis_ldp.yml`, `14_fabric_single_dc_l3ls.yml`, and any other file a repository scan finds referencing the legacy fields.
- **FR-015**: The migration MUST NOT change any non-design attributes or relationships of the fabric/pod/rack objects (pools, MLAG, sorting methods, group memberships, hierarchy, etc.).

### Key Entities

- **NetworkFabricDeviceDesign** (new seed data): `super_spine` design on multi-tier fabrics; nested inline under each `NetworkFabric`.
- **NetworkPodDeviceDesign** (new seed data): `spine` design on each non-fabric-role pod; nested inline under each `NetworkPod` (itself a child of a fabric).
- **NetworkRackDeviceDesign** (new seed data): `leaf` (and optional `l2leaf`) design on each `LocationRack`; nested inline under each rack.
- **NetworkFabric / NetworkPod / LocationRack** (existing seed objects, modified): gain `device_designs`, lose the legacy per-role fields.
- **CoreObjectTemplate** (existing, referenced): the device templates (`super-spine-switch`, `spine-switch`, `leaf-switch-compute`, `l2leaf-switch`, and Dell/Fabric-C variants), referenced by `template_name`; defined in `06_device_template.yml` / `06a_fabric_c_device_templates.yml`.

### Key Files

- `objects/10_fabric.yml`, `objects/10a_fabric_c_fabric.yml` — fabrics + nested pods.
- `objects/11_rack.yml`, `objects/11a_fabric_c_rack.yml` — racks.
- `objects/13a_fabric_l2ls.yml`, `objects/13b_fabric_campus.yml`, `objects/13c_fabric_isis_ldp.yml`, `objects/14_fabric_single_dc_l3ls.yml` — example fabrics/pods/racks.
- `objects/06_device_template.yml`, `objects/06a_fabric_c_device_templates.yml` — templates referenced by `device_designs` (unchanged, load earlier).
- `schemas/device_design.yml` and the 005 Stage-3 removals — the schema these objects conform to.

### Dependency Load Order

```
06_device_template.yml         -- CoreObjectTemplate (referenced by device_designs; unchanged)
10_fabric.yml / 10a_*          -- NetworkFabric + nested NetworkPod, each with device_designs
11_rack.yml / 11a_*            -- LocationRack with device_designs
13a_* / 13b_* / 13c_* / 14_*   -- example fabrics/pods/racks with device_designs
```

## Assumptions

- **Parity migration.** Each container's `device_designs` reproduces its current effective design; no fabric changes shape. Implicit default counts (spines/super-spines default 4, leafs default 1) are materialized explicitly.
- **Absence-means-none.** A role with prior count 0 (or a fabric-role pod with no spines) gets no design entry, matching the generator's absence handling.
- **Templates by HFID.** `device_template` references the `CoreObjectTemplate` `template_name`; templates already load earlier, so no re-ordering is needed.
- **Inline nested representation.** Device designs are written as inline `device_designs: {data: [...]}` under each container (mirroring how `spanning_tree_priorities` and pod `children` are already nested), rather than as separate top-level objects.
- **Clean end-state (drop legacy fields), co-loaded with Stage-3.** Seed files drop the legacy fields rather than dual-writing. Because pod `spine_switch_template` and rack `leaf_switch_template` are required in the Stage-1 schema, this requires the 005 Stage-3 removal (`state: absent`) to be applied on the same integration branch/load. *Alternative if a more decoupled merge is preferred:* keep the legacy fields populated alongside `device_designs` (dual-write) so the Stage-1 schema still validates, and remove them in a later cleanup — at the cost of temporarily redundant, drift-prone data.

## Dependencies & Out of Scope

- **Co-requisite — Generators (002)**: the generators read `device_designs`; this data populates it. They must land together (hard cutover).
- **Prerequisite/co-load — Schema Stage-3 removal (005 T020)**: to drop the required legacy relationships from seed data, the schema on the load branch must no longer require them. This cycle therefore lands with the 005 Stage-3 removal.
- **Prerequisite — Schema Stage-1 (001)**: `device_designs` must exist (done).
- **Out of scope**: any change to device templates, pools, MLAG, EVPN, server, or other non-design seed data; generator/transform code (002 and prior); schema definition (001).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The full `objects/` set loads without errors on a branch whose schema has `device_designs` and the legacy fields removed — no missing references, no validation failures.
- **SC-002**: Every seeded multi-tier fabric has a `super_spine` design; every non-fabric-role pod a `spine` design; every rack a `leaf` design (and an `l2leaf` design where it previously had L2 leaves).
- **SC-003**: No `amount_of_*` or `*_switch_template` legacy field remains in any migrated seed file.
- **SC-004**: All `device_template` references resolve to existing `CoreObjectTemplate` objects (no dangling references).
- **SC-005**: Re-loading the migrated files is idempotent — no duplicate `device_designs`.
- **SC-006**: Single-tier fabrics (prior `amount_of_super_spines: 0`) and the fabric-role pod have no super-spine/spine design entry.
- **SC-007**: Running the generator chain on the migrated data produces the same devices (names, roles, templates, counts) as the pre-migration baseline.
