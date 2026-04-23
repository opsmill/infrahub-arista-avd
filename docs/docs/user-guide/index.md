---
title: User Guide
description: How to consume the Infrahub Arista AVD solution as a network operator.
audience: user
hide_table_of_contents: true
---

# User Guide

This guide is for **network engineers and operators** who want to provision fabrics, manage day-2 operations, and consume the AVD-rendered configurations and documentation. You do not need to read Python, GraphQL, or schema YAML to follow any page in this guide.

## Start here

If this is your first time with the system, follow these pages in order:

1. **[Quick Start](./quick-start.md)** — install dependencies, build the image, start the stack, and load seed data.
2. **[Provision Your First Fabric](./provision-first-fabric.md)** — generate `Fabric-A` end-to-end and reach rendered AVD artifacts.
3. **[Viewing Artifacts](./viewing-artifacts.md)** — find and download the EOS configuration, fabric documentation, and device documentation.

## How-to guides

Once your fabric is up, the day-2 workflows live in the **Streamlit service portal** at `http://localhost:8501`:

- **[Add a Network Segment](./how-to/add-network-segment.md)** — create a VRF + VLAN + SVI on a fabric.
- **[Add a Server](./how-to/add-server.md)** — provision a physical server into a compute rack.
- **[Create a Tenant](./how-to/create-tenant.md)** — create an EVPN tenant for one or more fabrics.
- **[Regenerate a Fabric](./how-to/regenerate-fabric.md)** — re-run the generator chain from the Fabric Design page.

## When something goes wrong

See **[Common Issues](./troubleshooting.md)** for the most frequent failure modes (stack not healthy, generators run out of order, missing seed data, "no structured config available").

## Looking for the developer guide?

If you want to extend the AVD integration, modify generators, or understand how hostvars are built, switch to the [developer guide](/developer-guide/).
