from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from ipaddress import ip_network
from typing import TYPE_CHECKING, Any, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Iterable
    from ipaddress import IPv4Network, IPv6Network


class ResourceRole(StrEnum):
    MANAGEMENT = "management"
    LOOPBACK = "loopback"
    LOOPBACK_VTEP = "loopback-vtep"
    FABRIC_POINT_TO_POINT = "fabric_point_to_point"
    DCI = "dci"
    FABRIC_SUPERNET = "fabric_supernet"
    MLAG = "mlag"
    MLAG_PEERING = "mlag_peering"


class PoolRoleResolutionError(ValueError):
    """Raised when pool resources cannot resolve to one authoritative role."""


@dataclass(frozen=True)
class RequiredPoolRole:
    role: ResourceRole
    label: str
    pool_kind: Literal["CoreIPAddressPool", "CoreIPPrefixPool"]


LEGACY_ROLE_ALIASES: dict[str, ResourceRole] = {
    "supernet": ResourceRole.FABRIC_SUPERNET,
    "pod_leaf_spine": ResourceRole.FABRIC_POINT_TO_POINT,
    "pod_super_spine_spine": ResourceRole.FABRIC_POINT_TO_POINT,
}

POOL_ROLE_BY_PREFIX_ROLE: dict[str, ResourceRole] = {
    "management": ResourceRole.MANAGEMENT,
    "loopback": ResourceRole.LOOPBACK,
    "loopback-vtep": ResourceRole.LOOPBACK_VTEP,
    "fabric_point_to_point": ResourceRole.FABRIC_POINT_TO_POINT,
    "dci": ResourceRole.DCI,
    "fabric_supernet": ResourceRole.FABRIC_SUPERNET,
    "mlag": ResourceRole.MLAG,
    "mlag_peering": ResourceRole.MLAG_PEERING,
    **LEGACY_ROLE_ALIASES,
}

# IpamPrefix.role values that can occupy space inside a Fabric Supernet. Used to
# read back what has already been carved out, so successive allocations do not
# land on top of each other. The supernet's own role is excluded: it is the
# container being carved, not an allocation within it.
ALLOCATED_PREFIX_ROLE_VALUES: tuple[str, ...] = tuple(
    sorted(
        prefix_role
        for prefix_role, role in POOL_ROLE_BY_PREFIX_ROLE.items()
        if role is not ResourceRole.FABRIC_SUPERNET
    )
)

FABRIC_POOL_ROLES: frozenset[ResourceRole] = frozenset(
    {
        ResourceRole.MANAGEMENT,
        ResourceRole.LOOPBACK,
        ResourceRole.LOOPBACK_VTEP,
        ResourceRole.FABRIC_POINT_TO_POINT,
        ResourceRole.DCI,
        ResourceRole.FABRIC_SUPERNET,
    }
)
POD_POOL_ROLES: frozenset[ResourceRole] = frozenset(
    {
        ResourceRole.LOOPBACK,
        ResourceRole.LOOPBACK_VTEP,
        ResourceRole.FABRIC_POINT_TO_POINT,
        ResourceRole.MLAG,
        ResourceRole.MLAG_PEERING,
    }
)
SCOPE_ROLES: dict[str, frozenset[ResourceRole]] = {
    "fabric": FABRIC_POOL_ROLES,
    "pod": POD_POOL_ROLES,
}

FABRIC_REQUIRED_ROLES: tuple[RequiredPoolRole, ...] = (
    RequiredPoolRole(ResourceRole.MANAGEMENT, "Management", "CoreIPAddressPool"),
    RequiredPoolRole(ResourceRole.LOOPBACK, "Loopback", "CoreIPPrefixPool"),
    RequiredPoolRole(ResourceRole.LOOPBACK_VTEP, "Loopback VTEP", "CoreIPPrefixPool"),
    RequiredPoolRole(ResourceRole.FABRIC_POINT_TO_POINT, "Fabric Point-to-Point", "CoreIPPrefixPool"),
    RequiredPoolRole(ResourceRole.DCI, "DCI", "CoreIPPrefixPool"),
)
FABRIC_SUPERNET_ALLOCATION_ORDER: tuple[ResourceRole, ...] = (
    ResourceRole.LOOPBACK,
    ResourceRole.LOOPBACK_VTEP,
    ResourceRole.FABRIC_POINT_TO_POINT,
    ResourceRole.DCI,
)
FABRIC_SUPERNET_PREFIX_LENGTHS: dict[ResourceRole, int] = {
    ResourceRole.LOOPBACK: 27,
    ResourceRole.LOOPBACK_VTEP: 27,
    ResourceRole.FABRIC_POINT_TO_POINT: 24,
    ResourceRole.DCI: 24,
}
FABRIC_SUPERNET_ROLE_LABELS: dict[ResourceRole, str] = {
    ResourceRole.LOOPBACK: "Loopback",
    ResourceRole.LOOPBACK_VTEP: "Loopback-VTEP",
    ResourceRole.FABRIC_POINT_TO_POINT: "Fabric-Point-to-Point",
    ResourceRole.DCI: "DCI",
}


