from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from infrahub_sdk.generator import InfrahubGenerator

from solution_arista_avd import sorting as solution_arista_avd_sorting
from solution_arista_avd.avd import SPINE_ROLE_BY_UNDERLAY
from solution_arista_avd.cabling import build_pod_cabling_plan, connect_interface_maps
from solution_arista_avd.generator import GeneratorMixin, set_fabric_avd_hostvars_ready, trigger_rack_generation
from solution_arista_avd.protocols import DcimDevice, DcimInterface, LocationRack, NetworkPod

from .asn import ensure_shared_device_asn
from .pod_generator_query import PodGeneratorQuery

if TYPE_CHECKING:
    from collections.abc import Callable

    from infrahub_sdk.protocols import CoreIPAddressPool, CoreNumberPool

EXCLUDED_POD_ROLES = ["fabric"]


class PodGenerator(InfrahubGenerator, GeneratorMixin):
    pod_id: str
    pod_index: int
    pod_name: str
    pod_spine_switch_template: str | None
    pod_role: str
    # L3LS default; generate() switches to l2spine for standalone L2LS fabrics.
    spine_role: str = "spine"

    fabric_interface_sorting_function: Callable
    spine_interface_sorting_function: Callable

    fabric_id: str
    fabric_name: str
    underlay_routing_protocol: str | None

    loopback_pool: CoreIPAddressPool | None

    spine_switches: list[DcimDevice]
    super_spine_switches: list[DcimDevice]

    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None
    vtep_loopback_pool: CoreIPAddressPool | None

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        data: PodGeneratorQuery = PodGeneratorQuery(**data)

        pod_node = data.network_pod.edges[0].node
        self.pod_id: str = pod_node.id
        self.pod_index: int = pod_node.index.value
        self.pod_name: str = pod_node.name.value.lower()
        self.pod_role: str = pod_node.role.value
        # Spine count + template come from the pod's device_designs (role "spine").
        self.pod_spine_switch_template, self.amount_of_spines = self.device_design_for(pod_node.device_designs, "spine")
        self.fabric_id: str = pod_node.parent.node.id
        self.fabric_name: str = pod_node.parent.node.name.value.lower()
        # Cross-tier completeness read: the expected super-spine count comes from
        # the parent fabric's device_designs (role "super_spine"), not a legacy field.
        _, self.fabric_amount_of_super_spines = self.device_design_for(
            pod_node.parent.node.device_designs, "super_spine"
        )
        underlay_attr = pod_node.parent.node.underlay_routing_protocol
        self.underlay_routing_protocol = underlay_attr.value if underlay_attr else None

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

        # Non-L3LS example fabrics use a different spine role, gated strictly on
        # the fabric underlay so routed L3LS fabrics (ebgp) are unaffected:
        #   underlay "none" -> l2spine (standalone L2LS)
        #   underlay "ospf" -> l3spine (campus core, SVI routing)
        # Read from the query data (no extra fetch).
        self.spine_role = SPINE_ROLE_BY_UNDERLAY.get(self.underlay_routing_protocol, "spine")

        # Get AVD-related pool references from parent fabric
        (
            self.asn_pool,
            self.node_id_pool,
            self.mgmt_pool,
            self.loopback_pool,
            self.vtep_loopback_pool,
        ) = await self.resolve_avd_pools(data.network_pod.edges[0].node.parent.node, data.network_pod.edges[0].node)

        await self.create_spine_switches()

        # Standalone-L2LS spines form an MLAG pair (the example MLAGs both tiers).
        # Gated on the l2spine role so routed L3LS spines are unaffected.
        await self.create_spine_mlag_pair()

        if self.fabric_amount_of_super_spines > 0:
            await self.connect_spine_to_super_spine()

        await self.update_checksum()

    async def create_spine_switches(self) -> None:
        """Create the spine switches"""

        device_asn_pool = None if self.underlay_routing_protocol == "ebgp" else self.asn_pool
        for idx in range(1, self.amount_of_spines + 1):
            device = await self.create_avd_device(
                name=f"spine-{self.pod_name}-{idx}",
                role=self.spine_role,
                object_template_id=self.pod_spine_switch_template,
                pod_id=self.pod_id,
                fabric_id=self.fabric_id,
                loopback_pool=self.loopback_pool,
                vtep_loopback_pool=self.vtep_loopback_pool,
                asn_pool=device_asn_pool,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
            self.spine_switches.append(device)

        if self.underlay_routing_protocol == "ebgp" and self.asn_pool is not None:
            await ensure_shared_device_asn(
                client=self.client,
                devices=self.spine_switches,
                asn_pool=self.asn_pool,
                fabric_id=self.fabric_id,
                allocate_routing_asn=self.allocate_routing_asn,
            )

    async def create_spine_mlag_pair(self) -> None:
        """Form the l2spine MLAG pair for a standalone-L2LS pod.

        Only the underlay-``none`` spine tier (l2spine) is MLAG'd here; routed L3LS
        spines are untouched. The l2spine model ships no dedicated ``mlag_peer``
        interfaces, so the peer-link is carved from its highest free
        super-spine-facing ports (unused in a standalone L2LS fabric, which has no
        super-spines) via the shared ``assign_mlag_peer_interfaces`` helper. Pure
        Layer-2: the domain carries no ASN because the pair runs no BGP.
        """
        if self.spine_role != "l2spine" or len(self.spine_switches) < 2:
            return

        for pair_idx in range(0, len(self.spine_switches) - 1, 2):
            spine_a = self.spine_switches[pair_idx]
            spine_b = self.spine_switches[pair_idx + 1]

            pair_suffix = f"-{pair_idx // 2 + 1}" if len(self.spine_switches) > 2 else ""
            domain_id = f"{self.pod_name}-spine{pair_suffix}"

            mlag_domain = await self.client.create(
                "MlagDomain",
                domain_id=domain_id,
                peers=[{"id": spine_a.id}, {"id": spine_b.id}],
                pod={"id": self.pod_id},
            )
            await mlag_domain.save(allow_upsert=True)

            # Carve the peer-link from the free super-spine-facing ports.
            carvable_roles = frozenset({"super_spine", "mlag_peer"})
            await self.assign_mlag_peer_interfaces(spine_a, carvable_roles=carvable_roles)
            await self.assign_mlag_peer_interfaces(spine_b, carvable_roles=carvable_roles)

            self.logger.info(
                "Created l2spine MLAG domain %s: %s + %s",
                domain_id,
                spine_a.name.value,
                spine_b.name.value,
            )

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

    async def update_checksum(self) -> None:
        racks = await self.client.filters(kind=LocationRack, pod__ids=[self.pod_id])

        # store the checksum for the fabric in the object itself
        checksum = self.calculate_checksum()
        unchanged_rack_ids: list[str] = []
        for rack in racks:
            if rack.checksum.value != checksum:
                rack.checksum.value = checksum
                # This update is only a trigger signal for the rack generator.
                # Do not add pre-seeded racks to PodGenerator's tracking
                # context, otherwise generator cleanup can treat those input
                # objects as pod-generated outputs.
                await rack.save(allow_upsert=True, update_group_context=False)
                self.logger.info(f"Rack {rack.name.value} has been updated to checksum {checksum}")
            else:
                unchanged_rack_ids.append(rack.id)

        if unchanged_rack_ids:
            await trigger_rack_generation(self.client, node_ids=unchanged_rack_ids)
