from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from solution_arista_avd.protocols import DcimDevice, RoutingAsn

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient
    from infrahub_sdk.protocols import CoreNumberPool


class RoutingAsnAllocator(Protocol):
    async def __call__(self, asn_pool: CoreNumberPool, fabric_id: str) -> RoutingAsn: ...


async def set_device_asn(client: InfrahubClient, device_id: str, routing_asn_id: str) -> None:
    """Link DcimDevice.asn to a RoutingAsn without resaving the SDK object's relationships."""
    await client.execute_graphql(
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


async def ensure_shared_device_asn(
    *,
    client: InfrahubClient,
    devices: list[DcimDevice],
    asn_pool: CoreNumberPool,
    fabric_id: str,
    allocate_routing_asn: RoutingAsnAllocator,
) -> RoutingAsn | None:
    """Link all devices to one shared fabric-owned RoutingAsn."""
    if not devices:
        return None

    device_ids = [device.id for device in devices]
    fetched_devices = [
        await client.get(  # type: ignore[type-abstract]
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
        routing_asn = await allocate_routing_asn(asn_pool, fabric_id)
        shared_asn_id = routing_asn.id

    try:
        for fetched_device in fetched_devices:
            if getattr(getattr(fetched_device, "asn", None), "id", None) == shared_asn_id:
                continue
            await set_device_asn(client, fetched_device.id, shared_asn_id)
    except Exception:
        if routing_asn is not None:
            await routing_asn.delete()
        raise

    return routing_asn
