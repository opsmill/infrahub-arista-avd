from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from infrahub_sdk.exceptions import ServerNotResponsiveError

from generators.generate_rack import RackGenerator, is_mlag_enabled
from solution_arista_avd.generator import trigger_hostvar_generation

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine


def _leaf(leaf_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=leaf_id,
        name=SimpleNamespace(value=name),
        save=AsyncMock(),
    )


def _pool(start: int = 65100, end: int = 65199) -> SimpleNamespace:
    return SimpleNamespace(start_range=SimpleNamespace(value=start), end_range=SimpleNamespace(value=end))


def _domain(domain_id: str, *, domain_uuid: str | None = None, asn_node_id: str | None = None) -> SimpleNamespace:
    """Mock MlagDomain whose ``asn`` relationship points at the given RoutingAsn node id."""
    return SimpleNamespace(
        id=domain_uuid or domain_id,
        domain_id=SimpleNamespace(value=domain_id),
        asn=SimpleNamespace(id=asn_node_id),
    )


def _named_device(device_id: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, name=SimpleNamespace(value=name))


def _rack_query_data(
    *,
    pod_node: dict | object | None = "default",
    leaf_template_id: str | None = "leaf-template",
    leaf_count: int = 2,
    l2leaf_template_id: str | None = None,
    l2leaf_count: int = 0,
    loopback_pool_id: str | None = "loopback-pool",
    prefix_pool_id: str | None = "prefix-pool",
) -> dict:
    if pod_node == "default":
        pod_node = {
            "id": "pod-1",
            "name": {"value": "Pod-A"},
            "index": {"value": 1},
            "prefix_pool": {"node": {"id": prefix_pool_id} if prefix_pool_id else None},
            "loopback_pool": {"node": {"id": loopback_pool_id} if loopback_pool_id else None},
            "amount_of_spines": {"value": 2},
            "leaf_interface_sorting_method": {"value": "sort_interfaces"},
            "spine_interface_sorting_method": {"value": "sort_interfaces"},
            "parent": {
                "node": {
                    "__typename": "NetworkFabric",
                    "name": {"value": "Fabric-A"},
                    "underlay_routing_protocol": {"value": "ebgp"},
                    "asn_pool": {"node": None},
                    "node_id_pool": {"node": None},
                    "mgmt_pool": {"node": None},
                    "vtep_pool": {"node": None},
                }
            },
        }

    return {
        "LocationRack": {
            "edges": [
                {
                    "node": {
                        "id": "rack-1",
                        "name": {"value": "DC1_BORDER"},
                        "checksum": {"value": "checksum"},
                        "index": {"value": 1},
                        "rack_type": {"value": "leaf"},
                        "amount_of_leafs": {"value": leaf_count},
                        "mlag": {"value": True},
                        "leaf_switch_template": {
                            "node": (
                                {"__typename": "TemplateDcimDevice", "id": leaf_template_id}
                                if leaf_template_id
                                else None
                            )
                        },
                        "amount_of_l2leafs": {"value": l2leaf_count},
                        "l2leaf_switch_template": {
                            "node": (
                                {"__typename": "TemplateDcimDevice", "id": l2leaf_template_id}
                                if l2leaf_template_id
                                else None
                            )
                        },
                        "parent": {"node": {"__typename": "LocationRack", "id": "parent-1", "name": {"value": "P"}}},
                        "pod": {"node": pod_node},
                    }
                }
            ]
        }
    }


def _rack_node() -> SimpleNamespace:
    return SimpleNamespace(generation_complete=SimpleNamespace(value=True), save=AsyncMock())


def _pod_node() -> SimpleNamespace:
    return SimpleNamespace(parent=SimpleNamespace(fetch=AsyncMock(), peer=SimpleNamespace(id="fabric-1")))


def _filters_side_effect(
    *,
    domains: list[SimpleNamespace] | None = None,
) -> Callable[..., Coroutine[Any, Any, list[SimpleNamespace]]]:
    async def side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))

        if kind_name == "MlagDomain" and kwargs.get("domain_id__value") == "DC1_BORDER":
            return domains or []
        return []

    return side_effect


