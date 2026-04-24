---
title: Quick Start
description: Install dependencies, bring the stack up, and load seed data.
audience: user
sidebar_position: 1
---

# Quick Start

This page takes you from a fresh clone to a running Infrahub instance with seed data loaded. After this, see [Provision Your First Fabric](./provision-first-fabric.md) to generate devices, configurations, and AVD artifacts.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) — the Python package manager this project uses.
- Python 3.11 or newer.

Everything else is installed by `uv sync` inside the project.

## 1. Install dependencies

From the repository root:

```bash
uv sync --all-packages
```

This creates a virtualenv under `.venv/` and installs the project and its dependencies, including `pyavd` and the Infrahub SDK.

## 2. Build the custom Infrahub image

The project extends the base Infrahub image with `pyavd` and project code. Build the image once:

```bash
export INFRAHUB_BASE_VERSION=1.8.4
uv run invoke build
```

Re-run this only after changes to `Dockerfile` or the Python dependencies.

## 3. Start the stack

```bash
uv run invoke start
```

This brings up, in the background:

| Service | URL | Purpose |
|---------|-----|---------|
| Infrahub UI | `http://localhost:8000` | Main web interface |
| Service Portal | `http://localhost:8501` | Streamlit self-service portal |
| Semaphore | `http://localhost:3000` | Ansible automation runner |
| Neo4j Browser | `http://localhost:7474` | Graph database browser |

Wait for services to become healthy. You can check with:

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml ps
```

All services should show `healthy` or `running`. Infrahub is ready once `http://localhost:8000` responds.

## 4. Load schemas, menus, objects, and repository

Once Infrahub is healthy, load everything in one command:

```bash
uv run invoke load
```

This runs, in order:

1. Initialise Semaphore (idempotent — safe to re-run).
2. Load schemas from `schemas/`.
3. Load the UI menu from `menus/`.
4. Load seed data from `objects/` — manufacturers, device types, IP pools, profiles, device templates, fabrics, racks, VLANs.
5. Register this repository with Infrahub and wait for it to reach `in-sync`.
6. Load event triggers and rules from `triggers.yml`.

## 5. Confirm everything loaded

Open the Infrahub UI at **`http://localhost:8000`** and log in. You should see:

- **Organization → Manufacturer**: Arista, Dell, and other manufacturers.
- **Network → NetworkFabric**: `Fabric-A` and `Fabric-B` with their pods.
- **Location → LocationRack**: pre-defined racks per pod.
- **IPAM → IpamIPPrefix**: the fabric supernet, per-fabric prefix pools, ASN/Node ID pools.

If you don't see these, re-run `uv run invoke load` or see [Common Issues](./troubleshooting.md).

## Next: provision a fabric

The stack is up but no devices exist yet — fabrics, pods, and racks are defined but leaves, spines, and super-spines need to be generated. Follow [Provision Your First Fabric](./provision-first-fabric.md) next.

## Common commands

| Command | What it does |
|---------|--------------|
| `uv run invoke start` | Start all services |
| `uv run invoke stop` | Stop containers, keep volumes |
| `uv run invoke destroy` | Stop and **remove** containers, networks, and volumes (wipes data) |
| `uv run invoke restart` | Restart all services |
| `uv run invoke restart --component=infrahub-server` | Restart a specific service |
| `uv run invoke load` | Re-run the full load sequence |
| `uv run invoke load-schema` | Reload schemas only |
| `uv run invoke load-menu` | Reload UI menus only |
