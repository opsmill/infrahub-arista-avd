# Feature Specification: L2LS Generator Capabilities

**Feature Branch**: `002-l2ls-generator-capabilities`

**Created**: 2026-07-24

**Status**: Draft

**Input**: User description: "continue" — Generator cycle for L2LS example conformance: make the fabric/pod/rack and AVD hostvar generators produce the AVD `l2ls-fabric` example's technical capabilities (deterministic generation of the topology, MLAG peer carving on both tiers, tag-scoped pure-Layer-2 VLANs, host access-port cabling, and the dual-homed firewall trunk port-channel to both spines), verifying pure-Layer-2 output. Hostnames and environment-specific values need not match the example literally — the goal is technical-capability parity.

## Overview

This is the **Generator cycle** (second in a Schema → Generator → Transform
chain) for reproducing the Arista AVD `l2ls-fabric` example. The
[schema cycle](../001-l2ls-example-conformance/spec.md) added the data-model
foundation (l2spine/l3spine spanning-tree roles, overlay-free tenants, L2-VLAN tag
scoping, and edge PortFast). This cycle makes the **generators** turn that
source-of-truth into the example's technical capabilities in the rendered EOS
configuration.

**Scope refinement (confirmed with the requester):** the objective is
**technical-capability parity**, not literal reproduction. Device hostnames, node
IDs, and environment-specific addressing do **not** need to match the example
byte-for-byte; the generated fabric must exhibit the same *functional* L2LS
configuration (pure Layer-2, MLAG on both tiers, per-tier MSTP priorities,
tag-scoped VLANs, access/trunk endpoints, and a dual-homed firewall). Conformance
is judged at the feature-section level, not by hostname/address equality.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate the L2LS topology with MLAG on both tiers and per-tier MSTP (Priority: P1)

A network engineer generates the `Fabric-L2LS` fabric. The generators create the
spine tier as `l2spine` switches and the leaf tier as `l2leaf` switches across the
two MLAG rack pairs, form an MLAG pair on **both** tiers (carving peer-link
interfaces where the switch model has no dedicated ones), aggregate each leaf's
uplinks to the spines into a LACP Port-Channel, and apply the per-tier MSTP
priorities recorded in the source of truth (l2spine 4096, l2leaf 16384).

**Why this priority**: MLAG on both tiers, the spanning-tree profile, and the
uplink port-channels are the structural backbone of the L2LS design. Everything
else (services, endpoints) rides on this topology being generated correctly.

**Independent Test**: Generate the fabric on a branch; confirm the spine pair and
each leaf pair form MLAG domains (peer VLAN, peer Port-Channel, peer addressing),
each leaf's spine uplinks aggregate into one LACP Port-Channel, and the rendered
config carries MSTP with the two tier priorities.

**Acceptance Scenarios**:

1. **Given** the L2LS fabric, **When** generation runs, **Then** the spine tier is
   an `l2spine` MLAG pair and each rack's leaf tier is an `l2leaf` MLAG pair.
2. **Given** a leaf switch model with no dedicated MLAG peer ports, **When**
   generation runs, **Then** peer-link interfaces are carved deterministically
   without colliding with uplink or host-facing ports.
3. **Given** the fabric's spanning-tree priority objects, **When** config renders,
   **Then** MSTP is applied with l2spine priority 4096 and l2leaf priority 16384.
4. **Given** each leaf's two spine-facing uplinks, **When** config renders,
   **Then** they aggregate into a single LACP Port-Channel.

---

### User Story 2 - Render tag-scoped, pure-Layer-2 VLANs (Priority: P1)

The generators emit the overlay-free tenant's L2 VLANs as AVD `tenants[].l2vlans[]`
with the tag names drawn from each VLAN's `rack_tags`/`avd_tags`, and emit the
matching `filter.tags` on each leaf node so AVD scopes each VLAN to the correct
leaf pair. Because the tenant carries no VNI base, no VNI/VXLAN/EVPN/BGP is
emitted — the fabric renders as pure Layer-2.

