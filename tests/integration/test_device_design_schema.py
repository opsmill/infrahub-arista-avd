"""Schema-contract integration test for device design entities.

Boots a real Infrahub via ``infrahub-testcontainers``, loads this repo's schemas
once, and asserts the device-design contract by schema introspection:

- the schema loads with zero errors (SC-001) and the ``NetworkDeviceDesign``
  generic carries ``role`` (super_spine/spine/leaf/l2leaf), ``device_quantity``,
  and ``device_template`` -> ``CoreObjectTemplate`` (one, ``no-action`` so a
  shared template survives a design deletion) (SC-002);
- each tier's concrete design node inherits the generic, is keyed
  ``(container, role)`` (SC-004) with a readable ``human_friendly_id`` (SC-003),
  and pairs its ``Parent`` relationship to the container's cascade-owned
  ``Component`` many relationship (SC-005/6);
- the legacy paired sizing fields are gone, so ``device_designs`` is the only
  source of device sizing with no stale fallback (SC-006).

All tiers share one class — and therefore one Infrahub stack and one schema
load — because ``infrahub_app`` is class-scoped: a class per tier would boot a
container stack per tier and blow the PR integration-test budget.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.testing.docker import TestInfrahubDockerClient

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

ROLE_CHOICES = {"super_spine", "spine", "leaf", "l2leaf"}

# design kind, container kind, Parent relationship name, shared identifier
TIERS = [
    ("NetworkRackDeviceDesign", "LocationRack", "rack", "rack__device_designs"),
    ("NetworkPodDeviceDesign", "NetworkPod", "pod", "pod__device_designs"),
    ("NetworkFabricDeviceDesign", "NetworkFabric", "fabric", "fabric__device_designs"),
]

# container kind -> the legacy fields device_designs replaced, which MUST be gone
LEGACY_FIELDS = {
    "NetworkFabric": ["super_spine_switch_template", "amount_of_super_spines"],
    "NetworkPod": ["spine_switch_template", "amount_of_spines"],
    "LocationRack": ["leaf_switch_template", "amount_of_leafs", "l2leaf_switch_template", "amount_of_l2leafs"],
}


class TestDeviceDesignSchema(TestInfrahubDockerClient):
    # Guards the one-time load below. The `schemas` fixture is function-scoped, so
    # this fixture cannot be class-scoped; the flag gives the same "load once"
    # behaviour without widening a fixture other tests share.
    _schema_is_loaded = False

    @pytest.fixture(autouse=True)
    async def _schema_loaded(self, client: InfrahubClient, default_branch: str, schemas: list[dict]) -> None:
        """Load the repo schemas once for the whole class."""
        cls = type(self)
        if cls._schema_is_loaded:
            return
        await client.schema.wait_until_converged(branch=default_branch)
        resp = await client.schema.load(schemas=schemas, branch=default_branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"  # SC-001
        await client.schema.wait_until_converged(branch=default_branch)
        cls._schema_is_loaded = True

    async def test_generic_shape(self, default_branch: str, client: InfrahubClient) -> None:
        """The NetworkDeviceDesign generic carries role, device_quantity, and device_template (SC-002)."""
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

    @pytest.mark.parametrize(("design_kind", "container_kind", "parent_rel", "identifier"), TIERS)
    async def test_tier_design_is_keyed_and_wired(
        self,
        default_branch: str,
        client: InfrahubClient,
        design_kind: str,
        container_kind: str,
        parent_rel: str,
        identifier: str,
    ) -> None:
        """Every tier exposes designs through the same keyed, cascade-owned entity (SC-002/3/4/5/6)."""
        design = await client.schema.get(kind=design_kind, branch=default_branch)
        assert "NetworkDeviceDesign" in design.inherit_from  # SC-002 (uniform shape)
        assert [parent_rel, "role__value"] in design.uniqueness_constraints  # SC-004
        assert design.human_friendly_id == [f"{parent_rel}__name__value", "role__value"]  # SC-003

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

    @pytest.mark.parametrize("container_kind", list(LEGACY_FIELDS))
    async def test_legacy_sizing_fields_are_gone(
        self, default_branch: str, client: InfrahubClient, container_kind: str
    ) -> None:
        """Device sizing has exactly one source; the legacy paired fields no longer exist (SC-006)."""
        node = await client.schema.get(kind=container_kind, branch=default_branch)
        field_names = {a.name for a in node.attributes} | {r.name for r in node.relationships}

        for legacy in LEGACY_FIELDS[container_kind]:
            assert legacy not in field_names, (
                f"{container_kind}.{legacy} still exists; device sizing must come only "
                "from device_designs so there is no stale fallback."
            )
