# Schema Contract: L2LS Fabric Example Conformance

This is the contract the schema cycle publishes for the downstream Generator and
Transform cycles to consume. It is the stable "interface" of this cycle: the
schema shapes that must exist (and must not break) so generation and rendering can
achieve golden-config parity. Verified by schema-contract unit tests
(`tests/unit/test_*_schema_contract.py`) and by `infrahubctl schema check`.

## C1 — Spanning-tree priority roles

- `Network.SpanningTreePriority.role` dropdown MUST include `l2spine` and
  `l3spine` in addition to the existing `super_spine`, `spine`, `leaf`, `l2leaf`.
- Existing role choices MUST be preserved (no removals/renames).
- Contract test: assert the role dropdown contains `{super_spine, spine, leaf,
  l2leaf, l2spine, l3spine}`.

## C2 — Overlay-free tenant

- `Evpn.Tenant.mac_vrf_vni_base` MUST be optional.
- Tenants that set `mac_vrf_vni_base` (Fabric-A/B/C) MUST remain valid and
  unchanged in behavior.
- Contract test: assert `mac_vrf_vni_base.optional is true`; assert an
  `EvpnTenant` can be created without it.

## C3 — L2 VLAN tag scoping

- `Evpn.L2Vlan` MUST expose `rack_tags` (→ `LocationRack`, cardinality many,
  optional) and `avd_tags` (→ `Avd.Tag`, cardinality many, optional), matching the
  relationship shape on `Evpn.Svi`.
- Contract test: assert both relationships exist with peer/cardinality/optional as
  specified and identifiers distinct from the SVI identifiers.

## C4 — Connected-endpoint switchport intent

- The endpoint/adapter model MUST be able to express: switchport `mode`
  (access|trunk), an access VLAN, a set of trunk VLANs, and edge portfast.
- A connected endpoint MUST be attachable to `l2spine` devices (not only rack
  leaves) so the firewall can be dual-homed to both spines.
- Port-channel (LACP) for endpoints MUST remain expressible via the existing
  `Interface.Lag` + adapter `port_channel` model.
- Contract test: assert the mode/vlan/portfast attributes exist; assert an
  endpoint→spine attachment is representable (or, if the escape-hatch fallback is
  chosen for the firewall, assert `DcimDevice.avd_custom_hostvars` accepts the
  firewall block and document the exception).

## C5 — Backward compatibility

- All changes MUST be additive: new enum values, one attribute made optional, new
  optional relationships. No existing attribute/relationship is removed, renamed,
  or made stricter.
- The existing fabrics (Fabric-A, Fabric-C, Fabric-Campus, Fabric-ISIS-LDP) MUST
  continue to load and render with no change in output.
- Contract test / gate: `infrahubctl schema check schemas/` passes; existing
  schema-contract tests still pass; protocol regeneration produces a clean diff.

## C6 — Namespaces & conventions

- New/edited elements stay within approved namespaces (`Network.*`, `Evpn.*`,
  `Ipam.*`, `Dcim.*`, `Avd.*`, `Compute.*`).
- After any schema change: regenerate `src/solution_arista_avd/protocols.py` via
  `infrahubctl protocols` (never hand-edit).

## Downstream dependencies (consumed by later cycles, not built here)

- **Generator cycle** consumes C1–C4 to: name devices SPINE1-2/LEAF1-4, build 2
  MLAG racks, emit per-tier STP priority, emit overlay-free `tenants[].l2vlans[]`
  with `tags` + node `filter.tags`, cable host access ports and the spine-attached
  firewall trunk port-channel, and (verify) emit L2LS design intent so PyAVD
  produces `l2ls`-shaped output.
- **Transform / integration cycle** consumes the rendered structured config to diff
  against `intended/configs/*.cfg` via `scripts/compare_avd_examples.py` and to run
  the fabric-selectable integration suite (`--fabric Fabric-L2LS`).
