---
title: Generators
description: The infrastructure generators that create devices, interfaces, cabling, and AVD inputs.
audience: developer
sidebar_position: 3
---

# Generators

:::info Developer Guide
This page is part of the developer guide. It explains how the generators are structured. To *run* generators as an operator, switch to [Quick Start](/quick-start).
:::

This document describes the infrastructure generators in this solution.

## Overview

Generators create infrastructure objects based on templates and target objects. They run via the Infrahub UI or API and use checksums for idempotent execution.

## Generator Architecture

Each generator consists of:

1. **Generator Class** (`generate_*.py`) - Python class extending `InfrahubGenerator`
2. **Query Class** (`*_query.py`) - Pydantic models for GraphQL response parsing
3. **GraphQL Query** (`*.gql`) - Query to fetch target data

```
┌──────────────────┐     ┌────────────────────┐     ┌─────────────────┐
│  GraphQL Query   │ ──▶ │  Pydantic Parser   │ ──▶ │  Generator      │
│  (*.gql)         │     │  (*_query.py)      │     │  (generate_*.py)│
└──────────────────┘     └────────────────────┘     └─────────────────┘
```

## Generators

### FabricGenerator

**File**: `generators/generate_fabric.py`

**Target**: `NetworkFabric`

**Purpose**: Initialize fabric infrastructure

**Actions**:
1. Allocate IP pools from FabricSupernetPool
   - Loopback prefix pool
   - Interconnect prefix pool
   - Management prefix pool
2. Allocate number pools
   - ASN pool (BGP autonomous systems)
   - Node ID pool (unique device identifiers)
3. Create super-spine devices from template
4. Assign loopback IPs to super-spines

**Query**: `generate_fabric.gql`

```graphql
query FabricGenerator($fabric_id: String!) {
  NetworkFabric(ids: [$fabric_id]) {
    edges {
      node {
        id
        name { value }
        supernet_pool { value }
        # ... pool and template data
      }
    }
  }
}
```

### PodGenerator

**File**: `generators/generate_pod.py`

**Target**: `NetworkPod`

**Purpose**: Create pod infrastructure

**Actions**:
1. Create spine devices from template
2. Link spines to super-spines
3. Allocate loopback IPs from pod pools
4. Set BGP ASN and node IDs

**Query**: `generate_pod.gql`

```graphql
query PodGenerator($pod_id: String!) {
  NetworkPod(ids: [$pod_id]) {
    edges {
      node {
        id
        name { value }
        fabric { node { ... } }
        # ... template and pool data
      }
    }
  }
}
```

### RackGenerator

**File**: `generators/generate_rack.py`

**Target**: `LocationRack`

**Purpose**: Create rack infrastructure

**Actions**:
1. Create leaf devices from template
2. Link leaves to pod spines
3. Allocate loopback IPs
4. Set BGP ASN and node IDs

**Query**: `generate_rack.gql`

```graphql
query RackGenerator($rack_id: String!) {
  LocationRack(ids: [$rack_id]) {
    edges {
      node {
        id
        name { value }
        pod { node { ... } }
        # ... device and link data
      }
    }
  }
}
```

### GenerateAVDDeviceHostvar

**File**: `generators/generate_avd_device_hostvar.py`

**Target**: `NetworkDevice`

**Purpose**: Generate pyAVD hostvars for each device

**Actions**:
1. Extract device attributes (hostname, role, ASN, node ID)
2. Extract IP addresses (loopback, management)
3. Determine uplink topology by device role
4. Extract connected endpoints (servers with VLANs)
5. Build pyAVD-compatible hostvars structure
6. Upload hostvars JSON to object store
7. Create/update AvdArtifact with checksum

**Query**: `avd_device_hostvar.gql`

### AvdDeviceStructuredConfigGenerator

**File**: `generators/generate_avd_device_structured_config.py`

**Target**: `NetworkFabric`

**Purpose**: Generate AVD structured configs for all fabric devices

**Actions**:
1. Traverse fabric hierarchy (pods → devices, racks → devices)
2. Fetch hostvars from object store for each device
3. Validate inputs with `pyavd.validate_inputs()`
4. Generate AVD facts with `pyavd.get_avd_facts()`
5. Generate structured config per device
6. Upload configs to object store
7. Update AvdArtifact with config identifier

**Query**: `generate_avd.gql`

## Generator Execution Order

Run generators in this order for a new fabric:

```
1. FabricGenerator     (on Fabric)
        ↓
2. PodGenerator        (on each Pod)
        ↓
3. RackGenerator       (on each Rack)
        ↓
4. AVD Hostvars        (on each Device)
        ↓
5. AVD Structured Cfg  (on Fabric)
```

## Running Generators

