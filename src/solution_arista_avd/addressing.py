from __future__ import annotations

from ipaddress import IPv4Network
from typing import TYPE_CHECKING, cast

from .protocols import DcimInterface

if TYPE_CHECKING:
    import logging
    from collections.abc import Iterator
    from ipaddress import IPv4Address, IPv6Address

    from infrahub_sdk import InfrahubClient
    from infrahub_sdk.protocols import CoreIPPrefixPool

    from .protocols import IpamIPAddress, IpamPrefix


async def allocate_p2p_prefix_from_pool(
    client: InfrahubClient,
    pool: CoreIPPrefixPool,
    *,
    identifier: str,
    prefix_length: int = 31,
) -> IPv4Network:
    """Allocate or reuse a stable point-to-point prefix from a prefix pool."""
    prefix = cast(
        "IpamPrefix",
        await client.allocate_next_ip_prefix(
            resource_pool=pool,
            identifier=identifier,
            member_type="address",
            prefix_length=prefix_length,
        ),
    )
    return IPv4Network(str(prefix.prefix.value), strict=False)


async def assign_ip_address_to_interface(
    client: InfrahubClient,
    interface: DcimInterface,
    logger: logging.Logger,
    host_addresses: Iterator[IPv4Address] | Iterator[IPv6Address],
    prefix_len: int,
) -> None:
    ip_address = cast(
        "IpamIPAddress",
        await client.create(kind="IpamIPAddress", address=str(next(host_addresses)) + f"/{prefix_len}"),
    )
    await ip_address.save(allow_upsert=True)
    # SDK accepts protocol kinds at runtime; assigning a node to a relationship is the SDK pattern.
    interface = await client.get(DcimInterface, id=interface.id, include=["connector"])  # type: ignore[type-abstract]
    interface.ip_address = ip_address  # type: ignore[assignment]
    await interface.save(allow_upsert=True)
    logger.info(f"Assigned {ip_address.address.value} to {interface.display_label}")


async def assign_ip_addresses_to_p2p_connections(
    client: InfrahubClient,
    logger: logging.Logger,
    connections: list[tuple[DcimInterface, DcimInterface]],
    prefix_len: int,
    prefix_role: str,
    pool: CoreIPPrefixPool,
) -> None:
    for src_interface, dst_interface in connections:
        # allocate a new prefix for the p2p connection
        prefix = cast(
            "IpamPrefix",
            await client.allocate_next_ip_prefix(
                resource_pool=pool,
                identifier=src_interface.id + dst_interface.id,
                member_type="address",
                prefix_length=prefix_len,
                data={"role": prefix_role},
            ),
        )

        logger.info(
            f"Allocated prefix {prefix.prefix.value} for connection between {src_interface.display_label}-{dst_interface.display_label}"
        )

        host_addresses = prefix.prefix.value.hosts()

        for interface in [src_interface, dst_interface]:
            await assign_ip_address_to_interface(client, interface, logger, host_addresses, prefix_len)
