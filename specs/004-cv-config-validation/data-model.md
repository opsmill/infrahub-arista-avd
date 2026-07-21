# Data Model: CloudVision Configuration Validation

## NetworkFabric

**Purpose**: The target fabric selected by the proposed-change check.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.
- `name`: Fabric name used as the targeted check parameter and in CloudVision workspace naming.
- `cloudvision_managed`: Boolean opt-in for CloudVision configuration validation; defaults to `false`.

**Relationships**:

- Parent of pods that contain candidate devices.
- Related from `CloudvisionWorkspace.fabric` for optional workspace tracking.

**Validation rules**:

- The check runs once per fabric target.
- If the target query returns no fabric node, validation records an informational result and exits without contacting CloudVision.
- If `cloudvision_managed` is false or absent, validation records an informational result and exits without requiring CloudVision credentials, device serial numbers, inventory membership, structured configs, or workspaces.
- If `cloudvision_managed` is true, the check authenticates to CloudVision before evaluating device identity or generated configs.

## NetworkPod

**Purpose**: The relationship path connecting devices to their parent fabric.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.

**Relationships**:

- `parent` points to the fabric that scopes a device.

**Validation rules**:

- Devices missing pod or parent fabric relationships are not considered members of the target fabric and must be ignored without failure.

## DcimDevice

**Purpose**: A candidate device whose generated EOS configuration may be validated in CloudVision.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.
- `name`: Hostname and user-facing device identifier.
- `serial`: CloudVision inventory identity.

**Relationships**:

- `pod` connects the device to a fabric through its parent.
- `avd_artifact` connects the device to generated AVD files.

**Validation rules**:

- A device is part of the managed-fabric eligibility set when it belongs to the target fabric, regardless of whether it has generated structured-config artifacts.
- Every device in the managed-fabric eligibility set must have a serial number.
- Every serial-numbered device in the managed-fabric eligibility set must exist in CloudVision inventory before workspace validation starts.
- Devices outside the target fabric are ignored.
- Devices with structured-config artifacts become the workspace validation set only after authentication, serial-number, and inventory eligibility pass for the whole managed fabric.

## AvdArtifact

**Purpose**: Per-device artifact container for generated AVD files.

**Fields used by this feature**:

- `id`: Stable Infrahub object identity.

**Relationships**:

- Parent or container relationship from a device.
- `structured_config_file` points to the generated structured config used for EOS rendering.

**Validation rules**:

- Missing artifact relationships do not remove a device from managed-fabric serial-number or inventory eligibility.
- Devices without an artifact or without a structured-config file are omitted from workspace config deployment after managed-fabric eligibility passes.

## AvdStructuredConfigFile

**Purpose**: Generated structured configuration source for a device.

**Fields used by this feature**:

- `id`: Stable Infrahub file object identity.
- File content: JSON structured config downloaded from the check branch.

**Relationships**:

- Child of a device's `AvdArtifact`.

**Validation rules**:

- File content must be downloadable from the check branch for each device selected for workspace config deployment.
- Missing file nodes mean no config is deployed for that device, but do not bypass serial-number or inventory eligibility.
- If a selected structured-config file cannot be downloaded, decoded, or rendered to EOS CLI, the check blocks the proposed change with a device-specific failure message, not a traceback.

## ProposedChangeContext

**Purpose**: Internal metadata used to derive CloudVision workspace identity and review labels.

**Fields**:

- `id`: Proposed-change identity used for deterministic workspace IDs.
- `name`: Proposed-change display name used in the CloudVision workspace name.
- `description`: Proposed-change description used as the workspace description.

**Relationships**:

- Resolved from check initializer metadata when available.
- May be enriched from `CoreProposedChange` by proposed-change ID or source branch.

**Validation rules**:

- Missing initializer identity must fall back to open proposed-change source branch lookup when possible.
- Missing description must fall back to `Infrahub proposed change validation`.

## CloudvisionWorkspace

**Purpose**: Optional Infrahub tracking object for a CloudVision validation workspace.

**Fields**:

- `name`: Human-readable workspace name.
- `workspace_id`: Deterministic CloudVision workspace ID; unique and human-friendly.
- `proposed_change_id`: Infrahub proposed-change identity associated with the workspace.
- `status`: Workspace tracking status.

**Relationships**:

- `fabric`: The `NetworkFabric` validated by this workspace.

**State transitions**:

```text
pending -> built
pending -> abandoned
built -> pending -> built
built -> abandoned
```

**Validation rules**:

- Tracking is created or updated only when the schema exists.
- Missing tracking schema must not block CloudVision validation.
- `workspace_id` is unique, so reruns update the same tracking object.

## CloudVision Workspace

**Purpose**: External CloudVision workspace used to build and validate device configlets.

**Fields**:

- Workspace ID: Deterministic from proposed-change identity and fabric name.
- Display name: Includes proposed-change name and fabric name.
- Description: Proposed-change description or safe fallback.
- Requested state: Built for validation.

**Relationships**:

- Contains configlets derived from selected devices' generated EOS configs.
- Corresponds to one optional `CloudvisionWorkspace` tracking object.

**State transitions**:

```text
missing -> pending -> built
built -> pending -> built
rolled_back -> pending -> built
```

**Validation rules**:

- Existing non-pending workspaces must be returned to pending before deploying configs.
- Build failure blocks the proposed change.
- Successful build does not submit the workspace.

## Runtime Configuration

**Purpose**: Check runtime values needed to connect to CloudVision.

**Fields**:

- `CLOUDVISION_SERVERS`: One or more CloudVision servers.
- `CLOUDVISION_TOKEN`: Preferred token credential.
- `CLOUDVISION_USERNAME` and `CLOUDVISION_PASSWORD`: Alternate credential pair.
- `CLOUDVISION_VERIFY_CERTS`: Optional certificate verification control.
- `CLOUDVISION_PROXY_*`: Optional proxy configuration.

**Validation rules**:

- Servers plus token, or servers plus username/password, are required.
- Blank optional proxy values are treated as unset.
- Missing required credentials block validation with an actionable error.
