from __future__ import annotations

import hashlib
import logging
from ipaddress import IPv4Network, IPv6Network, ip_network
from typing import TYPE_CHECKING, Any, ClassVar, cast

from infrahub_sdk.exceptions import ServerNotResponsiveError
from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from .pool_roles import (
    ALLOCATED_PREFIX_ROLE_VALUES,
    FABRIC_SUPERNET_PREFIX_LENGTHS,
    FABRIC_SUPERNET_ROLE_LABELS,
    ResourceRole,
    map_prefix_role,
    next_available_prefix,
)
from .protocols import DcimDevice, DcimInterface, InterfacePhysical, InterfaceVirtual, RoutingAsn

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

    from infrahub_sdk import InfrahubClient

    from .protocols import LocationRack, NetworkPod

logger = logging.getLogger("infrahub.tasks")

# Every generated network device starts life in provisioning and is enrolled in
# the avd_devices group so the AVD generators pick it up for config generation.
DEVICE_STATUS_PROVISIONING = "provisioning"
AVD_DEVICES_GROUP = "avd_devices"
VTEP_LOOPBACK_ROLES = {"leaf", "border_leaf"}


async def save_file_if_changed(
    *,
    existing_file: Any | None,
    existing_checksum: str | None,
    new_checksum: str,
    new_content: bytes,
    filename: str,
    create_file: Callable[[], Awaitable[Any]],
) -> bool:
    """Upload and save a file node only when the stored content differs."""
    if existing_file is not None and existing_checksum == new_checksum:
        return False

    file_node = existing_file or await create_file()
    file_node.upload_from_bytes(content=new_content, name=filename)
    await file_node.save(allow_upsert=True, update_group_context=False)
    return True


async def fetch_allocated_prefixes(
    client: InfrahubClient, supernets: Sequence[IPv4Network | IPv6Network]
) -> list[IPv4Network | IPv6Network]:
    """Return persisted IPAM prefixes that already sit inside ``supernets``.

    Prefixes carved out of a Fabric Supernet are saved as standalone IpamPrefix
    nodes; they are never pushed back onto the fabric's pool collection. A query
    snapshot of that collection therefore cannot see what an earlier role in this
    run, or an earlier generator in the chain, already allocated. Reading the
    prefixes back from IPAM is what keeps successive carve-outs off each other.
    """
    if not supernets:
        return []

    nodes = await client.filters(kind="IpamPrefix", role__values=list(ALLOCATED_PREFIX_ROLE_VALUES))
    allocated: list[IPv4Network | IPv6Network] = []
    for node in nodes:
        raw_prefix = getattr(getattr(node, "prefix", None), "value", None)
        if not raw_prefix:
            continue
        prefix = ip_network(str(raw_prefix))
        if any(prefix.version == supernet.version and prefix.overlaps(supernet) for supernet in supernets):
            allocated.append(prefix)
    return allocated


async def set_fabric_avd_hostvars_ready(client: InfrahubClient, fabric_id: str, ready: bool) -> None:
    """Set avd_hostvars_ready on a fabric via targeted GraphQL mutation.

    Workaround for SDK bug that serializes `parent: null` on hierarchical nodes.
    """
    await client.execute_graphql(
        query="""
        mutation FabricUpsert($id: String!, $ready: Boolean!) {
            NetworkFabricUpsert(data: { id: $id, avd_hostvars_ready: { value: $ready } }) {
                ok
                object { id }
            }
        }
        """,
        variables={"id": fabric_id, "ready": ready},
    )


