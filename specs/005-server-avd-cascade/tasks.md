# Tasks: Server AVD Cascade

## Task 1: Add cascade trigger to ServerCablingGenerator

**Description**: After the server cabling generator finishes creating links, navigate from the server's rack to the fabric and trigger the AVD hostvar regeneration cascade.

**Changes**:
- `generators/generate_server_cabling.py`: Import `set_fabric_avd_hostvars_ready` and `trigger_hostvar_generation` from `solution_ai_dc.generator`. After the cabling loop, fetch rack → pod → fabric, set `avd_hostvars_ready = False`, then call `trigger_hostvar_generation()`.

**Dependencies**: None

## Task 2: Add unit tests for the cascade trigger

**Description**: Test that the ServerCablingGenerator triggers hostvar regeneration after cabling.

**Changes**:
- `tests/unit/test_server_cabling.py`: Add tests verifying:
  - After successful cabling, `set_fabric_avd_hostvars_ready(False)` is called
  - After successful cabling, `trigger_hostvar_generation()` is called
  - When no links are created (no interfaces), cascade is still triggered
  - When server has no rack, cascade is NOT triggered

**Dependencies**: Task 1

## Task 3: Verify linting passes

**Description**: Run ruff and mypy to ensure no linting issues.

**Dependencies**: Task 1, Task 2
