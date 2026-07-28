# Phase 1 Data Model: Device-Design Seed Data Migration

No new schema entities (those are in 001). The "data model" here is the **shape of the migrated seed data**: the inline `device_designs` block on each container and the parity mapping from the legacy fields. YAML is illustrative; the implementing agent authors final files with the `infrahub-managing-objects` skill.

## `device_designs` entry shape (all tiers)

```yaml
device_designs:
  kind: <NetworkFabricDeviceDesign | NetworkPodDeviceDesign | NetworkRackDeviceDesign>  # optional (peer is concrete)
  data:
    - role: <super_spine | spine | leaf | l2leaf>   # choice NAME
      device_quantity: <int ≥ 1>                     # explicit; materialize prior defaults
      device_template: <template_name>               # CoreObjectTemplate HFID
```

## Parity mapping (legacy field → design entry)

| Tier | Legacy fields | Migrated design (when count > 0) |
|------|---------------|----------------------------------|
| `NetworkFabric` | `amount_of_super_spines: N` + `super_spine_switch_template: T` | `{role: super_spine, device_quantity: N, device_template: T}` |
| `NetworkPod` | `amount_of_spines: M` (or default 4) + `spine_switch_template: T` | `{role: spine, device_quantity: M, device_template: T}` |
| `LocationRack` | `amount_of_leafs: L` + `leaf_switch_template: T` | `{role: leaf, device_quantity: L, device_template: T}` |
| `LocationRack` | `amount_of_l2leafs: K` + `l2leaf_switch_template: T2` | `{role: l2leaf, device_quantity: K, device_template: T2}` |

**Count 0 (or absent) → no entry for that role.**

## Per-tier examples (illustrative)

Fabric (multi-tier), pods nested as today:

```yaml
- name: "Fabric-A"
  # ... unchanged attributes/pools/STP/mgmt ...
  device_designs:
    data:
      - {role: super_spine, device_quantity: 6, device_template: super-spine-switch}
  children:
    kind: NetworkPod
    data:
      - name: "Pod-A1"          # role: fabric → NO spine design
        role: "fabric"
        member_of_groups: ["pods"]
      - name: "Pod-A2"
        # ... unchanged pod attributes ...
        device_designs:
          data:
            - {role: spine, device_quantity: 4, device_template: spine-switch}   # default 4 materialized
        member_of_groups: ["pods"]
```

Rack (leaf + optional L2 leaf):

```yaml
- name: "Rack-A2-1"
  # ... unchanged rack attributes (pod, parent, rack_type, mlag, groups) ...
  device_designs:
    data:
      - {role: leaf,   device_quantity: 2, device_template: leaf-switch-compute}
      - {role: l2leaf, device_quantity: 1, device_template: l2leaf-switch}
- name: "Rack-A2-2"           # no L2 leaves → only a leaf design
  device_designs:
    data:
      - {role: leaf, device_quantity: 1, device_template: leaf-switch-compute}
```

## Effective-count materialization (Decision 2)

| Source file | Spine count source | Materialized `device_quantity` |
|-------------|--------------------|-------------------------------|
| `10_fabric.yml` pods | no `amount_of_spines` → schema default | **4** |
| `10a_fabric_c_fabric.yml`, `13a`, `13b`, `13c` | explicit `amount_of_spines: 2` | 2 |
| all racks | explicit `amount_of_leafs` | as written (1 or 2) |
| all fabrics | explicit `amount_of_super_spines` | as written (0 → omit) |

## Validation rules (from spec requirements)

- **VR-1** (FR-004): `role` uses the choice name; `device_quantity` ≥ 1; `device_template` is a `CoreObjectTemplate` HFID.
- **VR-2** (FR-005/006): a role's design exists iff its prior effective count was > 0; implicit defaults materialized explicitly.
- **VR-3** (FR-007/008): legacy fields removed from seed data; load occurs against a schema where they are removed (005 Stage-3).
- **VR-4** (FR-009/010): existing file numbering preserved; template HFIDs resolve to earlier-loaded `CoreObjectTemplate` objects.
- **VR-5** (FR-012): re-load is idempotent (designs keyed `(container, role)`).
- **VR-6** (FR-013/015): non-design attributes unchanged; generated devices match the pre-migration baseline.

## State transitions

Static seed data — no lifecycle. The migration itself is a one-way transform of each container object: legacy fields → `device_designs`. Re-loading the migrated files converges on the same graph state (upsert by HFID).
