from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

import generators.generate_fabric as generate_fabric_module
import generators.generate_pod as generate_pod_module
from generators.generate_fabric import FabricGenerator
from generators.generate_pod import PodGenerator
from generators.generation_state import FabricAvdGenerationState, trigger_hostvar_generation


def _attr(value: Any) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _rel_set(id_: str = "rel-1") -> SimpleNamespace:
    return SimpleNamespace(id=id_)


def _device(id_: str, role: str, *, complete: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        role=_attr(role),
        bgp_asn=_attr(65001 if complete else None),
        node_id=_attr(1 if complete else None),
        loopback_ip=_rel_set("loopback-1") if complete else None,
        mgmt_ip=_rel_set("mgmt-1") if complete else None,
    )


def _pod(
    id_: str = "pod-1",
    *,
    role: str = "cpu",
    checksum: str = "new-checksum",
    pools: bool = True,
    spines: int = 2,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        name=_attr(id_),
        role=_attr(role),
        checksum=_attr(checksum),
        amount_of_spines=_attr(spines),
        prefix_pool=_rel_set("prefix-1") if pools else None,
        loopback_pool=_rel_set("loopback-pool-1") if pools else None,
    )


def _rack(
    id_: str = "rack-1",
    *,
    checksum: str = "new-checksum",
    complete: bool = True,
    leafs: int = 2,
    l2leafs: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=id_,
        name=_attr(id_),
        checksum=_attr(checksum),
        generation_complete=_attr(complete),
        amount_of_leafs=_attr(leafs),
        amount_of_l2leafs=_attr(l2leafs),
    )


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
    gen.update_checksum = AsyncMock(return_value=[])  # type: ignore[method-assign]
    gen.recover_preseeded_racks = AsyncMock()  # type: ignore[method-assign]
    return gen


class TestTargetedGeneratorTriggers:
    @pytest.mark.asyncio
    async def test_targeted_generator_helper_sends_nodes(self) -> None:
        client = MagicMock()
        client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-def-1")])
        client.execute_graphql = AsyncMock()

        await trigger_hostvar_generation(client, nodes=["device-1", "device-2"])

        client.execute_graphql.assert_awaited_once()
        _, kwargs = client.execute_graphql.await_args
        assert "nodes: $nodes" in kwargs["query"]
        assert kwargs["variables"] == {"id": "generator-def-1", "nodes": ["device-1", "device-2"]}

    @pytest.mark.asyncio
    async def test_global_generator_helper_omits_nodes_by_default(self) -> None:
        client = MagicMock()
        client.filters = AsyncMock(return_value=[SimpleNamespace(id="generator-def-1")])
        client.execute_graphql = AsyncMock()

        await trigger_hostvar_generation(client)

        client.execute_graphql.assert_awaited_once()
        _, kwargs = client.execute_graphql.await_args
        assert "nodes" not in kwargs["query"]
        assert kwargs["variables"] == {"id": "generator-def-1"}


