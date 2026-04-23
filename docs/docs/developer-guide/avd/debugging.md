---
title: Debugging the Pipeline
description: Inspect intermediate files, force regeneration, and isolate a single generator or transform.
audience: developer
sidebar_position: 7
---

# Debugging the Pipeline

:::info Developer Guide
This page is part of the developer guide. For operator-facing issues (stack health, generator order, "no structured config available") switch to the [user guide troubleshooting page](/user-guide/troubleshooting).
:::

## Inspecting hostvars and structured configs

Both files live on the `AvdArtifact` for each device (see [AvdArtifact & File Storage](./artifacts.md)). To read them:

### Via the Infrahub UI

1. Navigate to the device's `AvdArtifact` (e.g. search for the artifact named after the device).
2. Open the `hostvar_file` or `structured_config_file` relationship — the child node is an `AvdHostvarFile` / `AvdStructuredConfigFile`.
3. Download or view the `content` attribute (JSON).

### Via the SDK

```python
from infrahub_sdk import InfrahubClient

client = InfrahubClient(address="http://localhost:8000")
await client.login()

artifact = await client.get(
    kind="AvdArtifact",
    device__name__value="leaf-pod-A1-1",
    branch="main",
    prefetch_relationships=True,
    include=["hostvar_file", "structured_config_file"],
)

hostvars_node = artifact.hostvar_file.peer
hostvars = hostvars_node.content.value   # raw JSON string
```

## Checksum-based change detection

Both generators skip writes when content is unchanged. The flow is:

1. Serialise the new content (hostvars dict or structured config dict) to JSON.
2. Compute `hashlib.sha256(json_bytes).hexdigest()`.
3. Compare against the existing file's `checksum` attribute (provided by `CoreFileObject`).
4. If equal → skip the write (log "unchanged, skipped").
5. If different → replace the file.

### Forcing a regeneration

If you need to force a fresh write (e.g. you suspect the checksum is stale or want to test the generator path end-to-end), delete the child file node:

```python
hostvars_node = artifact.hostvar_file.peer
await hostvars_node.delete()
```

The next generator run will write a new `AvdHostvarFile` unconditionally.

## Re-running a single generator

### From the UI

1. On a branch, open **Actions → Generator definitions**.
2. Pick the generator (e.g. `generate-avd-device-hostvar`).
3. Click **Run** and select the target device (or fabric for Phase 2).

### Via the SDK

Generators can be triggered programmatically:

```python
await client.execute_graphql(
    query="""
    mutation RunGenerator($group: String!, $generator: String!) {
        CoreGeneratorDefinitionRun(
            data: { generator: $generator, group: $group }
        ) { ok }
    }
    """,
    variables={"generator": "generate-avd-device-hostvar", "group": "avd_devices"},
    branch_name="my-branch",
)
```

See the service portal implementation in [`service_catalog/utils/api.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/service_catalog/utils/api.py) (`run_avd_pipeline()` and related helpers) for a working example.

## Missing structured config

**Symptoms**: `avd_eos_config` transform returns "No structured config available".

**Diagnostic flow**:

1. Fetch the device's `AvdArtifact`. Is there one? If not — the device isn't in the `avd_devices` group.
2. Does `AvdArtifact.hostvar_file` exist? If not — Phase 1 didn't run for this device. Run `generate-avd-device-hostvar` for it.
3. Does `AvdArtifact.structured_config_file` exist? If not — Phase 2 didn't run (or failed) for this device's fabric. Run `generate-avd-device-structured-config` for the fabric.
4. If `structured_config_file` exists but `content` is empty or malformed — the previous Phase 2 run had a partial failure. Delete the file and re-run Phase 2.

## pyAVD validation errors

`pyavd.validate_inputs()` is called in Phase 2 across **all** devices in the fabric. If one device has invalid hostvars, the whole Phase 2 run fails.

**Reading the error**:

```text
pyavd.j2lint.utils.ValidationError: Invalid type for ... in ...
```

The error usually names a field and a device. Fetch that device's hostvars (above) and look for:

- Missing required fields for the role (`id`, `bgp_as`, `loopback_ipv4_address` for L3 roles).
- Mismatched list lengths in the uplink block (`uplink_interfaces` vs `uplink_switches`).
- Type mismatches — pyAVD expects stringified ASNs (`"65101"`), CIDR-less loopbacks, etc.

Cross-reference [Hostvars Reference](./hostvars.md) for the expected types.

## Common failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Phase 2 fails "Missing hostvar_file for device X" | Phase 1 didn't complete for device X | Re-run Phase 1 for that device |
| `get_avd_type` raises `ValueError` | New role added to schema without adding to `ROLE_TO_AVD_TYPE` | Update [`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py) |
| Fabric documentation empty or partial | One or more devices missing hostvars | Complete Phase 1 for all devices |
| Artifact regenerates every run even when nothing changed | Hostvars dict has a non-deterministic field (e.g. iteration order of a set) | Sort lists/dicts before JSON-serialising |
| Transform returns stale output | `CoreFileObject.content` cached somewhere; rare | Force-regenerate the artifact from the UI preview panel |

## Turning up log verbosity

The generators log via the Infrahub SDK's logging. To see more detail on a dev stack, bump the log level in the Infrahub server's environment:

```bash
# in docker-compose.override.yml for the infrahub service
environment:
  INFRAHUB_LOG_LEVEL: DEBUG
```

Then restart:

```bash
uv run invoke restart --component=infrahub-server
```

## Related reading

- [Overview](./overview.md) — the pipeline shape at a glance.
- [AvdArtifact & File Storage](./artifacts.md) — exactly which node holds which piece of data.
- [User guide troubleshooting](/user-guide/troubleshooting) — operator-level issues and fixes.
