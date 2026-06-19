# Schema Design Specification: Schema-Driven AVD IP Pools

> **This is a schema design spec.** The implementing agent MUST use the `infrahub-managing-schemas` skill to build and validate all schema definitions.

**Feature Branch**: `015-schema-driven-ip-pools`
**Created**: 2026-06-19
**Status**: Draft
**Input**: User description: "Replace the hardcoded fallback IP pools (10.250.0.0/16, 10.251.0.0/24, 10.255.0.0/24) in the AVD hostvar generator with required, schema-driven fabric/pod IP pool attributes that fail loudly when unset."

## Schema Files

All schema definitions live in `schemas/*.yml`. Each file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

The relevant nodes (`NetworkFabric`, `NetworkPod`) are defined in `schemas/logical_design.yml`. This feature adds relationships to those existing nodes (inline or via an `extensions` block). The downstream generator changes that consume these pools are **out of scope** for this schema cycle and will be specified in a follow-up `/speckit.specify` run for the generator artifact.

---

## Background & Problem Statement

The AVD hostvar generator (`generators/generate_avd_device_hostvar.py`) emits per-device pyAVD hostvars. Three IP pools are currently sourced from hardcoded literals instead of from the data model:

| pyAVD field | Hardcoded literal | Generator location | Intended source |
|-------------|-------------------|--------------------|-----------------|
| `uplink_ipv4_pool` | `10.250.0.0/16` | `generate_avd_device_hostvar.py:383` | `fabric.uplink_pool` (relationship exists in `l3ls_extensions.yml` but is `optional`; literal fires when unset) |
| `vtep_loopback_ipv4_pool` | `10.251.0.0/24` | `generate_avd_device_hostvar.py:384` | `fabric.vtep_pool` (relationship exists in `l3ls_extensions.yml` but is `optional`; literal fires when unset) |
| `loopback_ipv4_pool` | `10.255.0.0/24` | `generate_avd_device_hostvar.py:523` | not wired to any relationship at all |

Four of these relationships (`uplink_pool`, `vtep_pool` on the fabric; `mlag_peer_pool`, `mlag_l3_pool` on the pod) DO already exist — defined in `schemas/l3ls_extensions.yml` as `optional: true`. The literals fire only when an optional relationship is left empty (e.g. Fabric-B sets no uplink/vtep pool). The loopback pool (`loopback_ipv4_pool`, line 523) is the one pool wired to no relationship at all, and its `10.255.0.0/24` literal overlaps the management subnet.

Because these literals can collide with real customer networks and a `/24` is thin for a multi-pod fabric, the pools must become first-class, schema-modeled relationships that the model can require and validate, rather than implicit fallbacks buried in generator code.

This spec covers **only the data-model change**: defining the pool relationships on `NetworkFabric` and `NetworkPod` so that the pools are explicit, discoverable in the UI, and enforceable. The generator behavior (reading the new relationships, removing the literals, raising a clear error when a required pool is unset) is a separate downstream cycle.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Model fabric-level underlay/overlay IP pools (Priority: P1)

A network operator configuring a new fabric must be able to assign, directly on the `NetworkFabric` object, the IP prefix pools used for point-to-point uplinks and for VTEP loopbacks, plus the prefix pool used to allocate device loopback addresses. These replace the `10.250.0.0/16`, `10.251.0.0/24`, and `10.255.0.0/24` literals.

**Why this priority**: These three fabric-level pools are the source of every underlay/overlay IP in the fabric. Without them modeled, the generator cannot produce correct, collision-free addressing for any device — this is the core of the feature.

**Independent Test**: Add the pool relationships to `NetworkFabric`, run `infrahubctl schema check schemas/`, load the schema, and confirm in the UI that a fabric can be linked to existing `CoreIPPrefixPool` / `CoreIPAddressPool` objects via the new relationships.

**Acceptance Scenarios**:

1. **Given** the schema is loaded, **When** an operator opens a `NetworkFabric` in the UI, **Then** relationship fields for the uplink pool, the VTEP loopback pool, and the device loopback pool are present and can be linked to existing IP pool objects.
2. **Given** a fabric with all required pools linked, **When** the fabric is queried over GraphQL, **Then** each pool relationship resolves to a pool node whose first resource prefix is retrievable (matching the existing `_extract_pool_prefix` access pattern in the generator).
3. **Given** the pools are required, **When** an operator attempts to create or save a fabric without them, **Then** the platform rejects the operation rather than silently allowing an unaddressed fabric.

---

### User Story 2 - Model pod-level MLAG IP pools (Priority: P2)

An operator configuring a pod that uses MLAG leaf pairs must be able to assign, on the `NetworkPod` object, the IP address pools for the MLAG peer link and for the MLAG L3 peering, so the generator can emit `mlag_peer_ipv4_pool` and `mlag_peer_l3_ipv4_pool` from data rather than leaving them empty.

**Why this priority**: MLAG pools are required for leaf pairs but not for every fabric topology, so they are second to the fabric-wide underlay pools. They are also the relationships the generator already *expects* (`pod.mlag_peer_pool`, `pod.mlag_l3_pool`) but that are missing from the schema.

**Independent Test**: Add the two pod relationships, run `infrahubctl schema check schemas/`, load, and confirm a `NetworkPod` can be linked to `CoreIPAddressPool` objects for both MLAG pools.

**Acceptance Scenarios**:

1. **Given** the schema is loaded, **When** an operator opens a `NetworkPod` in the UI, **Then** relationship fields for the MLAG peer pool and MLAG L3 peer pool are present.
2. **Given** a pod with both MLAG pools linked, **When** the pod is queried over GraphQL, **Then** both relationships resolve under names the generator can read (the relationship name is chosen to be stable despite Pydantic `l3` → `l_3` mangling).

---

### User Story 3 - Seed data and existing fabrics carry valid pools (Priority: P3)

The seed/object data under `objects/` and any existing fabrics must reference real IP pool objects for the new relationships, so that loading the project end-to-end produces a fabric that generates configs without relying on any hardcoded fallback.

**Why this priority**: Modeling the relationships is only useful if the shipped example data actually populates them; otherwise the feature regresses the out-of-the-box experience. This depends on stories 1 and 2 being complete.

**Independent Test**: Run `inv load` (or the schema + object load path) and confirm the seeded fabrics/pods have all required pools populated and pass `infrahubctl schema check`.

**Acceptance Scenarios**:

1. **Given** the new schema relationships, **When** the project objects are loaded, **Then** every seeded `NetworkFabric` and MLAG-using `NetworkPod` references valid pool objects (no missing-relationship errors).
2. **Given** required pools are enforced, **When** the full load runs, **Then** it completes without falling back to any `10.250` / `10.251` / `10.255` literal.

---

### Edge Cases

- **Existing data on a mandatory relationship**: if the pool relationships are introduced as mandatory (`optional: false`) on nodes that already have instances, what happens to fabrics/pods created before the change? (Drives the migration approach — see FR-060/FR-061.)
- **Pool exists but has no resources**: a linked pool with an empty `resources` list yields no prefix; the model permits the link but the downstream generator must treat "linked but empty" distinctly from "unlinked." (Schema cannot enforce non-empty resources; documented as a generator-cycle concern.)
- **Wrong pool kind linked**: an operator links a `CoreIPAddressPool` where a `CoreIPPrefixPool` is expected (or vice versa). The relationship `peer` kind must constrain this at the schema level.
- **MLAG pools on a non-MLAG pod**: pods without MLAG leaf pairs have no need for MLAG pools — these relationships must remain optional even if the fabric-level pools are mandatory.
- **Relationship naming vs Pydantic mangling**: `mlag_l3_pool` is auto-renamed to `mlag_l_3_pool` in generated Pydantic models. The relationship is NOT renamed (FR-014/FR-061); the generator's existing two-name getattr handling stays, and a typed-accessor cleanup is a generator-cycle item.
- **Duplicate pool assignment**: the same pool object linked to multiple fabrics — allowed or constrained? (Assumed allowed; pools are shared resources.)

