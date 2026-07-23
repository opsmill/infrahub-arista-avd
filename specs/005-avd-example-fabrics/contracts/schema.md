# Contract: Native Schema Changes for AVD Example Fabric Designs

This contract defines the native schema surface added in this cycle. Everything
not listed here is delivered via the escape hatch (see
[escape-hatch.md](./escape-hatch.md)).

## Files

- `schemas/dcim_extensions.yml`: extend `DcimDevice.role` with new role choices.
- `schemas/l3ls_extensions.yml`: extend `NetworkFabric` with the extended underlay
  choices, the `evpn_vlan_aware_bundles` input, and the EVPN DC Gateway surface.
- `schemas/avd/avd.yml`: alternative home for `evpn_vlan_aware_bundles` if EVPN
  settings are consolidated on `Avd.Evpn`.
- `src/solution_arista_avd/avd.py`: extend `ROLE_TO_AVD_TYPE`.

Every new/edited schema file must start with:

```yaml
---
# yaml-language-server: $schema=https://schema.infrahub.app/infrahub/schema/latest.json
version: "1.0"
```

## Device Role Extension

`DcimDevice.role` MUST retain all current choices
(`super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`) and add:

```yaml
- name: l2spine
  label: L2 Spine
- name: l3spine
  label: L3 Spine
- name: p
  label: Provider (P)
- name: pe
  label: Provider Edge (PE)
- name: rr
  label: Route Reflector (RR)
- name: wan_router
  label: WAN Router
- name: wan_rr
  label: WAN Route Reflector (Pathfinder)
```

Automation uses machine values, not display labels.

## Role → AVD Node-Type Mapping

`ROLE_TO_AVD_TYPE` MUST gain an entry for every new role. Intended targets
(confirm against pinned pyAVD `node_type_keys`):

| Role | AVD node_type |
|------|---------------|
| `l2spine` | `l2spine` |
| `l3spine` | `l3spine` |
| `p` | `p` |
| `pe` | `pe` |
| `rr` | `rr` |
| `wan_router` | `wan_router` |
| `wan_rr` | `wan_rr` |

- Unknown roles MUST raise `ValueError`.
- A unit test MUST assert every schema role choice maps to a non-empty node type.

## Underlay Protocol Extension

Extend `NetworkFabric.underlay_routing_protocol` choices, preserving `ebgp` and
`ospf` and their default, adding:

```yaml
- name: none
  label: None (L2 only)
- name: isis-ldp
  label: ISIS-LDP
```

- The hostvar generator MUST handle each new value explicitly.
- `none` MUST NOT require underlay-only pools/settings.

## EVPN vlan-aware-bundles Input

Add an optional Boolean controlling vlan-aware-bundle rendering:

```yaml
- name: evpn_vlan_aware_bundles
  kind: Boolean
  optional: true
  # default_value chosen to preserve current rendering behavior
```

Placed on `NetworkFabric` (or `Avd.Evpn`), it MUST default so existing fabrics
render unchanged.

## EVPN DC Gateway Surface

Add an optional Boolean on the gateway device kind:

```yaml
- name: evpn_gateway
  kind: Boolean
  optional: true
  default_value: false
```

- Default `false` preserves existing behavior.
- When `true`, the device renders EVPN DC Gateway next-hop-self behavior.
- Final placement (device attribute vs. fabric-level gateway naming) is fixed
  during implementation; if pyAVD requires per-device tuning beyond a flag, this
  capability moves to the escape hatch.

## Prohibited / out-of-scope native additions (this cycle)

The following MUST NOT be added as native schema this cycle (escape hatch
instead): dot1x/NAC, PoE, port profiles, in-band management SVI automation, MPLS/
LDP config, BGP VPN-IPv4 overlay modeling, routed subinterfaces, PE-CE OSPF, CV-
Pathfinder path groups, DPS, virtual topologies, WAN HA, STUN, and CVaaS
integration.

## Migration & Regeneration

- New attributes on existing nodes MUST be optional or carry safe defaults.
- Removed attributes (if any) MUST use `state: absent`, not deletion.
- After schema changes: regenerate protocols
  (`infrahubctl protocols --schemas schemas --out src/solution_arista_avd/protocols.py`)
  and, after query changes, regenerate GraphQL return types. Generated files MUST
  NOT be hand-edited.

## Schema Validation Expectations

- `uv run infrahubctl schema check schemas/ --branch <branch>` passes with zero
  errors.
- Existing devices with roles `super_spine`, `spine`, `leaf`, `border_leaf`,
  `l2leaf` remain valid.
- Existing fabrics remain valid with unchanged rendered output.
- Contract tests confirm the new role choices, underlay choices, and EVPN inputs
  exist with the specified kinds and defaults.
