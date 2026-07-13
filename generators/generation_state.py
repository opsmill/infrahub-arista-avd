from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from solution_arista_avd.protocols import DcimDevice

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from infrahub_sdk import InfrahubClient

    from solution_arista_avd.protocols import LocationRack, NetworkPod

logger = logging.getLogger("infrahub.tasks")

RESOURCE_FIELDS_BY_ROLE = {
    "super_spine": ("bgp_asn", "loopback_ip", "mgmt_ip", "node_id"),
    "spine": ("bgp_asn", "loopback_ip", "mgmt_ip", "node_id"),
    "leaf": ("bgp_asn", "loopback_ip", "mgmt_ip", "node_id"),
    "l2leaf": ("mgmt_ip", "node_id"),
}


@dataclass(slots=True)
class FabricAvdGenerationState:
    """AVD artifact/file health for devices generated under a fabric."""

    device_ids: list[str]
    missing_hostvar_device_ids: list[str]
    missing_structured_config_device_ids: list[str]

    @property
    def has_devices(self) -> bool:
        return bool(self.device_ids)

    @property
    def is_complete(self) -> bool:
        return not self.missing_hostvar_device_ids and not self.missing_structured_config_device_ids


def _value(obj: Any, default: Any = None) -> Any:
    """Return an Infrahub attribute value or the object itself for plain test doubles."""
    return getattr(obj, "value", obj) if obj is not None else default


def _role_value(node: Any) -> str | None:
    role = getattr(node, "role", None)
    value = _value(role)
    return str(value) if value is not None else None


def _int_value(node: Any, attr_name: str) -> int:
    return int(_value(getattr(node, attr_name, None), 0) or 0)


def _safe_getattr(obj: Any, attr_name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, attr_name, default)
    except ValueError:
        return default


def _relationship_is_set(node: Any, attr_name: str) -> bool:
    rel_or_attr = getattr(node, attr_name, None)
    if rel_or_attr is None:
        return False

    for nested_attr in ("id", "node"):
        nested = _safe_getattr(rel_or_attr, nested_attr)
        if nested:
            return True

    value = _safe_getattr(rel_or_attr, "value")
    if value is not None:
        return value not in ("", None)

    return rel_or_attr not in ("", None)


def device_has_expected_resources(device: Any) -> bool:
    """Return whether a generated AVD network device has its role-specific allocations."""
    role = _role_value(device)
    if role is None:
        return True
    required_fields = RESOURCE_FIELDS_BY_ROLE.get(role)
    if not required_fields:
        return True

    return all(_relationship_is_set(device, field) for field in required_fields)


async def rack_needs_generation(client: InfrahubClient, rack: LocationRack) -> bool:
    """Return True when a rack's generated state is missing or incomplete."""
    if not _value(getattr(rack, "generation_complete", None), False):
        logger.info("Rack %s generation_complete is false", getattr(getattr(rack, "name", None), "value", rack.id))
        return True

    devices = await client.filters(kind=DcimDevice, rack__ids=[rack.id])
    expected_leafs = _int_value(rack, "amount_of_leafs")
    expected_l2leafs = _int_value(rack, "amount_of_l2leafs")
    leafs = [device for device in devices if _role_value(device) == "leaf"]
    l2leafs = [device for device in devices if _role_value(device) == "l2leaf"]

    if len(leafs) != expected_leafs:
        logger.info("Rack %s has %s leafs, expected %s", rack.id, len(leafs), expected_leafs)
        return True

    if len(l2leafs) != expected_l2leafs:
        logger.info("Rack %s has %s l2leafs, expected %s", rack.id, len(l2leafs), expected_l2leafs)
        return True

    for device in devices:
        if not device_has_expected_resources(device):
            logger.info("Rack %s device %s is missing generated resources", rack.id, device.id)
            return True

    return False


async def pod_needs_generation(client: InfrahubClient, pod: NetworkPod) -> bool:
    """Return True when a pod's generated state or any child rack state is incomplete."""
    if _role_value(pod) == "fabric":
        return False

    if not _relationship_is_set(pod, "prefix_pool") or not _relationship_is_set(pod, "loopback_pool"):
        logger.info("Pod %s is missing generated prefix or loopback pools", pod.id)
        return True

    spines = await client.filters(kind=DcimDevice, pod__ids=[pod.id], role__value="spine")
    expected_spines = _int_value(pod, "amount_of_spines")
    if len(spines) != expected_spines:
        logger.info("Pod %s has %s spines, expected %s", pod.id, len(spines), expected_spines)
        return True

    for spine in spines:
        if not device_has_expected_resources(spine):
            logger.info("Pod %s spine %s is missing generated resources", pod.id, spine.id)
            return True

    racks = await client.filters(kind="LocationRack", pod__ids=[pod.id])
    for rack_node in racks:
        rack = cast("LocationRack", rack_node)
        if await rack_needs_generation(client, rack):
            return True

    return False


async def get_pods_needing_generation(
    client: InfrahubClient, fabric_id: str, *, exclude_pod_ids: Iterable[str] = ()
) -> list[str]:
    """Return non-fabric pod IDs whose generated state requires recovery."""
    excluded = set(exclude_pod_ids)
    pods = await client.filters(kind="NetworkPod", parent__ids=[fabric_id])
    pod_ids: list[str] = []
    for pod_node in pods:
        pod = cast("NetworkPod", pod_node)
        if pod.id in excluded:
            continue
        if await pod_needs_generation(client, pod):
            pod_ids.append(pod.id)
    return pod_ids


