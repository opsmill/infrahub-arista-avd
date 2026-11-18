from __future__ import annotations

from typing import TYPE_CHECKING

from infrahub_sdk.node import RelationshipManager

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient


async def keep_tracked_nodes(client: InfrahubClient) -> None:
    """Track again every node the previous run of this generator instance tracked.

    The cleanup at the end of a run deletes every group member the run did not save, so a run that
    stops before it saves its nodes would otherwise delete everything the previous run created.
    """
    group = await client.group_context.get_group()
    if group is None:
        return
    members = group.members
    if not isinstance(members, RelationshipManager):
        return
    already_tracked = set(client.group_context.related_node_ids) | set(client.group_context.related_group_ids)
    missing = [peer_id for peer_id in members.peer_ids if peer_id not in already_tracked]
    if missing:
        await client.group_context.add_related_nodes(ids=missing, update_group_context=True)
