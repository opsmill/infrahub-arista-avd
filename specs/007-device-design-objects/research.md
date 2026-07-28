# Phase 0 Research: Device-Design Seed Data Migration

All Technical Context unknowns resolved. Grounded in the current seed files (`10_fabric.yml`, `11_rack.yml`, etc.), the 005 schema contract, and the objects skill's nesting/idempotence rules.

## Decision 1 — Inline nested `device_designs` under each container

**Decision**: Write device designs as an inline component block on each container: `device_designs: { data: [ {role, device_quantity, device_template}, ... ] }`. Include an explicit `kind:` on the wrapper (`NetworkFabricDeviceDesign` / `NetworkPodDeviceDesign` / `NetworkRackDeviceDesign`) for clarity, though the loader can infer it (the relationship peer is concrete per container).

**Rationale**: Matches the patterns already in these files — the fabric nests `spanning_tree_priorities: { data: [...] }` and its pods as `children: { kind: NetworkPod, data: [...] }`. Inline children are created with their parent in one loader pass, so no extra load-order dependency is introduced. The peer being concrete means `kind` is optional (children-components rule), but stating it removes ambiguity when reading three different design kinds across tiers.

**Alternatives considered**:
- *Separate top-level design objects referencing the container by HFID*: rejected — more verbose, splits a container's design across the file, and gains nothing since inline nesting is idempotent and already the house style.

## Decision 2 — Materialize implicit default counts explicitly

**Decision**: Where a pod/fabric relied on the schema **default** count, write the effective value explicitly as `device_quantity`. Concretely: the pods in `10_fabric.yml` set no `amount_of_spines` and relied on the default **4**, so their `spine` design gets `device_quantity: 4`. Pods/fabrics that set the count explicitly (`10a`, `13a`, `13b`, `13c` use `2`) carry that value.

**Rationale**: `device_quantity` is required with no default (min 1), so an implicit count cannot be carried implicitly — it must be materialized or the design is wrong/invalid. Reading the effective value per object (explicit value if present, else the schema default that applied) preserves parity.

**Alternatives considered**:
- *Assume a uniform count*: rejected — pods differ (4 in `10_fabric`, 2 in the example fabrics); each must be read from its source.

## Decision 3 — Zero-count roles become absent designs

**Decision**: A role whose prior count was `0` gets no `device_designs` entry. Applies to single-tier fabrics (`amount_of_super_spines: 0` in `10a`, `13a`, `13b`, `13c` → no `super_spine` design) and the `role: fabric` pod (no spine template → no `spine` design), and racks without L2 leaves (no `l2leaf` design).

**Rationale**: Matches the generator's absence-means-none handling (002) and the schema's `device_quantity ≥ 1` — a zero-quantity design is invalid and meaningless. This is the intended replacement for the old `amount_of_*: 0` idiom.

**Alternatives considered**:
- *Zero-quantity design entries*: rejected — invalid against the schema minimum and semantically empty.

## Decision 4 — Drop legacy fields, co-load with the 005 Stage-3 removal

**Decision**: The migrated seed files omit all legacy per-role fields. Because pod `spine_switch_template` and rack `leaf_switch_template` are **required** in the Stage-1 schema, the load must occur against a schema where those fields are removed (005 Stage-3 `state: absent`). This cycle therefore lands on the same integration branch as the Stage-3 removal (and the 006 generators).

**Rationale**: The initiative's goal is a normalized single source of truth; leaving legacy fields in the seed data (dual-write) invites drift and needs a later cleanup pass. Load-order on the integration branch is deterministic: (1) load schema with `device_designs` added and legacy fields `state: absent`; (2) load the migrated seed data using `device_designs` only. Step 1 removes the required legacy relationships, so step 2 validates.

**Alternatives considered**:
- *Dual-write (keep legacy fields alongside `device_designs`)*: viable and more decoupled (no Stage-3 dependency, Stage-1 schema validates), but leaves redundant, drift-prone data and requires a second edit later. Recorded in the spec as the fallback if a more incremental merge is preferred.

## Decision 5 — Reference templates by human_friendly_id

**Decision**: Each `device_template` references its `CoreObjectTemplate` by `template_name` (the HFID), e.g. `device_template: leaf-switch-compute`, mirroring how the legacy `leaf_switch_template: leaf-switch-compute` already referenced it.

**Rationale**: Same reference target and mechanism as today; the template objects load earlier (`06_device_template.yml` / `06a_fabric_c_device_templates.yml`), so references resolve. Cardinality-one relationship → scalar HFID.

**Alternatives considered**:
- *Reference by id*: rejected — seed data references by HFID throughout for portability across loads.

## Decision 6 — Preserve everything else; per-object read for correctness

**Decision**: Change only the design fields. All other attributes/relationships (pools, MLAG, EVPN, sorting methods, `member_of_groups`, hierarchy, pod `children` nesting) stay byte-for-byte. The implementer reads each container's current legacy values (or effective defaults) and writes the matching design, file by file.

**Rationale**: This is a mechanical, parity-preserving migration; the risk is silently changing counts/templates. Reading each object's actual values (rather than assuming) is the guard, verified by the generator-chain parity check.

**Alternatives considered**:
- *Scripted blanket transform*: could help but the per-file structures vary (nested pods, default vs explicit counts, L2-leaf presence); a careful per-object edit validated by parity is safer than a one-size regex.
