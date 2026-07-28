# Quickstart / Validation: L2LS Generator Capabilities

Validates that the generators produce the L2LS example's technical capabilities.
Prerequisite: feature 001 schema + seed merged/loaded.

## Prerequisites

- Infrahub running (`uv run invoke start`), `uv sync --all-packages`.
- Feature-001 schema + `Fabric-L2LS` seed loaded on a working branch.
- `alias ihctl='uv run infrahubctl'`.

## Step 1 — Typed query regeneration (Constitution III)

After editing `generators/avd_device_hostvar.gql`:
```bash
uv run infrahubctl graphql generate-return-types generators/avd_device_hostvar.gql
```
**Expected**: `generate_avd_device_hostvar_query.py` regenerated with the new
`mac_vrf_vni_base`/l2vlan-tag fields; clean diff.

## Step 2 — Unit tests (fast inner loop)

```bash
uv run pytest tests/unit/test_generate_avd_device_hostvar.py \
              tests/unit/test_generate_pod.py \
              tests/unit/test_generate_rack.py \
              tests/unit/test_avd.py -q
```
**Expected**: VNI omission, l2vlan tags, node `filter.tags`, spine MLAG + carving,
and firewall cabling tests pass.

## Step 3 — Generate the fabric on a branch

```bash
ihctl branch create l2ls-gen-capabilities
# (ensure feature-001 schema + seed are present on the branch)
# Trigger the fabric generation chain (fabric -> pod -> rack -> hostvar), then:
```
**Expected**: spine and leaf MLAG pairs exist; each leaf's uplinks aggregate to a
Port-Channel; hostvars show overlay-free tenant, tag-scoped l2vlans, and node
`filter.tags`.

## Step 4 — Pure-Layer-2 assertion

Render the L2LS device configs and confirm the invariant:
```bash
# For each L2LS device config, assert absence of overlay constructs:
grep -LE 'interface Vxlan|router bgp|address-family evpn' <rendered configs>
```
**Expected**: no L2LS device config contains VXLAN, `router bgp`, or EVPN.

## Step 5 — Feature-level parity

```bash
uv run python scripts/compare_avd_examples.py   # l2ls-fabric feature sections
```
**Expected**: MLAG, MSTP, VLAN, trunk, access-port, and port-channel sections match
the AVD `l2ls-fabric` example (hostname/address differences tolerated); zero
unexplained feature-level differences.

## Step 6 — Idempotence + no regression (Constitution II / C6)

- Re-run the fabric generation; confirm no object churn and no config drift
  (`$infrahub-test-generator-idempotence`).
- `uv run pytest tests/unit -q` — existing overlay-fabric tests remain green.
- `uv run invoke lint` — ruff/mypy/yamllint clean.

## Validation criteria (this cycle)

- [X] Typed query regenerated; clean diff (III) — +18 lines, only the two new `spanning_tree_portfast` selections.
- [X] Unit tests for VNI omission, l2vlan tags, filter.tags, spine MLAG, host access ports pass (519 total). Firewall dropped from scope.
- [X] Spine + leaf MLAG generated; leaf uplinks aggregated (peer-links Ethernet31/1+32/1 on spines, Ethernet47+48 on leaves).
- [X] No VXLAN/BGP/EVPN in any of the 6 L2LS configs; zero PyAVD violations.
- [!] Feature-level parity NOT reported — the harness needs AVD's upstream `intended/configs/*.cfg`, which are not vendored in this repo. Sections were verified by inspection instead (MLAG, MSTP priorities, per-rack VLANs, access ports, port-channels).
- [X] Idempotent re-run (structured config: 0 updated / 6 unchanged; hostvar checksums stable); existing fabrics unchanged; lint clean.

## Downstream validation (next cycle)

- Transform/integration cycle: the fabric-selectable integration suite
  (`pytest tests/integration --fabric Fabric-L2LS`) and `$infrahub-run-integration-tests`.
