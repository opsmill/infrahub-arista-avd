from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from infrahub_sdk.exceptions import ServerNotResponsiveError

from solution_arista_avd.generator import GeneratorMixin, save_file_if_changed, trigger_hostvar_generation


def _make_generator() -> GeneratorMixin:
    gen = GeneratorMixin.__new__(GeneratorMixin)
    gen.client = MagicMock()
    gen.client.filters = AsyncMock(return_value=[])
    gen.client.create = AsyncMock()
    gen.client.execute_graphql = AsyncMock()
    gen.client.get = AsyncMock()
    return gen


def _device(device_id: str = "device-1", *, asn_id: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(id=device_id, save=AsyncMock(), delete=AsyncMock(), asn=SimpleNamespace(id=asn_id))


def _device_with_relationships(
    device_id: str = "device-1",
    *,
    serial: str | None = None,
    status: str | None = None,
    role: str | None = None,
    node_id: int | None = None,
    mgmt_ip_id: str | None = None,
    group_ids: list[str] | None = None,
    asn_id: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=device_id,
        name=SimpleNamespace(value="leaf-a"),
        serial=SimpleNamespace(value=serial),
        status=SimpleNamespace(value=status),
        role=SimpleNamespace(value=role),
        index=SimpleNamespace(value=None),
        object_template=SimpleNamespace(id=None, node=None),
        pod=SimpleNamespace(id=None, node=None),
        rack=SimpleNamespace(id=None, node=None),
        mgmt_ip=SimpleNamespace(id=mgmt_ip_id, node=SimpleNamespace(id=mgmt_ip_id) if mgmt_ip_id else None),
        node_id=SimpleNamespace(value=node_id),
        loopback_ip=SimpleNamespace(id=None, node=None),
        vtep_loopback_ip=SimpleNamespace(id=None, node=None),
        asn=SimpleNamespace(id=asn_id, node=SimpleNamespace(id=asn_id) if asn_id else None),
        member_of_groups=SimpleNamespace(
            peers=[
                SimpleNamespace(peer=SimpleNamespace(id=group_id, name=SimpleNamespace(value=group_id)))
                for group_id in group_ids or []
            ]
        ),
        save=AsyncMock(),
        delete=AsyncMock(),
    )


def _interface(kind: str = "InterfacePhysical") -> SimpleNamespace:
    return SimpleNamespace(
        delete=AsyncMock(),
        get_kind=MagicMock(return_value=kind),
    )


def _resource(resource_id: str) -> SimpleNamespace:
    return SimpleNamespace(node=SimpleNamespace(id=resource_id))


def test_relationship_node_id_detects_missing_and_populated_relationships() -> None:
    assert GeneratorMixin._relationship_node_id(None) is None
    assert GeneratorMixin._relationship_node_id(SimpleNamespace(id=None, node=None)) is None
    assert GeneratorMixin._relationship_node_id(SimpleNamespace(id="rel-1", node=None)) == "rel-1"
    assert GeneratorMixin._relationship_node_id(SimpleNamespace(node=SimpleNamespace(id="node-1"))) == "node-1"


def test_non_empty_value_detects_missing_and_populated_attributes() -> None:
    assert GeneratorMixin._has_non_empty_value(None) is False
    assert GeneratorMixin._has_non_empty_value(SimpleNamespace(value=None)) is False
    assert GeneratorMixin._has_non_empty_value(SimpleNamespace(value="")) is False
    assert GeneratorMixin._has_non_empty_value(SimpleNamespace(value="SERIAL1")) is True


@pytest.mark.asyncio
async def test_save_file_if_changed_skips_matching_existing_content() -> None:
    existing_file = MagicMock()
    existing_file.save = AsyncMock()
    create_file = AsyncMock()

    uploaded = await save_file_if_changed(
        existing_file=existing_file,
        existing_checksum="checksum-1",
        new_checksum="checksum-1",
        new_content=b"{}",
        filename="leaf-1-hostvars.json",
        create_file=create_file,
    )

    assert uploaded is False
    existing_file.upload_from_bytes.assert_not_called()
    existing_file.save.assert_not_awaited()
    create_file.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_file_if_changed_uploads_existing_file_when_content_differs() -> None:
    existing_file = MagicMock()
    existing_file.save = AsyncMock()

    uploaded = await save_file_if_changed(
        existing_file=existing_file,
        existing_checksum="checksum-1",
        new_checksum="checksum-2",
        new_content=b'{"changed": true}',
        filename="leaf-1-hostvars.json",
        create_file=AsyncMock(),
    )

    assert uploaded is True
    existing_file.upload_from_bytes.assert_called_once_with(content=b'{"changed": true}', name="leaf-1-hostvars.json")
    existing_file.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)


