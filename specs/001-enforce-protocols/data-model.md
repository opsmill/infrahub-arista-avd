# Data Model: Enforce Protocol-Typed Access

**Branch**: `001-enforce-protocols` | **Date**: 2026-02-10

## Overview

This feature does not introduce new data entities. It enforces typed access to existing entities via protocol classes and Pydantic query models. The data model below documents the entities involved and their typed access mechanisms.

## Entities Requiring Protocol Class Generation

These entities are defined in `schemas/routing/routing.yml` but do not yet have protocol classes in `protocols.py`:

### RoutingBGPPeerGroup

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| name | String | Peer group name |
| type | String (optional) | Peer group type |
| remote_as | String (optional) | Remote AS number |
| device | Relationship → NetworkDevice | Parent device |

### RoutingBGPNeighbor

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| peer_address | String | Neighbor IP address |
| peer_group | Relationship → RoutingBGPPeerGroup | Associated peer group |
| remote_as | String (optional) | Remote AS number |
| description | String (optional) | Neighbor description |
| device | Relationship → NetworkDevice | Parent device |

### RoutingPrefixList

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| name | String | Prefix list name |
| device | Relationship → NetworkDevice | Parent device |

### RoutingPrefixListEntry

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| sequence | Integer | Sequence number |
| action | String | permit/deny |
| prefix | String (optional) | IP prefix |
| le | Integer (optional) | Less-than-or-equal mask length |
| ge | Integer (optional) | Greater-than-or-equal mask length |
| prefix_list | Relationship → RoutingPrefixList | Parent prefix list |

### RoutingRouteMap

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| name | String | Route map name |
| device | Relationship → NetworkDevice | Parent device |

### RoutingRouteMapEntry

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| sequence | Integer | Sequence number |
| type | String | permit/deny |
| description | String (optional) | Entry description |
| match | JSON (optional) | Match conditions |
| set | JSON (optional) | Set actions |
| route_map | Relationship → RoutingRouteMap | Parent route map |

### RoutingStaticRoute

| Attribute | Type | Notes |
| --------- | ---- | ----- |
| destination | String | Destination prefix |
| gateway | String (optional) | Next hop gateway |
| interface | String (optional) | Outgoing interface |
| distance | Integer (optional) | Administrative distance |
| name | String (optional) | Route name |
| device | Relationship → NetworkDevice | Parent device |

## Entities with Existing Protocol Classes (no changes needed)

- **IpamIPPrefix** — exists in `protocols.py` lines 210-231
- **IpamIPAddress** — exists in `protocols.py` lines 200-208
- **NetworkInterface** — exists in `protocols.py` lines 233-248
- **NetworkDevice** — exists in `protocols.py` lines 128-145
- **NetworkPod** — exists in `protocols.py` lines 287-305
- **AvdArtifact** — exists in `protocols.py`

## Pydantic Query Model Updates

### AvdFabricDevicesQuery (transforms/avd_fabric_devices_query.py)

The existing model needs to be extended to include the `avd_artifact` relationship path:

**Current structure**:
```
AvdFabricDevicesQuery
├── network_fabric → edges → node (id, name)
└── network_device → edges → node (id, hostname, pod → parent)
```

**Required structure**:
```
AvdFabricDevicesQuery
├── network_fabric → edges → node (id, name)
└── network_device → edges → node
    ├── id, hostname
    ├── pod → node → parent → node (id)
    └── avd_artifact → node
        ├── hostvar_identifier (value)
        └── structured_config_identifier (value)
```
