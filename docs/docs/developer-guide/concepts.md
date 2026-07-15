---
title: Concepts
description: The core Infrahub terms this reference design relies on, for readers new to the platform.
audience: developer
---

# Concepts

This reference design is built on Infrahub. If you come from an AVD-and-files background, these are the platform terms used throughout the docs. Each links to the upstream [Infrahub documentation](https://docs.infrahub.app) for full detail.

## Branch

A named, isolated line of change over the whole data model — like a Git branch, but for the graph. Every change set in this reference design happens on a branch: the generator chain and the service portal both create and operate on branches, so parallel work does not interfere. See [Infrahub branches](https://docs.infrahub.app/branches/overview).

## Proposed change

A request to merge a branch into `main`, with a full diff of the data and the rendered artifacts it affects. Reviewers see exactly what a change does — new devices, reallocated addresses, changed EOS config — before it reaches production. This is the review gate for every fabric change. See [proposed changes](https://docs.infrahub.app/proposed-changes/overview).

## Generator

A Python routine that reads high-level design intent and creates the many detailed objects it implies — devices, interfaces, links, and address/number allocations. In this reference design, `FabricGenerator`, `PodGenerator`, and `RackGenerator` expand a fabric design into the full technical model, and the AVD generators assemble per-device host_vars and structured configuration. Generators are idempotent (see below). See the [Generators](/developer-guide/generators) reference and [Infrahub generators](https://docs.infrahub.app/generators/overview).

## Transform

A routine that converts stored data into an output document, saved as an artifact. Here, transforms render EOS CLI configuration, fabric and per-device Markdown documentation, the cabling-plan CSV, and the ANTA test catalog — with PyAVD running inside Infrahub's workers. See the [Transforms](/developer-guide/transforms) reference.

## Artifact

A generated, downloadable output stored in the object store and versioned with the data that produced it — a rendered EOS config, a documentation file, a cabling CSV. An artifact regenerates when its underlying data or its transform changes, so it never drifts from the source of truth. The `AvdArtifact` node tracks each device's host_vars and structured config with checksums. See [AvdArtifact & File Storage](/developer-guide/avd/artifacts).

## Resource pool

A managed range — IP prefixes, IP addresses, BGP ASNs, or node IDs — that hands out unique values on demand. Pools in this reference design are **branch-aware**, so two engineers working on different branches never allocate the same prefix, ASN, or node ID. See [Infrahub resource manager](https://docs.infrahub.app/resource-manager/overview).

## Checksum-based idempotency

Each generator records a checksum of the objects it depends on. On re-run, if nothing relevant changed, the generator skips its work; if only part of the design changed, it regenerates only the affected objects. This makes re-running after a partial failure safe, and limits each day-two change to the objects it actually affects. See [Regenerate a Fabric](/how-to/regenerate-fabric).
