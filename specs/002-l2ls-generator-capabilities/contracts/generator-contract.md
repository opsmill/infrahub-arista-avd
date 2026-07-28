# Generator Contract: L2LS Generator Capabilities

The observable behavior this cycle publishes for the Transform/integration cycle
and for regression safety. Verified by unit tests, `scripts/compare_avd_examples.py`,
and the generator idempotence path.

## C1 — Spine + leaf MLAG

- Generating a fabric with `underlay_routing_protocol == none` MUST produce an MLAG
  pair on the spine tier (l2spine) AND on each rack's leaf tier (l2leaf), each with
  a peer VLAN, peer Port-Channel, and peer addressing.
- Peer-link interfaces MUST be carved deterministically on models without dedicated
  peer ports, without colliding with uplink/host ports.
- Test: unit tests assert spine and leaf MLAG domains + carved peer interfaces;
  idempotence path asserts no churn on re-run.

## C2 — Overlay-free tenant

- Hostvars for a tenant with no `mac_vrf_vni_base` MUST NOT contain a
  `mac_vrf_vni_base` key (or any derived VNI).
- Tenants that set the base MUST still emit it unchanged.
- Test: unit test on `_build_tenants_hostvars` for both cases.

## C3 — Tag-scoped VLANs

- Each `l2vlans[]` entry MUST carry `tags` from the VLAN's `rack_tags`/`avd_tags`.
- Each leaf node config MUST carry `filter.tags` from its rack's `avd_tags`/name.
- Net effect: RACK1 leaves carry VLANs 10/20; RACK2 leaves carry VLANs 10/30.
- Test: unit tests on the l2vlans builder and node-config builder; feature-level
  diff confirms per-rack VLAN membership.

## C4 — Pure Layer-2

- Rendered L2LS device configs MUST contain no `interface Vxlan`, no `router bgp`,
  and no EVPN address-family/route-target configuration.
- Test: render + grep in quickstart/integration; zero PyAVD validation violations.

## C5 — Endpoints

- Host endpoints render as access ports (correct VLAN + edge PortFast).
- The firewall endpoint renders as a trunk Port-Channel on both spines allowing the
  fabric VLANs (native, or `avd_custom_hostvars` fallback — documented).
- Test: unit + feature-level diff of the connected-endpoint sections.

## C6 — No regression / typed queries

- All new behavior MUST be gated on `underlay_routing_protocol == none`; existing
  fabrics (Fabric-A/C/Campus/ISIS-LDP) render unchanged.
- `avd_device_hostvar.gql` MUST fetch the new fields and its `*_query.py` MUST be
  regenerated (not hand-edited); mypy/ruff/yamllint clean.
- Test: full unit suite stays green; existing hostvar tests unchanged; lint passes.

## Downstream (Transform/integration cycle)

- Consumes this rendered output to diff against the example's feature sections and
  to run the fabric-selectable integration suite (`pytest --fabric Fabric-L2LS`),
  gated by `$infrahub-run-integration-tests`.
