# AVD Integration Plan for Infrahub

## Overview

Integrate pyAVD with Infrahub to generate Arista EOS configurations from fabric data. This is an **incremental Phase 1** implementation focusing on forward configuration generation, with backfill deferred to Phase 2.

**Architecture Flow:**
```
Infrahub Data → AVD Input Builder → pyAVD → EOS Config / Docs
```

---

## Phase 1 Scope

### What's Included
- Schema extensions for BGP ASN (using CoreNumberPool), node ID, management IP
- Extend existing NetworkFabric with AVD attributes (no separate settings node)
- AVD Input Builder transform (Infrahub → pyAVD hostvars)
- EOS CLI config generation via `pyavd.get_device_config()`
- Fabric and device documentation generation

### What's Deferred (Phase 2)
- VRF/VLAN/Tenant service layer schemas
- EVPN overlay configuration
- Backfill (importing AVD structured config back to Infrahub)
- Connected endpoints (server port profiles)

---

## Implementation Steps

### Step 1: Schema Extensions

**1.1 Modify `schemas/logical_design.yml`** - Extend NetworkFabric with AVD attributes:
```yaml
# Add to NetworkFabric node attributes:
- name: mgmt_gateway
  label: Management Gateway
  kind: Text
  optional: true
  order_weight: 5000

# Add to NetworkFabric relationships:
- name: asn_pool
  label: BGP ASN Pool
  peer: CoreNumberPool
  kind: Attribute
  cardinality: one
  optional: true
  identifier: "fabric__asn_pool"
  order_weight: 6000

- name: node_id_pool
  label: Node ID Pool
  peer: CoreNumberPool
  kind: Attribute
  cardinality: one
  optional: true
  identifier: "fabric__node_id_pool"
  order_weight: 7000

- name: mgmt_pool
  label: Management IP Pool
  peer: CoreIPAddressPool
  kind: Attribute
  cardinality: one
  optional: true
  identifier: "fabric__mgmt_pool"
  order_weight: 8000
```

**1.2 Modify `schemas/device.yml`** - Add to NetworkDevice:
```yaml
attributes:
  - name: bgp_asn
    kind: Number
    optional: true
  - name: node_id
    kind: Number
    optional: true
  # AVD intermediate data storage
  - name: avd_inputs
    label: AVD Inputs (hostvars)
    kind: JSON
    optional: true
    description: "Per-device pyAVD hostvars input structure"
  - name: avd_structured_config
    label: AVD Structured Config
    kind: JSON
    optional: true
    description: "Device structured configuration from pyAVD"
relationships:
  - name: mgmt_ip
    peer: IpamIPAddress
    kind: Attribute
    cardinality: one
    optional: true
    identifier: "device__mgmt_ip"
```

The JSON attributes store:
- `avd_inputs`: The hostvars dict for this device (type, id, bgp_as, uplinks, etc.)
- `avd_structured_config`: The output from `pyavd.get_device_structured_config()`

**1.3 Modify `schemas/ipam.yml`** - Add role choice:
```yaml
- name: management
  label: Management
```

### Step 2: Object Data - Create ASN and Node ID Pools

**Modify `objects/04_ipam.yml`** - Add number pools for ASN and Node ID:
```yaml
# ASN Pool for Fabric-A (private ASN range)
- kind: CoreNumberPool
  name: Fabric-A-ASN-Pool
  node: NetworkDevice
  node_attribute: bgp_asn
  start_range: 65000
  end_range: 65999

# Node ID Pool for Fabric-A
- kind: CoreNumberPool
  name: Fabric-A-NodeID-Pool
  node: NetworkDevice
  node_attribute: node_id
  start_range: 1
  end_range: 9999

# Similar for Fabric-B with different ranges
- kind: CoreNumberPool
  name: Fabric-B-ASN-Pool
  node: NetworkDevice
  node_attribute: bgp_asn
  start_range: 65100
  end_range: 65199
```

