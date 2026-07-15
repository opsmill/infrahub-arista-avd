from __future__ import annotations

import hashlib
import logging
import operator
from typing import TYPE_CHECKING, Any, TypedDict

from infrahub_sdk.generator import InfrahubGenerator
from netutils.interface import sort_interface_list
from netutils.vlan import vlanlist_to_config

from solution_arista_avd.avd import get_avd_type
from solution_arista_avd.generator import set_fabric_avd_hostvars_ready
from solution_arista_avd.protocols import AvdArtifact, AvdHostvarFile, NetworkPod

from .generate_avd_device_inputs_query import (
    GenerateAvdDeviceInputsQuery,
    GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges,
    GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical,
)

if TYPE_CHECKING:
    from infrahub_sdk import InfrahubClient

logger = logging.getLogger("infrahub.tasks")


class UplinkData(TypedDict):
    uplink_interfaces: list[str]
    uplink_switches: list[str]
    uplink_switch_interfaces: list[str]


class ServerEndpoint(TypedDict):
    name: str
    adapters: list[dict[str, Any]]


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

        try:
            await device.avd_artifact.fetch()
            artifact = device.avd_artifact.peer

            if not artifact.hostvar_file.id:
                return False
            await artifact.hostvar_file.fetch()
            if not artifact.hostvar_file.peer:
                return False
        except Exception as exc:  # noqa: BLE001 - any read failure means "not ready yet"
            logger.debug("Hostvar readiness check failed for a device: %s", exc)
            return False

    await set_fabric_avd_hostvars_ready(client, fabric_id, True)
    return True


def extract_uplinks_from_dict(
    interfaces: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges],
    uplink_role: str | None,
    device_id: str,  # noqa: ARG001 — part of the public signature; retained for callers/tests
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
    sorted_servers = sorted(servers.values(), key=operator.itemgetter("name"))
    for server in sorted_servers:
        server["adapters"].sort(key=lambda a: sort_interface_list(a["switch_ports"])[0] if a["switch_ports"] else "")
    return sorted_servers


