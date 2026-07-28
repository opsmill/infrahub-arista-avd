# Implementation Plan: L2LS Generator Capabilities

**Branch**: `002-l2ls-generator-capabilities` | **Date**: 2026-07-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-l2ls-generator-capabilities/spec.md`

## Summary

Make the fabric/pod/rack and AVD hostvar generators turn the L2LS source of truth
(from feature 001) into the AVD `l2ls-fabric` example's **technical capabilities**
in rendered EOS: MLAG on both tiers, per-tier MSTP, LACP uplink port-channels,
tag-scoped pure-Layer-2 VLANs, host access ports, and a dual-homed firewall trunk
port-channel to the spines. Conformance is judged at the feature-section level —
hostnames and environment-specific values need not match the example.

Technical approach (grounded in the current code):
- **Spine-tier MLAG** — `generate_pod.py` creates no MLAG today; add l2spine MLAG
  pair creation + peer-link carving (mirroring `generate_rack.py`'s l2leaf carving)
  when the fabric underlay is `none`.
- **Overlay-free tenants** — `_build_tenants_hostvars` emits `mac_vrf_vni_base`
  unconditionally (`generate_avd_device_hostvar.py:1265`); guard it so an unset
  base emits nothing (pure Layer-2, no VNI/VXLAN).
- **Tag-scoped VLANs** — the l2vlans builder (lines 1314-1324) emits no tags; add
  `rack_tags`/`avd_tags` emission (reuse the SVI tag helper) and emit per-node
  `filter.tags` on leaves in the node-config builder (which has no `filter` today).
- **Endpoints** — reuse the existing server/adapter/LAG builder for host access
  ports (+ the new `spanning_tree_portfast`); add firewall-to-spine dual-homed
  trunk-port-channel cabling (a new endpoint-on-spine path), with the documented
  `avd_custom_hostvars` fallback.
- **Verification** — feature-level parity via `scripts/compare_avd_examples.py`,
  zero PyAVD violations, and generator idempotence.

## Technical Context

**Language/Version**: Python >=3.11,<3.14

**Primary Dependencies**: `infrahub-sdk[all]>=1.19.0` (`InfrahubGenerator`),
`pyavd>=6.3.0,<6.4.0`, Infrahub 1.10.1

**Storage**: Infrahub graph — generators create DcimDevice/DcimInterface/MlagDomain
objects and emit per-device AVD hostvars

**Testing**: `pytest` unit (`tests/unit/test_generate_*`, `test_avd.py`,
`test_generate_avd_device_hostvar.py`), `$infrahub-test-generator-idempotence`,
`$infrahub-run-integration-tests`, and `scripts/compare_avd_examples.py`

**Target Platform**: Infrahub server; output is Arista EOS via PyAVD

**Project Type**: Infrahub reference-design repository (generators + queries)

**Performance Goals**: N/A; correctness = feature-level parity + zero PyAVD
violations + idempotent re-runs

**Constraints**: Additive/gated on `underlay_routing_protocol == none` so existing
eBGP L3LS and other fabrics (Fabric-A/C/Campus/ISIS-LDP) render unchanged. GraphQL
responses stay typed — update `.gql`, regenerate `*_query.py`, never hand-edit.

**Scale/Scope**: One fabric (`Fabric-L2LS`): 2 l2spine + 4 l2leaf, 3 VLANs, host +
firewall endpoints. Four code areas: `generate_pod.py`, `generate_rack.py`,
`generate_avd_device_hostvar.py` (+ its `.gql`/query model), and the
server-cabling path.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Schema-Driven Architecture | Schema exists before code references it | ✅ PASS — feature 001 added the STP roles, optional VNI base, L2-VLAN tags, and PortFast this cycle consumes |
| II. Idempotent Operations | `allow_upsert`, natural keys, checksum; no churn on re-run | ⚠️ GATE — the new spine-MLAG creation, peer-link carving, and firewall cabling MUST be idempotent; validated with `$infrahub-test-generator-idempotence` |
| III. Type Safety | Typed GraphQL models; mypy clean | ✅ PASS — the hostvar `.gql` gains `mac_vrf_vni_base`/l2vlan tag fields; regenerate `avd_device_hostvar_query.py`, never hand-edit; mypy enforced |
| IV. Test-Required Quality | Unit + integration; lint | ✅ PASS — unit tests for VNI omission, tag emission, filter.tags, spine MLAG, firewall cabling; integration via the mandated path |
| V. Convention-Based Structure | `generate_<entity>.py` + matching `.gql`/`*_query.py` | ✅ PASS — edits stay within the existing generator files and their co-located queries |

**Initial gate: PASS** (Principle II is the active quality gate for this cycle, not
a violation). Complexity Tracking not required.

**Post-design re-check (after Phase 1): PASS.** The design keeps every change gated
on `underlay_routing_protocol == none` (contract C6, no regression to other
fabrics), preserves typed queries via regeneration (III), and makes the new
creation paths idempotent with upsert + deterministic natural keys (II) — validated
by the idempotence gate. No new violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-l2ls-generator-capabilities/
├── plan.md              # This file
├── research.md          # Phase 0 — generator design decisions
├── data-model.md        # Phase 1 — generator output shapes + created objects
├── quickstart.md        # Phase 1 — validation guide
├── contracts/
│   └── generator-contract.md   # Phase 1 — observable behavior downstream depends on
├── checklists/
│   └── requirements.md  # From /speckit-specify
└── tasks.md             # From /speckit-tasks (not created here)
```

### Source Code (repository root)

```text
generators/
├── generate_pod.py                    # add l2spine MLAG pair + peer-link carving (underlay none)
├── generate_rack.py                   # reuse/extend l2leaf MLAG carving (already present)
├── generate_avd_device_hostvar.py     # VNI omission; l2vlan tags; node filter.tags; firewall endpoint
├── avd_device_hostvar.gql             # fetch mac_vrf_vni_base(optional), l2vlan rack_tags/avd_tags
├── generate_avd_device_hostvar_query.py   # regenerated from the .gql (not hand-edited)
└── generate_server_cabling.py         # firewall dual-homed-to-spines cabling path

src/solution_arista_avd/
└── avd.py                             # role/underlay constants (reuse; extend only if needed)

tests/unit/
├── test_generate_avd_device_hostvar.py   # VNI omission, l2vlan tags, filter.tags, firewall
├── test_generate_pod.py                  # new: l2spine MLAG pair + peer carving
├── test_generate_rack.py                 # l2leaf carving (extend if shared with spine)
└── test_avd.py                           # role/underlay constants if touched

docs/docs/developer-guide/avd/
├── role-mapping.md                    # spine MLAG / underlay-none notes
└── hostvars.md                        # l2vlan tags, filter.tags, overlay-free tenant
```

**Structure Decision**: Single Infrahub reference-design repository. All changes
are edits to existing generators and their co-located GraphQL query + regenerated
query model; no new generator files. Behavior is gated on
`underlay_routing_protocol == none` so other fabrics are untouched.

## Complexity Tracking

> No constitution violations — section intentionally empty.
