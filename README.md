# Infrahub Arista AVD

An Infrahub repository for datacenter infrastructure management. It models network fabric hierarchies (Fabric > Pod > Rack > Device) with full [Arista Validated Design (AVD)](https://avd.arista.com/) integration, automatic device generation, and configuration rendering.

## Documentation

The documentation site lives under [`docs/`](./docs) and is split into two tracks:

- **[User Guide](https://opsmill.github.io/infrahub-arista-avd/user-guide/)** — for network engineers and operators. Quick start, first-fabric provisioning, service-portal how-tos, artifact viewing, troubleshooting.
- **[Developer Guide](https://opsmill.github.io/infrahub-arista-avd/developer-guide/)** — for contributors. Architecture, schemas, generators, transforms, and a dedicated AVD Integration sub-section covering the two-phase pipeline, hostvars, role mapping, extending the integration, and debugging.

To build and preview locally:

```bash
cd docs
npm install
npm run start     # hot-reloading preview at http://localhost:3000/infrahub-arista-avd/
npm run build     # production build; fails on any broken internal link
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package manager)
- Python 3.11+

## Quick Start

### 1. Install dependencies

```bash
uv sync --all-packages
```

### 2. Build the custom Infrahub image

The project extends the base Infrahub image with project-specific Python dependencies (pyAVD, etc.).

```bash
export INFRAHUB_BASE_VERSION=1.8.4
uv run invoke build
```

### 3. Start all services

This brings up Infrahub, Neo4j, PostgreSQL, Redis, RabbitMQ, the service catalog UI, and Semaphore.

```bash
uv run invoke start
```

Wait for the services to become healthy. You can check status with:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml ps
```

### 4. Load schemas, menus, objects, and repository

Once the Infrahub server is healthy (available at http://localhost:8000), load everything in one command:

```bash
uv run invoke load
```

This will, in order:
1. Initialize Semaphore (automation runner)
2. Load all schema definitions from `schemas/`
3. Load the UI menu from `menus/`
4. Load seed data from `objects/` (manufacturers, device types, IP pools, profiles, templates, fabrics, racks)
5. Register this repository with Infrahub and wait for it to sync
6. Load event triggers and rules from `triggers.yml`

### 5. Run the fabric generator

Open the Infrahub UI at http://localhost:8000 and create a new branch. Then navigate to **Actions > Generator definitions > generate_fabric**, click the run button, and select a target fabric (e.g. `Fabric-A`). The generator must be run on a branch, not on main.

This kicks off the generator chain:
1. **FabricGenerator** creates super-spine devices
2. **PodGenerator** creates spine devices per pod (triggered automatically)
3. **RackGenerator** creates leaf devices per rack (triggered automatically)
4. **AvdDeviceStructuredConfigGenerator** populates AVD structured configs

Once the generators finish, AVD artifacts (EOS configs, fabric docs, device docs) are automatically rendered.

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Infrahub UI | http://localhost:8000 | Main web interface |
| Service Catalog | http://localhost:8501 | Streamlit-based service catalog |
| Semaphore | http://localhost:3000 | Ansible automation runner (admin / semaphore) |
| Neo4j Browser | http://localhost:7474 | Graph database browser |

## Service Portal

The Service Portal is a Streamlit application available at http://localhost:8501 that provides a self-service interface for common datacenter operations. All changes made through the portal are created on a branch and submitted as a proposed change for review.

### Dashboard

The home page shows an overview of your fabrics, EVPN tenants, VRFs, and device counts. Use the branch selector in the sidebar to view resources on different branches.

### Add Network Segment

Creates a new EVPN network segment (VRF + VLAN + SVI) on a target fabric. The workflow:
1. Select a tenant, fabric, and L2 domain
2. Provide a VLAN ID, VRF name, VNI, and gateway IP
3. The portal creates a branch, provisions the objects, runs the AVD generators, and opens a proposed change

### Add Server

Provisions a new physical server into a compute rack. Select a rack and server template, and the portal handles branch creation, server provisioning, cabling generation, and proposed change creation.

### Create Tenant

Creates a new EVPN tenant with a MAC VRF VNI base allocation on one or more fabrics. After creation, network segments can be added to the tenant.

### Fabric Design

An interactive visualization of the fabric topology with four tabs:
- **Design Topology** -- hierarchical view of the fabric (pods, racks, devices)
- **Cabling Topology** -- physical cabling map showing device interconnections
- **Fabric Settings** -- underlay/overlay protocols, MTU, spanning tree config
- **EVPN Tenants** -- tenant VRFs, SVIs, and L2 VLANs

From this page you can also trigger a full fabric generation (devices, cabling, hostvars, structured configs) directly from the UI.

## Available Commands

All commands use [Invoke](https://www.pyinvoke.org/) and should be run from the repository root.

| Command | Description |
|---------|-------------|
| `uv run invoke start` | Start all services in detached mode |
| `uv run invoke stop` | Stop containers and remove networks |
| `uv run invoke destroy` | Stop and remove containers, networks, and volumes |
| `uv run invoke restart` | Restart all services (or `uv run invoke restart --component=<name>` for one) |
| `uv run invoke load` | Load schemas, menus, objects, repository, and triggers |
| `uv run invoke load-schema` | Load schema definitions only |
| `uv run invoke load-menu` | Load UI menus only |
| `uv run invoke build` | Build the custom Docker image |
| `uv run invoke init-semaphore` | Seed Semaphore with project, repo, inventory, and task template |
| `uv run invoke format` | Format Python code with ruff |
| `uv run invoke lint` | Run all linters (yamllint, ruff, mypy) |
| `uv run invoke test` | Run the test suite |

## Running Tests

```bash
pytest tests               # All tests
pytest tests/unit          # Unit tests only
pytest tests/integration   # Integration tests (requires running Infrahub)
```

## Teardown

To stop and remove all containers, networks, and volumes:

```bash
uv run invoke destroy
```
