# Contract: Regenerate Fabric Reconciliation

This contract documents the operator-visible behavior of running `generate-fabric` for an existing fabric.

## Entry Points

- Infrahub UI: run generator definition `generate-fabric` for a selected `NetworkFabric`.
- Service portal: Fabric Design page, **Generate Fabric**, which creates a branch and runs `generate-fabric` for the selected fabric.
- GraphQL/API: `CoreGeneratorDefinitionRun(data: { id: <generate-fabric-id>, nodes: [<fabric-id>] })`.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| Fabric target node ID | Yes | The `NetworkFabric` to reconcile. |
| Branch | Yes | Non-main branch where trigger rules are active for the cascade. |
| Override mode | No | Not supported by the current external contract in this slice. Standard runs always use preservation mode. |

## Standard Preservation Mode

Running `generate-fabric` MUST:

1. Mark the target fabric's hostvars as not ready.
2. Reconcile fabric-owned generated objects and pools.
3. Continue through pod generation for every expected non-fabric pod under the target fabric, including pods whose checksum was already current.
4. Continue through rack generation for every expected rack under those pods, including racks whose checksum was already current.
5. Populate missing generated device values required for AVD.
6. Preserve non-empty operator-provided device values by default, including `serial` and `mgmt_ip`.
7. Populate missing generated uplinks, `NetworkLink` nodes, interface connector relationships, generated interface attributes, and point-to-point IP relationships when the source fabric intent exists.
8. Preserve non-empty existing connector, interface, and IP values that conflict with generated intent.
9. Report populated, preserved, and skipped connectivity decisions through generator logs or another completed-run artifact visible during validation.
10. Trigger hostvar generation after all racks for the fabric are complete.
11. Allow the existing `avd_hostvars_ready` trigger to run structured config generation.

## Completion Signals

A standard run is complete when:

- Expected pod, rack, and device objects exist for the target fabric.
- No expected device remains partial solely because it had pre-existing non-empty values.
- Missing generated uplink connectivity has been populated where source intent was complete.
- Non-empty conflicting connector, interface, or IP values remain unchanged and are visible as skipped conflicts.
- Every expected fabric device has an `AvdArtifact.hostvar_file`.
- Every expected fabric device has an `AvdArtifact.structured_config_file`.
- Re-running the same fabric does not create duplicate objects, links, IP addresses, or relationships.

## Non-Goals for This Contract

- No schema-backed override flag is added.
- No branch-name convention, environment variable, or hidden runtime switch may enable overwrite behavior.
- No external API parameter is documented for override mode because the current local `GeneratorDefinitionRequestRunInput` accepts only generator definition ID and target node IDs.

## Future Override Contract Requirements

If override mode is added later, it MUST be explicit and operator-visible before generation starts. Acceptable future designs include:

- Separate override generator definitions with clear names.
- A service-portal workflow that stores and displays the selected mode.
- A schema-backed run setting with lifecycle rules that prevent stale override state.

Any future override MUST only replace generator-owned fields and MUST continue to preserve unrelated operator-owned data.
