# CloudVision Configuration Check Handoff

## Purpose

Date updated: 2026-07-09

This is the handoff file for continuing work on the
`feat/cv-config-check` feature. The feature validates generated EOS
configuration in CloudVision during Infrahub proposed-change validation.

Post-merge CloudVision workspace submission is intentionally out of scope for
this feature. Implement submission later with Semaphore or a separate workflow.

## Current Git State

Feature branch:

- Branch: `feat/cv-config-check`
- Latest local/remote commit after the follow-up work:
  `f78bf17 Match CV proposed changes by short source branch`.
- The earlier misplaced commit `9a73883 Use proposed change metadata for CV
  workspaces` was removed from `feat/infrahub-avd-lab`; equivalent work now
  lives correctly on `feat/cv-config-check` as the commits listed below.

Dependent lab branch:

- Branch: `feat/infrahub-avd-lab`
- Rebased successfully onto `feat/cv-config-check` after commit `f78bf17`.
- `feat/cv-config-check` was confirmed as an ancestor of
  `feat/infrahub-avd-lab`.
- Latest local/remote commit after the rebase:
  `d2ee035 Update lab Infrahub version environment`.
- The rebased lab branch was force-pushed with lease.

Untracked local handoff/config files at the time of this update:

- `docs/plan-cv-config-check.md`
- `docs/plan-infrahub-avd-seed-data.md`

Do not assume these are committed.

## Work Completed In This Session

Earlier committed on `feat/cv-config-check`:

```text
e87f2f2 Harden CloudVision config validation
```

The commit:

- Makes `checks/cv_config_check_query.py` tolerate nullable GraphQL
  relationships for `pod`, `avd_artifact`, `parent`, and
  `structured_config_file`.
- Hardens `checks/cv_config_check.py` so device filtering skips devices missing
  structured-config relationships instead of raising an `AttributeError`.
- Adds regression fixture coverage in `tests/unit/test_cv_integration.py` for
  devices with missing `pod`, missing `avd_artifact`, or missing
  `structured_config_file`.
- Updates `docs/docs/developer-guide/cloudvision.md` so it documents
  proposed-change validation only and no longer claims a post-merge
  `submit-cv-workspace` generator exists.

Validation run after the commit and after rebasing `feat/infrahub-avd-lab`:

```bash
uv run pytest tests/unit
```

Result:

```text
157 passed
```

Focused CloudVision lint:

```bash
uv run ruff check checks/cv_config_check.py checks/cv_helpers.py checks/cv_config_check_query.py tests/unit/test_cv_integration.py
```

Result:

```text
All checks passed!
```

Known unrelated full-repo Ruff issues remain outside this feature:

- `generators/generate_avd_device_structured_config.py`: try block length
- `scripts/verify_avd_structural_parity.py`: shebang/import formatting
- `src/solution_arista_avd/addressing.py`: duplicate `logging` import under
  `TYPE_CHECKING`

Follow-up commits completed later in the same work stream:

```text
77dd565 Use proposed change metadata for CV workspaces
b86ef23 Resolve CV workspace metadata from source branch
f78bf17 Match CV proposed changes by short source branch
```

These commits:

- Change CloudVision workspace names to
  `Infrahub Proposed Changes {proposed_change_name} - Fabric {fabric_name}`.
- Use the proposed-change description for the CloudVision workspace
  description, with the safe fallback
  `Infrahub proposed change validation` when no description exists.
- Enrich check context by looking up `CoreProposedChange` metadata. The
  primary lookup uses the initializer-provided proposed-change ID when
  Infrahub provides it.
- Add a live-run fallback for cases where the check initializer does not carry
  `proposed_change_id`: the check looks up the open proposed change by source
  branch. It tries the check branch name as-is and, for branches prefixed with
  `feat/`, also tries the short branch name without that prefix. This covers
  the live case where the repository branch is `feat/cv-config-check` while
  the proposed-change source branch is `cv-config-check`.
- Reconcile CloudVision workspace metadata when reusing deterministic
  workspaces.
- Add unit coverage for workspace naming, description fallback,
  proposed-change metadata lookup, and the short source-branch fallback.

Validation after the final rebase of `feat/infrahub-avd-lab`:

```bash
uv run ruff check checks/cv_config_check.py checks/cv_helpers.py tests/unit/test_cv_integration.py
uv run mypy checks/cv_helpers.py checks/cv_config_check.py tests/unit/test_cv_integration.py
uv run pytest tests/unit
```

