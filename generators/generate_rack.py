from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from infrahub_sdk.generator import InfrahubGenerator
from infrahub_sdk.protocols import CoreIPAddressPool, CoreIPPrefixPool, CoreNumberPool

from solution_arista_avd import sorting as solution_arista_avd_sorting
from solution_arista_avd.cabling import build_rack_cabling_plan, connect_interface_maps
from solution_arista_avd.generator import (
    GeneratorMixin,
    check_all_racks_generated,
    set_fabric_avd_hostvars_ready,
    trigger_hostvar_generation,
)
from solution_arista_avd.protocols import DcimDevice, DcimInterface, LocationRack, NetworkPod

from .rack_generator_query import RackGeneratorQuery

if TYPE_CHECKING:
    from collections.abc import Callable

EXCLUDED_RACK_TYPES = []


class RackGenerator(InfrahubGenerator, GeneratorMixin):
    rack_id: str
    rack_index: int
    rack_name: str
    rack_leaf_switch_template: str
    rack_amount_of_leafs: int

    spine_interface_sorting_function: Callable
    leaf_interface_sorting_function: Callable

    pod_id: str
    pod_index: int
    pod_name: str

    spine_switches: list[DcimDevice]

    leaf_switches: list[DcimDevice]

    loopback_pool: CoreIPAddressPool
    prefix_pool: CoreIPPrefixPool

    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        data: RackGeneratorQuery = RackGeneratorQuery(**data)

        self.rack_id: str = data.location_rack.edges[0].node.id
        self.rack_index: int = data.location_rack.edges[0].node.index.value
        self.rack_name: str = data.location_rack.edges[0].node.name.value
        self.rack_type: str = data.location_rack.edges[0].node.rack_type.value
        self.rack_leaf_switch_template: str = data.location_rack.edges[0].node.leaf_switch_template.node.id
        self.rack_amount_of_leafs: int = data.location_rack.edges[0].node.amount_of_leafs.value
        self.leaf_switches = []
        self.l2leaf_switches: list[DcimDevice] = []

        # L2 leaf fields (optional)
        rack_node = data.location_rack.edges[0].node
        l2leaf_count_attr = getattr(rack_node, "amount_of_l_2_leafs", None)
        self.rack_amount_of_l2leafs: int = (
            l2leaf_count_attr.value if l2leaf_count_attr and l2leaf_count_attr.value else 0
        )
        l2leaf_template_attr = getattr(rack_node, "l_2_leaf_switch_template", None)
        self.rack_l2leaf_switch_template: str | None = (
            l2leaf_template_attr.node.id if l2leaf_template_attr and l2leaf_template_attr.node else None
        )

        self.pod_id: str = data.location_rack.edges[0].node.pod.node.id
        self.pod_index: int = data.location_rack.edges[0].node.pod.node.index.value
        self.pod_name: str = data.location_rack.edges[0].node.pod.node.name.value.lower()
        self.pod_amount_of_spines: int = data.location_rack.edges[0].node.pod.node.amount_of_spines.value
        self.pod: NetworkPod = await self.client.get(kind=NetworkPod, id=self.pod_id)
        await self.pod.parent.fetch()
        self.fabric = self.pod.parent.peer
        await set_fabric_avd_hostvars_ready(self.client, self.fabric.id, False)

        # Reset generation_complete flag to prevent stale flags during re-runs
        rack = await self.client.get(kind=LocationRack, id=self.rack_id)
        rack.generation_complete.value = False
        await rack.save(allow_upsert=True)

        self.loopback_pool_id: str = data.location_rack.edges[0].node.pod.node.loopback_pool.node.id
        self.prefix_pool_id: str = data.location_rack.edges[0].node.pod.node.prefix_pool.node.id

        self.loopback_pool = await self.client.get(kind=CoreIPAddressPool, id=self.loopback_pool_id)
        self.prefix_pool = await self.client.get(kind=CoreIPPrefixPool, id=self.prefix_pool_id)

        self.spine_switches = await self.client.filters(kind=DcimDevice, pod__ids=[self.pod_id], role__value="spine")

        if self.rack_type in EXCLUDED_RACK_TYPES:
            msg = f"Cannot run rack generator on {self.rack_name}-{self.rack_id}: {self.rack_type} is not supported by the generator!"
            raise ValueError(msg)

        if self.pod_amount_of_spines != len(self.spine_switches):
            msg = f"Cannot start rack generator on {self.rack_name}-{self.rack_id}: the pod doesn't seem to be fully generated"
            raise RuntimeError(msg)

        leaf_interface_sorting_method: str = data.location_rack.edges[
            0
        ].node.pod.node.leaf_interface_sorting_method.value
        spine_interface_sorting_method: str = data.location_rack.edges[
            0
        ].node.pod.node.spine_interface_sorting_method.value

        self.leaf_interface_sorting_function = getattr(solution_arista_avd_sorting, leaf_interface_sorting_method)
        self.spine_interface_sorting_function = getattr(solution_arista_avd_sorting, spine_interface_sorting_method)

        # Get AVD-related pool references from parent fabric (via pod)
        self.asn_pool = None
        self.node_id_pool = None
        self.mgmt_pool = None

        pod_node = data.location_rack.edges[0].node.pod.node
        if pod_node.parent and pod_node.parent.node:
            fabric_node = pod_node.parent.node
            if hasattr(fabric_node, "asn_pool") and fabric_node.asn_pool and fabric_node.asn_pool.node:
                self.asn_pool = await self.client.get(kind=CoreNumberPool, id=fabric_node.asn_pool.node.id)
            if hasattr(fabric_node, "node_id_pool") and fabric_node.node_id_pool and fabric_node.node_id_pool.node:
                self.node_id_pool = await self.client.get(kind=CoreNumberPool, id=fabric_node.node_id_pool.node.id)
            if hasattr(fabric_node, "mgmt_pool") and fabric_node.mgmt_pool and fabric_node.mgmt_pool.node:
                self.mgmt_pool = await self.client.get(kind=CoreIPAddressPool, id=fabric_node.mgmt_pool.node.id)

        await self.create_leaf_switches()

        await self.create_mlag_pairs()

        await self.connect_leafs_to_spine()

        await self.create_l2leaf_switches()

        await self.connect_l2leafs_to_leafs()

        # Mark this rack as generation complete
        rack = await self.client.get(kind=LocationRack, id=self.rack_id)
        rack.generation_complete.value = True
        await rack.save(allow_upsert=True)
        self.logger.info(f"Rack {self.rack_name} generation complete")

        # Check if all racks in the fabric are done; if so, trigger hostvar generation
        if await check_all_racks_generated(self.client, self.fabric.id):
            self.logger.info("All racks generated — triggering hostvar generation")
            await trigger_hostvar_generation(self.client)

    async def create_leaf_switches(self) -> None:
        for index in range(1, self.rack_amount_of_leafs + 1):
            device_kwargs = {
                "name": f"leaf-{self.pod_name}-{self.rack_index}-{index}",
                "status": "provisioning",
                "object_template": {"id": self.rack_leaf_switch_template},
                "pod": {"id": self.pod_id},
                "rack": {"id": self.rack_id},
                "loopback_ip": self.loopback_pool,
                "index": index,
                "role": "leaf",
                "member_of_groups": ["avd_devices"],
            }

            # Allocate from ASN and Node ID pools if available
            if self.asn_pool:
                device_kwargs["bgp_asn"] = self.asn_pool
            if self.node_id_pool:
                device_kwargs["node_id"] = self.node_id_pool
            if self.mgmt_pool:
                device_kwargs["mgmt_ip"] = self.mgmt_pool

            leaf_switch = await self.client.create(DcimDevice, **device_kwargs)
            await leaf_switch.save(allow_upsert=True)
            self.leaf_switches.append(leaf_switch)

            # FIX: seems the id of a related node assigned from a pool is not immediately accessible
            device = await self.client.get(
                DcimDevice,
                id=leaf_switch.id,
                include=["ip_address"],
                exclude=["rack", "pod", "role", "name", "object_template", "member_of_groups"],
            )
            loopback_interface = await self.client.get(DcimInterface, device__ids=[device.id], role__value="loopback")
            loopback_interface.status.value = "active"
            loopback_interface.ip_address = device.loopback_ip.id
            await loopback_interface.save(allow_upsert=True)

    async def create_mlag_pairs(self) -> None:
        """Create MLAG domains pairing consecutive leaf switches.

        For every pair of consecutive leafs (0+1, 2+3, ...):
        - Create MlagDomain with both leafs as peers
        AVD auto-generates the switch-side Port-Channel from mlag_interfaces in hostvars.
        """
        if len(self.leaf_switches) < 2:
            self.logger.info(f"Rack {self.rack_name}: fewer than 2 leafs, skipping MLAG pair creation")
            return

        for pair_idx in range(0, len(self.leaf_switches) - 1, 2):
            leaf_a = self.leaf_switches[pair_idx]
            leaf_b = self.leaf_switches[pair_idx + 1]

            pair_suffix = f"-{pair_idx // 2 + 1}" if len(self.leaf_switches) > 2 else ""
            domain_id = f"mlag-{self.rack_name}{pair_suffix}"

            self.logger.info(f"Creating MLAG pair {domain_id}: {leaf_a.name.value} + {leaf_b.name.value}")

            mlag_domain = await self.client.create(
                "MlagDomain",
                domain_id=domain_id,
                peers=[{"id": leaf_a.id}, {"id": leaf_b.id}],
                pod={"id": self.pod_id},
            )
            await mlag_domain.save(allow_upsert=True)

            self.logger.info(f"MLAG domain {domain_id} created successfully")

    async def connect_leafs_to_spine(self) -> None:
        spine_interfaces = await self.client.filters(
            kind=DcimInterface, device__ids=[spine.id for spine in self.spine_switches], role__value="leaf"
        )
        spine_interface_map = self.spine_interface_sorting_function(spine_interfaces)

        leaf_interfaces = await self.client.filters(
            kind=DcimInterface,
            device__ids=[leaf_switch.id for leaf_switch in self.leaf_switches],
            role__value="spine",
        )
        leaf_interface_map = self.leaf_interface_sorting_function(leaf_interfaces)

        created_cabling_plan: list[tuple[DcimInterface, DcimInterface]] = build_rack_cabling_plan(
            rack_index=self.rack_index,
            src_interface_map=leaf_interface_map,
            dst_interface_map=spine_interface_map,
        )

        await connect_interface_maps(client=self.client, logger=self.logger, cabling_plan=created_cabling_plan)

    async def create_l2leaf_switches(self) -> None:
        """Create L2 leaf switches in this rack (access-only, no EVPN)."""
        if self.rack_amount_of_l2leafs == 0 or not self.rack_l2leaf_switch_template:
            return

        self.logger.info(f"Creating {self.rack_amount_of_l2leafs} L2 leaf switches in {self.rack_name}")

        for index in range(1, self.rack_amount_of_l2leafs + 1):
            device_kwargs: dict = {
                "name": f"l2leaf-{self.pod_name}-{self.rack_index}-{index}",
                "status": "provisioning",
                "object_template": {"id": self.rack_l2leaf_switch_template},
                "pod": {"id": self.pod_id},
                "rack": {"id": self.rack_id},
                "index": index,
                "role": "l2leaf",
                "member_of_groups": ["avd_devices"],
            }

            if self.node_id_pool:
                device_kwargs["node_id"] = self.node_id_pool
            if self.mgmt_pool:
                device_kwargs["mgmt_ip"] = self.mgmt_pool

            l2leaf = await self.client.create(DcimDevice, **device_kwargs)
            await l2leaf.save(allow_upsert=True)
            self.l2leaf_switches.append(l2leaf)
            self.logger.info(f"  Created L2 leaf {l2leaf.name.value}")

    async def connect_l2leafs_to_leafs(self) -> None:
        """Connect L2 leaf uplinks to the L3 leaf pair in the same rack."""
        if not self.l2leaf_switches or not self.leaf_switches:
            return

        self.logger.info(f"Connecting {len(self.l2leaf_switches)} L2 leafs to L3 leaf pair")

        # L2 leaf interfaces with role "leaf" are uplinks to the L3 leaf pair
        l2leaf_uplink_interfaces = await self.client.filters(
            kind=DcimInterface,
            device__ids=[l2leaf.id for l2leaf in self.l2leaf_switches],
            role__value="leaf",
        )
        l2leaf_interface_map = self.leaf_interface_sorting_function(l2leaf_uplink_interfaces)

        # L3 leaf "server" interfaces are the downlinks to L2 leafs
        leaf_downlink_interfaces = await self.client.filters(
            kind=DcimInterface,
            device__ids=[leaf.id for leaf in self.leaf_switches],
            role__value="server",
        )
        leaf_interface_map = self.leaf_interface_sorting_function(leaf_downlink_interfaces)

        created_cabling_plan: list[tuple[DcimInterface, DcimInterface]] = build_rack_cabling_plan(
            rack_index=self.rack_index,
            src_interface_map=l2leaf_interface_map,
            dst_interface_map=leaf_interface_map,
        )

        await connect_interface_maps(client=self.client, logger=self.logger, cabling_plan=created_cabling_plan)
