# Schema Contract: Device Design Entities

The schema surface this feature exposes to downstream consumers (generators, GraphQL queries, generated protocols, seed objects). Follow-on cycles depend on this contract; changes to it are breaking.

## New node kinds

| GraphQL kind | Type | Purpose |
|--------------|------|---------|
| `NetworkDeviceDesign` | Generic (interface) | Shared shape; query when tier-agnostic. |
| `NetworkFabricDeviceDesign` | Node | Fabric-tier design (super-spines). |
| `NetworkPodDeviceDesign` | Node | Pod-tier design (spines). |
| `NetworkRackDeviceDesign` | Node | Rack-tier design (leaf / l2leaf). |

## Field contract (all concrete design nodes, via the generic)

| Field | GraphQL shape | Contract |
|-------|---------------|----------|
| `role` | `role { value }` — enum of `super_spine`\|`spine`\|`leaf`\|`l2leaf` | Always present. Authoritative device role. |
| `device_quantity` | `device_quantity { value }` — Int ≥ 1 | Always present. Number of devices. |
| `device_template` | `device_template { node { id } }` — `CoreObjectTemplate`, cardinality one | Always present. The object template to clone. |
| container parent | `fabric`/`pod`/`rack` `{ node { id name { value } } }` | Always present (required Parent). |

## Container contract (added relationship)

Each of `NetworkFabric`, `NetworkPod`, `LocationRack` exposes:

```graphql
device_designs {
  edges {
    node {
      id
      role { value }
      device_quantity { value }
      device_template { node { id } }
    }
  }
}
```

- Cardinality: many. May be empty during Stage 1 migration.
- Cascade: deleting the container deletes its `device_designs`; the referenced `CoreObjectTemplate` is preserved.

## Natural key / identity contract

- Each design is uniquely identified by `(container, role)`.
- `human_friendly_id` = `<container-name>__<role>` (e.g. `fabric-a__super_spine`), usable directly in `objects/*.yml` relationship references and for HFID-based upsert in generators (Constitution Principle II).

## Migration contract (removed fields)

Downstream consumers MUST migrate off these fields; after Stage 3 they no longer exist:

| Kind | Removed field | Read instead |
|------|---------------|--------------|
| `NetworkFabric` | `super_spine_switch_template`, `amount_of_super_spines` | `device_designs` where `role == super_spine` → `device_template`, `device_quantity` |
| `NetworkPod` | `spine_switch_template`, `amount_of_spines` | `device_designs` where `role == spine` |
| `LocationRack` | `leaf_switch_template`, `amount_of_leafs` | `device_designs` where `role == leaf` |
| `LocationRack` | `l2leaf_switch_template`, `amount_of_l2leafs` | `device_designs` where `role == l2leaf` |

**"None of a role"**: previously `amount_of_*: 0` (e.g. `amount_of_l2leafs: 0`); now the **absence** of a design with that role. Generators MUST treat a missing role-design as "create zero devices of that role."

## Consumers to update (follow-on cycles)

- **Generator queries** (`generate_fabric.gql`, `generate_pod.gql`, `generate_rack.gql`): replace old-field selections with `device_designs`; regenerate `*_query.py`.
- **Generators** (`generate_fabric.py`, `generate_pod.py`, `generate_rack.py`): iterate `device_designs` by role instead of reading the fixed fields; preserve deterministic ordering and idempotence.
- **Protocols** (`src/solution_arista_avd/protocols.py`): regenerate after schema load.
- **Seed objects** (`objects/*.yml`): declare `device_designs` child entities instead of the paired fields.
