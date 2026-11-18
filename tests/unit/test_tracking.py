from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from infrahub_sdk.node import RelationshipManager

from generators.tracking import keep_tracked_nodes


def _client(group: object, *, tracked_node_ids: list[str] | None = None) -> MagicMock:
    client = MagicMock()
    client.group_context.get_group = AsyncMock(return_value=group)
    client.group_context.add_related_nodes = AsyncMock()
    client.group_context.related_node_ids = tracked_node_ids or []
    client.group_context.related_group_ids = []
    return client


def _group(member_ids: list[str]) -> MagicMock:
    group = MagicMock()
    group.members = MagicMock(spec=RelationshipManager)
    group.members.peer_ids = member_ids
    return group


@pytest.mark.asyncio
async def test_keeps_previous_members_not_tracked_by_this_run() -> None:
    client = _client(_group(["leaf-1", "rack-1", "link-1"]), tracked_node_ids=["rack-1"])

    await keep_tracked_nodes(client)

    client.group_context.add_related_nodes.assert_awaited_once_with(ids=["leaf-1", "link-1"], update_group_context=True)


@pytest.mark.asyncio
async def test_does_nothing_without_a_previous_run() -> None:
    client = _client(None)

    await keep_tracked_nodes(client)

    client.group_context.add_related_nodes.assert_not_awaited()


@pytest.mark.asyncio
async def test_does_nothing_when_every_member_is_already_tracked() -> None:
    client = _client(_group(["rack-1"]), tracked_node_ids=["rack-1"])

    await keep_tracked_nodes(client)

    client.group_context.add_related_nodes.assert_not_awaited()