### Via Infrahub UI

1. Navigate to target object (Fabric, Pod, Rack, or Device)
2. Click **Actions** → **Generator definitions**
3. Select the generator
4. Click **Run**

### Via infrahubctl CLI

```bash
# Run generator on a specific target
infrahubctl generator run generate-fabric --target <fabric-id>
infrahubctl generator run generate-pod --target <pod-id>
infrahubctl generator run generate-rack --target <rack-id>
```

## GeneratorMixin

All generators use `GeneratorMixin` from `src/solution_arista_avd/generator.py`:

```python
class GeneratorMixin:
    def calculate_checksum(self, related_node_ids: list[str]) -> str:
        """
        Calculate deterministic checksum from related node IDs.
        Used to detect when regeneration is needed.
        """
        sorted_ids = sorted(related_node_ids)
        combined = "".join(sorted_ids)
        return hashlib.sha256(combined.encode()).hexdigest()
```

Usage in generator:

```python
class FabricGenerator(GeneratorMixin, InfrahubGenerator):
    async def generate(self, data):
        # Calculate checksum from related nodes
        new_checksum = self.calculate_checksum([
            pod.id for pod in data.pods
        ])

        # Skip if unchanged
        if new_checksum == data.checksum:
            return

        # ... generate infrastructure ...

        # Update checksum
        data.checksum = new_checksum
        await data.save()
```

## Query Classes (Pydantic)

Each generator has a corresponding query class for type-safe parsing. **These `*_query.py` files are generated, not hand-written** — regenerate them whenever the `.gql` query or the schema changes:

```bash
uv run infrahubctl graphql generate-return-types generators/generate_fabric.gql
```

This reads `schema.graphql` at the repo root (refresh with `uv run infrahubctl graphql export-schema --out schema.graphql` when needed) and emits the matching `*_query.py` next to the query file.

Shape of a typical generated class:

```python
# generators/fabric_generator_query.py  (generated)

from pydantic import BaseModel

class FabricNode(BaseModel):
    id: str
    name: ValueWrapper[str]
    supernet_pool: ValueWrapper[str]
    pods: EdgesWrapper[PodNode]

class FabricGeneratorQuery(BaseModel):
    NetworkFabric: EdgesWrapper[FabricNode]
```

## Configuration

Generators are registered in `.infrahub.yml`:

```yaml
generator_definitions:
  - name: generate-fabric
    file_path: "./generators/generate_fabric.py"
    class_name: FabricGenerator
    targets: fabrics
    query: generate_fabric

  - name: generate-pod
    file_path: "./generators/generate_pod.py"
    class_name: PodGenerator
    targets: pods
    query: generate_pod

  - name: generate-rack
    file_path: "./generators/generate_rack.py"
    class_name: RackGenerator
    targets: racks
    query: generate_rack
```

## File Structure

```
generators/
├── generate_fabric.py              # Fabric generator class
├── generate_fabric.gql             # Fabric GraphQL query
├── fabric_generator_query.py       # Fabric Pydantic models
├── generate_pod.py                 # Pod generator class
├── generate_pod.gql                # Pod GraphQL query
├── pod_generator_query.py          # Pod Pydantic models
├── generate_rack.py                # Rack generator class
├── generate_rack.gql               # Rack GraphQL query
├── rack_generator_query.py         # Rack Pydantic models
├── generate_avd_device_hostvar.py  # AVD hostvars generator
├── avd_device_hostvar.gql          # AVD device query
├── generate_avd_device_structured_config.py  # AVD structured config
├── generate_avd.gql                # AVD fabric query
├── generate_avd_inputs_query.py    # AVD fabric Pydantic models
└── generate_avd_device_inputs_query.py  # AVD device Pydantic models
```

## Source

- Generator framework: [`src/solution_arista_avd/generator.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/generator.py) — `GeneratorMixin` with checksum-based change detection.
- Infrastructure generators:
  - [`generators/generate_fabric.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_fabric.py) — `FabricGenerator`.
  - [`generators/generate_pod.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_pod.py) — `PodGenerator`.
  - [`generators/generate_rack.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_rack.py) — `RackGenerator`.
- AVD generators (documented in detail in the [AVD Pipeline sub-section](./avd/overview.md)):
  - [`generators/generate_avd_device_hostvar.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_hostvar.py) — `GenerateAVDDeviceHostvar`.
  - [`generators/generate_avd_device_structured_config.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/generators/generate_avd_device_structured_config.py) — `AvdDeviceStructuredConfigGenerator`.
- Registration: [`.infrahub.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/.infrahub.yml) — `generator_definitions:` block.
- Tests: [`tests/unit/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/tests/unit) and [`tests/integration/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/tests/integration).