## Requirements *(mandatory)*

### Functional Requirements

#### Nodes & Generics

- **FR-001**: The schema MUST add/modify the IP-pool relationships on the existing `NetworkFabric` and `NetworkPod` nodes via an `extensions.nodes` block in `schemas/l3ls_extensions.yml` — NOT by editing the original `schemas/logical_design.yml` (Constitution Principle I), and without redefining unrelated attributes of those nodes.
- **FR-002**: No new nodes or generics are required by this feature; the change is additive relationships on existing nodes.

#### Relationships

- **FR-010**: The existing `NetworkFabric.uplink_pool` relationship (`peer: CoreIPPrefixPool`, `identifier: fabric__uplink_pool`) MUST be changed from `optional: true` to `optional: false`. This makes the `10.250.0.0/16` literal source unreachable.
- **FR-011**: The existing `NetworkFabric.vtep_pool` relationship (`peer: CoreIPPrefixPool`, `identifier: fabric__vtep_pool`) MUST be changed from `optional: true` to `optional: false`. This makes the `10.251.0.0/24` literal source unreachable.
- **FR-012**: `NetworkFabric` MUST define a NEW relationship that supplies the device loopback prefix pool (the source for pyAVD `loopback_ipv4_pool`), with `peer: CoreIPPrefixPool`, `kind: Attribute`, `cardinality: one`, and a unique `identifier` (`fabric__loopback_pool`). This is the one genuinely missing relationship; it replaces the unconditional `10.255.0.0/24` literal at `generate_avd_device_hostvar.py:523`.
- **FR-013**: The existing `NetworkPod.mlag_peer_pool` relationship (`peer: CoreIPAddressPool`, `identifier: pod__mlag_peer_pool`, `optional: true`) is already correct and MUST remain optional (FR-021). No change required.
- **FR-014**: The existing `NetworkPod.mlag_l3_pool` relationship MUST remain optional and MUST NOT be renamed (a rename is a destructive migration; FR-061). The generator's `mlag_l_3_pool`/`mlag_l3_pool` getattr handling for Pydantic's `l3`→`l_3` mangling is retained; introducing a typed accessor is deferred to the generator cycle.
- **FR-015**: All new relationship `peer` values MUST use the full kind name (`CoreIPPrefixPool` for prefix pools, `CoreIPAddressPool` for address pools), consistent with the existing `asn_pool` / `loopback_pool` / `prefix_pool` relationships in the same file.
- **FR-016**: All new relationship names MUST be snake_case (pattern `^[a-z0-9\_]+$`, 3-32 chars), and each MUST carry a unique `identifier` so it does not collide with the existing pool relationships (`fabric__mgmt_pool`, `pod__loopback_pool`, `pod__prefix_pool`, etc.).
- **FR-017**: Each new relationship MUST set `branch: aware` and an `order_weight` that places it sensibly among the existing pool relationships (fabric pools in the 6000–9000 band, pod pools after the existing 6000/7000 entries).

#### Optionality & Enforcement

- **FR-020**: The fabric-level pools (`uplink_pool`, `vtep_pool`, loopback prefix pool) MUST be modeled as mandatory (`optional: false`) so the data model itself enforces their presence — this is the "fail loudly when unset" requirement expressed at the schema layer.
- **FR-021**: The pod-level MLAG pools (`mlag_peer_pool`, MLAG L3 pool) MUST remain optional (`optional: true`), because not every pod uses MLAG leaf pairs.
- **FR-022**: Where schema-level mandatory enforcement cannot fully cover a case (e.g., a linked-but-empty pool), the spec MUST record that the residual validation belongs to the downstream generator cycle (raise a clear error rather than fall back to a literal).

#### Display & Identification