class TestFabricGenerator:
    @pytest.mark.asyncio
    async def test_zero_super_spines_does_not_require_template(self, monkeypatch: pytest.MonkeyPatch) -> None:
        gen = _make_generator()
        gen.resolve_avd_pools = AsyncMock(return_value=(None, None, None))  # type: ignore[method-assign]
        gen.allocate_resource_pools = AsyncMock()  # type: ignore[method-assign]
        gen.create_super_spine_switches = AsyncMock()  # type: ignore[method-assign]
        gen.update_checksum = AsyncMock(return_value=[])  # type: ignore[method-assign]
        gen.recover_preseeded_state = AsyncMock()  # type: ignore[method-assign]
        set_ready = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "set_fabric_avd_hostvars_ready", set_ready)

        await gen.generate(_fabric_query_data(amount_of_super_spines=0, template_id=None))

        assert gen.fabric_super_spine_switch_template is None
        gen.create_super_spine_switches.assert_awaited_once()
        gen.recover_preseeded_state.assert_awaited_once_with(changed_pod_ids=[])

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
        changed_pod.id = "pod-1"
        changed_pod.name.value = "pod-1"
        changed_pod.checksum.value = "old-checksum"
        changed_pod.save = AsyncMock()
        unchanged_pod = MagicMock()
        unchanged_pod.id = "pod-2"
        unchanged_pod.name.value = "pod-2"
        unchanged_pod.checksum.value = "new-checksum"
        unchanged_pod.save = AsyncMock()
        gen.client.filters = AsyncMock(return_value=[changed_pod, unchanged_pod])

        changed_pod_ids = await gen.update_checksum()

        assert changed_pod_ids == ["pod-1"]
        changed_pod.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
        unchanged_pod.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fabric_does_not_directly_recover_when_pods_changed_checksum(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"
        get_pods = AsyncMock(return_value=["pod-2"])
        trigger_pods = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "get_pods_needing_generation", get_pods)
        monkeypatch.setattr(generate_fabric_module, "trigger_pod_generation", trigger_pods)

        await gen.recover_preseeded_state(changed_pod_ids=["pod-1"])

        get_pods.assert_not_awaited()
        trigger_pods.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fabric_triggers_pod_generation_for_unchanged_pod_missing_pools(self) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"

        async def filters(**kwargs: Any) -> list[SimpleNamespace]:
            if kwargs.get("kind") == "NetworkPod":
                return [_pod("pod-1", pools=False)]
            return [SimpleNamespace(id="generate-pod-def")]

        gen.client.filters = AsyncMock(side_effect=filters)

        await gen.recover_preseeded_state(changed_pod_ids=[])

        gen.client.execute_graphql.assert_awaited_once()
        _, kwargs = gen.client.execute_graphql.await_args
        assert kwargs["variables"] == {"id": "generate-pod-def", "nodes": ["pod-1"]}

    @pytest.mark.asyncio
    async def test_fabric_triggers_pod_generation_when_child_rack_needs_reconciliation(self) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"

        async def filters(**kwargs: Any) -> list[SimpleNamespace]:
            kind = kwargs.get("kind")
            if kind == "NetworkPod":
                return [_pod("pod-1", pools=True)]
            if kind == "LocationRack":
                return [_rack("rack-1", complete=False)]
            if kind == "CoreGeneratorDefinition":
                return [SimpleNamespace(id="generate-pod-def")]
            return [_device("spine-1", "spine"), _device("spine-2", "spine")]

        gen.client.filters = AsyncMock(side_effect=filters)

        await gen.recover_preseeded_state(changed_pod_ids=[])

        gen.client.execute_graphql.assert_awaited_once()
        _, kwargs = gen.client.execute_graphql.await_args
        assert kwargs["variables"] == {"id": "generate-pod-def", "nodes": ["pod-1"]}

    @pytest.mark.asyncio
    async def test_fabric_triggers_hostvar_generation_when_topology_complete_but_hostvars_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"
        monkeypatch.setattr(generate_fabric_module, "get_pods_needing_generation", AsyncMock(return_value=[]))
        monkeypatch.setattr(
            generate_fabric_module,
            "get_fabric_avd_generation_state",
            AsyncMock(return_value=FabricAvdGenerationState(["dev-1"], ["dev-1"], [])),
        )
        hostvar_trigger = AsyncMock()
        structured_trigger = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "trigger_hostvar_generation", hostvar_trigger)
        monkeypatch.setattr(generate_fabric_module, "trigger_structured_config_generation", structured_trigger)

        await gen.recover_preseeded_state(changed_pod_ids=[])

        hostvar_trigger.assert_awaited_once_with(gen.client, nodes=["dev-1"])
        structured_trigger.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fabric_triggers_structured_config_when_hostvars_exist_but_structured_configs_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"
        monkeypatch.setattr(generate_fabric_module, "get_pods_needing_generation", AsyncMock(return_value=[]))
        monkeypatch.setattr(
            generate_fabric_module,
            "get_fabric_avd_generation_state",
            AsyncMock(return_value=FabricAvdGenerationState(["dev-1"], [], ["dev-1"])),
        )
        hostvar_trigger = AsyncMock()
        structured_trigger = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "trigger_hostvar_generation", hostvar_trigger)
        monkeypatch.setattr(generate_fabric_module, "trigger_structured_config_generation", structured_trigger)

        await gen.recover_preseeded_state(changed_pod_ids=[])

        hostvar_trigger.assert_not_awaited()
        structured_trigger.assert_awaited_once_with(gen.client, nodes=["fabric-1"])

    @pytest.mark.asyncio
    async def test_fabric_triggers_nothing_when_topology_and_avd_state_are_complete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gen = _make_generator()
        gen.fabric_id = "fabric-1"
        gen.fabric_name = "infrahub_avd"
        monkeypatch.setattr(generate_fabric_module, "get_pods_needing_generation", AsyncMock(return_value=[]))
        monkeypatch.setattr(
            generate_fabric_module,
            "get_fabric_avd_generation_state",
            AsyncMock(return_value=FabricAvdGenerationState(["dev-1"], [], [])),
        )
        hostvar_trigger = AsyncMock()
        structured_trigger = AsyncMock()
        monkeypatch.setattr(generate_fabric_module, "trigger_hostvar_generation", hostvar_trigger)
        monkeypatch.setattr(generate_fabric_module, "trigger_structured_config_generation", structured_trigger)

        await gen.recover_preseeded_state(changed_pod_ids=[])

        hostvar_trigger.assert_not_awaited()
        structured_trigger.assert_not_awaited()
        gen.client.execute_graphql.assert_not_awaited()