def extract_connected_endpoints(  # noqa: C901 — endpoint extraction is inherently branchy
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
            status = untagged_vlan_node.status.value
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
                    # Skip L2 leaf devices — AVD handles them via l2leaf type, not connected_endpoints
                    remote_role = getattr(remote_device, "role", None)
                    if remote_role and remote_role.value == "l2leaf":
                        continue

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

                    # Detect port-channel on the remote (server) endpoint
                    endpoint_lag = getattr(endpoint, "lag", None)
                    if endpoint_lag and endpoint_lag.node:
                        lag_node = endpoint_lag.node
                        port_channel: dict[str, str] = {"mode": "active"}
                        lacp_mode = getattr(lag_node, "lacp_mode", None)
                        if lacp_mode and lacp_mode.value:
                            port_channel["mode"] = lacp_mode.value
                        adapter["port_channel"] = port_channel

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

                    # Add spanning tree portfast for server ports
                    adapter["spanning_tree_portfast"] = "edge"

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
                l2v_data: dict[str, Any] = {
                    "id": l2vlan.vlan_id.value,
                    "name": l2vlan.name.value,
                }
                vni_override = getattr(l2vlan, "vni_override", None)
                if vni_override and vni_override.value is not None:
                    l2v_data["vni_override"] = vni_override.value
                l2vlans_list.append(l2v_data)

            if l2vlans_list:
                tenant_data["l2vlans"] = l2vlans_list

            tenants_list.append(tenant_data)

        return tenants_list

    async def _extract_pool_prefix(self, pool_ref: object, pool_kind: str) -> str | None:
        """Extract the first resource prefix from a pool relationship reference."""
        pool_node = getattr(pool_ref, "node", None)
        if pool_ref is None or pool_node is None:
            return None

        pool = await self.client.get(kind=pool_kind, id=pool_node.id, include=["resources"])
        await pool.resources.fetch()

        for resource_peer in pool.resources.peers:
            resource = resource_peer.peer
            # CoreIPPrefixPool resources are IpamPrefix nodes with a prefix attribute
            if hasattr(resource, "prefix"):
                return str(resource.prefix.value)
            # CoreIPAddressPool resources also have prefix
            if hasattr(resource, "address"):
                return str(resource.address.value)

        return None

    @staticmethod
    def _get_first_attr(obj: object, *names: str) -> object | None:
        """Return the first present attribute/relationship by name, preserving falsey objects."""
        for name in names:
            attr = getattr(obj, name, None)
            if attr is not None:
                return attr
        return None

    @staticmethod
    def _get_first_attr_value(obj: object, *names: str) -> str | int | bool | None:
        """Return the first non-None Infrahub attribute value by name, preserving falsey values."""
        for name in names:
            attr = getattr(obj, name, None)
            if attr is None:
                continue
            value = attr.value
            if value is not None:
                return value
        return None

    @classmethod
    def _get_attr_value(cls, obj: object, attr_name: str) -> str | int | bool | None:
        """Safely get an attribute value from a GraphQL node."""
        return cls._get_first_attr_value(obj, attr_name)

    async def _require_pool_prefix(self, pool_ref: object, pool_kind: str, fabric_name: object, pool_label: str) -> str:
        """Resolve a mandatory pool's first prefix, failing loudly if unset or empty.

        The fabric-level pools are mandatory in the schema, so an unset relationship
        should not occur; this still guards against a pool that is linked but has no
        resources, rather than silently emitting a hardcoded prefix.
        """
        prefix = await self._extract_pool_prefix(pool_ref, pool_kind)
        if not prefix:
            raise ValueError(
                f"Fabric '{fabric_name}': required IP pool '{pool_label}' is unset or has no "
                f"resources. Assign a {pool_kind} with at least one prefix."
            )
        return prefix

    async def _extract_l3ls_pools(self, fabric: object, pod: object) -> dict[str, str | None]:
        """Extract IP pools from the fabric/pod data model.

        The three fabric-level pools (uplink, vtep, loopback) are mandatory and are
        resolved with no hardcoded fallback — a missing or empty pool raises a clear
        error. The pod-level MLAG pools remain optional.
        """
        fabric_name = self._get_attr_value(fabric, "name")

        uplink = await self._require_pool_prefix(
            getattr(fabric, "uplink_pool", None), "CoreIPPrefixPool", fabric_name, "uplink_pool"
        )
        vtep = await self._require_pool_prefix(
            getattr(fabric, "vtep_pool", None), "CoreIPPrefixPool", fabric_name, "vtep_pool"
        )
        loopback = await self._require_pool_prefix(
            getattr(fabric, "loopback_pool", None), "CoreIPPrefixPool", fabric_name, "loopback_pool"
        )

        mlag_peer = await self._extract_pool_prefix(getattr(pod, "mlag_peer_pool", None), "CoreIPAddressPool")
        # Auto-generated Pydantic model renames mlag_l3_pool to mlag_l_3_pool
        mlag_l3_ref = self._get_first_attr(pod, "mlag_l_3_pool", "mlag_l3_pool")
        mlag_l3 = await self._extract_pool_prefix(mlag_l3_ref, "CoreIPAddressPool")

        return {
            "uplink_ipv4_pool": uplink,
            "vtep_loopback_ipv4_pool": vtep,
            "loopback_ipv4_pool": loopback,
            "mlag_peer_ipv4_pool": mlag_peer,
            "mlag_peer_l3_ipv4_pool": mlag_l3,
        }

    @staticmethod
    def _gql_val(node: object, field: str) -> Any | None:
        """Get a value from a GQL node that may be a Pydantic model or raw dict."""
        attr = getattr(node, field, None)
        if attr is None:
            return None
        if isinstance(attr, dict):
            return attr.get("value")
        return attr.value if hasattr(attr, "value") else None

    @classmethod
    def _extract_management_settings(cls, fabric: object) -> dict[str, Any]:  # noqa: C901 — maps many optional fabric fields
        """Extract DNS, NTP, and local user settings from fabric."""
        result: dict[str, Any] = {}

        dns_servers_rel = getattr(fabric, "dns_servers", None)
        if dns_servers_rel and hasattr(dns_servers_rel, "edges"):
            dns_list = []
            for edge in dns_servers_rel.edges:
                node = edge.node
                if node:
                    ip = cls._gql_val(node, "ip_address")
                    if ip:
                        entry: dict[str, Any] = {"ip_address": str(ip).split("/")[0]}
                        vrf = cls._gql_val(node, "vrf")
                        if vrf:
                            entry["vrf"] = vrf
                        dns_list.append(entry)
            if dns_list:
                result["dns_servers"] = dns_list

        ntp_servers_rel = getattr(fabric, "ntp_servers", None)
        if ntp_servers_rel and hasattr(ntp_servers_rel, "edges"):
            ntp_list = []
            for edge in ntp_servers_rel.edges:
                node = edge.node
                if node:
                    name = cls._gql_val(node, "name")
                    if name:
                        entry: dict[str, Any] = {"name": name}
                        server_vrf = cls._gql_val(node, "server_vrf")
                        if server_vrf:
                            entry["server_vrf"] = server_vrf
                        ntp_list.append(entry)
            if ntp_list:
                result["ntp_servers"] = ntp_list

        local_users_rel = getattr(fabric, "local_users", None)
        if local_users_rel and hasattr(local_users_rel, "edges"):
            users_list = []
            for edge in local_users_rel.edges:
                node = edge.node
                if node:
                    name = cls._gql_val(node, "name")
                    if name:
                        user: dict[str, Any] = {
                            "name": name,
                            "privilege": cls._gql_val(node, "privilege") or 15,
                            "role": cls._gql_val(node, "role") or "network-admin",
                        }
                        pw_type = cls._gql_val(node, "password_type")
                        pw_value = cls._gql_val(node, "password")
                        if pw_type == "sha512" and pw_value:
                            user["sha512_password"] = pw_value
                        elif pw_value:
                            user["no_password"] = True
                        users_list.append(user)
            if users_list:
                result["local_users"] = users_list

        return result

    @staticmethod
    def _extract_mlag_info(device: object) -> dict[str, Any]:
        """Extract MLAG domain info for a device, including peer names."""
        device_mlag_domain = getattr(device, "mlag_domain", None)
        if not device_mlag_domain or not device_mlag_domain.node:
            return {"domain_id": None, "virtual_router_mac": None, "peer_names": []}

        mlag_domain = device_mlag_domain.node
        domain_id = mlag_domain.domain_id.value if mlag_domain.domain_id else None
        vrmac = getattr(mlag_domain, "virtual_router_mac", None)

        # Extract all peer names from the MLAG domain
        peer_names: list[str] = []
        if hasattr(mlag_domain, "peers") and mlag_domain.peers:
            peer_names = [
                peer_edge.node.name.value
                for peer_edge in mlag_domain.peers.edges
                if peer_edge.node and peer_edge.node.name
            ]

        return {
            "domain_id": domain_id,
            "virtual_router_mac": vrmac.value if vrmac else None,
            "peer_names": peer_names,
        }

    @staticmethod
    def _build_hostvars(  # noqa: C901 — assembles the full AVD hostvars payload
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
        spanning_tree_mode: str | None,
        spanning_tree_priority: int | None,
        loopback_ipv4_offset: int | None,
        bgp_passwords: dict[str, str | None],
        management: dict[str, Any],
        pools: dict[str, str | None],
        uplinks: UplinkData,
        mlag_info: dict[str, str | None],
        tenants_data: list[dict[str, Any]],
        connected_endpoints: list[ServerEndpoint],
    ) -> dict[str, Any]:
        """Build the complete pyAVD hostvars structure."""
        avd_type = get_avd_type(role)
        node_type_key = "super_spine" if role == "super_spine" else avd_type

        # Build node config
        node_config: dict[str, Any] = {"name": hostname}
        if node_id is not None:
            node_config["id"] = node_id
        if bgp_asn is not None:
            node_config["bgp_as"] = str(bgp_asn)
        if loopback_ip:
            node_config["loopback_ipv4_address"] = loopback_ip
            if pools.get("loopback_ipv4_pool"):
                node_config["loopback_ipv4_pool"] = pools["loopback_ipv4_pool"]
        if mgmt_ip:
            node_config["mgmt_ip"] = mgmt_ip

        if pools["uplink_ipv4_pool"]:
            node_config["uplink_ipv4_pool"] = pools["uplink_ipv4_pool"]
        if pools["vtep_loopback_ipv4_pool"]:
            node_config["vtep_loopback_ipv4_pool"] = pools["vtep_loopback_ipv4_pool"]
        if pools["mlag_peer_ipv4_pool"]:
            node_config["mlag_peer_ipv4_pool"] = pools["mlag_peer_ipv4_pool"]
        if pools["mlag_peer_l3_ipv4_pool"]:
            node_config["mlag_peer_l3_ipv4_pool"] = pools["mlag_peer_l3_ipv4_pool"]

        if uplinks["uplink_interfaces"]:
            node_config["uplink_interfaces"] = uplinks["uplink_interfaces"]
            node_config["uplink_switches"] = uplinks["uplink_switches"]
            node_config["uplink_switch_interfaces"] = uplinks["uplink_switch_interfaces"]

        # Extract MLAG peer interfaces for leaf devices (AVD needs mlag_interfaces)
        if mlag_info["domain_id"] and role == "leaf" and "mlag_peer_interfaces" in mlag_info:
            node_config["mlag_interfaces"] = mlag_info["mlag_peer_interfaces"]

        # Leaf devices with SVIs need virtual_router_mac at node level
        if role == "leaf" and virtual_router_mac and tenants_data:
            node_config["virtual_router_mac_address"] = virtual_router_mac

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
        if p2p_uplinks_mtu is not None:
            hostvars["p2p_uplinks_mtu"] = p2p_uplinks_mtu
        if spanning_tree_mode:
            hostvars["spanning_tree_mode"] = spanning_tree_mode
        if spanning_tree_priority is not None:
            hostvars["spanning_tree_priority"] = spanning_tree_priority

        # Loopback offset for leaf devices
        if loopback_ipv4_offset is not None and role == "leaf":
            hostvars.setdefault(node_type_key, {})
            hostvars[node_type_key]["defaults"] = hostvars[node_type_key].get("defaults", {})
            hostvars[node_type_key]["defaults"]["loopback_ipv4_offset"] = loopback_ipv4_offset

        # BGP peer group passwords
        bgp_peer_groups: dict[str, Any] = {}
        if bgp_passwords.get("evpn_overlay"):
            bgp_peer_groups["evpn_overlay_peers"] = {"password": bgp_passwords["evpn_overlay"]}
        if bgp_passwords.get("underlay"):
            bgp_peer_groups["ipv4_underlay_peers"] = {"password": bgp_passwords["underlay"]}
        if bgp_passwords.get("mlag"):
            bgp_peer_groups["mlag_ipv4_underlay_peer"] = {"password": bgp_passwords["mlag"]}
        if bgp_peer_groups:
            hostvars["bgp_peer_groups"] = bgp_peer_groups

        # Management settings
        if management.get("dns_servers"):
            hostvars["dns_settings"] = {"servers": management["dns_servers"]}
        if management.get("ntp_servers"):
            ntp_settings: dict[str, Any] = {"servers": []}
            for srv in management["ntp_servers"]:
                ntp_settings["servers"].append({"name": srv["name"]})
                # server_vrf goes at the ntp_settings level, not per-server
                if "server_vrf" in srv and "server_vrf" not in ntp_settings:
                    ntp_settings["server_vrf"] = srv["server_vrf"]
            hostvars["ntp_settings"] = ntp_settings
        if management.get("local_users"):
            hostvars["aaa_settings"] = {"local_users": management["local_users"]}

        hostvars[node_type_key] = hostvars.get(node_type_key, {})
        hostvars[node_type_key]["nodes"] = [node_config]

        # Add MLAG node_group for leaf devices (AVD expects nodes listed inside the group)
        if mlag_info["domain_id"] and role == "leaf":
            effective_vrmac = mlag_info["virtual_router_mac"] or virtual_router_mac
            node_group: dict[str, Any] = {"group": mlag_info["domain_id"]}
            if bgp_asn is not None:
                node_group["bgp_as"] = str(bgp_asn)
            if effective_vrmac:
                node_group["virtual_router_mac_address"] = effective_vrmac
            # Include peer node names in the group
            group_nodes: list[dict[str, str]] = [{"name": peer_name} for peer_name in mlag_info.get("peer_names", [])]
            if group_nodes:
                node_group["nodes"] = group_nodes
            hostvars[node_type_key]["node_groups"] = [node_group]

        if tenants_data:
            hostvars["tenants"] = tenants_data
        if connected_endpoints:
            hostvars["servers"] = connected_endpoints

        return hostvars

    async def generate(self, data: dict) -> None:  # noqa: C901 — top-level generator orchestration
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
        elif role == "l2leaf":
            uplink_role = "leaf"

        # Extract uplinks
        iface_edges = device.interfaces.edges or []
        uplinks = extract_uplinks_from_dict(iface_edges, uplink_role, device_id)

        # Extract connected endpoints (servers)
        connected_endpoints = extract_connected_endpoints(iface_edges, hostname)

        is_l2leaf = role == "l2leaf"

        # Extract fabric L3LS settings (with backwards-compatible fallbacks)
        # L2 leafs don't participate in EVPN/BGP/VXLAN so skip most L3 settings
        virtual_router_mac = None if is_l2leaf else self._get_attr_value(fabric, "virtual_router_mac")
        underlay_routing_protocol = None if is_l2leaf else self._get_attr_value(fabric, "underlay_routing_protocol")
        overlay_routing_protocol = None if is_l2leaf else self._get_attr_value(fabric, "overlay_routing_protocol")
        p2p_uplinks_mtu = (
            None if is_l2leaf else self._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu")
        )
        spanning_tree_mode = self._get_attr_value(fabric, "spanning_tree_mode")
        spanning_tree_priority = self._get_attr_value(fabric, "spanning_tree_priority")
        # Auto-generated Pydantic model renames loopback_ipv4_offset to loopback_ipv_4_offset
        loopback_ipv4_offset = (
            None if is_l2leaf else self._get_first_attr_value(pod, "loopback_ipv_4_offset", "loopback_ipv4_offset")
        )

        # BGP peer group passwords (not applicable for L2 leafs)
        bgp_passwords: dict[str, str | None] = {"evpn_overlay": None, "underlay": None, "mlag": None}
        if not is_l2leaf:
            bgp_passwords = {
                "evpn_overlay": self._get_attr_value(fabric, "bgp_evpn_overlay_password"),
                "underlay": self._get_attr_value(fabric, "bgp_underlay_password"),
                "mlag": self._get_attr_value(fabric, "bgp_mlag_password"),
            }

        # Extract management settings from fabric (applies to all device types)
        management = self._extract_management_settings(fabric)

        # Extract configurable IP pools (not applicable for L2 leafs)
        if is_l2leaf:
            pools: dict[str, str | None] = {
                "uplink_ipv4_pool": None,
                "vtep_loopback_ipv4_pool": None,
                "loopback_ipv4_pool": None,
                "mlag_peer_ipv4_pool": None,
                "mlag_peer_l3_ipv4_pool": None,
            }
        else:
            pools = await self._extract_l3ls_pools(fabric, pod)

        # Extract MLAG domain info (only for L3 leaf devices)
        mlag_info: dict[str, Any] = {"domain_id": None, "virtual_router_mac": None, "peer_names": []}
        if not is_l2leaf:
            mlag_info = self._extract_mlag_info(device)
            # Extract mlag_peer interface names for AVD mlag_interfaces
            if mlag_info["domain_id"] and iface_edges:
                mlag_peer_ifaces = []
                for edge in iface_edges:
                    iface = edge.node
                    if hasattr(iface, "role") and iface.role and iface.role.value == "mlag_peer":
                        mlag_peer_ifaces.append(iface.name.value)
                if mlag_peer_ifaces:
                    mlag_info["mlag_peer_interfaces"] = sorted(mlag_peer_ifaces)

        # Fetch EVPN tenants (not applicable for L2 leafs)
        tenants_data: list[dict[str, Any]] = []
        if not is_l2leaf:
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
            spanning_tree_mode=spanning_tree_mode,
            spanning_tree_priority=spanning_tree_priority,
            loopback_ipv4_offset=loopback_ipv4_offset,
            bgp_passwords=bgp_passwords,
            management=management,
            pools=pools,
            uplinks=uplinks,
            mlag_info=mlag_info,
            tenants_data=tenants_data,
            connected_endpoints=connected_endpoints,
        )

        # Validate hostvars against pyAVD schema before saving
        import json

        from pyavd import validate_inputs

        validated = validate_inputs(hostvars)
        if validated.validation_result.violations:
            violation_msgs = []
            for v in validated.validation_result.violations:
                msg = getattr(v, "message", str(v))
                path = getattr(v, "path", "")
                violation_msgs.append(f"{msg} (path: {path})")

            error_detail = "; ".join(violation_msgs)
            raise ValueError(f"pyAVD validation failed for {hostname}: {error_detail}")

        new_content = json.dumps(hostvars, indent=2).encode()
        new_checksum = hashlib.sha256(new_content).hexdigest()

        artifact_name = hostname

        # Get or create the artifact
        avd_artifact = await self.client.create(
            AvdArtifact,
            name=artifact_name,
            device=device_id,
            member_of_groups=["avd_artifacts"],
        )
        await avd_artifact.save(allow_upsert=True)

        # Re-fetch to get the relationship IDs populated
        avd_artifact = await self.client.get(AvdArtifact, name__value=artifact_name)

        # Get existing hostvar file if it exists
        existing_file = None
        existing_checksum = None
        if avd_artifact.hostvar_file.id:
            try:
                await avd_artifact.hostvar_file.fetch()
                existing_file = avd_artifact.hostvar_file.peer
                if existing_file:
                    existing_content = await existing_file.download_file()
                    existing_checksum = hashlib.sha256(existing_content).hexdigest()
            except Exception as exc:  # noqa: BLE001 - treat any fetch/download failure as "no existing file"
                self.logger.warning("Could not read existing hostvar file for %s, forcing re-upload: %s", hostname, exc)
                existing_file = None

        # Always upload and save to ensure the file exists on this branch
        if existing_file:
            existing_file.upload_from_bytes(content=new_content, name=f"{hostname}-hostvars.json")
            await existing_file.save(allow_upsert=True)
        else:
            hostvar_file = await self.client.create(AvdHostvarFile, artifact=avd_artifact)
            hostvar_file.upload_from_bytes(content=new_content, name=f"{hostname}-hostvars.json")
            await hostvar_file.save(allow_upsert=True)

        if existing_checksum == new_checksum:
            self.logger.info(f"Hostvars unchanged for {hostname}")
        else:
            self.logger.info(f"Hostvars updated for {hostname}")

        await check_fabric_hostvars_ready(self.client, fabric.id)