**Why this priority**: Tag-scoped, overlay-free VLANs are the defining service
behavior of the L2LS example and the main correctness gap in the current output
(which emits a VNI base). Without this, the rendered config is neither correctly
scoped nor pure-Layer-2.

**Independent Test**: Generate the fabric; confirm each leaf carries exactly the
VLANs its rack's tags entitle it to (RACK1 = 10/20, RACK2 = 10/30), that the
tenant's VLANs render as plain L2 VLANs, and that no device config contains
`interface Vxlan`, `router bgp`, or EVPN address-family/route-target stanzas.

**Acceptance Scenarios**:

1. **Given** an L2 VLAN with `avd_tags`/`rack_tags`, **When** hostvars are built,
   **Then** the VLAN is emitted under the tenant with those tag names and each
   leaf node carries matching `filter.tags`.
2. **Given** tag scoping (RACK1 = blue+green, RACK2 = blue+orange), **When** config
   renders, **Then** LEAF pair 1 carries VLANs 10 and 20 and LEAF pair 2 carries
   VLANs 10 and 30.
3. **Given** a tenant with no `mac_vrf_vni_base`, **When** hostvars are built,
   **Then** no VNI base is emitted and no VNI/VXLAN is derived for its VLANs.
4. **Given** any L2LS device, **When** config renders, **Then** it contains no
   VXLAN interface, no `router bgp`, and no EVPN configuration.

---

### User Story 3 - Cable host access ports and the dual-homed firewall (Priority: P2)

The generators cable connected endpoints: server hosts to leaf access ports with
the correct access VLAN and edge PortFast, and a firewall dual-homed to **both
spines** as a trunk Port-Channel allowing the fabric's VLANs. This introduces a
new cabling path — an endpoint attached to the spine tier rather than to rack
leaves.

**Why this priority**: Endpoints and the firewall complete the example's technical
capabilities and exercise access vs. trunk switchport intent and a spine-side
dual-homed port-channel. They add value after the fabric and services are correct.

**Independent Test**: Generate the fabric; confirm host-facing leaf ports render as
access ports on the right VLAN with edge PortFast, and the firewall renders as a
trunk Port-Channel on both spines allowing the fabric VLANs.

**Acceptance Scenarios**:

1. **Given** server endpoints with access switchport intent, **When** config
   renders, **Then** each host-facing leaf port is an access port on the correct
   VLAN with edge PortFast enabled.
2. **Given** a dual-homed firewall endpoint, **When** generation runs, **Then** it
   is cabled to both spines and rendered as a trunk Port-Channel allowing the
   fabric VLANs.
3. **Given** single-homed and dual-homed (MLAG) endpoints, **When** config
   renders, **Then** both attach correctly.

---

### User Story 4 - Verify feature-level conformance and idempotence (Priority: P2)

An engineer verifies that the generated L2LS fabric renders configuration whose
feature sections match the AVD `l2ls-fabric` example (tolerating hostname/address
differences) with zero PyAVD validation violations, and that re-running generation
produces no object churn or config drift.

**Why this priority**: The whole point of "support the example" is a repeatable,
verifiable result. Feature-level parity and idempotence are what make the
capability trustworthy.

**Independent Test**: Run the comparison harness against the example's feature
sections; confirm the L2LS-relevant features (MLAG, MSTP, VLANs, trunks, access
ports, port-channels) match; render with zero PyAVD violations; re-run generation
and confirm no diffs.

**Acceptance Scenarios**:

1. **Given** the rendered L2LS config, **When** compared feature-by-feature to the
   example, **Then** the MLAG, spanning-tree, VLAN, trunk, and access-port sections
   match (allowing hostname/address normalization).
2. **Given** the fabric, **When** rendered, **Then** PyAVD reports zero validation
   violations.