Result:

```text
Ruff passed
Mypy passed for the touched CloudVision check files
176 passed
```

## Feature Architecture

Proposed-change validation flow:

```text
Proposed Change created or updated
  -> cv-config-validation check, per fabric
     -> collect devices with structured-config artifacts
     -> require serial numbers for CloudVision-managed devices
     -> render EOS CLI with pyavd.get_device_config()
     -> create or roll back deterministic CloudVision workspace
     -> verify serial-numbered devices in CloudVision inventory
     -> deploy configlets to Static Configuration Studio
     -> build workspace
     -> track workspace in Infrahub when CloudvisionWorkspace schema exists
```

Primary files:

- `.infrahub.yml`: registers `cv_config_check` and `cv-config-validation`.
- `checks/cv_config_check.py`: main proposed-change validation check.
- `checks/cv_config_check.gql`: fabric and device query for validation.
- `checks/cv_config_check_query.py`: Pydantic model for the check query.
- `checks/cv_helpers.py`: CloudVision environment parsing, workspace IDs,
  proposed-change identity, and workspace rollback helper.
- `schemas/cv/cv.yml`: `CloudvisionWorkspace` schema.
- `repository_checks.yml`: seed data for `CoreGraphQLQuery` and
  `CoreCheckDefinition`.
- `tasks.py`: loads `repository_checks.yml` after `repository.yml` and
  repository sync.
- `tests/unit/test_cv_integration.py`: unit coverage for device filtering and
  deterministic workspace IDs.

Important registration detail:

- `.infrahub.yml` registers the query under top-level `queries`.
- `CVConfigValidationCheck.query = "cv_config_check"` binds the Python check to
  that query.
- `check_definitions` must not contain a `query:` key.
- `repository_checks.yml` does include `query: cv_config_check` because it
  creates live `CoreCheckDefinition` seed data, not `.infrahub.yml` config.

## Runtime Configuration

CloudVision credentials are read from task-worker environment variables:

```bash
CLOUDVISION_SERVERS=www.cv-prod-euwest-2.arista.io
CLOUDVISION_TOKEN=<service-account-token>
CLOUDVISION_VERIFY_CERTS=true
```

Token authentication is preferred. Username/password authentication is also
supported:

```bash
CLOUDVISION_USERNAME=<username>
CLOUDVISION_PASSWORD=<password>
```

Optional proxy variables:

```bash
CLOUDVISION_PROXY_HOST=<proxy-host>
CLOUDVISION_PROXY_PORT=<proxy-port>
CLOUDVISION_PROXY_USERNAME=<proxy-username>
CLOUDVISION_PROXY_PASSWORD=<proxy-password>
```

`docker-compose.override.yml` passes these variables into the custom Infrahub
runtime through the shared service environment.

## Last Known Live State

Live validation was retested on `black` after fixing the task-worker
CloudVision runtime configuration. The previous blocker was not missing
environment propagation into the workers: the token reached both task-worker
containers, and `get_cloudvision_config()` picked it up correctly. The
`UNAUTHENTICATED` / `401` CloudVision response was caused by using the wrong
CloudVision server, `www.arista.io`.

Correct CloudVision server:

```bash
CLOUDVISION_SERVERS=www.cv-prod-euwest-2.arista.io
```

After updating `.env` with the correct server and recreating the task-worker
containers, `cv-config-validation` succeeded.

Live target:

- URL: `http://black.tfd:8000`
- Proposed change under test: `test`
- Source branch: `cv-config-check`
- Destination branch: `main`
- Proposed change state: `open`

Latest observed `cv-config-validation` run after fixing CloudVision server
configuration:

- State: `completed`
- Conclusion: `success`
- Branch: `cv-config-check`
- Workspace ID after the proposed-change metadata fix:
  `ws-b9ed1f9f-bf20-5947-a79e-2809515dbfdf`
- Workspace tracking: exists on branch `cv-config-check`
- Workspace tracking name:
  `Infrahub Proposed Changes test - Fabric INFRAHUB_AVD`
- Workspace tracking proposed-change ID:
  `18c0a166-1d8c-3307-2cab-c5170d11f768`
- Workspace tracking status: `built`

Earlier failed runs for the same feature included:

- Missing CloudVision credentials in the task-worker environment, before the
  variables were passed into both task-worker containers.
- `UNAUTHENTICATED` / `401` responses from CloudVision when
  `CLOUDVISION_SERVERS` was incorrectly set to `www.arista.io`.

Earlier repository loading issue:

- `RepositoryFileNotFoundError` was previously fixed by updating
  `test-repository.commit` on both `main` and `test2` to a commit containing
  `.infrahub.yml` and `checks/cv_config_check.py`.
- The previous fixed commit pointer was:

```text
9da744a9f0741f96a622738a57bcdbc07d49f5da
```

If testing the latest local feature work in live Infrahub, update the live
repository commit pointer to a pushed commit that includes `e87f2f2` or a later
successor.

## Workspace Behavior

`CloudvisionWorkspace` tracks:

- `workspace_id`: deterministic CloudVision workspace ID
- `proposed_change_id`: proposed change that created the workspace
- `status`: `pending`, `built`, `submitted`, or `abandoned`
- `fabric`: fabric validated by the workspace

The workspace ID is deterministic from proposed-change ID and fabric name, so a
validation rerun updates the same CloudVision workspace instead of creating a
new one. Concurrent proposed changes on the same fabric use different
workspaces because their proposed-change IDs differ.

Device selection is serial-aware:

- Devices must belong to the target fabric and have an AVD structured-config
  artifact.
- Devices with missing `pod`, missing `avd_artifact`, or missing
  `structured_config_file` are skipped during selection.
- If a fabric has no serial-numbered devices with structured configs, the check
  skips CloudVision validation for that fabric.
- If at least one selected device has a serial number and other selected
  devices are missing serial numbers, the check fails clearly and lists the
  missing devices.

The check handles missing `CloudvisionWorkspace` schema gracefully by logging a
server-side warning and skipping workspace tracking. CloudVision validation
still runs.

## Next Steps

For code/branch work:

1. Push `feat/cv-config-check` if the latest commit should be tested by live
   Infrahub.
2. If needed, force-push `feat/infrahub-avd-lab` with lease because it was
   rebased.
3. Keep post-merge CloudVision submission out of this feature unless a separate
   plan is created.

For live validation on `black`:

1. Keep `.env` using the correct CloudVision server:
   `CLOUDVISION_SERVERS=www.cv-prod-euwest-2.arista.io`.
2. Ensure the CloudVision token is still present in both task-worker container
   environments.
3. Recreate or restart the Infrahub task-worker containers after any `.env`
   changes.
4. Verify the live schema exposes `CloudvisionWorkspace`.
5. Verify live repository definitions exist for `cv_config_check` and
   `cv-config-validation`.
6. Ensure the live repository commit pointer references a pushed commit that
   contains the latest feature files.
7. Rerun user-defined checks for proposed change `test` on branch
   `cv-config-check`.
8. Inspect task status, validation logs, and workspace objects.

When CloudVision or EOS validation returns value mismatches, treat them as seed
data fixes first. Change schema or generator code only when the existing model
cannot represent the required configuration.

Follow-up implementation tasks:

- Done: change the CloudVision workspace name format to
  `Infrahub Proposed Changes {proposed_changes_name} - Fabric {fabric_name}`.
- Done: change the CloudVision workspace description to use the proposed change
  description instead of the hardcoded `Infrahub proposed change validation`.
- Done: define a safe fallback for proposed changes that do not have a
  description.
- Done: handle live check executions where the initializer lacks
  `proposed_change_id` by looking up the open proposed change by source branch.

Optional improvements:

- Report CloudVision config diffs in the check output after successful builds.
- Add cleanup for abandoned proposed-change workspaces.
- Add a fabric-level configuration flag or group filter if CloudVision
  validation should only target a subset of fabrics.
- Design Semaphore-based post-merge workspace submission in a separate plan.

## Retest Commands

Rerun only user-defined checks for `test`:

```bash
uv run python - <<'PY'
import asyncio

from infrahub_sdk import InfrahubClient
from infrahub_sdk.config import Config


async def main() -> None:
    client = InfrahubClient(
        config=Config(
            address="http://black.tfd:8000",
            username="admin",
            password="infrahub",
        )
    )
    await client.login()
    result = await client.execute_graphql(
        query="""
mutation RunPcChecks($id: String!, $checkType: CheckType) {
  CoreProposedChangeRunCheck(data: {id: $id, check_type: $checkType}) { ok }
}
""",
        variables={
            # Replace with the current CoreProposedChange ID for `test` if it changes.
            "id": "<test-proposed-change-id>",
            "checkType": "USER",
        },
    )
    print(result)


asyncio.run(main())
PY
```

