from __future__ import annotations

import logging

from infrahub_sdk.generator import InfrahubGenerator
from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from solution_arista_avd.generator import GeneratorMixin, set_fabric_avd_hostvars_ready
from solution_arista_avd.protocols import DcimDevice, DcimInterface, NetworkPod

from .fabric_generator_query import FabricGeneratorQuery


class FabricGenerator(InfrahubGenerator, GeneratorMixin):
    fabric_name: str
    fabric_id: str
    fabric_super_spine_switch_template: str

    loopback_pool: CoreIPAddressPool
    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None

    log = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        data: FabricGeneratorQuery = FabricGeneratorQuery(**data)

        self.fabric_name = data.network_fabric.edges[0].node.name.value.lower()
        self.fabric_id = data.network_fabric.edges[0].node.id
        self.fabric_super_spine_switch_template = data.network_fabric.edges[0].node.super_spine_switch_template.node.id
        self.amount_of_super_spines = data.network_fabric.edges[0].node.amount_of_super_spines.value
        await set_fabric_avd_hostvars_ready(self.client, self.fabric_id, False)
        self.super_spine_devices: list[DcimDevice] = []

        # Get AVD-related pool references
        asn_pool_node = data.network_fabric.edges[0].node.asn_pool
        node_id_pool_node = data.network_fabric.edges[0].node.node_id_pool
        mgmt_pool_node = data.network_fabric.edges[0].node.mgmt_pool

        self.asn_pool = None
        self.node_id_pool = None
        self.mgmt_pool = None

        if asn_pool_node and asn_pool_node.node:
            self.asn_pool = await self.client.get(kind=CoreNumberPool, id=asn_pool_node.node.id)
        if node_id_pool_node and node_id_pool_node.node:
            self.node_id_pool = await self.client.get(kind=CoreNumberPool, id=node_id_pool_node.node.id)
        if mgmt_pool_node and mgmt_pool_node.node:
            self.mgmt_pool = await self.client.get(kind=CoreIPAddressPool, id=mgmt_pool_node.node.id)

        await self.allocate_resource_pools()

        await self.create_super_spine_switches()

        await self.update_checksum()

    async def create_super_spine_switches(self) -> None:
        fabric_pod = await self.client.get(kind=NetworkPod, parent__ids=[self.fabric_id], role__value="fabric")

        for idx in range(1, self.amount_of_super_spines + 1):
            device_kwargs = {
                "name": f"ss-{self.fabric_name}-{idx}",
                "status": "provisioning",
                "object_template": {"id": self.fabric_super_spine_switch_template},
                "loopback_ip": self.loopback_pool,
                "role": "super_spine",
                "pod": fabric_pod,
                "member_of_groups": ["avd_devices"],
            }

            # Allocate from ASN and Node ID pools if available
            if self.asn_pool:
                device_kwargs["bgp_asn"] = self.asn_pool
            if self.node_id_pool:
                device_kwargs["node_id"] = self.node_id_pool
            if self.mgmt_pool:
                device_kwargs["mgmt_ip"] = self.mgmt_pool

            device = await self.client.create(DcimDevice, **device_kwargs)
            await device.save(allow_upsert=True)

            # FIX: seems the id of a related node assigned from a pool is not immediately accessible
            device = await self.client.get(
                DcimDevice,
                id=device.id,
                include=["ip_address"],
                exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
            )
            loopback_interface = await self.client.get(DcimInterface, device__ids=[device.id], role__value="loopback")
            loopback_interface.status.value = "active"
            loopback_interface.ip_address = device.loopback_ip.id
            await loopback_interface.save(allow_upsert=True)

            self.super_spine_devices.append(device)

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
        for pod in pods:
            if pod.checksum.value != fabric_checksum:
                pod.checksum.value = fabric_checksum
                await pod.save(allow_upsert=True)
                self.logger.info(f"Pod {pod.name.value} has been updated to checksum {fabric_checksum}")
