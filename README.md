# Arista AVD Reference Design

![CI](https://github.com/opsmill/infrahub-arista-avd/actions/workflows/ci.yml/badge.svg)

The Arista AVD Reference Design models a full Arista datacenter fabric in Infrahub — topology, addressing pools, EVPN configuration, and per-device intent as structured, queryable data. The whole team can browse, filter, and query the fabric through the web UI, GraphQL API, or MCP interface; every change runs through Infrahub branches and proposed changes, with a complete audit trail before it reaches a device.

Designed for network automation teams running AVD with static variable files who need a shared source of truth, API access, and branch-based change control — and for teams evaluating how to operate AVD at scale without building the inventory-to-PyAVD translation layer themselves.

## What It's For

- **Generate a complete fabric from a design** — define topology parameters and addressing pools; generators create all super-spines, spines, and leaves, allocate loopback, interconnect, and management addresses, BGP ASNs, and node IDs, and cable devices together automatically.
- **Render EOS device configurations and documentation** — PyAVD runs inside Infrahub workers and produces EOS CLI configurations, per-device and fabric-level Markdown documentation, and a cabling plan CSV as downloadable artifacts.
- **Make day-two changes without rebuilding** — edit the design and regenerate; checksum-based idempotency applies changes only to affected objects; branch-aware pools prevent collisions across parallel work.
- **Give other teams access to network data** — the fabric is queryable through the Infrahub Web UI, GraphQL API, and MCP interface; the Streamlit service portal provides guided workflows for stakeholders without API or CLI access.
- **Track and review every change** — all changes run through Infrahub branches and proposed changes, with a full diff before any change reaches a device.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Python 3.11+
- pyAVD ≥ 6.2.0 (bundled in the custom Docker image — no separate install required)

## Quick Start

```bash
# Install Python dependencies, including pyAVD and the Infrahub SDK
uv sync --all-packages

# Build the custom Infrahub image (extends the base image with pyAVD — run once)
export INFRAHUB_BASE_VERSION=1.10.1
uv run invoke build

# Start all services: Infrahub, Neo4j, PostgreSQL, Redis, RabbitMQ, service portal, Semaphore
uv run invoke start

# Load schemas, UI menu, seed data, register the repository, and load event triggers
uv run invoke load
```

Open the Infrahub UI at `http://localhost:8000` and the service portal at `http://localhost:8501`.

Then follow [Provision Your First Fabric](#) to run the generator chain and reach rendered EOS artifacts.

## What You'll See

After `invoke load` completes and you run the generator chain on a fabric:

1. **Seed data appears in the UI** — manufacturers, device types, addressing pools, device templates, two example fabrics (Fabric-A, Fabric-B) with pods and racks, and seed VLANs are loaded.
2. **FabricGenerator runs** — super-spine devices appear on the branch, with loopback and management addresses allocated from pools.
3. **PodGenerator and RackGenerator trigger automatically** — spine and leaf devices appear, cabled to their uplinks, with interconnect addresses, BGP ASNs, and node IDs assigned.
4. **AVD generators run** — each device's PyAVD host_vars and structured configuration are stored as `AvdArtifact` graph objects.
5. **Transforms produce artifacts** — EOS device configuration, per-device Markdown documentation, fabric documentation, and a cabling plan CSV are available as downloadable artifacts on each device and fabric object.
6. **Propose and review** — open a proposed change from the branch; the UI shows a diff of every new object and the rendered artifacts for review before any configuration reaches production.

## What's Included

- **Schemas** — 20 schema files covering the full fabric data model:
  - Topology: NetworkFabric, NetworkPod, NetworkDevice, NetworkInterface, NetworkLink
  - IPAM: prefixes and addresses with role tagging (loopback, interconnect, management, server)
  - EVPN: tenants, VRFs, SVIs, L2 VLANs
  - MLAG: domain and peer pool definitions
  - AVD types: `AvdArtifact` for per-device hostvar and structured config tracking with checksums
- **Generators** — six checksum-based, idempotent generators:
  - FabricGenerator, PodGenerator, RackGenerator — device creation, addressing, and cabling
  - GenerateAVDDeviceHostvar — assembles per-device PyAVD input from the source of truth
  - AvdDeviceStructuredConfigGenerator — runs PyAVD to produce structured configuration
  - GenerateServerCabling — handles server attachment
- **Transforms** — render structured data into downloadable artifacts:
  - EOS device configuration (via PyAVD, running inside Infrahub workers)
  - Per-device and fabric-level Markdown documentation
  - Cabling plan CSV
  - ANTA test catalogs — generation ships; test execution is on the roadmap
  - Computed interface descriptions
- **Seed data** — manufacturers, device types, addressing and number pools (loopback, interconnect, management, ASN, node ID), device profiles and templates, two example fabrics with pods and racks, and seed VLANs.
- **Service portal** — Streamlit application with guided day-2 workflows:
  - Add network segment (VRF, VLAN, SVI)
  - Provision server into a rack
  - Create EVPN tenant
  - Fabric Design visualization (topology, cabling, settings, EVPN)
- **Stack** — Docker Compose extending Infrahub 1.10.1 with pyAVD. Includes Infrahub UI, service portal, Semaphore (bundled Ansible runner for deployment), and Neo4j.

| File | What it does |
|------|-------------|
| `.infrahub.yml` | Registers all generators, transforms, queries, and artifact definitions with Infrahub |
| `schemas/` | YAML schema definitions for the full data model |
| `generators/` | Python generators (fabric, pod, rack, AVD hostvars, structured config, server cabling) |
| `transforms/` | Python and Jinja2 transforms (EOS config, docs, cabling plan, ANTA catalog, interface descriptions) |
| `objects/` | Seed YAML (manufacturers, device types, pools, profiles, templates, fabrics, racks, VLANs) |
| `triggers.yml` | Event trigger rules wiring schema changes to generator runs |
| `service_catalog/` | Streamlit service portal |
| `docker-compose.yml` | Stack definition; docker-compose.override.yml adds the portal and Semaphore |
| `Dockerfile` | Custom Infrahub image with pyAVD |
| `tasks.py` | Invoke task definitions (build, start, stop, load, lint, test) |

> **Note:** Brownfield import (modeling an existing fabric and importing configurations via Infrahub Sync) is available in a guided engagement today — it is not yet a self-serve path.

## Documentation

| | |
|--|--|
| **Provision a fabric end-to-end** | [Provision Your First Fabric](#) — step-by-step walkthrough from seed data to rendered EOS artifacts |
| **Use the service portal** | [Get Started](#) — day-two workflows, how-to guides, troubleshooting |
| **Understand the generator pipeline** | [Architecture Overview](#) — system components, data model, and generator chain |
| **Understand the AVD pipeline** | [AVD Pipeline Overview](#) — two-phase pipeline, hostvars reference, role mapping |
| **Extend the integration** | [Extending the Integration](#) — new device roles, transform outputs, schema fields |
| **Debug pipeline issues** | [Debugging the Pipeline](#) — intermediate-file inspection, single-generator re-runs, common failure modes |

## About Infrahub

[Infrahub](https://github.com/opsmill/infrahub) is an open source infrastructure data management and automation platform (Apache 2.0), developed by [OpsMill](https://opsmill.com). It gives infrastructure and network teams a unified, schema-driven source of truth for all infrastructure data — devices, topology, IP space, configuration — with built-in version control, a generator framework for automation, and native integrations with Git, Ansible, Terraform, and CI/CD pipelines.
