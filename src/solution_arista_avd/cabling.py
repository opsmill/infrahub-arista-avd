from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .protocols import DcimDevice, DcimInterface, InterfacePhysical, NetworkLink

if TYPE_CHECKING:
    import logging

    from infrahub_sdk import InfrahubClient


@dataclass(frozen=True)
class _LinkSpec:
    src_interface: DcimInterface
    dst_interface: DcimInterface
    name: str


def build_pod_cabling_plan(
    pod_index: int,
    src_interface_map: dict[DcimDevice, list[DcimInterface]],
    dst_interface_map: dict[DcimDevice, list[DcimInterface]],
) -> list[tuple[DcimInterface, DcimInterface]]:
    """Builds a cabling plan between source and destination interfaces based on Indexes.

    See tests/unit/test_cabling.py for the behavioural contract.
    """
    dst_devices = list(dst_interface_map.keys())
    dst_device_count = len(dst_devices)
    dst_interface_base_index = (pod_index - 2) * len(dst_interface_map)
    src_index = 0

    cabling_plan: list[tuple[DcimInterface, DcimInterface]] = []

    for src_interfaces in src_interface_map.values():
        dst_interface_index = dst_interface_base_index + src_index

        for dst_index, src_interface in enumerate(src_interfaces[:dst_device_count]):
            dst_interface = dst_interface_map[dst_devices[dst_index]][dst_interface_index]

            cabling_plan.append((src_interface, dst_interface))

        src_index += 1  # noqa: SIM113 replace with enumerate
        dst_interface_index = dst_interface_base_index + src_index

    return cabling_plan


def build_rack_cabling_plan(
    rack_index: int,
    src_interface_map: dict[DcimDevice, list[DcimInterface]],
    dst_interface_map: dict[DcimDevice, list[DcimInterface]],
) -> list[tuple[DcimInterface, DcimInterface]]:
    cabling_plan: list[tuple[DcimInterface, DcimInterface]] = []
    dst_devices = list(dst_interface_map.keys())
    dst_device_count = len(dst_devices)
    start = (rack_index * 2) - 2
    end = start + 2

    for fallback_index, (src_device, src_interfaces) in enumerate(src_interface_map.items(), start=1):
        src_device_index = _rack_source_device_index(src_device, fallback=fallback_index)

        for dst_index, src_interface in enumerate(src_interfaces[:dst_device_count]):
            dst_interface = dst_interface_map[dst_devices[dst_index]][start:end][src_device_index - 1]
            cabling_plan.append((src_interface, dst_interface))

    return cabling_plan


def _rack_source_device_index(device: DcimDevice, *, fallback: int) -> int:
    value = getattr(getattr(device, "index", None), "value", None)
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdecimal() and int(value) > 0:
        return int(value)

    for name_attr in ("name", "display_label"):
        candidate = getattr(device, name_attr, None)
        name = getattr(candidate, "value", candidate)
        if isinstance(name, str):
            suffix = name.rsplit("-", maxsplit=1)[-1]
            if suffix.isdecimal() and int(suffix) > 0:
                return int(suffix)

    return fallback


