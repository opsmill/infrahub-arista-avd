from __future__ import annotations

from typing import Any, TypedDict

from infrahub_sdk import InfrahubClient
from infrahub_sdk.generator import InfrahubGenerator
from netutils.interface import sort_interface_list
from netutils.vlan import vlanlist_to_config

from solution_ai_dc.generator import set_fabric_avd_hostvars_ready, trigger_structured_config_generation
from solution_ai_dc.protocols import AvdArtifact, AvdHostvarFile, NetworkPod

from .generate_avd_device_inputs_query import (
    GenerateAvdDeviceInputsQuery,
    GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges,
    GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical,
)


class UplinkData(TypedDict):
    uplink_interfaces: list[str]
    uplink_switches: list[str]
    uplink_switch_interfaces: list[str]


class ServerEndpoint(TypedDict):
    name: str
    adapters: list[dict[str, Any]]


# Mapping from Infrahub device roles to AVD types
ROLE_TO_AVD_TYPE: dict[str, str] = {
    "super_spine": "super-spine",
    "spine": "spine",
    "leaf": "l3leaf",
}


async def check_fabric_hostvars_ready(client: InfrahubClient, fabric_id: str) -> bool:
    pods = await client.filters(NetworkPod, parent__ids=[fabric_id])

    devices = set()
    for pod in pods:
        await pod.devices.fetch()
        await pod.racks.fetch()

        devices.update(device_peer.peer for device_peer in pod.devices.peers)

        for rack_peer in pod.racks.peers:
            rack = rack_peer.peer
            await rack.devices.fetch()

            devices.update(device_peer.peer for device_peer in rack.devices.peers)

    for device in devices:
        if not device.avd_artifact.id:
            return False

        await device.avd_artifact.fetch()
        artifact = device.avd_artifact.peer

        await artifact.hostvar_file.fetch()
        if not artifact.hostvar_file.id:
            return False

    await set_fabric_avd_hostvars_ready(client, fabric_id, True)
    await trigger_structured_config_generation(client)
    return True


def extract_uplinks_from_dict(
    interfaces: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges],
    uplink_role: str | None,
    device_id: str,
) -> UplinkData:
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
        if not isinstance(
            interface, GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical
        ):
            continue
        iface_role = interface.role
        if not iface_role or iface_role.value != uplink_role:
            continue

        # Get the remote endpoint from the link
        link = interface.connector.node
        if link:
            endpoints = link.connected_endpoints.edges or []
            for ep_edge in endpoints:
                endpoint = ep_edge.node
                # Skip null endpoints or this interface
                if not endpoint:
                    continue
                if endpoint.id != interface.id and hasattr(endpoint, "device"):
                    remote_device = endpoint.device.node
                    if remote_device:
                        # Only add interface when we have a valid link with remote device
                        uplink_interfaces.append(interface.name.value)
                        uplink_switches.append(remote_device.name.value)
                        uplink_switch_interfaces.append(endpoint.name.value)

    # Sort all three lists in lockstep by local interface name to ensure
    # deterministic ordering regardless of GraphQL return order.
    # This prevents P2P IP address changes when Neo4j returns interfaces
    # in a different order (e.g., after adding server interfaces).
    if uplink_interfaces:
        sorted_names = sort_interface_list(uplink_interfaces)
        name_to_idx = {name: i for i, name in enumerate(uplink_interfaces)}
        sorted_indices = [name_to_idx[name] for name in sorted_names]
        uplink_interfaces = [uplink_interfaces[i] for i in sorted_indices]
        uplink_switches = [uplink_switches[i] for i in sorted_indices]
        uplink_switch_interfaces = [uplink_switch_interfaces[i] for i in sorted_indices]

    return {
        "uplink_interfaces": uplink_interfaces,
        "uplink_switches": uplink_switches,
        "uplink_switch_interfaces": uplink_switch_interfaces,
    }


def _sort_server_endpoints(servers: dict[str, ServerEndpoint]) -> list[ServerEndpoint]:
    """Sort servers by name and adapters within each server by switch port."""
    sorted_servers = sorted(servers.values(), key=lambda s: s["name"])
    for server in sorted_servers:
        server["adapters"].sort(key=lambda a: sort_interface_list(a["switch_ports"])[0] if a["switch_ports"] else "")
    return sorted_servers


