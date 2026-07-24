# Contract: Per-Scenario Seed Designs (Objects)

Each of the seven scenarios ships a loadable seed design under `objects/`,
following the Fabric-C convention (its own suffixed, numbered files). Use the
`infrahub-managing-objects` skill to author these.

## File format

- Every file uses `apiVersion: infrahub.app/v1` and `kind: Object`.
- Each `spec` block has a `kind` matching a schema node and a `data` list.
- Multiple documents in one file are separated by `---`.
- Cardinality-one relationships reference targets by `human_friendly_id`
  (scalar for single-element ids, list for multi-element).
- Group membership uses `member_of_groups`.
- Dropdown values use the choice `name` (not the display label).
- IPHost values include prefix length; IPNetwork uses CIDR.

## Load order (per design)

Numeric filename prefixes enforce dependency order, mirroring the existing
Fabric-C files (`02a_`, `03a_`, `04c_`, `06a_`, `10a_`, `11a_`, `12a_`):

```
NNa_<scenario>_manufacturer.yml   # OrganizationManufacturer
NNa_<scenario>_device_types.yml   # DcimDeviceType (depends on manufacturer)
NNc_<scenario>_pools.yml          # CoreIPPrefixPool / CoreIPAddressPool / CoreNumberPool
NNd_<scenario>_management.yml     # DNS / NTP / users
NNa_<scenario>_templates.yml      # device/server templates (depends on device types)
NNa_<scenario>_fabric.yml         # NetworkFabric (+ NetworkPod) (depends on pools, templates)
NNa_<scenario>_rack.yml           # LocationRack (depends on fabric)
NNa_<scenario>_services.yml       # EVPN tenants / SVIs / VRFs (depends on fabric)
NNa_<scenario>_devices.yml        # WAN scenarios only: DcimDevice/DcimInterface/NetworkLink
```

(Exact numbers chosen to sort after existing files and preserve dependency order.)

## Per-scenario content

| Scenario | Distinguishing seed content |
|----------|-----------------------------|
| Single-DC L3LS | spines + L3 leaf MLAG pairs + L2 leaves; eBGP underlay; EVPN tenants/SVIs; server port-channels |
| 5-stage Clos | super-spines + 2 pods; `evpn_vlan_aware_bundles: true`; tenant with route targets |
| Dual-DC | two fabrics; border leaves with `evpn_gateway: true`; `dci` NetworkLinks between them; `dci_pool` |
| L2LS | `l2spine`/`l2leaf` (+ `l3spine` variant); `underlay_routing_protocol: none`; VLANs with tag filtering |
| Campus | `l3spine` core + IDF `l2leaf` incl. hierarchical aggregation/edge; `ospf` underlay; escape-hatch dot1x/PoE/port-profiles/in-band mgmt |
| ISIS-LDP IPVPN | directly-seeded `p`/`pe`/`rr` devices + links; `isis-ldp` underlay; escape-hatch MPLS/VPN-IPv4, per-customer VRFs, PE-CE |
| CV-Pathfinder | directly-seeded `wan_router`/`wan_rr` devices + links; escape-hatch path groups/DPS/virtual-topologies/WAN-HA/STUN/CVaaS |

## Integrity rules

- Object names and human_friendly_ids are unique across all seven designs.
- Each design's pools are distinct and sized so all designs can load together
  without ASN/prefix exhaustion.
- Every device is in the `avd_devices` group.
- WAN devices are not placed in `fabrics`/`racks` in a way that triggers
  leaf-spine generation.
- Escape-hatch payloads live in `avd_custom_hostvars` (fabric/pod/device) and use
  only keys accepted by the pinned pyAVD.

## Validation expectations

- `uv run infrahubctl object load objects/ --branch <branch>` loads all designs
  with no missing references or schema validation errors.
- After loading + generation, every device renders valid EOS config.
- Re-loading and re-generating produces no diffs (idempotent).
