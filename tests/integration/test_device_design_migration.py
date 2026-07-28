"""Migration integration test for device design entities (feature 001).

Guards the completed normalization: every container exposes ``device_designs``
and the legacy per-role template/quantity fields no longer exist in the schema.
Device sizing has exactly one source of truth, so nothing can quietly fall back
to a stale count or template.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.testing.docker import TestInfrahubDockerClient

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

# container kind -> the legacy fields device_designs replaced, which MUST be gone
LEGACY_FIELDS = {
    "NetworkFabric": ["super_spine_switch_template", "amount_of_super_spines"],
    "NetworkPod": ["spine_switch_template", "amount_of_spines"],
    "LocationRack": ["leaf_switch_template", "amount_of_leafs", "l2leaf_switch_template", "amount_of_l2leafs"],
}

# container kind -> the concrete design node its device_designs relationship points at
DESIGN_PEER = {
    "NetworkFabric": "NetworkFabricDeviceDesign",
    "NetworkPod": "NetworkPodDeviceDesign",
    "LocationRack": "NetworkRackDeviceDesign",
}


class TestDeviceDesignMigration(TestInfrahubDockerClient):
    @staticmethod
    async def _load_schema(client: InfrahubClient, branch: str, schemas: list[dict]) -> None:
        await client.schema.wait_until_converged(branch=branch)
        resp = await client.schema.load(schemas=schemas, branch=branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"  # SC-001
        await client.schema.wait_until_converged(branch=branch)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("container_kind", list(LEGACY_FIELDS))
    async def test_device_designs_replaced_legacy_fields(
        self,
        default_branch: str,
        client: InfrahubClient,
        schemas: list[dict],
        container_kind: str,
    ) -> None:
        """device_designs is present and the legacy paired fields are gone (SC-006)."""
        await self._load_schema(client, default_branch, schemas)

        node = await client.schema.get(kind=container_kind, branch=default_branch)
        relationships = {r.name: r for r in node.relationships}
        field_names = {a.name for a in node.attributes} | set(relationships)

        assert "device_designs" in relationships, f"{container_kind}.device_designs missing"
        assert relationships["device_designs"].peer == DESIGN_PEER[container_kind]
        assert relationships["device_designs"].cardinality == "many"

        for legacy in LEGACY_FIELDS[container_kind]:
            assert legacy not in field_names, (
                f"{container_kind}.{legacy} still exists; device sizing must come only "
                "from device_designs so there is no stale fallback."
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("design_kind", sorted(set(DESIGN_PEER.values())))
    async def test_design_nodes_carry_role_quantity_and_template(
        self,
        default_branch: str,
        client: InfrahubClient,
        schemas: list[dict],
        design_kind: str,
    ) -> None:
        """Each concrete design node exposes role, device_quantity, and device_template."""
        await self._load_schema(client, default_branch, schemas)

        node = await client.schema.get(kind=design_kind, branch=default_branch)
        attributes = {a.name: a for a in node.attributes}
        relationships = {r.name for r in node.relationships}

        assert "role" in attributes, f"{design_kind}.role missing"
        assert "device_quantity" in attributes, f"{design_kind}.device_quantity missing"
        assert "device_template" in relationships, f"{design_kind}.device_template missing"

        roles = {choice["name"] for choice in attributes["role"].choices or []}
        assert {"super_spine", "spine", "leaf", "l2leaf"} <= roles, f"{design_kind}.role choices incomplete: {roles}"
