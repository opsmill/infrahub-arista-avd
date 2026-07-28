# Generator I/O Contract: Device-Design-Driven Fabric Generators

Input/output contract for each generator after the refactor. Consumers: the generator trigger pipeline and the downstream hostvar/structured-config chain (which read the generated devices, unaffected here).

## Shared helper (on `GeneratorMixin`, `src/solution_arista_avd/generator.py`)

```
device_design_for(design_edges, role) -> (template_id: str | None, quantity: int)
```
- Returns the `(device_template_id, device_quantity)` for the single design matching `role`.
- Returns `(None, 0)` when no design has that role (absence-means-none).
- Schema uniqueness (001) guarantees at most one design per `(container, role)`.

## `generate-fabric` (target group `fabrics`)

- **Input**: `NetworkFabric.device_designs` (role `super_spine`), plus existing pools (`asn_pool`, `node_id_pool`, `mgmt_pool`, `FabricSupernetPool`).
- **Reads**: `super_spine` → `(template, qty)`.
- **Output** (unchanged): `qty` super-spine `DcimDevice`s named `ss-<fabric>-<idx>`, role `super_spine`, cloned from `template`; fabric loopback pools; pod checksums bumped.
- **Guards**: `qty == 0` → no super-spines; `qty > 0` with `template is None` → error.

## `generate-pod` (target group `pods`)

- **Input**: `NetworkPod.device_designs` (role `spine`) + parent `NetworkFabric.device_designs` (role `super_spine`, count only) + fabric underlay/sorting/pools.
- **Reads**: pod `spine` → `(template, qty)`; fabric `super_spine` → `(_, ss_qty)`.
- **Output** (unchanged): `qty` spine `DcimDevice`s named `spine-<pod>-<idx>`, role via `SPINE_ROLE_BY_UNDERLAY`; spine↔super-spine cabling when `ss_qty > 0`; rack checksums bumped.
- **Guards**: `ss_qty > 0` and `ss_qty != len(super_spine_switches)` → "fabric not fully generated"; `pod` template missing → error; `fabric`-role pod skipped.

## `generate-rack` (target group `racks`)

- **Input**: `LocationRack.device_designs` (roles `leaf`, `l2leaf`) + parent `NetworkPod.device_designs` (role `spine`, count only) + pod/fabric context (underlay, sorting, pools, MLAG).
- **Reads**: rack `leaf` → `(leaf_template, leaf_qty)`; rack `l2leaf` → `(l2_template, l2_qty)`; pod `spine` → `(_, spine_qty)`.
- **Output** (unchanged): `leaf_qty` leaf `DcimDevice`s named `leaf-<pod>-<rack>-<idx>`, role via `LEAF_ROLE_BY_UNDERLAY`; MLAG pairing when leaves ≥2 and MLAG enabled; leaf↔spine cabling; `l2_qty` L2-leaf devices + L2↔leaf cabling when `l2_qty > 0`; `generation_complete` flag; hostvar trigger when all racks done.
- **Guards**: `spine_qty != len(spine_switches)` → "pod not fully generated"; `l2_qty == 0` or no L2 template → skip L2 leaves; missing `leaf` design → `leaf_qty == 0` (no leaves, no error).

## Cross-cutting invariants

- **Idempotence**: every `save()` uses `allow_upsert=True`; unchanged designs are a checksum no-op; quantity-down / removed-design cleaned up via the generator tracking context (no orphans).
- **Typed access**: `generate()` reads through the regenerated `*_query.py` model; no untyped dict access; generated models are regenerated from `.gql`, never hand-edited.
- **Registration**: `.infrahub.yml` `queries`/`generator_definitions` unchanged (names/paths stable).
- **Parity**: for a design equivalent to the pre-refactor legacy fields, the produced device set (names, roles, templates, counts, cabling, MLAG) is identical.
