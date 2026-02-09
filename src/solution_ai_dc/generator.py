from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

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
    def calculate_checksum(self) -> str:
        """Calculates a checksum of the generator based on the related ids during the session"""

        related_ids = self.client.group_context.related_group_ids + self.client.group_context.related_node_ids
        sorted_ids = sorted(related_ids)
        joined = ",".join(sorted_ids)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    async def generate_hostvars_for_devices(self, devices: list) -> None:
        """Generate AVD hostvars for a list of devices by chaining to the hostvar generator."""
        from generators.generate_avd_device_hostvar import GenerateAVDDeviceHostvar

        for device in devices:
            hostname = device.hostname.value
            logger.info(f"Chaining hostvars generation for device {hostname}")
            hostvar_gen = GenerateAVDDeviceHostvar(
                query="avd_device_hostvar",
                client=self._init_client,
                infrahub_node=type(device),
                branch=self.branch_name,
                params={"hostname": hostname},
                convert_query_response=False,
            )
            await hostvar_gen.run(identifier=f"generate-avd-device-hostvar-{hostname}")