class GeneratorMixin:
    client: InfrahubClient

    _DEVICE_RECONCILE_INCLUDE: ClassVar[list[str]] = [
        "asn",
        "index",
        "loopback_ip",
        "member_of_groups",
        "mgmt_ip",
        "node_id",
        "object_template",
        "pod",
        "rack",
        "role",
        "serial",
        "status",
        "vtep_loopback_ip",
    ]

    @staticmethod
    def resolve_device_designs(device_designs: Any) -> dict[str, tuple[str | None, int]]:
        """Map a container's ``device_designs`` relationship to ``{role: (template_id, quantity)}``.

        ``device_designs`` is the relationship object from a generated query
        model (it exposes ``.edges``, each ``.node`` carrying ``role``,
        ``device_quantity``, and a ``device_template`` relationship). A role
        with no design is simply absent from the returned map — see
        ``device_design_for`` for the absence-means-none default. The schema
        uniqueness constraint ``(container, role)`` guarantees at most one design
        per role, so later edges never silently shadow earlier ones in practice.
        """
        resolved: dict[str, tuple[str | None, int]] = {}
        for edge in getattr(device_designs, "edges", None) or []:
            node = edge.node
            template = node.device_template.node
            resolved[node.role.value] = (template.id if template else None, node.device_quantity.value)
        return resolved

    @classmethod
    def device_design_for(cls, device_designs: Any, role: str) -> tuple[str | None, int]:
        """Return ``(template_id, quantity)`` for one role's device design.

        Returns ``(None, 0)`` when the container has no design for ``role``
        (absence-means-none): the generator creates zero devices of that role
        and does not error, replacing the previous ``amount_of_<role>s: 0`` idiom.
        """
        return cls.resolve_device_designs(device_designs).get(role, (None, 0))

    async def assign_mlag_peer_interfaces(
        self,
        device: DcimDevice,
        count: int = 2,
        carvable_roles: frozenset[str] = frozenset({"server", "mlag_peer"}),
    ) -> None:
        """Repurpose the highest-numbered carvable ports as the MLAG peer-link.

        Some standalone-L2LS / campus main-tier switch models ship no dedicated
        ``mlag_peer``-role interfaces; without them PyAVD raises
        ``'mlag_interfaces' not set`` for the pair. Convert the highest-numbered
        ports whose role is in ``carvable_roles`` to role ``mlag_peer`` so the
        pair renders a peer-link.

        Deterministic + idempotent: ports are ordered by the interface's computed
        ``index`` attribute (the same numeric ordering used to build leaf-spine
        interface maps) and the highest ``count`` are chosen, so the choice never
        shifts once a port has been converted (a re-run is a no-op). Highest-index
        ports avoid colliding with server/uplink cabling, which fills the
        lowest-index ports first. Saves use ``update_group_context=False`` so these
        template-owned interfaces are not enrolled in the generator's tracking group
        and are never reset or deleted by the tracking reconciliation on a
        subsequent run.
        """
        interfaces = await self.client.filters(kind=DcimInterface, device__ids=[device.id])
        carvable_ports = [
            iface for iface in interfaces if getattr(iface, "role", None) and iface.role.value in carvable_roles
        ]
        if len(carvable_ports) < count:
            msg = (
                f"{device.name.value}: only {len(carvable_ports)} carvable ports available to "
                f"repurpose as an MLAG peer-link, need {count}"
            )
            raise ValueError(msg)

        # Order by the interface's computed index and take the highest-numbered ports.
        # ``index`` is a read-only computed attribute (present at runtime) that the
        # generated protocol does not type, hence the ignore.
        carvable_ports.sort(key=lambda iface: int(iface.index.value))  # type: ignore[attr-defined]
        for iface in carvable_ports[-count:]:
            if iface.role.value == "mlag_peer":
                continue
            iface.role.value = "mlag_peer"
            await iface.save(allow_upsert=True, update_group_context=False)
            logger.info("Assigned MLAG peer-link role to %s on %s", iface.name.value, device.name.value)

    def calculate_checksum(self) -> str:
        """Calculates a checksum of the generator based on the related ids during the session"""

        related_ids = self.client.group_context.related_group_ids + self.client.group_context.related_node_ids
        sorted_ids = sorted(related_ids)
        joined = ",".join(sorted_ids)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    async def resolve_avd_pools(
        self, node: Any, pod_node: Any | None = None
    ) -> tuple[
        CoreNumberPool | None,
        CoreNumberPool | None,
        CoreIPAddressPool | None,
        CoreIPAddressPool | None,
        CoreIPAddressPool | None,
    ]:
        """Resolve the (asn, node_id, mgmt, loopback, vtep) AVD pools referenced by a fabric node.

        The fabric/pod/rack generators all read common pools off the fabric.
        When a pod node is supplied, pod-scoped loopback and VTEP prefix pools
        take precedence over matching fabric pools.
        """
        asn_pool: CoreNumberPool | None = None
        node_id_pool: CoreNumberPool | None = None
        mgmt_pool: CoreIPAddressPool | None = None
        loopback_pool: CoreIPAddressPool | None = None
        vtep_loopback_pool: CoreIPAddressPool | None = None

        asn_rel = getattr(node, "asn_pool", None)
        if asn_rel and asn_rel.node:
            asn_pool = await self.client.get(kind=CoreNumberPool, id=asn_rel.node.id)  # type: ignore[type-abstract]

        node_id_rel = getattr(node, "node_id_pool", None)
        if node_id_rel and node_id_rel.node:
            node_id_pool = await self.client.get(kind=CoreNumberPool, id=node_id_rel.node.id)  # type: ignore[type-abstract]

        mgmt_rel = getattr(node, "mgmt_pool", None)
        fabric_pool_refs = self._pool_refs_by_role(getattr(node, "fabric_ip_pools", None))
        pod_pool_refs = self._pool_refs_by_role(getattr(pod_node, "pod_ip_pools", None))
        mgmt_ref = fabric_pool_refs.get(ResourceRole.MANAGEMENT)
        mgmt_ref_id = getattr(mgmt_ref, "id", None)
        if mgmt_ref_id:
            mgmt_pool = await self.client.get(kind=CoreIPAddressPool, id=mgmt_ref_id)  # type: ignore[type-abstract]
        elif mgmt_rel and mgmt_rel.node:
            mgmt_pool = await self.client.get(kind=CoreIPAddressPool, id=mgmt_rel.node.id)  # type: ignore[type-abstract]

        fabric_name = getattr(getattr(node, "name", None), "value", None)
        pod_name = getattr(getattr(pod_node, "name", None), "value", None)
        loopback_ref = pod_pool_refs.get(ResourceRole.LOOPBACK) or fabric_pool_refs.get(ResourceRole.LOOPBACK)
        loopback_rel = getattr(node, "loopback_pool", None)
        if fabric_name and loopback_ref is None and not (loopback_rel and loopback_rel.node):
            loopback_ref = await self._ensure_fabric_supernet_fallback_pool(
                fabric_name=str(fabric_name),
                role=ResourceRole.LOOPBACK,
                fabric_pool_refs=fabric_pool_refs,
            )
        if fabric_name and loopback_ref is not None:
            loopback_pool = await self._ensure_address_pool_from_prefix_pool(
                fabric_name=self._address_pool_scope(
                    prefix_pool_ref=loopback_ref,
                    pod_pool_refs=pod_pool_refs,
                    fabric_name=fabric_name,
                    pod_name=pod_name,
                ),
                pool_role="loopback",
                prefix_pool_ref=loopback_ref,
            )
        elif fabric_name and loopback_rel and loopback_rel.node:
            loopback_pool = await self._ensure_address_pool_from_prefix_pool(
                fabric_name=str(fabric_name).lower(),
                pool_role="loopback",
                prefix_pool_ref=loopback_rel.node,
            )

        vtep_ref = pod_pool_refs.get(ResourceRole.LOOPBACK_VTEP) or fabric_pool_refs.get(ResourceRole.LOOPBACK_VTEP)
        vtep_rel = getattr(node, "vtep_pool", None)
        if fabric_name and vtep_ref is None and not (vtep_rel and vtep_rel.node):
            vtep_ref = await self._ensure_fabric_supernet_fallback_pool(
                fabric_name=str(fabric_name),
                role=ResourceRole.LOOPBACK_VTEP,
                fabric_pool_refs=fabric_pool_refs | ({ResourceRole.LOOPBACK: loopback_ref} if loopback_ref else {}),
            )
        if fabric_name and vtep_ref is not None:
            vtep_loopback_pool = await self._ensure_address_pool_from_prefix_pool(
                fabric_name=self._address_pool_scope(
                    prefix_pool_ref=vtep_ref,
                    pod_pool_refs=pod_pool_refs,
                    fabric_name=fabric_name,
                    pod_name=pod_name,
                ),
                pool_role="vtep-loopback",
                prefix_pool_ref=vtep_ref,
            )
        elif fabric_name and vtep_rel and vtep_rel.node:
            vtep_loopback_pool = await self._ensure_address_pool_from_prefix_pool(
                fabric_name=str(fabric_name).lower(),
                pool_role="vtep-loopback",
                prefix_pool_ref=vtep_rel.node,
            )

        return asn_pool, node_id_pool, mgmt_pool, loopback_pool, vtep_loopback_pool

    @staticmethod
    def _address_pool_scope(
        *,
        prefix_pool_ref: object,
        pod_pool_refs: dict[ResourceRole, object],
        fabric_name: object,
        pod_name: object,
    ) -> str:
        """Name the wrapper address pool after the scope that owns its prefix pool.

        A fabric-level prefix pool has to keep a fabric-level wrapper: naming it
        after the pod would mint one wrapper per pod around the same prefixes and
        make a device's pool identity depend on which generator got there first.
        """
        if pod_name and any(pool_ref is prefix_pool_ref for pool_ref in pod_pool_refs.values()):
            return str(pod_name).lower()
        return str(fabric_name).lower()

    async def _ensure_vtep_loopback_address_pool(
        self, *, fabric_name: str, vtep_prefix_pool_ref: object
    ) -> CoreIPAddressPool:
        """Create or update the address pool used for Infrahub-owned VTEP IP allocation."""
        return await self._ensure_address_pool_from_prefix_pool(
            fabric_name=fabric_name,
            pool_role="vtep-loopback",
            prefix_pool_ref=vtep_prefix_pool_ref,
        )

    async def _ensure_address_pool_from_prefix_pool(
        self, *, fabric_name: str, pool_role: str, prefix_pool_ref: object
    ) -> CoreIPAddressPool:
        """Create or update an address pool wrapper around fabric prefix-pool resources."""
        prefix_ids = await self._prefix_resource_ids(prefix_pool_ref)
        if not prefix_ids:
            msg = f"Fabric '{fabric_name}': {pool_role} pool has no prefix resources for IP address allocation"
            raise ValueError(msg)

        address_pool = await self.client.create(
            kind=CoreIPAddressPool,
            name=f"{fabric_name}-{pool_role}-address-pool",
            default_address_type="IpamIPAddress",
            default_prefix_length=32,
            ip_namespace={"hfid": ["default"]},
            resources=[{"id": prefix_id} for prefix_id in prefix_ids],
        )
        await address_pool.save(allow_upsert=True, update_group_context=False)
        return address_pool

    async def _ensure_fabric_supernet_fallback_pool(
        self,
        *,
        fabric_name: str,
        role: ResourceRole,
        fabric_pool_refs: dict[ResourceRole, object],
    ) -> CoreIPPrefixPool | None:
        """Create or reuse a deterministic prefix pool carved from the Fabric Supernet."""
        if role not in FABRIC_SUPERNET_PREFIX_LENGTHS:
            return None

        supernet_ref = fabric_pool_refs.get(ResourceRole.FABRIC_SUPERNET)
        if supernet_ref is None:
            return None

        pool_name = f"{fabric_name}-{FABRIC_SUPERNET_ROLE_LABELS[role]}-Pool"
        existing = await self._existing_prefix_pool_by_name(pool_name)
        if existing is not None:
            return existing

        supernet_pool = await self._hydrated_prefix_pool(supernet_ref)
        prefix_length = FABRIC_SUPERNET_PREFIX_LENGTHS[role]
        reserved_prefixes = self._fabric_supernet_reserved_prefixes()
        child_prefix = await self._next_fabric_supernet_child_prefix(
            fabric_name=fabric_name,
            role=role,
            prefix_length=prefix_length,
            supernet_pool=supernet_pool,
            fabric_pool_refs=fabric_pool_refs,
            reserved_prefixes=reserved_prefixes,
        )
        reserved_prefixes.append(child_prefix)

        prefix = await self.client.create(
            kind="IpamPrefix",
            prefix=str(child_prefix),
            role=role.value,
            ip_namespace={"hfid": ["default"]},
        )
        await prefix.save(allow_upsert=True, update_group_context=False)

        prefix_pool = await self.client.create(
            CoreIPPrefixPool,  # type: ignore[type-abstract]
            name=pool_name,
            default_prefix_type="IpamPrefix",
            default_prefix_length=prefix_length,
            ip_namespace={"hfid": ["default"]},
            resources=[{"id": prefix.id}],
        )
        await prefix_pool.save(allow_upsert=True, update_group_context=False)
        pool_id = getattr(prefix_pool, "id", None)
        prefix_id = getattr(prefix, "id", None)
        if pool_id and prefix_id:
            self._generated_prefix_pool_resource_ids()[str(pool_id)] = [str(prefix_id)]
        return prefix_pool

    async def _existing_prefix_pool_by_name(self, pool_name: str) -> CoreIPPrefixPool | None:
        matches = await self.client.filters(CoreIPPrefixPool, name__value=pool_name)  # type: ignore[type-abstract]
        if not matches:
            return None

        if self._resource_ids(getattr(matches[0], "resources", None)):
            return cast("CoreIPPrefixPool", matches[0])

        pool_id = getattr(matches[0], "id", None)
        if not pool_id:
            return cast("CoreIPPrefixPool", matches[0])
        return await self.client.get(CoreIPPrefixPool, id=pool_id, include=["resources"])  # type: ignore[type-abstract]

    async def _hydrated_prefix_pool(self, pool_ref: object) -> CoreIPPrefixPool:
        if self._resource_prefixes(getattr(pool_ref, "resources", None)):
            return cast("CoreIPPrefixPool", pool_ref)

        pool_id = getattr(pool_ref, "id", None)
        if not pool_id:
            msg = "Fabric Supernet pool reference has no id and no prefetched prefix resources"
            raise ValueError(msg)
        hydrated_pools = self._hydrated_prefix_pools()
        if str(pool_id) not in hydrated_pools:
            hydrated_pools[str(pool_id)] = await self.client.get(  # type: ignore[type-abstract]
                CoreIPPrefixPool, id=pool_id, include=["resources"]
            )
        return hydrated_pools[str(pool_id)]

    async def _next_fabric_supernet_child_prefix(
        self,
        *,
        fabric_name: str,
        role: ResourceRole,
        prefix_length: int,
        supernet_pool: object,
        fabric_pool_refs: dict[ResourceRole, object],
        reserved_prefixes: list[Any],
    ) -> Any:
        supernets = self._resource_prefixes(getattr(supernet_pool, "resources", None))
        if not supernets:
            msg = f"Fabric '{fabric_name}': Fabric Supernet pool has no prefix resources"
            raise ValueError(msg)

        # The supernet is the container being carved, so its own prefix is never
        # "used" — only the allocations sitting inside it are.
        used_prefixes = [
            prefix
            for pool_ref in fabric_pool_refs.values()
            for prefix in self._resource_prefixes(getattr(pool_ref, "resources", None), include_supernets=False)
        ]
        used_prefixes.extend(reserved_prefixes)
        # Pools carved by an earlier role, or by an earlier generator in the
        # chain, are not attached to fabric_ip_pools and so are invisible in the
        # query snapshot above.
        used_prefixes.extend(await fetch_allocated_prefixes(self.client, supernets))

        child = next_available_prefix(supernets, used_prefixes, prefix_length)
        if child is not None:
            return child

        supernet_name = getattr(getattr(supernet_pool, "name", None), "value", None) or getattr(
            supernet_pool, "id", "unknown"
        )
        msg = (
            f"Fabric '{fabric_name}': unable to allocate {role.value} /{prefix_length} "
            f"from Fabric Supernet pool {supernet_name}"
        )
        raise ValueError(msg)

    def _fabric_supernet_reserved_prefixes(self) -> list[Any]:
        reserved = getattr(self, "_fabric_supernet_reserved", None)
        if reserved is None:
            reserved = []
            self._fabric_supernet_reserved = reserved
        return reserved

    def _generated_prefix_pool_resource_ids(self) -> dict[str, list[str]]:
        resource_ids = getattr(self, "_generated_prefix_pool_resources", None)
        if resource_ids is None:
            resource_ids = {}
            self._generated_prefix_pool_resources = resource_ids
        return resource_ids

    def _hydrated_prefix_pools(self) -> dict[str, CoreIPPrefixPool]:
        hydrated_pools = getattr(self, "_hydrated_prefix_pool_cache", None)
        if hydrated_pools is None:
            hydrated_pools = {}
            self._hydrated_prefix_pool_cache = hydrated_pools
        return hydrated_pools

    async def _prefix_resource_ids(self, prefix_pool_ref: object) -> list[str]:
        resources = getattr(prefix_pool_ref, "resources", None)
        prefix_ids = self._resource_ids(resources)
        if prefix_ids:
            return prefix_ids

        prefix_pool_id = getattr(prefix_pool_ref, "id", None)
        if not prefix_pool_id:
            return []

        generated_resource_ids = self._generated_prefix_pool_resource_ids().get(str(prefix_pool_id))
        if generated_resource_ids is not None:
            return generated_resource_ids

        prefix_pool = await self.client.get(  # type: ignore[type-abstract]
            CoreIPPrefixPool,
            id=prefix_pool_id,
            include=["resources"],
        )
        return self._resource_ids(getattr(prefix_pool, "resources", None))

    @staticmethod
    def _resource_ids(resources: object) -> list[str]:
        if resources is None:
            return []

        edges = getattr(resources, "edges", None)
        if edges:
            return [
                node.id
                for edge in edges
                if (node := getattr(edge, "node", None)) is not None and getattr(node, "id", None)
            ]

        peers = getattr(resources, "peers", None)
        if peers:
            prefix_ids: list[str] = []
            for peer_ref in peers:
                peer = getattr(peer_ref, "peer", None) or getattr(peer_ref, "node", None) or peer_ref
                if getattr(peer, "id", None):
                    prefix_ids.append(peer.id)
            return prefix_ids

        return []

    @staticmethod
    def _resource_prefixes(resources: object, *, include_supernets: bool = True) -> list[IPv4Network | IPv6Network]:
        prefixes: list[IPv4Network | IPv6Network] = []
        for resource in GeneratorMixin._relationship_nodes(resources):
            role = map_prefix_role(GeneratorMixin._pool_attr_value(resource, "role"))
            if not include_supernets and role is ResourceRole.FABRIC_SUPERNET:
                continue
            raw_prefix = getattr(getattr(resource, "prefix", None), "value", None)
            if isinstance(raw_prefix, str):
                prefixes.append(ip_network(raw_prefix))
            elif raw_prefix is not None:
                prefixes.append(ip_network(str(raw_prefix)))
        return prefixes

    @classmethod
    def _pool_refs_by_role(cls, pool_relationship: object) -> dict[ResourceRole, object]:
        """Resolve role-tagged pool collection members from prefetched resources."""
        pools_by_role: dict[ResourceRole, object] = {}
        for pool_ref in cls._relationship_nodes(pool_relationship):
            resources = (
                pool_ref.get("resources") if isinstance(pool_ref, dict) else getattr(pool_ref, "resources", None)
            )
            roles = {
                role
                for resource in cls._relationship_nodes(resources)
                if (role := map_prefix_role(GeneratorMixin._pool_attr_value(resource, "role"))) is not None
            }
            if len(roles) == 1:
                pools_by_role[next(iter(roles))] = pool_ref
                continue
            # A pool that does not resolve to exactly one role is indistinguishable
            # from an absent pool here, and the generator would silently carve a
            # replacement out of the Fabric Supernet instead. Say so, because the
            # generator can run ahead of the check that reports it properly.
            pool_id = pool_ref.get("id") if isinstance(pool_ref, dict) else getattr(pool_ref, "id", None)
            pool_name = cls._pool_attr_value(pool_ref, "name") or pool_id or "unknown"
            logger.warning(
                "Ignoring pool %s: backing prefixes resolve to %s roles (%s), expected exactly one",
                pool_name,
                len(roles),
                ", ".join(sorted(role.value for role in roles)) or "none",
            )
        return pools_by_role

    @staticmethod
    def _relationship_nodes(relationship: object) -> list[object]:
        if relationship is None:
            return []

        edges = relationship.get("edges") if isinstance(relationship, dict) else getattr(relationship, "edges", None)
        if edges:
            edge_nodes: list[object] = []
            for edge in edges:
                node = edge.get("node") if isinstance(edge, dict) else getattr(edge, "node", None)
                if node is not None:
                    edge_nodes.append(node)
            return edge_nodes

        peers = relationship.get("peers") if isinstance(relationship, dict) else getattr(relationship, "peers", None)
        if peers:
            peer_nodes: list[object] = []
            for peer_ref in peers:
                peer = getattr(peer_ref, "peer", None) or getattr(peer_ref, "node", None) or peer_ref
                if peer is not None:
                    peer_nodes.append(peer)
            return peer_nodes

        return []

    @staticmethod
    def _pool_attr_value(obj: object, name: str) -> str | None:
        attr = getattr(obj, name, None)
        if attr is not None and hasattr(attr, "value"):
            value = attr.value
            return str(value) if value is not None else None
        if isinstance(obj, dict):
            raw = obj.get(name)
            if isinstance(raw, dict):
                value = raw.get("value")
                return str(value) if value is not None else None
        return None

    async def create_avd_device(
        self,
        *,
        name: str,
        role: str,
        object_template_id: str,
        pod_id: str,
        fabric_id: str,
        rack_id: str | None = None,
        index: int | None = None,
        loopback_pool: CoreIPAddressPool | None = None,
        vtep_loopback_pool: CoreIPAddressPool | None = None,
        asn_pool: CoreNumberPool | None = None,
        node_id_pool: CoreNumberPool | None = None,
        mgmt_pool: CoreIPAddressPool | None = None,
    ) -> DcimDevice:
        """Create an AVD-managed network device, allocating from the given pools.

        Centralises the device-creation pattern shared by the fabric, pod and
        rack generators: assemble the common kwargs, allocate from whichever of
        the node-id / management / loopback pools are supplied, save, and (when a
        loopback pool was given) activate the loopback interface.

        The BGP ASN is modelled as a first-class ``Routing.Asn`` node owned by
        the fabric. When an ASN pool is supplied the device is linked to a
        ``RoutingAsn`` allocated from it (see ``_ensure_device_asn``).

        Returns the created device.
        """
        existing_devices = await self.client.filters(DcimDevice, name__value=name)
        device_existed = bool(existing_devices)
        existing_device = await self._fetch_existing_avd_device(existing_devices[0].id) if device_existed else None

        device_kwargs, decisions = self._build_avd_device_payload(
            name=name,
            role=role,
            object_template_id=object_template_id,
            pod_id=pod_id,
            rack_id=rack_id,
            index=index,
            loopback_pool=loopback_pool,
            vtep_loopback_pool=vtep_loopback_pool,
            node_id_pool=node_id_pool,
            mgmt_pool=mgmt_pool,
            existing_device=existing_device,
        )
        self._log_device_field_decisions(name, decisions)

        device = await self.client.create(DcimDevice, **device_kwargs)  # type: ignore[type-abstract]
        await device.save(allow_upsert=True)
        await self._reconcile_physical_interfaces_from_template(device.id, object_template_id)

        created_asn: RoutingAsn | None = None
        try:
            if asn_pool is not None:
                created_asn = await self._ensure_device_asn(device.id, asn_pool, fabric_id)

            if loopback_pool is not None:
                await self._reconcile_generated_loopback_interfaces(device.id, role)
        except Exception:
            if not device_existed:
                try:
                    await device.delete()
                except Exception:
                    logger.exception("Failed to clean up partially-created device %s after generator error", name)
                if created_asn is not None:
                    try:
                        await created_asn.delete()
                    except Exception:
                        logger.exception(
                            "Failed to clean up RoutingAsn %s after rolling back device %s",
                            created_asn.id,
                            name,
                        )
            raise

        return device

    async def _fetch_existing_avd_device(self, device_id: str) -> DcimDevice:
        return await self.client.get(  # type: ignore[type-abstract]
            DcimDevice,
            id=device_id,
            include=self._DEVICE_RECONCILE_INCLUDE,
        )

    def _build_avd_device_payload(
        self,
        *,
        name: str,
        role: str,
        object_template_id: str,
        pod_id: str,
        rack_id: str | None,
        index: int | None,
        loopback_pool: CoreIPAddressPool | None,
        vtep_loopback_pool: CoreIPAddressPool | None,
        node_id_pool: CoreNumberPool | None,
        mgmt_pool: CoreIPAddressPool | None,
        existing_device: DcimDevice | None,
    ) -> tuple[dict[str, Any], dict[str, list[str]]]:
        decisions: dict[str, list[str]] = {"populated": [], "preserved": [], "skipped": []}
        payload: dict[str, Any] = {"name": name}

        if existing_device is not None and self._has_non_empty_value(getattr(existing_device, "serial", None)):
            decisions["preserved"].append("serial")

        self._add_attribute_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="status",
            value=DEVICE_STATUS_PROVISIONING,
            include_preserved=True,
        )
        self._add_attribute_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="role",
            value=role,
            include_preserved=True,
        )
        self._add_attribute_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="index",
            value=index,
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="object_template",
            value={"id": object_template_id},
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="pod",
            value={"id": pod_id},
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="rack",
            value={"id": rack_id} if rack_id is not None else None,
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="loopback_ip",
            value=loopback_pool,
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="vtep_loopback_ip",
            value=vtep_loopback_pool if role in VTEP_LOOPBACK_ROLES else None,
        )
        self._add_attribute_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="node_id",
            value=node_id_pool,
        )
        self._add_relationship_if_missing(
            payload,
            decisions,
            existing_device=existing_device,
            field_name="mgmt_ip",
            value=mgmt_pool,
        )
        self._add_avd_group_membership(payload, decisions, existing_device)

        return payload, decisions

    def _add_attribute_if_missing(
        self,
        payload: dict[str, Any],
        decisions: dict[str, list[str]],
        *,
        existing_device: DcimDevice | None,
        field_name: str,
        value: object,
        include_preserved: bool = False,
    ) -> None:
        existing_attribute = getattr(existing_device, field_name, None) if existing_device is not None else None
        if existing_device is not None and self._has_non_empty_value(existing_attribute):
            if include_preserved:
                payload[field_name] = getattr(existing_attribute, "value", existing_attribute)
            decisions["preserved"].append(field_name)
            return
        if value is None:
            decisions["skipped"].append(field_name)
            return
        payload[field_name] = value
        decisions["populated"].append(field_name)

    def _add_relationship_if_missing(
        self,
        payload: dict[str, Any],
        decisions: dict[str, list[str]],
        *,
        existing_device: DcimDevice | None,
        field_name: str,
        value: object,
    ) -> None:
        if existing_device is not None and self._relationship_node_id(getattr(existing_device, field_name, None)):
            decisions["preserved"].append(field_name)
            return
        if value is None:
            decisions["skipped"].append(field_name)
            return
        payload[field_name] = value
        decisions["populated"].append(field_name)

    def _add_avd_group_membership(
        self,
        payload: dict[str, Any],
        decisions: dict[str, list[str]],
        existing_device: DcimDevice | None,
    ) -> None:
        if existing_device is None:
            payload["member_of_groups"] = [AVD_DEVICES_GROUP]
            decisions["populated"].append("member_of_groups")
            return

        existing_groups = self._relationship_peer_refs(getattr(existing_device, "member_of_groups", None))
        has_avd_group = any(
            group_ref.get("id") == AVD_DEVICES_GROUP or group_ref.get("name") == AVD_DEVICES_GROUP
            for group_ref in existing_groups
        )
        if has_avd_group:
            decisions["preserved"].append("member_of_groups")
            return

        payload["member_of_groups"] = [
            {"id": group_ref["id"]} if "id" in group_ref else group_ref["name"] for group_ref in existing_groups
        ]
        payload["member_of_groups"].append(AVD_DEVICES_GROUP)
        decisions["populated"].append("member_of_groups")

    def _log_device_field_decisions(self, name: str, decisions: dict[str, list[str]]) -> None:
        log = getattr(self, "logger", logger)
        for decision, fields in decisions.items():
            if fields:
                log.info("Device %s: %s fields %s", name, decision, ", ".join(sorted(fields)))

    async def _reconcile_physical_interfaces_from_template(self, device_id: str, object_template_id: str) -> None:
        """Create missing physical interfaces for devices whose template was applied by upsert.

        Infrahub expands template interfaces when a device is created from a template, but a
        pre-seeded device may receive its object_template later through generator upsert. In
        that case, copy only missing physical interfaces and leave existing manual interfaces
        untouched.
        """
        template_interfaces = await self.client.filters(
            kind="TemplateInterfacePhysical",
            device__ids=[object_template_id],
        )
        if not template_interfaces:
            return

        existing_interfaces = await self.client.filters(
            DcimInterface,  # type: ignore[type-abstract]
            device__ids=[device_id],
        )
        existing_names = {
            name
            for interface in existing_interfaces
            if (name := self._attribute_value(getattr(interface, "name", None)))
        }

        for template_interface in template_interfaces:
            name = self._attribute_value(getattr(template_interface, "name", None))
            if not name or name in existing_names:
                continue

            interface_kwargs: dict[str, Any] = {
                "name": name,
                "device": {"id": device_id},
            }
            for field_name in ("status", "role", "mtu", "description", "l2_mode", "dot1q_id", "mac_address", "index"):
                value = self._attribute_value(getattr(template_interface, field_name, None))
                if value not in (None, ""):
                    interface_kwargs[field_name] = value

            interface = await self.client.create(InterfacePhysical, **interface_kwargs)  # type: ignore[type-abstract]
            await interface.save(allow_upsert=True)
            existing_names.add(name)

    @staticmethod
    def _has_non_empty_value(attribute: object) -> bool:
        if attribute is None:
            return False
        value = getattr(attribute, "value", attribute)
        if value is None:
            return False
        return not (isinstance(value, str) and not value)

    @staticmethod
    def _attribute_value(attribute: object) -> object:
        if attribute is None:
            return None
        return getattr(attribute, "value", attribute)

    @staticmethod
    def _relationship_peer_refs(relationship: object) -> list[dict[str, str]]:
        peers = getattr(relationship, "peers", None)
        if not peers:
            return []

        refs: list[dict[str, str]] = []
        for peer_ref in peers:
            peer = getattr(peer_ref, "peer", None) or getattr(peer_ref, "node", None) or peer_ref
            peer_id = getattr(peer, "id", None)
            if isinstance(peer_id, str) and peer_id:
                refs.append({"id": peer_id})
                continue
            peer_name = getattr(getattr(peer, "name", None), "value", None)
            if isinstance(peer_name, str) and peer_name:
                refs.append({"name": peer_name})
        return refs

    async def allocate_routing_asn(self, asn_pool: CoreNumberPool, fabric_id: str) -> RoutingAsn:
        """Allocate a BGP ASN from ``asn_pool`` as a first-class ``Routing.Asn`` node.

        The ASN ``CoreNumberPool`` is bound to ``RoutingAsn.asn``, so creating a
        ``RoutingAsn`` with ``asn=<pool>`` draws the next free number from the
        fabric's range. Ownership is recorded via the ``fabric`` relationship
        (FR-003). The allocated value is not populated on the object returned by
        ``create()`` + ``save()`` (as with pool-backed IP allocations), but the
        node id is — which is all the caller needs to wire the ``asn``
        relationship. Callers are responsible for idempotency (reusing an
        already-linked node) — this helper always allocates a new one.

        The node is saved with ``update_group_context=False`` so it is not
        enrolled in the generator's tracking group: a ``RoutingAsn`` that is no
        longer referenced is retained rather than cleaned up (FR-009), and a
        re-run that reuses an existing ASN never risks the tracking cleanup
        deleting an in-use node.

        This is a plain create (no ``allow_upsert``): ``asn`` is both
        pool-sourced and the node's human-friendly id, so an upsert cannot
        resolve the HFID before the pool assigns a value. Idempotency is the
        caller's responsibility — reuse an already-linked node instead of
        allocating again.
        """
        routing_asn = await self.client.create(  # type: ignore[type-abstract]
            RoutingAsn,
            asn=asn_pool,
            fabric={"id": fabric_id},
        )
        await routing_asn.save(update_group_context=False)
        return routing_asn

    async def _ensure_device_asn(self, device_id: str, asn_pool: CoreNumberPool, fabric_id: str) -> RoutingAsn | None:
        """Link a device to a fabric-owned ``RoutingAsn`` (unique per device), idempotently.

        Re-runs must not allocate a fresh AS number: ``RoutingAsn`` is keyed only
        by its (pool-allocated) value, so the device's existing ``asn`` link is
        the stable idempotency anchor. If the device is already linked, reuse it
        and return ``None``; otherwise allocate a new ``RoutingAsn`` from the pool,
        attach it, and return it so callers can roll back later failures.
        """
        device = await self.client.get(  # type: ignore[type-abstract]
            DcimDevice,
            id=device_id,
            include=["asn"],
            exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
        )
        if device.asn.id:  # type: ignore[attr-defined]
            return None

        routing_asn = await self.allocate_routing_asn(asn_pool, fabric_id)
        device.asn = routing_asn.id  # type: ignore[assignment, attr-defined]
        try:
            await device.save(allow_upsert=True)
        except Exception:
            try:
                await routing_asn.delete()
            except Exception:
                logger.exception(
                    "Failed to clean up unlinked RoutingAsn %s after device ASN link error", routing_asn.id
                )
            raise
        return routing_asn

    async def _set_device_asn(self, device_id: str, routing_asn_id: str) -> None:
        """Link DcimDevice.asn to a RoutingAsn without resaving the SDK object's relationships."""
        await self.client.execute_graphql(
            query="""
            mutation SetDeviceAsn($id: String!, $asn_id: String!) {
                DcimDeviceUpsert(data: { id: $id, asn: { id: $asn_id } }) {
                    ok
                    object { id }
                }
            }
            """,
            variables={"id": device_id, "asn_id": routing_asn_id},
        )

    async def _device_vtep_loopback_ip_id(self, device_id: str) -> str | None:
        """Return the linked VTEP loopback IP node id for a device."""
        device = await self.client.get(
            DcimDevice,  # type: ignore[type-abstract]
            id=device_id,
            include=["vtep_loopback_ip"],
            exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
        )
        return self._relationship_node_id(getattr(device, "vtep_loopback_ip", None))

    async def _set_device_vtep_loopback_ip(self, device_id: str, ip_address_id: str) -> None:
        """Link DcimDevice.vtep_loopback_ip to an existing IpamIPAddress by id."""
        await self.client.execute_graphql(
            query="""
            mutation SetDeviceVtepLoopbackIp($id: String!, $ip_address_id: String!) {
                DcimDeviceUpsert(data: { id: $id, vtep_loopback_ip: { id: $ip_address_id } }) {
                    ok
                    object { id }
                }
            }
            """,
            variables={"id": device_id, "ip_address_id": ip_address_id},
        )

    async def ensure_shared_device_asn(
        self, devices: list[DcimDevice], asn_pool: CoreNumberPool, fabric_id: str
    ) -> RoutingAsn | None:
        """Link all devices to one shared fabric-owned ``RoutingAsn``.

        The first existing ASN found in the supplied device order is the
        idempotency anchor. If none of the devices has an ASN yet, allocate one
        from the fabric pool and link every device to it. Existing non-selected
        ASN nodes are intentionally left in place; only the device links are
        reconciled.
        """
        if not devices:
            return None

        device_ids = [device.id for device in devices]
        fetched_devices = [
            await self.client.get(  # type: ignore[type-abstract]
                DcimDevice,
                id=device_id,
                include=["asn"],
                exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
            )
            for device_id in device_ids
        ]

        shared_asn_id = next(
            (
                cast("str", fetched_device.asn.id)  # type: ignore[attr-defined]
                for fetched_device in fetched_devices
                if getattr(getattr(fetched_device, "asn", None), "id", None)
            ),
            None,
        )

        routing_asn: RoutingAsn | None = None
        if shared_asn_id is None:
            routing_asn = await self.allocate_routing_asn(asn_pool, fabric_id)
            shared_asn_id = routing_asn.id

        try:
            for fetched_device in fetched_devices:
                if getattr(getattr(fetched_device, "asn", None), "id", None) == shared_asn_id:
                    continue
                await self._set_device_asn(fetched_device.id, shared_asn_id)
        except Exception:
            if routing_asn is not None:
                try:
                    await routing_asn.delete()
                except Exception:
                    logger.exception(
                        "Failed to clean up shared RoutingAsn %s after device ASN link error", routing_asn.id
                    )
            raise

        return routing_asn

    async def _reconcile_generated_loopback_interfaces(self, device_id: str, role: str) -> None:
        """Ensure generated loopback interfaces are virtual and bound to device IPs.

        The IP assigned from a CoreIPAddressPool is not populated on the node
        returned by ``create()`` + ``save()`` (the relationship id only resolves
        on a subsequent read), so the device is re-fetched by id before wiring
        Loopback0 and, for VTEP-capable roles, Loopback1.
        """
        device = await self.client.get(
            DcimDevice,  # type: ignore[type-abstract]
            id=device_id,
            include=["loopback_ip", "vtep_loopback_ip"],
            exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
        )

        await self._ensure_virtual_loopback_interface(
            device_id=device_id,
            name="Loopback0",
            role="loopback",
            ip_address_id=self._relationship_node_id(getattr(device, "loopback_ip", None)),
        )
        if role in VTEP_LOOPBACK_ROLES:
            await self._ensure_virtual_loopback_interface(
                device_id=device_id,
                name="Loopback1",
                role="vtep_loopback",
                ip_address_id=self._relationship_node_id(getattr(device, "vtep_loopback_ip", None)),
            )

    async def _ensure_virtual_loopback_interface(
        self, *, device_id: str, name: str, role: str, ip_address_id: str | None
    ) -> None:
        existing = await self.client.filters(
            DcimInterface,  # type: ignore[type-abstract]
            device__ids=[device_id],
            name__value=name,
        )
        for interface in existing:
            if self._node_kind(interface) == "InterfacePhysical":
                await interface.delete()

        interface = await self.client.create(
            InterfaceVirtual,  # type: ignore[type-abstract]
            name=name,
            role=role,
            status="active",
            device={"id": device_id},
        )
        if ip_address_id:
            interface.ip_address = ip_address_id  # type: ignore[assignment, attr-defined]
        await interface.save(allow_upsert=True)

    @staticmethod
    def _relationship_node_id(relationship: object) -> str | None:
        if relationship is None:
            return None
        relationship_id = getattr(relationship, "id", None)
        if isinstance(relationship_id, str) and relationship_id:
            return relationship_id
        node = getattr(relationship, "node", None)
        node_id = getattr(node, "id", None)
        if isinstance(node_id, str) and node_id:
            return node_id
        return None

    @staticmethod
    def _node_kind(node: object) -> str | None:
        get_kind = getattr(node, "get_kind", None)
        if get_kind:
            return get_kind()
        return getattr(node, "__typename", None) or getattr(node, "typename__", None)


