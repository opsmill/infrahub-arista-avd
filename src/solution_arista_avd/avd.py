"""AVD (Arista Validated Design) utilities for Infrahub integration.

Role mapping shared between the hostvar generator and the rest of the
solution. The per-device hostvars assembly itself lives in
``generators/generate_avd_device_hostvar.py``.
"""

from __future__ import annotations

# Mapping from Infrahub device roles to AVD types.
# Every value is a valid pyAVD ``node_type_keys`` type for the pinned pyAVD range.
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
    "border_leaf": "l3leaf",
    "l2leaf": "l2leaf",
    # Standalone L2LS fabric (and campus core) roles.
    "l2spine": "l2spine",
    "l3spine": "l3spine",
    # MPLS / ISIS-LDP IPVPN provider roles.
    "p": "p",
    "pe": "pe",
    "rr": "rr",
}


# Non-L3LS example fabrics select spine/leaf device roles from the fabric
# underlay, gated so routed L3LS fabrics (ebgp) keep the default spine/leaf roles:
#   underlay "none"     -> standalone L2LS (l2spine + l2leaf)
#   underlay "ospf"     -> campus (l3spine core + l2leaf access)
#   underlay "isis-ldp" -> MPLS/IPVPN (P core in the spine position + PE in the
#                          leaf position; PE-P links are ISIS-LDP p2p uplinks)
SPINE_ROLE_BY_UNDERLAY: dict[str, str] = {
    "none": "l2spine",
    "ospf": "l3spine",
    "isis-ldp": "p",
}
LEAF_ROLE_BY_UNDERLAY: dict[str, str] = {
    "none": "l2leaf",
    "ospf": "l2leaf",
    "isis-ldp": "pe",
}
# Underlays whose main leaf tier uplinks to the spine tier (interface role "spine"),
# as opposed to the L3LS access-tier l2leaf that uplinks to an L3 leaf (role "leaf").
SPINE_UPLINK_UNDERLAYS: frozenset[str] = frozenset({"none", "ospf", "isis-ldp"})
# Leaf-tier device roles that uplink to the spine tier via interface role "spine".
SPINE_UPLINK_LEAF_ROLES: frozenset[str] = frozenset({"pe"})
# Underlay sentinel that is a design signal, not a real pyAVD underlay value, so
# the generator must not emit `underlay_routing_protocol` for it.
NON_EMITTED_UNDERLAYS: frozenset[str] = frozenset({"none"})
# Main-tier device roles of non-L3LS designs (standalone L2LS, campus) that form
# MLAG pairs and therefore need node-group / peer-link / MLAG-domain rendering,
# just like the L3LS leaf family. Gated on SPINE_UPLINK_UNDERLAYS at the call site
# so the L3LS access-tier l2leaf (pure access under EVPN) is unaffected.
MLAG_MAIN_TIER_ROLES: frozenset[str] = frozenset({"l2leaf", "l2spine", "l3spine"})
# Device roles that render anycast SVIs (ip_address_virtual) and therefore need a
# node-level virtual_router_mac_address: L3 leaves, the campus l3spine SVI-routing
# core, and the MPLS PE. Deliberately excludes the pure-L3 fabric transit roles
# (spine, super_spine, p, rr) — which carry a fabric virtual_router_mac but no
# SVIs — so routed L3LS spines keep their existing (mac-free) node config.
SVI_RENDERING_ROLES: frozenset[str] = frozenset({"leaf", "border_leaf", "l3spine", "pe"})


def get_avd_type(role: str) -> str:
    """Convert Infrahub device role to AVD device type.

    Args:
        role: The Infrahub device role (e.g. super_spine, spine, leaf,
            border_leaf, l2leaf, l2spine, l3spine, p, pe, rr).

    Returns:
        The corresponding AVD device type

    Raises:
        ValueError: If the role is not recognized
    """
    if role not in ROLE_TO_AVD_TYPE:
        msg = f"Unknown device role: {role}"
        raise ValueError(msg)
    return ROLE_TO_AVD_TYPE[role]
