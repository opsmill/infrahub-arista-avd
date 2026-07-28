# Generator Specification: Device-Design-Driven Fabric Generators

> **Workflow type**: Infrahub Generator (design-driven automation)
> **Skill**: Use the `infrahub-managing-generators` skill to implement this specification.

**Feature Branch**: `006-device-design-generators`
**Created**: 2026-07-24
**Status**: Draft
**Input**: User description: "Update the fabric, pod, and rack generators and their GraphQL queries and generated query models to read the new `device_designs` relationship per role (super_spine, spine, leaf, l2leaf) instead of the legacy per-role template/quantity fields. Preserve generator idempotence, deterministic ordering, and role-driven device naming, cabling, and MLAG logic. Treat absence of a role's design as zero devices of that role."

## Generator Overview

This is the **Generator** follow-on cycle to `005-device-design-entities` (the schema cycle). The schema now exposes a normalized `device_designs` relationship on `NetworkFabric`, `NetworkPod`, and `LocationRack` — each design being a `(role, device_quantity, device_template)` entity (see `specs/005-device-design-entities/contracts/schema-contract.md`). This cycle rewires the three fabric generators to **read the device count and object template per role from `device_designs`** instead of the legacy paired fields, while preserving every downstream behavior (device naming, cabling, MLAG pairing, pool allocation, hostvar triggering, idempotence).

This cycle changes **how the generators source their inputs**; it does not change what devices are produced for an equivalent design.

**Design Object (Source)**: `NetworkFabric`, `NetworkPod`, `LocationRack` — each now carrying a `device_designs` many relationship of device design entities (`NetworkFabricDeviceDesign` / `NetworkPodDeviceDesign` / `NetworkRackDeviceDesign`).

**Generated Objects (Targets)**: unchanged — `DcimDevice` (spines, super-spines, leaves, L2 leaves), their `DcimInterface`s, cabling `NetworkLink`s, `MlagDomain`s, and allocated pool resources.

