from __future__ import annotations

import logging
from inspect import signature
from typing import TYPE_CHECKING, Any

from infrahub_sdk.exceptions import ServerNotResponsiveError
from infrahub_sdk.generator import InfrahubGenerator

from solution_arista_avd import sorting as solution_arista_avd_sorting
from solution_arista_avd.avd import LEAF_ROLE_BY_UNDERLAY, SPINE_ROLE_BY_UNDERLAY
from solution_arista_avd.cabling import build_rack_cabling_plan, connect_interface_maps
from solution_arista_avd.generator import (
    VTEP_LOOPBACK_ROLES,
    GeneratorMixin,
    check_all_racks_generated,
    set_fabric_avd_hostvars_ready,
    trigger_hostvar_generation,
)
from solution_arista_avd.protocols import (
    AvdArtifact,
    DcimDevice,
    DcimInterface,
    LocationRack,
    NetworkPod,
)

from .asn import set_device_asn
from .rack_generator_query import RackGeneratorQuery

if TYPE_CHECKING:
    from collections.abc import Callable

    from infrahub_sdk.protocols import CoreIPAddressPool, CoreNumberPool

TASK_LOGGER = logging.getLogger("infrahub.tasks")

# Number of access ports repurposed as the MLAG peer-link on a standalone-L2LS /
# campus main-tier l2leaf. The L3LS leaf templates ship dedicated mlag_peer-role
# interfaces; the arista-7050sx3-48yc8c model used by the l2leaf main tier does
# not, so the peer-link ports are carved from its access ports instead.
L2LEAF_MLAG_PEER_INTERFACE_COUNT = 2


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
    rack_leaf_switch_template: str | None
    rack_amount_of_leafs: int

    spine_interface_sorting_function: Callable
    leaf_interface_sorting_function: Callable

    pod_id: str
    pod_index: int
    pod_name: str

    spine_switches: list[DcimDevice]

    leaf_switches: list[DcimDevice]

    # Device roles for this fabric. Defaults are the L3LS roles; generate()
    # switches them to l2spine/l2leaf for standalone L2LS fabrics (underlay "none").
    leaf_role: str = "leaf"
    spine_role: str = "spine"

    loopback_pool: CoreIPAddressPool | None

    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None
    vtep_loopback_pool: CoreIPAddressPool | None

    logger = TASK_LOGGER

    async def generate(self, data: dict) -> None:
        data: RackGeneratorQuery = RackGeneratorQuery(**data)
        rack_node = data.location_rack.edges[0].node
        if rack_node is None:
            msg = "Rack generator query returned no rack node"
            raise ValueError(msg)

        self.rack_id = rack_node.id
        self.rack_index = self._attr_value(rack_node.index, default=0)
        self.rack_name = self._attr_value(rack_node.name, default=self.rack_id)
        # Leaf count + template come from the rack's device_designs (role "leaf");
        # an absent design means zero leaves.
        self.rack_leaf_switch_template, self.rack_amount_of_leafs = self.device_design_for(
            rack_node.device_designs, "leaf"
        )
        if self.rack_amount_of_leafs > 0 and not self.rack_leaf_switch_template:
            msg = (
                f"Rack {self.rack_name}: leaf device design quantity is "
                f"{self.rack_amount_of_leafs} but its device_template is missing"
            )
            raise ValueError(msg)

        rack_mlag_attr = rack_node.mlag
        self.rack_mlag: bool = is_mlag_enabled(None if rack_mlag_attr is None else rack_mlag_attr.value)
        self.rack_mlag_enabled: bool = self.rack_mlag and self.rack_amount_of_leafs >= 2
        self.logger.info(f"Rack {self.rack_name}: mlag_enabled={self.rack_mlag}")
        self.leaf_switches = []
        self.l2leaf_switches: list[DcimDevice] = []

        # L2-leaf count + template come from the rack's device_designs (role
        # "l2leaf"); an absent design means no L2 leaves.
        self.rack_l2leaf_switch_template, self.rack_amount_of_l2leafs = self.device_design_for(
            rack_node.device_designs, "l2leaf"
        )
        if self.rack_amount_of_l2leafs > 0 and not self.rack_l2leaf_switch_template:
            msg = (
                f"Rack {self.rack_name}: l2leaf device design quantity is "
                f"{self.rack_amount_of_l2leafs} but its device_template is missing"
            )
            raise ValueError(msg)

        pod_node = self._relationship_node(rack_node.pod)
        if pod_node is None:
            await self.defer_rack_generation("rack has no pod")
            return

        fabric_node = self._relationship_node(pod_node.parent)
        if fabric_node is None or getattr(fabric_node, "typename__", None) != "NetworkFabric":
            await self.defer_rack_generation("pod has no parent fabric")
            return

        self.pod_id = pod_node.id
        self.pod_index = self._attr_value(pod_node.index, default=0)
        self.pod_name = str(self._attr_value(pod_node.name, default=self.pod_id)).lower()
        # Cross-tier completeness read: the expected spine count comes from the
        # pod's device_designs (role "spine"), not a legacy field.
        _, self.pod_amount_of_spines = self.device_design_for(pod_node.device_designs, "spine")
        self.pod = await self.client.get(kind=NetworkPod, id=self.pod_id)
        await self.pod.parent.fetch()
        self.fabric = self.pod.parent.peer

        # Standalone L2LS fabrics (underlay "none") use l2leaf leaves. Gated on the
        # fabric underlay so L3LS fabrics (ebgp/ospf) keep the routed leaf role.
        # Read from the query data (no extra fetch), mirroring the pod generator.
        underlay = getattr(getattr(fabric_node, "underlay_routing_protocol", None), "value", None)
        self.leaf_role = LEAF_ROLE_BY_UNDERLAY.get(underlay, "leaf")
        self.spine_role = SPINE_ROLE_BY_UNDERLAY.get(underlay, "spine")

        self.spine_switches = await self.client.filters(
            kind=DcimDevice, pod__ids=[self.pod_id], role__value=self.spine_role
        )

        if self.pod_amount_of_spines != len(self.spine_switches):
            await self.defer_rack_generation(
                f"pod is not fully generated: expected {self.pod_amount_of_spines} "
                f"{self.spine_role} devices, found {len(self.spine_switches)}"
            )
            return

        await set_fabric_avd_hostvars_ready(self.client, self.fabric.id, False)

        # Reset generation_complete flag to prevent stale flags during re-runs
        await self.set_rack_generation_complete(False)

        leaf_interface_sorting_method: str = pod_node.leaf_interface_sorting_method.value
        spine_interface_sorting_method: str = pod_node.spine_interface_sorting_method.value

        self.leaf_interface_sorting_function = getattr(solution_arista_avd_sorting, leaf_interface_sorting_method)
        self.spine_interface_sorting_function = getattr(solution_arista_avd_sorting, spine_interface_sorting_method)

        # Get AVD-related pool references from parent fabric (via pod)
        self.asn_pool = None
        self.node_id_pool = None
        self.mgmt_pool = None
        self.vtep_loopback_pool = None

        (
            self.asn_pool,
            self.node_id_pool,
            self.mgmt_pool,
            self.loopback_pool,
            self.vtep_loopback_pool,
        ) = await self.resolve_avd_pools(fabric_node, pod_node)

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
        await self.set_rack_generation_complete(True)
        self.logger.info(f"Rack {self.rack_name} generation complete")

        # Check if all racks in the fabric are done; if so, trigger hostvar generation
        if await check_all_racks_generated(self.client, self.fabric.id):
            hostvar_target_ids = await self.hostvar_target_device_ids()
            await self.invalidate_hostvars(hostvar_target_ids)
            self.logger.info(
                "All racks generated — triggering hostvar generation for %s devices", len(hostvar_target_ids)
            )
            await self.trigger_hostvar_generation_after_rack_completion(hostvar_target_ids)

    async def trigger_hostvar_generation_after_rack_completion(self, node_ids: list[str]) -> None:
        """Trigger hostvars with timeout tolerance, compatible with older installed helper packages."""
        if "timeout" in signature(trigger_hostvar_generation).parameters:
            await trigger_hostvar_generation(
                self.client,
                node_ids=node_ids,
                timeout=300,
                tolerate_timeout=True,
            )
            return

        await self._trigger_hostvar_generation_compat(node_ids=node_ids, timeout=300, tolerate_timeout=True)

    async def _trigger_hostvar_generation_compat(
        self,
        *,
        node_ids: list[str] | None,
        timeout: int | None,  # noqa: ASYNC109 - forwards the SDK GraphQL timeout option
        tolerate_timeout: bool,
    ) -> None:
        if node_ids is None:
            self.logger.warning("Skipping generate-avd-device-hostvar trigger: target node IDs are required")
            return
        if not node_ids:
            self.logger.warning("Skipping generate-avd-device-hostvar trigger: no target node IDs found")
            return

        generator_defs = await self.client.filters(
            kind="CoreGeneratorDefinition", name__value="generate-avd-device-hostvar"
        )
        if not generator_defs:
            msg = "Could not find CoreGeneratorDefinition 'generate-avd-device-hostvar'"
            raise ValueError(msg)

        execute_kwargs: dict[str, Any] = {
            "query": """
            mutation RunGenerator($id: String!, $nodes: [String!]!) {
                CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                    ok
                }
            }
            """,
            "variables": {"id": generator_defs[0].id, "nodes": node_ids},
        }
        if timeout is not None:
            execute_kwargs["timeout"] = timeout

        try:
            await self.client.execute_graphql(**execute_kwargs)
        except ServerNotResponsiveError:
            if not tolerate_timeout:
                raise
            self.logger.warning(
                "Timed out while triggering generate-avd-device-hostvar; downstream generator state is ambiguous "
                "and will be observed later"
            )

    async def defer_rack_generation(self, reason: str) -> None:
        """Mark the rack incomplete and return without enrolling deferral in tracking."""
        self.logger.info("Deferring rack %s generation: %s", self.rack_name, reason)
        if getattr(self, "rack_id", None):
            await self.set_rack_generation_complete(False, update_group_context=False)

    async def set_rack_generation_complete(self, complete: bool, *, update_group_context: bool = True) -> None:
        rack = await self.client.get(kind=LocationRack, id=self.rack_id)
        rack.generation_complete.value = complete
        if update_group_context:
            await rack.save(allow_upsert=True)
            return
        await rack.save(allow_upsert=True, update_group_context=False)

    @staticmethod
    def _relationship_node(relationship: object) -> object | None:
        if relationship is None:
            return None
        return getattr(relationship, "node", None)

    @staticmethod
    def _attr_value(attribute: object, *, default: Any) -> Any:
        value = getattr(attribute, "value", None)
        return default if value is None else value

    async def create_leaf_switches(self) -> None:
        # MLAG leafs share an ASN allocated onto the MLAG domain, so they must not
        # draw a per-device ASN from the fabric pool. Non-MLAG leafs allocate directly.
        asn_pool = None if self.rack_mlag_enabled else self.asn_pool
        share_mlag_vtep_loopback = (
            self.rack_mlag_enabled and self.leaf_role in VTEP_LOOPBACK_ROLES and self.vtep_loopback_pool is not None
        )
        for index in range(1, self.rack_amount_of_leafs + 1):
            vtep_loopback_pool = self.vtep_loopback_pool
            if share_mlag_vtep_loopback and index % 2 == 0:
                vtep_loopback_pool = None

            leaf_switch = await self.create_avd_device(
                name=f"leaf-{self.pod_name}-{self.rack_index}-{index}",
                role=self.leaf_role,
                object_template_id=self.rack_leaf_switch_template,
                pod_id=self.pod_id,
                fabric_id=self.fabric.id,
                rack_id=self.rack_id,
                index=index,
                loopback_pool=self.loopback_pool,
                vtep_loopback_pool=vtep_loopback_pool,
                asn_pool=asn_pool,
                node_id_pool=self.node_id_pool,
                mgmt_pool=self.mgmt_pool,
            )
            self.leaf_switches.append(leaf_switch)
            if share_mlag_vtep_loopback and index % 2 == 0:
                await self._share_mlag_vtep_loopback_ip(self.leaf_switches[-2], leaf_switch)

    async def _share_mlag_vtep_loopback_ip(self, primary_leaf: DcimDevice, secondary_leaf: DcimDevice) -> None:
        """Point both leaves in an MLAG pair at the primary leaf's VTEP loopback IP."""
        vtep_loopback_ip_id = await self._device_vtep_loopback_ip_id(primary_leaf.id)
        if vtep_loopback_ip_id is None:
            msg = (
                f"MLAG pair {primary_leaf.name.value} + {secondary_leaf.name.value}: "
                "primary leaf has no VTEP loopback IP to share"
            )
            raise ValueError(msg)

        await self._set_device_vtep_loopback_ip(secondary_leaf.id, vtep_loopback_ip_id)
        await self._reconcile_generated_loopback_interfaces(secondary_leaf.id, self.leaf_role)

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
            await set_device_asn(self.client, leaf_a.id, routing_asn_id)
            await set_device_asn(self.client, leaf_b.id, routing_asn_id)

            # Standalone-L2LS / campus main-tier l2leaf switches use a model with
            # no dedicated mlag_peer interfaces, so carve the peer-link from the
            # access ports. L3LS leaf/border_leaf templates already ship them.
            if self.leaf_role == "l2leaf":
                await self._assign_l2leaf_mlag_peer_interfaces(leaf_a)
                await self._assign_l2leaf_mlag_peer_interfaces(leaf_b)

            self.logger.info(f"MLAG domain {domain_id} created successfully with shared ASN node {routing_asn_id}")

    async def _assign_l2leaf_mlag_peer_interfaces(self, leaf: DcimDevice) -> None:
        """Carve the MLAG peer-link on an l2leaf main-tier switch.

        Thin wrapper over the shared ``GeneratorMixin.assign_mlag_peer_interfaces``
        helper, pinned to the l2leaf peer-link port count. The l2leaf model
        (arista-7050sx3-48yc8c) ships no dedicated ``mlag_peer`` interfaces, so the
        peer-link is carved from its highest-numbered access ports.
        """
        await self.assign_mlag_peer_interfaces(leaf, count=L2LEAF_MLAG_PEER_INTERFACE_COUNT)

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
        """Keep existing hostvar files in place before targeted regeneration.

        Hostvar and structured-config generators checksum-gate file writes, so a
        no-op rack reconciliation must not delete and recreate file nodes.
        """
        if not device_ids:
            return

        self.logger.info(
            "Preserving existing hostvar files before targeted regeneration for %s devices", len(device_ids)
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
