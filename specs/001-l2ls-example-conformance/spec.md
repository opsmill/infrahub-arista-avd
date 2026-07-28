# Feature Specification: L2LS Fabric Example Conformance

**Feature Branch**: `001-l2ls-example-conformance`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "ensure the repo and integration support arista L2LS Fabric design example and matches configuration exactly. https://github.com/aristanetworks/avd/tree/devel/ansible_collections/arista/avd/examples/l2ls-fabric"

## Overview

The official Arista AVD `l2ls-fabric` example is a pure Layer-2 Leaf-Spine
reference design: two MLAG `l2spine` switches, four `l2leaf` switches in two
MLAG rack pairs, tag-scoped L2 VLANs, connected server endpoints, and a
dual-homed firewall — with **no** EVPN/VXLAN/BGP overlay. This reference design
already carries partial L2LS plumbing (`Fabric-L2LS`, roles `l2spine`/`l2leaf`,
underlay `none` gating, MLAG rendering, and a `scripts/compare_avd_examples.py`
harness), but its modeled topology, service model, and rendered output diverge
from the example.

This feature makes the reference design reproduce the AVD `l2ls-fabric` example
**exactly**: the modeled source of truth mirrors the example's devices, VLANs,
tags, and endpoints, and the rendered EOS configuration matches the example's
`intended/configs/*.cfg` golden files, verified by the comparison harness.

This specification is the **schema / data-model foundation** (the first cycle in
a Schema → Generator → Transform chain). It defines *what the data model must be
able to represent* so that downstream generator and transform cycles can render
matching configuration. Requirements that depend on generation or rendering are
included so the end-to-end conformance goal stays visible, but the deliverable of
this cycle is the schema and seed-data model.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reproduce the L2LS spine/leaf topology (Priority: P1)

A network engineer loads the L2LS example fabric into Infrahub and generates the
fabric. The result is the example's exact device set — `SPINE1`, `SPINE2` as
MLAG-paired `l2spine` switches and `LEAF1`–`LEAF4` as `l2leaf` switches in two
MLAG rack pairs (RACK1 = LEAF1/LEAF2, RACK2 = LEAF3/LEAF4) — with MSTP spanning
tree (spine priority 4096, leaf priority 16384), MLAG on both tiers, and
Port-Channel uplinks from each leaf to both spines.

**Why this priority**: The device roster, roles, MLAG, spanning-tree, and uplink
topology are the backbone of the example. Every other config section depends on
this structure existing and being named correctly. Without it there is nothing to
match against the golden configs.

**Independent Test**: Load the fabric on a fresh instance, run the fabric
generation chain, and confirm the six devices exist with the correct names,
roles, MLAG pairing, spanning-tree priorities, and uplink port-channels; diff the
device-level (non-service, non-endpoint) config sections against
`intended/configs/{SPINE1,SPINE2,LEAF1,LEAF2,LEAF3,LEAF4}.cfg`.

**Acceptance Scenarios**:

1. **Given** the L2LS example fabric definition, **When** the fabric is
   generated, **Then** exactly `SPINE1`, `SPINE2`, `LEAF1`, `LEAF2`, `LEAF3`,
   `LEAF4` are created with roles `l2spine`/`l2leaf`.
2. **Given** the generated fabric, **When** device config is rendered, **Then**
   both spines form an MLAG pair and each rack's leaf pair forms an MLAG pair
   (peer VLAN 4094, peer Port-Channel, peer addressing from the MLAG pool).
3. **Given** the generated fabric, **When** device config is rendered, **Then**
   spanning tree is MSTP with spine priority 4096 and leaf priority 16384, and
   VLAN 4094 is excluded from spanning tree.
4. **Given** the generated fabric, **When** device config is rendered, **Then**
   each leaf aggregates its two spine-facing uplinks into a single LACP
   Port-Channel and the rendered structure matches the golden leaf configs.
5. **Given** the rendered configs, **When** compared to the golden example
   configs, **Then** the comparison harness reports no unexplained differences in
   the topology/MLAG/spanning-tree/uplink sections.

---

### User Story 2 - Model pure Layer-2 network services exactly (Priority: P2)

