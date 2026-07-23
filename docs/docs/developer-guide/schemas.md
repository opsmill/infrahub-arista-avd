---
title: Schemas
description: All Infrahub schema definitions in this solution.
audience: developer
sidebar_position: 2
---

# Schemas

:::info Developer Guide
Documents the YAML schema files that define the data model.
:::

Every kind in the data model is defined in a YAML file under `schemas/` and loaded with `infrahubctl schema load schemas` (`inv load-schema`). The GraphQL kind is the schema `namespace` joined to its `name` — `Dcim` + `Device` becomes `DcimDevice`. Generics load as GraphQL interfaces; nodes load as GraphQL object types.

Regenerate the typed protocol classes after any schema change (see [the command below](#protocols)).

## Schema files

| File | Defines |
|------|---------|
| `base/dcim.yml` | `Dcim.GenericDevice`, `Dcim.PhysicalDevice`, `Dcim.Device`, interface generics/nodes, `Dcim.DeviceType`, `Dcim.Platform` |
| `base/ipam.yml` | `Ipam.IPAddress`, `Ipam.Prefix` base definitions |
| `base/location.yml` | `Location.Generic`, `Location.Hosting` base definitions |
| `base/organization.yml` | `Organization.Generic`, `Organization.Manufacturer`, `Organization.Provider` |
| `logical_design.yml` | `Network.Fabric`, `Network.Pod`, `Network.BuildingBlock` |
| `dcim_extensions.yml` | `Network.Link`, including `role=dci` and DCI link fields, plus device extensions (`role`, `bgp_asn`, `node_id`, loopback/mgmt, pod/rack relations) and the interface `role`/`description`/`ip_address` extensions |
| `dci.yml` | `NetworkFabric.dci_pool` DCI addressing source |
| `l3ls_extensions.yml` | L3LS fabric attributes (routing protocols, MTU, spanning-tree, EVPN overlay) and pod/rack/VRF/MLAG extensions |
| `location_extensions.yml` | `Location.Hall`, `Location.Rack` (`rack_type`, leaf counts, `generation_complete`) |
| `ipam_extensions.yml` | `Ipam.Prefix` `role` and `status` dropdowns |
| `management.yml` | `Network.DnsServer`, `Network.NtpServer`, `Network.LocalUser` |
| `generator.yml` | `Generator.Target` generic (`checksum` tracking) |
| `vlan/vlan.yml` | `Ipam.VLAN`, `Ipam.L2Domain` |
| `vrf/vrf.yml` | `Ipam.VRF`, `Ipam.RouteTarget` |
| `evpn/evpn_services.yml` | `Evpn.Tenant`, `Evpn.Svi`, `Evpn.L2Vlan` |
| `evpn/evpn_gateway.yml` | `Evpn.Domain`, `Evpn.GatewayGroup`, plus fabric/pod/device EVPN Gateway relationship extensions |
| `lag/lag.yml` | `Interface.Lag`, `Generic.InterfaceBundle` |
| `mlag/mlag.yml` | `Generic.MlagDomain`, `Mlag.Domain`, `Mlag.Interface` |
| `routing/routing.yml` | `Routing.BGPPeerGroup`, `Routing.BGPNeighbor`, prefix lists, route maps, static routes |
| `compute/compute.yml` | `Compute.GenericUnit`, `Compute.PhysicalServer`, virtualization hosts |
| `avd/avd.yml` | `Avd.Evpn` |
| `objects/objects.yml` | `Avd.Artifact`, `Avd.HostvarFile`, `Avd.StructuredConfigFile` |

The device and interface `role` dropdowns that the fabric uses are defined in `dcim_extensions.yml`, not in the base `dcim.yml` — the extension redefines the base lists.

## Network fabric hierarchy

### `NetworkFabric` — `Network.Fabric`

Top-level container for a datacenter fabric. Inherits `Network.BuildingBlock` and `CoreArtifactTarget`; parents `NetworkPod`.

- **Attributes**: `name` (unique), `index`, `amount_of_super_spines` (default 4), interface-sorting methods, `mgmt_gateway`, `avd_hostvars_ready`. L3LS attributes (via `l3ls_extensions.yml`): `underlay_routing_protocol` (`ebgp`/`ospf`), `overlay_routing_protocol` (`ebgp`/`ibgp`), `p2p_uplinks_mtu`, `spanning_tree_mode`, `virtual_router_mac`, EVPN/underlay/MLAG passwords, `anta_enabled`.
- **Relationships**: `uplink_pool` / `vtep_pool` / `loopback_pool` / `dci_pool` → `CoreIPPrefixPool`, `asn_pool` / `node_id_pool` → `CoreNumberPool`, `mgmt_pool` → `CoreIPAddressPool`, `avd_evpn` → `AvdEvpn`, `dns_servers` / `ntp_servers` / `local_users` → management kinds.

### `NetworkPod` — `Network.Pod`

A pod within a fabric. Inherits `Network.BuildingBlock` and `Generator.Target`; parented by `NetworkFabric`.

- **Attributes**: `name` (unique), `index`, `amount_of_spines` (default 4), `role` (`fabric`, `cpu`, `storage`), interface-sorting methods, `checksum` (from `Generator.Target`).
- **Relationships**: `racks` → `LocationRack`, `devices` → `DcimDevice` (the pod's spines), `loopback_pool` / `mlag_peer_pool` / `mlag_l3_pool` → `CoreIPAddressPool`, `prefix_pool` → `CoreIPPrefixPool`.

### `NetworkBuildingBlock` — `Network.BuildingBlock` (generic)

Hierarchical base for `NetworkFabric` and `NetworkPod`. Attributes: `name` (unique), `index`.

### `NetworkLink` — `Network.Link`

A cabled connection between interfaces. Inherits `Dcim.Connector`, so it carries `name` and `medium` (`mmf`, `smf`, `copper`) and relates to `connected_endpoints` → `DcimEndpoint`. A DCI connection is a normal `NetworkLink` with `role=dci`, not a separate schema node.

- **DCI attributes**: `role` (`dci`) and `include_in_underlay_protocol` (Boolean, default `true`). BGP ASNs are taken from each endpoint device's own `asn`, not stored on the link.
- **Relationships**: inherited `connected_endpoints`; no DCI-specific endpoint, pool, subnet, endpoint IP, speed, BFD, MTU, external-network, or EVPN Gateway fields are added.
- **Addressing source**: `NetworkFabric.dci_pool`; the hostvars generator allocates one `/31` from this pool per valid DCI-role link.

## Devices and interfaces

### `DcimDevice` — `Dcim.Device`

The concrete network device (switch). Inherits `Dcim.GenericDevice`, `Dcim.PhysicalDevice`, and `CoreArtifactTarget`.

- **Attributes**: `name` (unique), `description`, `os_version`, `status` (`active`, `provisioning`, `maintenance`, `drained`). Fabric extensions (via `dcim_extensions.yml`): `role` (`super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`), `index`, `bgp_asn`, `node_id`.
- **Relationships**: `interfaces` → `DcimInterface`, `device_type` → `DcimDeviceType`, `platform` → `DcimPlatform`, `primary_address` / `loopback_ip` / `mgmt_ip` → `IpamIPAddress`, `pod` → `NetworkPod`, `rack` → `LocationRack`, `avd_artifact` → `AvdArtifact`, `mlag_domain` → `MlagDomain`, plus routing relations (`bgp_peer_groups`, `bgp_neighbors`, `prefix_lists`, `route_maps`, `static_routes`).

### Interface kinds

`DcimInterface` (`Dcim.Interface`) is the interface generic; the concrete nodes are `InterfacePhysical` (`Interface.Physical`), `InterfaceVirtual` (`Interface.Virtual`), and `InterfaceLag` (`Interface.Lag`). GraphQL queries that select any interface root on `DcimInterface`.

- **`DcimInterface` attributes**: `name`, `description`, `mtu`, `status`, `role`. The fabric `role` list (via `dcim_extensions.yml`) is `uplink`, `access`, `spine`, `super_spine`, `leaf`, `loopback`, `server`, `storage`, `mlag_peer`.
- **`DcimInterface` relationships**: `device` → `DcimGenericDevice` (parent), `ip_address` → `IpamIPAddress`, `untagged_vlan` / `tagged_vlan` → `IpamVLAN`.
- Layer-2/3 behaviour comes from the `Interface.Layer2` (`l2_mode`) and `Interface.Layer3` (`ip_addresses`, `dot1q_id`, `mac_address`) generics.

### `DcimDeviceType` — `Dcim.DeviceType`

A device model. Attributes: `name` (unique), `part_number`, `height`, `full_depth`, `weight`. Relationships: `manufacturer` → `OrganizationManufacturer`, `platform` → `DcimPlatform`.

### `OrganizationManufacturer` — `Organization.Manufacturer`

A device manufacturer. Inherits `Organization.Generic`; attributes `name` (unique), `description`; relates to `device_type` → `DcimDeviceType`.

## Locations

### `LocationHall` — `Location.Hall`

A datacenter hall. Inherits `Location.Generic`; parents `LocationRack`. Attributes: `name`, `shortname`, `description`, `index`.

### `LocationRack` — `Location.Rack`

A physical rack. Inherits `Location.Generic`, `Location.Hosting`, and `Generator.Target`; parented by `LocationHall`.

- **Attributes**: `name`, `index`, `rack_type` (`compute`, `storage`), `amount_of_leafs` (1–2), `amount_of_l2leafs` (via `l3ls_extensions.yml`), `generation_complete`, `checksum`.
- **Relationships**: `pod` → `NetworkPod`, `devices` → `DcimPhysicalDevice`, `leaf_switch_template` / `l2leaf_switch_template` → `CoreObjectTemplate`.

## IPAM

### `IpamIPAddress` — `Ipam.IPAddress`

An IP address. Inherits `BuiltinIPAddress`. Relationships: `interface` → `Interface.Layer3`, `vrf` → `IpamVRF`.

### `IpamPrefix` — `Ipam.Prefix`

An IP prefix. Inherits `BuiltinIPPrefix`.

- **`role`** (required, via `ipam_extensions.yml`): `supernet`, `fabric_supernet`, `super_spine_loopback`, `pod_supernet`, `pod_loopback`, `pod_super_spine_spine`, `pod_leaf_spine`, `loopback`, `loopback-vtep`, `technical`, `management`, `backfill`.
- **`status`** (via `ipam_extensions.yml`): `active`, `deprecated`, `reserved`.
- **Relationships**: `gateway` → `IpamIPAddress`, `vlan` → `IpamVLAN`, `vrf` → `IpamVRF`, `location` → `Location.Hosting`.

### `IpamVLAN` — `Ipam.VLAN`

A VLAN. Attributes: `name`, `vlan_id`, `status`, `role` (`server`, `management`, `user`). Relationships: `l2domain` → `IpamL2Domain` (required), `prefixes` → `IpamPrefix`.

### `IpamL2Domain` — `Ipam.L2Domain`

A layer-2 domain grouping VLANs. Attributes: `name`. Relationships: `vlans` → `IpamVLAN`.

### `IpamVRF` — `Ipam.VRF`

A VRF. Attributes: `name` (unique), `vrf_rd`, `vrf_vni`, `vtep_diagnostic_loopback`. Relationships: `namespace` → `BuiltinIPNamespace`, `import_rt` / `export_rt` → `IpamRouteTarget`, `tenant` → `EvpnTenant`, `svis` → `EvpnSvi`.

### `IpamRouteTarget` — `Ipam.RouteTarget`

A route target. Attributes: `name` (unique), `description`. Relationships: `vrf` → `IpamVRF`.

## EVPN services

### `EvpnTenant` — `Evpn.Tenant`

An EVPN tenant. Attributes: `name` (unique), `mac_vrf_vni_base`, `description`. Relationships: `fabrics` → `NetworkFabric`, `vrfs` → `IpamVRF`, `l2vlans` → `EvpnL2Vlan` (component).

### `EvpnSvi` — `Evpn.Svi`

An SVI. Attributes: `name`, `svi_id`, `ip_address_virtual`, `enabled`. Relationships: `vrf` → `IpamVRF` (parent), `vlan` → `IpamVLAN`, `rack_tags` → `LocationRack`, `avd_tags` → `AvdTag`.

### `EvpnL2Vlan` — `Evpn.L2Vlan`

An L2-only VLAN attached to a tenant. Attributes: `name`, `vlan_id`, `vni_override`. Relationships: `tenant` → `EvpnTenant` (parent), `vlan` → `IpamVLAN`.

### `EvpnDomain` — `Evpn.Domain`

An EVPN domain owned by one `NetworkFabric`. Attributes: `name`, `domain_id`, and optional `description`. Relationships: `fabric` -> `NetworkFabric` (parent), `pods` -> `NetworkPod`, `local_gateway_groups` -> `EvpnGatewayGroup` (component children), and `remote_gateway_groups` -> `EvpnGatewayGroup`. `domain_id` and `name` are unique per fabric. The hostvar generator uses `EvpnGatewayGroup.local_domain.domain_id` as the local EVPN Gateway D-PATH domain ID and `EvpnGatewayGroup.remote_domain.domain_id` as the remote D-PATH domain ID.

### `EvpnGatewayGroup` — `Evpn.GatewayGroup`

EVPN Multi-Domain Gateway intent shared by one or more Border Leaf devices in a selected Pod. Attributes include `resiliency_model` (only `all_active_multihoming`), EVPN L2/L3 enablement flags, D-PATH enablement, All-Active Multihoming enablement, and Ethernet Segment identifier/RT import values. Relationships: `local_domain` -> `EvpnDomain` (parent), `pod` -> `NetworkPod` (required non-owning context), `remote_domain` -> `EvpnDomain`, and `members` -> `DcimDevice`. The selected Pod must have `evpn_domain` set to the same object as `local_domain`, `remote_domain` must differ from `local_domain`, and group names are unique by `[local_domain, pod, name__value]`. Its schema-valid HFID uses the selected Pod and group name, while the display label and ordering include native `local_domain`, `pod`, `remote_domain`, and `name` fields. Reviewers distinguish the parent local domain from the EVPN Domain relationship view through `EvpnDomain.local_gateway_groups`; no computed or denormalized helper attribute is added solely for local-domain display.

`NetworkFabric.evpn_domains`, `NetworkPod.evpn_domain`, `NetworkPod.evpn_gateway_groups`, and `DcimDevice.evpn_gateway_group` are additive relationships from `evpn/evpn_gateway.yml`. Both `EvpnDomain` and `EvpnGatewayGroup` set `include_in_menu: false` because the custom EVPN Services menu exposes one Domains item for `EvpnDomain`; gateway groups are reached from EVPN Domain relationship views.

## Compute

### `ComputePhysicalServer` — `Compute.PhysicalServer`

A physical server. Inherits `Compute.GenericUnit`, `Dcim.GenericDevice`, and `Generator.Target`. Attributes: `name`, `role` (`compute`, `gpu`), `status`. Relationships: `rack` → `LocationRack`, `interfaces` → `DcimInterface`.

## AVD

### `AvdArtifact` — `Avd.Artifact`

Per-device container linking a device to its stored hostvars and structured config. Attributes: `name` (unique). Relationships: `device` → `DcimDevice` (required), `hostvar_file` → `AvdHostvarFile` (component), `structured_config_file` → `AvdStructuredConfigFile` (component). See [AvdArtifact & File Storage](./avd/artifacts.md).

### `AvdHostvarFile` — `Avd.HostvarFile` · `AvdStructuredConfigFile` — `Avd.StructuredConfigFile`

Child file nodes holding the per-device hostvars and structured-config JSON. Both inherit `CoreFileObject` (providing `content`, `content_type`, `checksum`) and are parented by `AvdArtifact`.

### `AvdEvpn` — `Avd.Evpn`

AVD EVPN fabric-wide settings. Attributes include `ebgp_multihop` and `overlay_bgp_rtc`. Relationships: `fabric` → `NetworkFabric`.

### `AvdTag` — `Avd.Tag`

AVD-specific fabric tag object. Attributes: `name`, `description`. Relationships: `racks` → `LocationRack`; reciprocal rack assignments emit pyAVD node-group `filter.tags`, and SVI `avd_tags` emit pyAVD SVI `tags`.

## Generator target

### `GeneratorTarget` — `Generator.Target` (generic)

Mixed into kinds that can be generator targets (`NetworkPod`, `LocationRack`, `ComputePhysicalServer`). Provides `checksum` (optional), which stores a hash of related node IDs for idempotent regeneration.

## Dropdown reference

**Device role** (`DcimDevice.role`): `super_spine`, `spine`, `leaf`, `border_leaf`, `l2leaf`.

**Interface role** (`DcimInterface.role`): `uplink`, `access`, `spine`, `super_spine`, `leaf`, `loopback`, `server`, `storage`, `mlag_peer`.

**Pod role** (`NetworkPod.role`): `fabric`, `cpu`, `storage`.

**Prefix role** (`IpamPrefix.role`): `supernet`, `fabric_supernet`, `super_spine_loopback`, `pod_supernet`, `pod_loopback`, `pod_super_spine_spine`, `pod_leaf_spine`, `loopback`, `loopback-vtep`, `technical`, `management`, `backfill`.

**Prefix status** (`IpamPrefix.status`): `active`, `deprecated`, `reserved`.

## Source {#protocols}

- [`schemas/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/schemas) — all schema definitions.
- [`schemas/base/dcim.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/dcim.yml) — base `Dcim.GenericDevice` / `Dcim.PhysicalDevice` / `Dcim.Device`, interfaces, `DcimDeviceType`; project device extensions (`role`, `bgp_asn`, relations) and `Network.Link` live in [`schemas/dcim_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/dcim_extensions.yml).
- [`schemas/logical_design.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/logical_design.yml) — `Network.Fabric`, `Network.Pod`.
- [`schemas/base/location.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/location.yml) + [`schemas/location_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/location_extensions.yml) — `Location.Hall`, `Location.Rack`.
- [`schemas/base/ipam.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/ipam.yml) + [`schemas/ipam_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/ipam_extensions.yml) — IPAM nodes (the `Prefix` `role`/`status` dropdowns live in the extension).
- [`schemas/avd/avd.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/avd/avd.yml) — `Avd.Evpn`, `Avd.Tag`.
- [`schemas/objects/objects.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/objects/objects.yml) — `Avd.Artifact`, `Avd.HostvarFile`, `Avd.StructuredConfigFile` (see [AvdArtifact & File Storage](./avd/artifacts.md) for the full reference).
- Generated protocols: [`src/solution_arista_avd/protocols.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/protocols.py) — regenerate after any schema change with:
  ```bash
  uv run infrahubctl protocols --out src/solution_arista_avd/protocols.py
  ```
  Note the `--out` flag (not `--output`) and the explicit path — the default would drop `schema_protocols.py` in the current directory instead of overwriting the checked-in file.