def _make_generator() -> RackGenerator:
    gen = RackGenerator.__new__(RackGenerator)
    gen.client = MagicMock()
    gen.client.create = AsyncMock()
    gen.client.get = AsyncMock()
    gen.client.filters = AsyncMock(side_effect=_filters_side_effect())
    gen.client.execute_graphql = AsyncMock()
    gen.logger = MagicMock()
    gen.fabric = SimpleNamespace(id="fabric-1")
    gen.pod_id = "pod-1"
    gen.rack_name = "DC1_BORDER"
    gen.rack_amount_of_leafs = 2
    gen.rack_mlag = True
    gen.rack_mlag_enabled = True
    gen.rack_index = 1
    gen.rack_id = "rack-1"
    gen.rack_leaf_switch_template = "leaf-template"
    gen.pod_name = "pod-a"
    gen.loopback_pool = object()
    gen.asn_pool = _pool()
    gen.node_id_pool = object()
    gen.mgmt_pool = object()
    gen.vtep_loopback_pool = object()
    gen.leaf_switches = [_leaf("leaf-a", "leaf-a"), _leaf("leaf-b", "leaf-b")]
    gen.l2leaf_switches = []
    gen.spine_switches = [_named_device("spine-a", "spine-a"), _named_device("spine-b", "spine-b")]
    return gen


def _iface(name: str, role: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=SimpleNamespace(value=name),
        role=SimpleNamespace(value=role),
        save=AsyncMock(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (_rack_query_data(pod_node=None), "rack has no pod"),
        (_rack_query_data(loopback_pool_id=None), "pod has no loopback_pool"),
        (_rack_query_data(prefix_pool_id=None), "pod has no prefix_pool"),
    ],
)
async def test_generate_defers_when_required_relationships_are_missing(data: dict, reason: str) -> None:
    gen = _make_generator()
    rack = _rack_node()
    gen.client.get.return_value = rack
    gen.create_leaf_switches = AsyncMock()  # type: ignore[method-assign]

    await gen.generate(data)

    assert rack.generation_complete.value is False
    rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    gen.create_leaf_switches.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()
    gen.logger.info.assert_any_call("Deferring rack %s generation: %s", "DC1_BORDER", reason)


@pytest.mark.asyncio
async def test_generate_defers_when_pod_parent_fabric_is_missing() -> None:
    data = _rack_query_data()
    data["LocationRack"]["edges"][0]["node"]["pod"]["node"]["parent"] = {"node": None}
    gen = _make_generator()
    rack = _rack_node()
    gen.client.get.return_value = rack
    gen.create_leaf_switches = AsyncMock()  # type: ignore[method-assign]

    await gen.generate(data)

    assert rack.generation_complete.value is False
    rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    gen.create_leaf_switches.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_defers_when_spines_are_missing() -> None:
    gen = _make_generator()
    rack = _rack_node()
    gen.client.get.side_effect = [_pod_node(), rack]
    gen.client.filters = AsyncMock(return_value=[])
    gen.create_leaf_switches = AsyncMock()  # type: ignore[method-assign]

    await gen.generate(_rack_query_data())

    assert rack.generation_complete.value is False
    rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    gen.create_leaf_switches.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_requires_leaf_template_when_leaf_count_is_positive() -> None:
    gen = _make_generator()

    with pytest.raises(ValueError, match=r"DC1_BORDER.*leaf_switch_template is missing"):
        await gen.generate(_rack_query_data(leaf_template_id=None, leaf_count=2))

    gen.client.get.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_requires_l2leaf_template_when_l2leaf_count_is_positive() -> None:
    gen = _make_generator()

    with pytest.raises(ValueError, match=r"DC1_BORDER.*l2leaf_switch_template is missing"):
        await gen.generate(_rack_query_data(l2leaf_template_id=None, l2leaf_count=1))

    gen.client.get.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_compat_passes_timeout() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    gen.client.execute_graphql = AsyncMock()

    await gen._trigger_hostvar_generation_compat(node_ids=["leaf-a"], timeout=300, tolerate_timeout=True)

    assert gen.client.execute_graphql.await_args.kwargs["timeout"] == 300
    assert gen.client.execute_graphql.await_args.kwargs["variables"] == {
        "id": "generator-1",
        "nodes": ["leaf-a"],
    }


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_compat_tolerates_only_server_timeout() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    gen.client.execute_graphql = AsyncMock(side_effect=ServerNotResponsiveError(url="http://infrahub", timeout=300))

    await gen._trigger_hostvar_generation_compat(node_ids=["leaf-a"], timeout=300, tolerate_timeout=True)

    gen.client.execute_graphql.assert_awaited_once()

    gen.client.execute_graphql = AsyncMock(side_effect=RuntimeError("graphql failed"))
    with pytest.raises(RuntimeError, match="graphql failed"):
        await gen._trigger_hostvar_generation_compat(node_ids=["leaf-a"], timeout=300, tolerate_timeout=True)