**Modify `objects/10_fabric.yml`** - Add AVD attributes to fabrics:
```yaml
# Add to Fabric-A:
mgmt_gateway: "10.255.0.1"
asn_pool: "Fabric-A-ASN-Pool"
node_id_pool: "Fabric-A-NodeID-Pool"
mgmt_pool: "Fabric-A-mgmt-pool"  # Created by generator
```

### Step 3: AVD Utilities Module

**New file: `src/solution_ai_dc/avd.py`**

Key functions:
- `AvdInputsBuilder.build_from_query()` - Transform Infrahub data to pyAVD hostvars
- `allocate_asn_from_pool(client, pool, device)` - Allocate ASN from CoreNumberPool
- `allocate_node_id_from_pool(client, pool, device)` - Allocate node ID from CoreNumberPool
- Role mapping: `super_spine` → `super-spine`, `spine` → `spine`, `leaf` → `l3leaf`

### Step 4: Generator Modifications

**4.1 Modify `generators/generate_fabric.py`**
- Allocate management IP pool from fabric supernet
- Allocate `bgp_asn` from fabric's `asn_pool` (CoreNumberPool)
- Allocate `node_id` from fabric's `node_id_pool` (CoreNumberPool)
- Assign management IPs from pool

**4.2 Modify `generators/generate_pod.py`**
- Allocate `bgp_asn` from fabric's `asn_pool` for spine switches
- Allocate `node_id` from fabric's `node_id_pool`
- Assign management IPs

**4.3 Modify `generators/generate_rack.py`**
- Allocate `bgp_asn` from fabric's `asn_pool` for leaf switches
- Allocate `node_id` from fabric's `node_id_pool`
- Assign management IPs

### Step 5: AVD Generators and Transforms

The pipeline uses generators to populate JSON attributes, then transforms to produce artifacts.

**Pipeline Flow:**
```
1. AVD Input Builder (Generator)
   └─ Stores hostvars in device.avd_inputs (JSON)

2. AVD Structured Config (Generator)
   └─ Reads device.avd_inputs
   └─ Runs pyavd.get_device_structured_config()
   └─ Stores result in device.avd_structured_config (JSON)

3. AVD EOS Config (Transform)
   └─ Reads device.avd_structured_config
   └─ Runs pyavd.get_device_config()
   └─ Outputs EOS CLI artifact

4. AVD Docs (Transform)
   └─ Reads device.avd_structured_config
   └─ Generates device/fabric documentation
```

**5.1 New file: `generators/generate_avd_inputs.py`** (Generator)
```python
class AvdInputsGenerator(InfrahubGenerator):
    """Builds and stores pyAVD hostvars for all devices in a fabric."""

    async def generate(self, data: dict) -> None:
        fabric = data["NetworkFabric"]["edges"][0]["node"]

        # Build hostvars for all devices
        for device in self.get_all_fabric_devices(fabric):
            hostvars = self.build_device_hostvars(device)

            # Store in JSON attribute
            device_obj = await self.client.get(kind="NetworkDevice", id=device["id"])
            device_obj.avd_inputs.value = hostvars
            await device_obj.save()
```

**5.2 New file: `generators/generate_avd_structured_config.py`** (Generator)
```python
class AvdStructuredConfigGenerator(InfrahubGenerator):
    """Generates and stores AVD structured config for all devices."""

    async def generate(self, data: dict) -> None:
        # Collect all device hostvars from stored avd_inputs
        all_hostvars = {}
        for device in self.get_all_fabric_devices(data):
            hostname = device["hostname"]["value"]
            all_hostvars[hostname] = device["avd_inputs"]["value"]

        # Generate AVD facts (requires all devices)
        avd_facts = pyavd.get_avd_facts(all_hostvars)

        # Generate and store structured config per device
        for hostname, hostvars in all_hostvars.items():
            structured_config = pyavd.get_device_structured_config(
                hostname, all_hostvars, avd_facts
            )

            device_obj = await self.client.get(kind="NetworkDevice", hostname__value=hostname)
            device_obj.avd_structured_config.value = structured_config
            await device_obj.save()
```

