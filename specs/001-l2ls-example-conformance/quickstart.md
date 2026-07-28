# Quickstart / Validation: L2LS Fabric Example Conformance (Schema cycle)

This guide validates the **schema cycle** deliverable: the schema deltas load
cleanly, are backward-compatible, and can represent the AVD `l2ls-fabric` example's
service and scoping model. End-to-end golden-config parity and the
fabric-selectable integration suite are validated in the later cycles (referenced
at the end).

## Prerequisites

- Infrahub stack running: `uv run invoke start` (targets `INFRAHUB_BASE_VERSION=1.10.1`).
- `uv sync --all-packages` completed.
- A working branch (never validate schema on the default branch):
  ```bash
  alias ihctl='uv run infrahubctl'
  ihctl branch create l2ls-example-conformance
  ```

## Step 1 — Schema check (gate C5/C6)

```bash
ihctl schema check schemas/ --branch l2ls-example-conformance
```
**Expected**: no errors; the edited `Network.SpanningTreePriority`,
`Evpn.Tenant`, and `Evpn.L2Vlan` validate; existing nodes unaffected.

## Step 2 — Load schema on the branch

```bash
ihctl schema load schemas --branch l2ls-example-conformance
```
**Expected**: load succeeds; migrations (attribute made optional, new enum values,
new optional relationships) apply without touching existing overlay tenants.

## Step 3 — Regenerate protocols (Constitution III)

```bash
uv run infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py
```
**Expected**: a clean, reviewable diff reflecting the new enum values / optional
attribute / new relationships. Do not hand-edit.

## Step 4 — Load the reshaped seed data

```bash
ihctl object load objects/ --branch l2ls-example-conformance
```
**Expected**: `Fabric-L2LS` loads with 2 spines, 2 MLAG racks, STP priority
objects (l2spine=4096, l2leaf=16384), overlay-free tenant `MY_FABRIC` with
BLUE/GREEN/ORANGE VLANs and tag scoping, host endpoints, and the firewall model.

## Step 5 — Contract tests (gate C1–C4)

```bash
uv run pytest tests/unit/test_avd_example_fabrics_schema_contract.py \
              tests/unit/test_l2ls_services_schema_contract.py -q
```
**Expected**: all pass — STP roles include `l2spine`/`l3spine`; tenant
`mac_vrf_vni_base` optional; `Evpn.L2Vlan` has `rack_tags`/`avd_tags`; endpoint
switchport intent present.

## Step 6 — Regression check (gate C5)

```bash
uv run pytest tests/unit -q
uv run invoke lint    # ruff + mypy + yamllint
```
**Expected**: existing fabric contract tests (Fabric-A/C/Campus/ISIS-LDP) still
pass; lint clean.

## Validation criteria (this cycle)

- [ ] `schema check` and `schema load` succeed on the branch (C5/C6).
- [ ] `protocols.py` regenerated with a clean diff (Constitution III).
- [ ] Seed data loads and the L2LS service/scoping model is representable.
- [ ] Contract tests C1–C4 pass; regression suite + lint pass (C5).

## Downstream validation (later cycles — not run here)

- **Generator cycle**: `$infrahub-test-generator-idempotence` for the fabric
  chain; devices named SPINE1-2/LEAF1-4; per-tier STP, MLAG both tiers, tag-scoped
  VLANs, endpoint cabling.
- **Transform / integration cycle**: render EOS and diff against
  `intended/configs/*.cfg` via `scripts/compare_avd_examples.py` (SC-001), assert
  no VXLAN/BGP/EVPN (SC-002), zero PyAVD violations (SC-003); run the
  fabric-selectable suite `pytest tests/integration --fabric Fabric-L2LS` and via
  `$infrahub-run-integration-tests` (SC-008).
