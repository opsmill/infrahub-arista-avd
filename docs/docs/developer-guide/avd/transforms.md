---
title: AVD Transforms
description: The three Python transforms that render EOS configs and AVD documentation from stored data.
audience: developer
sidebar_position: 3
---

# AVD Transforms

:::info Developer Guide
This page is part of the developer guide. It documents the transform implementations. To *view* artifacts as an operator, switch to [Viewing Artifacts](/viewing-artifacts).
:::

Three Python transforms turn the data produced by the [two-phase pipeline](./overview.md) into user-facing artifacts. All three are registered in [`.infrahub.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/.infrahub.yml).

:::note Generated Pydantic models
The `*_query.py` files referenced below are **generated** from their matching `.gql` and the checked-in `schema.graphql` via `infrahubctl graphql generate-return-types`. Do not hand-edit them. See [Transforms → Query Classes](../transforms.md#query-classes) for the regeneration command.
:::

| Transform | Target group | Content type | Wraps |
|-----------|-------------|--------------|-------|
| `avd_eos_config` | `avd_devices` | `text/plain` | `pyavd.get_device_config()` |
| `avd_device_doc` | `avd_devices` | `text/markdown` | PyAVD device documentation |
| `avd_fabric_doc` | `fabrics` | `text/markdown` | `pyavd.get_fabric_documentation()` |

## `avd_eos_config`

**Class**: `AvdEosConfigTransform`
**Source**: [`transforms/avd_eos_config.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/transforms/avd_eos_config.py)
**Query**: [`transforms/avd_device_config.gql`](https://github.com/opsmill/infrahub-arista-avd/blob/main/transforms/avd_device_config.gql)
**Pydantic model**: `transforms/avd_device_config_query.py`

Renders a single device's Arista EOS CLI configuration.

Flow:

1. Query resolves the target device and navigates to `AvdArtifact.structured_config_file`.
2. Transform fetches the structured-config JSON from the `AvdStructuredConfigFile` (a `CoreFileObject`).
3. Calls `pyavd.get_device_config(structured_config)`.
4. Returns the EOS CLI text.

If `structured_config_file` is missing or empty, the transform returns a user-readable "No structured config available" message rather than crashing — see [Debugging the Pipeline](./debugging.md#missing-structured-config) for the diagnostic flow.

## `avd_device_doc`

**Class**: `AvdDeviceDocTransform`
**Source**: [`transforms/avd_device_doc.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/transforms/avd_device_doc.py)
**Query**: `transforms/avd_device_config.gql` (reused)
**Pydantic model**: `transforms/avd_device_config_query.py`

Renders per-device markdown documentation.

Flow:

1. Same query as `avd_eos_config` — resolves device and its structured config.
2. Calls the PyAVD device documentation function on the structured config.
3. Returns markdown.

## `avd_fabric_doc`

**Class**: `AvdFabricDocTransform`
**Source**: [`transforms/avd_fabric_doc.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/transforms/avd_fabric_doc.py)
**Query**: [`transforms/avd_fabric_devices.gql`](https://github.com/opsmill/infrahub-arista-avd/blob/main/transforms/avd_fabric_devices.gql)
**Pydantic model**: `transforms/avd_fabric_devices_query.py`

Renders fabric-wide markdown documentation covering the full topology.

Flow:

1. Query resolves the fabric and walks to every device in its pods and racks.
2. Transform fetches **hostvars** and **structured config** files for all devices.
3. Calls `pyavd.get_avd_facts(all_hostvars)` to build the shared facts.
4. Calls `pyavd.get_fabric_documentation(avd_facts, structured_configs, fabric_name)`.
5. Returns markdown.

Fabric documentation requires hostvars to be present for *every* device in the fabric. If any device has no hostvars, the transform fails the artifact generation with a message naming the missing device(s).

## Registration in `.infrahub.yml`

```yaml
python_transforms:
  - name: avd_eos_config
    class_name: AvdEosConfigTransform
    file_path: "./transforms/avd_eos_config.py"
  - name: avd_fabric_doc
    class_name: AvdFabricDocTransform
    file_path: "./transforms/avd_fabric_doc.py"
  - name: avd_device_doc
    class_name: AvdDeviceDocTransform
    file_path: "./transforms/avd_device_doc.py"

artifact_definitions:
  - name: avd_eos_configuration
    targets: avd_devices
    transformation: avd_eos_config
  - name: avd_fabric_documentation
    targets: fabrics
    transformation: avd_fabric_doc
  - name: avd_device_documentation
    targets: avd_devices
    transformation: avd_device_doc
```

## Jinja2 transforms

Separate from the AVD transforms above, the project also ships a Jinja2 startup-config transform for OSPF (see [Transforms](../transforms.md#jinja2-transform)). That transform is independent of the AVD pipeline.

## Adding a new transform

See [Extending the Pipeline → Adding a new transform output](./extending.md#add-a-new-transform-output).
