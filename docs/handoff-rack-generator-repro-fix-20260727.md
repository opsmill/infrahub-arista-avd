# Rack Generator Repro Fix Handoff - 2026-07-27

## User-Visible Failures

- Racks that are not ready, including `DC1_BORDER`, could fail with `AttributeError`
  when optional relationships such as `pod`, `loopback_pool`, or `prefix_pool`
  were absent.
- A rack generator run could complete its own rack work, then leave the
  `generate-rack:*` generator instance in `Error` because the downstream hostvar
  trigger timed out or returned an ambiguous server response.

## Root Causes

- `generators/generate_rack.py` dereferenced optional query relationships inline
  before validating prerequisites. Missing `pod`, parent fabric, or pool
  relationships therefore raised implementation exceptions instead of deferring
  the rack.
- The rack generator marked fabric hostvars stale before it knew the rack could
  actually run. Deferred or unrelated racks could therefore invalidate readiness.
- The shared generator trigger helper treated a missing
  `CoreGeneratorDefinition` as a logged no-op, did not pass SDK GraphQL timeouts,
  and had no way to tolerate only server responsiveness timeouts.
- In the Infrahub integration image, synced repository generator files are loaded
  from the checked-out repo, but `solution_arista_avd.generator` can still come
  from the image-installed package. The rack generator therefore needs a
  compatibility path until the image package includes the new helper signature.

## Implementation Details

- `generators/generate_rack.py`
  - Adds guarded extraction for rack, pod, parent fabric, `loopback_pool`,
    `prefix_pool`, and template relationships.
  - Defers missing prerequisites by logging a reason, setting
    `generation_complete=false` with `update_group_context=False`, and returning.
  - Keeps invalid rack configuration as hard errors:
    positive `amount_of_leafs` requires `leaf_switch_template`; positive
    `amount_of_l2leafs` requires `l2leaf_switch_template`.
  - Moves `set_fabric_avd_hostvars_ready(..., False)` until after prerequisite
    validation and spine readiness.
  - Calls hostvar generation after rack completion through
    `trigger_hostvar_generation_after_rack_completion()`.
  - Adds `_trigger_hostvar_generation_compat()` so rack completion still supports
    `timeout=300` plus tolerant server-timeout handling when the installed helper
    package is older than the repo code.

- `src/solution_arista_avd/generator.py`
  - Extends `_trigger_generator()` and `trigger_hostvar_generation()` with
    keyword-only `timeout` and `tolerate_timeout`.
  - Passes `timeout` to `client.execute_graphql`.
  - Raises `ValueError` when `CoreGeneratorDefinition` is missing.
  - Catches only `ServerNotResponsiveError` when `tolerate_timeout=True`; all
    GraphQL, auth, schema, validation, and other exceptions still propagate.

- `tests/unit/test_generate_rack.py`
  - Covers missing pod, parent fabric, loopback pool, prefix pool, and generated
    spines as deferrals.
  - Covers missing L3/L2 leaf templates as `ValueError`s.
  - Covers the rack-side compatibility trigger timeout behavior.

- `tests/unit/test_generator_mixin.py`
  - Covers missing generator definition, timeout passthrough,
    `ServerNotResponsiveError` tolerance, default non-tolerance, and propagation
    of non-timeout exceptions.

- `tests/integration/test_e2e_pipeline.py`
  - Adds an explicit rack rerun regression test that includes `DC1_BORDER`.
  - Captures normalized snapshots after two explicit rack rerun passes and
    compares generator statuses, IPAM addresses, physical-interface IP
    assignments, structured-config file metadata, and structured-config Ethernet
    IP references.

## Validation Status

Local validation completed successfully:

```bash
uv run pytest tests/unit/test_generate_rack.py tests/unit/test_generator_mixin.py
uv run ruff check generators/generate_rack.py src/solution_arista_avd/generator.py tests/unit/test_generate_rack.py tests/unit/test_generator_mixin.py tests/integration/test_e2e_pipeline.py
uv run ruff format --check generators/generate_rack.py src/solution_arista_avd/generator.py tests/unit/test_generate_rack.py tests/unit/test_generator_mixin.py tests/integration/test_e2e_pipeline.py
uv run mypy --show-error-codes src/solution_arista_avd
```

Remote integration validation was started on `black` from an isolated worktree
with `INFRAHUB_TESTING_IMAGE_VER=1.10.1`.

- First run of `tests/integration` reached the e2e module and showed failures.
- Focused rerun identified the image/repo import mismatch:
  `trigger_hostvar_generation() got an unexpected keyword argument 'timeout'`.
- The compatibility wrapper was added after that finding.
- A second focused e2e rerun passed through structured config/backfill and was
  running the explicit rack rerun regression test when the user requested the
  integration tests be stopped.
- The remote pytest process, testcontainers stack, patch file, and isolated
  worktree were cleaned up.

## Follow-Up

- Re-run the mandatory remote integration suite after merging the other pending
  change the user mentioned.
- If the rack rerun integration test remains slow, inspect whether the snapshot
  readiness condition should wait only on rack/hostvar-related generator
  instances instead of all active generator instances.
