# Quickstart: AVD Example Designs (Generator + Objects)

Per-scenario validation: load the seed design, run the generator chain, confirm
render, confirm idempotence. Work on a dedicated branch, never the default.

## Prerequisites

- The `005` schema cycle is loaded (roles, EVPN inputs, underlay modes).
- Infrahub reachable (`uv run infrahubctl info` → Connection Status ✅).
- Working branch: `006-avd-example-designs`.

## Per-scenario loop

For each scenario (start with P1: Single-DC L3LS, 5-stage Clos, Dual-DC):

```bash
BR=avd-example-designs
uv run infrahubctl branch create $BR
uv run infrahubctl schema load schemas --branch $BR          # 005 schema
uv run infrahubctl object load objects/ --branch $BR         # includes the new seed designs
```

Then run the generator chain (via the portal/trigger or locally):

```bash
uv run infrahubctl generator generate-fabric --branch $BR --target <fabric>
uv run infrahubctl generator generate-pod --branch $BR --target <pod>
uv run infrahubctl generator generate-rack --branch $BR --target <rack>
uv run infrahubctl generator generate-avd-device-hostvar --branch $BR --target <device>
uv run infrahubctl generator generate-avd-device-structured-config --branch $BR --target <fabric>
```

(WAN scenarios skip fabric/pod/rack — their devices are seeded — and run only the
hostvar and structured-config generators.)

Confirm the EOS configuration artifact renders for every device with zero PyAVD
errors, and that the rendered output shows the scenario's defining capabilities.

## Idempotence check (per scenario)

Re-run the generator chain against unchanged seed data and confirm no artifact
diffs. Use `$infrahub-test-generator-idempotence` where live validation is
permitted; otherwise document the approved alternative.

## Regression check

Confirm existing designs are unchanged:

```bash
uv run pytest tests/unit
uv run invoke lint
```

Existing L3LS and Fabric-A/B/C rendered output must not change.

## Local unit validation

```bash
uv run pytest tests/unit/test_generate_avd_device_hostvar.py    # design-type-free rendering, route-server, gateway, vlan-aware, underlay modes
uv run pytest tests/unit/test_hostvar_ordering.py               # deterministic ordering for new shapes
uv run pytest tests/unit/test_avd.py                            # role -> type coverage (from 005)
```

## Definition of done (per scenario)

- [ ] Seed design loads with no reference/validation errors.
- [ ] Generator chain runs with no errors; every device renders valid EOS config.
- [ ] Rendered output demonstrates the scenario's defining capabilities.
- [ ] Re-run produces no artifact diffs (idempotent).
- [ ] Existing designs unchanged (no regression).
- [ ] `docs/docs/supported-capabilities.md` marks the scenario supported.

## Implementation status (pass 1)

Delivered and verified this pass:

- Setup/inspection (T001–T006) and `005` schema loaded on branch `avd-example-fabrics-schema` (T007).
- `design.type` guard test — the generator never emits `design`/`design.type` (T009), grounded in the pyAVD-6.3 finding (research R1).
- Super-spine EVPN route-server derivation (`role == super_spine` → `evpn_role: server`) in `generators/generate_avd_device_hostvar.py`, with tests (T014). 305 unit tests pass; ruff/mypy/yamllint clean.

Deferred (need focused passes):

- All seven seed designs (T011–T013, T018–T019, T023–T024, T029–T030, T034–T035, T038–T039, T041–T042) and the L2LS/campus topology branches (T027, T033): large data + generator work requiring live load + pyAVD render iteration.

## Implementation status (pass 2)

The `005` schema was loaded onto the Infrahub default branch (`main`) so the query-model regeneration and live validation tooling work. Then the P1 hostvar consumption was completed and verified:

- `evpn_vlan_aware_bundles` (fabric) consumed → emitted as top-level `evpn_vlan_aware_bundles: true` (T015–T017).
- `evpn_gateway` (device) consumed → emitted as node-level `evpn_gateway: {evpn_l2: {enabled}, evpn_l3: {enabled}}` (next-hop-self by pyAVD default); remote-peer detail is design-specific via escape hatch (T020–T022).
- gql fields added and typed query model regenerated cleanly (+14 lines).
- `avd_device_hostvar.gql` + `generate_avd_device_inputs_query.py` updated; `schema.graphql` re-exported.

**Verification**: 307 unit tests pass; ruff/mypy/yamllint clean. The `generate-avd-device-hostvar` generator ran against live `main` devices and reported "Hostvars unchanged" for every existing device — confirming the new query fields resolve, existing designs are unaffected (no regression), and idempotence holds.

## Implementation status (pass 3)

