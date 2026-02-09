from __future__ import annotations

from typing import Any

from infrahub_sdk import InfrahubClient
from infrahub_sdk.generator import InfrahubGenerator
from netutils.vlan import vlanlist_to_config
from pyavd._eos_designs.schema import EosDesigns

from solution_ai_dc.generator import set_fabric_avd_hostvars_ready
from solution_ai_dc.protocols import AvdArtifact

from .generate_avd_device_inputs_query import GenerateAvdDeviceInputsQuery, GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces

# Mapping from Infrahub device roles to AVD types
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
}

async def check_fabric_hostvars_ready(client: InfrahubClient, fabric: str) -> bool:
    fabric = await client.get("NetworkFabric", id=fabric, include=["children"], prefetch_relationships=True)

    devices = set()
    for pod_peer in fabric.children.peers:
        pod = pod_peer.peer
        await pod.devices.fetch()
        await pod.racks.fetch()

        for device_peer in pod.devices.peers:
            devices.add(device_peer.peer)
        
        for rack_peer in pod.racks.peers:
            rack = rack_peer.peer
            await rack.devices.fetch()

            for device_peer in rack.devices.peers:
                devices.add(device_peer.peer)

    for device in devices:
        if not device.avd_artifact.id:
            return False

        await device.avd_artifact.fetch()

        if not device.avd_artifact.peer.hostvar_identifier.value:
            return False

    await set_fabric_avd_hostvars_ready(client, fabric.id, True)
    return True
    

def extract_uplinks_from_dict(
    interfaces: GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces,
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
        interface = edge.node
        iface_role = interface.role
        if not iface_role or iface_role.value != uplink_role:
            continue

        # Get the remote endpoint from the link
        link = interface.link.node
        if link:
            endpoints = link.endpoints.edges
            for ep_edge in endpoints:
                endpoint = ep_edge.node
                # Skip null endpoints or this interface
                if not endpoint:
                    continue
                if endpoint.id != interface.id:
                    remote_device = endpoint.device.node
                    if remote_device:
                        # Only add interface when we have a valid link with remote device
                        uplink_interfaces.append(interface.name.value)
                        uplink_switches.append(remote_device.hostname.value)
                        uplink_switch_interfaces.append(endpoint.name.value)

    return {
        "uplink_interfaces": uplink_interfaces,
        "uplink_switches": uplink_switches,
        "uplink_switch_interfaces": uplink_switch_interfaces,
    }


def extract_connected_endpoints(
    interfaces: GenerateAvdDeviceInputsQueryNetworkDeviceEdgesNodeInterfaces,
    hostname: str,
) -> list[dict]:
    """Extract connected endpoints (servers) from device interfaces.

    Args:
        interfaces: List of interface edge dicts from GraphQL response
        hostname: Current device hostname (for switch_ports reference)

    Returns:
        List of server endpoint configs for pyAVD
    """
    servers: dict[str, dict] = {}  # Group by remote device name

    for edge in interfaces:
        interface = edge.node
        iface_role = interface.role
        if not iface_role or iface_role.value != "server":
            continue

        # Get the remote endpoint from the link
        link = interface.link.node
        if not link:
            continue

        # Extract VLAN information (only active VLANs)
        tagged_vlans: list[int] = []
        tagged_vlan_edges = interface.tagged_vlan.edges
        for vlan_edge in tagged_vlan_edges:
            vlan_node = vlan_edge.node
            status = vlan_node.status.value
            if status != "active":
                continue
            vlan_id = vlan_node.vlan_id.value
            if vlan_id:
                tagged_vlans.append(vlan_id)

        untagged_vlan = None
        untagged_vlan_node = interface.untagged_vlan.node
        if untagged_vlan_node:
            status = untagged_vlan_node.status.node
            if status == "active":
                untagged_vlan = untagged_vlan_node.vlan_id.value

        endpoints = link.endpoints.edges
        for ep_edge in endpoints:
            endpoint = ep_edge.node
            if not endpoint:
                continue
            # Skip this interface, find the remote one
            if endpoint.id != interface.id:
                remote_device = endpoint.device.node
                if remote_device:
                    server_name = remote_device.hostname.value
                    endpoint_port = endpoint.name.value
                    switch_port = interface.name.value

                    # Group adapters by server
                    if server_name not in servers:
                        servers[server_name] = {
                            "name": server_name,
                            "adapters": [],
                        }

                    # Build adapter config
                    adapter: dict = {
                        "endpoint_ports": [endpoint_port],
                        "switch_ports": [switch_port],
                        "switches": [hostname],
                    }

                    # Determine mode and add VLAN config
                    if tagged_vlans:
                        adapter["mode"] = "trunk"
                        # Use netutils to convert VLAN list to config string
                        vlan_str = vlanlist_to_config(sorted(tagged_vlans))[0]
                        adapter["vlans"] = vlan_str
                        if untagged_vlan:
                            adapter["native_vlan"] = untagged_vlan
                    elif untagged_vlan:
                        adapter["mode"] = "access"
                        adapter["vlans"] = str(untagged_vlan)

                    servers[server_name]["adapters"].append(adapter)

    return list(servers.values())


class GenerateAVDDeviceHostvar(InfrahubGenerator):
    async def generate(self, data: dict) -> None:
        data: GenerateAvdDeviceInputsQuery = GenerateAvdDeviceInputsQuery(**data)
        device = data.network_device.edges[0].node
        pod = device.pod.node
        fabric = pod.parent.node

        # Extract basic device info
        device_id = device.id
        hostname = device.hostname.value
        role = device.role.value
        bgp_asn = device.bgp_asn.value if device.bgp_asn else None
        node_id = device.node_id.value if device.node_id else None

        # Extract IP addresses
        loopback_ip = None
        if device.loopback_ip and device.loopback_ip.node:
            loopback_ip = device.loopback_ip.node.address.value
            # Strip CIDR notation if present
            if "/" in loopback_ip:
                loopback_ip = loopback_ip.split("/")[0]

        mgmt_ip = None
        if device.mgmt_ip and device.mgmt_ip.node:
            mgmt_ip = device.mgmt_ip.node.address.value

        # Extract fabric info
        fabric_name = fabric.name.value
        mgmt_gateway = fabric.mgmt_gateway.value if fabric.mgmt_gateway else None

        # Determine uplink role based on device role
        uplink_role = None
        if role == "spine":
            uplink_role = "super_spine"
        elif role == "leaf":
            uplink_role = "spine"

        # Extract uplinks
        uplinks = extract_uplinks_from_dict(
            device.interfaces.edges,
            uplink_role,
            device_id,
        )

        # Extract connected endpoints (servers)
        connected_endpoints = extract_connected_endpoints(
            device.interfaces.edges,
            hostname,
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

        # Add connected endpoints (servers) if any
        if connected_endpoints:
            hostvars["servers"] = connected_endpoints

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
        avd_artifact = await self.client.create(AvdArtifact, name=hostname, hostvar_checksum=response['checksum'], hostvar_identifier=response['identifier'], device=device_id)
        await avd_artifact.save(allow_upsert=True)

        
