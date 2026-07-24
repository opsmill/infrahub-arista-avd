from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from solution_arista_avd.generator import GeneratorMixin


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
    gen._activate_loopback_interface = AsyncMock(side_effect=RuntimeError("loopback failed"))  # type: ignore[method-assign]

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
    gen._activate_loopback_interface = AsyncMock(side_effect=RuntimeError("loopback failed"))  # type: ignore[method-assign]

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
