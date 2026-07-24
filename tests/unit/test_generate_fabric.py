from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import generators.generate_fabric as generate_fabric_module
from generators.generate_fabric import FabricGenerator
from generators.generate_pod import PodGenerator


def _make_generator() -> FabricGenerator:
    gen = FabricGenerator.__new__(FabricGenerator)
    gen.client = MagicMock()
    gen.client.get = AsyncMock()
    gen.client.execute_graphql = AsyncMock()
    gen.logger = MagicMock()
    return gen


def _pod_query_data(*, amount_of_super_spines: int) -> dict:
    return {
        "NetworkPod": {
            "edges": [
                {
                    "node": {
                        "id": "pod-1",
                        "amount_of_spines": {"value": 2},
                        "name": {"value": "infrahub-dc1"},
                        "checksum": {"value": "old-checksum"},
                        "index": {"value": 1},
                        "role": {"value": "cpu"},
                        "spine_switch_template": {"node": {"__typename": "TemplateDcimDevice", "id": "spine-template"}},
                        "parent": {
                            "node": {
                                "__typename": "NetworkFabric",
                                "id": "fabric-1",
                                "name": {"value": "INFRAHUB_AVD"},
                                "amount_of_super_spines": {"value": amount_of_super_spines},
                                "underlay_routing_protocol": {"value": "ebgp"},
                                "fabric_interface_sorting_method": {"value": "create_sorted_device_interface_map"},
                                "spine_interface_sorting_method": {"value": "create_sorted_device_interface_map"},
                                "asn_pool": {"node": None},
                                "node_id_pool": {"node": None},
                                "mgmt_pool": {"node": None},
                            }
                        },
                    }
                }
            ]
        }
    }


def _fabric_query_data(*, amount_of_super_spines: int, template_id: str | None) -> dict:
    template_node = {"__typename": "TemplateDcimDevice", "id": template_id} if template_id else None
    return {
        "NetworkFabric": {
            "edges": [
                {
                    "node": {
                        "id": "fabric-1",
                        "name": {"value": "INFRAHUB_AVD"},
                        "amount_of_super_spines": {"value": amount_of_super_spines},
                        "super_spine_switch_template": {"node": template_node},
                        "mgmt_gateway": {"value": None},
                        "asn_pool": {"node": None},
                        "node_id_pool": {"node": None},
                        "mgmt_pool": {"node": None},
                    }
                }
            ]
        }
    }


def _make_pod_generator() -> PodGenerator:
    gen = PodGenerator.__new__(PodGenerator)
    gen.client = MagicMock()
    gen.client.execute_graphql = AsyncMock()
    gen.logger = MagicMock()
    gen.allocate_resource_pools = AsyncMock()  # type: ignore[method-assign]
    gen.create_spine_switches = AsyncMock()  # type: ignore[method-assign]
    gen.connect_spine_to_super_spine = AsyncMock()  # type: ignore[method-assign]
    gen.get_super_spine_switches_for_fabric = AsyncMock()  # type: ignore[method-assign]
    gen.update_checksum = AsyncMock()  # type: ignore[method-assign]
    return gen


class TestFabricGenerator:
    @pytest.mark.asyncio
    async def test_zero_super_spines_does_not_require_template(self, monkeypatch: pytest.MonkeyPatch) -> None:
        gen = _make_generator()
        gen.resolve_avd_pools = AsyncMock(return_value=(None, None, None))  # type: ignore[method-assign]
        gen.allocate_resource_pools = AsyncMock()  # type: ignore[method-assign]
        gen.create_super_spine_switches = AsyncMock()  # type: ignore[method-assign]
        gen.update_checksum = AsyncMock()  # type: ignore[method-assign]
        set_ready = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "set_fabric_avd_hostvars_ready", set_ready)

        await gen.generate(_fabric_query_data(amount_of_super_spines=0, template_id=None))

        assert gen.fabric_super_spine_switch_template is None
        gen.create_super_spine_switches.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_zero_super_spines_does_not_require_fabric_pod(self) -> None:
        gen = _make_generator()
        gen.amount_of_super_spines = 0
        gen.fabric_name = "fabric-dc1"

        await gen.create_super_spine_switches()

        gen.client.get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_nonzero_super_spines_require_template(self) -> None:
        gen = _make_generator()
        gen.amount_of_super_spines = 1
        gen.fabric_name = "fabric-dc1"
        gen.fabric_super_spine_switch_template = None

        with pytest.raises(ValueError, match="no super-spine switch template defined"):
            await gen.create_super_spine_switches()

        gen.client.get.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_checksum_does_not_track_preseeded_pods(self) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.calculate_checksum = MagicMock(return_value="new-checksum")  # type: ignore[method-assign]

        changed_pod = MagicMock()
        changed_pod.name.value = "pod-1"
        changed_pod.checksum.value = "old-checksum"
        changed_pod.save = AsyncMock()
        unchanged_pod = MagicMock()
        unchanged_pod.name.value = "pod-2"
        unchanged_pod.checksum.value = "new-checksum"
        unchanged_pod.save = AsyncMock()
        gen.client.filters = AsyncMock(return_value=[changed_pod, unchanged_pod])

        await gen.update_checksum()

        changed_pod.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
        unchanged_pod.save.assert_not_awaited()


class TestPodGenerator:
    @pytest.mark.asyncio
    async def test_zero_super_spines_does_not_require_fabric_pod(self) -> None:
        gen = _make_pod_generator()

        await gen.generate(_pod_query_data(amount_of_super_spines=0))

        gen.get_super_spine_switches_for_fabric.assert_not_awaited()
        gen.connect_spine_to_super_spine.assert_not_awaited()
        gen.create_spine_switches.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_checksum_does_not_track_preseeded_racks(self) -> None:
        gen = PodGenerator.__new__(PodGenerator)
        gen.client = MagicMock()
        gen.logger = MagicMock()
        gen.pod_id = "pod-1"
        gen.calculate_checksum = MagicMock(return_value="new-checksum")  # type: ignore[method-assign]

        changed_rack = MagicMock()
        changed_rack.name.value = "rack-1"
        changed_rack.checksum.value = "old-checksum"
        changed_rack.save = AsyncMock()
        unchanged_rack = MagicMock()
        unchanged_rack.name.value = "rack-2"
        unchanged_rack.checksum.value = "new-checksum"
        unchanged_rack.save = AsyncMock()
        gen.client.filters = AsyncMock(return_value=[changed_rack, unchanged_rack])

        await gen.update_checksum()

        changed_rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
        unchanged_rack.save.assert_not_awaited()