@pytest.mark.asyncio
async def test_assign_l2leaf_mlag_peer_interfaces_uses_highest_access_ports() -> None:
    """The peer-link is carved from the highest-numbered access ports so it never
    collides with server cabling, which fills the lowest-numbered ports first. Only
    access ports (role server/mlag_peer) are eligible — uplinks are never touched."""
    gen = _make_generator()
    ifaces = [
        _iface("Ethernet1", "server"),
        _iface("Ethernet2", "server"),
        _iface("Ethernet47", "server"),
        _iface("Ethernet48", "server"),
        _iface("Ethernet49/1", "spine"),  # uplink — never eligible
    ]
    gen.client.filters = AsyncMock(return_value=ifaces)

    await gen._assign_l2leaf_mlag_peer_interfaces(_leaf("leaf-a", "leaf-pod-a-1-1"))

    converted = {i.name.value for i in ifaces if i.role.value == "mlag_peer"}
    assert converted == {"Ethernet47", "Ethernet48"}
    assert ifaces[0].role.value == "server"  # low ports untouched (reserved for servers)
    assert ifaces[4].role.value == "spine"  # uplink untouched
    for i in ifaces:
        if i.name.value in {"Ethernet47", "Ethernet48"}:
            # Template-owned interfaces are saved outside the tracking group so a
            # later reconciliation never resets or deletes them.
            i.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
        else:
            i.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_l2leaf_mlag_peer_interfaces_is_idempotent() -> None:
    """A re-run is a no-op: ports already in role mlag_peer are re-selected (the pool
    still includes them) but not re-saved, so the choice never shifts on re-run."""
    gen = _make_generator()
    ifaces = [
        _iface("Ethernet1", "server"),
        _iface("Ethernet2", "server"),
        _iface("Ethernet47", "mlag_peer"),
        _iface("Ethernet48", "mlag_peer"),
    ]
    gen.client.filters = AsyncMock(return_value=ifaces)

    await gen._assign_l2leaf_mlag_peer_interfaces(_leaf("leaf-a", "leaf-pod-a-1-1"))

    for i in ifaces:
        i.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_l2leaf_mlag_peer_interfaces_raises_when_too_few_ports() -> None:
    """Fewer access ports than the peer-link needs is a hard error, not a silent
    partial peer-link that would leave PyAVD without mlag_interfaces."""
    gen = _make_generator()
    gen.client.filters = AsyncMock(return_value=[_iface("Ethernet1", "server")])

    with pytest.raises(ValueError, match="MLAG peer-link"):
        await gen._assign_l2leaf_mlag_peer_interfaces(_leaf("leaf-a", "leaf-pod-a-1-1"))


@pytest.mark.parametrize("value", [False, "false", "False", "0", "no", "off"])
def test_is_mlag_enabled_handles_false_values(value: object) -> None:
    assert is_mlag_enabled(value) is False


@pytest.mark.parametrize("value", [None, True, "true", "1", "yes", "on"])
def test_is_mlag_enabled_defaults_to_enabled(value: object) -> None:
    assert is_mlag_enabled(value) is True