A network engineer models the example's L2 services — a single tenant
(`MY_FABRIC`) carrying three L2 VLANs (`BLUE-NET` 10, `GREEN-NET` 20, `ORANGE-NET`
30) — and scopes each VLAN to the correct leaf pair using tags (RACK1 =
blue+green, RACK2 = blue+orange). The rendered configuration contains only
Layer-2 VLAN definitions and trunking; it contains **no** EVPN, VXLAN, or BGP.

**Why this priority**: Services define what the fabric actually carries and are
where the current model diverges most: today the L2LS services are modeled
through EVPN objects with a VNI base, which is wrong for a pure-L2 fabric.
Correct, tag-scoped, overlay-free VLANs are essential to matching the golden
configs and to the design being correct.

**Independent Test**: Load the services, render the leaf configs, and confirm
each leaf has exactly the VLANs its tags entitle it to, that VLAN names/IDs match
the example, and that no `vxlan`, `router bgp`, or EVPN stanza appears anywhere in
the L2LS device configs.

**Acceptance Scenarios**:

1. **Given** the example tenant and three L2 VLANs, **When** services render,
   **Then** VLAN 10 is `BLUE-NET`, VLAN 20 is `GREEN-NET`, VLAN 30 is
   `ORANGE-NET`, with no L3 SVIs for these VLANs.
2. **Given** tag-based scoping, **When** leaf configs render, **Then** LEAF1/LEAF2
   carry VLANs 10 and 20, and LEAF3/LEAF4 carry VLANs 10 and 30.
3. **Given** a pure Layer-2 fabric, **When** any L2LS device config renders,
   **Then** it contains no `interface Vxlan`, no `router bgp`, and no EVPN
   address-family or route-target configuration.
4. **Given** the rendered configs, **When** compared to the golden configs,
   **Then** the VLAN and trunk-allowed-VLAN sections match.

---

### User Story 3 - Model connected endpoints and the firewall exactly (Priority: P3)

A network engineer models the example's connected endpoints: server hosts on leaf
access ports using per-color port profiles (access VLAN 10/20/30 with edge
portfast), and a dual-homed `FIREWALL` connected to both spines as a trunk
Port-Channel carrying VLANs 10, 20, and 30. The rendered access and trunk
interface configuration matches the example.

**Why this priority**: Endpoints and the firewall complete the example and
exercise access vs. trunk port profiles and a spine-side dual-homed port-channel.
They are valuable for full parity but the fabric and services deliver the core
value first.

**Independent Test**: Load endpoints, render leaf and spine configs, and confirm
each host-facing interface has the correct access VLAN, description, and portfast,
and that the firewall renders as a trunk Port-Channel on both spines allowing
VLANs 10, 20, 30 — then diff the endpoint interface sections against the golden
configs.

**Acceptance Scenarios**:

1. **Given** the server endpoints, **When** leaf configs render, **Then** each
   host-facing access port carries the correct single VLAN and has edge portfast
   enabled, matching the golden leaf configs.
2. **Given** the dual-homed firewall, **When** spine configs render, **Then**
   both spines present a trunk Port-Channel to the firewall allowing VLANs
   10/20/30, matching the golden spine configs.
3. **Given** the rendered configs, **When** compared to the golden configs,
   **Then** the connected-endpoint interface sections match.

---

### User Story 4 - Validate the L2LS deployment via fabric-selectable integration tests (Priority: P1)

An engineer validates the L2LS deployment end to end with the integration test
suite, and can point that suite at a specific fabric by name — for example
`pytest tests/integration --fabric Fabric-L2LS` (the same mechanism usable for
`Fabric-C` or any other fabric). The integration test loads the fabric, runs the
generation chain, renders configuration, and asserts the deployment result
(golden-config parity, zero validation violations, idempotence) for the selected
fabric.

**Why this priority**: "Matches configuration exactly" is only trustworthy if it
is proven by an automated, repeatable deployment test — not a one-off manual
diff. The reference design mandates integration tests for Infrahub changes, and
making the suite fabric-selectable is what lets the L2LS example (and every other
example fabric) be validated on demand without editing test code.