- **FR-030**: Each new relationship MUST have a human-readable `label` (e.g., "Uplink Prefix Pool", "VTEP Loopback Pool", "Loopback Prefix Pool", "MLAG Peer Pool", "MLAG L3 Peer Pool") for the UI.
- **FR-031**: The change MUST NOT alter the existing `display_label` or `human_friendly_id` of `NetworkFabric` or `NetworkPod`.

#### Migration

- **FR-060**: Because `uplink_pool`, `vtep_pool`, and the loopback prefix pool are introduced as mandatory on nodes that may already have instances, the change MUST follow a safe migration path: add the relationships as optional, populate existing fabrics/pods and the seed data, then flip to mandatory — OR ship the mandatory relationships together with seed-data updates so a fresh load is internally consistent.
- **FR-061**: Existing pool relationships and attributes on `NetworkFabric` / `NetworkPod` MUST NOT be removed or renamed by this change; only additive relationships are introduced.

### Key Entities

- **NetworkFabric** (existing node; relationships live in `schemas/l3ls_extensions.yml`): ends with three mandatory IP-pool relationships pointing at `CoreIPPrefixPool` — `uplink_pool` and `vtep_pool` (already present, flipped to mandatory) plus a new `loopback_pool` (added). These are the data-model source for the three hardcoded literals.
- **NetworkPod** (existing node; relationships live in `schemas/l3ls_extensions.yml`): already carries two optional MLAG IP-address-pool relationships (`mlag_peer_pool`, `mlag_l3_pool`) pointing at `CoreIPAddressPool`. They remain optional and unchanged this cycle.
- **CoreIPPrefixPool / CoreIPAddressPool** (Infrahub built-in pool kinds): the peer targets; the generator extracts the first resource prefix from these (per the existing `_extract_pool_prefix` pattern), so the relationship shapes must remain compatible with that access path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `infrahubctl schema check schemas/` passes with zero validation errors after the new relationships are added.
- **SC-002**: After loading the schema, `NetworkFabric` shows the uplink, VTEP loopback, and device loopback pool relationship fields in the UI, and `NetworkPod` shows the two MLAG pool fields.
- **SC-003**: A `NetworkFabric` cannot be saved without its three mandatory pool relationships set (the platform rejects the operation), while a `NetworkPod` can be saved with the MLAG pools left empty.
- **SC-004**: The five pyAVD pool values (`uplink_ipv4_pool`, `vtep_loopback_ipv4_pool`, `loopback_ipv4_pool`, `mlag_peer_ipv4_pool`, `mlag_peer_l3_ipv4_pool`) are each traceable to a schema relationship — zero of them require a hardcoded literal as the only source.
- **SC-005**: The project seed data (`objects/`) loads end-to-end with every seeded fabric and MLAG-using pod referencing valid pool objects, with no missing-mandatory-relationship errors.
- **SC-006**: After the mandatory flip, all five pyAVD pool inputs are sourced from a schema relationship in the data model (the model no longer depends on any literal as the *only* source). NOTE: the generator code still contains the `10.250` / `10.251` / `10.255` literals — removing them and reading `fabric.loopback_pool` (so generated hostvars are literal-free) is a generator-cycle deliverable, tracked separately. That output-level verification is NOT in scope for this schema cycle.

## Assumptions

- The device loopback pool (source for pyAVD `loopback_ipv4_pool`) is modeled at the **fabric** level rather than the pod level, because the existing literal (`10.255.0.0/24`) was applied uniformly to all devices regardless of pod. (The existing `pod.loopback_pool` is a `CoreIPAddressPool` used for a different purpose and is left unchanged.) If per-pod loopback prefixes are required instead, this placement should be revisited during planning.
- The relationships use `kind: Attribute` (single, attribute-like ownership) consistent with every existing pool relationship on these nodes, not `kind: Component`.
- Removing the hardcoded literals, reading the new relationships, and raising a clear error when a required pool is unset are **generator-cycle** changes, specified separately after this schema cycle.
- Sharing a single pool object across multiple fabrics/pods is permitted (pools are shared resources); no uniqueness constraint is added for pool assignment.