def build_server_cabling_plan(
    server_index: int,
    src_interface_map: dict[DcimDevice, list[DcimInterface]],
    dst_interface_map: dict[DcimDevice, list[DcimInterface]],
) -> list[tuple[DcimInterface, DcimInterface]]:
    """Builds a cabling plan connecting server interfaces to leaf switch interfaces.

    Each server interface is paired with a leaf at the given index position,
    round-robin across leaves. Follows the same index-based pattern as
    build_pod_cabling_plan and build_rack_cabling_plan.
    """
    dst_devices = list(dst_interface_map.keys())
    dst_device_count = len(dst_devices)
    cabling_plan: list[tuple[DcimInterface, DcimInterface]] = []

    for src_interfaces in src_interface_map.values():
        for i, src_interface in enumerate(src_interfaces):
            dst_device = dst_devices[i % dst_device_count]
            dst_offset = server_index + (i // dst_device_count)
            dst_interface = dst_interface_map[dst_device][dst_offset]
            cabling_plan.append((src_interface, dst_interface))

    return cabling_plan


async def connect_interface_maps(
    client: InfrahubClient,
    logger: logging.Logger,
    cabling_plan: list[tuple[DcimInterface, DcimInterface]],
    *,
    link_role: str | None = None,
) -> None:
    """Create or reconcile links for an interface cabling plan.

    The default path preserves the existing server-link contract: interface-based
    names and no link role. Inter-switch callers opt into ``link_role="uplink"``.
    Generators leave the link medium unset for users to define. Uplinks use
    device-pair names and only reconcile links already generated with the current
    naming scheme.
    """
    for link_spec in _build_link_specs(cabling_plan, link_role=link_role):
        if link_role == "uplink":
            await _connect_uplink(client, logger, link_spec)
            continue

        network_link = await client.create(kind="NetworkLink", name=link_spec.name)
        await network_link.save(allow_upsert=True)

        src_populated = await _connect_interface_if_missing(client, logger, link_spec.src_interface, network_link)
        dst_populated = await _connect_interface_if_missing(client, logger, link_spec.dst_interface, network_link)

        if src_populated or dst_populated:
            logger.info("Populated missing generated connector(s) for %s", link_spec.name)
        else:
            logger.info("Preserved existing connector state for %s", link_spec.name)


def _build_link_specs(
    cabling_plan: list[tuple[DcimInterface, DcimInterface]], *, link_role: str | None
) -> list[_LinkSpec]:
    indexed_plan = list(enumerate(cabling_plan))
    names_by_index: dict[int, str] = {}

    if link_role == "uplink":
        links_by_device_pair: dict[tuple[str, str], list[tuple[int, DcimInterface, DcimInterface]]] = defaultdict(list)
        for index, (src_interface, dst_interface) in indexed_plan:
            pair = (_device_name(src_interface), _device_name(dst_interface))
            links_by_device_pair[pair].append((index, src_interface, dst_interface))

        for (lower_device, upper_device), links in links_by_device_pair.items():
            base_name = f"Uplink {lower_device}__{upper_device}"
            sorted_links = sorted(
                links,
                key=lambda item: (
                    _natural_sort_key(item[1].name.value),
                    _natural_sort_key(item[2].name.value),
                    item[1].id,
                    item[2].id,
                ),
            )
            for sequence, (index, _src_interface, _dst_interface) in enumerate(sorted_links, start=1):
                name = f"{base_name} {sequence}" if len(sorted_links) > 1 else base_name
                names_by_index[index] = name

    specs: list[_LinkSpec] = []
    for index, (src_interface, dst_interface) in indexed_plan:
        name = names_by_index.get(index, _interface_link_name(src_interface, dst_interface))
        specs.append(
            _LinkSpec(
                src_interface=src_interface,
                dst_interface=dst_interface,
                name=name,
            )
        )
    return specs


def _device_name(interface: DcimInterface) -> str:
    device = getattr(interface.device, "peer", None)
    device_name = getattr(getattr(device, "name", None), "value", None)
    if isinstance(device_name, str):
        return device_name

    display_label = interface.device.display_label
    value = getattr(display_label, "value", display_label)
    return str(value)


def _interface_link_name(src_interface: DcimInterface, dst_interface: DcimInterface) -> str:
    return (
        f"{_device_name(src_interface)}-{src_interface.name.value}"
        f"__{_device_name(dst_interface)}-{dst_interface.name.value}"
    )


def _natural_sort_key(value: str) -> tuple[tuple[int, str | int], ...]:
    return tuple((1, int(part)) if part.isdecimal() else (0, part.casefold()) for part in re.split(r"(\d+)", value))


async def _connect_uplink(client: InfrahubClient, logger: logging.Logger, link_spec: _LinkSpec) -> None:
    src_interface = await _get_physical_interface(client, link_spec.src_interface)
    dst_interface = await _get_physical_interface(client, link_spec.dst_interface)
    src_connector_id = _relationship_node_id(getattr(src_interface, "connector", None))
    dst_connector_id = _relationship_node_id(getattr(dst_interface, "connector", None))
    connector_ids = {connector_id for connector_id in (src_connector_id, dst_connector_id) if connector_id}

    network_link: object | None = None
    if len(connector_ids) > 1:
        logger.warning(
            "Skipped uplink reconciliation for %s: endpoint connectors conflict (%s)",
            link_spec.name,
            ", ".join(sorted(connector_ids)),
        )
        return

    if connector_ids:
        connector_id = next(iter(connector_ids))
        attached_link = await client.get(NetworkLink, id=connector_id)
        if _node_attribute_value(attached_link, "name") != link_spec.name:
            logger.warning(
                "Preserved existing connector %s for intended uplink %s",
                connector_id,
                link_spec.name,
            )
            return

        network_link = attached_link
        await _ensure_generated_uplink_role(network_link)
        logger.info("Reconciled generated uplink %s", link_spec.name)

    if network_link is None:
        network_link = await client.create(
            kind="NetworkLink",
            name=link_spec.name,
            role="uplink",
        )
        await network_link.save(allow_upsert=True)

    src_populated = await _connect_fetched_interface_if_missing(logger, src_interface, network_link)
    dst_populated = await _connect_fetched_interface_if_missing(logger, dst_interface, network_link)

    if src_populated or dst_populated:
        logger.info("Populated missing generated connector(s) for %s", link_spec.name)
    else:
        logger.info("Preserved existing connector state for %s", link_spec.name)


async def _ensure_generated_uplink_role(network_link: object) -> None:
    _set_node_attribute_value(network_link, "role", "uplink")
    await network_link.save(allow_upsert=True)  # type: ignore[attr-defined]


def _node_attribute_value(node: object, attribute_name: str) -> str | None:
    attribute = getattr(node, attribute_name, None)
    value = getattr(attribute, "value", attribute)
    return value if isinstance(value, str) else None


def _set_node_attribute_value(node: object, attribute_name: str, value: str) -> None:
    attribute = getattr(node, attribute_name, None)
    if attribute is not None and hasattr(attribute, "value"):
        attribute.value = value
    else:
        setattr(node, attribute_name, value)


async def _get_physical_interface(client: InfrahubClient, interface: DcimInterface) -> InterfacePhysical:
    # InterfacePhysical is the concrete type exposing DcimEndpoint.connector.
    return await client.get(InterfacePhysical, id=interface.id, include=["connector"])  # type: ignore[type-abstract, no-any-return]


async def _connect_interface_if_missing(
    client: InfrahubClient, logger: logging.Logger, interface: DcimInterface, network_link: object
) -> bool:
    iface = await _get_physical_interface(client, interface)
    return await _connect_fetched_interface_if_missing(logger, iface, network_link)


async def _connect_fetched_interface_if_missing(
    logger: logging.Logger, iface: InterfacePhysical, network_link: object
) -> bool:
    connector_id = _relationship_node_id(getattr(iface, "connector", None))
    network_link_id = getattr(network_link, "id", None)

    if connector_id:
        if network_link_id and connector_id == network_link_id:
            logger.info("Preserved generated connector on %s", iface.display_label)
        else:
            logger.warning(
                "Skipped connector reconciliation for %s: existing connector %s conflicts with generated link %s",
                iface.display_label,
                connector_id,
                getattr(network_link, "name", network_link_id),
            )
        return False

    # SDK accepts protocol kinds at runtime; assigning a node to a relationship is the SDK pattern.
    iface.connector = network_link  # type: ignore[assignment]
    iface.status.value = "active"
    await iface.save(allow_upsert=True)
    logger.info("Populated missing connector on %s", iface.display_label)
    return True


def _relationship_node_id(relationship: object | None) -> str | None:
    if relationship is None:
        return None
    relationship_id = getattr(relationship, "id", None)
    if isinstance(relationship_id, str) and relationship_id:
        return relationship_id
    node = getattr(relationship, "node", None)
    if node is None:
        try:
            node = getattr(relationship, "peer", None)
        except ValueError as exc:
            if str(exc) == "Node must have at least one identifier (ID or HFID) to query it.":
                return None
            raise
    node_id = getattr(node, "id", None)
    if isinstance(node_id, str) and node_id:
        return node_id
    return None
