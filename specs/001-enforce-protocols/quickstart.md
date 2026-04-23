# Quickstart: Enforce Protocol-Typed Access

**Branch**: `001-enforce-protocols` | **Date**: 2026-02-10

## Prerequisites

- Python >=3.11
- `uv` package manager
- Running Infrahub instance (for `infrahubctl protocols` generation)
- All schemas loaded (`inv load-schema`)

## Setup

```bash
git checkout 001-enforce-protocols
uv sync --all-packages
```

## Development Workflow

### Step 1: Regenerate protocol classes

```bash
infrahubctl protocols --output src/solution_arista_avd/protocols.py
```

Verify the new Routing protocol classes exist:
```bash
grep -c "class Routing" src/solution_arista_avd/protocols.py
```

Expected: 7 (one per Routing node type).

### Step 2: Update generators

Replace string-kind references with protocol class imports in:
- `generators/backfill_structured_config.py` (10 calls)
- `generators/generate_avd_device_hostvar.py` (1 call)

### Step 3: Update avd_fabric_doc transform

1. Fix the GraphQL query in `transforms/avd_fabric_devices.gql`
2. Update Pydantic models in `transforms/avd_fabric_devices_query.py`
3. Replace raw dict access with Pydantic model attribute access

### Step 4: Clean up avd.py dead code

Remove or type the unused `extract_uplink_info()` and `build_fabric_hostvars()` functions.

### Step 5: Verify

```bash
pytest tests/unit                    # All unit tests pass
inv lint                             # ruff + mypy + yamllint pass
grep 'kind="' generators/*.py       # Zero string-kind matches
```

## Key Files

| File | Role |
| ---- | ---- |
| `src/solution_arista_avd/protocols.py` | Generated protocol classes (regenerate first) |
| `generators/backfill_structured_config.py` | Main target: 10 string-kind → protocol |
| `generators/generate_avd_device_hostvar.py` | Minor fix: 1 string-kind → protocol |
| `transforms/avd_fabric_doc.py` | Dict access → Pydantic models |
| `transforms/avd_fabric_devices.gql` | GraphQL query to fix |
| `transforms/avd_fabric_devices_query.py` | Pydantic models to update |
| `src/solution_arista_avd/avd.py` | Dead code cleanup |
