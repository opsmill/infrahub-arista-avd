from __future__ import annotations

from infrahub_sdk.generator import InfrahubGenerator
from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from solution_arista_avd.generator import GeneratorMixin, set_fabric_avd_hostvars_ready, trigger_pod_generation
from solution_arista_avd.protocols import DcimDevice, NetworkPod

from .asn import ensure_shared_device_asn
from .fabric_generator_query import FabricGeneratorQuery


class FabricGenerator(InfrahubGenerator, GeneratorMixin):
    fabric_name: str
    fabric_id: str
    fabric_super_spine_switch_template: str | None
    underlay_routing_protocol: str | None

    loopback_pool: CoreIPAddressPool
    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None
    vtep_loopback_pool: CoreIPAddressPool | None

    async def generate(self, data: dict) -> None:
        data: FabricGeneratorQuery = FabricGeneratorQuery(**data)

        self.fabric_name = data.network_fabric.edges[0].node.name.value.lower()
        self.fabric_id = data.network_fabric.edges[0].node.id
        self.amount_of_super_spines = data.network_fabric.edges[0].node.amount_of_super_spines.value
        underlay_attr = data.network_fabric.edges[0].node.underlay_routing_protocol
        self.underlay_routing_protocol = underlay_attr.value if underlay_attr else None
        super_spine_template = data.network_fabric.edges[0].node.super_spine_switch_template.node
        self.fabric_super_spine_switch_template = super_spine_template.id if super_spine_template else None
        await set_fabric_avd_hostvars_ready(self.client, self.fabric_id, False)
        self.super_spine_devices: list[DcimDevice] = []

        # Get AVD-related pool references
        self.asn_pool, self.node_id_pool, self.mgmt_pool, self.vtep_loopback_pool = await self.resolve_avd_pools(
            data.network_fabric.edges[0].node
        )

        await self.allocate_resource_pools()

        await self.create_super_spine_switches()

        await self.update_checksum()

    async def create_super_spine_switches(self) -> None:
        if self.amount_of_super_spines == 0:
            self.logger.info("Skipping super-spine creation for %s: amount_of_super_spines is 0", self.fabric_name)
            return

        if not self.fabric_super_spine_switch_template:
            msg = f"Cannot create super-spines for {self.fabric_name}: no super-spine switch template defined!"
            raise ValueError(msg)

        fabric_pod = await self.client.get(kind=NetworkPod, parent__ids=[self.fabric_id], role__value="fabric")
        device_asn_pool = None if self.underlay_routing_protocol == "ebgp" else self.asn_pool

        for idx in range(1, self.amount_of_super_spines + 1):
            device = await self.create_avd_device(
                name=f"ss-{self.fabric_name}-{idx}",
                role="super_spine",
                object_template_id=self.fabric_super_spine_switch_template,
                pod_id=fabric_pod.id,
                fabric_id=self.fabric_id,
                loopback_pool=self.loopback_pool,
                vtep_loopback_pool=self.vtep_loopback_pool,
                asn_pool=device_asn_pool,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
            self.super_spine_devices.append(device)

        if self.underlay_routing_protocol == "ebgp" and self.asn_pool is not None:
            await ensure_shared_device_asn(
                client=self.client,
                devices=self.super_spine_devices,
                asn_pool=self.asn_pool,
                fabric_id=self.fabric_id,
                allocate_routing_asn=self.allocate_routing_asn,
            )

    async def allocate_resource_pools(self) -> None:
        fabric_supernet_pool = await self.client.get(kind=CoreIPPrefixPool, name__value="FabricSupernetPool")
        fabric_supernet = await self.client.allocate_next_ip_prefix(
            resource_pool=fabric_supernet_pool, identifier=self.fabric_id, data={"role": "fabric_supernet"}
        )

        fabric_prefix_pool = await self.client.create(
            kind=CoreIPPrefixPool,
            name=f"{self.fabric_name}-prefix-pool",
            default_prefix_type="IpamPrefix",
            default_prefix_length=24,
            ip_namespace={"hfid": ["default"]},
            resources=[fabric_supernet],
        )
        await fabric_prefix_pool.save(allow_upsert=True)

        ss_loopback_prefix = await self.client.allocate_next_ip_prefix(
            resource_pool=fabric_prefix_pool,
            identifier=self.fabric_id,
            member_type="address",
            prefix_length=28,
            data={"role": "super_spine_loopback"},
        )

        self.loopback_pool = await self.client.create(
            kind=CoreIPAddressPool,
            name=f"{self.fabric_name}-super-spine-loopback-pool",
            default_address_type="IpamIPAddress",
            default_prefix_length=32,
            ip_namespace={"hfid": ["default"]},
            resources=[ss_loopback_prefix],
        )
        await self.loopback_pool.save(allow_upsert=True)

    async def update_checksum(self) -> None:
        pods = await self.client.filters(kind=NetworkPod, parent__ids=[self.fabric_id])

        # store the checksum for the fabric in the object itself
        fabric_checksum = self.calculate_checksum()
        unchanged_pod_ids: list[str] = []
        for pod in pods:
            if pod.checksum.value != fabric_checksum:
                pod.checksum.value = fabric_checksum
                # This update is only a trigger signal for the pod generator.
                # Do not add pre-seeded pods to FabricGenerator's tracking
                # context, otherwise generator cleanup can treat those input
                # objects as fabric-generated outputs.
                await pod.save(allow_upsert=True, update_group_context=False)
                self.logger.info(f"Pod {pod.name.value} has been updated to checksum {fabric_checksum}")
            elif pod.role.value != "fabric":
                unchanged_pod_ids.append(pod.id)

        if unchanged_pod_ids:
            await trigger_pod_generation(self.client, node_ids=unchanged_pod_ids)
