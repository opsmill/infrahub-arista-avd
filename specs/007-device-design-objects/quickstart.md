# Quickstart: Validate Device-Design Seed Migration

Runnable load + parity validation guide. Final YAML edits live in `tasks.md` and the implementation phase.

## Prerequisites

- Infrahub reachable (`uv run infrahubctl info` → ✅).
- An integration branch whose schema has `device_designs` (005 Stage-1) **and** the legacy fields removed (005 Stage-3 `state: absent`). Without Stage-3, the load fails on the required pod/rack template relationships.
- The 006 generators present (to run the parity check).
- Author edits with the `infrahub-managing-objects` skill.

## Capture the pre-migration baseline (before editing)

Record what the current seed data generates, to compare against after migration:

```bash
alias ihctl='uv run infrahubctl'
# On a baseline branch with the pre-migration objects + generators, capture the device set:
ihctl object get DcimDevice --branch <baseline> -o csv > /tmp/devices-before.csv   # names, roles
```

## Validate YAML + load

```bash
uv run yamllint objects/            # lint the edited files
ihctl branch create device-design-objects
# integration branch must already carry the 005 Stage-1 + Stage-3 schema:
ihctl object load objects --branch device-design-objects
```

**Expected**: load succeeds with no missing-reference or validation errors (SC-001). Query the new designs:

```bash
ihctl object get NetworkRackDeviceDesign --branch device-design-objects
ihctl object get NetworkPodDeviceDesign  --branch device-design-objects
ihctl object get NetworkFabricDeviceDesign --branch device-design-objects
```

## Acceptance checks (mapped to Success Criteria)

- **SC-002/006**: every multi-tier fabric has a `super_spine` design; every non-fabric-role pod a `spine` design; every rack a `leaf` design (+ `l2leaf` where it had L2 leaves); single-tier fabrics and the fabric-role pod have none.
- **SC-003**: `grep -rE "amount_of_|_switch_template" objects/` returns nothing on the migrated fabric/pod/rack files.
- **SC-004**: no dangling `device_template` references (load would error otherwise).
- **SC-005**: re-run `object load` → idempotent, no duplicate designs.

## Parity check (SC-007) — the key gate

Run the generator chain on the migrated data and diff against the baseline:

```bash
# trigger the fabric/pod/rack generators (or the e2e pipeline) on the migrated branch, then:
ihctl object get DcimDevice --branch device-design-objects -o csv > /tmp/devices-after.csv
diff <(sort /tmp/devices-before.csv) <(sort /tmp/devices-after.csv) && echo "PARITY OK"
```

**Expected**: identical device set (names, roles, templates, counts). The e2e suite (`tests/integration/test_e2e_pipeline.py`) exercises this generation path.

## Integration & merge gates (per constitution)

- `$infrahub-run-integration-tests` — full load + generator chain (records tested branch + commit).
- `$infrahub-test-generator-idempotence` — repeated generator runs on the migrated data, no-diff.
- `uv run invoke lint` (yamllint) clean.
- Merge the **whole normalization together** on one integration branch: 001 (Stage-1 + Stage-3) + 006 generators + 007 objects.

## Definition of done (this objects cycle)

- [ ] All 8 seed files migrated to `device_designs`; legacy fields removed.
- [ ] Implicit spine counts materialized (10_fabric pods → 4); zero-count roles omitted.
- [ ] `yamllint` clean; full `object load` succeeds on the integration branch; idempotent re-load.
- [ ] Generator-chain parity vs. the pre-migration baseline confirmed.
- [ ] Ready to merge together with 001 (Stage-1 + Stage-3) and 002.
