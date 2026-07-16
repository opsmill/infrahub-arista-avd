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
│   │   └── DcimDevice (leaf switches)
│   └── DcimDevice (spine switches)
└── DcimDevice (super-spine switches)

DcimDevice
├── NetworkInterface (components)
│   ├── NetworkLink (bidirectional connections)
│   └── IpamIPAddress (IP addressing)
└── Relationships: pod, rack, device_type, loopback_ip, mgmt_ip, avd_artifact
```

### Schema Files (`schemas/`)

Schemas are split into reusable **base** definitions (`base/`) and project
**extensions** at the root that add roles, pools and AVD-specific attributes on
top of them, plus feature-specific subdirectories. Loaded via
`infrahubctl schema load schemas` (see `inv load-schema`).

| File | Purpose |
|------|---------|
| `logical_design.yml` | `Network.Fabric`, `Network.Pod`, `Network.BuildingBlock` generic (interface-sorting methods, super-spine counts) |
| `generator.yml` | `Generator.Target` generic (checksum tracking for idempotent regeneration) |
| `dcim_extensions.yml` | `Network.Link` plus device extensions (role, bgp_asn, node_id, loopback_ip, mgmt_ip, rack/pod relations) |
| `l3ls_extensions.yml` | L3LS fabric attributes on the fabric (routing protocols, MTU, spanning-tree, EVPN overlay) |
| `location_extensions.yml` | `Location.Hall`, `Location.Rack` (rack_type, leaf counts, generation_complete) |
| `ipam_extensions.yml` | IP prefix/address `role` & `status` dropdowns (fabric_supernet, *_loopback, management, backfill) |
| `management.yml` | `Network.DnsServer`, `Network.NtpServer`, `Network.LocalUser` |
| `base/dcim.yml` | `Dcim.GenericDevice`, `Dcim.PhysicalDevice`, interfaces |
| `base/ipam.yml` | `Ipam.IPAddress`, `Ipam.Prefix` base definitions |
| `base/location.yml` | `Location.Generic`, `Location.Hosting` base definitions |
| `base/organization.yml` | `Organization.Generic`, `Organization.Manufacturer`, `Organization.Provider` |
| `avd/avd.yml` | `Avd.Evpn` AVD-specific configuration |
| `evpn/evpn_services.yml` | `Evpn.Tenant`, `Evpn.Svi` EVPN service definitions |
| `lag/lag.yml` | `Interface.Lag`, LAG bundle generic |
| `mlag/mlag.yml` | `Generic.MlagDomain`, `Mlag.Interface` |
| `routing/routing.yml` | `Routing.BGPPeerGroup`, BGP neighbors, prefix lists, route maps, static routes |
| `vlan/vlan.yml` | `Ipam.VLAN` configuration schema |
| `vrf/vrf.yml` | `Ipam.VRF`, `Ipam.RouteTarget` |
| `compute/compute.yml` | `Compute.GenericUnit`, `Compute.PhysicalServer`, virtualization hosts |
| `objects/objects.yml` | `Avd.Artifact`, `Avd.HostvarFile`, `Avd.StructuredConfigFile` |

### Generator System (`generators/`)

Generators create infrastructure hierarchically:

| Generator | Target | Purpose |
|-----------|--------|---------|
| `FabricGenerator` | Fabric | Creates super-spine switches, allocates IP pools from FabricSupernetPool |
| `PodGenerator` | Pod | Creates spine switches per pod (skips the `fabric`-role pod) |
| `RackGenerator` | Rack | Creates leaf + optional l2leaf switches, MLAG pairs, and cabling per rack |
| `ServerCablingGenerator` | Rack | Cables compute/storage servers to leaf switches (`generate_server_cabling.py`) |
| `GenerateAVDDeviceHostvar` | Device | Generates pyAVD hostvars per device |
| `AvdDeviceStructuredConfigGenerator` | Fabric | Populates device AVD inputs & structured config |
| `BackfillStructuredConfigGenerator` | Fabric | Reconciles AVD structured config back into the Infrahub data model (IPAM, MTU, BGP, prefix lists, route maps, static routes) |

**Generator Execution Flow:**
1. `FabricGenerator` → creates super-spine devices
2. `PodGenerator` → creates spine devices per pod
3. `RackGenerator` → creates leaf devices per rack (triggers hostvar generation once all racks are complete)
4. `AvdDeviceStructuredConfigGenerator` → populates AVD configs

Each generator extends `InfrahubGenerator`. The fabric/pod/rack generators also
mix in `GeneratorMixin` (from `src/solution_arista_avd/generator.py`), which
provides `calculate_checksum()` for idempotent regeneration and
`create_avd_device()` — the shared device-creation helper that allocates from
the ASN / node-id / management / loopback pools and activates the loopback.

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
| `AvdEosConfigTransform` | Converts structured config to EOS CLI configuration |
| `AvdFabricDocTransform` | Generates markdown fabric documentation |
| `AvdDeviceDocTransform` | Generates markdown device documentation |
| `AvdAntaCatalogTransform` | Generates a per-device ANTA test catalog (YAML) from structured config; gated by the fabric `anta_enabled` flag (renders a disabled marker when off). Needs fabric-wide structured configs to build `AVDFabricData`. |

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
| `generator.py` | `GeneratorMixin`: checksum-based change detection + `create_avd_device()` shared device-creation helper; plus generator-trigger and readiness helpers |

### Object Data Files (`objects/`)

Numbered YAML files loaded in order (`infrahubctl object load objects/`):
1. `00_user_groups.yml` - User account groups
2. `01_groups.yml` - Network groups
3. `02_manufacturer.yml` - Device manufacturers (Arista, Dell, etc.)
4. `03_device_type.yml` - Device models
5. `04_ipam.yml` - IP pools (FabricSupernetPool, ASN pools, Node ID pools, Mgmt pools)
6. `04a_l3ls_pools.yml` - L3LS-specific resource pools
7. `04b_management.yml` - Management network objects (DNS/NTP/users)
8. `05_profiles.yml` - Infrahub profiles
9. `06_device_template.yml` - Device object templates (super-spine, spine, leaf)
10. `07_vlans.yml` - VLAN definitions
11. `07a_server_profiles.yml` - Server interface/VLAN profiles
12. `08_server_templates.yml` - Server object templates
13. `09_avd_evpn.yml` - AVD EVPN configuration objects
14. `10_fabric.yml` - Fabric instances (Fabric-A, Fabric-B with pods)
15. `11_rack.yml` - Rack definitions
16. `12_evpn_services.yml` - EVPN tenants / SVIs / services

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
| `.infrahub.yml` | Defines queries, generators (7), transforms (5), artifact definitions. Note: schemas load via `inv load`/`infrahubctl schema load schemas`, not the (commented-out) `schemas:` key |
| `repository.yml` | CoreRepository definition for Infrahub |
| `pyproject.toml` | Python config: deps (pyavd>=5.0.0, infrahub-sdk[all]>=1.19.0), ruff, mypy, pytest |
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

## Git worktree caveat

The task-worker container clones `/upstream` via the worktree's `.git` pointer file, which points at a host path outside the mount and fails to resolve inside the container. If you check out this repo as a `git worktree` (rather than a normal `git clone`), bind-mount the parent `.git` directory into the worker by adding to `docker-compose.override.yml` under `task-worker.volumes`: `- /abs/path/to/parent/.git:/abs/path/to/parent/.git:ro`. Standard `git clone` checkouts are unaffected.

## Regenerating Protocols

When schema changes, regenerate type-safe protocol classes:
```bash
infrahubctl protocols --out src/solution_arista_avd/protocols.py
```

## Active Technologies
- Python >=3.11, <3.14 + infrahub-sdk[all]>=1.19.0, pyavd>=5.0.0 (001-enforce-protocols)
- Neo4j (via Infrahub), PostgreSQL, Redis, RabbitMQ (001-enforce-protocols)
- Markdown (CommonMark + MDX) authored against Docusaurus 3.10 + `@docusaurus/core@^3.10.0`, `@docusaurus/preset-classic@^3.10.0`, `@docusaurus/theme-mermaid@^3.10.0` (already installed; no new deps) (012-enhance-docs)
- Files on disk under `docs/docs/`; sidebar in `docs/sidebars.ts` (012-enhance-docs)
- Python >=3.11, <3.14 (no runtime code changes this cycle — schema YAML + seed YAML + protocol regeneration) + `infrahub-sdk==1.18.1` (`infrahubctl` for schema check / protocols), Infrahub 1.9.x server (015-schema-driven-ip-pools)
- Infrahub (Neo4j graph); IP pools are `CoreIPPrefixPool` / `CoreIPAddressPool` built-ins (015-schema-driven-ip-pools)
- Python >=3.11, <3.14 + `pyavd>=5.0.0` (`get_device_test_catalog`, `pyavd.api.anta.AVDFabricData`, `AVDCatalogGenerationSettings`, `pyavd.validate_structured_config`), `infrahub-sdk[all]>=1.19.0` (`InfrahubTransform`) (001-avd-anta-catalog)
- Infrahub (Neo4j graph); structured config already stored as `Avd.StructuredConfigFile` artifacts (001-avd-anta-catalog)
- Python >=3.11, <3.14 (downstream only; this cycle is schema YAML + `infrahubctl protocols` regeneration) + `infrahub-sdk` (`infrahubctl schema check` / `schema load` / `protocols`); `pyavd` unaffected this cycle (002-bgp-asn-schema)
- Infrahub (Neo4j graph). ASN becomes a graph node; pools are `CoreNumberPool` built-ins (002-bgp-asn-schema)

## Recent Changes
- 001-enforce-protocols: Added Python >=3.11, <3.14 + infrahub-sdk==1.18.1, pyavd>=5.0.0