**Target Groups**: unchanged — `fabrics` (`generate-fabric`), `pods` (`generate-pod`), `racks` (`generate-rack`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rack generator reads device designs (leaf + L2 leaf) (Priority: P1)

As a network engineer, when I define a rack's leaf and L2-leaf devices as `device_designs` (role `leaf` × N, role `l2leaf` × M), I want the rack generator to create exactly those switches — the same devices it produced from `amount_of_leafs`/`leaf_switch_template` and `amount_of_l2leafs`/`l2leaf_switch_template` before — so the rack model is normalized without changing the generated fabric.

**Why this priority**: The rack generator is the busiest of the three (leaf creation, MLAG pairing, spine/L2-leaf cabling) and the tier with two device roles, so it exercises the full per-role read. It is the concrete case in the original request.

**Independent Test**: On a branch with device designs populated, run `generate-rack` for one rack and confirm the same leaf and L2-leaf `DcimDevice`s (names, roles, templates, count) are produced as with the legacy fields, and a re-run makes no changes.

**Acceptance Scenarios**:

1. **Given** a rack with a `leaf` design (`device_quantity` 2, a leaf template) and an `l2leaf` design (`device_quantity` 1, an L2-leaf template), **When** `generate-rack` runs, **Then** 2 leaf switches and 1 L2-leaf switch are created with the same names, roles, and templates the legacy fields produced.
2. **Given** the rack generator has already run, **When** it runs again with no design change, **Then** no duplicate or changed objects result (idempotent upsert).
3. **Given** a rack with **no** `l2leaf` design, **When** `generate-rack` runs, **Then** no L2-leaf switches are created (absence-means-none, replacing `amount_of_l2leafs: 0`).
4. **Given** a standalone-L2LS fabric (underlay `none`), **When** `generate-rack` runs for a rack with a `leaf` design, **Then** the underlay-based role switch still applies (primary leaves become role `l2leaf`) exactly as today.

---

### User Story 2 - Pod and fabric generators read device designs (spine, super-spine) (Priority: P2)

As a network engineer, when I define a pod's spines and a fabric's super-spines as `device_designs`, I want the pod and fabric generators to create the same spine and super-spine switches they created from `amount_of_spines`/`spine_switch_template` and `amount_of_super_spines`/`super_spine_switch_template`.

**Why this priority**: Completes the uniform read across all three tiers; depends on the per-role read proven in US1 but is structurally simpler (one role per tier).

**Independent Test**: On a branch with designs populated, run `generate-pod` and `generate-fabric` and confirm the same spine / super-spine devices are produced as with the legacy fields, idempotently.

**Acceptance Scenarios**:

1. **Given** a pod with a `spine` design (`device_quantity` N, a spine template), **When** `generate-pod` runs, **Then** N spine switches are created with the same names, roles, and templates as before.
2. **Given** a fabric with a `super_spine` design (`device_quantity` M, a super-spine template), **When** `generate-fabric` runs, **Then** M super-spine switches are created as before.
3. **Given** a fabric with no `super_spine` design (e.g. a single-tier fabric that previously set `amount_of_super_spines: 0`), **When** `generate-fabric` runs, **Then** no super-spine switches are created.

---

### User Story 3 - Design changes re-drive generation idempotently (Priority: P3)

As an operator, when I change a device design (quantity up/down) or add/remove a role's design, I want re-running the generator to converge the fabric to the new design — creating new devices, and cleaning up devices no longer described — without duplicates or stale objects.

**Why this priority**: Idempotence and stale-cleanup are constitutional requirements (Principle II) and the main regression risk of the refactor; validated after the reads work.

**Independent Test**: Change a design's `device_quantity`, re-run the generator, and confirm the device count converges and no orphaned devices/relationships remain; then revert and re-run to confirm convergence back.

**Acceptance Scenarios**:

1. **Given** a rack whose `leaf` design quantity increases from 1 to 2, **When** `generate-rack` re-runs, **Then** the second leaf is created and MLAG pairing/cabling updates accordingly.
2. **Given** a rack whose `l2leaf` design is removed, **When** `generate-rack` re-runs, **Then** the previously generated L2-leaf switches are cleaned up (no orphans).
3. **Given** any generator re-run with unchanged designs, **When** it completes, **Then** the checksum/idempotence path reports no changes.

### Edge Cases

- **Empty `device_designs`**: a container with no designs generates no devices for those roles (replaces the `amount_of_*: 0` idiom); the generator must not error on an empty relationship.
- **Missing required design**: if a rack has no `leaf` design at all (previously `amount_of_leafs` was mandatory ≥1), the generator has no primary leaves — behavior must be defined (see Assumptions: treated as zero leaves, consistent with absence-means-none, not an error).
- **Duplicate role**: the schema forbids two designs of the same role per container (uniqueness), so the generator can assume at most one design per role.
- **Design template missing/dangling**: `device_template` is required by the schema; the generator surfaces a clear error if the referenced template cannot be resolved.
- **Quantity change downward**: reducing a design's quantity must clean up the now-excess devices via the existing tracking/cleanup path (no orphans).
- **Branch vs. main**: generators run on a branch during rollout; behavior must match main once merged.
- **Underlay role switch interaction**: the `leaf`/`spine` design roles still feed the underlay-based role switch (`LEAF_ROLE_BY_UNDERLAY` / `SPINE_ROLE_BY_UNDERLAY`); the design's `l2leaf` role remains the additional-L2-leaf slot.

## Requirements *(mandatory)*

### Functional Requirements

**Generator Class & Method**:

- **FR-001**: The three generators MUST continue to inherit from `infrahub_sdk.generator.InfrahubGenerator` and implement `async generate(self, data: dict) -> None`; class names, target groups, and registration are unchanged.
- **FR-002**: Each generator MUST derive its per-role device count and object template from the container's `device_designs` relationship (matching on `role`) rather than from the legacy paired fields.
- **FR-003**: The refactor MUST preserve all existing downstream behavior for an equivalent design: device naming (`<role>-<pod>-<rack>-<index>` etc.), interface-role cabling filters, MLAG pairing and shared-ASN allocation, pool allocations, `generation_complete` flagging, and hostvar-generation triggering.

**GraphQL Query & Generated Models**:

- **FR-004**: Each generator query MUST be updated to fetch `device_designs { edges { node { role { value } device_quantity { value } device_template { node { id } } } } }` on its container, replacing the legacy field selections.
- **FR-005**: The generated query models (`generators/*_query.py`) MUST be regenerated from the updated `.gql` files (never hand-edited) and used as the typed access path (Constitution Principle III).
- **FR-006**: The rack query MUST stop selecting `amount_of_leafs`, `leaf_switch_template`, `amount_of_l2leafs`, `l2leaf_switch_template`; the pod query MUST stop selecting `amount_of_spines`, `spine_switch_template`; the fabric query MUST stop selecting `amount_of_super_spines`, `super_spine_switch_template`.

**Per-role resolution**:

- **FR-007**: Each generator MUST resolve a role's `(template_id, quantity)` by selecting the single `device_designs` entry whose `role` matches; the schema uniqueness constraint guarantees at most one per role.
- **FR-008**: A role with **no** matching design MUST be treated as **zero** devices of that role (no creation, no error), replacing the previous `amount_of_*: 0` handling.
- **FR-009**: The rack generator MUST map the `leaf` design to the primary leaf switches (still subject to the underlay role switch) and the `l2leaf` design to the additional L2-leaf switches (as the current `amount_of_l2leafs` slot does).

**Idempotence & Cleanup**:

- **FR-010**: All `save()` calls MUST retain `allow_upsert=True`; repeated runs with an unchanged design MUST produce no duplicate or changed objects.
- **FR-011**: When a design's quantity decreases or a role's design is removed, re-running the generator MUST clean up the now-unused generated devices and their relationships via the existing tracking mechanism (no orphans).
- **FR-012**: The existing checksum / change-detection path MUST continue to short-circuit no-op re-runs.

**Registration**:

- **FR-013**: The `generator_definitions` and `queries` entries in `.infrahub.yml` MUST remain valid; if query file contents change but paths/names do not, no `.infrahub.yml` edit is required.

### Key Entities

- **NetworkFabricDeviceDesign / NetworkPodDeviceDesign / NetworkRackDeviceDesign** (source input, from 001): the per-role design entities the generators now read — `role`, `device_quantity`, `device_template` → `CoreObjectTemplate`.
- **DcimDevice** (generated, unchanged): the spine/super-spine/leaf/l2leaf switches; role, index, name, and template assignment are unchanged for an equivalent design.
- **DcimInterface / NetworkLink / MlagDomain / pool resources** (generated, unchanged): produced by the same downstream logic.

### Key Files

| File | Purpose |
|------|---------|
| `generators/generate_rack.py` | Rack generator — read `device_designs` for `leaf` + `l2leaf` |
| `generators/generate_rack.gql` | Rack query — select `device_designs`, drop legacy fields |
| `generators/rack_generator_query.py` | Regenerated typed model for the rack query |
| `generators/generate_pod.py` | Pod generator — read `device_designs` for `spine` |
| `generators/generate_pod.gql` | Pod query — select `device_designs`, drop legacy fields |
| `generators/pod_generator_query.py` | Regenerated typed model for the pod query |
| `generators/generate_fabric.py` | Fabric generator — read `device_designs` for `super_spine` |
| `generators/generate_fabric.gql` | Fabric query — select `device_designs`, drop legacy fields |
| `generators/fabric_generator_query.py` | Regenerated typed model for the fabric query |
| `.infrahub.yml` | Verify query/generator registrations remain valid |
| `tests/unit/` | Unit tests for the per-role resolution and absence-means-none logic |

## Assumptions

- **Behavior-preserving refactor.** For an equivalent design, the generators produce the identical fabric (same devices, names, roles, cabling, MLAG). This cycle only changes the input source, not the output.
- **Design role vs. device role.** A rack's `leaf` design drives the primary leaf switches and still passes through the underlay role switch (`leaf`→`l2leaf` for standalone L2LS); the `l2leaf` design is the additional-L2-leaf slot (today's `amount_of_l2leafs`). Pod `spine` and fabric `super_spine` map directly. This preserves current behavior exactly.
- **Absence-means-none, including primary roles.** A missing design for any role means zero devices of that role and is not an error, even for the rack `leaf` role that was previously mandatory (≥1). Seed data is expected to always provide a `leaf` design where leaves are wanted.
- **Hard cutover, no legacy fallback.** The generators read `device_designs` only; they do not fall back to the legacy fields. This avoids transitional cruft and depends on the Objects cycle populating `device_designs` (see Dependencies).
- **At most one design per role.** Guaranteed by the schema uniqueness constraint from 001, so the generator can select a role's design unambiguously.

