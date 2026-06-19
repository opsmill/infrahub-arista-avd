# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Infrahub repository solution for AI datacenter infrastructure management. It defines schemas, generators, and transforms for modeling network fabric hierarchies (Fabric → Pod → Rack → Device) with full AVD (Arista Validated Design) integration.

## Directory Structure

```
avd-workshop/
├── src/solution_arista_avd/    # Core Python library (protocols, AVD utils, helpers)
├── generators/            # Infrahub generators (infrastructure creation)
├── transforms/            # Data transforms (computed attributes, artifacts)
├── schemas/               # Infrahub schema definitions (YAML)
├── objects/               # Seed/test data (numbered YAML files)
├── tests/                 # Test suite (unit + integration)
├── menus/                 # UI menu definitions
├── scripts/               # Utility scripts
├── queries/               # GraphQL query templates
├── docs/                  # Documentation
├── .infrahub.yml          # Infrahub configuration (generators, transforms, artifacts)
├── repository.yml         # CoreRepository definition
├── docker-compose.yml     # Full service stack
├── Dockerfile             # Custom image definition
├── pyproject.toml         # Python project config
└── tasks.py               # Invoke task definitions
```

## Commands

### Setup
```bash
uv sync --all-packages     # Install all dependencies
```

### Infrahub Services
```bash
inv start                  # Start Infrahub with docker-compose
inv stop                   # Stop containers
inv destroy                # Stop and remove containers, networks, volumes
inv restart                # Restart all services (or specific: inv restart --component=<name>)
```

### Building
```bash
export INFRAHUB_BASE_VERSION=local
uv run inv build           # Build custom docker image
```

### Loading Data
```bash
inv load                   # Load schema, menus, objects, and repository
inv load-schema            # Load schemas only
inv load-menu              # Load menus only
```

### Testing
```bash
pytest tests                                    # Run all tests
pytest tests/unit                               # Unit tests only
pytest tests/integration                        # Integration tests only
pytest tests/unit/test_computed_attribute.py   # Single test file
```

### Linting
```bash
inv lint                   # Run all linters (yamllint, ruff, mypy)
inv lint-ruff              # Ruff only
inv lint-yaml              # Yamllint only
inv lint-mypy              # Mypy only
inv format                 # Format code with ruff
```

## Architecture

### Data Model Hierarchy

```
NetworkFabric (top-level)
├── NetworkPod (child, GeneratorTarget)
│   ├── LocationRack (peer relationship)
│   │   └── NetworkDevice (leaf switches)
│   └── NetworkDevice (spine switches)
└── NetworkDevice (super-spine switches)

NetworkDevice
├── NetworkInterface (components)
│   ├── NetworkLink (bidirectional connections)
│   └── IpamIPAddress (IP addressing)
└── Relationships: pod, rack, device_type, loopback_ip, mgmt_ip, avd_artifact
```

### Schema Files (`schemas/`)

| File | Purpose |
|------|---------|
| `logical_design.yml` | NetworkFabric, NetworkPod, BuildingBlock generic |
| `device.yml` | NetworkDevice, NetworkInterface, NetworkLink, DeviceType, Manufacturer |
| `physical_location.yml` | LocationHall, LocationRack, Physical generic |
| `ipam.yml` | IpamIPAddress, IpamIPPrefix with role dropdown |
| `generator.yml` | GeneratorTarget generic (checksum tracking) |
| `vlan/vlan.yml` | VLAN configuration schema |
| `compute/compute.yml` | ComputeGenericUnit, compute nodes |
| `avd/avd.yml` | AvdEvpn, AVD-specific configuration |
| `objects/objects.yml` | Generic template object definitions |

### Generator System (`generators/`)

Generators create infrastructure hierarchically:

| Generator | Target | Purpose |
|-----------|--------|---------|
| `FabricGenerator` | Fabric | Creates super-spine switches, allocates IP pools from FabricSupernetPool |
| `PodGenerator` | Pod | Creates spine switches per pod |
| `RackGenerator` | Rack | Creates leaf switches per rack |
| `AvdDeviceHostvarGenerator` | Device | Generates hostvars for pyAVD |
| `AvdDeviceStructuredConfigGenerator` | Fabric | Populates device AVD inputs & structured config |

**Generator Execution Flow:**
1. `FabricGenerator` → creates super-spine devices
2. `PodGenerator` → creates spine devices per pod
3. `RackGenerator` → creates leaf devices per rack
4. `AvdDeviceStructuredConfigGenerator` → populates AVD configs

Each generator extends `InfrahubGenerator` and uses `GeneratorMixin` (from `src/solution_arista_avd/generator.py`). The `calculate_checksum()` method tracks related node changes for idempotent regeneration.

**Generator File Structure:**
- `generate_<entity>.py` - Generator class implementation
- `<entity>_generator_query.py` - Pydantic models matching GraphQL response
- `generate_<entity>.gql` - GraphQL query definition

### Transform System (`transforms/`)

**Python Transforms:**
| Transform | Purpose |
|-----------|---------|
| `ComputedInterfaceDescription` | Generates interface descriptions ("→ device:interface") |
| `CablingPlan` | Generates CSV cabling documentation for fabric |
| `AvdEosConfig` | Converts structured config to EOS CLI configuration |
| `AvdFabricDoc` | Generates markdown fabric documentation |
| `AvdDeviceDoc` | Generates markdown device documentation |

**Transform File Structure:**
- `<transform>.py` - Transform class implementation
- `<transform>_query.py` - Pydantic query models
- `<transform>.gql` - GraphQL query definition

