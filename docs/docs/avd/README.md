# AVD Integration

This document describes how Arista Validated Design (AVD) is integrated with Infrahub to generate EOS configurations and documentation from the network data model.

## Overview

The integration uses [pyAVD](https://avd.arista.com/5.5/docs/pyavd/pyavd.html) to transform Infrahub fabric data into Arista EOS configurations. The pipeline follows a two-phase approach:

```
Infrahub Data Model
        │
        ▼
┌───────────────────────────────┐
│  Phase 1: Device Hostvars     │  Per-device generator
│  (generate-avd-device-hostvar)│
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Phase 2: Structured Config   │  Fabric-level generator
│  (generate-avd-device-        │
│   structured-config)          │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Transforms (on-demand)       │
│  • EOS CLI configuration      │
│  • Fabric documentation       │
│  • Device documentation       │
└───────────────────────────────┘
```

## Components

### Generators

| Generator | Target | Purpose |
|-----------|--------|---------|
| `generate-avd-device-hostvar` | Per device | Extracts device data and builds pyAVD hostvars |
| `generate-avd-device-structured-config` | Per fabric | Generates AVD structured configs for all devices |

### Transforms

| Transform | Output | Content Type |
|-----------|--------|--------------|
| `avd_eos_config` | EOS CLI commands | `text/plain` |
| `avd_fabric_doc` | Fabric documentation | `text/markdown` |
| `avd_device_doc` | Device documentation | `text/markdown` |

### Artifacts

| Artifact | Description |
|----------|-------------|
| `avd_eos_configuration` | Device startup configuration |
| `avd_fabric_documentation` | Fabric-wide documentation |
| `avd_device_documentation` | Per-device documentation |

## Data Model

### Role Mapping

Infrahub device roles map to AVD types:

| Infrahub Role | AVD Type |
|---------------|----------|
| `super_spine` | `super-spine` |
| `spine` | `spine` |
| `leaf` | `l3leaf` |

### AvdArtifact Schema

The `AvdArtifact` node stores intermediate data in Infrahub's object store:

```yaml
AvdArtifact:
  attributes:
    - hostvar_identifier      # Object store ID for hostvars JSON
    - hostvar_checksum        # Checksum for change detection
    - structured_config_identifier  # Object store ID for structured config
    - structured_config_checksum    # Checksum for change detection
  relationships:
    - device: NetworkDevice   # One-to-one with device
```

### AvdEvpn Schema

Optional EVPN configuration per fabric:

```yaml
AvdEvpn:
  attributes:
    - name: Text
    - ebgp_multihop: Number (optional)
    - overlay_bgp_rtc: Boolean (default: false)
  relationships:
    - fabric: NetworkFabric
```

## Data Flow

### Phase 1: Device Hostvars Generation

The `GenerateAVDDeviceHostvar` generator (`generators/generate_avd_device_hostvar.py`) runs per device and:

1. Extracts device attributes (hostname, role, BGP ASN, node ID)
2. Extracts IP addresses (loopback, management)
3. Determines uplink topology based on device role
4. Extracts connected endpoints (servers) with VLAN configuration
5. Builds pyAVD-compatible hostvars structure
6. Uploads hostvars JSON to object store
7. Creates/updates `AvdArtifact` with identifier and checksum

**Uplink Role Determination:**
- `spine` devices → uplinks from `super_spine` interfaces
- `leaf` devices → uplinks from `spine` interfaces
- `super_spine` devices → no uplinks

**Connected Endpoints:**
Server connections are extracted from interfaces with `role="server"`, including:
- Tagged VLANs (trunk mode)
- Untagged VLAN (access mode or native VLAN)

### Phase 2: Structured Config Generation

The `AvdDeviceStructuredConfigGenerator` generator (`generators/generate_avd_device_structured_config.py`) runs per fabric and:

1. Traverses fabric hierarchy to find all devices (pods → devices, racks → devices)
2. Fetches hostvars from object store for each device
3. Validates inputs with `pyavd.validate_inputs()`
4. Generates AVD facts with `pyavd.get_avd_facts()`
5. Generates structured config per device with `pyavd.get_device_structured_config()`
6. Uploads structured configs to object store
7. Updates `AvdArtifact` with structured config identifier

### Transforms

Transforms read from the object store and generate final outputs:

**AvdEosConfigTransform** (`transforms/avd_eos_config.py`):
```python
structured_config = await client.object_store.get(identifier=...)
return pyavd.get_device_config(structured_config)
```

**AvdFabricDocTransform** (`transforms/avd_fabric_doc.py`):
```python
avd_facts = pyavd.get_avd_facts(all_hostvars)
return pyavd.get_fabric_documentation(avd_facts, structured_configs, fabric_name)
```

## Usage

### Running the Generators

Run generators in order after infrastructure is created:

```bash
# Phase 1: Generate hostvars for each device
# Run from Infrahub UI: Actions > Generator definitions > generate-avd-device-hostvar

# Phase 2: Generate structured configs for entire fabric
# Run from Infrahub UI: Actions > Generator definitions > generate-avd-device-structured-config
```

### Viewing Artifacts

Artifacts are generated on-demand when accessed:
- Navigate to a device → Artifacts → "AVD EOS Configuration"
- Navigate to a fabric → Artifacts → "AVD Fabric Documentation"

## File Structure

```
generators/
├── generate_avd_device_hostvar.py      # Per-device hostvars generator
├── generate_avd_device_structured_config.py  # Fabric structured config generator
├── generate_avd.gql                    # Fabric-level GraphQL query
├── avd_device_hostvar.gql              # Device-level GraphQL query
├── generate_avd_inputs_query.py        # Pydantic model for fabric query
└── generate_avd_device_inputs_query.py # Pydantic model for device query

transforms/
├── avd_eos_config.py                   # EOS CLI config transform
├── avd_fabric_doc.py                   # Fabric documentation transform
├── avd_device_doc.py                   # Device documentation transform
├── avd_device_config.gql               # Device config query
├── avd_fabric_devices.gql              # Fabric devices query
└── avd_*_query.py                      # Pydantic models for queries

schemas/avd/
└── avd.yml                             # AvdEvpn schema definition

src/solution_ai_dc/
└── avd.py                              # AvdInputsBuilder utility class
```

## Configuration

All AVD components are registered in `.infrahub.yml`:

```yaml
queries:
  - name: avd_device_hostvar
    file_path: "./generators/avd_device_hostvar.gql"
  - name: generate_avd
    file_path: "./generators/generate_avd.gql"
  - name: avd_device_config
    file_path: "./transforms/avd_device_config.gql"
  - name: avd_fabric_devices
    file_path: "./transforms/avd_fabric_devices.gql"

generator_definitions:
  - name: generate-avd-device-hostvar
    file_path: "./generators/generate_avd_device_hostvar.py"
    class_name: GenerateAVDDeviceHostvar
    targets: avd_devices

  - name: generate-avd-device-structured-config
    file_path: "./generators/generate_avd_device_structured_config.py"
    class_name: AvdDeviceStructuredConfigGenerator
    targets: fabrics

python_transforms:
  - name: avd_eos_config
    class_name: AvdEosConfigTransform
    file_path: "./transforms/avd_eos_config.py"
  - name: avd_fabric_doc
    class_name: AvdFabricDocTransform
    file_path: "./transforms/avd_fabric_doc.py"
  - name: avd_device_doc
    class_name: AvdDeviceDocTransform
    file_path: "./transforms/avd_device_doc.py"

artifact_definitions:
  - name: avd_eos_configuration
    targets: avd_devices
    transformation: avd_eos_config
  - name: avd_fabric_documentation
    targets: fabrics
    transformation: avd_fabric_doc
  - name: avd_device_documentation
    targets: avd_devices
    transformation: avd_device_doc
```

## Dependencies

- **pyavd** - Arista AVD Python library
- **netutils** - Network utilities (VLAN list formatting)
- **infrahub-sdk** - Infrahub SDK for generators and transforms

## Hostvars Structure

Example hostvars generated for a leaf device:

```json
{
  "type": "l3leaf",
  "fabric_name": "Fabric-A",
  "mgmt_gateway": "10.255.0.1",
  "l3leaf": {
    "nodes": [
      {
        "name": "leaf-pod-A1-1",
        "id": 1,
        "bgp_as": "65101",
        "loopback_ipv4_address": "10.255.1.1",
        "loopback_ipv4_pool": "10.255.0.0/24",
        "mgmt_ip": "10.255.0.11/24",
        "uplink_ipv4_pool": "10.250.0.0/16",
        "vtep_loopback_ipv4_pool": "10.251.0.0/24",
        "uplink_interfaces": ["Ethernet1", "Ethernet2"],
        "uplink_switches": ["spine-A1-1", "spine-A1-2"],
        "uplink_switch_interfaces": ["Ethernet1", "Ethernet1"]
      }
    ]
  },
  "servers": [
    {
      "name": "server-1",
      "adapters": [
        {
          "endpoint_ports": ["eth0"],
          "switch_ports": ["Ethernet10"],
          "switches": ["leaf-pod-A1-1"],
          "mode": "trunk",
          "vlans": "100-105"
        }
      ]
    }
  ]
}
```

## Troubleshooting

### Validation Errors

If `pyavd.validate_inputs()` fails, check:
- Device has `bgp_asn` and `node_id` assigned
- Loopback IP is properly formatted (CIDR stripped)
- Uplink interfaces have valid links to upstream devices

### Missing Structured Config

If EOS config transform returns "No structured config available":
1. Verify hostvars generator ran successfully
2. Run the structured config generator for the fabric
3. Check `AvdArtifact` has `structured_config_identifier` populated

### Object Store Issues

Hostvars and structured configs are stored in Infrahub's object store. To debug:
```python
# Fetch hostvars manually
content = await client.object_store.get(identifier=hostvar_identifier)
hostvars = json.loads(content)
```
