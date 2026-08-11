---
title: Checks
description: Python checks that run in the proposed-change pipeline — the CloudVision configuration validation check and its workspace lifecycle.
audience: developer
sidebar_position: 5
---

# Checks

:::info Developer Guide
Documents the check implementations. For the operator view of CloudVision validation — credentials, workspace tracking, and submission — see [CloudVision Validation](/cloudvision).
:::

## Overview

A check is a Python routine that Infrahub runs during proposed-change validation. Unlike a
transform, it produces no artifact: it reports success, informational messages, or errors, and an
error blocks the proposed change.

Checks live in `checks/` and are registered under `check_definitions:` in `.infrahub.yml`:

```yaml
check_definitions:
  - name: cv-config-validation
    file_path: "./checks/cv_config_check.py"
    class_name: CVConfigValidationCheck
    targets: fabrics
    parameters:
      name: name__value
```

`targets` is a group, exactly as for generators and artifact definitions — `cv-config-validation`
runs once per member of the `fabrics` group, with the fabric name passed as the `name` parameter.

## `cv-config-validation`

**Class**: `CVConfigValidationCheck`
**Source**: [`checks/cv_config_check.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/checks/cv_config_check.py)
**Query**: [`checks/cv_config_check.gql`](https://github.com/opsmill/infrahub-arista-avd/blob/main/checks/cv_config_check.gql) (registered as `cv_config_check`)
**Target**: `NetworkFabric` (group `fabrics`)
**Timeout**: 600 seconds

The check deploys each device's rendered EOS configuration into a CloudVision workspace and asks
CloudVision to build it, so a reviewer sees CloudVision's own verdict on the configuration before
the branch merges.

```python
class CVConfigValidationCheck(InfrahubCheck):
    query = "cv_config_check"
    timeout = 600

    async def validate(self, data: dict[str, Any]) -> None:
        parsed = CVConfigCheckQuery(**_normalize_optional_relationships(data))
        ...
```

The flow, in order:

1. Resolve the target fabric from the query response. A fabric with `cloudvision_managed = false`
   skips everything that follows.
2. Read CloudVision credentials from the task-worker environment (`get_cloudvision_config()`),
   and authenticate.
3. Require every confirmed device in the fabric to have a serial number and to exist — and be
   active — in CloudVision inventory.
4. Select the devices that have a stored `AvdStructuredConfigFile`, download each one, and render
   EOS CLI with `pyavd.get_device_config()`.
5. Deploy the configs to a deterministic workspace for this proposed change and fabric, and request
   a build.
6. Record the workspace as a `CloudvisionWorkspace` object and post its URL to a proposed-change
   thread.

Download, JSON-decode, render, connection, deployment, and build failures are all reported as
errors and block the proposed change. The behavioural detail — eligibility rules, workspace naming
and reuse, thread comments, and what happens when the tracking schema is absent — is documented on
the [CloudVision Validation](/cloudvision) page rather than duplicated here.

### Optional relationships and the generated query model

`_normalize_optional_relationships()` runs before the generated Pydantic model parses the response.
GraphQL omits nullable relationship selections entirely rather than returning `null`, so a device
with no pod or no `avd_artifact` arrives with the key missing. The helper fills those keys with
`{"node": None}` so an absent relationship parses as absent membership instead of failing
validation.

### Supporting modules

| Module | Holds |
|--------|-------|
| [`checks/cv_helpers.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/checks/cv_helpers.py) | Credential loading from the environment, deterministic workspace ID/name/description/URL derivation, proposed-change context lookup, workspace rollback |
| [`checks/cv_workspace_lifecycle.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/checks/cv_workspace_lifecycle.py) | Workspace threads and comments, and the two submission entry points below |

The two submission entry points in `cv_workspace_lifecycle.py`:

- `submit_linked_workspace_for_custom_webhook()` — the CustomWebhook entry point. It extracts the
  proposed-change ID and branch from the event, ignores events that name a check other than
  `cv-config-validation`, and delegates to the shared handler.
- `submit_linked_workspace_for_proposed_change()` — the shared handler. It resolves
  `CloudvisionWorkspace` objects by proposed-change ID and submits only when exactly one linked
  workspace exists in a submit-ready state (`built` or `submit_failed`).

The manual retry path for the same handler is an invoke task:

```bash
uv run invoke submit-cv-workspace --proposed-change-id <proposed-change-id> --branch main
```

### The webhook payload transform

`cv_workspace_submission_webhook_payload` (`CVWorkspaceSubmissionWebhookPayload`, in
`transforms/cv_workspace_submission_webhook.py`) renders the CustomWebhook body. It is a transform
rather than a check, but it belongs to this pipeline: it returns the check name, the proposed-change
ID, and one entry per linked workspace with its ID, status, URL, and fabric name. See
[Transforms](./transforms.md#cvworkspacesubmissionwebhookpayload).

## Schema

`schemas/cv/cv.yml` defines `CloudvisionWorkspace` — `Cloudvision.Workspace` — the node the check
writes its workspace tracking to. See [Schemas](./schemas.md#cloudvisionworkspace--cloudvisionworkspace).

## Running and testing a check

Run it against a fabric from the CLI:

```bash
# Variables are passed as key=value; this check takes the fabric name.
uv run infrahubctl check cv-config-validation name=Fabric-L3LS-Multi-Domain --branch <branch-name>

# List the checks the repository defines
uv run infrahubctl check --list
```

In the UI, a check runs automatically as part of proposed-change validation; its result appears
under the proposed change's **Checks** tab.

Unit and integration coverage is in
[`tests/unit/test_cv_integration.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_cv_integration.py).
Because the check reaches CloudVision through PyAVD's `CVClient`, tests exercise it with that client
stubbed rather than against a live CloudVision instance.

## Adding a check

1. Write the GraphQL query under `checks/` and register it in the `queries:` block of
   `.infrahub.yml`.
2. Regenerate the matching `*_query.py` — do not hand-write it:

   ```bash
   uv run infrahubctl graphql generate-return-types checks/my_check.gql
   ```

3. Implement a class deriving from `InfrahubCheck`, setting `query` and implementing
   `async def validate(self, data)`. Report through `self.log_info()` and `self.log_error()`; an
   error fails the check.
4. Register it under `check_definitions:` with its `targets` group and `parameters`.
5. Add tests under `tests/unit/`.

## Source

- Checks: [`checks/`](https://github.com/opsmill/infrahub-arista-avd/tree/main/checks)
- Registration: [`.infrahub.yml`](https://github.com/opsmill/infrahub-arista-avd/blob/main/.infrahub.yml) — `check_definitions:` block.
- Operator documentation: [CloudVision Validation](/cloudvision).
