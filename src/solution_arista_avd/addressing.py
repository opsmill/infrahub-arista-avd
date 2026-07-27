from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .protocols import DcimInterface

if TYPE_CHECKING:
    import logging
    from collections.abc import Iterator
    from ipaddress import IPv4Address, IPv6Address

    from infrahub_sdk import InfrahubClient
    from infrahub_sdk.protocols import CoreIPPrefixPool

    from .protocols import IpamIPAddress, IpamPrefix


async def assign_ip_address_to_interface(
    client: InfrahubClient,
    interface: DcimInterface,
    logger: logging.Logger,
    host_addresses: Iterator[IPv4Address] | Iterator[IPv6Address],
    prefix_len: int,
) -> None:
    host_address = next(host_addresses)
    expected_address = f"{host_address}/{prefix_len}"
    # Re-fetch the generated interface with its existing IP relationship so
    # preservation is based on current graph state, not stale query data.
    interface = await client.get(DcimInterface, id=interface.id, include=["ip_address"])  # type: ignore[type-abstract]
    existing_address = _relationship_address(getattr(interface, "ip_address", None))
    if existing_address:
        if existing_address == expected_address:
            logger.info("Preserved generated IP %s on %s", existing_address, interface.display_label)
        else:
            logger.warning(
                "Skipped IP reconciliation for %s: existing IP %s conflicts with generated IP %s",
                interface.display_label,
                existing_address,
                expected_address,
            )
        return

    ip_address = cast(
        "IpamIPAddress",
        await client.create(kind="IpamIPAddress", address=expected_address),
    )
    await ip_address.save(allow_upsert=True)
    # SDK accepts protocol kinds at runtime; assigning a node to a relationship is the SDK pattern.
    interface.ip_address = ip_address  # type: ignore[assignment, attr-defined]
    await interface.save(allow_upsert=True)
    logger.info("Populated missing IP %s on %s", ip_address.address.value, interface.display_label)


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


def _relationship_address(relationship: object | None) -> str | None:
    if relationship is None:
        return None

    address = getattr(getattr(relationship, "address", None), "value", None)
    if isinstance(address, str) and address:
        return address

    node = getattr(relationship, "node", None) or getattr(relationship, "peer", None)
    address = getattr(getattr(node, "address", None), "value", None)
    if isinstance(address, str) and address:
        return address

    relationship_id = getattr(relationship, "id", None)
    if isinstance(relationship_id, str) and relationship_id:
        return relationship_id

    node_id = getattr(node, "id", None)
    if isinstance(node_id, str) and node_id:
        return node_id

    return None