@dataclass(frozen=True)
class MlagDefaultPool:
    """Fallback MLAG pool definition, carved per pod from a shared supernet.

    The pools are named per pod and each pod is allocated its own child prefix:
    a single shared prefix would cap the deployment at one MLAG pair (PyAVD
    carves a /31 per pair out of the pool) and would put every pod's MLAG L3
    peering addresses on the same subnet, which the underlay then advertises
    from several places at once.
    """

    name_suffix: str
    supernet: str
    prefix_length: int


MLAG_DEFAULT_POOLS: dict[ResourceRole, MlagDefaultPool] = {
    # RFC 3927 link-local: the MLAG peer-link is a back-to-back L2 connection,
    # so its addresses never leave the pair and the block is safe to reuse.
    ResourceRole.MLAG: MlagDefaultPool(
        name_suffix="MLAG-Peer-Subnet",
        supernet="169.254.0.0/16",
        prefix_length=24,
    ),
    # MLAG L3 peering addresses are advertised into the underlay, so there is no
    # universally safe default. This block only exists so generation does not
    # fail outright; the fabric pool check requires an explicit mlag_peering pool.
    ResourceRole.MLAG_PEERING: MlagDefaultPool(
        name_suffix="MLAG-L3-Peering-Subnet",
        supernet="192.0.0.0/24",
        prefix_length=28,
    ),
}


def mlag_default_pool_name(*, pod_name: str, role: ResourceRole) -> str:
    """Return the pod-scoped name of a fallback MLAG pool."""
    return f"{pod_name}-{MLAG_DEFAULT_POOLS[role].name_suffix}"


def next_available_prefix(
    supernets: Iterable[IPv4Network | IPv6Network],
    used_prefixes: Iterable[IPv4Network | IPv6Network],
    prefix_length: int,
) -> IPv4Network | IPv6Network | None:
    """Return the first child prefix of ``supernets`` that no used prefix overlaps.

    Supernets are grouped by IP version before sorting: ``ipaddress`` refuses to
    order networks of different families, so a dual-stack pool would otherwise
    raise ``TypeError`` instead of skipping the mismatched family.
    """
    used = list(used_prefixes)
    by_version: dict[int, list[IPv4Network | IPv6Network]] = {}
    for supernet in supernets:
        by_version.setdefault(supernet.version, []).append(supernet)

    for version in sorted(by_version):
        for supernet in sorted(by_version[version]):
            if prefix_length < supernet.prefixlen:
                continue
            for child in supernet.subnets(new_prefix=prefix_length):
                if not any(child.overlaps(prefix) for prefix in used if prefix.version == version):
                    return child
    return None


def map_prefix_role(prefix_role: str | None) -> ResourceRole | None:
    """Map an IpamPrefix.role value to the authoritative pool role."""
    if prefix_role is None:
        return None
    return POOL_ROLE_BY_PREFIX_ROLE.get(prefix_role)


def resolve_resource_role(
    prefix_roles: list[str | None] | tuple[str | None, ...], *, scope: Literal["fabric", "pod"], pool_name: str
) -> ResourceRole:
    """Resolve a pool's backing prefix roles to one authoritative role."""
    mapped_roles = {role for prefix_role in prefix_roles if (role := map_prefix_role(prefix_role)) is not None}
    if not mapped_roles:
        msg = f"Pool {pool_name!r} does not satisfy {scope} pool requirements"
        raise PoolRoleResolutionError(msg)
    if len(mapped_roles) > 1:
        msg = f"Pool {pool_name!r} has mixed roles: {sorted(mapped_roles)}"
        raise PoolRoleResolutionError(msg)

    role = next(iter(mapped_roles))
    if role not in SCOPE_ROLES[scope]:
        msg = f"Pool {pool_name!r} role {role.value!r} does not satisfy {scope} pool requirements"
        raise PoolRoleResolutionError(msg)
    return role


