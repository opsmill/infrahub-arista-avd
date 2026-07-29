from __future__ import annotations

from enum import StrEnum
from ipaddress import ip_network
from typing import Any, Literal, cast

from infrahub_sdk.checks import InfrahubCheck


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


POOL_ROLE_BY_PREFIX_ROLE: dict[str, ResourceRole] = {
    "management": ResourceRole.MANAGEMENT,
    "loopback": ResourceRole.LOOPBACK,
    "loopback-vtep": ResourceRole.LOOPBACK_VTEP,
    "fabric_point_to_point": ResourceRole.FABRIC_POINT_TO_POINT,
    "dci": ResourceRole.DCI,
    "fabric_supernet": ResourceRole.FABRIC_SUPERNET,
    "mlag": ResourceRole.MLAG,
    "mlag_peering": ResourceRole.MLAG_PEERING,
    "supernet": ResourceRole.FABRIC_SUPERNET,
    "pod_leaf_spine": ResourceRole.FABRIC_POINT_TO_POINT,
    "pod_super_spine_spine": ResourceRole.FABRIC_POINT_TO_POINT,
}

FABRIC_POOL_ROLES = frozenset(
    {
        ResourceRole.MANAGEMENT,
        ResourceRole.LOOPBACK,
        ResourceRole.LOOPBACK_VTEP,
        ResourceRole.FABRIC_POINT_TO_POINT,
        ResourceRole.DCI,
        ResourceRole.FABRIC_SUPERNET,
    }
)
POD_POOL_ROLES = frozenset(
    {
        ResourceRole.LOOPBACK,
        ResourceRole.LOOPBACK_VTEP,
        ResourceRole.FABRIC_POINT_TO_POINT,
        ResourceRole.MLAG,
        ResourceRole.MLAG_PEERING,
    }
)
SCOPE_ROLES = {
    "fabric": FABRIC_POOL_ROLES,
    "pod": POD_POOL_ROLES,
}
FABRIC_SUPERNET_ALLOCATION_ORDER = (
    ResourceRole.LOOPBACK,
    ResourceRole.LOOPBACK_VTEP,
    ResourceRole.FABRIC_POINT_TO_POINT,
    ResourceRole.DCI,
)
FABRIC_SUPERNET_PREFIX_LENGTHS = {
    ResourceRole.LOOPBACK: 27,
    ResourceRole.LOOPBACK_VTEP: 27,
    ResourceRole.FABRIC_POINT_TO_POINT: 24,
    ResourceRole.DCI: 24,
}


def map_prefix_role(prefix_role: str | None) -> ResourceRole | None:
    if prefix_role is None:
        return None
    return POOL_ROLE_BY_PREFIX_ROLE.get(prefix_role)


def resolve_resource_role(
    prefix_roles: list[str | None] | tuple[str | None, ...], *, scope: Literal["fabric", "pod"], pool_name: str
) -> ResourceRole:
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
    roles = {ResourceRole.MANAGEMENT}
    if overlay_routing_protocol:
        roles.update({ResourceRole.LOOPBACK, ResourceRole.LOOPBACK_VTEP})
    if underlay_routing_protocol and underlay_routing_protocol != "none":
        roles.add(ResourceRole.FABRIC_POINT_TO_POINT)
    if has_dci_links:
        roles.add(ResourceRole.DCI)
    return roles


def validate_unique_roles(pool_roles: dict[str, ResourceRole], *, scope: Literal["fabric", "pod"]) -> None:
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
) -> None:
    for role in (ResourceRole.LOOPBACK, ResourceRole.LOOPBACK_VTEP, ResourceRole.FABRIC_POINT_TO_POINT):
        pod_prefixes = [ip_network(prefix) for prefix in pod_role_prefixes.get(role, [])]
        if not pod_prefixes:
            continue

        fabric_prefixes = [ip_network(prefix) for prefix in fabric_role_prefixes.get(role, [])]
        if not fabric_prefixes:
            msg = f"Pod pool role {role.value!r} has no matching fabric pool for containment"
            raise PoolRoleResolutionError(msg)

        for pod_prefix in pod_prefixes:
            if not any(
                pod_prefix.version == fabric_prefix.version and cast("Any", pod_prefix).subnet_of(fabric_prefix)
                for fabric_prefix in fabric_prefixes
            ):
                msg = f"Pod pool prefix {pod_prefix} for role {role.value!r} is not contained by matching fabric pool"
                raise PoolRoleResolutionError(msg)


def _edges(container: Any) -> list[dict[str, Any]]:
    if not isinstance(container, dict):
        return []
    edges = container.get("edges")
    return edges if isinstance(edges, list) else []


