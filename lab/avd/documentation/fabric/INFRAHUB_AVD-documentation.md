# INFRAHUB_AVD

## Table of Contents

- [Fabric Switches and Management IP](#fabric-switches-and-management-ip)
  - [Fabric Switches with inband Management IP](#fabric-switches-with-inband-management-ip)
- [Fabric Topology](#fabric-topology)
- [Fabric IP Allocation](#fabric-ip-allocation)
  - [Fabric Point-To-Point Links](#fabric-point-to-point-links)
  - [Point-To-Point Links Node Allocation](#point-to-point-links-node-allocation)
  - [Loopback Interfaces (BGP EVPN Peering)](#loopback-interfaces-bgp-evpn-peering)
  - [Loopback0 Interfaces Node Allocation](#loopback0-interfaces-node-allocation)
  - [VTEP Loopback VXLAN Tunnel Source Interfaces (VTEPs Only)](#vtep-loopback-vxlan-tunnel-source-interfaces-vteps-only)
  - [VTEP Loopback Node allocation](#vtep-loopback-node-allocation)

## Fabric Switches and Management IP

| POD | Type | Node | Management IP | Platform | Provisioned in CloudVision | Serial Number |
| --- | ---- | ---- | ------------- | -------- | -------------------------- | ------------- |
| DC1_POD1 | l3leaf | ih-dc1-leaf1a | 10.0.6.13/24 | cEOSLab | Provisioned | INFRAHUB003 |
| DC1_POD1 | l3leaf | ih-dc1-leaf1b | 10.0.6.14/24 | cEOSLab | Provisioned | INFRAHUB004 |
| DC1_POD1 | l3leaf | ih-dc1-leaf2a | 10.0.6.15/24 | cEOSLab | Provisioned | INFRAHUB005 |
| DC1_POD1 | l3leaf | ih-dc1-leaf2b | 10.0.6.16/24 | cEOSLab | Provisioned | INFRAHUB006 |
| DC1_POD1 | spine | ih-dc1-spine1 | 10.0.6.11/24 | cEOSLab | Provisioned | INFRAHUB001 |
| DC1_POD1 | spine | ih-dc1-spine2 | 10.0.6.12/24 | cEOSLab | Provisioned | INFRAHUB002 |
| DC2_POD1 | l3leaf | ih-dc2-leaf1a | 10.0.6.23/24 | cEOSLab | Provisioned | INFRAHUB013 |
| DC2_POD1 | l3leaf | ih-dc2-leaf1b | 10.0.6.24/24 | cEOSLab | Provisioned | INFRAHUB014 |
| DC2_POD1 | l3leaf | ih-dc2-leaf2a | 10.0.6.25/24 | cEOSLab | Provisioned | INFRAHUB015 |
| DC2_POD1 | l3leaf | ih-dc2-leaf2b | 10.0.6.26/24 | cEOSLab | Provisioned | INFRAHUB016 |
| DC2_POD1 | spine | ih-dc2-spine1 | 10.0.6.21/24 | cEOSLab | Provisioned | INFRAHUB011 |
| DC2_POD1 | spine | ih-dc2-spine2 | 10.0.6.22/24 | cEOSLab | Provisioned | INFRAHUB012 |

> Provision status is based on Ansible inventory declaration and do not represent real status from CloudVision.

### Fabric Switches with inband Management IP

| POD | Type | Node | Management IP | Inband Interface |
| --- | ---- | ---- | ------------- | ---------------- |

## Fabric Topology

| Type | Node | Node Interface | Peer Type | Peer Node | Peer Interface |
| ---- | ---- | -------------- | --------- | --------- | -------------- |
| l3leaf | ih-dc1-leaf1a | Ethernet5 | l3leaf | ih-dc2-leaf1a | Ethernet5 |
| l3leaf | ih-dc1-leaf1a | Ethernet6 | l3leaf | ih-dc2-leaf1b | Ethernet6 |
| l3leaf | ih-dc1-leaf1a | Ethernet49/1 | spine | ih-dc1-spine1 | Ethernet1/1 |
| l3leaf | ih-dc1-leaf1a | Ethernet50/1 | spine | ih-dc1-spine2 | Ethernet1/1 |
| l3leaf | ih-dc1-leaf1b | Ethernet5 | l3leaf | ih-dc2-leaf1b | Ethernet5 |
| l3leaf | ih-dc1-leaf1b | Ethernet6 | l3leaf | ih-dc2-leaf1a | Ethernet6 |
| l3leaf | ih-dc1-leaf1b | Ethernet49/1 | spine | ih-dc1-spine1 | Ethernet2/1 |
| l3leaf | ih-dc1-leaf1b | Ethernet50/1 | spine | ih-dc1-spine2 | Ethernet2/1 |
| l3leaf | ih-dc1-leaf2a | Ethernet49/1 | spine | ih-dc1-spine1 | Ethernet3/1 |
| l3leaf | ih-dc1-leaf2a | Ethernet50/1 | spine | ih-dc1-spine2 | Ethernet3/1 |
| l3leaf | ih-dc1-leaf2b | Ethernet49/1 | spine | ih-dc1-spine1 | Ethernet4/1 |
| l3leaf | ih-dc1-leaf2b | Ethernet50/1 | spine | ih-dc1-spine2 | Ethernet4/1 |
| l3leaf | ih-dc2-leaf1a | Ethernet49/1 | spine | ih-dc2-spine1 | Ethernet1/1 |
| l3leaf | ih-dc2-leaf1a | Ethernet50/1 | spine | ih-dc2-spine2 | Ethernet1/1 |
| l3leaf | ih-dc2-leaf1b | Ethernet49/1 | spine | ih-dc2-spine1 | Ethernet2/1 |
| l3leaf | ih-dc2-leaf1b | Ethernet50/1 | spine | ih-dc2-spine2 | Ethernet2/1 |
| l3leaf | ih-dc2-leaf2a | Ethernet49/1 | spine | ih-dc2-spine1 | Ethernet3/1 |
| l3leaf | ih-dc2-leaf2a | Ethernet50/1 | spine | ih-dc2-spine2 | Ethernet3/1 |
| l3leaf | ih-dc2-leaf2b | Ethernet49/1 | spine | ih-dc2-spine1 | Ethernet4/1 |
| l3leaf | ih-dc2-leaf2b | Ethernet50/1 | spine | ih-dc2-spine2 | Ethernet4/1 |

## Fabric IP Allocation

### Fabric Point-To-Point Links

| Uplink IPv4 Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ---------------- | ------------------- | ------------------ | ------------------ |
| 10.250.3.0/24 | 256 | 16 | 6.25 % |
| 10.251.3.0/24 | 256 | 16 | 6.25 % |

### Point-To-Point Links Node Allocation

| Node | Node Interface | Node IP Address | Peer Node | Peer Interface | Peer IP Address |
| ---- | -------------- | --------------- | --------- | -------------- | --------------- |
| ih-dc1-leaf1a | Ethernet5 | 172.16.0.0/31 | ih-dc2-leaf1a | Ethernet5 | 172.16.0.1/31 |
| ih-dc1-leaf1a | Ethernet6 | 172.16.0.2/31 | ih-dc2-leaf1b | Ethernet6 | 172.16.0.3/31 |
| ih-dc1-leaf1a | Ethernet49/1 | 10.250.3.1/31 | ih-dc1-spine1 | Ethernet1/1 | 10.250.3.0/31 |
| ih-dc1-leaf1a | Ethernet50/1 | 10.250.3.3/31 | ih-dc1-spine2 | Ethernet1/1 | 10.250.3.2/31 |
| ih-dc1-leaf1b | Ethernet5 | 172.16.0.4/31 | ih-dc2-leaf1b | Ethernet5 | 172.16.0.5/31 |
| ih-dc1-leaf1b | Ethernet6 | 172.16.0.6/31 | ih-dc2-leaf1a | Ethernet6 | 172.16.0.7/31 |
| ih-dc1-leaf1b | Ethernet49/1 | 10.250.3.5/31 | ih-dc1-spine1 | Ethernet2/1 | 10.250.3.4/31 |
| ih-dc1-leaf1b | Ethernet50/1 | 10.250.3.7/31 | ih-dc1-spine2 | Ethernet2/1 | 10.250.3.6/31 |
| ih-dc1-leaf2a | Ethernet49/1 | 10.250.3.9/31 | ih-dc1-spine1 | Ethernet3/1 | 10.250.3.8/31 |
| ih-dc1-leaf2a | Ethernet50/1 | 10.250.3.11/31 | ih-dc1-spine2 | Ethernet3/1 | 10.250.3.10/31 |
| ih-dc1-leaf2b | Ethernet49/1 | 10.250.3.13/31 | ih-dc1-spine1 | Ethernet4/1 | 10.250.3.12/31 |
| ih-dc1-leaf2b | Ethernet50/1 | 10.250.3.15/31 | ih-dc1-spine2 | Ethernet4/1 | 10.250.3.14/31 |
| ih-dc2-leaf1a | Ethernet49/1 | 10.251.3.1/31 | ih-dc2-spine1 | Ethernet1/1 | 10.251.3.0/31 |
| ih-dc2-leaf1a | Ethernet50/1 | 10.251.3.3/31 | ih-dc2-spine2 | Ethernet1/1 | 10.251.3.2/31 |
| ih-dc2-leaf1b | Ethernet49/1 | 10.251.3.5/31 | ih-dc2-spine1 | Ethernet2/1 | 10.251.3.4/31 |
| ih-dc2-leaf1b | Ethernet50/1 | 10.251.3.7/31 | ih-dc2-spine2 | Ethernet2/1 | 10.251.3.6/31 |
| ih-dc2-leaf2a | Ethernet49/1 | 10.251.3.9/31 | ih-dc2-spine1 | Ethernet3/1 | 10.251.3.8/31 |
| ih-dc2-leaf2a | Ethernet50/1 | 10.251.3.11/31 | ih-dc2-spine2 | Ethernet3/1 | 10.251.3.10/31 |
| ih-dc2-leaf2b | Ethernet49/1 | 10.251.3.13/31 | ih-dc2-spine1 | Ethernet4/1 | 10.251.3.12/31 |
| ih-dc2-leaf2b | Ethernet50/1 | 10.251.3.15/31 | ih-dc2-spine2 | Ethernet4/1 | 10.251.3.14/31 |

### Loopback Interfaces (BGP EVPN Peering)

| Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------- | ------------------- | ------------------ | ------------------ |
| 10.250.1.0/24 | 256 | 6 | 2.35 % |
| 10.251.1.0/24 | 256 | 6 | 2.35 % |

### Loopback0 Interfaces Node Allocation

| POD | Node | Loopback0 |
| --- | ---- | --------- |
| DC1_POD1 | ih-dc1-leaf1a | 10.250.1.3/32 |
| DC1_POD1 | ih-dc1-leaf1b | 10.250.1.4/32 |
| DC1_POD1 | ih-dc1-leaf2a | 10.250.1.5/32 |
| DC1_POD1 | ih-dc1-leaf2b | 10.250.1.6/32 |
| DC1_POD1 | ih-dc1-spine1 | 10.250.1.1/32 |
| DC1_POD1 | ih-dc1-spine2 | 10.250.1.2/32 |
| DC2_POD1 | ih-dc2-leaf1a | 10.251.1.3/32 |
| DC2_POD1 | ih-dc2-leaf1b | 10.251.1.4/32 |
| DC2_POD1 | ih-dc2-leaf2a | 10.251.1.5/32 |
| DC2_POD1 | ih-dc2-leaf2b | 10.251.1.6/32 |
| DC2_POD1 | ih-dc2-spine1 | 10.251.1.1/32 |
| DC2_POD1 | ih-dc2-spine2 | 10.251.1.2/32 |

### VTEP Loopback VXLAN Tunnel Source Interfaces (VTEPs Only)

| VTEP Loopback Pool | Available Addresses | Assigned addresses | Assigned Address % |
| ------------------ | ------------------- | ------------------ | ------------------ |
| 10.250.2.0/24 | 256 | 4 | 1.57 % |
| 10.251.2.0/24 | 256 | 4 | 1.57 % |

### VTEP Loopback Node allocation

| POD | Node | Loopback1 |
| --- | ---- | --------- |
| DC1_POD1 | ih-dc1-leaf1a | 10.250.2.3/32 |
| DC1_POD1 | ih-dc1-leaf1b | 10.250.2.4/32 |
| DC1_POD1 | ih-dc1-leaf2a | 10.250.2.5/32 |
| DC1_POD1 | ih-dc1-leaf2b | 10.250.2.6/32 |
| DC2_POD1 | ih-dc2-leaf1a | 10.251.2.3/32 |
| DC2_POD1 | ih-dc2-leaf1b | 10.251.2.4/32 |
| DC2_POD1 | ih-dc2-leaf2a | 10.251.2.5/32 |
| DC2_POD1 | ih-dc2-leaf2b | 10.251.2.6/32 |