**5.3 New file: `transforms/avd_eos_config.py`** (Transform)
```python
class AvdEosConfigTransform(InfrahubTransform):
    """Generates EOS CLI config from stored structured config."""
    query = "avd_device_config"

    async def transform(self, data: dict) -> str:
        device = data["NetworkDevice"]["edges"][0]["node"]
        structured_config = device["avd_structured_config"]["value"]

        # Generate EOS CLI from stored structured config
        return pyavd.get_device_config(structured_config)
```

**5.4 New file: `transforms/avd_fabric_doc.py`** (Transform)
```python
class AvdFabricDocTransform(InfrahubTransform):
    """Generates fabric documentation from stored structured configs."""
    query = "avd_fabric_devices"

    async def transform(self, data: dict) -> str:
        fabric = data["NetworkFabric"]["edges"][0]["node"]

        # Collect stored data from all devices
        all_hostvars = {}
        structured_configs = {}
        for device in self.get_all_devices(fabric):
            hostname = device["hostname"]["value"]
            all_hostvars[hostname] = device["avd_inputs"]["value"]
            structured_configs[hostname] = device["avd_structured_config"]["value"]

        avd_facts = pyavd.get_avd_facts(all_hostvars)
        fabric_doc = pyavd.get_fabric_documentation(
            avd_facts, structured_configs, fabric["name"]["value"]
        )
        return fabric_doc.content
```

**5.5 GraphQL Queries:**
- `transforms/avd_device_config.gql` - Fetch single device with avd_structured_config
- `transforms/avd_fabric_devices.gql` - Fetch fabric with all devices and their AVD JSON attributes
- `generators/generate_avd_inputs.gql` - Fetch fabric with full topology for input building
- `generators/generate_avd_structured_config.gql` - Fetch fabric devices with avd_inputs

### Step 6: Configuration Updates

**6.1 Update `.infrahub.yml`**
```yaml
queries:
  # AVD Generator queries
  - name: generate_avd_inputs
    file_path: "./generators/generate_avd_inputs.gql"
  - name: generate_avd_structured_config
    file_path: "./generators/generate_avd_structured_config.gql"

  # AVD Transform queries
  - name: avd_device_config
    file_path: "./transforms/avd_device_config.gql"
  - name: avd_fabric_devices
    file_path: "./transforms/avd_fabric_devices.gql"

generator_definitions:
  # AVD Input Builder - populates device.avd_inputs
  - name: generate-avd-inputs
    file_path: "./generators/generate_avd_inputs.py"
    query: generate_avd_inputs
    targets: fabrics
    parameters:
      fabric_name: name__value
    class_name: AvdInputsGenerator
    convert_query_response: false

  # AVD Structured Config - populates device.avd_structured_config
  - name: generate-avd-structured-config
    file_path: "./generators/generate_avd_structured_config.py"
    query: generate_avd_structured_config
    targets: fabrics
    parameters:
      fabric_name: name__value
    class_name: AvdStructuredConfigGenerator
    convert_query_response: false

python_transforms:
  - name: avd_eos_config
    class_name: AvdEosConfigTransform
    file_path: "./transforms/avd_eos_config.py"
  - name: avd_fabric_doc
    class_name: AvdFabricDocTransform
    file_path: "./transforms/avd_fabric_doc.py"

artifact_definitions:
  - name: "avd_eos_configuration"
    artifact_name: "AVD EOS Configuration"
    parameters:
      name: "hostname__value"
    content_type: "text/plain"
    targets: "devices"
    transformation: "avd_eos_config"
  - name: "avd_fabric_documentation"
    artifact_name: "AVD Fabric Documentation"
    parameters:
      name: "name__value"
    content_type: "text/markdown"
    targets: "fabrics"
    transformation: "avd_fabric_doc"
```

**6.2 Update `pyproject.toml`**
```toml
dependencies = [
    "httpx>=0.28.1",
    "pyavd>=5.0.0",
]
```

### Step 7: Testing

**7.1 Unit tests: `tests/unit/test_avd.py`**
- Test BGP ASN calculation for each role
- Test node ID calculation
- Test role-to-AVD-type mapping
- Test uplink extraction from links