**Independent Test**: Run the integration suite twice — once targeting
`Fabric-L2LS` and once targeting another example fabric (e.g. `Fabric-C`) — and
confirm each run drives generation and validation scoped to the named fabric and
reports pass/fail for that fabric's deployment.

**Acceptance Scenarios**:

1. **Given** the integration suite, **When** it is run with a fabric selector
   (e.g. `--fabric Fabric-L2LS`), **Then** the suite scopes loading, generation,
   and assertions to that fabric.
2. **Given** no fabric selector, **When** the suite runs, **Then** it preserves
   its current default behavior (existing fabrics/tests are not broken).
3. **Given** the L2LS fabric selected, **When** the integration test runs the
   deployment, **Then** it asserts golden-config parity for the six example
   devices, zero PyAVD validation violations, and idempotent regeneration.
4. **Given** an unknown fabric name, **When** the suite is run with it, **Then**
   the suite fails fast with a clear "fabric not found" message rather than
   silently passing.

---

### Edge Cases

- **Leaf model lacks dedicated MLAG peer interfaces**: The example's leaf switch
  model may not expose reserved MLAG peer ports; the model must still yield a
  correct MLAG peer-link without colliding with uplink or host-facing ports.
- **VLAN 4094 reservation**: The MLAG peer VLAN (4094) must be reserved and
  excluded from spanning tree, and must not collide with any user VLAN.
- **Tag with no matching leaf pair**: A VLAN whose tag matches no rack must not be
  rendered onto any leaf (and should be surfaced rather than silently dropped).
- **Single-homed vs. dual-homed endpoints**: Endpoints connected to one leaf
  versus an MLAG pair must render correctly in both cases.
- **Management / underlay addressing**: The example's environment-specific
  management addressing must map onto the reference design's addressing model
  without introducing Layer-3 underlay routing (the fabric remains pure L2).
- **Re-running generation**: Regenerating the fabric must not create duplicate
  devices, VLANs, MLAG domains, or endpoints (idempotence).

## Requirements *(mandatory)*

### Functional Requirements

#### Topology & data model

- **FR-001**: The data model MUST represent the example's exact device roster:
  two `l2spine` spines and four `l2leaf` leaves, named to match the example
  (`SPINE1`, `SPINE2`, `LEAF1`–`LEAF4`).
- **FR-002**: The data model MUST represent two MLAG rack pairs (RACK1 =
  LEAF1/LEAF2, RACK2 = LEAF3/LEAF4) and an MLAG-paired spine tier.
- **FR-003**: The data model MUST represent MLAG on both the spine tier and the
  leaf tier, including the MLAG peer VLAN (4094), peer Port-Channel, and a peer
  addressing pool, for a leaf model that does not expose dedicated peer ports.
- **FR-004**: The data model MUST represent per-role spanning-tree priorities
  (spine 4096, leaf 16384) and MSTP as the spanning-tree mode.
- **FR-005**: The data model MUST represent each leaf's uplinks to both spines
  such that they render as a single aggregated LACP Port-Channel.
- **FR-006**: The fabric MUST be modeled as a standalone Layer-2 fabric (underlay
  routing protocol `none`) with no Layer-3 underlay, no loopback/VTEP underlay
  addressing requirement, and no EVPN overlay.

#### Services

- **FR-007**: The data model MUST represent the example's three L2 VLANs with
  matching IDs and names (`BLUE-NET` 10, `GREEN-NET` 20, `ORANGE-NET` 30) under a
  single tenant matching the example (`MY_FABRIC`).
- **FR-008**: The service model for the L2LS fabric MUST NOT introduce EVPN,
  VXLAN/VNI, or BGP constructs; VLANs MUST render as pure Layer-2 objects.
- **FR-009**: The data model MUST represent tag-based scoping of VLANs to leaf
  pairs so that RACK1 carries VLANs 10 and 20 and RACK2 carries VLANs 10 and 30.

#### Connected endpoints

- **FR-010**: The data model MUST represent server endpoints on leaf access ports
  with per-color access port profiles (access VLAN + edge portfast) matching the
  example.
- **FR-011**: The data model MUST represent a dual-homed `FIREWALL` endpoint
  connected to both spines as a trunk Port-Channel allowing VLANs 10, 20, and 30.
