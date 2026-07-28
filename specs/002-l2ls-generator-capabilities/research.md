# Phase 0 Research: L2LS Generator Capabilities

Resolves the generator-design decisions for producing the AVD `l2ls-fabric`
example's technical capabilities. Grounded in the current generator code and the
feature-001 schema foundation. All decisions target **feature-level parity** (not
literal hostname/address reproduction).

## Current-state findings (code-grounded)

- `generate_avd_device_hostvar.py:1265` emits `mac_vrf_vni_base` unconditionally —
  now that the attribute is optional, this would emit `None` for overlay-free
  tenants.
- The l2vlans builder (lines 1314-1324) emits `id`/`name`/`vni_override` but **no
  tags**; the SVI builder (lines 1298-1302) already emits tags via
  `_fetch_relationship_peers` + `_build_svi_tags`.
- The node-config builder (~line 1672) emits `name`/`id`/`bgp_as`/loopback/mgmt/
  uplink but **no `filter` / `filter.tags`**.
- `generate_pod.py` contains **no MLAG logic** — the spine tier is created without
  an MLAG pair; only `generate_rack.py` builds leaf MLAG (incl.
  `_assign_l2leaf_mlag_peer_interfaces` peer-link carving).
- `generate_server_cabling.py` cables server endpoints to rack leaves; there is no
  endpoint-to-spine path.

## Decision 1 — Spine-tier (l2spine) MLAG creation

**Decision**: Extend `generate_pod.py` to form the l2spine MLAG pair (MLAG domain +
peer-link carving) when the fabric `underlay_routing_protocol == none`, reusing the
carving logic factored out of `generate_rack.py`
(`_assign_l2leaf_mlag_peer_interfaces`). Factor the shared carving into a helper
usable by both tiers.

**Rationale**: The example MLAGs the spines, but no generator creates a spine MLAG
domain today. The pod generator owns spine creation, so it is the right place. The
leaf carving already handles "model without dedicated peer ports"; the spine model
(`arista-7050cx3-32c`) needs the same treatment. Factoring the helper avoids
duplicated, drift-prone carving logic.

**Alternatives considered**:
- *Create spine MLAG in a new generator*: rejected — spine lifecycle already lives
  in the pod generator; a new generator adds a target group and ordering for no
  benefit.
- *Author the spine MLAG domain as seed data*: rejected — MLAG membership + carved
  peer interfaces are computed from the generated devices, not static; that is
  generator work, not object data.

## Decision 2 — Overlay-free tenant: omit the VNI base

**Decision**: In `_build_tenants_hostvars`, only set `tenant_data["mac_vrf_vni_base"]`
when the tenant's value is not `None`.

**Rationale**: Minimal, correct, and backward-compatible — overlay tenants
(Fabric-A/C) keep emitting their base; the overlay-free L2LS tenant emits none, so
PyAVD derives no VNI/VXLAN for its VLANs (the nodes are not VTEPs anyway). Directly
fixes FR-006/FR-008.

**Alternatives considered**:
- *Emit `0`/sentinel*: rejected — a real VNI base of 0 is meaningful; absence is
  the correct signal.
- *Branch on fabric underlay*: rejected — the tenant's own (missing) base is the
  authoritative signal and keeps the logic local to the tenant builder.

## Decision 3 — L2-VLAN tags + per-node `filter.tags`

**Decision**: (a) In the l2vlans builder, fetch `rack_tags`/`avd_tags` and set
`l2v_data["tags"]` using the existing tag helper (rename `_build_svi_tags` →
`_build_tags` or reuse as-is). (b) In the node-config builder, emit
`node_config["filter"] = {"tags": [...]}` for leaf nodes from their rack's
`avd_tags` (and rack name), so AVD scopes each VLAN to the leaves whose filter tags
intersect the VLAN's tags.

