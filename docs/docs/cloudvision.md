---
title: CloudVision Validation
---

# CloudVision Validation

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

`docker-compose.override.yml` passes these variables into the Infrahub task
worker so proposed-change checks can access them.

## Proposed-Change Validation

The `cv-config-validation` check uses the `cv_config_check` GraphQL query to
collect the target fabric and related devices. The fabric must have
`cloudvision_managed` set to `true` before CloudVision validation runs.
Unmanaged fabrics skip CloudVision credential setup, serial-number checks,
inventory checks, and workspace validation.

For a managed fabric, validation first authenticates to CloudVision, then
requires every confirmed device in the fabric to have a serial number and to
exist in CloudVision inventory. Devices outside the target fabric are ignored,
and missing optional relationships are treated as absent membership rather than
runtime failures. Inventory-confirmed devices must also be active in
CloudVision; inactive targeted devices fail validation even if the workspace
build itself succeeds.

After eligibility passes, only devices with generated structured-config
artifacts are deployed to the validation workspace. If no generated
structured-config artifacts exist for an otherwise eligible managed fabric, the
check records an informational skip and does not create or build a workspace.

For each selected device, the check downloads the
`AvdStructuredConfigFile`, renders EOS CLI with `pyavd.get_device_config()`,
deploys the configs to a CloudVision workspace, and requests a workspace build.
Download, JSON decode, or render failures block the proposed change with a
device-specific error. CloudVision connection, deployment, or workspace build
failures also block the proposed change and include the fabric and workspace
context when available.

## Workspace Tracking

Successful validation creates or updates a deterministic CloudVision workspace
for the proposed change and target fabric. If the workspace already exists and
is not pending, the check returns it to a pending state before deploying the
latest configs and requesting a build.

When the tracking schema is loaded, validation also creates or updates a
`CloudvisionWorkspace` object in Infrahub. The object tracks:

- `workspace_id`: deterministic CloudVision workspace ID
- `proposed_change_id`: proposed change that created the workspace
- `status`: `pending`, `built`, `submitted`, or `abandoned`
- `fabric`: fabric validated by the workspace

The workspace ID is deterministic from proposed-change ID and fabric name, so a
validation rerun updates the same CloudVision workspace instead of creating a
new one. Separate proposed changes against the same fabric receive different
workspace IDs.

The CloudVision workspace display name uses the proposed-change name and fabric
name. Its description uses the proposed-change description, with a generic
Infrahub validation description when the proposed change has no description.
When the check context does not include full proposed-change metadata, the check
looks up the open proposed change by source branch and also tries the short
branch name for `feat/` branches.

If the `CloudvisionWorkspace` schema is unavailable during rollout, tracking is
skipped without masking CloudVision validation success or failure.

## Operational Notes

CloudVision validation depends on the AVD generator chain having already
produced structured-config artifacts. Missing artifacts do not exempt devices
from managed-fabric serial-number or inventory eligibility; they only remove the
device from workspace config deployment after eligibility succeeds.

CloudVision build or EOS validation failures should be handled as data fixes
first. Add schema or generator code only when a required configuration family
cannot be represented with the existing model.

The check builds workspaces for review only. It does not submit workspaces after
merge, abandon workspaces when a proposed change is deleted, or register
post-merge deployment hooks. Those lifecycle actions belong in a separate
operator-controlled workflow.
