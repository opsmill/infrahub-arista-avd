from __future__ import annotations

from infrahub_sdk.generator import InfrahubGenerator

from pyavd._eos_designs.schema import EosDesigns

# Mapping from Infrahub device roles to AVD types
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
}


def extract_uplinks_from_dict(
    interfaces: list[dict],
    uplink_role: str | None,
    device_id: str,
) -> dict[str, list[str]]:
    """Extract uplink information from device interfaces (dict format).

    Args:
        interfaces: List of interface edge dicts from GraphQL response
        uplink_role: The interface role to filter for uplinks (e.g., "super_spine", "spine")
        device_id: The current device's ID to exclude from endpoints

    Returns:
        Dict with uplink_interfaces, uplink_switches, uplink_switch_interfaces
    """
    if not uplink_role:
        return {
            "uplink_interfaces": [],
            "uplink_switches": [],
            "uplink_switch_interfaces": [],
        }

    uplink_interfaces: list[str] = []
    uplink_switches: list[str] = []
    uplink_switch_interfaces: list[str] = []

    for edge in interfaces:
        interface = edge["node"]
        iface_role = interface.get("role", {})
        if not iface_role or iface_role.get("value") != uplink_role:
            continue

        # Get the remote endpoint from the link
        link = interface.get("link", {}).get("node")
        if link:
            endpoints = link.get("endpoints", {}).get("edges", [])
            for ep_edge in endpoints:
                endpoint = ep_edge.get("node")
                # Skip null endpoints or this interface
                if not endpoint:
                    continue
                if endpoint.get("id") != interface["id"]:
                    remote_device = endpoint.get("device", {}).get("node")
                    if remote_device:
                        # Only add interface when we have a valid link with remote device
                        uplink_interfaces.append(interface["name"]["value"])
                        uplink_switches.append(remote_device["hostname"]["value"])
                        uplink_switch_interfaces.append(endpoint["name"]["value"])

    return {
        "uplink_interfaces": uplink_interfaces,
        "uplink_switches": uplink_switches,
        "uplink_switch_interfaces": uplink_switch_interfaces,
    }


class GenerateAVDDeviceHostvar(InfrahubGenerator):
    async def generate(self, data: dict) -> None:
        device = data["NetworkDevice"]["edges"][0]["node"]
        pod = device["pod"]["node"]
        fabric = pod["parent"]["node"]

        # Extract basic device info
        device_id = device["id"]
        hostname = device["hostname"]["value"]
        role = device["role"]["value"]
        bgp_asn = device["bgp_asn"]["value"] if device.get("bgp_asn") else None
        node_id = device["node_id"]["value"] if device.get("node_id") else None

        # Extract IP addresses
        loopback_ip = None
        if device.get("loopback_ip") and device["loopback_ip"].get("node"):
            loopback_ip = device["loopback_ip"]["node"]["address"]["value"]
            # Strip CIDR notation if present
            if "/" in loopback_ip:
                loopback_ip = loopback_ip.split("/")[0]

        mgmt_ip = None
        if device.get("mgmt_ip") and device["mgmt_ip"].get("node"):
            mgmt_ip = device["mgmt_ip"]["node"]["address"]["value"]

        # Extract fabric info
        fabric_name = fabric["name"]["value"]
        mgmt_gateway = fabric.get("mgmt_gateway", {}).get("value") if fabric.get("mgmt_gateway") else None

        # Determine uplink role based on device role
        uplink_role = None
        if role == "spine":
            uplink_role = "super_spine"
        elif role == "leaf":
            uplink_role = "spine"

        # Extract uplinks
        uplinks = extract_uplinks_from_dict(
            device["interfaces"]["edges"],
            uplink_role,
            device_id,
        )

        # Map role to AVD type (node_type_key)
        avd_type = ROLE_TO_AVD_TYPE.get(role, role)
        # AVD uses different keys: super_spine (underscore) for the key, but "super-spine" for type value
        node_type_key = "super_spine" if role == "super_spine" else avd_type

        # Build node config (goes in node_type_key.nodes array)
        node_config: dict[str, any] = {"name": hostname}

        if node_id is not None:
            node_config["id"] = node_id
        if bgp_asn is not None:
            node_config["bgp_as"] = str(bgp_asn)
        if loopback_ip:
            node_config["loopback_ipv4_address"] = loopback_ip
            node_config["loopback_ipv4_pool"] = "10.255.0.0/24"
        if mgmt_ip:
            node_config["mgmt_ip"] = mgmt_ip

        node_config["uplink_ipv4_pool"] = "10.250.0.0/16"
        node_config["vtep_loopback_ipv4_pool"] = "10.251.0.0/24" # Move to auto generated when creating devices

        # Add uplink configuration for spine and leaf devices
        if uplinks["uplink_interfaces"]:
            node_config["uplink_interfaces"] = uplinks["uplink_interfaces"]
            node_config["uplink_switches"] = uplinks["uplink_switches"]
            node_config["uplink_switch_interfaces"] = uplinks["uplink_switch_interfaces"]

        # Build complete pyAVD hostvars structure
        hostvars: dict[str, any] = {
            "type": avd_type,
            "fabric_name": fabric_name,
        }

        if mgmt_gateway:
            hostvars["mgmt_gateway"] = mgmt_gateway

        # Add node type configuration
        hostvars[node_type_key] = {
            "nodes": [node_config],
        }

        # Print for debugging
        print(f"\n=== AVD Device Hostvar for {hostname} ===")
        print(f"Device: {hostname}")
        print(f"Role: {role} -> AVD type: {avd_type}")
        print(f"Node type key: {node_type_key}")

        print(f"\nNode config:")
        for key, value in node_config.items():
            print(f"  {key}: {value}")

        print(f"\nFull hostvars structure:")
        import json
        print(json.dumps(hostvars, indent=2))

        response = await self.client.object_store.upload(content=json.dumps(hostvars))
        avd_artifact = await self.client.create(kind="AvdArtifact", name=hostname, hostvar_checksum=response['checksum'], hostvar_identifier=response['identifier'], device=device_id)
        await avd_artifact.save(allow_upsert=True)

        