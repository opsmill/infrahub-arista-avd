# Contract: Escape Hatch & Demonstrability

This contract governs how scenario-specific, pass-through capabilities are
delivered via `avd_custom_hostvars`, and what "a fabric design exists for this
scenario" means and how it is verified.

## Escape-Hatch Mechanism

- **Surface**: the existing `avd_custom_hostvars` JSON attribute at
  `NetworkFabric`, `NetworkPod`, and `DcimDevice` scope. No schema change.
- **Merge**: escape-hatch content deep-merges with generator-produced hostvars;
  **generator-produced values win** on conflict. This precedence MUST NOT change.
- **Source**: escape-hatch content MUST live in committed seed objects, never in
  manual UI edits, so designs are reproducible and idempotent.
- **pyAVD**: every escape-hatch key MUST be accepted by `pyavd>=6.3.0,<6.4.0`.
  Keys rejected by the pinned version are a defect, not an acceptable design.

## Capabilities delivered via escape hatch

| Scenario | Escape-hatch capabilities (PyAVD keys, pass-through) |
|----------|------------------------------------------------------|
| Campus (5) | dot1x/NAC settings, PoE policies, port profiles, in-band management SVI |
| ISIS-LDP IPVPN (6) | MPLS/LDP, BGP VPN-IPv4 overlay, per-customer VRF-on-PE, routed subinterfaces, PE-CE OSPF |
| CV-Pathfinder (7) | path groups (MPLS/INTERNET), DPS/flow tracking, application-aware virtual topologies, WAN HA, STUN, CVaaS integration |

Capabilities NOT in this table are delivered natively (see
[schema.md](./schema.md)): new roles, underlay choices, `evpn_vlan_aware_bundles`,
super-spine route-server derivation, and the EVPN DC Gateway flag.

## Native-vs-Escape-Hatch Classification (record per capability)

Each gap-closing capability MUST be recorded as native or escape hatch in the
scenario's documentation, with the reason drawn from the Decision Principle. The
authoritative classification for this feature is in
[../research.md](../research.md) (Decisions R1–R9).

## Demonstrability Contract (per scenario)

A scenario is "supported" only when all of the following hold:

1. A **loadable seed design** exists in `objects/` (and any `avd_custom_hostvars`
   payloads) representing the scenario.
2. Loading the design on a clean branch and running the generator chain
   (`generate-fabric` → `generate-pod` → `generate-rack` →
   `generate-avd-device-hostvar` → `generate-avd-device-structured-config`)
   produces **valid PyAVD EOS configuration for every device** with zero render
   errors.
3. The rendered output **demonstrates the scenario's defining capabilities** as
   listed in that user story's acceptance scenarios.
4. **Re-running generation** against unchanged seed data produces **no artifact
   diffs** (idempotence).

> Note: full demonstrability (items 1–4) is completed in the follow-on generator
> and objects cycles. This schema cycle delivers the schema surface that makes
> the designs possible and validates it (schema check, role-mapping tests,
> contract tests). The seed designs and their render/idempotence proof land in
> the later cycles.

## Offline rendering

WAN/SD-WAN scenarios (6, 7) MUST render device configuration **offline** —
without a live CloudVision/CVaaS instance. External-service integration is
represented as intent in hostvars, not as a runtime dependency of rendering.

## Idempotence & determinism

- Seed designs and escape-hatch payloads MUST render deterministically.
- The generator chain's existing checksum-based change detection MUST continue to
  skip work when nothing changed.
- Escape-hatch payloads MUST NOT introduce nondeterministic ordering.