3. **Given** a completed generation, **When** generation is re-run, **Then** no
   objects are created/deleted and no configuration drift is produced.

---

### Edge Cases

- **Spine model without dedicated MLAG peer ports**: peer-link carving must work on
  the `l2spine` model too, deterministically and without port collisions.
- **VLAN tag matching no leaf pair**: a VLAN whose tag maps to no rack must not
  render on any leaf and should be surfaced, not silently dropped.
- **Overlay-free vs. overlay tenants coexisting**: the VNI-omission logic must not
  regress the existing overlay fabrics (Fabric-A/C) that DO set `mac_vrf_vni_base`.
- **Firewall attached to spines**: the new endpoint-to-spine cabling must not
  disturb existing leaf-attached server cabling or the `skip_l2leaf_endpoints`
  behavior.
- **Re-run after partial generation**: idempotent tracking must not orphan or
  duplicate carved peer-link interfaces, MLAG domains, or endpoint cabling.

## Requirements *(mandatory)*

### Functional Requirements

#### Topology, MLAG & spanning tree

- **FR-001**: Generation MUST create the spine tier as `l2spine` and the leaf tier
  as `l2leaf` for a fabric whose underlay routing protocol is `none`.
- **FR-002**: Generation MUST form an MLAG pair on both the spine tier and each
  rack's leaf tier, including peer VLAN, peer Port-Channel, and peer addressing.
- **FR-003**: Generation MUST carve MLAG peer-link interfaces deterministically on
  switch models lacking dedicated peer ports, on both the l2spine and l2leaf tiers,
  without colliding with uplink or host-facing interfaces, and idempotently across
  re-runs.
- **FR-004**: Generation MUST aggregate each leaf's spine-facing uplinks into a
  single LACP Port-Channel.
- **FR-005**: Rendering MUST apply the fabric's per-tier MSTP priorities
  (l2spine and l2leaf) from the spanning-tree priority objects.

#### Pure-Layer-2, tag-scoped services

- **FR-006**: Hostvar generation MUST emit the overlay-free tenant's L2 VLANs as
  AVD `tenants[].l2vlans[]` and MUST NOT emit a VNI base (or any derived VNI) when
  the tenant has no `mac_vrf_vni_base`.
- **FR-007**: Hostvar generation MUST emit each L2 VLAN's tag names from its
  `rack_tags`/`avd_tags` and MUST emit matching `filter.tags` on each leaf node so
  AVD scopes VLANs to the correct leaf pairs.
- **FR-008**: Rendered L2LS device configuration MUST contain no VXLAN interface,
  no `router bgp`, and no EVPN address-family/route-target configuration.
- **FR-009**: The VNI-omission and tag-scoping behavior MUST NOT change the
  rendered output of existing overlay fabrics that set `mac_vrf_vni_base`.

#### Connected endpoints

- **FR-010**: Generation MUST cable server host endpoints to leaf access ports and
  render them as access ports on the correct VLAN with edge PortFast.
- **FR-011**: Generation MUST support a firewall endpoint dual-homed to both spines
  and render it as a trunk Port-Channel allowing the fabric's VLANs.
- **FR-012**: Generation MUST support both single-homed and dual-homed (MLAG)
  endpoint attachments without disturbing existing leaf-attached server cabling.

#### Correctness, verification & lifecycle

- **FR-013**: The pipeline MUST produce L2LS-shaped PyAVD output for the example's
  device roles (via node-type behavior and, if required, an emitted design intent),
  with zero PyAVD validation violations.
- **FR-014**: The comparison harness (`scripts/compare_avd_examples.py`) MUST report
  feature-section parity between the generated L2LS config and the AVD
  `l2ls-fabric` example, tolerating hostname/address normalization.
- **FR-015**: Generation MUST be idempotent — re-running produces no object churn
  and no configuration drift (validated with the generator idempotence path).
