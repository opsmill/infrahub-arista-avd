---
title: Role Mapping
description: Infrahub device roles mapped to PyAVD device types.
audience: developer
sidebar_position: 5
---

# Role Mapping

:::info Developer Guide
This page is part of the developer guide. Role names are **PyAVD-version-sensitive** — see the [overview](./overview.md#pyavd-version) for the pinned version.
:::

Infrahub's `NetworkDevice.role.value` is a string enum that the hostvars generator maps to a PyAVD `type`. The mapping lives in [`src/solution_arista_avd/avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/src/solution_arista_avd/avd.py):

## Table

| Infrahub role | PyAVD `type` |
|---------------|--------------|
| `super_spine` | `super-spine` |
| `spine` | `spine` |
| `leaf` | `l3leaf` |
| `l2leaf` | `l2leaf` |

## The mapping in code

```python
# src/solution_arista_avd/avd.py
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
    "l2leaf": "l2leaf",
}


def get_avd_type(role: str) -> str:
    if role not in ROLE_TO_AVD_TYPE:
        msg = f"Unknown device role: {role}"
        raise ValueError(msg)
    return ROLE_TO_AVD_TYPE[role]
```

An unrecognised role raises `ValueError` at generation time — Phase 1 will fail for that device.

## Role implications

The role governs several downstream behaviours in the hostvars generator and in PyAVD itself:

| Role | Uplink source | Gets EVPN data? | MLAG? |
|------|---------------|----------------|-------|
| `super_spine` | — (top of fabric) | No | No |
| `spine` | `super_spine` | No | No |
| `leaf` | `spine` | Yes | Yes (if peer set) |
| `l2leaf` | `leaf` | No (skipped) | Yes (if peer set) |

See [Hostvars Reference](./hostvars.md) for exactly which fields each role emits.

## Tests

The role mapping is exercised by:

- [`tests/unit/test_avd.py`](https://github.com/opsmill/infrahub-arista-avd/blob/main/tests/unit/test_avd.py) — covers `get_avd_type()` for each role and the `ValueError` on unknown roles.

## Adding a new role

See [Extending the Pipeline → Add a new device role](./extending.md#add-a-new-device-role).