def fabric_required_roles(
    *,
    overlay_routing_protocol: str | None,
    underlay_routing_protocol: str | None,
    has_dci_links: bool,
) -> set[ResourceRole]:
    """Return required fabric-scope roles from routing and DCI intent."""
    roles = {ResourceRole.MANAGEMENT}
    if overlay_routing_protocol:
        roles.update({ResourceRole.LOOPBACK, ResourceRole.LOOPBACK_VTEP})
    if underlay_routing_protocol and underlay_routing_protocol != "none":
        roles.add(ResourceRole.FABRIC_POINT_TO_POINT)
    if has_dci_links:
        roles.add(ResourceRole.DCI)
    return roles


def validate_unique_roles(pool_roles: dict[str, ResourceRole], *, scope: Literal["fabric", "pod"]) -> None:
    """Reject more than one authoritative pool per role in a scope."""
    pools_by_role: dict[ResourceRole, list[str]] = {}
    for pool_name, role in pool_roles.items():
        if role not in SCOPE_ROLES[scope]:
            msg = f"Pool {pool_name!r} role {role.value!r} does not satisfy {scope} pool requirements"
            raise PoolRoleResolutionError(msg)
        pools_by_role.setdefault(role, []).append(pool_name)

    duplicates = {role: names for role, names in pools_by_role.items() if len(names) > 1}
    if duplicates:
        details = ", ".join(f"{role.value}: {', '.join(names)}" for role, names in sorted(duplicates.items()))
        msg = f"{scope.capitalize()} pool collection has duplicate authoritative roles: {details}"
        raise PoolRoleResolutionError(msg)


def missing_fabric_roles(*, required_roles: set[ResourceRole], available_roles: set[ResourceRole]) -> set[ResourceRole]:
    """Return missing fabric roles, requiring Fabric Supernet when fallback is needed."""
    missing = required_roles - available_roles
    if missing and ResourceRole.FABRIC_SUPERNET not in available_roles:
        missing_list = ", ".join(sorted(role.value for role in missing))
        msg = f"Missing fabric pool roles require a Fabric Supernet fallback: {missing_list}"
        raise PoolRoleResolutionError(msg)
    return missing


def validate_pod_pool_containment(
    *,
    pod_role_prefixes: dict[ResourceRole, list[str]],
    fabric_role_prefixes: dict[ResourceRole, list[str]],
    unconstrained_roles: frozenset[ResourceRole] | set[ResourceRole] = frozenset(),
) -> None:
    """Validate pod prefix pools are subnets of matching fabric prefix pools.

    ``unconstrained_roles`` are roles the fabric carves out of its Fabric Supernet
    on demand: there is no fabric pool to contain them yet, and that is a valid
    design rather than a missing pool.
    """
    for role in (ResourceRole.LOOPBACK, ResourceRole.LOOPBACK_VTEP, ResourceRole.FABRIC_POINT_TO_POINT):
        pod_prefixes = [ip_network(prefix) for prefix in pod_role_prefixes.get(role, [])]
        if not pod_prefixes:
            continue

        fabric_prefixes = [ip_network(prefix) for prefix in fabric_role_prefixes.get(role, [])]
        if not fabric_prefixes:
            if role in unconstrained_roles:
                continue
            msg = f"Pod pool role {role.value!r} has no matching fabric pool for containment"
            raise PoolRoleResolutionError(msg)

        for pod_prefix in pod_prefixes:
            if not any(
                pod_prefix.version == fabric_prefix.version and cast("Any", pod_prefix).subnet_of(fabric_prefix)
                for fabric_prefix in fabric_prefixes
            ):
                msg = f"Pod pool prefix {pod_prefix} for role {role.value!r} is not contained by matching fabric pool"
                raise PoolRoleResolutionError(msg)


def pod_required_mlag_roles(*, underlay_routing_protocol: str | None, has_mlag_enabled_rack: bool) -> set[ResourceRole]:
    """Return MLAG roles required by fabric underlay and rack MLAG state."""
    underlay_defined = bool(underlay_routing_protocol and underlay_routing_protocol != "none")
    roles: set[ResourceRole] = set()
    if not underlay_defined or has_mlag_enabled_rack:
        roles.add(ResourceRole.MLAG)
    if underlay_defined and has_mlag_enabled_rack:
        roles.add(ResourceRole.MLAG_PEERING)
    return roles
