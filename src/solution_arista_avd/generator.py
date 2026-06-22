from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

    from .protocols import LocationRack, NetworkPod

logger = logging.getLogger("infrahub.tasks")


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


async def _trigger_generator(client: InfrahubClient, name: str) -> None:
    """Trigger a generator by name via CoreGeneratorDefinition mutation."""
    generator_defs = await client.filters(kind="CoreGeneratorDefinition", name__value=name)
    if not generator_defs:
        logger.error("Could not find CoreGeneratorDefinition '%s'", name)
        return

    generator_def = generator_defs[0]
    logger.info("Triggering %s via CoreGeneratorDefinitionRun for %s", name, generator_def.id)

    await client.execute_graphql(
        query="""
        mutation RunGenerator($id: String!) {
            CoreGeneratorDefinitionRun(data: { id: $id }) {
                ok
            }
        }
        """,
        variables={"id": generator_def.id},
    )


async def trigger_hostvar_generation(client: InfrahubClient) -> None:
    """Trigger the hostvar generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(client, "generate-avd-device-hostvar")


async def trigger_structured_config_generation(client: InfrahubClient) -> None:
    """Trigger the structured config generator via CoreGeneratorDefinition mutation."""
    await _trigger_generator(client, "generate-avd-device-structured-config")
