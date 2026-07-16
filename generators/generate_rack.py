from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

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
from solution_arista_avd.protocols import AvdArtifact, DcimDevice, DcimInterface, LocationRack, NetworkPod

from .rack_generator_query import RackGeneratorQuery

if TYPE_CHECKING:
    from collections.abc import Callable

TASK_LOGGER = logging.getLogger("infrahub.tasks")


def is_mlag_enabled(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.lower() not in {"false", "no", "0", "off"}
    return bool(value)


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

    logger = TASK_LOGGER

    async def generate(self, data: dict) -> None:
        data: RackGeneratorQuery = RackGeneratorQuery(**data)

        self.rack_id: str = data.location_rack.edges[0].node.id
        self.rack_index: int = data.location_rack.edges[0].node.index.value
        self.rack_name: str = data.location_rack.edges[0].node.name.value
        self.rack_leaf_switch_template: str = data.location_rack.edges[0].node.leaf_switch_template.node.id
        self.rack_amount_of_leafs: int = data.location_rack.edges[0].node.amount_of_leafs.value
        rack_mlag_attr = data.location_rack.edges[0].node.mlag
        self.rack_mlag: bool = is_mlag_enabled(None if rack_mlag_attr is None else rack_mlag_attr.value)
        self.rack_mlag_enabled: bool = self.rack_mlag and self.rack_amount_of_leafs >= 2
        self.logger.info(f"Rack {self.rack_name}: mlag_enabled={self.rack_mlag}")
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
            self.asn_pool, self.node_id_pool, self.mgmt_pool = await self.resolve_avd_pools(pod_node.parent.node)

        await self.create_leaf_switches()

        if self.rack_mlag_enabled:
            await self.create_mlag_pairs()
        else:
            self.logger.info(f"Rack {self.rack_name}: MLAG disabled, skipping MLAG pair creation")
            await self.delete_stale_mlag_domains()

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
            hostvar_target_ids = await self.hostvar_target_device_ids()
            await self.invalidate_hostvars(hostvar_target_ids)
            self.logger.info(
                "All racks generated — triggering hostvar generation for %s devices", len(hostvar_target_ids)
            )
            await trigger_hostvar_generation(self.client, node_ids=hostvar_target_ids)

    async def create_leaf_switches(self) -> None:
        # MLAG leafs share an ASN allocated onto the MLAG domain, so they must not
        # draw a per-device ASN from the fabric pool. Non-MLAG leafs allocate directly.
        asn_pool = None if self.rack_mlag_enabled else self.asn_pool
        for index in range(1, self.rack_amount_of_leafs + 1):
            leaf_switch = await self.create_avd_device(
                name=f"leaf-{self.pod_name}-{self.rack_index}-{index}",
                role="leaf",
                object_template_id=self.rack_leaf_switch_template,
                pod_id=self.pod_id,
                fabric_id=self.fabric.id,
                rack_id=self.rack_id,
                index=index,
                loopback_pool=self.loopback_pool,
                asn_pool=asn_pool,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
            self.leaf_switches.append(leaf_switch)

    async def create_mlag_pairs(self) -> None:
        """Create MLAG domains pairing consecutive leaf switches.

        For every pair of consecutive leafs (0+1, 2+3, ...):
        - Create an MlagDomain with both leafs as peers.
        - Allocate a single shared ``Routing.Asn`` from the fabric ASN pool and
          link it to both leaf devices and the domain via the ``asn``
          relationship, so the pair presents one BGP ASN (FR-004).
        AVD auto-generates the switch-side Port-Channel from mlag_interfaces in hostvars.
        """
        if not self.rack_mlag_enabled:
            self.logger.info(f"Rack {self.rack_name}: MLAG disabled or fewer than 2 leafs, skipping MLAG pair creation")
            return

        if self.asn_pool is None:
            msg = f"Rack {self.rack_name}: MLAG is enabled but the parent fabric has no ASN pool"
            raise ValueError(msg)

        for pair_idx in range(0, len(self.leaf_switches) - 1, 2):
            leaf_a = self.leaf_switches[pair_idx]
            leaf_b = self.leaf_switches[pair_idx + 1]

            pair_suffix = f"-{pair_idx // 2 + 1}" if len(self.leaf_switches) > 2 else ""
            domain_id = f"{self.rack_name}{pair_suffix}"

            self.logger.info(f"Creating MLAG pair {domain_id}: {leaf_a.name.value} + {leaf_b.name.value}")

            routing_asn_id = await self._get_or_allocate_mlag_asn(domain_id)

            domain_kwargs = {
                "domain_id": domain_id,
                "asn": {"id": routing_asn_id},
                "peers": [{"id": leaf_a.id}, {"id": leaf_b.id}],
                "pod": {"id": self.pod_id},
            }

            mlag_domain = await self.client.create(
                "MlagDomain",
                **domain_kwargs,
            )
            await mlag_domain.save(allow_upsert=True)

            # Both leaves share the domain's single ASN node.
            await self._set_device_asn(leaf_a.id, routing_asn_id)
            await self._set_device_asn(leaf_b.id, routing_asn_id)

            self.logger.info(f"MLAG domain {domain_id} created successfully with shared ASN node {routing_asn_id}")

    async def delete_stale_mlag_domains(self) -> None:
        """Delete MLAG domains for this rack before hostvar generation runs.

        Generator tracking would eventually delete domains that are no longer
        created by this run, but hostvar generation is triggered before the
        tracking context exits. Removing stale domains explicitly prevents
        downstream hostvars from seeing old MLAG state.
        """
        domains = await self.client.filters(kind="MlagDomain", pod__ids=[self.pod_id])
        for domain in domains:
            domain_id = getattr(getattr(domain, "domain_id", None), "value", None)
            if domain_id != self.rack_name and not str(domain_id).startswith(f"{self.rack_name}-"):
                continue

            await domain.delete()
            self.logger.info("Deleted stale MLAG domain %s for rack %s", domain_id, self.rack_name)

    def rack_hostvar_target_device_ids(self) -> list[str]:
        """Return rack-local devices plus pod spines whose hostvars should be refreshed."""
        devices = [*self.leaf_switches, *self.l2leaf_switches, *self.spine_switches]
        seen: set[str] = set()
        device_ids: list[str] = []
        for device in devices:
            if device.id in seen:
                continue
            seen.add(device.id)
            device_ids.append(device.id)
        return device_ids

    async def hostvar_target_device_ids(self) -> list[str]:
        """Return devices that need hostvar generation after a rack run.

        On an already-generated fabric, only the rack leafs/l2leafs and their
        pod spines are affected by a rack change. During initial fabric
        generation, however, the last rack to complete is the first point where
        hostvars can be triggered. In that case many other fabric devices still
        have no hostvar artifact, so targeting only the last rack would leave the
        fabric permanently not ready and structured config / EOS artifacts would
        never render. Detect that bootstrap state and generate hostvars for the
        whole fabric.
        """
        fabric_devices = await self.fabric_devices()
        missing_hostvars = await self.devices_missing_hostvars(fabric_devices)
        if missing_hostvars:
            self.logger.info(
                "Fabric %s is missing hostvars for %s devices; triggering full-fabric hostvar generation",
                getattr(self.fabric, "id", "<unknown>"),
                len(missing_hostvars),
            )
            return self.device_ids(fabric_devices)

        return self.rack_hostvar_target_device_ids()

    async def fabric_devices(self) -> list[Any]:
        """Return all generated devices under the current fabric."""
        pods = await self.client.filters(kind=NetworkPod, parent__ids=[self.fabric.id])
        devices: list[Any] = []

        for pod in pods:
            await pod.devices.fetch()
            devices.extend(peer.peer for peer in pod.devices.peers if peer.peer)

            await pod.racks.fetch()
            for rack_peer in pod.racks.peers:
                rack = rack_peer.peer
                if not rack:
                    continue
                await rack.devices.fetch()
                devices.extend(peer.peer for peer in rack.devices.peers if peer.peer)

        return devices

    def device_ids(self, devices: list[Any]) -> list[str]:
        """Return de-duplicated device IDs preserving input order."""
        seen: set[str] = set()
        device_ids: list[str] = []
        for device in devices:
            if device.id in seen:
                continue
            seen.add(device.id)
            device_ids.append(device.id)
        return device_ids

    async def devices_missing_hostvars(self, devices: list[Any]) -> list[Any]:
        """Return devices without an AVD artifact hostvar file."""
        missing: list[Any] = []
        for device in devices:
            hostname = device.name.value
            artifacts = await self.client.filters(kind=AvdArtifact, name__value=hostname)
            if not artifacts:
                missing.append(device)
                continue

            artifact = artifacts[0]
            if not artifact.hostvar_file.id:
                missing.append(device)
                continue

            try:
                await artifact.hostvar_file.fetch()
            except Exception as exc:  # noqa: BLE001 - a missing file means hostvars are not ready
                self.logger.debug("Hostvar readiness check failed for %s: %s", hostname, exc)
                missing.append(device)
                continue

            if not artifact.hostvar_file.peer:
                missing.append(device)

        return missing

    async def invalidate_hostvars(self, device_ids: list[str]) -> None:
        """Remove existing hostvar files for targeted devices before regeneration.

        The hostvar generator marks the fabric ready once every device has a
        hostvar file. If existing target files remain in place, the first
        regenerated device can flip the fabric back to ready before the rest of
        the targeted devices have refreshed. Deleting only the target files
        makes the existing readiness check wait for the full target set.
        """
        if not device_ids:
            return

        devices = await self.client.filters(kind=DcimDevice, ids=device_ids)
        for device in devices:
            hostname = device.name.value
            artifacts = await self.client.filters(kind=AvdArtifact, name__value=hostname)
            if not artifacts:
                continue

            artifact = artifacts[0]
            if not artifact.hostvar_file.id:
                continue

            try:
                await artifact.hostvar_file.fetch()
                hostvar_file = artifact.hostvar_file.peer
            except Exception as exc:  # noqa: BLE001 - a missing file is already invalidated
                self.logger.debug("Could not fetch hostvar file for %s before invalidation: %s", hostname, exc)
                continue

            if hostvar_file:
                await hostvar_file.delete()
                self.logger.info("Invalidated hostvars for %s before targeted regeneration", hostname)

    async def _set_device_asn(self, device_id: str, routing_asn_id: str) -> None:
        """Link DcimDevice.asn to a RoutingAsn without resaving the SDK object's relationships."""
        await self.client.execute_graphql(
            query="""
            mutation SetDeviceAsn($id: String!, $asn_id: String!) {
                DcimDeviceUpsert(data: { id: $id, asn: { id: $asn_id } }) {
                    ok
                    object { id }
                }
            }
            """,
            variables={"id": device_id, "asn_id": routing_asn_id},
        )

    async def _get_existing_mlag_domain(self, domain_id: str) -> object | None:
        """Return the current MLAG domain for a rack pair, if present."""
        domains = await self.client.filters(kind="MlagDomain", domain_id__value=domain_id)
        return domains[0] if domains else None

    async def _get_or_allocate_mlag_asn(self, domain_id: str) -> str:
        """Return the shared ``Routing.Asn`` node id for an MLAG pair, allocating if needed.

        The idempotency anchor is the existing domain's ``asn`` link: a re-run
        reuses the same shared ASN node rather than drawing a new number from the
        pool (FR-007). When no domain exists yet, a new ``RoutingAsn`` is
        allocated from the fabric ASN pool (FR-004/FR-005).
        """
        if self.asn_pool is None:  # pragma: no cover - guarded by caller
            msg = f"Rack {self.rack_name}: MLAG is enabled but the parent fabric has no ASN pool"
            raise ValueError(msg)

        existing = await self.client.filters(kind="MlagDomain", domain_id__value=domain_id, include=["asn"])
        if existing:
            existing_asn_id = getattr(existing[0].asn, "id", None)
            if existing_asn_id:
                return existing_asn_id

        routing_asn = await self.allocate_routing_asn(self.asn_pool, self.fabric.id)
        return routing_asn.id

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
            # L2 leafs have no loopback/BGP — only node-id and mgmt allocations.
            l2leaf = await self.create_avd_device(
                name=f"l2leaf-{self.pod_name}-{self.rack_index}-{index}",
                role="l2leaf",
                object_template_id=self.rack_l2leaf_switch_template,
                pod_id=self.pod_id,
                fabric_id=self.fabric.id,
                rack_id=self.rack_id,
                index=index,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
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
