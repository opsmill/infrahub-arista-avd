"""Integration test for the rack tier of device design entities (feature 001).

Boots a real Infrahub via ``infrahub-testcontainers``, loads this repo's schemas,
and validates User Story 1 — rack device designs as a normalized entity:

- the schema loads with zero errors (SC-001) and the ``NetworkDeviceDesign``
  generic plus ``NetworkRackDeviceDesign`` exist (SC-002);
- the generic carries ``role`` (super_spine/spine/leaf/l2leaf), ``device_quantity``
  (Number), and ``device_template`` -> ``CoreObjectTemplate`` (one, no-action);
- ``NetworkRackDeviceDesign`` is keyed ``(rack, role)`` (SC-004) with a readable
  ``human_friendly_id`` (SC-003);
- ``LocationRack.device_designs`` is a cascade-owned ``Component`` many
  relationship whose identifier pairs it to the child's ``rack`` Parent (SC-005).

Schema-only: this asserts the design contract by schema introspection, so it
needs only a stock Infrahub image and is far lighter than the ``-m e2e`` pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.testing.docker import TestInfrahubDockerClient

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

ROLE_CHOICES = {"super_spine", "spine", "leaf", "l2leaf"}


class TestDeviceDesignRackSchema(TestInfrahubDockerClient):
    @staticmethod
    async def _load_schema(client: InfrahubClient, branch: str, schemas: list[dict]) -> None:
        await client.schema.wait_until_converged(branch=branch)
        resp = await client.schema.load(schemas=schemas, branch=branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"  # SC-001
        await client.schema.wait_until_converged(branch=branch)

    @pytest.mark.asyncio
    async def test_generic_shape(self, default_branch: str, client: InfrahubClient, schemas: list[dict]) -> None:
        """The NetworkDeviceDesign generic carries role, device_quantity, and device_template (SC-002)."""
        await self._load_schema(client, default_branch, schemas)

        generic = await client.schema.get(kind="NetworkDeviceDesign", branch=default_branch)

        attrs = {a.name: a for a in generic.attributes}
        assert attrs["role"].kind == "Dropdown"
        assert {c["name"] for c in attrs["role"].choices} == ROLE_CHOICES
        assert attrs["device_quantity"].kind == "Number"

        rels = {r.name: r for r in generic.relationships}
        assert rels["device_template"].peer == "CoreObjectTemplate"
        assert rels["device_template"].cardinality == "one"
        assert rels["device_template"].optional is False
        # Shared template must survive design deletion.
        assert rels["device_template"].on_delete == "no-action"

    @pytest.mark.asyncio
    async def test_rack_design_is_keyed_and_wired(
        self, default_branch: str, client: InfrahubClient, schemas: list[dict]
    ) -> None:
        """NetworkRackDeviceDesign inherits the generic, is keyed (rack, role), and is cascade-owned (SC-002/3/4/5)."""
        await self._load_schema(client, default_branch, schemas)

        design = await client.schema.get(kind="NetworkRackDeviceDesign", branch=default_branch)
        assert "NetworkDeviceDesign" in design.inherit_from  # SC-002

        # SC-004: at most one design per (rack, role).
        assert ["rack", "role__value"] in design.uniqueness_constraints
        # SC-003: readable identifier.
        assert design.human_friendly_id == ["rack__name__value", "role__value"]

        # Child Parent side.
        design_rels = {r.name: r for r in design.relationships}
        assert design_rels["rack"].peer == "LocationRack"
        assert design_rels["rack"].cardinality == "one"
        assert design_rels["rack"].kind == "Parent"
        assert design_rels["rack"].identifier == "rack__device_designs"

        # SC-005: container Component side — many, cascade, matching identifier.
        rack = await client.schema.get(kind="LocationRack", branch=default_branch)
        dd = next((r for r in rack.relationships if r.name == "device_designs"), None)
        assert dd is not None, "LocationRack is missing the 'device_designs' relationship"
        assert dd.peer == "NetworkRackDeviceDesign"
        assert dd.cardinality == "many"
        assert dd.kind == "Component"
        assert dd.on_delete == "cascade"
        assert dd.identifier == "rack__device_designs"
