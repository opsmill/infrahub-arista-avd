# Phase 0 Research: Device-Design-Driven Fabric Generators

All Technical Context unknowns resolved. Each decision records what was chosen, why, and the alternatives rejected. Grounded in the current generators (`generate_fabric.py`, `generate_pod.py`, `generate_rack.py`) and the 005 schema contract.

## Decision 1 — Shared `role → (template_id, quantity)` resolver on `GeneratorMixin`

**Decision**: Add one helper (e.g. `resolve_device_designs(design_edges) -> dict[str, tuple[str, int]]` and/or `device_design_for(design_edges, role) -> tuple[str | None, int]`) on `GeneratorMixin` in `src/solution_arista_avd/generator.py`. It reads a container's `device_designs` edges (from the typed query model), keys them by `role`, and returns `(template_id, device_quantity)`, defaulting to `(None, 0)` when a role has no design.

**Rationale**: All three generators, plus the two cross-tier completeness reads, perform the same lookup. Centralizing it satisfies the DRY guidance, keeps absence-means-none (Decision 5) in one place, and keeps each `generate()` under the Ruff C901 ≤17 complexity cap. `GeneratorMixin` already hosts shared generator utilities (`resolve_avd_pools`, checksum, hostvar triggering), so it is the natural home.

**Alternatives considered**:
- *Inline the lookup in each generator*: rejected — three-way duplication and three places for the absence rule to drift.
- *A free function in `avd.py`*: acceptable, but `GeneratorMixin` co-locates it with the other generator helpers the classes already inherit.

## Decision 2 — Migrate the two cross-tier completeness reads

**Decision**: Move the cross-tier reads to `device_designs`:
- `generate_pod.py` currently reads the parent fabric's `amount_of_super_spines` (to gate spine→super-spine cabling and to assert the fabric is fully generated). It will read the fabric's `device_designs[super_spine].device_quantity`.
- `generate_rack.py` currently reads the pod's `amount_of_spines` (to assert the pod is fully generated before cabling leaves to spines). It will read the pod's `device_designs[spine].device_quantity`.

The `.gql` queries fetch these via the existing nested `parent`/`pod` selections, now selecting the upstream container's `device_designs` instead of its legacy count field.

**Rationale**: These reads are the expected-device-count side of a "is the upstream tier fully generated?" guard (`expected != len(actual)` → raise). Once the count lives only in `device_designs`, the guard must source it there or it breaks. They are easy to miss because they read a *different* tier's legacy field than the generator's own.

**Alternatives considered**:
- *Count upstream devices instead of reading the design*: rejected — the guard's purpose is to compare the design's intent against what exists; dropping the design side removes the check's meaning.

## Decision 3 — Hard cutover, no legacy fallback

**Decision**: The generators read `device_designs` only. They do not fall back to the legacy fields when `device_designs` is empty.

**Rationale**: Matches the spec. A fallback would be transitional code deleted a cycle later, and it would mask un-migrated seed data (a fabric would silently generate from stale fields). The staged migration (001 Decision 8) keeps old and new fields coexisting at the *schema* level; the *generator* cutover is clean and pairs with the Objects cycle that populates `device_designs`. Branch isolation makes the cutover safe to validate before merge.

**Alternatives considered**:
- *Dual-read with fallback*: rejected — extra complexity, hides migration gaps, removed next cycle anyway.

## Decision 4 — Preserve the underlay role switch and the leaf/l2leaf slot split

**Decision**: Keep `LEAF_ROLE_BY_UNDERLAY` / `SPINE_ROLE_BY_UNDERLAY` exactly as today. The rack's `leaf` design feeds the primary-leaf creation (whose device role is still switched to `l2leaf`/`l2spine` for standalone-L2LS/campus underlays); the rack's `l2leaf` design remains the additional-L2-leaf slot (today's `amount_of_l2leafs`). Pod `spine` and fabric `super_spine` map directly to `create_spine_switches` / `create_super_spine_switches`.

**Rationale**: The design's `role` is the logical tier slot, not the final device role. The underlay switch is orthogonal fabric behavior that must not change. This preserves the current two-slot rack model and every generated device role.

**Alternatives considered**:
- *Treat the design `role` as the final device role (drop the underlay switch)*: rejected — would change generated device roles for standalone-L2LS/campus fabrics, violating the behavior-preserving constraint.

## Decision 5 — Absence-means-none, including primary roles; keep the count-zero guards

**Decision**: A role with no design resolves to quantity 0 and creates no devices. The existing "count == 0 → skip" branches are retained but driven by the resolved quantity:
- fabric: `super_spine` quantity 0 → skip super-spine creation (as `amount_of_super_spines == 0` does today);
- pod: fabric `super_spine` quantity 0 → skip super-spine cabling/guard (as today);
- rack: `l2leaf` quantity 0 → skip L2-leaf creation/cabling (as today), and a missing `leaf` design → 0 primary leaves (previously `amount_of_leafs` was mandatory ≥1).

**Rationale**: Reproduces every current zero-count code path from the design instead of the fixed field, and removes the special "0 means don't create" attribute handling. Making a missing `leaf` design 0-leaves (rather than an error) is consistent and lets seed data omit roles cleanly; seed data is expected to always supply a `leaf` design where leaves are wanted.

**Alternatives considered**:
- *Raise if a rack has no `leaf` design*: rejected — inconsistent with absence-means-none for every other role and unnecessary; a rack with no leaf design is simply empty of leaves.

## Decision 6 — Do not adopt `from_graphql` hydration in this cycle

**Decision**: Keep the current typed-query-model access pattern; do not refactor to `InfrahubNode.from_graphql()` hydration here.

**Rationale**: The generators already use generated typed query models and targeted `self.client.filters/get` calls; the `device_designs` read adds a small bounded relationship, not an N+1 re-fetch loop. Introducing a hydration refactor now would enlarge the diff and risk behavior drift in a cycle whose whole point is parity. Revisit as a separate optimization if profiling warrants.

**Alternatives considered**:
- *Refactor to `from_graphql` while here*: rejected for this behavior-preserving cycle — orthogonal optimization, bigger blast radius.

## Decision 7 — `.infrahub.yml` unchanged; regenerate query models

**Decision**: Leave `queries` and `generator_definitions` in `.infrahub.yml` as-is (names and file paths are stable). After editing each `.gql`, regenerate its `*_query.py` with `infrahubctl graphql generate-return-types` and use the regenerated model in `generate()`.

**Rationale**: Only query *contents* change, not their registered names/paths, so no registration edit is needed (registration rule). Regenerating the return types keeps typed access (Principle III) and surfaces any query/shape mismatch at generation time rather than runtime.

**Alternatives considered**:
- *Hand-edit the `*_query.py` models*: rejected — generated files must be regenerated, never hand-edited (Principle III).