@pytest.mark.asyncio
async def test_save_file_if_changed_creates_missing_file() -> None:
    new_file = MagicMock()
    new_file.save = AsyncMock()
    create_file = AsyncMock(return_value=new_file)

    uploaded = await save_file_if_changed(
        existing_file=None,
        existing_checksum=None,
        new_checksum="checksum-1",
        new_content=b"{}",
        filename="leaf-1-structured-config.json",
        create_file=create_file,
    )

    assert uploaded is True
    create_file.assert_awaited_once()
    new_file.upload_from_bytes.assert_called_once_with(content=b"{}", name="leaf-1-structured-config.json")
    new_file.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)


@pytest.mark.asyncio
async def test_create_avd_device_deletes_new_device_when_asn_allocation_fails() -> None:
    gen = _make_generator()
    device = _device()
    gen.client.create.return_value = device
    gen._ensure_device_asn = AsyncMock(side_effect=RuntimeError("asn allocation failed"))  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="asn allocation failed"):
        await gen.create_avd_device(
            name="spine-a",
            role="spine",
            object_template_id="template-1",
            pod_id="pod-1",
            fabric_id="fabric-1",
            asn_pool=object(),
        )

    device.save.assert_awaited_once_with(allow_upsert=True)
    device.delete.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_create_avd_device_does_not_delete_existing_device_when_post_save_step_fails() -> None:
    gen = _make_generator()
    gen.client.filters.return_value = [SimpleNamespace(id="existing-device")]
    device = _device()
    gen.client.create.return_value = device
    gen._reconcile_generated_loopback_interfaces = AsyncMock(side_effect=RuntimeError("loopback failed"))  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="loopback failed"):
        await gen.create_avd_device(
            name="spine-a",
            role="spine",
            object_template_id="template-1",
            pod_id="pod-1",
            fabric_id="fabric-1",
            loopback_pool=object(),
        )

    device.save.assert_awaited_once_with(allow_upsert=True)
    device.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_avd_device_deletes_new_asn_when_later_step_fails() -> None:
    gen = _make_generator()
    device = _device()
    routing_asn = SimpleNamespace(id="asn-1", delete=AsyncMock())
    gen.client.create.return_value = device
    gen._ensure_device_asn = AsyncMock(return_value=routing_asn)  # type: ignore[method-assign]
    gen._reconcile_generated_loopback_interfaces = AsyncMock(side_effect=RuntimeError("loopback failed"))  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="loopback failed"):
        await gen.create_avd_device(
            name="spine-a",
            role="spine",
            object_template_id="template-1",
            pod_id="pod-1",
            fabric_id="fabric-1",
            asn_pool=object(),
            loopback_pool=object(),
        )

    device.delete.assert_awaited_once_with()
    routing_asn.delete.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_create_avd_device_allocates_vtep_loopback_for_leaf_roles_only() -> None:
    gen = _make_generator()
    leaf = _device("leaf-1")
    spine = _device("spine-1")
    gen.client.create.side_effect = [leaf, spine]
    gen._reconcile_generated_loopback_interfaces = AsyncMock()  # type: ignore[method-assign]

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        loopback_pool=object(),
        vtep_loopback_pool="vtep-pool",  # type: ignore[arg-type]
    )
    await gen.create_avd_device(
        name="spine-a",
        role="spine",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        loopback_pool=object(),
        vtep_loopback_pool="vtep-pool",  # type: ignore[arg-type]
    )

    leaf_kwargs = gen.client.create.await_args_list[0].kwargs
    spine_kwargs = gen.client.create.await_args_list[1].kwargs
    assert leaf_kwargs["vtep_loopback_ip"] == "vtep-pool"
    assert "vtep_loopback_ip" not in spine_kwargs


