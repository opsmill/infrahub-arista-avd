"""AVD (Arista Validated Design) utilities for Infrahub integration.

Role mapping shared between the hostvar generator and the rest of the
solution. The per-device hostvars assembly itself lives in
``generators/generate_avd_device_hostvar.py``.
"""

from __future__ import annotations

# Mapping from Infrahub device roles to AVD types
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
    "border_leaf": "l3leaf",
    "l2leaf": "l2leaf",
}


def get_avd_type(role: str) -> str:
    """Convert Infrahub device role to AVD device type.

    Args:
        role: The Infrahub device role (super_spine, spine, leaf, l2leaf)

    Returns:
        The corresponding AVD device type

    Raises:
        ValueError: If the role is not recognized
    """
    if role not in ROLE_TO_AVD_TYPE:
        msg = f"Unknown device role: {role}"
        raise ValueError(msg)
    return ROLE_TO_AVD_TYPE[role]
