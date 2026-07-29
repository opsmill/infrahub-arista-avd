from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from infrahub_sdk.generator import InfrahubGenerator

_REPO_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_REPO_SRC) not in sys.path:
    sys.path.insert(0, str(_REPO_SRC))
_PACKAGE_ROOT = _REPO_SRC / "solution_arista_avd"
if (package := sys.modules.get("solution_arista_avd")) is not None and hasattr(package, "__path__"):
    package.__path__ = [str(_PACKAGE_ROOT), *[path for path in package.__path__ if path != str(_PACKAGE_ROOT)]]
for module_name in (
    "solution_arista_avd.generator",
    "solution_arista_avd.protocols",
):
    sys.modules.pop(module_name, None)

from solution_arista_avd.generator import (  # noqa: E402
    GeneratorMixin,
    set_fabric_avd_hostvars_ready,
    trigger_pod_generation,
)
from solution_arista_avd.protocols import DcimDevice, NetworkPod  # noqa: E402

from .asn import ensure_shared_device_asn  # noqa: E402
from .fabric_generator_query import FabricGeneratorQuery  # noqa: E402

if TYPE_CHECKING:
    from infrahub_sdk.protocols import CoreIPAddressPool, CoreNumberPool


class FabricGenerator(InfrahubGenerator, GeneratorMixin):
    fabric_name: str
    fabric_id: str
    fabric_super_spine_switch_template: str | None
    underlay_routing_protocol: str | None

    loopback_pool: CoreIPAddressPool | None
    asn_pool: CoreNumberPool | None
    node_id_pool: CoreNumberPool | None
    mgmt_pool: CoreIPAddressPool | None
    vtep_loopback_pool: CoreIPAddressPool | None

    async def generate(self, data: dict) -> None:
        data: FabricGeneratorQuery = FabricGeneratorQuery(**data)

        fabric_node = data.network_fabric.edges[0].node
        self.fabric_name = fabric_node.name.value.lower()
        self.fabric_id = fabric_node.id
        underlay_attr = fabric_node.underlay_routing_protocol
        self.underlay_routing_protocol = underlay_attr.value if underlay_attr else None
        # Super-spine count + template now come from the fabric's device_designs
        # (role "super_spine"); an absent design means zero super-spines.
        self.fabric_super_spine_switch_template, self.amount_of_super_spines = self.device_design_for(
            fabric_node.device_designs, "super_spine"
        )
        await set_fabric_avd_hostvars_ready(self.client, self.fabric_id, False)
        self.super_spine_devices: list[DcimDevice] = []

        # Get AVD-related pool references
        (
            self.asn_pool,
            self.node_id_pool,
            self.mgmt_pool,
            self.loopback_pool,
            self.vtep_loopback_pool,
        ) = await self.resolve_avd_pools(data.network_fabric.edges[0].node)

        await self.create_super_spine_switches()

        await self.update_checksum()

    async def create_super_spine_switches(self) -> None:
        if self.amount_of_super_spines == 0:
            self.logger.info("Skipping super-spine creation for %s: no super_spine device design", self.fabric_name)
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
