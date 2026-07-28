# Phase 1 Data Model: Normalized Device Design Entities

Conceptual data model for the schema change. YAML shapes are illustrative of the intended structure; the implementing agent authors the final YAML with the `infrahub-managing-schemas` skill and validates with `infrahubctl schema check`.

## Overview

```text
NetworkFabric ──(device_designs, Component many, cascade)──> NetworkFabricDeviceDesign ─┐
NetworkPod    ──(device_designs, Component many, cascade)──> NetworkPodDeviceDesign    ─┤ inherit_from
LocationRack  ──(device_designs, Component many, cascade)──> NetworkRackDeviceDesign   ─┘   │
                                                                                            v
                                                                                   NetworkDeviceDesign (generic)
                                                                                     • device_quantity : Number ≥1
                                                                                     • role            : Dropdown
                                                                                     • device_template ──(Attribute one, no-action)──> CoreObjectTemplate
```

## Generic: `NetworkDeviceDesign`

The reusable shape of a device design. Not instantiated directly.

| Field | Kind | Cardinality | Required | Notes |
|-------|------|-------------|----------|-------|
| `device_quantity` | Number (Attribute) | — | yes | `parameters: {min_value: 1}`. Count of devices of this design. |
| `role` | Dropdown (Attribute) | — | yes | Choices: `super_spine`, `spine`, `leaf`, `l2leaf` (mirrors `NetworkSpanningTreePriority`). Authoritative for downstream generation. |
| `device_template` | Relationship, `kind: Attribute` | one | yes | Peer `CoreObjectTemplate`. `on_delete: no-action` (template is shared, must survive). Identifier derived — see research Decision 5. |

Generic-level settings: `namespace: Network`, `include_in_menu: false`. `branch: agnostic` to match the container nodes (`NetworkFabric`, `NetworkPod`, `LocationRack` are all `branch: agnostic`).

Illustrative:

```yaml
generics:
  - name: DeviceDesign
    namespace: Network
    branch: agnostic
    include_in_menu: false
    display_label: role__value
    attributes:
      - name: role
        kind: Dropdown
        optional: false
        order_weight: 1000
        choices:
          - {name: super_spine, label: Super Spine, color: "#A9CCE3"}
          - {name: spine,       label: Spine,       color: "#A9DFBF"}
          - {name: leaf,        label: Leaf,        color: "#D2B4DE"}
          - {name: l2leaf,      label: L2 Leaf,     color: "#F9E79F"}
      - name: device_quantity
        kind: Number
        optional: false
        order_weight: 1100
        parameters: {min_value: 1}
    relationships:
      - name: device_template
        peer: CoreObjectTemplate
        kind: Attribute
        cardinality: one
        optional: false
        on_delete: no-action
        order_weight: 900
```

## Concrete nodes (one per tier)

All three `inherit_from: [NetworkDeviceDesign]`, add a `Parent` relationship to their container, and define per-tier `uniqueness_constraints` + `human_friendly_id`. They redefine no inherited attribute/relationship.

| Node | Parent relationship (`kind: Parent`, one, required) | Peer | Uniqueness | human_friendly_id |
|------|------------------------------------------------------|------|------------|-------------------|
| `NetworkFabricDeviceDesign` | `fabric` | `NetworkFabric` | `[["fabric", "role__value"]]` | `["fabric__name__value", "role__value"]` |
| `NetworkPodDeviceDesign` | `pod` | `NetworkPod` | `[["pod", "role__value"]]` | `["pod__name__value", "role__value"]` |
| `NetworkRackDeviceDesign` | `rack` | `LocationRack` | `[["rack", "role__value"]]` | `["rack__name__value", "role__value"]` |

Illustrative (fabric tier; pod/rack analogous):