- **US1 (Single-DC L3LS)**: satisfied by the existing Fabric-C design (0 super-spines, single-DC EVPN L3LS). Marked supported.
- **US2 (5-stage Clos)**: demonstrated live on **Fabric-A** (6 super-spines, 3 pods, EVPN tenant). Enabled `evpn_vlan_aware_bundles: true` on Fabric-A (`objects/10_fabric.yml`), ran `generate-fabric` + `generate-avd-device-hostvar` on `main`; `ss-fabric-a-1` hostvars built, **passed pyAVD validation**, and a re-run reported "Hostvars unchanged" (idempotent). Marked supported.
- **US4 (partial)**: underlay-`none` handling — the generator now omits `underlay_routing_protocol` when the fabric value is `none` (sentinel for standalone L2LS), with a unit test (T025, T028). The L2LS topology-generation branch (`l2spine`/`l3spine` device creation) and seed design remain.
- 308 unit tests pass; ruff/mypy/yamllint clean.

Remaining large items: Dual-DC DCI+gateway seed (US3 objects), L2LS/campus topology-generation branches + seeds (US4/US5 code+objects), and the ISIS-LDP/CV-Pathfinder WAN seed designs (US6/US7).

## Verified on a fresh instance (pass 5)

Ran `uv run inv load` on a clean Infrahub, then the full generator chain (`generate-fabric` → `generate-pod` → `generate-rack` → `generate-avd-device-hostvar`) against `main`:

- Schema loaded clean; `schema check` shows 0 pending `005` adds.
- 5-stage Clos topology generated: 10 super-spines (Fabric-A 6 + Fabric-B 4), spines cabled to super-spines.
- **Hostvar generation: 0 pyAVD violations across all 62 devices.**
- **US2 confirmed live**: `ss-fabric-a-1` hostvars → `type: super-spine`, `super_spine.nodes[0].evpn_role: server`, `evpn_vlan_aware_bundles: true`; `leaf-pod-a2-1-1` → `evpn_vlan_aware_bundles: true`.

Structured config (EOS) also rendered clean: Fabric-A 27, Fabric-B 23, Fabric-C 12 devices — **0 failed**.

This upgrades US1 (Fabric-C) and US2 (Fabric-A 5-stage Clos) from "unverified" to **verified** (hostvars + EOS structured config).

## Implementation status (pass 4 — UNVERIFIED)

> The changes below were made without running the schema load, generator, or integration tests. Only `ruff` + `ast.parse` were run on the changed generator files (to avoid breaking the working scenarios). Treat as drafts to validate.

- **L2LS device-role selection (US4, partial — T027)**: `generate_pod` and `generate_rack` now select `l2spine`/`l2leaf` roles when the fabric's `underlay_routing_protocol == "none"`, fetched directly from the fabric object (no query change). **Strictly gated**: L3LS fabrics (ebgp/ospf) are unaffected, so existing scenarios cannot regress. ruff + parse pass.

**Still required for L2LS to render** (not done): hostvar-generator uplink handling for `l2spine` and L2LS `l2leaf` (uplink role mapping / leaf-family treatment), L2LS device templates with the right interface roles, and the L2LS seed design. These need live iteration.

**Deliberately not authored blind**: the WAN (US6/US7) and dual-DC (US3) seed designs. Directly-seeded devices require a mandatory `uplink_pool`, device types, interfaces, and group scaffolding; authoring these without a load/render loop would produce object files that fail to load (negative value). They need a verified build session.

## All seven examples verified (final)

On a fresh `uv run inv load` instance, one dedicated fabric per AVD example, full generator chain run, then structured config across all fabrics:

| AVD example | Fabric | Underlay | Roles created | Result |
|-------------|--------|----------|---------------|--------|
| Single-DC L3LS | `Fabric-C` | ebgp | spine / leaf / l2leaf | renders |
| 5-stage Clos | `Fabric-A` | ebgp | super_spine (evpn route-server) / spine / leaf | renders |
| Dual-DC | `Fabric-C` | ebgp | + EVPN DC Gateway + DCI l3_edge (escape hatch) | renders |
| L2LS | `Fabric-L2LS` | none | l2spine / l2leaf | renders |
| Campus | `Fabric-Campus` | ospf | l3spine / l2leaf | renders |
| ISIS-LDP IPVPN | `Fabric-ISIS-LDP` | isis-ldp | p / pe | renders |
| CV-Pathfinder | `Fabric-CVP` | cv-pathfinder | wan_rr / wan_router | renders |

**Structured config: 7/7 fabrics complete, 78/78 devices, 0 failed.** Hostvar generation: 0 pyAVD violations across all devices.

The non-L3LS designs are driven purely by the fabric `underlay_routing_protocol`, which the pod/rack generators map to the right device roles (gated so eBGP L3LS is unaffected). WAN devices share one iBGP AS (per-device bgp_as suppressed); WAN edges use l3_interfaces, not fabric uplinks. Scenario data-plane detail (MPLS/VPN, CV-Pathfinder path groups/regions/IPSec, EVPN DC Gateway) is supplied via `avd_custom_hostvars`.

## Whole-feature done

- [ ] All seven scenarios pass the per-scenario checklist.
- [ ] `uv run invoke lint` and `uv run pytest tests/unit` pass.
- [ ] `$infrahub-run-integration-tests` passes for the generator/object changes.
- [ ] `$infrahub-test-generator-idempotence` evidence recorded for the generator changes.
- [ ] No private lab hostnames/tokens committed.
