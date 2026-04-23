---
title: Home
description: Infrahub solution for AI datacenter infrastructure management with Arista Validated Design.
slug: /
hide_table_of_contents: true
hide_title: true
---

## Infrahub Arista AVD

This repository is an Infrahub solution for AI datacenter infrastructure management. It defines schemas, generators, and transforms for modeling network fabric hierarchies (Fabric → Pod → Rack → Device) with full AVD (Arista Validated Design) integration.

## Documentation

- [Architecture Overview](./architecture.md) — System architecture and data flow
- [Schemas](./schemas.md) — Data model and schema definitions
- [Generators](./generators.md) — Infrastructure generation system
- [Transforms](./transforms.md) — Data transforms and artifact generation
- [AVD Integration](./avd/README.md) — Arista Validated Design integration

## Getting Started

```bash
uv sync --all-packages     # Install dependencies
inv start                  # Start Infrahub with docker-compose
inv load                   # Load schemas, menus, objects, and repository
```

Generators are then run from the Infrahub UI. See the repository [`README.md`](https://github.com/opsmill/infrahub-arista-avd/blob/main/README.md) for the full command reference.
