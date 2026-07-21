# Contract: Validation Runtime Behavior

## Inputs

The check receives:

- Target fabric query data from `cv_config_check`.
- CloudVision connection settings from task-worker environment variables.
- Proposed-change metadata from check context or source-branch lookup.
- Structured-config file content from the check branch.

## Required Environment

One of these credential sets is required:

- `CLOUDVISION_SERVERS` and `CLOUDVISION_TOKEN`
- `CLOUDVISION_SERVERS`, `CLOUDVISION_USERNAME`, and `CLOUDVISION_PASSWORD`

Optional settings:

- `CLOUDVISION_VERIFY_CERTS`
- `CLOUDVISION_PROXY_HOST`
- `CLOUDVISION_PROXY_PORT`
- `CLOUDVISION_PROXY_USERNAME`
- `CLOUDVISION_PROXY_PASSWORD`

Blank optional values are treated as unset.

## Validation Outcomes

| Condition | Expected outcome |
| --------- | ---------------- |
| No target fabric found | Informational result; no CloudVision setup and no workspace validation |
| Target fabric has `cloudvision_managed` false or absent | Informational result; no CloudVision setup, serial-number validation, inventory validation, or workspace validation |
| Managed target fabric and missing CloudVision credentials | Failing result with actionable credential message before device eligibility checks |
| Managed target fabric and CloudVision authentication or connection failure | Failing result with CloudVision connection details before device eligibility checks |
| Managed target fabric has no confirmed member devices | Informational result after CloudVision setup; serial-number and inventory eligibility pass with zero devices; no workspace validation |
| Any confirmed managed-fabric device lacks a serial number | Failing result listing every missing serial device before inventory or workspace validation |
| Any serial-numbered managed-fabric device is missing from CloudVision inventory | Failing result listing every missing inventory device before workspace validation |
| Managed-fabric eligibility passes but no devices have structured configs | Informational result; no workspace validation |
| Structured-config file selected for workspace deployment cannot be downloaded, decoded, or rendered | Failing result identifying affected device |
| CloudVision build failure | Failing result with fabric and workspace location |
| Successful workspace build | Passing result with workspace location and deployment counts |

## Workspace Behavior

- Workspace ID is deterministic from proposed-change identity and fabric name.
- Workspace display name includes proposed-change name and fabric name.
- Workspace description uses proposed-change description or a safe fallback.
- Existing non-pending workspaces are returned to pending before deploying configs.
- Successful validation builds the workspace but does not submit it.

## Acceptance Criteria

- Any validation failure uses an error log that blocks merge.
- Non-blocking observations use informational logs.
- No warning path attempts to call a non-existent warning API.
- Runtime failures are reported as check failures or informational skips, not uncaught tracebacks.
- CloudVision credential, authentication, and connection setup is validated before target-device eligibility decisions only for fabrics where `cloudvision_managed` is true.
- Missing CloudVision inventory membership is blocking for every serial-numbered device in a managed fabric.