```yaml
nodes:
  - name: FabricDeviceDesign
    namespace: Network
    branch: agnostic
    include_in_menu: false
    inherit_from: [NetworkDeviceDesign]
    uniqueness_constraints: [["fabric", "role__value"]]
    human_friendly_id: ["fabric__name__value", "role__value"]
    relationships:
      - name: fabric
        peer: NetworkFabric
        kind: Parent
        cardinality: one
        optional: false
        identifier: "fabric__device_designs"   # matches the Component side
        order_weight: 800
```

## Container relationships (added to existing nodes)

Each container gains a `device_designs` `Component` relationship (many, `on_delete: cascade`) whose `identifier` matches its child's `Parent` relationship. Added via the `extensions:` block so the whole feature reads from one file.

| Container | Relationship | Peer | identifier |
|-----------|--------------|------|------------|
| `NetworkFabric` | `device_designs` | `NetworkFabricDeviceDesign` | `fabric__device_designs` |
| `NetworkPod` | `device_designs` | `NetworkPodDeviceDesign` | `pod__device_designs` |
| `LocationRack` | `device_designs` | `NetworkRackDeviceDesign` | `rack__device_designs` |

Illustrative (fabric; pod/rack analogous):

```yaml
extensions:
  nodes:
    - kind: NetworkFabric
      relationships:
        - name: device_designs
          peer: NetworkFabricDeviceDesign
          kind: Component
          cardinality: many
          optional: true
          on_delete: cascade
          identifier: "fabric__device_designs"
          order_weight: 4000
```

## Removed fields (staged, `state: absent`)

Marked `state: absent` in the files that currently define them; **loaded only after** data migration and the follow-on generator/objects cycles (research Decision 8).

| Node | Field | Kind | Defined in | Replaced by |
|------|-------|------|------------|-------------|
| `NetworkFabric` | `super_spine_switch_template` | Relationship | `logical_design.yml` | design with `role: super_spine` |
| `NetworkFabric` | `amount_of_super_spines` | Number | `logical_design.yml` | that design's `device_quantity` |
| `NetworkPod` | `spine_switch_template` | Relationship | `logical_design.yml` | design with `role: spine` |
| `NetworkPod` | `amount_of_spines` | Number | `logical_design.yml` | that design's `device_quantity` |
| `LocationRack` | `leaf_switch_template` | Relationship | `location_extensions.yml` | design with `role: leaf` |
| `LocationRack` | `amount_of_leafs` | Number | `location_extensions.yml` | that design's `device_quantity` |
| `LocationRack` | `l2leaf_switch_template` | Relationship | `l3ls_extensions.yml` | design with `role: l2leaf` |
| `LocationRack` | `amount_of_l2leafs` | Number | `l3ls_extensions.yml` | that design's `device_quantity` |

## Validation rules (from spec requirements)

- **VR-1** (FR-010, Decision 7): `device_quantity` ≥ 1; a role with no devices has **no** design row.
- **VR-2** (FR-011): `role` ∈ {`super_spine`, `spine`, `leaf`, `l2leaf`}.
- **VR-3** (FR-020, FR-025): `device_template` required, cardinality one, `on_delete: no-action` (template survives design deletion).
- **VR-4** (FR-021, FR-024): each container↔design pair uses matching `identifier`; `LocationRack.device_designs` added via `extensions`.
- **VR-5** (FR-025): `device_designs` is `on_delete: cascade` (deleting a container deletes its designs).
- **VR-6** (FR-050): at most one design per `(container, role)`.
- **VR-7** (Decision 6): tier↔role validity (fabric→super_spine, pod→spine, rack→leaf/l2leaf) is **not** enforced in schema; deferred to generator/check logic.

## State transitions

Device design entities are static configuration data — no lifecycle state machine. Their only "transition" is the staged migration of the containers themselves:

```text
Stage 1 (additive):  container has BOTH old fields AND device_designs (empty)
Stage 2 (migrate):   device_designs populated from old field values (idempotent upsert by HFID)
Stage 3 (remove):    old fields state: absent; device_designs is the sole source of design intent
```