@pytest.mark.asyncio
async def test_create_avd_device_preserves_existing_non_empty_serial() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships(serial="SERIAL1")
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
    )

    assert "serial" not in gen.client.create.await_args.kwargs
    gen.client.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_avd_device_preserves_existing_non_empty_mgmt_ip() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships(mgmt_ip_id="mgmt-existing")
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        mgmt_pool="mgmt-pool",  # type: ignore[arg-type]
    )

    assert "mgmt_ip" not in gen.client.create.await_args.kwargs


@pytest.mark.asyncio
async def test_create_avd_device_populates_missing_generated_relationships() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships()
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device
    gen._ensure_device_asn = AsyncMock()  # type: ignore[method-assign]
    gen._reconcile_generated_loopback_interfaces = AsyncMock()  # type: ignore[method-assign]

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        loopback_pool="loopback-pool",  # type: ignore[arg-type]
        vtep_loopback_pool="vtep-pool",  # type: ignore[arg-type]
        asn_pool="asn-pool",  # type: ignore[arg-type]
        node_id_pool="node-id-pool",  # type: ignore[arg-type]
        mgmt_pool="mgmt-pool",  # type: ignore[arg-type]
    )

    kwargs = gen.client.create.await_args.kwargs
    assert kwargs["mgmt_ip"] == "mgmt-pool"
    assert kwargs["node_id"] == "node-id-pool"
    assert kwargs["loopback_ip"] == "loopback-pool"
    assert kwargs["vtep_loopback_ip"] == "vtep-pool"
    gen._ensure_device_asn.assert_awaited_once_with("device-1", "asn-pool", "fabric-1")
    gen._reconcile_generated_loopback_interfaces.assert_awaited_once_with("device-1", "leaf")


@pytest.mark.asyncio
async def test_create_avd_device_includes_preserved_required_attributes_without_reallocating_node_id() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships(status="active", role="spine", node_id=7)
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        node_id_pool="node-id-pool",  # type: ignore[arg-type]
    )

    kwargs = gen.client.create.await_args.kwargs
    assert kwargs["status"] == "active"
    assert kwargs["role"] == "spine"
    assert "node_id" not in kwargs


@pytest.mark.asyncio
async def test_create_avd_device_backfills_missing_template_physical_interfaces() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships()
    saved_device = _device()
    created_interface = SimpleNamespace(save=AsyncMock())
    template_interface_existing = SimpleNamespace(
        name=SimpleNamespace(value="Ethernet1"),
        status=SimpleNamespace(value="active"),
        role=SimpleNamespace(value="server"),
        mtu=SimpleNamespace(value=1500),
        description=SimpleNamespace(value=""),
        l2_mode=SimpleNamespace(value=""),
        dot1q_id=SimpleNamespace(value=""),
        mac_address=SimpleNamespace(value=""),
        index=SimpleNamespace(value=None),
    )
    template_interface_missing = SimpleNamespace(
        name=SimpleNamespace(value="Ethernet2"),
        status=SimpleNamespace(value="active"),
        role=SimpleNamespace(value="spine"),
        mtu=SimpleNamespace(value=9200),
        description=SimpleNamespace(value="uplink"),
        l2_mode=SimpleNamespace(value=""),
        dot1q_id=SimpleNamespace(value=""),
        mac_address=SimpleNamespace(value=""),
        index=SimpleNamespace(value=None),
    )
    existing_interface = SimpleNamespace(name=SimpleNamespace(value="Ethernet1"))
    gen.client.filters.side_effect = [
        [SimpleNamespace(id="device-1")],
        [template_interface_existing, template_interface_missing],
        [existing_interface],
    ]
    gen.client.get.return_value = existing_device
    gen.client.create.side_effect = [saved_device, created_interface]

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
    )

    assert gen.client.create.await_args_list[1].args[0].__name__ == "InterfacePhysical"
    assert gen.client.create.await_args_list[1].kwargs == {
        "name": "Ethernet2",
        "device": {"id": "device-1"},
        "status": "active",
        "role": "spine",
        "mtu": 9200,
        "description": "uplink",
    }
    created_interface.save.assert_awaited_once_with(allow_upsert=True)