**7.2 Integration tests: `tests/integration/test_avd_transforms.py`**
- Test AVD inputs transform produces valid structure
- Test pyavd.validate_inputs() passes
- Test EOS config generation
- Test fabric doc generation

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| **Schemas** | | |
| `schemas/logical_design.yml` | MODIFY | Add AVD attributes to NetworkFabric (mgmt_gateway, asn_pool, node_id_pool, mgmt_pool) |
| `schemas/device.yml` | MODIFY | Add bgp_asn, node_id, mgmt_ip, avd_inputs (JSON), avd_structured_config (JSON) |
| `schemas/ipam.yml` | MODIFY | Add management role |
| **Object Data** | | |
| `objects/04_ipam.yml` | MODIFY | Add CoreNumberPool for ASN and Node ID per fabric |
| `objects/10_fabric.yml` | MODIFY | Add AVD attributes (mgmt_gateway, pool references) |
| **Utilities** | | |
| `src/solution_ai_dc/avd.py` | CREATE | AVD utilities and hostvars builders |
| **Existing Generators** | | |
| `generators/generate_fabric.py` | MODIFY | Allocate from ASN/Node ID pools for super-spines |
| `generators/generate_pod.py` | MODIFY | Allocate spine ASNs/IDs from pools |
| `generators/generate_rack.py` | MODIFY | Allocate leaf ASNs/IDs from pools |
| **AVD Generators (NEW)** | | |
| `generators/generate_avd_inputs.py` | CREATE | Builds and stores pyAVD hostvars in device.avd_inputs |
| `generators/generate_avd_inputs.gql` | CREATE | GraphQL query for fabric topology |
| `generators/generate_avd_structured_config.py` | CREATE | Generates structured config, stores in device.avd_structured_config |
| `generators/generate_avd_structured_config.gql` | CREATE | Query to fetch devices with avd_inputs |
| **AVD Transforms** | | |
| `transforms/avd_eos_config.py` | CREATE | EOS config transform (reads avd_structured_config) |
| `transforms/avd_device_config.gql` | CREATE | Query for single device with AVD data |
| `transforms/avd_fabric_doc.py` | CREATE | Fabric doc transform |
| `transforms/avd_fabric_devices.gql` | CREATE | Query for fabric with all device AVD data |
| **Configuration** | | |
| `.infrahub.yml` | MODIFY | Register new generators, transforms, artifacts |
| `pyproject.toml` | MODIFY | Add pyavd dependency |
| **Tests** | | |
| `tests/unit/test_avd.py` | CREATE | Unit tests for AVD utilities |
| `tests/integration/test_avd_transforms.py` | CREATE | Integration tests for AVD pipeline |

---

## Data Mapping: Infrahub → AVD

| Infrahub Concept | AVD Concept |
|------------------|-------------|
| NetworkFabric.name | fabric_name |
| NetworkDevice.role (super_spine) | type: super-spine |
| NetworkDevice.role (spine) | type: spine |
| NetworkDevice.role (leaf) | type: l3leaf |
| NetworkDevice.bgp_asn (from CoreNumberPool) | bgp_as |
| NetworkDevice.node_id (from CoreNumberPool) | id |
| NetworkDevice.loopback_ip | loopback_ipv4_address |
| NetworkDevice.mgmt_ip | mgmt_ip |
| NetworkFabric.mgmt_gateway | mgmt_gateway |
| NetworkLink → remote device | uplink_switches |
| NetworkInterface.name (uplink) | uplink_interfaces |
| Remote interface name | uplink_switch_interfaces |

---

## CoreNumberPool Allocation Pattern

Using Infrahub's built-in resource manager for ASN and Node ID allocation:

```python
# In generator code - allocate ASN from pool
async def allocate_device_asn(self, device: NetworkDevice, asn_pool: CoreNumberPool):
    """Allocate BGP ASN from fabric's ASN pool."""
    # The pool automatically allocates the next available number
    device.bgp_asn = asn_pool  # SDK handles allocation
    await device.save()

# Alternative: Manual allocation via GraphQL mutation
mutation {
    CoreNumberPoolAllocate(
        data: {
            id: "<asn-pool-id>"
            identifier: "device-hostname"
        }
    ) {
        ok
        resource {
            id
            value
        }
    }
}
```

