from __future__ import annotations

from typing import TYPE_CHECKING

from .protocols import DcimDevice, DcimInterface

if TYPE_CHECKING:
    import logging

    from infrahub_sdk import InfrahubClient


def build_pod_cabling_plan(
    pod_index: int,
    src_interface_map: dict[DcimDevice, list[DcimInterface]],
    dst_interface_map: dict[DcimDevice, list[DcimInterface]],
) -> list[tuple[DcimInterface, DcimInterface]]:
    """Builds a cabling plan between source and destination interfaces based on Indexes

    TODO Write unit test to validate that the algorithm works as expected
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

    for src_device, src_interfaces in src_interface_map.items():
        src_device_index: int = src_device.index.value

        for dst_index, src_interface in enumerate(src_interfaces[:dst_device_count]):
            start = (rack_index * 2) - 2
            end = start + 2
            dst_interface = dst_interface_map[dst_devices[dst_index]][start:end][src_device_index - 1]
            cabling_plan.append((src_interface, dst_interface))

    return cabling_plan


async def connect_interface_maps(
    client: InfrahubClient, logger: logging.Logger, cabling_plan: list[tuple[DcimInterface, DcimInterface]]
) -> None:
    for src_interface, dst_interface in cabling_plan:
        name = f"{src_interface.device.display_label}-{src_interface.name.value}__{dst_interface.device.display_label}-{dst_interface.name.value}"
        network_link = await client.create(
            kind="DcimConnector", name=name, medium="copper", connected_endpoints=[src_interface, dst_interface]
        )
        await network_link.save(allow_upsert=True)

        src_interface = await client.get(DcimInterface, id=src_interface.id, include=["connector"])
        dst_interface = await client.get(DcimInterface, id=dst_interface.id, include=["connector"])

        src_interface.status.value = "active"
        dst_interface.status.value = "active"
        await src_interface.save(allow_upsert=True)
        await dst_interface.save(allow_upsert=True)
        logger.info(f"Connected {name}")
