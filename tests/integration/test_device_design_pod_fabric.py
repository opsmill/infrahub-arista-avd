"""Integration test for the pod and fabric tiers of device design entities (feature 001).

Validates User Story 2 — the same normalized device-design pattern applied to
``NetworkPod`` (spine designs) and ``NetworkFabric`` (super-spine designs):

- ``NetworkPodDeviceDesign`` and ``NetworkFabricDeviceDesign`` inherit the
  ``NetworkDeviceDesign`` generic and are keyed ``(container, role)`` (SC-004);
- ``NetworkPod.device_designs`` and ``NetworkFabric.device_designs`` are
  cascade-owned ``Component`` many relationships whose identifiers pair them to
  the child Parent relationships (SC-005);
- all three tiers therefore expose device designs through one identical entity
  shape (SC-006).

Schema-only, by schema introspection — no generators, stock Infrahub image.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.testing.docker import TestInfrahubDockerClient

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

# (concrete design kind, container kind, Parent/Component relationship name, shared identifier)
TIERS = [
    ("NetworkPodDeviceDesign", "NetworkPod", "pod", "pod__device_designs"),
    ("NetworkFabricDeviceDesign", "NetworkFabric", "fabric", "fabric__device_designs"),
]


class TestDeviceDesignPodFabricSchema(TestInfrahubDockerClient):
    @staticmethod
    async def _load_schema(client: InfrahubClient, branch: str, schemas: list[dict]) -> None:
        await client.schema.wait_until_converged(branch=branch)
        resp = await client.schema.load(schemas=schemas, branch=branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"  # SC-001
        await client.schema.wait_until_converged(branch=branch)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("design_kind", "container_kind", "parent_rel", "identifier"), TIERS)
    async def test_tier_design_is_keyed_and_wired(
        self,
        default_branch: str,
        client: InfrahubClient,
        schemas: list[dict],
        design_kind: str,
        container_kind: str,
        parent_rel: str,
        identifier: str,
    ) -> None:
        """Each of pod/fabric exposes designs through the same keyed, cascade-owned entity (SC-004/5/6)."""
        await self._load_schema(client, default_branch, schemas)

        design = await client.schema.get(kind=design_kind, branch=default_branch)
        assert "NetworkDeviceDesign" in design.inherit_from  # SC-006 (uniform shape)
        assert [parent_rel, "role__value"] in design.uniqueness_constraints  # SC-004
        assert design.human_friendly_id == [f"{parent_rel}__name__value", "role__value"]

        design_rels = {r.name: r for r in design.relationships}
        assert design_rels[parent_rel].peer == container_kind
        assert design_rels[parent_rel].kind == "Parent"
        assert design_rels[parent_rel].cardinality == "one"
        assert design_rels[parent_rel].identifier == identifier

        # SC-005: container Component side — many, cascade, matching identifier.
        container = await client.schema.get(kind=container_kind, branch=default_branch)
        dd = next((r for r in container.relationships if r.name == "device_designs"), None)
        assert dd is not None, f"{container_kind} is missing the 'device_designs' relationship"
        assert dd.peer == design_kind
        assert dd.cardinality == "many"
        assert dd.kind == "Component"
        assert dd.on_delete == "cascade"
        assert dd.identifier == identifier