async def get_racks_needing_generation(
    client: InfrahubClient, pod_id: str, *, exclude_rack_ids: Iterable[str] = ()
) -> list[str]:
    """Return rack IDs under a pod whose generated state requires recovery."""
    excluded = set(exclude_rack_ids)
    racks = await client.filters(kind="LocationRack", pod__ids=[pod_id])
    rack_ids: list[str] = []
    for rack_node in racks:
        rack = cast("LocationRack", rack_node)
        if rack.id in excluded:
            continue
        if await rack_needs_generation(client, rack):
            rack_ids.append(rack.id)
    return rack_ids


async def _relationship_node_or_peer(relationship: Any) -> Any | None:
    if not relationship:
        return None

    node = _safe_getattr(relationship, "node")
    if node:
        return node

    if _safe_getattr(relationship, "id") and hasattr(relationship, "fetch"):
        await relationship.fetch()
        return _safe_getattr(relationship, "peer")

    return None


async def _collect_fabric_devices(client: InfrahubClient, fabric_id: str) -> list[DcimDevice]:
    pods = await client.filters(kind="NetworkPod", parent__ids=[fabric_id])
    if not pods:
        return []

    devices: list[DcimDevice] = []
    seen_ids: set[str] = set()
    for pod in pods:
        for device_node in await client.filters(kind=DcimDevice, pod__ids=[pod.id]):
            device = cast("DcimDevice", device_node)
            if device.id in seen_ids:
                continue
            seen_ids.add(device.id)
            devices.append(device)
    return devices


async def get_fabric_avd_generation_state(client: InfrahubClient, fabric_id: str) -> FabricAvdGenerationState:
    """Inspect AVD artifact, hostvar file, and structured config file presence for fabric devices."""
    devices = await _collect_fabric_devices(client, fabric_id)
    state = FabricAvdGenerationState(
        device_ids=[device.id for device in devices],
        missing_hostvar_device_ids=[],
        missing_structured_config_device_ids=[],
    )

    for device in devices:
        artifact = await _relationship_node_or_peer(getattr(device, "avd_artifact", None))
        if artifact is None:
            state.missing_hostvar_device_ids.append(device.id)
            continue

        hostvar_file = await _relationship_node_or_peer(getattr(artifact, "hostvar_file", None))
        if hostvar_file is None:
            state.missing_hostvar_device_ids.append(device.id)
            continue

        structured_config_file = await _relationship_node_or_peer(getattr(artifact, "structured_config_file", None))
        if structured_config_file is None:
            state.missing_structured_config_device_ids.append(device.id)

    return state


async def _trigger_generator(client: InfrahubClient, name: str, nodes: Sequence[str] | None = None) -> None:
    """Trigger a generator by name via CoreGeneratorDefinition mutation.

    When ``nodes`` is provided, Infrahub runs the generator only for those target
    node IDs. Omitting ``nodes`` preserves the previous global trigger behavior.
    """
    generator_defs = await client.filters(kind="CoreGeneratorDefinition", name__value=name)
    if not generator_defs:
        logger.error("Could not find CoreGeneratorDefinition '%s'", name)
        return

    generator_def = generator_defs[0]
    logger.info("Triggering %s via CoreGeneratorDefinitionRun for %s with nodes=%s", name, generator_def.id, nodes)

    if nodes is None:
        await client.execute_graphql(
            query="""
            mutation RunGenerator($id: String!) {
                CoreGeneratorDefinitionRun(data: { id: $id }) {
                    ok
                }
            }
            """,
            variables={"id": generator_def.id},
        )
        return

    await client.execute_graphql(
        query="""
        mutation RunGenerator($id: String!, $nodes: [String!]) {
            CoreGeneratorDefinitionRun(data: { id: $id, nodes: $nodes }) {
                ok
            }
        }
        """,
        variables={"id": generator_def.id, "nodes": list(nodes)},
    )


async def trigger_pod_generation(client: InfrahubClient, nodes: Sequence[str] | None = None) -> None:
    """Trigger the pod generator, optionally constrained to pod node IDs."""
    await _trigger_generator(client, "generate-pod", nodes=nodes)


async def trigger_rack_generation(client: InfrahubClient, nodes: Sequence[str] | None = None) -> None:
    """Trigger the rack generator, optionally constrained to rack node IDs."""
    await _trigger_generator(client, "generate-rack", nodes=nodes)


async def trigger_hostvar_generation(client: InfrahubClient, nodes: Sequence[str] | None = None) -> None:
    """Trigger the hostvar generator, optionally constrained to device node IDs."""
    await _trigger_generator(client, "generate-avd-device-hostvar", nodes=nodes)


async def trigger_structured_config_generation(client: InfrahubClient, nodes: Sequence[str] | None = None) -> None:
    """Trigger the structured config generator, optionally constrained to fabric node IDs."""
    await _trigger_generator(client, "generate-avd-device-structured-config", nodes=nodes)