Expected accepted response:

```text
{'CoreProposedChangeRunCheck': {'ok': True}}
```

Check task status:

```bash
INFRAHUB_ADDRESS=http://black.tfd:8000 uv run infrahubctl task list
```

Check task-worker logs:

```bash
ssh black 'docker logs --since 5m infrahub-task-worker-1 2>&1 | egrep -i "cv-config|cloudvision|credentials|workspace|RepositoryFileNotFound|CVConfig|validation|exception|traceback|error|warning" | tail -180'
ssh black 'docker logs --since 5m infrahub-task-worker-2 2>&1 | egrep -i "cv-config|cloudvision|credentials|workspace|RepositoryFileNotFound|CVConfig|validation|exception|traceback|error|warning" | tail -180'
```

Check live validation and workspace state:

```graphql
query ProposedChangeCheckState {
  CoreProposedChange(name__value: "test") {
    edges {
      node {
        id
        name { value }
        source_branch { value }
        destination_branch { value }
        state { value }
        validations {
          edges {
            node {
              label { value }
              state { value }
              conclusion { value }
              started_at { value }
              completed_at { value }
              checks {
                edges {
                  node {
                    display_label
                    severity { value }
                    message { value }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  CloudvisionWorkspace {
    count
    edges {
      node {
        id
        display_label
        workspace_id { value }
        proposed_change_id { value }
        status { value }
      }
    }
  }
}
```

Confirm the task-worker repository snapshot contains the CloudVision files:

```bash
ssh black 'docker exec infrahub-task-worker-1 git -C /upstream rev-parse HEAD'
ssh black 'docker exec infrahub-task-worker-1 git -C /upstream ls-tree -r HEAD -- checks .infrahub.yml'
```

## Expected Success Criteria

Current retest result:

- `RepositoryFileNotFoundError` did not reappear.
- `CloudVision credentials not configured` did not reappear after environment
  propagation was fixed.
- `UNAUTHENTICATED` / `401` did not reappear after switching from
  `www.arista.io` to `www.cv-prod-euwest-2.arista.io`.
- The check created or updated CloudVision workspace
  `ws-b9ed1f9f-bf20-5947-a79e-2809515dbfdf`.
- `CloudvisionWorkspace` tracking exists in Infrahub on branch
  `cv-config-check`.
- `cv-config-validation` completed with `success` for proposed change `test`.

Expected success criteria for future reruns:

- `RepositoryFileNotFoundError` does not reappear.
- `CloudVision credentials not configured` does not reappear.
- `UNAUTHENTICATED` / `401` does not reappear when using
  `www.cv-prod-euwest-2.arista.io`.
- The check creates or updates the deterministic CloudVision workspace.
- At least one `CloudvisionWorkspace` object exists in Infrahub when the schema
  is loaded.
- `cv-config-validation` completes with `success`, unless CloudVision returns a
  real EOS or config validation failure.

## Known Issues

- Resolved in `b86ef23` and `f78bf17`: the CloudVision workspace no longer
  intentionally falls back to `local` during live proposed-change validation.
  If `proposed_change_id` is absent from the check initializer, the check
  derives proposed-change metadata from the open proposed change whose
  `source_branch` matches the check branch or its short `feat/`-stripped name.
- The disposable `black` instance may retain stale data from earlier live runs,
  including a `CloudvisionWorkspace` object with `proposed_change_id=local`.
  This is expected to disappear after a clean rebuild.

## Infrahub Default Branch and Repository Sync Recovery

### Default-branch mismatch observed on `black`

Before the clean-rebuild plan below, the live `black` instance had this state:

```text
Infrahub default branch: main
test-repository.default_branch: feat/infrahub-avd-lab
test-repository.commit: d2ee0356e207c2a96992653e36ba122a4cd5cf39
test-repository.sync_status: in-sync
test-repository.operational_status: error
```

Infrahub task-worker logs repeatedly showed:

```text
Ignoring import of mismatched default branch
branch=main
repository=test-repository
```

The Infrahub runtime setting that controls the default branch is:

```bash
INFRAHUB_INITIAL_DEFAULT_BRANCH=feat/infrahub-avd-lab
```

This is an initialization-only setting. Changing it after the instance has
already been initialized is not a normal supported runtime toggle. For the
disposable `black` lab, the clean fix is to rebuild/reinitialize the Infrahub
instance with that environment variable set before `invoke load`.

### Recovering cleanly after force-updating the branch Infrahub tracks

Avoid force-pushing or rebasing the Git branch that Infrahub uses as the
repository/default branch whenever possible. Prefer fast-forward commits or use
a new feature branch. If a force update is unavoidable, treat the Infrahub
repository checkout as stateful and recover it deliberately before relying on
repository sync.

Recommended recovery workflow:

1. Pause automatic repository sync if practical, or at least stop task workers
   while repairing the checkout.
2. On `black`, reset the repository checkout used by Infrahub to the forced
   remote branch:

   ```bash
   ssh black 'cd ~/git/infrahub && \
     git fetch origin feat/infrahub-avd-lab && \
     git checkout feat/infrahub-avd-lab && \
     git reset --hard origin/feat/infrahub-avd-lab && \
     git clean -fd'
   ```

3. If the live `CoreRepository.commit` value does not match the new branch
   HEAD, update it or let a successful sync update it. The ad-hoc update used
   during this session was:

   ```python
   repo = await client.get(
       kind="CoreRepository",
       name__value="test-repository",
       branch="<branch-name>",
   )
   repo.commit.value = "<new-branch-head>"
   await repo.save()
   ```

4. Restart task workers and trigger or wait for repository sync.
5. Verify:

   ```bash
   ssh black 'cd ~/git/infrahub && uv run infrahubctl repository list'
   ```

Expected healthy repository status:

```text
Operational status: online
Sync status: in-sync
Internal status: active
```

If sync fails with a generic conflict message after a force update, inspect the
task-worker logs:

```bash
ssh black 'docker logs --since 10m infrahub-task-worker-1 2>&1 | \
  egrep -i "repository|sync|error|exception|traceback|conflict|worktree|failed" | tail -220'
ssh black 'docker logs --since 10m infrahub-task-worker-2 2>&1 | \
  egrep -i "repository|sync|error|exception|traceback|conflict|worktree|failed" | tail -220'
```

The failure observed in this session looked like:

```text
Failed to synchronize branch, skipping it.
branch=feat/infrahub-avd-lab
reason=Unable to pull the branch feat/infrahub-avd-lab for repository test-repository, there are conflicts that must be resolved.
RepositoryError: Unable to synchronize the following branches of repository test-repository: feat/infrahub-avd-lab
```

This message is raised around `git pull`; after a rebase/force-push the local
checkout can diverge from the remote branch and Infrahub's sync may refuse to
reconcile it automatically.

### Does rebuilding with `INFRAHUB_INITIAL_DEFAULT_BRANCH` avoid the force-update recovery flow?

It avoids the default-branch mismatch and should prevent the
`Ignoring import of mismatched default branch` noise. It does **not** make
future force-pushes to the tracked branch automatically safe. If the branch
Infrahub tracks is force-updated again after initialization and after Infrahub
has a local clone/worktree for it, the local Git state can still diverge and
the recovery flow above may still be required.

For a disposable lab, a full rebuild with
`INFRAHUB_INITIAL_DEFAULT_BRANCH=feat/infrahub-avd-lab` is the cleanest way to
clear stale repository sync state, stale `CloudvisionWorkspace` objects, and
the default-branch mismatch at the same time.

## Known Live Noise

The task-worker logs may repeatedly show an unrelated repository sync warning:

```text
Failed to synchronize branch, skipping it.
branch=feat/infrahub-avd-lab
reason=Unable to identify the worktree for the branch : feat/infrahub-avd-lab
repository=test-repository
```

This was not the active blocker for `cv-config-validation` after the repository
commit pointer was corrected.

## Live Patch Workflow

When making additional fixes for this feature, use this workflow:

1. Validate the patch locally.
2. Commit it on `feat/cv-config-check`.
3. Rebase `feat/infrahub-avd-lab` onto `feat/cv-config-check`.
4. Push both branches.
5. Update `black` to the latest `feat/infrahub-avd-lab`.
6. Rerun the `cv-config-validation` check.