**Rationale**: This is exactly how AVD scopes `l2vlans` to nodes. The SVI path
already proves the tag-emission pattern; extending it to l2vlans is consistent and
low-risk. `filter.tags` is the matching node-side half and is currently missing.

**Alternatives considered**:
- *Emit VLANs on every leaf*: rejected — breaks per-rack scoping (RACK1=10/20 vs
  RACK2=10/30) and diverges from the example.
- *Compute scoping in a transform*: rejected — AVD's native mechanism is tag
  filtering; reconstructing it downstream duplicates logic.

## Decision 4 — Host access ports + edge PortFast

**Decision**: Reuse the existing connected-endpoint/adapter/LAG builder; drive the
access VLAN from the interface/profile L2 config and emit `spanning_tree_portfast`
(the new schema attribute) as the adapter's PortFast intent.

**Rationale**: `l2_mode` (access/trunk) and VLAN membership already exist; the only
missing switchport element was PortFast, added in feature 001. No new endpoint
model is needed for hosts.

**Alternatives considered**:
- *New port-profile object model*: rejected — the profile/interface + adapter model
  already expresses access ports; adding a parallel model is unjustified.

## Decision 5 — Firewall dual-homed to both spines

**Decision**: Add a firewall endpoint cabling path that attaches a connected
endpoint to **both spines** and renders it as a trunk Port-Channel allowing the
fabric VLANs. Model natively in the cabling/hostvar path if the spine-attached
endpoint is reasonable; otherwise fall back to `avd_custom_hostvars` on the two
spines (per feature 001 research Decision 4). Record the choice in
`supported-capabilities.md`.

**Rationale**: This is the one structurally new pattern (endpoints attach to leaves
today). Staging native-with-fallback keeps the P2 endpoint scope from blocking the
P1 topology/services and matches the repo's documented native-vs-escape-hatch
guidance.

**Alternatives considered**:
- *Force fully native immediately*: acceptable but risks over-building; the fallback
  de-risks delivery.
- *Escape hatch only*: rejected for the general case — but acceptable specifically
  for this single niche endpoint if native proves disproportionate.

## Decision 6 — Typed query updates

**Decision**: Update `generators/avd_device_hostvar.gql` to fetch the (now optional)
`mac_vrf_vni_base` and the l2vlan `rack_tags`/`avd_tags`, then regenerate
`generate_avd_device_hostvar_query.py` with `infrahubctl graphql
generate-return-types`. Never hand-edit the generated model.

**Rationale**: Constitution III — GraphQL responses stay typed. New fields the
generator reads MUST be in the query and its regenerated model.

**Alternatives considered**:
- *Fetch via `self.client.get` per object*: rejected — adds round-trips and bypasses
  the typed query; the `from_graphql`/query-first pattern is preferred.

## Decision 7 — Idempotence & gating

**Decision**: All new creation (spine MLAG domain, carved peer interfaces, firewall
cabling) uses `allow_upsert=True` with deterministic natural keys (e.g. MLAG
domain id derived from the pod/pair; carved interfaces selected deterministically
by highest port index). Gate all new behavior on
`underlay_routing_protocol == none`. Validate with
`$infrahub-test-generator-idempotence`.

**Rationale**: Constitution II is the active gate. Non-idempotent carving or MLAG
creation could orphan/duplicate interfaces on re-run. Gating protects the other
fabrics from any behavior change.

**Alternatives considered**:
- *Random/first-free interface selection*: rejected — non-deterministic selection
  breaks idempotence; the existing l2leaf carving already selects deterministically
  by highest index.

## Resolved unknowns

- No `[NEEDS CLARIFICATION]` remain. The scope decision (technical-capability
  parity, not literal names) was resolved with the requester during
  `/speckit-specify`.
- Whether an explicit `design.type: l2ls` must be emitted: PyAVD's built-in
  `node_type_keys` for l2spine/l2leaf already drive L2LS behavior; emitting design
  intent is only required if feature-level parity reveals a gap (verified in
  quickstart, not assumed).
