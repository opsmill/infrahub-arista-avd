# Phase 1 Data Model: Device-Design-Driven Fabric Generators

This cycle introduces no new schema entities (those live in 001). The "data model" here is the **generator input model**: what each `.gql` query fetches from `device_designs`, and how each generator maps roles to `(template_id, quantity)`. Shapes are illustrative; the implementing agent authors final `.gql`/Python with the `infrahub-managing-generators` skill and regenerates `*_query.py`.

## Shared resolution (all three generators)

Given a container's `device_designs` edges, build a role→(template, quantity) map; absent role → `(None, 0)`.

```python
# src/solution_arista_avd/generator.py  (on GeneratorMixin)
def resolve_device_designs(design_edges) -> dict[str, tuple[str | None, int]]:
    """role -> (device_template_id, device_quantity). Absent role is simply missing from the map."""
    resolved: dict[str, tuple[str | None, int]] = {}
    for edge in design_edges:
        node = edge.node
        template = node.device_template.node
        resolved[node.role.value] = (template.id if template else None, node.device_quantity.value)
    return resolved

def device_design_for(design_edges, role) -> tuple[str | None, int]:
    """(template_id, quantity) for one role; (None, 0) if absent (absence-means-none)."""
    return resolve_device_designs(design_edges).get(role, (None, 0))
```

## `device_designs` selection (each container node)

Every generator query selects this on its container (and, where noted, on the upstream container):

```graphql
device_designs {
  edges {
    node {
      role { value }
      device_quantity { value }
      device_template { node { __typename id } }
    }
  }
}
```

## Per-generator mapping

### Fabric — `generate_fabric` (own tier only)

| Was | Now |
|-----|-----|
| `amount_of_super_spines { value }` | `device_designs` → `device_design_for(…, "super_spine")` → quantity |
| `super_spine_switch_template { node { id } }` | same design → template_id |

- `create_super_spine_switches`: `(template, qty) = device_design_for(fabric.device_designs, "super_spine")`; `qty == 0` → skip (was `amount_of_super_spines == 0`); `qty > 0` and `template is None` → raise (was "no super-spine template").

### Pod — `generate_pod` (own tier + cross-tier read of fabric)

| Was | Now |
|-----|-----|
| pod `amount_of_spines` | pod `device_designs` → `device_design_for(…, "spine")` → quantity |
| pod `spine_switch_template` | same design → template_id |
| **parent fabric** `amount_of_super_spines` (completeness guard + cabling gate) | **parent fabric** `device_designs` → `device_design_for(…, "super_spine")` → quantity |

- `create_spine_switches` uses the pod `spine` design (role still passed through `SPINE_ROLE_BY_UNDERLAY`).
- The `fabric_amount_of_super_spines` guard (`!= len(super_spine_switches)` → raise) and the `connect_spine_to_super_spine` gate use the fabric super-spine **design quantity**.

### Rack — `generate_rack` (own tier + cross-tier read of pod)

| Was | Now |
|-----|-----|
| rack `amount_of_leafs` | rack `device_designs` → `device_design_for(…, "leaf")` → quantity |
| rack `leaf_switch_template` | same design → template_id |
| rack `amount_of_l2leafs` | rack `device_designs` → `device_design_for(…, "l2leaf")` → quantity |
| rack `l2leaf_switch_template` | same design → template_id |
| **pod** `amount_of_spines` (completeness guard) | **pod** `device_designs` → `device_design_for(…, "spine")` → quantity |

- `create_leaf_switches` uses the rack `leaf` design (role still passed through `LEAF_ROLE_BY_UNDERLAY`); MLAG pairing keyed off leaf count unchanged.
- `create_l2leaf_switches` uses the rack `l2leaf` design; `qty == 0` or no template → skip (as today).
- The `pod_amount_of_spines` guard (`!= len(spine_switches)` → raise) uses the pod spine **design quantity**.

## Validation rules (from spec requirements)

- **VR-1** (FR-002, FR-007): device count + template per role come from `device_designs`, matched on `role`; schema uniqueness guarantees ≤1 per role.
- **VR-2** (FR-008, Decision 5): absent role → quantity 0, no creation, no error — for every role including rack `leaf`.
- **VR-3** (FR-009, Decision 4): rack `leaf` → primary leaves (underlay-switched); rack `l2leaf` → additional L2 leaves; pod `spine`, fabric `super_spine` map directly.
- **VR-4** (Decision 2): cross-tier guards (pod←fabric super_spine qty, rack←pod spine qty) source the expected count from the upstream container's `device_designs`.
- **VR-5** (FR-010/011/012): `allow_upsert=True` retained; quantity-down / removed-design cleaned up by tracking; checksum short-circuit intact.
- **VR-6** (FR-005/006, Decision 7): legacy field selections removed from all three `.gql`; `*_query.py` regenerated, not hand-edited.

## State transitions

Generators are stateless transforms of design → devices. The only "transition" is convergence on re-run: increasing a design quantity creates the new devices (+ cabling/MLAG); decreasing it or removing a role's design triggers tracking cleanup of the excess; an unchanged design is a checksum no-op.