### Core Library (`src/solution_arista_avd/`)

| Module | Purpose |
|--------|---------|
| `protocols.py` | Generated protocol classes for type-safe Infrahub node access (regenerate with `infrahubctl protocols`) |
| `avd.py` | AVD utilities: role mapping (Infrahub ↔ AVD), hostvars builder for pyAVD |
| `cabling.py` | Cabling plan generation from network topology |
| `addressing.py` | IP address management utilities |
| `sorting.py` | Interface sorting algorithms for device configuration |
| `generator.py` | GeneratorMixin class for checksum-based change detection |

### Object Data Files (`objects/`)

Numbered YAML files loaded in order:
1. `01_groups.yml` - Network groups
2. `02_manufacturer.yml` - Device manufacturers (Arista, Dell, etc.)
3. `03_device_type.yml` - Device models
4. `04_ipam.yml` - IP pools (FabricSupernetPool, ASN pools, Node ID pools, Mgmt pools)
5. `05_profiles.yml` - Infrahub profiles
6. `06_device_template.yml` - Device object templates (super-spine, spine, leaf)
7. `07_vlans.yml` - VLAN definitions
8. `10_fabric.yml` - Fabric instances (Fabric-A, Fabric-B with pods)
9. `11_rack.yml` - Rack definitions

## AVD Integration

### Role Mapping
Infrahub device roles map to AVD device types (defined in `src/solution_arista_avd/avd.py`):
- `super_spine` → `super-spine`
- `spine` → `spine`
- `leaf` → `l3leaf`

### Device Roles
- `super_spine`, `spine`, `leaf` - Network device roles

### Interface Roles
- `uplink`, `access`, `spine`, `super_spine`, `leaf`, `loopback`, `server`, `storage`

### Pod Roles
- `fabric` (spine), `cpu`, `storage`

### AVD Workflow
1. Generators create devices with proper roles
2. `AvdDeviceStructuredConfigGenerator` populates `avd_structured_config`
3. Transforms generate EOS configs and documentation from structured config

## IP Pool Management

Hierarchical IP allocation:
- **FabricSupernetPool** - Top-level supernet allocation
- **Per-fabric prefix pools** - Derived from supernet
- **Per-fabric address pools** - Super-spine loopback, pod loopback, device interconnects
- **ASN pools** - Auto-numbering for BGP
- **Node ID pools** - Device identification

## Key Configuration Files

| File | Purpose |
|------|---------|
| `.infrahub.yml` | Defines queries, generators (5), transforms (6), artifact definitions (5) |
| `repository.yml` | CoreRepository definition for Infrahub |
| `pyproject.toml` | Python config: deps (pyavd>=5.0.0, infrahub-sdk==1.18.1), ruff, mypy, pytest |
| `docker-compose.yml` | Service stack: Infrahub, Neo4j, PostgreSQL, Redis, RabbitMQ |
| `docker-compose.override.yml` | Local development overrides |
| `Dockerfile` | Custom image based on Infrahub with project code |
| `tasks.py` | Invoke tasks (start, stop, load, build, test, lint) |
| `.yamllint.yml` | YAML linting rules |
| `.graphqlrc.yml` | GraphQL configuration |

## Tests

### Unit Tests (`tests/unit/`)
- `test_avd.py` - AVD utilities (role mapping, hostvars builder)
- `test_computed_attribute.py` - Computed attribute behavior

### Integration Tests (`tests/integration/`)
- `test_infrahub.py` - Full Infrahub integration
- `test_avd_transforms.py` - AVD transform validation

## Development Patterns

### Checksum-Based Change Detection
Generators use `GeneratorMixin.calculate_checksum()` to track related node IDs. Stored in `GeneratorTarget.checksum` field for idempotent regeneration.

### Pydantic Query Models
All `*_query.py` files define Pydantic models matching GraphQL response structures for type safety and validation.

### Naming Conventions
- Generators: `generate_<entity>.py`
- Query classes: `<entity>_generator_query.py` or `<entity>_query.py`
- GraphQL queries: matching `.gql` files with same base name
- Node namespaces: `Network.*`, `Location.*`, `Organization.*`, `Ipam.*`, `Avd.*`

## Regenerating Protocols

When schema changes, regenerate type-safe protocol classes:
```bash
infrahubctl protocols --out src/solution_arista_avd/protocols.py
```

## Active Technologies
- Python >=3.11, <3.14 + infrahub-sdk==1.18.1, pyavd>=5.0.0 (001-enforce-protocols)
- Neo4j (via Infrahub), PostgreSQL, Redis, RabbitMQ (001-enforce-protocols)
- Markdown (CommonMark + MDX) authored against Docusaurus 3.10 + `@docusaurus/core@^3.10.0`, `@docusaurus/preset-classic@^3.10.0`, `@docusaurus/theme-mermaid@^3.10.0` (already installed; no new deps) (012-enhance-docs)
- Files on disk under `docs/docs/`; sidebar in `docs/sidebars.ts` (012-enhance-docs)
- Python >=3.11, <3.14 (no runtime code changes this cycle — schema YAML + seed YAML + protocol regeneration) + `infrahub-sdk==1.18.1` (`infrahubctl` for schema check / protocols), Infrahub 1.9.x server (015-schema-driven-ip-pools)
- Infrahub (Neo4j graph); IP pools are `CoreIPPrefixPool` / `CoreIPAddressPool` built-ins (015-schema-driven-ip-pools)

## Recent Changes
- 001-enforce-protocols: Added Python >=3.11, <3.14 + infrahub-sdk==1.18.1, pyavd>=5.0.0
