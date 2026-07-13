from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from infrahub_sdk.generator import InfrahubGenerator
from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from solution_arista_avd import sorting as solution_arista_avd_sorting
from solution_arista_avd.cabling import build_pod_cabling_plan, connect_interface_maps
from solution_arista_avd.generator import GeneratorMixin, set_fabric_avd_hostvars_ready
from solution_arista_avd.protocols import DcimDevice, DcimInterface, LocationRack, NetworkPod

from .generation_state import get_racks_needing_generation, trigger_rack_generation
from .pod_generator_query import PodGeneratorQuery

if TYPE_CHECKING:
    from collections.abc import Callable

EXCLUDED_POD_ROLES = ["fabric"]


class PodGenerator(InfrahubGenerator, GeneratorMixin):
    pod_id: str
    pod_index: int
    pod_name: str
    pod_spine_switch_template: str
    pod_role: str

    fabric_interface_sorting_function: Callable
    spine_interface_sorting_function: Callable

    fabric_id: str
    fabric_name: str

    loopback_pool: CoreIPAddressPool

    pod_prefix_pool: CoreIPPrefixPool
    spine_switches: list[DcimDevice]
    super_spine_switches: list[DcimDevice]

    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        data: PodGeneratorQuery = PodGeneratorQuery(**data)

        self.pod_id: str = data.network_pod.edges[0].node.id
        self.pod_index: int = data.network_pod.edges[0].node.index.value
        self.pod_name: str = data.network_pod.edges[0].node.name.value.lower()
        self.pod_role: str = data.network_pod.edges[0].node.role.value
        self.pod_spine_switch_template: str | None = (
            data.network_pod.edges[0].node.spine_switch_template.node.id
            if data.network_pod.edges[0].node.spine_switch_template.node
            else None
        )
        self.fabric_id: str = data.network_pod.edges[0].node.parent.node.id
        self.fabric_name: str = data.network_pod.edges[0].node.parent.node.name.value.lower()
        self.amount_of_spines: int = data.network_pod.edges[0].node.amount_of_spines.value
        self.fabric_amount_of_super_spines: int = data.network_pod.edges[
            0
        ].node.parent.node.amount_of_super_spines.value

        await set_fabric_avd_hostvars_ready(self.client, self.fabric_id, False)

        self.spine_switches = []

        # The fabric-role pod is owned by FabricGenerator (it holds the
        # super-spines), so this generator legitimately skips it — not an error.
        if self.pod_role in EXCLUDED_POD_ROLES:
            self.logger.info(
                f"Skipping pod generator on {self.pod_name}-{self.pod_id}: role '{self.pod_role}' is handled elsewhere"
            )
            return

        self.super_spine_switches = []
        if self.fabric_amount_of_super_spines > 0:
            await self.get_super_spine_switches_for_fabric()

            if self.fabric_amount_of_super_spines != len(self.super_spine_switches):
                msg = f"Cannot start pod generator on {self.pod_name}-{self.pod_id}: the fabric doesn't seem to be fully generated yet!"
                raise RuntimeError(msg)

        if not self.pod_spine_switch_template:
            msg = f"Cannot start pod generator on {self.pod_name}-{self.pod_id}: no spine switch template defined!"
            raise RuntimeError(msg)

        fabric_interface_sorting_method: str = data.network_pod.edges[
            0
        ].node.parent.node.fabric_interface_sorting_method.value
        spine_interface_sorting_method: str = data.network_pod.edges[
            0
        ].node.parent.node.spine_interface_sorting_method.value

        self.fabric_interface_sorting_function = getattr(solution_arista_avd_sorting, fabric_interface_sorting_method)
        self.spine_interface_sorting_function = getattr(solution_arista_avd_sorting, spine_interface_sorting_method)

        # Get AVD-related pool references from parent fabric
        self.asn_pool, self.node_id_pool, self.mgmt_pool = await self.resolve_avd_pools(
            data.network_pod.edges[0].node.parent.node
        )

        await self.allocate_resource_pools()

        await self.create_spine_switches()

        if self.fabric_amount_of_super_spines > 0:
            await self.connect_spine_to_super_spine()

        changed_rack_ids = await self.update_checksum()
        await self.recover_preseeded_racks(changed_rack_ids=changed_rack_ids or [])

    async def create_spine_switches(self) -> None:
        """Create the spine switches"""

        for idx in range(1, self.amount_of_spines + 1):
            device = await self.create_avd_device(
                name=f"spine-{self.pod_name}-{idx}",
                role="spine",
                object_template_id=self.pod_spine_switch_template,
                pod_id=self.pod_id,
                loopback_pool=self.loopback_pool,
                asn_pool=self.asn_pool,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
            self.spine_switches.append(device)

    async def allocate_resource_pools(self) -> None:
        """Allocate IP Space for the Pod"""

        fabric_prefix_pool = await self.client.get(CoreIPPrefixPool, name__value=f"{self.fabric_name}-prefix-pool")

        pod_supernet = await self.client.allocate_next_ip_prefix(
            resource_pool=fabric_prefix_pool,
            identifier=self.pod_id,
            member_type="prefix",
            prefix_length=19,
            data={"role": "pod_supernet"},
        )

        self.pod_prefix_pool = await self.client.create(
            kind=CoreIPPrefixPool,
            name=f"{self.fabric_name}-{self.pod_name}-prefix-pool",
            default_prefix_type="IpamPrefix",
            default_prefix_length=24,
            ip_namespace={"hfid": ["default"]},
            resources=[pod_supernet],
        )
        await self.pod_prefix_pool.save(allow_upsert=True)

        pod_loopback_prefix = await self.client.allocate_next_ip_prefix(
            resource_pool=self.pod_prefix_pool,
            identifier=str(self.pod_id),
            member_type="address",
            prefix_length=27,
            data={"role": "pod_loopback"},
        )

        self.loopback_pool = await self.client.create(
            kind=CoreIPAddressPool,
            name=f"{self.fabric_name}-{self.pod_name}-loopback-pool",
            default_address_type="IpamIPAddress",
            default_prefix_length=32,
            ip_namespace={"hfid": ["default"]},
            resources=[pod_loopback_prefix],
        )
        await self.loopback_pool.save(allow_upsert=True)

        pod = await self.client.get(kind=NetworkPod, id=self.pod_id)
        pod.loopback_pool = self.loopback_pool
        pod.prefix_pool = self.pod_prefix_pool
        await pod.save(allow_upsert=True)

    async def get_super_spine_switches_for_fabric(self) -> tuple[NetworkPod | None, list[DcimDevice]]:
        if self.fabric_amount_of_super_spines == 0:
            self.super_spine_switches = []
            return None, self.super_spine_switches

        self.fabric_pod = await self.client.get(kind=NetworkPod, parent__ids=[self.fabric_id], role__value="fabric")
        self.super_spine_switches = await self.client.filters(
            kind=DcimDevice, pod__ids=[self.fabric_pod.id], role__value="super_spine"
        )
        return self.fabric_pod, self.super_spine_switches

    async def connect_spine_to_super_spine(self) -> None:
        if self.fabric_amount_of_super_spines == 0:
            self.logger.info(f"Pod {self.pod_name}: no super-spines configured, skipping spine-to-super-spine cabling")
            return

        spine_interfaces = await self.client.filters(
            kind=DcimInterface, device__ids=[spine.id for spine in self.spine_switches], role__value="super_spine"
        )
        spine_interface_map = self.spine_interface_sorting_function(spine_interfaces)

        super_spine_interfaces = await self.client.filters(
            kind=DcimInterface, device__ids=[ss.id for ss in self.super_spine_switches], role__value="spine"
        )
        super_spine_interface_map = self.fabric_interface_sorting_function(super_spine_interfaces)

        created_cabling_plan: list[tuple[DcimInterface, DcimInterface]] = build_pod_cabling_plan(
            pod_index=self.pod_index,
            src_interface_map=spine_interface_map,
            dst_interface_map=super_spine_interface_map,
        )

        await connect_interface_maps(client=self.client, logger=self.logger, cabling_plan=created_cabling_plan)

    async def recover_preseeded_racks(self, *, changed_rack_ids: list[str]) -> None:
        """Explicitly recover unchanged pre-seeded racks whose generated state is incomplete."""
        racks_needing_generation = await get_racks_needing_generation(
            self.client, self.pod_id, exclude_rack_ids=changed_rack_ids
        )
        if not racks_needing_generation:
            self.logger.info("Pod %s racks are complete or already triggered normally", self.pod_name)
            return

        self.logger.info("Triggering targeted rack generation for recovered racks: %s", racks_needing_generation)
        await trigger_rack_generation(self.client, nodes=racks_needing_generation)

    async def update_checksum(self) -> list[str]:
        racks = await self.client.filters(kind=LocationRack, pod__ids=[self.pod_id])

        changed_rack_ids: list[str] = []

        # store the checksum for the fabric in the object itself
        checksum = self.calculate_checksum()
        for rack in racks:
            if rack.checksum.value != checksum:
                rack.checksum.value = checksum
                # This update is only a trigger signal for the rack generator.
                # Do not add pre-seeded racks to PodGenerator's tracking
                # context, otherwise generator cleanup can treat those input
                # objects as pod-generated outputs.
                await rack.save(allow_upsert=True, update_group_context=False)
                changed_rack_ids.append(rack.id)
                self.logger.info(f"Rack {rack.name.value} has been updated to checksum {checksum}")

        return changed_rack_ids