def _node(edge_or_rel: Any) -> dict[str, Any] | None:
    if not isinstance(edge_or_rel, dict):
        return None
    node = edge_or_rel.get("node")
    return node if isinstance(node, dict) else None


def _value(node: dict[str, Any], field: str) -> Any:
    attr = node.get(field)
    if isinstance(attr, dict):
        return attr.get("value")
    return None


class FabricPoolValidationCheck(InfrahubCheck):
    """Validates role-driven fabric and pod pool assignments."""

    query = "fabric_pool_check"

    async def validate(self, data: dict) -> None:  # type: ignore[override]
        fabric_edges = _edges(data.get("NetworkFabric"))
        if not fabric_edges:
            self.log_info(message="No fabric found")
            return

        has_dci_links = bool(_edges(data.get("NetworkLink")))
        for fabric_edge in fabric_edges:
            fabric = _node(fabric_edge)
            if fabric is None:
                continue
            self._validate_fabric(fabric, has_dci_links=has_dci_links)

        for pod_edge in _edges(data.get("NetworkPod")):
            pod = _node(pod_edge)
            if pod is not None:
                self._validate_pod(pod)

    def _validate_fabric(self, fabric: dict[str, Any], *, has_dci_links: bool) -> None:
        fabric_name = str(_value(fabric, "name") or fabric.get("id") or "unknown")
        pool_roles: dict[str, ResourceRole] = {}

        for pool_edge in _edges(fabric.get("fabric_ip_pools")):
            pool = _node(pool_edge)
            if pool is None:
                continue
            pool_name = self._pool_name(pool)
            typename = pool.get("__typename")
            if typename not in {"CoreIPAddressPool", "CoreIPPrefixPool"}:
                self.log_error(message=f"Fabric {fabric_name}: fabric_ip_pools contains non-IP pool {pool_name}")
                continue

            prefix_roles = self._pool_prefix_roles(pool)
            try:
                pool_roles[pool_name] = resolve_resource_role(prefix_roles, scope="fabric", pool_name=pool_name)
            except PoolRoleResolutionError as exc:
                self.log_error(message=f"Fabric {fabric_name}: {exc}")

        try:
            validate_unique_roles(pool_roles, scope="fabric")
        except PoolRoleResolutionError as exc:
            self.log_error(message=f"Fabric {fabric_name}: {exc}")

        required_roles = fabric_required_roles(
            overlay_routing_protocol=_value(fabric, "overlay_routing_protocol"),
            underlay_routing_protocol=_value(fabric, "underlay_routing_protocol"),
            has_dci_links=has_dci_links,
)
        try:
            missing_roles = missing_fabric_roles(
                required_roles=required_roles, available_roles=set(pool_roles.values())
            )
        except PoolRoleResolutionError as exc:
            self.log_error(message=f"Fabric {fabric_name}: {exc}")
            return

        self._validate_fabric_supernet_capacity(
            fabric_name=fabric_name,
            missing_roles=missing_roles,
            pools_by_role=pool_roles,
            fabric=fabric,
        )

    def _validate_pod(self, pod: dict[str, Any]) -> None:
        pod_name = str(_value(pod, "name") or pod.get("id") or "unknown")
        parent = _node(pod.get("parent"))
        if parent is None:
            self.log_error(message=f"Pod {pod_name}: pod_ip_pools validation requires parent fabric")
            return

        pool_roles: dict[str, ResourceRole] = {}
        pod_role_prefixes: dict[ResourceRole, list[str]] = {}
        for pool_edge in _edges(pod.get("pod_ip_pools")):
            pool = _node(pool_edge)
            if pool is None:
                continue
            pool_name = self._pool_name(pool)
            typename = pool.get("__typename")
            if typename not in {"CoreIPAddressPool", "CoreIPPrefixPool"}:
                self.log_error(message=f"Pod {pod_name}: pod_ip_pools contains non-IP pool {pool_name}")
                continue

            prefix_roles = self._pool_prefix_roles(pool)
            try:
                role = resolve_resource_role(prefix_roles, scope="pod", pool_name=pool_name)
            except PoolRoleResolutionError as exc:
                self.log_error(message=f"Pod {pod_name}: {exc}")
                continue
            if role in {ResourceRole.MLAG, ResourceRole.MLAG_PEERING} and typename != "CoreIPAddressPool":
                self.log_error(message=f"Pod {pod_name}: pool {pool_name} role {role.value} must be CoreIPAddressPool")
                continue
            pool_roles[pool_name] = role
            pod_role_prefixes.setdefault(role, []).extend(str(prefix) for prefix in self._pool_prefixes(pool))

        try:
            validate_unique_roles(pool_roles, scope="pod")
        except PoolRoleResolutionError as exc:
            self.log_error(message=f"Pod {pod_name}: {exc}")

        fabric_role_prefixes = self._role_prefixes(parent, "fabric_ip_pools")
        try:
            validate_pod_pool_containment(
                pod_role_prefixes=pod_role_prefixes,
                fabric_role_prefixes=fabric_role_prefixes,
            )
        except PoolRoleResolutionError as exc:
            self.log_error(message=f"Pod {pod_name}: {exc}")

    @staticmethod
    def _pool_name(pool: dict[str, Any]) -> str:
        name = _value(pool, "name") or pool.get("display_label") or pool.get("id") or "unknown"
        return str(name)

    @staticmethod
    def _pool_prefix_roles(pool: dict[str, Any]) -> list[str | None]:
        roles: list[str | None] = []
        for resource_edge in _edges(pool.get("resources")):
            resource = _node(resource_edge)
            if resource is not None:
                roles.append(_value(resource, "role"))
        return roles

    def _validate_fabric_supernet_capacity(
        self,
        *,
        fabric_name: str,
        missing_roles: set[ResourceRole],
        pools_by_role: dict[str, ResourceRole],
        fabric: dict[str, Any],
    ) -> None:
        missing_prefix_roles = [
            role
            for role in FABRIC_SUPERNET_ALLOCATION_ORDER
            if role in missing_roles and role in FABRIC_SUPERNET_PREFIX_LENGTHS
        ]
        if not missing_prefix_roles:
            return

        supernet_pool = self._pool_for_role(fabric, pools_by_role, ResourceRole.FABRIC_SUPERNET)
        if supernet_pool is None:
            return

        supernets = self._pool_prefixes(supernet_pool)
        used_prefixes = [
            prefix
            for pool_edge in _edges(fabric.get("fabric_ip_pools"))
            if (pool := _node(pool_edge)) is not None
            for prefix in self._pool_prefixes(pool)
            if ResourceRole.FABRIC_SUPERNET not in {role for role in self._pool_roles(pool) if role is not None}
        ]
        allocated = []
        for role in missing_prefix_roles:
            prefix_length = FABRIC_SUPERNET_PREFIX_LENGTHS[role]
            next_prefix = self._next_available_prefix(supernets, used_prefixes + allocated, prefix_length)
            if next_prefix is None:
                pool_name = self._pool_name(supernet_pool)
                self.log_error(
                    message=(
                        f"Fabric {fabric_name}: unable to allocate {role.value} /{prefix_length} "
                        f"from Fabric Supernet pool {pool_name}"
                    )
                )
                return
            allocated.append(next_prefix)

    def _pool_for_role(
        self, fabric: dict[str, Any], pools_by_role: dict[str, ResourceRole], role: ResourceRole
    ) -> dict[str, Any] | None:
        for pool_edge in _edges(fabric.get("fabric_ip_pools")):
            pool = _node(pool_edge)
            if pool is not None and pools_by_role.get(self._pool_name(pool)) is role:
                return pool
        return None

    @classmethod
    def _pool_roles(cls, pool: dict[str, Any]) -> set[ResourceRole | None]:
        return {resolved_role for role in cls._pool_prefix_roles(pool) if (resolved_role := map_prefix_role(role))}

    @classmethod
    def _pool_prefixes(cls, pool: dict[str, Any]) -> list[Any]:
        prefixes = []
        for resource_edge in _edges(pool.get("resources")):
            resource = _node(resource_edge)
            if resource is None:
                continue
            raw_prefix = _value(resource, "prefix")
            if raw_prefix:
                prefixes.append(ip_network(str(raw_prefix)))
        return prefixes

    @classmethod
    def _role_prefixes(cls, owner: dict[str, Any], relationship_name: str) -> dict[ResourceRole, list[str]]:
        role_prefixes: dict[ResourceRole, list[str]] = {}
        for pool_edge in _edges(owner.get(relationship_name)):
            pool = _node(pool_edge)
            if pool is None:
                continue
            roles = {role for role in cls._pool_roles(pool) if role is not None}
            if len(roles) != 1:
                continue
            role = next(iter(roles))
            role_prefixes.setdefault(role, []).extend(str(prefix) for prefix in cls._pool_prefixes(pool))
        return role_prefixes

    @staticmethod
    def _next_available_prefix(supernets: list[Any], used_prefixes: list[Any], prefix_length: int) -> Any | None:
        for supernet in sorted(supernets):
            if prefix_length < supernet.prefixlen:
                continue
            for child in supernet.subnets(new_prefix=prefix_length):
                if not any(child.overlaps(used) for used in used_prefixes):
                    return child
        return None
