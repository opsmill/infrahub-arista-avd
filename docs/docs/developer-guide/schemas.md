---
title: Schemas
description: All Infrahub schema definitions in this solution.
audience: developer
sidebar_position: 2
---

# Schemas

:::info Developer Guide
This page is part of the developer guide. It documents the YAML schema files that define the data model.
:::

This document describes all Infrahub schema definitions in this solution.

## Schema Files

All schemas are located in `schemas/`:

| File | Purpose |
|------|---------|
| `logical_design.yml` | Fabric and pod hierarchy |
| `device.yml` | Network devices, interfaces, links |
| `physical_location.yml` | Physical locations (halls, racks) |
| `ipam.yml` | IP addressing |
| `generator.yml` | Generator target tracking |
| `vlan/vlan.yml` | VLAN configuration |
| `compute/compute.yml` | Compute units |
| `avd/avd.yml` | AVD-specific configuration |
| `objects/objects.yml` | Generic object templates |

## Core Schemas

### NetworkFabric

Top-level container for a datacenter fabric.

```yaml
NetworkFabric:
  namespace: Network
  attributes:
    - name: Text (unique)
    - description: Text (optional)
    - supernet_pool: Dropdown (FabricSupernetPool)
  relationships:
    - pods: NetworkPod (one-to-many)
    - devices: NetworkDevice (one-to-many, super-spines)
```

### NetworkPod

A pod within a fabric containing spines and racks.

```yaml
NetworkPod:
  namespace: Network
  inherit_from: [BuildingBlock, GeneratorTarget]
  attributes:
    - name: Text
    - role: Dropdown (fabric, cpu, storage)
  relationships:
    - fabric: NetworkFabric (many-to-one)
    - racks: LocationRack (one-to-many)
    - devices: NetworkDevice (one-to-many, spines)
```

### NetworkDevice

A network device (switch, router).

```yaml
NetworkDevice:
  namespace: Network
  attributes:
    - name: Text (unique)
    - role: Dropdown (super_spine, spine, leaf)
    - status: Dropdown (provisioning, active, maintenance)
    - bgp_asn: Number (optional)
    - node_id: Number (optional)
  relationships:
    - device_type: DeviceType (many-to-one)
    - pod: NetworkPod (many-to-one, optional)
    - rack: LocationRack (many-to-one, optional)
    - interfaces: NetworkInterface (one-to-many, components)
    - loopback_ip: IpamIPAddress (one-to-one)
    - mgmt_ip: IpamIPAddress (one-to-one)
    - avd_artifact: AvdArtifact (one-to-one)
```

### NetworkInterface

A network interface on a device.

```yaml
NetworkInterface:
  namespace: Network
  attributes:
    - name: Text
    - description: Text (optional, computed)
    - role: Dropdown (uplink, access, spine, super_spine, leaf, loopback, server, storage)
    - enabled: Boolean (default: true)
    - speed: Text (optional)
    - mtu: Number (optional)
  relationships:
    - device: NetworkDevice (many-to-one, parent)
    - link: NetworkLink (one-to-one)
    - ip_addresses: IpamIPAddress (one-to-many)
    - tagged_vlans: Vlan (many-to-many)
    - untagged_vlan: Vlan (many-to-one)
```

### NetworkLink

A bidirectional link between interfaces.

```yaml
NetworkLink:
  namespace: Network
  attributes:
    - name: Text (optional)
  relationships:
    - interface_a: NetworkInterface (one-to-one)
    - interface_b: NetworkInterface (one-to-one)
```

## Location Schemas

### LocationHall

A physical datacenter hall.

```yaml
LocationHall:
  namespace: Location
  inherit_from: [Physical]
  attributes:
    - name: Text (unique)
    - description: Text (optional)
  relationships:
    - racks: LocationRack (one-to-many)
```

### LocationRack

A physical rack in a hall.

```yaml
LocationRack:
  namespace: Location
  inherit_from: [Physical, GeneratorTarget]
  attributes:
    - name: Text (unique)
    - row: Number (optional)
    - position: Number (optional)
  relationships:
    - hall: LocationHall (many-to-one)
    - pod: NetworkPod (many-to-one)
    - devices: NetworkDevice (one-to-many)
```

## IPAM Schemas

### IpamIPAddress

An IP address assignment.

```yaml
IpamIPAddress:
  namespace: Ipam
  attributes:
    - address: IPHost
    - role: Dropdown (loopback, management, interconnect, server)
  relationships:
    - interface: NetworkInterface (many-to-one)
    - device: NetworkDevice (many-to-one, for loopback/mgmt)
```

### IpamIPPrefix

An IP prefix/subnet.

```yaml
IpamIPPrefix:
  namespace: Ipam
  attributes:
    - prefix: IPNetwork
    - role: Dropdown (loopback, interconnect, management)
```