@pytest.mark.asyncio
async def test_create_mlag_pairs_skips_when_rack_mlag_false() -> None:
    gen = _make_generator()
    gen.rack_mlag = False
    gen.rack_mlag_enabled = False

    await gen.create_mlag_pairs()

    gen.client.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_mlag_pairs_allocates_shared_asn_node() -> None:
    gen = _make_generator()
    gen.rack_mlag = True
    gen.allocate_routing_asn = AsyncMock(return_value=SimpleNamespace(id="asn-node-1"))  # type: ignore[method-assign]
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    # A single shared RoutingAsn is allocated from the fabric pool and linked to the domain.
    gen.allocate_routing_asn.assert_awaited_once_with(gen.asn_pool, gen.fabric.id)
    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="DC1_BORDER",
        asn={"id": "asn-node-1"},
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )
    mlag_domain.save.assert_awaited_once_with(allow_upsert=True)
    # Both leaves are linked to that same shared ASN node via a targeted mutation.
    assert gen.client.execute_graphql.await_count == 2
    linked_asn_ids = {call.kwargs["variables"]["asn_id"] for call in gen.client.execute_graphql.await_args_list}
    assert linked_asn_ids == {"asn-node-1"}


@pytest.mark.asyncio
async def test_mlag_enabled_leafs_do_not_allocate_device_asns() -> None:
    gen = _make_generator()
    gen.rack_mlag_enabled = True
    leaf1 = _leaf("leaf-1", "leaf-pod-a-1-1")
    leaf2 = _leaf("leaf-2", "leaf-pod-a-1-2")
    gen.create_avd_device = AsyncMock(side_effect=[leaf1, leaf2])  # type: ignore[method-assign]
    gen._share_mlag_vtep_loopback_ip = AsyncMock()  # type: ignore[method-assign]
    gen.leaf_switches = []

    await gen.create_leaf_switches()

    assert [call.kwargs["asn_pool"] for call in gen.create_avd_device.await_args_list] == [None, None]
    assert gen.leaf_switches == [leaf1, leaf2]
    gen._share_mlag_vtep_loopback_ip.assert_awaited_once_with(leaf1, leaf2)


@pytest.mark.asyncio
async def test_mlag_leaf_pairs_allocate_one_vtep_loopback_per_pair() -> None:
    gen = _make_generator()
    gen.rack_mlag_enabled = True
    gen.rack_amount_of_leafs = 4
    leafs = [_leaf(f"leaf-{idx}", f"leaf-pod-a-1-{idx}") for idx in range(1, 5)]
    gen.create_avd_device = AsyncMock(side_effect=leafs)  # type: ignore[method-assign]
    gen._share_mlag_vtep_loopback_ip = AsyncMock()  # type: ignore[method-assign]
    gen.leaf_switches = []

    await gen.create_leaf_switches()

    assert [call.kwargs["loopback_pool"] for call in gen.create_avd_device.await_args_list] == [
        gen.loopback_pool,
        gen.loopback_pool,
        gen.loopback_pool,
        gen.loopback_pool,
    ]
    assert [call.kwargs["vtep_loopback_pool"] for call in gen.create_avd_device.await_args_list] == [
        gen.vtep_loopback_pool,
        None,
        gen.vtep_loopback_pool,
        None,
    ]
    assert gen._share_mlag_vtep_loopback_ip.await_args_list[0].args == (leafs[0], leafs[1])
    assert gen._share_mlag_vtep_loopback_ip.await_args_list[1].args == (leafs[2], leafs[3])


@pytest.mark.asyncio
async def test_share_mlag_vtep_loopback_links_secondary_to_primary_ip() -> None:
    gen = _make_generator()
    primary = _leaf("leaf-1", "leaf-pod-a-1-1")
    secondary = _leaf("leaf-2", "leaf-pod-a-1-2")
    gen._device_vtep_loopback_ip_id = AsyncMock(return_value="ip-shared")  # type: ignore[method-assign]
    gen._set_device_vtep_loopback_ip = AsyncMock()  # type: ignore[method-assign]
    gen._reconcile_generated_loopback_interfaces = AsyncMock()  # type: ignore[method-assign]

    await gen._share_mlag_vtep_loopback_ip(primary, secondary)

    gen._device_vtep_loopback_ip_id.assert_awaited_once_with("leaf-1")
    gen._set_device_vtep_loopback_ip.assert_awaited_once_with("leaf-2", "ip-shared")
    gen._reconcile_generated_loopback_interfaces.assert_awaited_once_with("leaf-2", "leaf")


