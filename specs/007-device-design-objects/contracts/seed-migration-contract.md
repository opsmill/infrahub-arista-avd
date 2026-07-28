# Seed Migration Contract: Device Designs

Per-file migration contract. Each listed file must, for every fabric/pod/rack it defines, replace the legacy fields with the equivalent `device_designs` block and remove the legacy fields. Consumers: the 006 generators (read `device_designs`) and the generator-chain parity check.

## Files in scope (8)

| File | Containers | Roles to populate | Notes |
|------|-----------|-------------------|-------|
| `objects/10_fabric.yml` | Fabric-A/B + nested pods | fabric `super_spine`; pods `spine` | **pods rely on default spine count 4 → materialize `device_quantity: 4`**; fabric-role pods get no spine design |
| `objects/10a_fabric_c_fabric.yml` | Fabric-C + pods | fabric `super_spine` (0 → omit); pods `spine` (2) | single-tier: `amount_of_super_spines: 0` → no super_spine design |
| `objects/11_rack.yml` | racks (many) | `leaf`, optional `l2leaf` | heaviest file (36 legacy occurrences); L2 leaves only where previously present |
| `objects/11a_fabric_c_rack.yml` | Fabric-C racks | `leaf` | |
| `objects/13a_fabric_l2ls.yml` | L2LS fabric/pod/rack | `super_spine` (0 → omit), `spine` (2), `leaf` | standalone L2LS |
| `objects/13b_fabric_campus.yml` | campus fabric/pod/rack | `super_spine` (0 → omit), `spine` (2), `leaf` | |
| `objects/13c_fabric_isis_ldp.yml` | ISIS-LDP fabric/pod/rack | `super_spine` (0 → omit), `spine` (2), `leaf` | |
| `objects/14_fabric_single_dc_l3ls.yml` | single-DC L3LS fabric/pod/rack | `super_spine`, `spine`, `leaf` | verify effective counts per object |

The implementer MUST re-scan `objects/` for any other file setting a legacy field and migrate it too (spec FR-014).

## Per-container output contract

For each container, after migration:
- Exactly one `device_designs` entry per role that had a prior effective count > 0.
- `role` = choice name (`super_spine`/`spine`/`leaf`/`l2leaf`); `device_quantity` = prior effective count (explicit or materialized default, ≥1); `device_template` = the prior `<role>_switch_template` HFID.
- No `amount_of_*` or `*_switch_template` field remains.
- Every other attribute/relationship byte-for-byte unchanged.

## Load contract (integration branch)

1. Schema loaded with `device_designs` (005 Stage-1) **and** legacy fields removed (005 Stage-3 `state: absent`).
2. `infrahubctl object load objects --branch <b>` succeeds — migrated data validates because the schema no longer requires the legacy relationships.
3. Re-load is a no-op (idempotent upsert by `(container, role)` HFID).

## Parity contract

Running the 006 generator chain on the migrated data produces the identical device set (names, roles, templates, counts, cabling, MLAG) as the pre-migration seed data. This is the acceptance gate (SC-007) and the guard against a mis-transcribed count or template.
