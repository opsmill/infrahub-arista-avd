# Phase 0 Research: Normalized Device Design Entities

All Technical Context unknowns are resolved below. Each decision records what was chosen, why, and the alternatives rejected.

## Decision 1 — Generic + three concrete nodes (not one shared node)

**Decision**: Define a `NetworkDeviceDesign` **generic** holding the shared shape, and three **concrete** nodes — `NetworkFabricDeviceDesign`, `NetworkPodDeviceDesign`, `NetworkRackDeviceDesign` — that `inherit_from` it. Each concrete node is a `Component` child of exactly one container.

**Rationale**: An Infrahub `Parent` relationship targets a single peer kind, and a `Component`/`Parent` pair keys on a shared `identifier`. The three containers (`NetworkFabric`, `NetworkPod`, `LocationRack`) share no common parent generic — `NetworkFabric`/`NetworkPod` inherit `NetworkBuildingBlock`, while `LocationRack` inherits `LocationGeneric`. A single reused design node would need a single `container` relationship pointing at one kind, which cannot express "child of fabric OR pod OR rack." Extracting the duplicated shape into a generic and specializing per tier is the idiomatic Infrahub pattern (the schema skill's "duplicate shape → extract a generic" guidance) and mirrors the existing `NetworkSpanningTreePriority` precedent, which is a `(fabric, role)`-keyed `Component` child of `NetworkFabric`.

**Alternatives considered**:
- *Single `RackDeviceDesignEntity` reused across tiers* (user's literal phrasing): rejected — cannot model three distinct parents without a shared container generic.
- *Introduce a new `NetworkDeviceContainer` generic that `NetworkFabric`/`NetworkPod`/`LocationRack` all inherit, then one design node with a `container` relationship to it*: rejected — invasive change to three established nodes across two namespaces, with migration risk on already-loaded fabric/pod/rack data, for no functional gain over per-tier concrete nodes.

## Decision 2 — Explicit `role` attribute is authoritative

**Decision**: `role` is a first-class `Dropdown` on the generic with choices `super_spine`, `spine`, `leaf`, `l2leaf`. The generator reads it directly to drive device naming, cabling interface-role filters, MLAG pairing, and the underlay-based role switch.

**Rationale**: Confirmed with the user. The `generate_rack.py` pipeline is entirely role-driven (`LEAF_ROLE_BY_UNDERLAY`, `SPINE_ROLE_BY_UNDERLAY`, interface roles `"spine"`/`"leaf"`/`"server"`/`"mlag_peer"`, device names like `leaf-{pod}-{rack}-{index}`). The current code overrides the object template's own role, so template role values are **not** authoritative today. A first-class field keeps that logic intact, is self-documenting in the UI, and decouples role from fragile template-naming conventions. The choice set reuses the roles already enumerated on `NetworkSpanningTreePriority` for consistency.

**Alternatives considered**:
- *Derive role from the referenced `CoreObjectTemplate`*: rejected — templates carry no authoritative role signal for generation, and it would couple role resolution to template naming and give no clean input to the underlay role switch.

## Decision 3 — Ownership: `Component` + explicit `on_delete: cascade`

**Decision**: Each container's `device_designs` relationship is `kind: Component`, `cardinality: many`, with `on_delete: cascade` set **explicitly**. The matching child side is `kind: Parent`, `cardinality: one`, `optional: false`, sharing the same `identifier`. The `device_template` relationship (`kind: Attribute`, `cardinality: one`) is left at the default `on_delete: no-action`.

**Rationale**: A device design has no meaning without its container, so it should be deleted with it — but per the on-delete rule, `kind: Component` does **not** cascade by default (it defaults to `no-action`, orphaning children). The cascade must be declared. Conversely `CoreObjectTemplate` is a shared object referenced by many designs; it must survive design deletion, which the default `no-action` on `device_template` provides.

**Alternatives considered**:
- *Rely on `kind: Component` for cascade*: rejected — it does not cascade on its own; children would orphan on container delete.
- *`on_delete: cascade` on `device_template`*: rejected — would delete a shared template when one design is removed, breaking every other design and container using it.

## Decision 4 — Uniqueness `(container, role)` and human-friendly ID

**Decision**: Each concrete node sets `uniqueness_constraints: [[<container_rel>, "role__value"]]` and `human_friendly_id: [<container_rel>__name__value, role__value]` (e.g. `[["fabric", "role__value"]]` and `["fabric__name__value", "role__value"]`). These live on the **concrete** nodes, not the generic, because the container relationship name differs per tier.

**Rationale**: Matches current semantics — exactly one template per role per container today. It gives the generator a stable natural key for HFID-based upsert (Constitution Principle II) and produces a readable identifier ("fabric-a / super_spine"). Uniqueness format follows the rule: attributes use `__value`, relationships bare name. This is the `NetworkSpanningTreePriority` pattern applied per tier.

**Alternatives considered**:
- *Allow multiple designs of the same role per container*: rejected for now — no current use case, and it would remove the natural key the generator relies on. Can be relaxed later by adding a discriminator attribute to the constraint.
- *Put uniqueness/HFID on the generic*: not possible cleanly — the container relationship referenced differs per concrete node.

## Decision 5 — `device_template` relationship identifier

**Decision**: Define `device_template` once on the generic. Omit an explicit bidirectional `identifier` and let Infrahub derive it, since `CoreObjectTemplate` (a built-in) defines no matching inverse. Confirm via `infrahubctl schema check`; if inheritance across the three concrete kinds triggers an identifier collision against `CoreObjectTemplate`, fall back to per-concrete-node identifiers (`fabric_design__template`, `pod_design__template`, `rack_design__template`).

**Rationale**: The relationship is effectively unidirectional (no inverse on the built-in template), so a hand-chosen shared identifier adds collision risk across inherited kinds for no benefit. Deriving keeps it simple; the schema-check gate is the deterministic validator. The existing repo uses distinct identifiers per template relationship (`pod__spine_template`, etc.) because those are separate per-node relationships — with a generic, one inherited definition is cleaner.

**Alternatives considered**:
- *Single explicit shared identifier on the generic*: rejected pending validation — risks "duplicate identifier" across the three inheriting kinds pointing at the same peer.

## Decision 6 — Role validity per tier is enforced downstream, not in schema

**Decision**: The `role` dropdown offers all four values on every tier. Restricting fabric designs to `super_spine`, pod to `spine`, rack to `leaf`/`l2leaf` is enforced by generator/check logic, not the schema.

**Rationale**: The choice set lives on the shared generic and cannot be narrowed per concrete node without duplicating the attribute. Tier-appropriate role validation is behavioral, fits a check/generator, and keeps the generic uniform. A follow-on Check cycle can add a proposed-change guard ("fabric design role must be super_spine") if desired.

**Alternatives considered**:
- *Per-tier role dropdowns (override choices on each concrete node)*: rejected — duplicates the attribute, fights inheritance, and hard-codes tier/role coupling in the schema.

## Decision 7 — Quantity bounds

**Decision**: `device_quantity` is `Number`, `optional: false`, `parameters: {min_value: 1}`. No maximum in the schema. "Zero of a role" is represented by the **absence** of a design row (replacing `amount_of_*: 0`, e.g. `amount_of_l2leafs: 0`).

**Rationale**: A design that exists describes at least one device. The current leaf cap of 2 (for MLAG pairing) is a generator concern tied to MLAG logic, not a universal schema rule — keeping it out of the shared generic avoids baking a rack-leaf constraint into fabric/pod designs. Absence-means-none is cleaner than a zero-quantity row and removes the "0 → don't create the relationship" special case the generator currently handles for L2 leaves.

**Alternatives considered**:
- *`min_value: 0` and keep zero-quantity rows*: rejected — a zero-quantity design is meaningless data and reintroduces the special case.
- *Encode leaf max=2 on the generic*: rejected — tier/role-specific, belongs in generator/check logic.

## Decision 8 — Staged migration and rollout ordering

**Decision**: Three stages, rolled out on a dedicated branch and merged via proposed change:
1. **Additive** — load the new generic, concrete nodes, and `device_designs` relationships. Old fields remain. Safe to load at any time; existing data unaffected.
2. **Migrate data** — populate device design entities from existing container fields. For a live instance, a one-time idempotent SDK helper reads each container's old template/quantity fields and upserts the matching design (keyed by `(container, role)` HFID). For the reference repo, the follow-on Objects cycle rewrites the numbered seed files to the new structure.
3. **Remove** — mark the four template relationships and four quantity attributes `state: absent`. This load is **gated** behind completion of the follow-on generator and objects cycles, because generators still read the old fields until then.

**Rationale**: Removing a field while a generator or seed file still reads it breaks generation and risks data loss — hence FR-062's "introduce + migrate before remove." Splitting additive from destructive lets the additive schema land immediately (unblocking the generator/objects cycles to be written against the real new shape) while the destructive load waits until nothing reads the old fields. `state: absent` (not YAML deletion) ensures the columns are actually retired from the graph. Branch-first rollout gives a preview and per-step undo that a direct default-branch load does not.

**Alternatives considered**:
- *Single big-bang load (new nodes + removals together)*: rejected — breaks generators and seed loads mid-flight; no safe intermediate state.
- *Delete old fields from YAML instead of `state: absent`*: rejected — leaves retired columns attached to every existing object (migration-state-absent rule).