@pytest.mark.asyncio
async def test_share_mlag_vtep_loopback_requires_primary_ip() -> None:
    gen = _make_generator()
    gen._device_vtep_loopback_ip_id = AsyncMock(return_value=None)  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="primary leaf has no VTEP loopback IP"):
        await gen._share_mlag_vtep_loopback_ip(_leaf("leaf-1", "leaf-a"), _leaf("leaf-2", "leaf-b"))


@pytest.mark.asyncio
async def test_mlag_disabled_leafs_allocate_device_asns() -> None:
    gen = _make_generator()
    gen.rack_mlag_enabled = False
    leaf1 = _leaf("leaf-1", "leaf-pod-a-1-1")
    leaf2 = _leaf("leaf-2", "leaf-pod-a-1-2")
    gen.create_avd_device = AsyncMock(side_effect=[leaf1, leaf2])  # type: ignore[method-assign]
    gen.leaf_switches = []

    await gen.create_leaf_switches()

    assert [call.kwargs["asn_pool"] for call in gen.create_avd_device.await_args_list] == [
        gen.asn_pool,
        gen.asn_pool,
    ]


@pytest.mark.asyncio
async def test_create_mlag_pairs_reuses_existing_domain_asn() -> None:
    """A re-run must reuse the pair's existing shared RoutingAsn, not allocate a new one (FR-007)."""
    gen = _make_generator()
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(domains=[_domain("DC1_BORDER", asn_node_id="asn-existing")])
    )
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]
    mlag_domain = MagicMock()
    mlag_domain.save = AsyncMock()
    gen.client.create.return_value = mlag_domain

    await gen.create_mlag_pairs()

    gen.allocate_routing_asn.assert_not_awaited()
    gen.client.create.assert_awaited_once_with(
        "MlagDomain",
        domain_id="DC1_BORDER",
        asn={"id": "asn-existing"},
        peers=[{"id": "leaf-a"}, {"id": "leaf-b"}],
        pod={"id": "pod-1"},
    )


@pytest.mark.asyncio
async def test_get_or_allocate_mlag_asn_allocates_when_no_existing_domain() -> None:
    gen = _make_generator()
    gen.allocate_routing_asn = AsyncMock(return_value=SimpleNamespace(id="asn-new"))  # type: ignore[method-assign]

    asn_id = await gen._get_or_allocate_mlag_asn("DC1_BORDER")

    assert asn_id == "asn-new"
    gen.allocate_routing_asn.assert_awaited_once_with(gen.asn_pool, gen.fabric.id)


@pytest.mark.asyncio
async def test_get_or_allocate_mlag_asn_reuses_existing_domain_link() -> None:
    gen = _make_generator()
    gen.client.filters = AsyncMock(
        side_effect=_filters_side_effect(domains=[_domain("DC1_BORDER", asn_node_id="asn-existing")])
    )
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]

    asn_id = await gen._get_or_allocate_mlag_asn("DC1_BORDER")

    assert asn_id == "asn-existing"
    gen.allocate_routing_asn.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_stale_mlag_domains_only_deletes_current_rack_domains() -> None:
    gen = _make_generator()
    stale_primary = _domain("DC1_BORDER")
    stale_pair = _domain("DC1_BORDER-2")
    other_domain = _domain("DC1_OTHER")
    for domain in [stale_primary, stale_pair, other_domain]:
        domain.delete = AsyncMock()
    gen.client.filters = AsyncMock(return_value=[stale_primary, stale_pair, other_domain])

    await gen.delete_stale_mlag_domains()

    stale_primary.delete.assert_awaited_once()
    stale_pair.delete.assert_awaited_once()
    other_domain.delete.assert_not_awaited()


def test_rack_hostvar_target_device_ids_deduplicates_rack_and_spine_devices() -> None:
    gen = _make_generator()
    gen.leaf_switches = [_named_device("leaf-a", "leaf-a"), _named_device("leaf-b", "leaf-b")]
    gen.l2leaf_switches = [_named_device("l2leaf-a", "l2leaf-a")]
    gen.spine_switches = [_named_device("spine-a", "spine-a"), _named_device("leaf-a", "leaf-a")]

    assert gen.rack_hostvar_target_device_ids() == ["leaf-a", "leaf-b", "l2leaf-a", "spine-a"]


