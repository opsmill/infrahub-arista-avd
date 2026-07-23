# Phase 1 Data Model: AVD Example Designs (Generator + Objects)

This feature adds no schema. It defines what the generators emit and how each
scenario's seed design is structured. Entities below are existing schema kinds
(from `005` and earlier) used in new ways.

## Generated / seeded entities

### DcimDevice (per scenario)

| Aspect | Value |
|--------|-------|
| Source | Created by fabric/pod/rack generators (fabric-model scenarios) or seeded directly (WAN scenarios) |
| Key attributes | `role` (maps to PyAVD `type`), `node_id`, `evpn_gateway` (dual-DC), `avd_custom_hostvars` (escape hatch) |
| Group | Must be in `avd_devices` so hostvar/structured-config generators run |
| Validation | `role` MUST map to a valid `node_type_keys` type; unmapped role aborts generation |

### Per-device hostvars (AvdHostvarFile content)

The hostvar generator emits, in addition to today's fields:

| Field / behavior | Condition | Source |
|------------------|-----------|--------|
| `type` | always | `ROLE_TO_AVD_TYPE[role]` (from `005`) |
| `evpn_role: server` | `role == super_spine` (5-stage Clos) | derived (R5) |
| vlan-aware-bundle tenant rendering | `fabric.evpn_vlan_aware_bundles` true | fabric input (R6) |
| EVPN DC Gateway next-hop-self | `device.evpn_gateway` true | device flag (R7) |
| `underlay_routing_protocol` omitted | `fabric.underlay_routing_protocol == none` | L2LS (R3) |
| ISIS-LDP underlay | `fabric.underlay_routing_protocol == isis-ldp` | ISIS-LDP IPVPN (R4) |
| escape-hatch keys | present in `avd_custom_hostvars` | deep-merged, generated wins |

No `design.type` is emitted (R1).

### Topology objects (fabric-model scenarios)

| Entity | New behavior |
|--------|--------------|
| `NetworkFabric`/`NetworkPod`/`LocationRack` | drive L2LS (`l2spine`/`l3spine`, underlay `none`) and campus (hierarchical IDF) topology branches |
| `DcimInterface` / `NetworkLink` | uplink cabling for the new topologies; `dci` links for dual-DC (existing) |

### Seed design (per scenario)

Each scenario ships a Fabric-C-style numbered file set under `objects/`:

| File group | Kind(s) | Depends on |
|------------|---------|-----------|
| manufacturer / device types | `OrganizationManufacturer`, `DcimDeviceType` | — |
| pools / management | `CoreIPPrefixPool`, `CoreIPAddressPool`, DNS/NTP | — |
| templates | `CoreObjectTemplate`-based device/server templates | device types |
| fabric / pods / racks | `NetworkFabric`, `NetworkPod`, `LocationRack` | pools, templates |
| services | `EvpnTenant`, `EvpnSvi`, `EvpnL2Vlan`, `IpamVRF` | fabric |
| devices (WAN scenarios) | `DcimDevice`, `DcimInterface`, `NetworkLink` | device types, groups |
| escape-hatch payloads | `avd_custom_hostvars` on fabric/pod/device | fabric/devices |

## Validation rules

- Every device is in the `avd_devices` group (FR-025).
- WAN devices are NOT in the `fabrics`/`racks` groups in a way that triggers
  leaf-spine generation (FR-023).
- Object names / human_friendly_ids are unique across all seven designs (FR-022).
- Shared pools are sized / partitioned so all designs can load together without
  ASN or prefix exhaustion (FR-022).
- Dropdown values use choice `name`; IPHost/IPNetwork use CIDR; relationships use
  human_friendly_id (objects skill conventions).
- Every escape-hatch key is accepted by the pinned pyAVD (FR-024).

## State (per scenario design)

| State | Meaning | Transition |
|-------|---------|------------|
| Seeded | Seed files loaded on a clean branch | generator chain can run |
| Generated | Topology (if any) built; hostvars + structured config produced | artifacts renderable |
| Rendered | Every device renders valid EOS config (zero PyAVD errors) | scenario demonstrable |
| Idempotent | Re-run produces no artifact diffs | scenario counted supported |

## Backward-compatibility

- Existing L3LS designs and Fabric-A/B/C render identically (new branches gated
  on new roles/underlay values).
- Escape-hatch deep-merge precedence (generated wins) is unchanged.