def extract_connected_endpoints(
    interfaces: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges],
    hostname: str,
) -> list[ServerEndpoint]:
    """Extract connected endpoints (servers) from device interfaces.

    Args:
        interfaces: List of interface edge dicts from GraphQL response
        hostname: Current device hostname (for switch_ports reference)

    Returns:
        List of server endpoint configs for pyAVD
    """
    servers: dict[str, ServerEndpoint] = {}  # Group by remote device name

    for edge in interfaces:
        interface = edge.node
        if not isinstance(
            interface, GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical
        ):
            continue
        iface_role = interface.role
        if not iface_role or iface_role.value != "server":
            continue

        # Get the remote endpoint from the connector
        link = interface.connector.node
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

        endpoints = link.connected_endpoints.edges or []
        for ep_edge in endpoints:
            endpoint = ep_edge.node
            if not endpoint:
                continue
            # Skip this interface, find the remote one
            if endpoint.id != interface.id and hasattr(endpoint, "device"):
                remote_device = endpoint.device.node
                if remote_device:
                    server_name = remote_device.name.value
                    endpoint_port = endpoint.name.value
                    switch_port = interface.name.value

                    # Group adapters by server
                    if server_name not in servers:
                        servers[server_name] = {
                            "name": server_name,
                            "adapters": [],
                        }

                    # Build adapter config
                    adapter: dict[str, Any] = {
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

    return _sort_server_endpoints(servers)


class GenerateAVDDeviceHostvar(InfrahubGenerator):
    async def _build_tenants_hostvars(self, fabric_id: str) -> list[dict[str, Any]]:
        """Build AVD-compatible tenants structure from EVPN data.

        Queries EvpnTenants assigned to the given fabric and builds
        the tenants/VRFs/SVIs/L2VLANs structure AVD expects.
        """
        try:
            tenants = await self.client.filters(kind="EvpnTenant", fabrics__ids=[fabric_id])
        except (AttributeError, KeyError):
            return []

        if not tenants:
            return []

        tenants_list: list[dict[str, Any]] = []
        for tenant in tenants:
            tenant_data: dict[str, Any] = {
                "name": tenant.name.value,
                "mac_vrf_vni_base": tenant.mac_vrf_vni_base.value,
            }

            # Fetch VRFs for this tenant
            await tenant.vrfs.fetch()
            vrfs_list: list[dict[str, Any]] = []
            for vrf_peer in tenant.vrfs.peers:
                vrf = vrf_peer.peer
                vrf_data: dict[str, Any] = {"name": vrf.name.value}

                vrf_vni = getattr(vrf, "vrf_vni", None)
                if vrf_vni and vrf_vni.value is not None:
                    vrf_data["vrf_vni"] = vrf_vni.value

                vtep_diag_lo = getattr(vrf, "vtep_diagnostic_loopback", None)
                vtep_diag_ip = getattr(vrf, "vtep_diagnostic_loopback_ip_range", None)
                if vtep_diag_lo and vtep_diag_lo.value is not None:
                    vrf_data["vtep_diagnostic"] = {"loopback": vtep_diag_lo.value}
                    if vtep_diag_ip and vtep_diag_ip.value:
                        vrf_data["vtep_diagnostic"]["loopback_ip_range"] = str(vtep_diag_ip.value)

                # Fetch SVIs for this VRF
                await vrf.svis.fetch()
                svis_list: list[dict[str, Any]] = []
                for svi_peer in vrf.svis.peers:
                    svi = svi_peer.peer
                    svi_data: dict[str, Any] = {
                        "id": svi.svi_id.value,
                        "name": svi.name.value,
                        "enabled": svi.enabled.value,
                    }
                    if svi.ip_address_virtual and svi.ip_address_virtual.value:
                        svi_data["ip_address_virtual"] = str(svi.ip_address_virtual.value)
                    svis_list.append(svi_data)

                if svis_list:
                    vrf_data["svis"] = svis_list
                vrfs_list.append(vrf_data)

            if vrfs_list:
                tenant_data["vrfs"] = vrfs_list

            # Fetch L2 VLANs for this tenant
            await tenant.l2vlans.fetch()
            l2vlans_list: list[dict[str, Any]] = []
            for l2v_peer in tenant.l2vlans.peers:
                l2vlan = l2v_peer.peer
                l2v_data: dict[str, Any] = {"id": l2vlan.vlan_id.value}
                vni_override = getattr(l2vlan, "vni_override", None)
                if vni_override and vni_override.value is not None:
                    l2v_data["vni"] = vni_override.value
                l2vlans_list.append(l2v_data)

            if l2vlans_list:
                tenant_data["l2vlans"] = l2vlans_list

            tenants_list.append(tenant_data)

        return tenants_list

    async def _extract_pool_name(self, pool_ref: object, pool_kind: str) -> str | None:
        """Extract pool name from a relationship reference."""
        if pool_ref and pool_ref.node:
            pool = await self.client.get(kind=pool_kind, id=pool_ref.node.id)
            return pool.name.value if hasattr(pool, "name") else None
        return None

    @staticmethod
    def _get_attr_value(obj: object, attr_name: str) -> str | int | bool | None:
        """Safely get an attribute value from a GraphQL node."""
        attr = getattr(obj, attr_name, None)
        return attr.value if attr else None

    async def _extract_l3ls_pools(self, fabric: object, pod: object) -> dict[str, str | None]:
        """Extract configurable IP pools from fabric/pod with hardcoded fallbacks."""
        uplink = await self._extract_pool_name(getattr(fabric, "uplink_pool", None), "CoreIPPrefixPool")
        vtep = await self._extract_pool_name(getattr(fabric, "vtep_pool", None), "CoreIPPrefixPool")
        mlag_peer = await self._extract_pool_name(getattr(pod, "mlag_peer_pool", None), "CoreIPAddressPool")
        mlag_l3 = await self._extract_pool_name(getattr(pod, "mlag_l3_pool", None), "CoreIPAddressPool")

        return {
            "uplink_ipv4_pool": uplink or "10.250.0.0/16",
            "vtep_loopback_ipv4_pool": vtep or "10.251.0.0/24",
            "mlag_peer_ipv4_pool": mlag_peer,
            "mlag_peer_l3_ipv4_pool": mlag_l3,
        }

    @staticmethod
    def _extract_mlag_info(device: object) -> dict[str, str | None]:
        """Extract MLAG domain info for a device."""
        device_mlag_domain = getattr(device, "mlag_domain", None)
        if not device_mlag_domain or not device_mlag_domain.node:
            return {"domain_id": None, "virtual_router_mac": None}

        mlag_domain = device_mlag_domain.node
        domain_id = mlag_domain.domain_id.value if mlag_domain.domain_id else None
        vrmac = getattr(mlag_domain, "virtual_router_mac", None)

        return {
            "domain_id": domain_id,
            "virtual_router_mac": vrmac.value if vrmac else None,
        }

    @staticmethod
    def _build_hostvars(
        *,
        hostname: str,
        role: str,
        bgp_asn: int | None,
        node_id: int | None,
        loopback_ip: str | None,
        mgmt_ip: str | None,
        fabric_name: str,
        mgmt_gateway: str | None,
        virtual_router_mac: str | None,
        underlay_routing_protocol: str | None,
        overlay_routing_protocol: str | None,
        p2p_uplinks_mtu: int | None,
        pools: dict[str, str | None],
        uplinks: UplinkData,
        mlag_info: dict[str, str | None],
        tenants_data: list[dict[str, Any]],
        connected_endpoints: list[ServerEndpoint],
    ) -> dict[str, Any]:
        """Build the complete pyAVD hostvars structure."""
        avd_type = ROLE_TO_AVD_TYPE.get(role, role)
        node_type_key = "super_spine" if role == "super_spine" else avd_type

        # Build node config
        node_config: dict[str, Any] = {"name": hostname}
        if node_id is not None:
            node_config["id"] = node_id
        if bgp_asn is not None:
            node_config["bgp_as"] = str(bgp_asn)
        if loopback_ip:
            node_config["loopback_ipv4_address"] = loopback_ip
            node_config["loopback_ipv4_pool"] = "10.255.0.0/24"
        if mgmt_ip:
            node_config["mgmt_ip"] = mgmt_ip

        node_config["uplink_ipv4_pool"] = pools["uplink_ipv4_pool"]
        node_config["vtep_loopback_ipv4_pool"] = pools["vtep_loopback_ipv4_pool"]

        if pools["mlag_peer_ipv4_pool"]:
            node_config["mlag_peer_ipv4_pool"] = pools["mlag_peer_ipv4_pool"]
        if pools["mlag_peer_l3_ipv4_pool"]:
            node_config["mlag_peer_l3_ipv4_pool"] = pools["mlag_peer_l3_ipv4_pool"]

        if uplinks["uplink_interfaces"]:
            node_config["uplink_interfaces"] = uplinks["uplink_interfaces"]
            node_config["uplink_switches"] = uplinks["uplink_switches"]
            node_config["uplink_switch_interfaces"] = uplinks["uplink_switch_interfaces"]

        # Build hostvars
        hostvars: dict[str, Any] = {"type": avd_type, "fabric_name": fabric_name}

        if mgmt_gateway:
            hostvars["mgmt_gateway"] = mgmt_gateway
        if virtual_router_mac:
            hostvars["virtual_router_mac_address"] = virtual_router_mac
        if underlay_routing_protocol:
            hostvars["underlay_routing_protocol"] = underlay_routing_protocol
        if overlay_routing_protocol:
            hostvars["overlay_routing_protocol"] = overlay_routing_protocol
        if p2p_uplinks_mtu:
            hostvars["p2p_uplinks_mtu"] = p2p_uplinks_mtu

        hostvars[node_type_key] = {"nodes": [node_config]}

        # Add MLAG node_group for leaf devices
        if mlag_info["domain_id"] and role == "leaf":
            effective_vrmac = mlag_info["virtual_router_mac"] or virtual_router_mac
            node_group: dict[str, Any] = {"group": mlag_info["domain_id"]}
            if effective_vrmac:
                node_group["virtual_router_mac_address"] = effective_vrmac
            hostvars[node_type_key]["node_groups"] = [node_group]

        if tenants_data:
            hostvars["tenants"] = tenants_data
        if connected_endpoints:
            hostvars["servers"] = connected_endpoints

        return hostvars

    async def generate(self, data: dict) -> None:
        data: GenerateAvdDeviceInputsQuery = GenerateAvdDeviceInputsQuery(**data)
        device = data.dcim_device.edges[0].node
        pod = device.pod.node
        fabric = pod.parent.node

        # Mark hostvars as not ready while regenerating
        await set_fabric_avd_hostvars_ready(self.client, fabric.id, False)

        # Extract basic device info
        device_id = device.id
        hostname = device.name.value
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
        iface_edges = device.interfaces.edges or []
        uplinks = extract_uplinks_from_dict(iface_edges, uplink_role, device_id)

        # Extract connected endpoints (servers)
        connected_endpoints = extract_connected_endpoints(iface_edges, hostname)

        # Extract fabric L3LS settings (with backwards-compatible fallbacks)
        virtual_router_mac = self._get_attr_value(fabric, "virtual_router_mac")
        underlay_routing_protocol = self._get_attr_value(fabric, "underlay_routing_protocol")
        overlay_routing_protocol = self._get_attr_value(fabric, "overlay_routing_protocol")
        p2p_uplinks_mtu = self._get_attr_value(fabric, "p2p_uplinks_mtu")

        # Extract configurable IP pools
        pools = await self._extract_l3ls_pools(fabric, pod)

        # Extract MLAG domain info for leaf devices
        mlag_info = self._extract_mlag_info(device)

        # Fetch EVPN tenants for this fabric
        tenants_data = await self._build_tenants_hostvars(fabric.id)

        hostvars = self._build_hostvars(
            hostname=hostname,
            role=role,
            bgp_asn=bgp_asn,
            node_id=node_id,
            loopback_ip=loopback_ip,
            mgmt_ip=mgmt_ip,
            fabric_name=fabric_name,
            mgmt_gateway=mgmt_gateway,
            virtual_router_mac=virtual_router_mac,
            underlay_routing_protocol=underlay_routing_protocol,
            overlay_routing_protocol=overlay_routing_protocol,
            p2p_uplinks_mtu=p2p_uplinks_mtu,
            pools=pools,
            uplinks=uplinks,
            mlag_info=mlag_info,
            tenants_data=tenants_data,
            connected_endpoints=connected_endpoints,
        )

        # Print for debugging
        import json

        print(f"\n=== AVD Device Hostvar for {hostname} ===")
        print(f"Device: {hostname}")
        print(f"Role: {role}")
        print("\nFull hostvars structure:")
        print(json.dumps(hostvars, indent=2))

        avd_artifact = await self.client.create(
            AvdArtifact,
            name=hostname,
            device=device_id,
            member_of_groups=["avd_artifacts"],
        )
        await avd_artifact.save(allow_upsert=True)

        hostvar_file = await self.client.create(
            AvdHostvarFile,
            artifact=avd_artifact,
        )
        hostvar_file.upload_from_bytes(content=json.dumps(hostvars, indent=2).encode(), name=f"{hostname}-hostvars.json")
        await hostvar_file.save(allow_upsert=True)

        await check_fabric_hostvars_ready(self.client, fabric.id)
