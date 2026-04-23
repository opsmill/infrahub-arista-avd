---
title: Architecture Overview
description: System architecture and data flow for the Infrahub Arista AVD solution.
audience: developer
sidebar_position: 1
---

# Architecture Overview

:::info Developer Guide
This page is part of the developer guide. It assumes familiarity with Infrahub and Python. If you only want to *use* the system, switch to the [user guide](/user-guide/).
:::

This document describes the system architecture of the AVD Workshop Infrahub solution.

## System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Infrahub Platform                              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Neo4j Graph   │  │   PostgreSQL    │  │   Object Store          │  │
│  │   Database      │  │   (Metadata)    │  │   (Hostvars, Configs)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │   Redis Cache   │  │   RabbitMQ      │  │   Infrahub Server       │  │
│  │                 │  │   (Queue)       │  │   (API + Git Backend)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Repository Solution                               │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │     Schemas     │  │   Generators    │  │   Transforms            │  │
│  │   (YAML DSL)    │  │   (Python)      │  │   (Python + Jinja2)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │  Object Data    │  │     Queries     │  │   Core Library          │  │
│  │   (Seed YAML)   │  │    (GraphQL)    │  │   (src/solution_arista_avd)  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Model Hierarchy

The system models a 3-tier datacenter network fabric:

```
NetworkFabric (e.g., "Fabric-A")
├── NetworkPod (e.g., "Pod-A1", "Pod-A2")
│   ├── LocationRack (e.g., "Rack-A1-01", "Rack-A1-02")
│   │   └── NetworkDevice [leaf] (e.g., "leaf-A1-01-1")
│   │       └── NetworkInterface (e.g., "Ethernet1")
│   │           ├── NetworkLink → remote interface
│   │           └── IpamIPAddress
│   └── NetworkDevice [spine] (e.g., "spine-A1-1")
└── NetworkDevice [super_spine] (e.g., "ss-A-1")
```

## IP Address Management

Hierarchical pool allocation:

```
FabricSupernetPool (e.g., 10.0.0.0/8)
├── CoreIPPrefixPool: Loopback Pool (e.g., 10.255.0.0/16)
│   └── CoreIPAddressPool: Device loopbacks
├── CoreIPPrefixPool: Interconnect Pool (e.g., 10.250.0.0/16)
│   └── CoreIPAddressPool: Point-to-point links
├── CoreIPPrefixPool: Management Pool (e.g., 10.254.0.0/16)
│   └── CoreIPAddressPool: OOB management
├── CoreNumberPool: ASN Pool (65000-65999)
│   └── Per-device BGP ASN allocation
└── CoreNumberPool: Node ID Pool (1-65535)
    └── Per-device unique identifier
```

## Generator Pipeline

Generators run in sequence to build infrastructure:

```
┌─────────────────────────┐
│  1. FabricGenerator     │  Triggered on: NetworkFabric
│  - Allocate IP pools    │  Creates: Super-spine devices
│  - Create super-spines  │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  2. PodGenerator        │  Triggered on: NetworkPod
│  - Create spine devices │  Creates: Spine switches
│  - Link to super-spines │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  3. RackGenerator       │  Triggered on: LocationRack
│  - Create leaf devices  │  Creates: Leaf switches
│  - Link to spines       │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  4. AVD Generators      │  Triggered on: NetworkFabric/Device
│  - Build hostvars       │  Creates: AVD configs
│  - Generate struct cfg  │
└─────────────────────────┘
```

## Transform Pipeline

Transforms convert data to artifacts:

```
┌──────────────────┐     ┌────────────────────┐     ┌─────────────────┐
│  GraphQL Query   │ ──▶ │  Transform Logic   │ ──▶ │  Output Artifact│
│  (Data Fetch)    │     │  (Python/Jinja2)   │     │  (Config/Doc)   │
└──────────────────┘     └────────────────────┘     └─────────────────┘

Examples:
- NetworkInterface → ComputedInterfaceDescription → "→ device:interface"
- NetworkFabric → CablingPlan → CSV cabling matrix
- NetworkDevice → AvdEosConfig → EOS CLI configuration
- NetworkFabric → AvdFabricDoc → Markdown documentation
```

## Checksum-Based Change Detection

Generators use checksums to avoid redundant regeneration:

```python
class GeneratorMixin:
    def calculate_checksum(self, related_node_ids: list[str]) -> str:
        """Create deterministic hash from related node IDs"""
        return hashlib.sha256("".join(sorted(related_node_ids))).hexdigest()

# Usage in generator:
new_checksum = self.calculate_checksum([pod.id, device.id, ...])
if new_checksum != target.checksum:
    # Regenerate
    target.checksum = new_checksum
```

## Configuration Files

| File | Role |
|------|------|
| `.infrahub.yml` | Register queries, generators, transforms, artifacts |
| `repository.yml` | Define repository as CoreRepository in Infrahub |
| `docker-compose.yml` | Orchestrate Infrahub services |
| `pyproject.toml` | Python dependencies and tool configuration |

## Docker Service Stack

```yaml
services:
  infrahub-server:    # Main API server
  infrahub-git:       # Git backend for repository
  infrahub-worker:    # Async task execution
  neo4j:              # Graph database
  postgres:           # Relational metadata
  redis:              # Cache layer
  rabbitmq:           # Message queue
```

## Development Workflow

```
1. Edit schema (schemas/*.yml)
        ↓
2. Load schema: inv load-schema
        ↓
3. Edit generator/transform code
        ↓
4. Test: pytest tests/
        ↓
5. Lint: inv lint
        ↓
6. Reload: inv load
        ↓
7. Run generators via UI
```

## Source

- Infrahub configuration: [`.infrahub.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/.infrahub.yml) — canonical list of queries, generators, transforms, and artifact definitions.
- Schemas: [`schemas/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/schemas) — the data model.
- Generators: [`generators/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/generators) — Python generator classes.
- Transforms: [`transforms/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/transforms) — Python and Jinja2 transforms.
- Core library: [`src/solution_arista_avd/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/src/solution_arista_avd) — shared protocols, AVD utilities, sorting, addressing.
- Service portal: [`service_catalog/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/service_catalog) — Streamlit UI that orchestrates the portal workflows.
