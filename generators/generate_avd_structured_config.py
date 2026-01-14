"""AVD Structured Config Generator.

This generator reads device.avd_inputs and generates structured config
using pyAVD, storing the result in device.avd_structured_config.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

import pyavd
from infrahub_sdk.generator import InfrahubGenerator


class AvdStructuredConfigGenerator(InfrahubGenerator):
    """Generates and stores AVD structured config for all devices in a fabric."""

    logger = logging.getLogger("infrahub.tasks")

    async def generate(self, data: dict) -> None:
        """Generate AVD structured config for all devices in the fabric."""
        # Get fabric info
        fabric_edges = data.get("NetworkFabric", {}).get("edges", [])
        if not fabric_edges:
            self.logger.warning("No fabric found in query results")
            return

        fabric_node = fabric_edges[0]["node"]
        fabric_name = fabric_node["name"]["value"]
        fabric_id = fabric_node["id"]

        self.logger.info(f"Generating AVD structured config for fabric: {fabric_name}")

        # Get all devices and filter by fabric, collecting their avd_inputs
        device_edges = data.get("NetworkDevice", {}).get("edges", [])
        all_hostvars: dict[str, dict[str, Any]] = {}
        device_map: dict[str, str] = {}  # hostname -> device_id

        for edge in device_edges:
            device = edge["node"]
            # Check if device belongs to this fabric
            pod = device.get("pod", {}).get("node")
            if not pod:
                continue
            parent = pod.get("parent", {}).get("node")
            if not parent or parent.get("id") != fabric_id:
                continue

            hostname = device["hostname"]["value"]
            avd_inputs = device.get("avd_inputs", {})
            avd_inputs_value = avd_inputs.get("value") if avd_inputs else None

            if not avd_inputs_value:
                self.logger.warning(f"Device {hostname} has no avd_inputs, skipping")
                continue

            all_hostvars[hostname] = avd_inputs_value
            device_map[hostname] = device["id"]

        if not all_hostvars:
            self.logger.warning("No devices with avd_inputs found")
            return

        self.logger.info(f"Found {len(all_hostvars)} devices with AVD inputs")

        # Generate AVD facts (requires all devices)
        # Make a deep copy since pyAVD modifies input data in-place
        hostvars_copy = copy.deepcopy(all_hostvars)
        avd_facts = pyavd.get_avd_facts(hostvars_copy)

        # Generate and store structured config per device
        for hostname in all_hostvars:
            device_id = device_map[hostname]

            # Generate structured config for this device
            # Make copies since pyAVD modifies data in-place
            hostvars_copy = copy.deepcopy(all_hostvars)
            structured_config = pyavd.get_device_structured_config(
                hostname,
                hostvars_copy,
                avd_facts,
            )

            # Store structured config in device
            device_obj = await self.client.get(kind="NetworkDevice", id=device_id)
            device_obj.avd_structured_config.value = structured_config
            await device_obj.save()

            self.logger.info(f"Stored AVD structured config for device: {hostname}")