- **FR-016**: Generation MUST NOT require device hostnames, node IDs, or
  management/underlay addressing to equal the example's; environment-specific values
  are the reference design's own.

### Key Entities *(include if feature involves data)*

- **Fabric / Pod / Rack generators**: create the l2spine/l2leaf devices, MLAG
  pairs, and uplink cabling for the underlay-`none` design.
- **AVD hostvar generator**: builds per-device hostvars — node type, MLAG,
  spanning-tree, overlay-free tenants/l2vlans with tags, `filter.tags`, and
  connected endpoints.
- **MLAG domain / peer-link interfaces**: the spine-pair and leaf-pair peering,
  including carved peer interfaces.
- **L2 VLAN + tags**: overlay-free VLANs scoped to leaf pairs via rack/AVD tags.
- **Connected endpoints (servers / firewall)**: host access ports and the
  spine-attached firewall trunk port-channel.
- **Comparison harness**: the feature-level conformance check against the example.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every generated L2LS device renders configuration exhibiting the
  example's L2LS feature set (MLAG both tiers, MSTP per-tier priorities, LACP
  uplink port-channels, tag-scoped VLANs, access/trunk endpoints).
- **SC-002**: Zero L2LS device configs contain VXLAN, `router bgp`, or EVPN
  stanzas.
- **SC-003**: The comparison harness reports feature-section parity with the AVD
  `l2ls-fabric` example (hostname/address differences tolerated) and zero
  unexplained feature-level differences.
- **SC-004**: Each leaf pair carries exactly the VLANs its tags entitle it to
  (RACK1: 10/20; RACK2: 10/30) and no others.
- **SC-005**: Rendering produces zero PyAVD validation violations.
- **SC-006**: Re-running generation produces no object churn and no configuration
  drift.
- **SC-007**: The existing overlay fabrics (Fabric-A/C/Campus/ISIS-LDP) render
  unchanged after these generator changes.

## Assumptions

- **Technical-capability parity, not literal reproduction** (confirmed): hostnames,
  node IDs, and environment-specific addressing need not match the example.
  Conformance is judged at the feature-section level by the comparison harness.
- The schema foundation from feature 001 is merged/available (l2spine/l3spine STP
  roles, optional `mac_vrf_vni_base`, `Evpn.L2Vlan.rack_tags`/`avd_tags`, and
  `Interface.Layer2.spanning_tree_portfast`).
- The existing device-naming convention (`spine-<pod>-<idx>`, `leaf-<pod>-<rack>-<idx>`)
  is retained; no per-fabric naming override and no repo-wide rename are introduced.
- The current MLAG peer-link carving for l2leaf is extended/reused for the l2spine
  tier where the spine model lacks dedicated peer ports.
- The firewall-to-spine attachment is modeled natively where the endpoint/cabling
  path is reasonable; the documented `avd_custom_hostvars` escape hatch on the two
  spines is the fallback if native spine-attached-endpoint cabling proves
  disproportionate (per feature 001 research Decision 4).
- The pinned PyAVD version (`pyavd>=6.3.0,<6.4.0`) accepts the L2LS inputs.
- The fabric-selectable integration suite (`pytest --fabric ...`) is delivered in
  the subsequent Transform/integration cycle; this cycle relies on unit tests, the
  comparison harness, and the generator idempotence path for verification.

## Dependencies

- Feature 001 schema foundation (`specs/001-l2ls-example-conformance/`).
- Existing generators: `generate_pod.py`, `generate_rack.py`,
  `generate_avd_device_hostvar.py`, `generate_server_cabling.py`, and the AVD
  role/underlay mapping in `src/solution_arista_avd/avd.py`.
- `scripts/compare_avd_examples.py` for feature-level conformance.
- The generator idempotence validation path (`$infrahub-test-generator-idempotence`)
  and integration path (`$infrahub-run-integration-tests`) per the constitution.
- The AVD `l2ls-fabric` example's intended configs as the feature-level reference.
