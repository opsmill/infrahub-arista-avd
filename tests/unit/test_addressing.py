from __future__ import annotations

from ipaddress import ip_network
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from solution_arista_avd.addressing import assign_ip_addresses_to_p2p_connections


def _interface(interface_id: str, label: str, ip_address: str | None = None) -> MagicMock:
    iface = MagicMock()
    iface.id = interface_id
    iface.display_label = label
    iface.ip_address = (
        SimpleNamespace(node=SimpleNamespace(id=f"{interface_id}-ip", address=SimpleNamespace(value=ip_address)))
        if ip_address
        else SimpleNamespace(node=None, id=None)
    )
    iface.save = AsyncMock()
    return iface


def _ip(address: str) -> SimpleNamespace:
    return SimpleNamespace(address=SimpleNamespace(value=address), save=AsyncMock())


@pytest.mark.asyncio
async def test_assign_p2p_addresses_populates_missing_interface_ips() -> None:
    src_query_iface = _interface("src-query", "leaf-1 Ethernet1")
    dst_query_iface = _interface("dst-query", "spine-1 Ethernet1")
    src_fetched_iface = _interface("src-query", "leaf-1 Ethernet1")
    dst_fetched_iface = _interface("dst-query", "spine-1 Ethernet1")
    prefix = SimpleNamespace(prefix=SimpleNamespace(value=ip_network("10.0.0.0/31")))
    created_ips = [_ip("10.0.0.0/31"), _ip("10.0.0.1/31")]
    client = SimpleNamespace(
        allocate_next_ip_prefix=AsyncMock(return_value=prefix),
        create=AsyncMock(side_effect=created_ips),
        get=AsyncMock(side_effect=[src_fetched_iface, dst_fetched_iface]),
    )
    logger = MagicMock()

    await assign_ip_addresses_to_p2p_connections(
        client=client,  # type: ignore[arg-type]
        logger=logger,
        connections=[(src_query_iface, dst_query_iface)],
        prefix_len=31,
        prefix_role="fabric",
        pool=object(),  # type: ignore[arg-type]
    )

    client.allocate_next_ip_prefix.assert_awaited_once()
    assert client.allocate_next_ip_prefix.await_args.kwargs["identifier"] == "src-querydst-query"
    assert [call.kwargs["address"] for call in client.create.await_args_list] == ["10.0.0.0/31", "10.0.0.1/31"]
    assert src_fetched_iface.ip_address is created_ips[0]
    assert dst_fetched_iface.ip_address is created_ips[1]
    src_fetched_iface.save.assert_awaited_once_with(allow_upsert=True)
    dst_fetched_iface.save.assert_awaited_once_with(allow_upsert=True)


@pytest.mark.asyncio
async def test_assign_p2p_addresses_preserves_conflicting_existing_ip_and_populates_peer() -> None:
    src_query_iface = _interface("src-query", "leaf-1 Ethernet1")
    dst_query_iface = _interface("dst-query", "spine-1 Ethernet1")
    src_fetched_iface = _interface("src-query", "leaf-1 Ethernet1", ip_address="192.0.2.10/31")
    dst_fetched_iface = _interface("dst-query", "spine-1 Ethernet1")
    prefix = SimpleNamespace(prefix=SimpleNamespace(value=ip_network("10.0.0.0/31")))
    dst_ip = _ip("10.0.0.1/31")
    client = SimpleNamespace(
        allocate_next_ip_prefix=AsyncMock(return_value=prefix),
        create=AsyncMock(return_value=dst_ip),
        get=AsyncMock(side_effect=[src_fetched_iface, dst_fetched_iface]),
    )
    logger = MagicMock()

    await assign_ip_addresses_to_p2p_connections(
        client=client,  # type: ignore[arg-type]
        logger=logger,
        connections=[(src_query_iface, dst_query_iface)],
        prefix_len=31,
        prefix_role="fabric",
        pool=object(),  # type: ignore[arg-type]
    )

    client.create.assert_awaited_once_with(kind="IpamIPAddress", address="10.0.0.1/31")
    assert src_fetched_iface.ip_address.node.address.value == "192.0.2.10/31"
    src_fetched_iface.save.assert_not_awaited()
    assert dst_fetched_iface.ip_address is dst_ip
    dst_fetched_iface.save.assert_awaited_once_with(allow_upsert=True)
    assert any("Skipped IP reconciliation" in call.args[0] for call in logger.warning.call_args_list)