@pytest.mark.asyncio
async def test_create_avd_device_adds_avd_group_without_removing_existing_groups() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships(group_ids=["ops-group"])
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
    )

    assert gen.client.create.await_args.kwargs["member_of_groups"] == [{"id": "ops-group"}, "avd_devices"]


@pytest.mark.asyncio
async def test_create_avd_device_logs_preserved_populated_and_skipped_field_decisions() -> None:
    gen = _make_generator()
    existing_device = _device_with_relationships(serial="SERIAL1", mgmt_ip_id="mgmt-existing")
    saved_device = _device()
    gen.client.filters.return_value = [SimpleNamespace(id="device-1")]
    gen.client.get.return_value = existing_device
    gen.client.create.return_value = saved_device
    gen.logger = MagicMock()

    await gen.create_avd_device(
        name="leaf-a",
        role="leaf",
        object_template_id="template-1",
        pod_id="pod-1",
        fabric_id="fabric-1",
        mgmt_pool="mgmt-pool",  # type: ignore[arg-type]
    )

    logged_args = [call.args for call in gen.logger.info.call_args_list]
    assert any("preserved" in args for args in logged_args)
    assert any("populated" in args for args in logged_args)
    assert any("skipped" in args for args in logged_args)


@pytest.mark.asyncio
async def test_ensure_virtual_loopback_replaces_stale_physical_interface() -> None:
    gen = _make_generator()
    stale_physical = _interface("InterfacePhysical")
    virtual = SimpleNamespace(save=AsyncMock())
    gen.client.filters.return_value = [stale_physical]
    gen.client.create.return_value = virtual

    await gen._ensure_virtual_loopback_interface(
        device_id="device-1",
        name="Loopback0",
        role="loopback",
        ip_address_id="ip-1",
    )

    stale_physical.delete.assert_awaited_once_with()
    assert gen.client.create.await_args.args[0].__name__ == "InterfaceVirtual"
    assert gen.client.create.await_args.kwargs["name"] == "Loopback0"
    assert gen.client.create.await_args.kwargs["role"] == "loopback"
    assert gen.client.create.await_args.kwargs["device"] == {"id": "device-1"}
    assert virtual.ip_address == "ip-1"
    virtual.save.assert_awaited_once_with(allow_upsert=True)


@pytest.mark.asyncio
async def test_ensure_vtep_loopback_address_pool_uses_prefix_pool_resources() -> None:
    gen = _make_generator()
    address_pool = SimpleNamespace(save=AsyncMock())
    gen.client.create.return_value = address_pool
    prefix_pool = SimpleNamespace(resources=SimpleNamespace(edges=[_resource("prefix-1"), _resource("prefix-2")]))

    result = await gen._ensure_vtep_loopback_address_pool(
        fabric_name="fabric-l3ls-multipod-a",
        vtep_prefix_pool_ref=prefix_pool,
    )

    assert result == address_pool
    gen.client.create.assert_awaited_once()
    assert gen.client.create.await_args.kwargs["name"] == "fabric-l3ls-multipod-a-vtep-loopback-address-pool"
    assert gen.client.create.await_args.kwargs["resources"] == [{"id": "prefix-1"}, {"id": "prefix-2"}]
    address_pool.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)


