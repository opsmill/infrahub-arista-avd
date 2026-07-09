---
title: CloudVision Integration
---

# CloudVision Integration

The repository validates generated EOS configurations in CloudVision during
Infrahub proposed-change validation. Post-merge workspace submission is out of
scope for this workflow and should be implemented separately with Semaphore.

## Runtime Configuration

CloudVision credentials are read from task-worker environment variables:

```bash
CLOUDVISION_SERVERS=cv.example.com
CLOUDVISION_TOKEN=...
CLOUDVISION_VERIFY_CERTS=true
```

Username/password authentication is also supported with
`CLOUDVISION_USERNAME` and `CLOUDVISION_PASSWORD`. Optional proxy settings use
the `CLOUDVISION_PROXY_*` variables.

`docker-compose.override.yml` passes these variables into the custom Infrahub
runtime so proposed-change checks can access them.

## Proposed-Change Validation

The `cv-config-validation` check uses the `cv_config_check` GraphQL query to
collect devices for the target fabric. Devices are considered CloudVision
managed when they have:

- an AVD structured-config artifact
- a serial number

If a fabric has no serial-numbered devices with structured configs, the check
skips CloudVision validation for that fabric. If some intended CloudVision
devices have structured configs but are missing serial numbers, the check fails
with a clear error listing those devices.

For each selected device, the check downloads the
`AvdStructuredConfigFile`, renders EOS CLI with `pyavd.get_device_config()`,
deploys the configs to a CloudVision workspace, and requests a workspace build.

## Workspace Tracking

Successful validation creates or updates a `CloudvisionWorkspace` object in
Infrahub. The object tracks:

- `workspace_id`: deterministic CloudVision workspace ID
- `proposed_change_id`: proposed change that created the workspace
- `status`: `pending`, `built`, `submitted`, or `abandoned`
- `fabric`: fabric validated by the workspace

The workspace ID is deterministic from proposed-change ID and fabric name, so a
validation rerun updates the same CloudVision workspace instead of creating a
new one.

The CloudVision workspace display name uses the proposed-change name and fabric
name. Its description uses the proposed-change description, with a generic
Infrahub validation description when the proposed change has no description.

## Operational Notes

CloudVision validation depends on the AVD generator chain having already
produced structured-config artifacts. Missing artifacts make the check skip the
device rather than submit an incomplete config.

CloudVision build or EOS validation failures should be handled as data fixes
first. Add schema or generator code only when a required configuration family
cannot be represented with the existing model.