## Generator Schema

### GeneratorTarget

Generic for nodes that can be generator targets.

```yaml
GeneratorTarget:
  namespace: Generator
  kind: Generic
  attributes:
    - checksum: Text (optional)
      # Stores hash of related node IDs for change detection
```

## VLAN Schema

### Vlan

VLAN configuration.

```yaml
Vlan:
  namespace: Vlan
  attributes:
    - vlan_id: Number (1-4094)
    - name: Text (unique)
    - description: Text (optional)
  relationships:
    - l2_domain: L2Domain (many-to-one)
```

### L2Domain

Layer 2 domain containing VLANs.

```yaml
L2Domain:
  namespace: Vlan
  attributes:
    - name: Text (unique)
    - description: Text (optional)
  relationships:
    - vlans: Vlan (one-to-many)
```

## AVD Schema

### AvdArtifact

Stores AVD intermediate data.

```yaml
AvdArtifact:
  namespace: Avd
  attributes:
    - hostvar_identifier: Text
      # Object store ID for hostvars JSON
    - hostvar_checksum: Text
    - structured_config_identifier: Text
      # Object store ID for structured config
    - structured_config_checksum: Text
  relationships:
    - device: NetworkDevice (one-to-one)
```

### AvdEvpn

EVPN configuration for a fabric.

```yaml
AvdEvpn:
  namespace: Avd
  attributes:
    - name: Text
    - ebgp_multihop: Number (optional)
    - overlay_bgp_rtc: Boolean (default: false)
  relationships:
    - fabric: NetworkFabric (one-to-one)
```

## Device Metadata

### Manufacturer

Device manufacturer.

```yaml
Manufacturer:
  namespace: Organization
  attributes:
    - name: Text (unique)
```

### DeviceType

Device model/type.

```yaml
DeviceType:
  namespace: Device
  attributes:
    - name: Text (unique)
    - part_number: Text (optional)
  relationships:
    - manufacturer: Manufacturer (many-to-one)
```

## Generic Schemas

### BuildingBlock

Base generic for hierarchical fabric elements.

```yaml
BuildingBlock:
  kind: Generic
  attributes:
    - name: Text
    - description: Text (optional)
```

### Physical

Base generic for physical locations.

```yaml
Physical:
  kind: Generic
  attributes:
    - name: Text
    - description: Text (optional)
```

## Dropdown Values

### Device Roles
- `super_spine` - Super-spine/core switch
- `spine` - Spine switch
- `leaf` - Leaf/ToR switch

### Interface Roles
- `uplink` - Uplink to parent tier
- `access` - Access/server port
- `spine` - Connection to spine
- `super_spine` - Connection to super-spine
- `leaf` - Connection to leaf
- `loopback` - Loopback interface
- `server` - Server connection
- `storage` - Storage connection

### Pod Roles
- `fabric` - Network fabric pod (spines)
- `cpu` - Compute pod
- `storage` - Storage pod

### IP Roles
- `loopback` - Loopback addresses
- `management` - OOB management
- `interconnect` - Point-to-point links
- `server` - Server addressing

## Source

- [`schemas/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/schemas) — all schema definitions.
- [`schemas/base/dcim.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/dcim.yml) — base `Dcim.GenericDevice`/`Dcim.PhysicalDevice`/`Dcim.Device`, interfaces, `DeviceType`; project extensions (device `role`, `bgp_asn`, relations) and `Network.Link` live in [`schemas/dcim_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/dcim_extensions.yml).
- [`schemas/logical_design.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/logical_design.yml) — `NetworkFabric`, `NetworkPod`.
- [`schemas/base/location.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/location.yml) + [`schemas/location_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/location_extensions.yml) — `Location.Hall`, `Location.Rack`.
- [`schemas/base/ipam.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/base/ipam.yml) + [`schemas/ipam_extensions.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/ipam_extensions.yml) — IPAM nodes (the `Prefix` `role`/`status` dropdowns live in the extension).
- [`schemas/avd/avd.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/avd/avd.yml) — `AvdEvpn` and related AVD-specific nodes.
- [`schemas/objects/objects.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/schemas/objects/objects.yml) — `AvdArtifact`, `AvdHostvarFile`, `AvdStructuredConfigFile` (see [AvdArtifact & File Storage](./avd/artifacts.md) for the full reference).
- Generated protocols: [`src/solution_arista_avd/protocols.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/protocols.py) — regenerate after any schema change with:
  ```bash
  uv run infrahubctl protocols --out src/solution_arista_avd/protocols.py
  ```
  Note the `--out` flag (not `--output`) and the explicit path — the default would drop `schema_protocols.py` in the current directory instead of overwriting the checked-in file.
