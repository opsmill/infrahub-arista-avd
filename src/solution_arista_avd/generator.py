from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Any, cast

from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from .protocols import DcimDevice, DcimInterface, InterfaceVirtual, RoutingAsn

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

    from .protocols import LocationRack, NetworkPod

logger = logging.getLogger("infrahub.tasks")

# Every generated network device starts life in provisioning and is enrolled in
# the avd_devices group so the AVD generators pick it up for config generation.
DEVICE_STATUS_PROVISIONING = "provisioning"
AVD_DEVICES_GROUP = "avd_devices"
VTEP_LOOPBACK_ROLES = {"leaf", "border_leaf"}


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

    def calculate_checksum(self) -> str:
        """Calculates a checksum of the generator based on the related ids during the session"""

        related_ids = self.client.group_context.related_group_ids + self.client.group_context.related_node_ids
        sorted_ids = sorted(related_ids)
        joined = ",".join(sorted_ids)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    async def resolve_avd_pools(
        self, node: Any
    ) -> tuple[CoreNumberPool | None, CoreNumberPool | None, CoreIPAddressPool | None, CoreIPAddressPool | None]:
        """Resolve the (asn, node_id, mgmt, vtep) AVD pools referenced by a fabric node.

        The fabric/pod/rack generators all read the same optional pool
        relationships off the fabric (directly, or via the pod's parent). Each
        is optional; a missing or unset relationship resolves to ``None``.
        """
        asn_pool: CoreNumberPool | None = None
        node_id_pool: CoreNumberPool | None = None
        mgmt_pool: CoreIPAddressPool | None = None
        vtep_loopback_pool: CoreIPAddressPool | None = None

        asn_rel = getattr(node, "asn_pool", None)
        if asn_rel and asn_rel.node:
            asn_pool = await self.client.get(kind=CoreNumberPool, id=asn_rel.node.id)  # type: ignore[type-abstract]

        node_id_rel = getattr(node, "node_id_pool", None)
        if node_id_rel and node_id_rel.node:
            node_id_pool = await self.client.get(kind=CoreNumberPool, id=node_id_rel.node.id)  # type: ignore[type-abstract]

        mgmt_rel = getattr(node, "mgmt_pool", None)
        if mgmt_rel and mgmt_rel.node:
            mgmt_pool = await self.client.get(kind=CoreIPAddressPool, id=mgmt_rel.node.id)  # type: ignore[type-abstract]

        fabric_name = getattr(getattr(node, "name", None), "value", None)
        vtep_rel = getattr(node, "vtep_pool", None)
        if fabric_name and vtep_rel and vtep_rel.node:
            vtep_loopback_pool = await self._ensure_vtep_loopback_address_pool(
                fabric_name=str(fabric_name).lower(),
                vtep_prefix_pool_ref=vtep_rel.node,
            )

        return asn_pool, node_id_pool, mgmt_pool, vtep_loopback_pool

    async def _ensure_vtep_loopback_address_pool(
        self, *, fabric_name: str, vtep_prefix_pool_ref: object
    ) -> CoreIPAddressPool:
        """Create or update the address pool used for Infrahub-owned VTEP IP allocation."""
        prefix_ids = await self._prefix_resource_ids(vtep_prefix_pool_ref)
        if not prefix_ids:
            msg = f"Fabric '{fabric_name}': vtep_pool has no prefix resources for VTEP loopback allocation"
            raise ValueError(msg)

        vtep_loopback_pool = await self.client.create(
            kind=CoreIPAddressPool,
            name=f"{fabric_name}-vtep-loopback-address-pool",
            default_address_type="IpamIPAddress",
            default_prefix_length=32,
            ip_namespace={"hfid": ["default"]},
            resources=[{"id": prefix_id} for prefix_id in prefix_ids],
        )
        await vtep_loopback_pool.save(allow_upsert=True, update_group_context=False)
        return vtep_loopback_pool

    async def _prefix_resource_ids(self, prefix_pool_ref: object) -> list[str]:
        resources = getattr(prefix_pool_ref, "resources", None)
        prefix_ids = self._resource_ids(resources)
        if prefix_ids:
            return prefix_ids

        prefix_pool_id = getattr(prefix_pool_ref, "id", None)
        if not prefix_pool_id:
            return []

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
        device_kwargs: dict[str, Any] = {
            "name": name,
            "status": DEVICE_STATUS_PROVISIONING,
            "object_template": {"id": object_template_id},
            "role": role,
            "pod": {"id": pod_id},
            "member_of_groups": [AVD_DEVICES_GROUP],
        }
        if rack_id is not None:
            device_kwargs["rack"] = {"id": rack_id}
        if index is not None:
            device_kwargs["index"] = index
        if loopback_pool is not None:
            device_kwargs["loopback_ip"] = loopback_pool
        if vtep_loopback_pool is not None and role in VTEP_LOOPBACK_ROLES:
            device_kwargs["vtep_loopback_ip"] = vtep_loopback_pool
        if node_id_pool is not None:
            device_kwargs["node_id"] = node_id_pool
        if mgmt_pool is not None:
            device_kwargs["mgmt_ip"] = mgmt_pool

        existing_devices = await self.client.filters(DcimDevice, name__value=name)
        device_existed = bool(existing_devices)

        device = await self.client.create(DcimDevice, **device_kwargs)  # type: ignore[type-abstract]
        await device.save(allow_upsert=True)

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


async def _trigger_generator(client: InfrahubClient, name: str, node_ids: list[str] | None = None) -> None:
    """Trigger a generator by name via CoreGeneratorDefinition mutation."""
    if node_ids is None:
        logger.warning("Skipping %s trigger: target node IDs are required", name)
        return
    if not node_ids:
        logger.warning("Skipping %s trigger: no target node IDs found", name)
        return

    generator_defs = await client.filters(kind="CoreGeneratorDefinition", name__value=name)
    if not generator_defs:
        logger.error("Could not find CoreGeneratorDefinition '%s'", name)
        return

    generator_def = generator_defs[0]
    logger.info("Triggering %s via CoreGeneratorDefinitionRun for %s", name, generator_def.id)

    await client.execute_graphql(
        query="""
        mutation RunGenerator($id: String!, $nodes: [String!]!) {
            CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                ok
            }
        }
        """,
        variables={"id": generator_def.id, "nodes": node_ids},
    )


async def trigger_hostvar_generation(client: InfrahubClient, node_ids: list[str] | None = None) -> None:
    """Trigger the hostvar generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(client, "generate-avd-device-hostvar", node_ids=node_ids)


async def trigger_structured_config_generation(client: InfrahubClient) -> None:
    """Trigger the structured config generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(client, "generate-avd-device-structured-config")