def _rel_peers(*peers: object) -> SimpleNamespace:
    return SimpleNamespace(fetch=AsyncMock(), peers=[SimpleNamespace(peer=peer) for peer in peers])


def _artifact_with_hostvar() -> SimpleNamespace:
    return SimpleNamespace(hostvar_file=SimpleNamespace(id="hostvar-file", fetch=AsyncMock(), peer=object()))


@pytest.mark.asyncio
async def test_hostvar_target_device_ids_uses_full_fabric_when_any_hostvars_missing() -> None:
    gen = _make_generator()
    super_spine = _named_device("super-spine", "super-spine")
    spine = _named_device("spine-a", "spine-a")
    leaf = _named_device("leaf-a", "leaf-a")
    rack = SimpleNamespace(devices=_rel_peers(leaf))
    pod = SimpleNamespace(devices=_rel_peers(super_spine, spine), racks=_rel_peers(rack))

    async def filters_side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))
        if kind_name == "NetworkPod":
            return [pod]
        if kind_name == "AvdArtifact" and kwargs.get("name__value") == "super-spine":
            return [_artifact_with_hostvar()]
        if kind_name == "AvdArtifact" and kwargs.get("name__value") == "spine-a":
            return [_artifact_with_hostvar()]
        if kind_name == "AvdArtifact" and kwargs.get("name__value") == "leaf-a":
            return []
        return []

    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    assert await gen.hostvar_target_device_ids() == ["super-spine", "spine-a", "leaf-a"]


@pytest.mark.asyncio
async def test_hostvar_target_device_ids_uses_rack_targets_when_fabric_hostvars_exist() -> None:
    gen = _make_generator()
    super_spine = _named_device("super-spine", "super-spine")
    spine = _named_device("spine-a", "spine-a")
    leaf = _named_device("leaf-a", "leaf-a")
    rack = SimpleNamespace(devices=_rel_peers(leaf))
    pod = SimpleNamespace(devices=_rel_peers(super_spine, spine), racks=_rel_peers(rack))
    gen.leaf_switches = [_named_device("leaf-a", "leaf-a")]
    gen.l2leaf_switches = []
    gen.spine_switches = [_named_device("spine-a", "spine-a")]

    async def filters_side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))
        if kind_name == "NetworkPod":
            return [pod]
        if kind_name == "AvdArtifact":
            return [_artifact_with_hostvar()]
        return []

    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    assert await gen.hostvar_target_device_ids() == ["leaf-a", "spine-a"]


@pytest.mark.asyncio
async def test_invalidate_hostvars_deletes_target_hostvar_files() -> None:
    gen = _make_generator()
    hostvar_file = SimpleNamespace(delete=AsyncMock())
    hostvar_rel = SimpleNamespace(id="hostvar-file-1", fetch=AsyncMock(), peer=hostvar_file)
    artifact = SimpleNamespace(hostvar_file=hostvar_rel)

    async def filters_side_effect(*args: object, **kwargs: object) -> list[SimpleNamespace]:
        kind = kwargs.get("kind", args[0] if args else None)
        kind_name = kind if isinstance(kind, str) else getattr(kind, "__name__", str(kind))
        if kind_name == "DcimDevice":
            return [_named_device("leaf-a", "leaf-a")]
        if kind_name == "AvdArtifact":
            return [artifact]
        return []

    gen.client.filters = AsyncMock(side_effect=filters_side_effect)

    await gen.invalidate_hostvars(["leaf-a"])

    hostvar_rel.fetch.assert_awaited_once()
    hostvar_file.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_limits_nodes() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock()

    await trigger_hostvar_generation(client, node_ids=["leaf-a", "spine-a"])

    client.execute_graphql.assert_awaited_once()
    assert client.execute_graphql.await_args.kwargs["variables"] == {
        "id": "generator-1",
        "nodes": ["leaf-a", "spine-a"],
    }


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_skips_without_node_ids() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock()

    await trigger_hostvar_generation(client)

    client.filters.assert_not_awaited()
    client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_hostvar_generation_skips_empty_node_ids() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock()

    await trigger_hostvar_generation(client, node_ids=[])

    client.filters.assert_not_awaited()
    client.execute_graphql.assert_not_awaited()