@pytest.mark.asyncio
async def test_resolve_avd_pools_creates_loopback_and_vtep_address_pools_from_fabric_prefix_pools() -> None:
    gen = _make_generator()
    loopback_address_pool = SimpleNamespace(save=AsyncMock())
    vtep_address_pool = SimpleNamespace(save=AsyncMock())
    gen.client.create.side_effect = [loopback_address_pool, vtep_address_pool]
    loopback_prefix_pool = SimpleNamespace(resources=SimpleNamespace(edges=[_resource("loopback-prefix")]))
    vtep_prefix_pool = SimpleNamespace(resources=SimpleNamespace(edges=[_resource("vtep-prefix")]))
    fabric = SimpleNamespace(
        name=SimpleNamespace(value="Fabric-L3LS-MultiPod-A"),
        asn_pool=SimpleNamespace(node=None),
        node_id_pool=SimpleNamespace(node=None),
        mgmt_pool=SimpleNamespace(node=None),
        loopback_pool=SimpleNamespace(node=loopback_prefix_pool),
        vtep_pool=SimpleNamespace(node=vtep_prefix_pool),
    )

    result = await gen.resolve_avd_pools(fabric)

    assert result == (None, None, None, loopback_address_pool, vtep_address_pool)
    assert [call.kwargs["name"] for call in gen.client.create.await_args_list] == [
        "fabric-l3ls-multipod-a-loopback-address-pool",
        "fabric-l3ls-multipod-a-vtep-loopback-address-pool",
    ]
    assert gen.client.create.await_args_list[0].kwargs["resources"] == [{"id": "loopback-prefix"}]
    assert gen.client.create.await_args_list[1].kwargs["resources"] == [{"id": "vtep-prefix"}]
    loopback_address_pool.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
    vtep_address_pool.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)


@pytest.mark.asyncio
async def test_set_device_vtep_loopback_ip_uses_targeted_mutation() -> None:
    gen = _make_generator()

    await gen._set_device_vtep_loopback_ip("device-1", "ip-1")

    gen.client.execute_graphql.assert_awaited_once()
    assert "vtep_loopback_ip" in gen.client.execute_graphql.await_args.kwargs["query"]
    assert gen.client.execute_graphql.await_args.kwargs["variables"] == {
        "id": "device-1",
        "ip_address_id": "ip-1",
    }


@pytest.mark.asyncio
async def test_ensure_device_asn_deletes_new_asn_when_device_link_save_fails() -> None:
    gen = _make_generator()
    device = _device()
    device.save.side_effect = RuntimeError("device link failed")
    routing_asn = SimpleNamespace(id="asn-1", delete=AsyncMock())
    gen.client.get.return_value = device
    gen.allocate_routing_asn = AsyncMock(return_value=routing_asn)  # type: ignore[method-assign]

    with pytest.raises(RuntimeError, match="device link failed"):
        await gen._ensure_device_asn("device-1", object(), "fabric-1")  # type: ignore[arg-type]

    gen.allocate_routing_asn.assert_awaited_once()
    assert device.asn == "asn-1"
    routing_asn.delete.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_ensure_shared_device_asn_allocates_one_asn_for_unlinked_devices() -> None:
    gen = _make_generator()
    devices = [_device("device-1"), _device("device-2")]
    fetched_devices = [_device("device-1"), _device("device-2")]
    routing_asn = SimpleNamespace(id="asn-shared", delete=AsyncMock())
    gen.client.get.side_effect = fetched_devices
    gen.allocate_routing_asn = AsyncMock(return_value=routing_asn)  # type: ignore[method-assign]

    result = await gen.ensure_shared_device_asn(devices, object(), "fabric-1")  # type: ignore[arg-type]

    assert result == routing_asn
    gen.allocate_routing_asn.assert_awaited_once()
    assert [call.kwargs["variables"] for call in gen.client.execute_graphql.await_args_list] == [
        {"id": "device-1", "asn_id": "asn-shared"},
        {"id": "device-2", "asn_id": "asn-shared"},
    ]