class TestPodGenerator:
    @pytest.mark.asyncio
    async def test_zero_super_spines_does_not_require_fabric_pod(self) -> None:
        gen = _make_pod_generator()

        await gen.generate(_pod_query_data(amount_of_super_spines=0))

        gen.get_super_spine_switches_for_fabric.assert_not_awaited()
        gen.connect_spine_to_super_spine.assert_not_awaited()
        gen.create_spine_switches.assert_awaited_once()
        gen.recover_preseeded_racks.assert_awaited_once_with(changed_rack_ids=[])

    @pytest.mark.asyncio
    async def test_update_checksum_does_not_track_preseeded_racks(self) -> None:
        gen = PodGenerator.__new__(PodGenerator)
        gen.client = MagicMock()
        gen.logger = MagicMock()
        gen.pod_id = "pod-1"
        gen.calculate_checksum = MagicMock(return_value="new-checksum")  # type: ignore[method-assign]

        changed_rack = MagicMock()
        changed_rack.id = "rack-1"
        changed_rack.name.value = "rack-1"
        changed_rack.checksum.value = "old-checksum"
        changed_rack.save = AsyncMock()
        unchanged_rack = MagicMock()
        unchanged_rack.id = "rack-2"
        unchanged_rack.name.value = "rack-2"
        unchanged_rack.checksum.value = "new-checksum"
        unchanged_rack.save = AsyncMock()
        gen.client.filters = AsyncMock(return_value=[changed_rack, unchanged_rack])

        changed_rack_ids = await gen.update_checksum()

        assert changed_rack_ids == ["rack-1"]
        changed_rack.save.assert_awaited_once_with(allow_upsert=True, update_group_context=False)
        unchanged_rack.save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pod_triggers_rack_generation_for_unchanged_rack_needing_reconciliation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gen = PodGenerator.__new__(PodGenerator)
        gen.client = MagicMock()
        gen.logger = MagicMock()
        gen.pod_id = "pod-1"
        gen.pod_name = "pod-1"
        monkeypatch.setattr(generate_pod_module, "get_racks_needing_generation", AsyncMock(return_value=["rack-2"]))
        rack_trigger = AsyncMock()
        monkeypatch.setattr(generate_pod_module, "trigger_rack_generation", rack_trigger)

        await gen.recover_preseeded_racks(changed_rack_ids=["rack-1"])

        generate_pod_module.get_racks_needing_generation.assert_awaited_once_with(
            gen.client, "pod-1", exclude_rack_ids=["rack-1"]
        )
        rack_trigger.assert_awaited_once_with(gen.client, nodes=["rack-2"])