## Dependencies & Out of Scope

- **Co-requisite — Objects cycle**: the generators read `device_designs`, which must be **populated** for devices to be produced. The follow-on **Objects** cycle migrates the numbered seed files (`objects/10_fabric.yml`, `objects/11_rack.yml`, `objects/10a_*`, `objects/11a_*`, `objects/13a_*`, `objects/13b_*`, `objects/13c_*`, `objects/14_*`) from the legacy paired fields to `device_designs`. This Generator cycle and the Objects cycle MUST land together (a fabric with un-migrated seed data would generate nothing once generators stop reading the legacy fields).
- **Prerequisite — Schema cycle (001)**: complete; the `device_designs` relationship and design nodes exist.
- **Gated follow-on — Stage-3 schema removal**: marking the legacy fields `state: absent` (spec 005, T020) happens only after this Generator cycle and the Objects cycle are merged, on a dedicated removal branch. Removing them is **out of scope** here.
- **Out of scope**: hostvar/structured-config generators and transforms (they read device/role data, not the container design fields) unless a specific field reference is found during implementation; changing what devices are produced; tier↔role validation (a possible future Check cycle).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a rack with `leaf`×2 and `l2leaf`×1 designs, `generate-rack` produces the same set of `DcimDevice`s (names, roles, templates, count) as the pre-refactor generator did from the equivalent legacy fields.
- **SC-002**: Running any of the three generators twice on an unchanged design produces no duplicate or changed objects (idempotent upsert).
- **SC-003**: `generate-pod` and `generate-fabric` produce the same spine and super-spine devices as before for equivalent designs.
- **SC-004**: A container with no design for a given role produces zero devices of that role and does not error.
- **SC-005**: Decreasing a design's quantity or removing a role's design cleans up the excess/orphaned devices on re-run (no orphans).
- **SC-006**: The three generator queries no longer reference the legacy fields; `generators/*_query.py` are regenerated from the `.gql` files and used as the typed access path.
- **SC-007**: Each generator can be exercised locally with `uv run infrahubctl generator <name> --target <object-name>` on a branch with populated designs, and generator idempotence is validated (`$infrahub-test-generator-idempotence` when live validation is permitted).