@pytest.mark.asyncio
async def test_ensure_shared_device_asn_reuses_first_existing_asn_in_device_order() -> None:
    gen = _make_generator()
    devices = [_device("device-1"), _device("device-2"), _device("device-3")]
    fetched_devices = [_device("device-1"), _device("device-2", asn_id="asn-existing"), _device("device-3")]
    gen.client.get.side_effect = fetched_devices
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]

    result = await gen.ensure_shared_device_asn(devices, object(), "fabric-1")  # type: ignore[arg-type]

    assert result is None
    gen.allocate_routing_asn.assert_not_awaited()
    assert [call.kwargs["variables"] for call in gen.client.execute_graphql.await_args_list] == [
        {"id": "device-1", "asn_id": "asn-existing"},
        {"id": "device-3", "asn_id": "asn-existing"},
    ]


@pytest.mark.asyncio
async def test_ensure_shared_device_asn_relinks_mixed_old_state_to_first_existing_asn() -> None:
    gen = _make_generator()
    devices = [_device("device-1"), _device("device-2"), _device("device-3")]
    fetched_devices = [
        _device("device-1", asn_id="asn-first"),
        _device("device-2", asn_id="asn-old"),
        _device("device-3"),
    ]
    gen.client.get.side_effect = fetched_devices
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]

    result = await gen.ensure_shared_device_asn(devices, object(), "fabric-1")  # type: ignore[arg-type]

    assert result is None
    gen.allocate_routing_asn.assert_not_awaited()
    assert [call.kwargs["variables"] for call in gen.client.execute_graphql.await_args_list] == [
        {"id": "device-2", "asn_id": "asn-first"},
        {"id": "device-3", "asn_id": "asn-first"},
    ]


@pytest.mark.asyncio
async def test_ensure_shared_device_asn_noops_when_all_devices_already_share_asn() -> None:
    gen = _make_generator()
    devices = [_device("device-1"), _device("device-2")]
    fetched_devices = [_device("device-1", asn_id="asn-shared"), _device("device-2", asn_id="asn-shared")]
    gen.client.get.side_effect = fetched_devices
    gen.allocate_routing_asn = AsyncMock()  # type: ignore[method-assign]

    result = await gen.ensure_shared_device_asn(devices, object(), "fabric-1")  # type: ignore[arg-type]

    assert result is None
    gen.allocate_routing_asn.assert_not_awaited()
    gen.client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_generator_raises_when_definition_is_missing() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[])
    client.execute_graphql = AsyncMock()

    with pytest.raises(ValueError, match="CoreGeneratorDefinition 'generate-avd-device-hostvar'"):
        await trigger_hostvar_generation(client, node_ids=["device-1"])

    client.execute_graphql.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_generator_passes_timeout_to_graphql() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock()

    await trigger_hostvar_generation(client, node_ids=["device-1"], timeout=300)

    assert client.execute_graphql.await_args.kwargs["timeout"] == 300
    assert client.execute_graphql.await_args.kwargs["variables"] == {
        "id": "generator-1",
        "nodes": ["device-1"],
    }


@pytest.mark.asyncio
async def test_trigger_generator_tolerates_server_timeout_when_enabled() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock(side_effect=ServerNotResponsiveError(url="http://infrahub", timeout=300))

    await trigger_hostvar_generation(
        client,
        node_ids=["device-1"],
        timeout=300,
        tolerate_timeout=True,
    )

    client.execute_graphql.assert_awaited_once()


@pytest.mark.asyncio
async def test_trigger_generator_does_not_tolerate_server_timeout_by_default() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock(side_effect=ServerNotResponsiveError(url="http://infrahub", timeout=300))

    with pytest.raises(ServerNotResponsiveError):
        await trigger_hostvar_generation(client, node_ids=["device-1"], timeout=300)


@pytest.mark.asyncio
async def test_trigger_generator_tolerant_mode_propagates_non_timeout_errors() -> None:
    client = MagicMock()
    client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-1")])
    client.execute_graphql = AsyncMock(side_effect=RuntimeError("graphql failed"))

    with pytest.raises(RuntimeError, match="graphql failed"):
        await trigger_hostvar_generation(
            client,
            node_ids=["device-1"],
            timeout=300,
            tolerate_timeout=True,
        )