- **FR-012**: The data model MUST support both single-homed and dual-homed
  (MLAG) endpoint attachments.

#### Rendering conformance (verified in downstream cycles, required here for traceability)

- **FR-013**: The pipeline MUST emit the AVD L2LS design intent (`design.type`
  `l2ls`, or the equivalent node-type configuration) so PyAVD produces L2LS-shaped
  output for the example devices.
- **FR-014**: For each of the six example devices, the rendered EOS configuration
  MUST match the corresponding `intended/configs/*.cfg` golden file, allowing only
  the normalizations defined by the comparison harness (e.g., environment-specific
  management addressing).
- **FR-015**: The comparison harness (`scripts/compare_avd_examples.py`) MUST be
  able to compare the reference design's rendered L2LS output against the AVD
  `l2ls-fabric` golden configs and report parity per device and per feature
  section.
- **FR-016**: Rendering the example MUST produce zero PyAVD validation violations.

#### Loading & lifecycle

- **FR-017**: The example fabric, services, and endpoints MUST load cleanly on a
  fresh Infrahub instance in deterministic order.
- **FR-018**: Generating the example fabric MUST be idempotent — repeated runs
  produce no duplicate or orphaned objects and no configuration drift.
- **FR-019**: The reference design's documented L2LS capability MUST accurately
  describe the conformance achieved (what matches exactly and any documented
  exceptions).

#### Integration testing

- **FR-020**: The integration test suite MUST validate the L2LS deployment end to
  end: load the fabric, run the generation chain, render configuration, and assert
  golden-config parity, zero PyAVD validation violations, and idempotent
  regeneration.
- **FR-021**: The integration test suite MUST accept a fabric selector (e.g. a
  `--fabric <name>` pytest option) so a run can be scoped to a single named fabric
  such as `Fabric-L2LS` or `Fabric-C`, without editing test code.
- **FR-022**: When no fabric selector is provided, the integration suite MUST
  preserve its current default behavior so existing fabrics and tests continue to
  pass.
- **FR-023**: When a fabric selector names a fabric that does not exist, the suite
  MUST fail fast with a clear error rather than passing silently or skipping.
- **FR-024**: The L2LS deployment MUST be validated through the project's
  mandatory integration path (`$infrahub-run-integration-tests`), reporting the
  tested branch and commit per the project's quality gates.

### Key Entities *(include if feature involves data)*

- **L2LS Fabric**: A standalone Layer-2 Leaf-Spine fabric (underlay routing
  protocol `none`, MSTP spanning tree) whose name and structure mirror the AVD
  example. Owns pods, spanning-tree priorities, addressing pools, and services.
- **Pod**: Groups the spine tier and racks; carries the MLAG peer pool and spine
  count for the L2LS design.
- **Rack (MLAG pair)**: A leaf-pair grouping (RACK1, RACK2) with MLAG enabled and
  a leaf switch model; scopes which VLANs its leaves carry via tags.
- **Device (l2spine / l2leaf)**: The six example switches, named to match the
  example, with role-appropriate spanning-tree priority and MLAG membership.
- **MLAG Domain**: The spine-pair and leaf-pair peering relationships, including
  peer VLAN, peer Port-Channel, and peer addressing.
- **L2 VLAN**: A pure Layer-2 broadcast domain (id + name) with no SVI and no
  VXLAN/VNI, scoped to leaves by tag.
- **Tenant**: The single service container (`MY_FABRIC`) grouping the L2 VLANs,
  modeled without EVPN/VXLAN overlay semantics.
- **Tag / Zone**: The scoping mechanism (bluezone/greenzone/orangezone) that binds
  VLANs to specific leaf pairs.
- **Connected Endpoint (server / firewall)**: Host and firewall attachments with
  access/trunk port profiles; the firewall is a dual-homed trunk Port-Channel to
  both spines.
- **Port Profile**: The reusable access/trunk interface intent (access VLAN + edge
  portfast for hosts; trunk VLANs 10/20/30 + port-channel for the firewall).
- **Golden Config Set**: The example's `intended/configs/*.cfg` files used as the
  authoritative comparison target.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All six example devices (`SPINE1`, `SPINE2`, `LEAF1`–`LEAF4`) render
  EOS configuration that matches the example's golden `intended/configs/*.cfg`
  with zero unexplained differences reported by the comparison harness.
