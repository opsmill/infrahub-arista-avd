# Quickstart: AVD Example Fabric Designs (schema cycle)

Branch-based validation for the schema surface added in this cycle. All commands
use `uv run`. Do the work on a dedicated branch, never the default branch.

## Prerequisites

- Infrahub reachable (`uv run infrahubctl info` shows Connection Status ✅).
- Working branch checked out: `005-avd-example-fabrics`.

## 1. Schema check

Add the new roles, underlay choices, and EVPN inputs per
[contracts/schema.md](./contracts/schema.md), then:

```bash
uv run infrahubctl schema check schemas/
```

Expected: zero validation errors. Existing role and fabric data remain valid
(all additions are optional/defaulted).

## 2. Load schema on a branch

```bash
uv run infrahubctl branch create av-example-fabrics-schema
uv run infrahubctl schema load schemas --branch av-example-fabrics-schema
```

Expected: schema loads cleanly; no migration failures on existing data.

## 3. Regenerate protocols and return types

Regenerate protocols **from the loaded branch**, not from local files:

```bash
uv run infrahubctl protocols --branch <branch> --out src/solution_arista_avd/protocols.py
```

:::warning Regeneration finding
`infrahubctl protocols --schemas schemas` (the form in the constitution) reads
only local schema files and produces a **reduced** file that drops the
server-generated `Profile*` and `Template*` classes (observed: 1993 → ~454 lines,
83 classes lost). Use `--branch <branch>` (reads the loaded schema from the
server, as `docs/.../extending.md` already documents) to reproduce the committed
structure. With `--branch`, the diff for this feature is exactly the two new
attributes (`evpn_gateway`, `evpn_vlan_aware_bundles`) propagated to the base,
`Profile*`, and `Template*` variants; new Dropdown role/underlay choices do not
change class structure. No generator query changed this cycle, so no GraphQL
schema / return-type regeneration is required.
:::

Expected: regenerated file includes the new inputs. Generated files are NOT
hand-edited.

## 4. Role → AVD node-type mapping

Extend `ROLE_TO_AVD_TYPE` in `src/solution_arista_avd/avd.py`, then:

```bash
uv run pytest tests/unit/test_avd.py
```

Expected: every schema role choice (`super_spine`, `spine`, `leaf`,
`border_leaf`, `l2leaf`, `l2spine`, `l3spine`, `p`, `pe`, `rr`, `wan_router`,
`wan_rr`) resolves to a non-empty AVD node type; unknown roles raise `ValueError`.

## 5. Schema contract tests

```bash
uv run pytest tests/unit/test_avd_example_fabrics_schema_contract.py
```

Expected assertions:

- New role choices exist with the specified machine names/labels.
- `underlay_routing_protocol` includes `none` and `isis-ldp` in addition to
  `ebgp`/`ospf`.
- `evpn_vlan_aware_bundles` and the EVPN DC Gateway flag exist with the specified
  kinds and safe defaults.
- Existing role/underlay machine values are unchanged.

## 6. Lint

```bash
uv run invoke lint
```

Expected: ruff, mypy, and yamllint pass with zero findings.

## 7. Regression: Single-DC L3LS unchanged

Confirm the already-supported baseline still renders identically:

```bash
uv run pytest tests/unit/test_avd.py tests/unit/test_hostvar_ordering.py
```

Expected: no change to Single-DC L3LS rendered output (SC-003).

## Per-scenario validation (follow-on cycles)

Full render + idempotence proof per scenario is completed in the generator and
objects cycles, per [contracts/escape-hatch.md](./contracts/escape-hatch.md):

1. Load the scenario seed design on a branch.
2. Run the full generator chain.
3. Confirm every device renders valid EOS config (zero PyAVD errors).
4. Confirm the rendered output demonstrates the scenario's defining capabilities.
5. Re-run generation; confirm no artifact diffs (idempotence), using
   `$infrahub-test-generator-idempotence` where live validation is permitted.

## Definition of done (schema cycle)

- [x] `schema check` passes; existing data valid. (EXIT=0; all 21 schemas Valid; schema loaded on branch `avd-example-fabrics-schema` with no migration errors.)
- [x] Protocols regenerated from the branch (not hand-edited); diff = the two new attributes only.
- [x] `ROLE_TO_AVD_TYPE` covers all new roles; unit test asserts full coverage (`test_schema_roles_all_mapped`, `test_every_role_maps_to_non_empty_type`).
- [x] Contract tests pass for roles, underlay choices, and EVPN inputs (`tests/unit/test_avd_example_fabrics_schema_contract.py`).
- [x] ruff / mypy / yamllint clean on changed files; full unit suite 302 passed.
- [x] Single-DC L3LS baseline output unchanged (existing `test_avd.py` / `test_hostvar_ordering.py` pass).
- [x] `docs/docs/supported-capabilities.md` and role-mapping/hostvars/extending docs updated.

### Remaining validation (requires the project validation environment)

- [ ] `$infrahub-run-integration-tests` for the schema/protocol change (not run here; needs the project-designated validation environment).
- [ ] Docs build/typecheck (`npm run typecheck && npm run build` from `docs/`) — docs `node_modules` not installed in this environment; changes are Markdown-only.
- [ ] pyAVD confirmation of every new node-type value: done via `EosDesigns` default `node_type_keys` (all seven types present in the pinned pyAVD).