Benefits of using CoreNumberPool:
- Automatic sequential allocation
- Prevents duplicate ASN/ID conflicts
- Visible in Infrahub UI for tracking
- Supports range-based allocation (e.g., 65000-65999 for private ASNs)

---

## Execution Workflow

The AVD pipeline runs in this order:

```
1. Infrastructure Generators (existing)
   inv run-generator generate-fabric    # Creates super-spines
   inv run-generator generate-pod       # Creates spines
   inv run-generator generate-rack      # Creates leaves
   └─ Devices created with bgp_asn, node_id allocated from pools

2. AVD Input Builder Generator (NEW)
   inv run-generator generate-avd-inputs --fabric=Fabric-A
   └─ Populates device.avd_inputs for all devices in fabric

3. AVD Structured Config Generator (NEW)
   inv run-generator generate-avd-structured-config --fabric=Fabric-A
   └─ Populates device.avd_structured_config for all devices
   └─ Calls pyavd.get_avd_facts() and pyavd.get_device_structured_config()

4. Artifact Generation (automatic or manual)
   └─ avd_eos_configuration artifact reads device.avd_structured_config
   └─ avd_fabric_documentation artifact reads all device configs
```

**Manual execution example:**
```bash
# After fabric generation, run AVD pipeline
infrahubctl generator generate-avd-inputs Fabric-A
infrahubctl generator generate-avd-structured-config Fabric-A

# View generated artifacts
infrahubctl artifact avd_eos_configuration leaf-pod-A2-1
```

---

## Verification Plan

1. **Schema validation**: `inv load-schema` succeeds
2. **Object loading**: `inv load` creates number pools and fabric AVD attributes
3. **Infrastructure generators**: Run fabric/pod/rack generators, verify bgp_asn and node_id assigned from pools
4. **AVD Input generator**: Run `generate-avd-inputs`, verify device.avd_inputs populated with valid hostvars
5. **pyAVD validation**: `pyavd.validate_inputs(device.avd_inputs)` returns no errors
6. **Structured config generator**: Run `generate-avd-structured-config`, verify device.avd_structured_config populated
7. **EOS config artifact**: Generate artifact, verify valid EOS CLI syntax
8. **Fabric doc artifact**: Generate artifact, verify markdown output
9. **Unit tests**: `pytest tests/unit/test_avd.py`
10. **Integration tests**: `pytest tests/integration/test_avd_transforms.py`

---

## pyAVD API Reference

```python
# Validate inputs against eos_designs schema
pyavd.validate_inputs(hostvars) → ValidationResult

# Build AVD facts from all device inputs
pyavd.get_avd_facts(all_hostvars) → dict[str, EosDesignsFacts]

# Generate structured config for one device
pyavd.get_device_structured_config(hostname, hostvars, avd_facts) → dict

# Validate structured config against eos_cli_config_gen schema
pyavd.validate_structured_config(structured_config) → ValidationResult

# Generate EOS CLI configuration
pyavd.get_device_config(structured_config) → str

# Generate device documentation
pyavd.get_device_doc(structured_config) → str

# Generate fabric documentation
pyavd.get_fabric_documentation(avd_facts, structured_configs, fabric_name) → FabricDocumentation
```

**Important constraints:**
- `get_device_structured_config()`, `get_device_config()`, `get_device_doc()` are NOT thread-safe
- Input data is modified in-place; deep copy if preservation needed
- `hostname` must be set in structured_config

---

## Sources

- [PyAVD Documentation](https://avd.arista.com/5.5/docs/pyavd/pyavd.html)
- [eos_designs Input Variables](https://avd.arista.com/5.1/roles/eos_designs/docs/input-variables.html)
- [DCI & L3 Edge](https://avd.arista.com/3.8/roles/eos_designs/doc/l3-edge.html)
- [Network Services](https://avd.arista.com/3.8/roles/eos_designs/doc/network-services.html)