- **SC-002**: The rendered L2LS configuration contains zero EVPN, VXLAN, or BGP
  stanzas across all six devices.
- **SC-003**: Rendering the example produces zero PyAVD validation violations.
- **SC-004**: Each leaf carries exactly the VLANs its rack's tags entitle it to
  (RACK1: 10/20; RACK2: 10/30) and no others.
- **SC-005**: The example fabric loads on a fresh instance and generates end to
  end without manual intervention.
- **SC-006**: Re-running fabric generation produces no object diffs and no
  configuration drift (idempotence verified).
- **SC-007**: The supported-capabilities documentation states the L2LS example is
  reproduced to golden-config parity, listing any explicitly documented
  exceptions (and none that are undocumented).
- **SC-008**: The integration suite can be pointed at a single named fabric
  (e.g. `--fabric Fabric-L2LS`) and validates that fabric's deployment
  (parity + zero violations + idempotence); with no selector the existing suite
  still passes unchanged.

## Assumptions

- **Golden-config parity is the target** (confirmed): the reference design should
  reproduce the AVD `l2ls-fabric` example literally — the example's device names,
  VLAN names, tenant, tags, and firewall — and be diffed against its
  `intended/configs/*.cfg` golden files via the comparison harness.
- **Full example topology is in scope** (confirmed): two MLAG `l2spine` switches,
  four `l2leaf` switches across two MLAG racks, tag-scoped VLANs, connected server
  endpoints, and the dual-homed firewall trunk Port-Channel.
- The existing `Fabric-L2LS` model and seed data are reshaped/renamed to mirror
  the example (rather than a second parallel fabric being added), since the
  chosen target is golden parity rather than "both golden + variant".
- Environment-specific values that are legitimately inputs (management IP scheme,
  NTP/DNS servers, local users) are mapped onto the reference design's existing
  addressing/pool model; the comparison harness normalizes these where the golden
  file's exact values are not reproducible, and such normalizations are documented.
- The current EVPN-based modeling of the L2LS services (an `EvpnTenant` with a VNI
  base and `EvpnL2Vlan` objects) is a correctness gap for a pure-L2 fabric and is
  replaced by an overlay-free L2 VLAN/tenant representation.
- PyAVD's built-in `node_type_keys` for `l2spine`/`l2leaf` plus the emitted L2LS
  design intent are sufficient to produce example-matching output; no custom
  node-type-key definitions are assumed unless a downstream cycle proves otherwise.
- This specification covers the schema/data-model cycle; the generator changes
  (device naming, MLAG carving, tag scoping, endpoint cabling), transform /
  comparison-harness changes, and the fabric-selectable integration tests are
  delivered in the subsequent `/speckit-specify` cycles for this feature.
- The fabric selector is added to the existing integration suite (a pytest option
  such as `--fabric`, backed by a conftest fixture) rather than as a separate test
  runner; the current suite runs against all fabrics on the pipeline branch today,
  so the selector narrows scope without changing the default path.
- The pinned PyAVD version (`pyavd>=6.3.0,<6.4.0`) accepts the L2LS inputs
  required; if the example targets a materially different behavior, the version
  constraint is revisited in planning.

## Dependencies

- The AVD `l2ls-fabric` example golden configs (`intended/configs/*.cfg`) and
  input group_vars as the authoritative reference target.
- The existing `scripts/compare_avd_examples.py` comparison harness.
- The existing L2LS plumbing: roles `l2spine`/`l2leaf`, the `underlay_routing_protocol`
  `none` gate, `NetworkSpanningTreePriority`, MLAG schema, and the fabric/pod/rack
  generator chain.
- Downstream generator and transform cycles (Schema → Generator → Transform) to
  achieve the end-to-end rendering conformance requirements (FR-013 – FR-016).
- The existing integration suite (`tests/integration/`, `conftest.py`,
  `helpers.py`, `test_e2e_pipeline.py`) and the mandatory
  `$infrahub-run-integration-tests` validation path, extended with fabric-scoped
  selection (FR-020 – FR-024).
