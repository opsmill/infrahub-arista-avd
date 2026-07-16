"""Integration test for the RoutingAsn schema (feature 002-bgp-asn-schema).

Boots a real Infrahub via ``infrahub-testcontainers``, loads this repo's schemas,
and validates the "BGP ASN as a first-class node" design:

- the schema loads with zero errors (SC-001) and ``RoutingAsn`` exists (SC-002);
- ``RoutingAsn.asn`` is globally unique — a duplicate AS number is rejected
  regardless of fabric (SC-004);
- the device / MLAG references are wired bidirectionally with matching
  identifiers (SC-005).

Schema-only: this does not run generators, so it needs only a stock Infrahub
image and is far lighter than the full ``-m e2e`` pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from infrahub_sdk.exceptions import GraphQLError
from infrahub_sdk.testing.docker import TestInfrahubDockerClient

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient


class TestBgpAsnSchema(TestInfrahubDockerClient):
    @staticmethod
    async def _load_schema(client: InfrahubClient, branch: str, schemas: list[dict]) -> None:
        await client.schema.wait_until_converged(branch=branch)
        resp = await client.schema.load(schemas=schemas, branch=branch, wait_until_converged=True)
        assert resp.errors == {}, f"schema load errors: {resp.errors}"  # SC-001
        await client.schema.wait_until_converged(branch=branch)

    @pytest.mark.asyncio
    async def test_schema_loads_and_wires_routing_asn(
        self, default_branch: str, client: InfrahubClient, schemas: list[dict]
    ) -> None:
        """Schema loads clean (SC-001); RoutingAsn exists and is wired to devices/MLAG (SC-002, SC-005)."""
        await self._load_schema(client, default_branch, schemas)

        # SC-002: the node exists and its AS number is globally unique.
        asn_schema = await client.schema.get(kind="RoutingAsn", branch=default_branch)
        asn_attr = next((a for a in asn_schema.attributes if a.name == "asn"), None)
        assert asn_attr is not None, "RoutingAsn is missing the 'asn' attribute"
        assert asn_attr.unique is True, "RoutingAsn.asn must be globally unique"

        # SC-005: inverses on the ASN node, with the identifiers that pair them to the peers.
        rels = {r.name: r for r in asn_schema.relationships}
        assert rels["fabric"].cardinality == "one"
        assert rels["devices"].cardinality == "many"
        assert rels["devices"].identifier == "device__asn"
        assert rels["mlag_domains"].cardinality == "many"
        assert rels["mlag_domains"].identifier == "mlag_domain__asn"

        # forward "one" side on each peer, sharing the identifier (bidirectional edge).
        device_schema = await client.schema.get(kind="DcimDevice", branch=default_branch)
        dev_asn = next((r for r in device_schema.relationships if r.name == "asn"), None)
        assert dev_asn is not None, "DcimDevice is missing the 'asn' relationship"
        assert dev_asn.peer == "RoutingAsn"
        assert dev_asn.cardinality == "one"
        assert dev_asn.identifier == "device__asn"

        mlag_schema = await client.schema.get(kind="MlagDomain", branch=default_branch)
        mlag_asn = next((r for r in mlag_schema.relationships if r.name == "asn"), None)
        assert mlag_asn is not None, "MlagDomain is missing the 'asn' relationship"
        assert mlag_asn.peer == "RoutingAsn"
        assert mlag_asn.cardinality == "one"
        assert mlag_asn.identifier == "mlag_domain__asn"

    @pytest.mark.asyncio
    async def test_asn_is_globally_unique(
        self, default_branch: str, client: InfrahubClient, schemas: list[dict]
    ) -> None:
        """A second RoutingAsn with the same AS number is rejected — no cross-fabric reuse (SC-004)."""
        await self._load_schema(client, default_branch, schemas)

        first = await client.create(kind="RoutingAsn", asn=64599, branch=default_branch)
        await first.save()

        duplicate = await client.create(kind="RoutingAsn", asn=64599, branch=default_branch)
        with pytest.raises(GraphQLError):
            await duplicate.save()
