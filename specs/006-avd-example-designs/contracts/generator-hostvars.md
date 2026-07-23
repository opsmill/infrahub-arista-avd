# Contract: Generator & Hostvars Behavior

What the generators must produce for each scenario. No `design.type` is used
(pyAVD 6.3); behavior comes from each node's `type` + `node_type_keys` defaults
plus the inputs below.

## Files

- `generators/generate_rack.py` (and `generate_pod.py` as needed): topology
  branches for L2LS (`l2spine`/`l3spine`) and campus (hierarchical IDF).
- `generators/generate_avd_device_hostvar.py`: rendering for new inputs.
- `generators/avd_device_hostvar.gql` + regenerated `*_query.py`: any new fields.
- `.infrahub.yml`: registration for any new generator/query.

## Hostvar emission contract

| Rule | Requirement |
|------|-------------|
| Node type | `hostvars["type"] = ROLE_TO_AVD_TYPE[role]`; abort with an actionable error if the role is unmapped (no silent skip). |
| Design type | MUST NOT emit `design.type` (does not exist in pyAVD 6.3). |
| Super-spine route server | If `role == super_spine`, render `evpn_role: server`. |
| vlan-aware bundles | If `fabric.evpn_vlan_aware_bundles` is true, render tenant L2 services as vlan-aware bundles with route targets; unchanged when false/unset. |
| EVPN DC Gateway | If `device.evpn_gateway` is true, render EVPN DC Gateway next-hop-self behavior. |
| Underlay `none` | If `fabric.underlay_routing_protocol == none`, do NOT emit `underlay_routing_protocol` and do NOT require underlay pools. |
| Underlay `isis-ldp` | If `fabric.underlay_routing_protocol == isis-ldp`, emit the pyAVD ISIS-LDP underlay value; MPLS/VPN specifics come from escape hatch. |
| Escape hatch | Deep-merge `avd_custom_hostvars` with generated hostvars; generated values win on conflict (unchanged). |
| Existing designs | L3LS/Fabric-A/B/C hostvars unchanged (new behavior gated on new roles/inputs). |

## Topology generation contract (fabric-model scenarios)

| Rule | Requirement |
|------|-------------|
| L2LS | Create `l2spine` (and optional `l3spine`) + `l2leaf` devices with MLAG on both tiers and port-channel/uplink cabling; no EVPN/underlay routing when underlay is `none`. |
| Campus | Create `l3spine` core + `l2leaf` access, including a hierarchical IDF (aggregation leaf feeding edge leaves) via existing parent/uplink relationships; OSPF underlay. |
| Idempotence | All `save()` use `allow_upsert=True`; deterministic ordering; checksum-based skipping preserved; repeated runs produce no new/duplicate objects. |
| WAN scenarios | No topology generator; devices/links come from seed data. |

## Validation expectations

- `infrahubctl generator <name> --target <fabric-or-device>` runs each scenario's
  generation without error.
- PyAVD `validate_inputs()` passes for every device in every scenario.
- Re-running any scenario's generator chain produces no artifact diffs.
- Regenerated typed query models exist for any changed query; generated files are
  not hand-edited.