async def check_all_racks_generated(client: InfrahubClient, fabric_id: str) -> bool:
    """Check if all racks across all non-fabric pods have generation_complete set to True."""
    pods = await client.filters(kind="NetworkPod", parent__ids=[fabric_id])

    for pod_node in pods:
        pod = cast("NetworkPod", pod_node)
        if hasattr(pod, "role") and pod.role.value == "fabric":
            continue

        racks = await client.filters(kind="LocationRack", pod__ids=[pod.id])
        if not racks:
            continue

        for rack_node in racks:
            rack = cast("LocationRack", rack_node)
            if not rack.generation_complete.value:
                logger.info(f"Rack {rack.name.value} not yet generated, waiting...")
                return False

    logger.info("All racks generated for fabric %s", fabric_id)
    return True


async def _trigger_generator(
    client: InfrahubClient,
    name: str,
    node_ids: list[str] | None = None,
    *,
    timeout: int | None = None,  # noqa: ASYNC109 - forwards the SDK GraphQL timeout option
    tolerate_timeout: bool = False,
) -> None:
    """Trigger a generator by name via CoreGeneratorDefinition mutation."""
    if node_ids is None:
        logger.warning("Skipping %s trigger: target node IDs are required", name)
        return
    if not node_ids:
        logger.warning("Skipping %s trigger: no target node IDs found", name)
        return

    generator_defs = await client.filters(kind="CoreGeneratorDefinition", name__value=name)
    if not generator_defs:
        msg = f"Could not find CoreGeneratorDefinition '{name}'"
        raise ValueError(msg)

    generator_def = generator_defs[0]
    logger.info("Triggering %s via CoreGeneratorDefinitionRun for %s", name, generator_def.id)

    execute_kwargs: dict[str, Any] = {
        "query": """
            mutation RunGenerator($id: String!, $nodes: [String!]!) {
                CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                    ok
                }
            }
            """,
        "variables": {"id": generator_def.id, "nodes": node_ids},
    }
    if timeout is not None:
        execute_kwargs["timeout"] = timeout

    try:
        await client.execute_graphql(**execute_kwargs)
    except ServerNotResponsiveError:
        if not tolerate_timeout:
            raise
        logger.warning(
            "Timed out while triggering %s; downstream generator state is ambiguous and will be observed later",
            name,
        )


async def trigger_hostvar_generation(
    client: InfrahubClient,
    node_ids: list[str] | None = None,
    *,
    timeout: int | None = None,  # noqa: ASYNC109 - forwards the SDK GraphQL timeout option
    tolerate_timeout: bool = False,
) -> None:
    """Trigger the hostvar generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(
        client,
        "generate-avd-device-hostvar",
        node_ids=node_ids,
        timeout=timeout,
        tolerate_timeout=tolerate_timeout,
    )


async def trigger_pod_generation(client: InfrahubClient, node_ids: list[str] | None = None) -> None:
    """Trigger the pod generator for explicit pod targets."""
    await _trigger_generator(client, "generate-pod", node_ids=node_ids)


async def trigger_rack_generation(client: InfrahubClient, node_ids: list[str] | None = None) -> None:
    """Trigger the rack generator for explicit rack targets."""
    await _trigger_generator(client, "generate-rack", node_ids=node_ids)


async def trigger_structured_config_generation(client: InfrahubClient) -> None:
    """Trigger the structured config generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(client, "generate-avd-device-structured-config")
