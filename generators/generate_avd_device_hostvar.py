from __future__ import annotations

import hashlib
import logging
import operator
import re
from copy import deepcopy
from dataclasses import dataclass
from ipaddress import IPv4Network
from typing import TYPE_CHECKING, Any, TypedDict

import yaml
from infrahub_sdk.generator import InfrahubGenerator
from netutils.interface import sort_interface_list
from netutils.vlan import vlanlist_to_config

from solution_arista_avd.avd import (
    MLAG_MAIN_TIER_ROLES,
    NON_EMITTED_UNDERLAYS,
    SPINE_UPLINK_LEAF_ROLES,
    SPINE_UPLINK_UNDERLAYS,
    SVI_RENDERING_ROLES,
)
from solution_arista_avd.avd import get_avd_type as _get_package_avd_type
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


class RackInfo(TypedDict):
    name: str | None
    mlag: bool | None
    leaf_names: list[str]
    avd_tags: list[str]


class EvpnGatewayPayload(TypedDict):
    remote_peers: list[dict[str, str]]
    evpn_l2: dict[str, bool]
    evpn_l3: dict[str, bool]
    d_path: dict[str, str | bool]
    all_active_multihoming: dict[str, bool | dict[str, str]]


@dataclass(frozen=True)
class EvpnGatewayContext:
    group_pod_id: str
    local_domain: object
    local_domain_id: str
    remote_domain: object
    remote_domain_id: str


@dataclass(frozen=True)
class DciEndpoint:
    device_id: str
    device_name: str
    device_role: str | None
    interface_id: str
    interface_name: str
    interface_role: str | None
    device_bgp_asn: int | None = None
    fabric_pool: object | None = None
    speed: str | None = None


@dataclass(frozen=True)
class DciNetworkLinkIntent:
    link_id: str
    link_name: str
    include_in_underlay_protocol: bool
    endpoints: tuple[DciEndpoint, DciEndpoint]
    asns: tuple[int | None, int | None]
    pool: object


LACP_MODE_MAP = {"active": "active", "passive": "passive", "disabled": "on"}
PORT_CHANNEL_RE = re.compile(r"^Port-Channel(?P<channel_id>\d+)$")
LEAF_FAMILY_ROLES = {"leaf", "border_leaf"}
FIELD_ALIASES = {
    "evpn_l2_enabled": "evpn_l_2_enabled",
    "evpn_l3_enabled": "evpn_l_3_enabled",
    "evpn_l3_inter_domain": "evpn_l_3_inter_domain",
}


def get_generator_avd_type(role: str) -> str:
    """Resolve role mappings used by repository-loaded generator code."""
    if role == "border_leaf":
        return "l3leaf"
    return _get_package_avd_type(role)


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


def apply_lag_adapter_config(
    adapter: dict[str, Any],
    lag_node: object,
    *,
    mlag_active: bool,
    evpn_lag_node: object | None = None,
    endpoint_lag_node: object | None = None,
) -> None:
    """Apply pyAVD port-channel and optional EVPN Ethernet Segment settings."""
    port_channel = {"mode": LACP_MODE_MAP.get(_value(lag_node, "lacp_mode"), "active")}
    channel_id = _lag_channel_id(lag_node, require_port_channel_name=False)
    if channel_id is not None:
        port_channel["channel_id"] = channel_id
    endpoint_port_channel = _value(endpoint_lag_node, "name") if endpoint_lag_node else None
    if endpoint_port_channel:
        port_channel["endpoint_port_channel"] = endpoint_port_channel
    adapter["port_channel"] = port_channel

    evpn_source = evpn_lag_node or lag_node
    if _value(evpn_source, "evpn_ethernet_segment") is True and not mlag_active and len(set(adapter["switches"])) >= 2:
        adapter["ethernet_segment"] = {"short_esi": "auto"}


def _node(value: object) -> object | None:
    if isinstance(value, dict):
        return value.get("node")
    return getattr(value, "node", None)


def _edges(value: object) -> list[object]:
    if isinstance(value, dict):
        return value.get("edges") or []
    return getattr(value, "edges", None) or []


def _field(value: object, name: str) -> object | None:
    if isinstance(value, dict):
        return value.get(name)
    attr = getattr(value, name, None)
    if attr is not None:
        return attr
    alias = FIELD_ALIASES.get(name)
    if alias:
        return getattr(value, alias, None)
    return None


def _value(value: object, name: str) -> Any:
    attr = _field(value, name)
    if isinstance(attr, dict):
        return attr.get("value")
    return getattr(attr, "value", None)


def _typename(value: object) -> str | None:
    if isinstance(value, dict):
        return value.get("__typename") or value.get("typename__")
    return getattr(value, "typename__", None)


def _lag_channel_id(lag_node: object | None, *, require_port_channel_name: bool) -> int | None:
    if lag_node is None:
        return None

    lag_name = _value(lag_node, "name")
    channel_id = _value(lag_node, "channel_id")
    parsed_channel_id = None
    if lag_name:
        match = PORT_CHANNEL_RE.match(str(lag_name))
        if match:
            parsed_channel_id = int(match.group("channel_id"))
        elif require_port_channel_name:
            raise ValueError(f"Switch LAG name '{lag_name}' must match Port-Channel<ID>")

    if channel_id is None:
        return parsed_channel_id

    channel_id = int(channel_id)
    if parsed_channel_id is not None and parsed_channel_id != channel_id:
        raise ValueError(
            f"Switch LAG name '{lag_name}' implies channel ID {parsed_channel_id}, but channel_id is {channel_id}"
        )
    if require_port_channel_name and parsed_channel_id is None:
        raise ValueError(f"Switch LAG with channel_id {channel_id} must be named Port-Channel{channel_id}")
    return channel_id


def _extract_vlan_config(interface: object) -> tuple[list[int], int | None]:
    tagged_vlans: list[int] = []
    for vlan_edge in _edges(_field(interface, "tagged_vlan")):
        vlan_node = _node(vlan_edge)
        if _value(vlan_node, "status") != "active":
            continue
        vlan_id = _value(vlan_node, "vlan_id")
        if vlan_id:
            tagged_vlans.append(vlan_id)

    untagged_vlan = None
    untagged_vlan_node = _node(_field(interface, "untagged_vlan"))
    if untagged_vlan_node and _value(untagged_vlan_node, "status") == "active":
        untagged_vlan = _value(untagged_vlan_node, "vlan_id")

    return tagged_vlans, untagged_vlan


def _apply_vlan_adapter_config(adapter: dict[str, Any], tagged_vlans: list[int], untagged_vlan: int | None) -> None:
    if tagged_vlans:
        adapter["mode"] = "trunk"
        adapter["vlans"] = vlanlist_to_config(sorted(tagged_vlans))[0]
        if untagged_vlan:
            adapter["native_vlan"] = untagged_vlan
    elif untagged_vlan:
        adapter["mode"] = "access"
        adapter["vlans"] = str(untagged_vlan)


def _vlan_signature(interface: object) -> tuple[tuple[int, ...], int | None]:
    tagged_vlans, untagged_vlan = _extract_vlan_config(interface)
    return tuple(sorted(tagged_vlans)), untagged_vlan


def _device_name(interface: object) -> str | None:
    device = _node(_field(interface, "device"))
    return _value(device, "name") if device else None


def _device_role(interface: object) -> str | None:
    device = _node(_field(interface, "device"))
    return _value(device, "role") if device else None


def _device_typename(interface: object) -> str | None:
    return _typename(_node(_field(interface, "device")))


def _object_id(value: object | None) -> str | None:
    obj_id = _field(value, "id")
    return str(obj_id) if obj_id else None


def _display_name(value: object | None) -> str:
    if value is None:
        return "<missing>"
    return str(_field(value, "display_label") or _value(value, "name") or _object_id(value) or "<unknown>")


def _relationship_node(value: object | None, relationship_name: str) -> object | None:
    return _node(_field(value, relationship_name))


def _role_value(value: object | None) -> str | None:
    return _value(value, "role")


def _pod_id(value: object | None) -> str | None:
    pod = _relationship_node(value, "pod")
    return _object_id(pod)


def _fabric_id(value: object | None) -> str | None:
    fabric = _relationship_node(value, "fabric")
    return _object_id(fabric)


def _domain_id(value: object | None) -> str | None:
    domain_id = _value(value, "domain_id")
    return str(domain_id) if domain_id else None


def _gateway_error(gateway: object | None, target_hostname: str, message: str) -> ValueError:
    return ValueError(f"EVPN Gateway Group '{_display_name(gateway)}' for target device '{target_hostname}': {message}")


def _require_gateway_field(gateway: object, target_hostname: str, field_name: str) -> str:
    value = _value(gateway, field_name)
    if value in (None, ""):
        raise _gateway_error(gateway, target_hostname, f"required field '{field_name}' is missing")
    return str(value)


def _validate_gateway_member(
    *,
    gateway: object,
    device: object | None,
    target_hostname: str,
    expected_pod_id: str,
) -> None:
    if device is None:
        raise _gateway_error(gateway, target_hostname, "members relationship contains an empty device")

    role = _role_value(device)
    if role != "border_leaf":
        raise _gateway_error(
            gateway,
            target_hostname,
            f"members must contain only border_leaf devices; device '{_display_name(device)}' role is {role!r}",
        )

    if _pod_id(device) != expected_pod_id:
        raise _gateway_error(
            gateway,
            target_hostname,
            f"member device '{_display_name(device)}' must belong to the gateway group's pod",
        )


def _gateway_members(gateway: object | None) -> list[object]:
    return [_node(edge) for edge in _edges(_field(gateway, "members")) if _node(edge) is not None]


def _gateway_local_domain(gateway: object | None) -> object | None:
    return _relationship_node(gateway, "local_domain")


def _validate_gateway_pod_domain(
    *,
    gateway: object,
    hostname: str,
    group_pod: object,
    local_domain: object,
    local_domain_id: str,
) -> None:
    pod_domain = _relationship_node(group_pod, "evpn_domain")
    if pod_domain is None:
        raise _gateway_error(gateway, hostname, "selected pod must have an evpn_domain matching local_domain")
    pod_domain_id = _domain_id(pod_domain)
    if not pod_domain_id:
        raise _gateway_error(gateway, hostname, "selected pod evpn_domain.domain_id is missing")
    if _object_id(pod_domain) != _object_id(local_domain):
        raise _gateway_error(
            gateway,
            hostname,
            "selected pod evpn_domain must match gateway group local_domain; "
            f"expected {_display_name(local_domain)}, got {_display_name(pod_domain)}",
        )
    if pod_domain_id != local_domain_id:
        raise _gateway_error(
            gateway,
            hostname,
            "selected pod evpn_domain.domain_id must match gateway group local_domain.domain_id",
        )


def _validate_gateway_group_context(gateway: object, hostname: str) -> EvpnGatewayContext:
    group_pod = _relationship_node(gateway, "pod")
    if group_pod is None:
        raise _gateway_error(gateway, hostname, "relationship 'pod' is missing")
    group_pod_id = _object_id(group_pod)
    if not group_pod_id:
        raise _gateway_error(gateway, hostname, "relationship 'pod' is missing an id")

    local_domain = _gateway_local_domain(gateway)
    if local_domain is None:
        raise _gateway_error(gateway, hostname, "relationship 'local_domain' is missing")
    local_domain_id = _domain_id(local_domain)
    if not local_domain_id:
        raise _gateway_error(gateway, hostname, "local_domain.domain_id is missing")
    _validate_gateway_pod_domain(
        gateway=gateway,
        hostname=hostname,
        group_pod=group_pod,
        local_domain=local_domain,
        local_domain_id=local_domain_id,
    )

    remote_domain = _relationship_node(gateway, "remote_domain")
    if remote_domain is None:
        raise _gateway_error(gateway, hostname, "relationship 'remote_domain' is missing")
    remote_domain_id = _domain_id(remote_domain)
    if not remote_domain_id:
        raise _gateway_error(gateway, hostname, "remote_domain.domain_id is missing")
    if _object_id(remote_domain) == _object_id(local_domain):
        raise _gateway_error(gateway, hostname, "remote_domain must differ from local_domain")
    if remote_domain_id == local_domain_id and _fabric_id(remote_domain) == _fabric_id(local_domain):
        raise _gateway_error(gateway, hostname, "remote_domain domain_id must differ from the local domain_id")
    if _fabric_id(remote_domain) and _fabric_id(local_domain) and _fabric_id(remote_domain) != _fabric_id(local_domain):
        raise _gateway_error(gateway, hostname, "remote_domain must belong to the same fabric as local_domain")

    return EvpnGatewayContext(
        group_pod_id=group_pod_id,
        local_domain=local_domain,
        local_domain_id=local_domain_id,
        remote_domain=remote_domain,
        remote_domain_id=remote_domain_id,
    )


def _validate_gateway_group_members(
    *,
    gateway: object,
    device: object,
    hostname: str,
    group_pod_id: str,
) -> None:
    members = _gateway_members(gateway)
    if not members:
        raise _gateway_error(gateway, hostname, "members must contain at least one border_leaf device")

    target_id = _object_id(device)
    member_ids: set[str] = set()
    target_is_member = False
    for member in members:
        _validate_gateway_member(gateway=gateway, device=member, target_hostname=hostname, expected_pod_id=group_pod_id)
        member_id = _object_id(member)
        if member_id:
            if member_id in member_ids:
                raise _gateway_error(
                    gateway, hostname, f"member device '{_display_name(member)}' appears more than once"
                )
            member_ids.add(member_id)
        if member_id == target_id:
            target_is_member = True
    if not target_is_member:
        raise _gateway_error(gateway, hostname, "target device must be a member of its evpn_gateway_group")


def _validate_peer_group_local_domain(
    *,
    gateway: object,
    peer_group: object,
    hostname: str,
    context: EvpnGatewayContext,
) -> str:
    peer_local_domain = _gateway_local_domain(peer_group)
    if peer_local_domain is None:
        raise _gateway_error(gateway, hostname, f"peer group '{_display_name(peer_group)}' has no local_domain")
    peer_local_domain_id = _domain_id(peer_local_domain)
    if not peer_local_domain_id:
        raise _gateway_error(
            gateway, hostname, f"peer group '{_display_name(peer_group)}' local_domain.domain_id is missing"
        )
    if _object_id(peer_local_domain) == _object_id(context.local_domain):
        raise _gateway_error(
            gateway, hostname, f"peer group '{_display_name(peer_group)}' uses the same local EVPN domain"
        )
    if peer_local_domain_id == context.local_domain_id and _fabric_id(peer_local_domain) == _fabric_id(
        context.local_domain
    ):
        raise _gateway_error(
            gateway, hostname, f"peer group '{_display_name(peer_group)}' uses the same local EVPN domain_id"
        )

    peer_pod = _relationship_node(peer_group, "pod")
    peer_pod_id = _object_id(peer_pod)
    if not peer_pod_id:
        raise _gateway_error(gateway, hostname, f"peer group '{_display_name(peer_group)}' has no pod")
    _validate_gateway_pod_domain(
        gateway=gateway,
        hostname=hostname,
        group_pod=peer_pod,
        local_domain=peer_local_domain,
        local_domain_id=peer_local_domain_id,
    )
    return peer_pod_id


def _derive_remote_peer_hostnames(
    *,
    gateway: object,
    device: object,
    hostname: str,
    context: EvpnGatewayContext,
) -> list[str]:
    remote_peer_hostnames: set[str] = set()
    target_id = _object_id(device)
    for peer_group_edge in _edges(_field(context.remote_domain, "remote_gateway_groups")):
        peer_group = _node(peer_group_edge)
        if peer_group is None or _object_id(peer_group) == _object_id(gateway):
            continue
        peer_pod_id = _validate_peer_group_local_domain(
            gateway=gateway,
            peer_group=peer_group,
            hostname=hostname,
            context=context,
        )
        for peer_member in _gateway_members(peer_group):
            _validate_gateway_member(
                gateway=peer_group,
                device=peer_member,
                target_hostname=hostname,
                expected_pod_id=peer_pod_id,
            )
            peer_hostname = _value(peer_member, "name")
            if not peer_hostname:
                raise _gateway_error(
                    gateway, hostname, f"peer group '{_display_name(peer_group)}' member hostname is missing"
                )
            if _object_id(peer_member) != target_id:
                remote_peer_hostnames.add(str(peer_hostname))
    return sorted(remote_peer_hostnames)


def _device_id(interface: object) -> str | None:
    device = _node(_field(interface, "device"))
    return _field(device, "id") if device else None


def _device_bgp_asn(interface: object) -> int | None:
    """Return the endpoint device's own BGP ASN (via its RoutingAsn relationship)."""
    device = _node(_field(interface, "device"))
    asn = _value(_node(_field(device, "asn")), "asn") if device else None
    return int(asn) if asn is not None else None


def _endpoint_fabric_pool(interface: object) -> object | None:
    """Return the DCI prefix pool of the fabric that owns the endpoint device."""
    device = _node(_field(interface, "device"))
    pod = _node(_field(device, "pod")) if device else None
    fabric = _node(_field(pod, "parent")) if pod else None
    return _node(_field(fabric, "dci_pool")) if fabric else None


def _extract_interface_speed(interface: object) -> str | None:
    for field in ("speed", "link_speed", "interface_speed"):
        speed = _value(interface, field)
        if speed:
            return str(speed)
    return None


def _normalize_dci_endpoints(endpoints: list[DciEndpoint]) -> tuple[DciEndpoint, DciEndpoint]:
    if len(endpoints) != 2:
        msg = f"DCI link must have exactly two physical endpoints, found {len(endpoints)}"
        raise ValueError(msg)

    ordered = tuple(
        sorted(
            endpoints,
            key=lambda endpoint: (endpoint.device_name, sort_interface_list([endpoint.interface_name])[0]),
        )
    )
    return ordered[0], ordered[1]


def _extract_dci_network_link_intent(link: object) -> DciNetworkLinkIntent:
    link_id = str(_field(link, "id") or _value(link, "name") or _field(link, "display_label"))
    link_name = str(_value(link, "name") or _field(link, "display_label") or link_id)
    if _value(link, "role") != "dci":
        msg = f"Network Link {link_name}: role must be dci for DCI generation"
        raise ValueError(msg)
    endpoints: list[DciEndpoint] = []

    for endpoint_edge in _edges(_field(link, "connected_endpoints")):
        endpoint = _node(endpoint_edge)
        if not endpoint:
            continue
        if _typename(endpoint) != "InterfacePhysical":
            msg = f"DCI link {link_name}: endpoint {_field(endpoint, 'id')} is not a physical interface"
            raise ValueError(msg)
        device_id = _device_id(endpoint)
        device_name = _device_name(endpoint)
        interface_name = _value(endpoint, "name")
        if not device_id or not device_name or not interface_name:
            msg = f"DCI link {link_name}: endpoint is missing device or interface identity"
            raise ValueError(msg)
        endpoints.append(
            DciEndpoint(
                device_id=str(device_id),
                device_name=str(device_name),
                device_role=_device_role(endpoint),
                interface_id=str(_field(endpoint, "id")),
                interface_name=str(interface_name),
                interface_role=_value(endpoint, "role"),
                device_bgp_asn=_device_bgp_asn(endpoint),
                fabric_pool=_endpoint_fabric_pool(endpoint),
                speed=_extract_interface_speed(endpoint),
            )
        )

    endpoint_1, endpoint_2 = _normalize_dci_endpoints(endpoints)
    if endpoint_1.device_role != "border_leaf" or endpoint_2.device_role != "border_leaf":
        msg = f"DCI link {link_name}: both endpoints must be Border Leaf devices"
        raise ValueError(msg)
    non_peering = [
        f"{endpoint.device_name} {endpoint.interface_name}"
        for endpoint in (endpoint_1, endpoint_2)
        if endpoint.interface_role != "peering"
    ]
    if non_peering:
        msg = (
            f"DCI link {link_name}: endpoint interfaces must use role=peering "
            f"({', '.join(non_peering)} are not peering)"
        )
        raise ValueError(msg)
    if endpoint_1.device_id == endpoint_2.device_id:
        msg = f"DCI link {link_name}: endpoints must use different devices"
        raise ValueError(msg)
    if endpoint_1.interface_id == endpoint_2.interface_id:
        msg = f"DCI link {link_name}: endpoints must use different interfaces"
        raise ValueError(msg)

    # A DCI /31 must come from a single pool so both border leafs (which generate
    # independently, potentially in different fabrics) allocate the same prefix
    # under the shared link identifier. Pick it deterministically from the
    # sorted-first endpoint's fabric, falling back to the peer's.
    pool = endpoint_1.fabric_pool or endpoint_2.fabric_pool
    if pool is None:
        msg = f"DCI link {link_name}: neither endpoint fabric defines a dci_pool"
        raise ValueError(msg)

    include_in_underlay_protocol = _value(link, "include_in_underlay_protocol")
    if include_in_underlay_protocol is None:
        include_in_underlay_protocol = True

    return DciNetworkLinkIntent(
        link_id=link_id,
        link_name=link_name,
        include_in_underlay_protocol=bool(include_in_underlay_protocol),
        endpoints=(endpoint_1, endpoint_2),
        asns=(endpoint_1.device_bgp_asn, endpoint_2.device_bgp_asn),
        pool=pool,
    )


def _uses_ebgp_underlay(underlay_routing_protocol: str | None) -> bool:
    return (underlay_routing_protocol or "").lower() == "ebgp"


async def allocate_dci_p2p_prefix_from_pool(
    client: InfrahubClient,
    pool: object,
    *,
    identifier: str,
    prefix_length: int = 31,
) -> IPv4Network:
    """Allocate or reuse a stable DCI point-to-point prefix from a prefix pool.

    Keep this helper local to the repository-loaded generator: Infrahub imports
    generator modules from the synced repository, but imports package modules
    from the task-worker image.
    """
    if isinstance(pool, dict):
        pool_id = pool.get("id")
        if not pool_id:
            msg = "DCI pool is missing an ID and cannot be used for prefix allocation"
            raise ValueError(msg)
        pool = await client.get(kind="CoreIPPrefixPool", id=pool_id)

    prefix = await client.allocate_next_ip_prefix(
        resource_pool=pool,
        identifier=identifier,
        member_type="prefix",
        prefix_length=prefix_length,
        data={"role": "technical"},
    )
    return IPv4Network(str(prefix.prefix.value), strict=False)


async def build_dci_l3_edge_p2p_links(
    client: InfrahubClient,
    *,
    dci_links: list[object],
    hostname: str,
    underlay_routing_protocol: str | None = "ebgp",
) -> list[dict[str, Any]]:
    """Build deterministic PyAVD l3_edge.p2p_links entries from DCI links.

    BGP ASNs are only required (and emitted as ``as``) when the fabric underlay
    routing protocol is eBGP. With a non-BGP underlay (e.g. OSPF) the p2p link is
    still emitted for reachability, but without ``as`` and without requiring the
    endpoint devices to carry an ASN.
    """
    ebgp_underlay = _uses_ebgp_underlay(underlay_routing_protocol)
    intents: list[DciNetworkLinkIntent] = []
    for link in dci_links:
        try:
            intents.append(_extract_dci_network_link_intent(link))
        except ValueError as exc:
            logger.warning("Skipping invalid DCI Network Link: %s", exc)

    intents = sorted(
        intents,
        key=lambda intent: (
            intent.link_name,
            intent.endpoints[0].device_name,
            sort_interface_list([intent.endpoints[0].interface_name])[0],
            intent.endpoints[1].device_name,
            sort_interface_list([intent.endpoints[1].interface_name])[0],
        ),
    )

    seen_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    p2p_links: list[dict[str, Any]] = []
    for intent in intents:
        endpoint_pair = tuple(sorted((endpoint.device_id, endpoint.interface_id) for endpoint in intent.endpoints))
        if endpoint_pair in seen_pairs:
            logger.warning(
                "Skipping invalid DCI Network Link: DCI link %s: duplicate endpoint-interface pair", intent.link_name
            )
            continue
        seen_pairs.add(endpoint_pair)

        if hostname not in {endpoint.device_name for endpoint in intent.endpoints}:
            continue

        if ebgp_underlay and (intent.asns[0] is None or intent.asns[1] is None):
            logger.warning(
                "Skipping invalid DCI Network Link: DCI link %s: both endpoint devices must have a BGP ASN "
                "when the underlay routing protocol is eBGP",
                intent.link_name,
            )
            continue

        try:
            prefix = await allocate_dci_p2p_prefix_from_pool(
                client,
                intent.pool,
                identifier=f"dci-link:{intent.link_id}",
                prefix_length=31,
            )
        except ValueError as exc:
            logger.warning("Skipping invalid DCI Network Link: %s", exc)
            continue
        addresses = [f"{address}/31" for address in prefix.hosts()]
        if len(addresses) != 2:
            logger.warning(
                "Skipping invalid DCI Network Link: DCI link %s: allocated prefix %s did not produce two /31 host addresses",
                intent.link_name,
                prefix,
            )
            continue

        p2p_link: dict[str, Any] = {
            "nodes": [intent.endpoints[0].device_name, intent.endpoints[1].device_name],
            "interfaces": [intent.endpoints[0].interface_name, intent.endpoints[1].interface_name],
            "ip": addresses,
            "include_in_underlay_protocol": intent.include_in_underlay_protocol,
        }
        if ebgp_underlay:
            p2p_link["as"] = [intent.asns[0], intent.asns[1]]
        speed = intent.endpoints[0].speed or intent.endpoints[1].speed
        if speed:
            p2p_link["speed"] = speed
        p2p_links.append(p2p_link)

    return p2p_links


def _lag_member_adapter(
    *,
    lag_node: object,
    switch_lag_node: object | None,
    local_interface: object,
    mlag_active: bool,
    skip_l2leaf_endpoints: bool = True,
) -> dict[str, Any] | None:
    members = _edges(_field(lag_node, "lag_members"))
    if not members:
        return None

    local_tagged_vlans, local_untagged_vlan = _extract_vlan_config(local_interface)
    member_links: list[tuple[str, str, str]] = []
    for member_edge in members:
        member = _node(member_edge)
        if not member:
            continue
        member_name = _value(member, "name")
        connector = _node(_field(member, "connector"))
        if not member_name or not connector:
            continue

        for endpoint_edge in _edges(_field(connector, "connected_endpoints")):
            endpoint = _node(endpoint_edge)
            if not endpoint or _field(endpoint, "id") == _field(member, "id"):
                continue
            if _typename(endpoint) != "InterfacePhysical":
                continue
            if skip_l2leaf_endpoints and _device_role(endpoint) == "l2leaf":
                continue
            switch_name = _device_name(endpoint)
            switch_port = _value(endpoint, "name")
            if switch_name and switch_port:
                member_links.append((switch_name, switch_port, member_name))

    if not member_links:
        return None

    member_links = sorted(set(member_links), key=lambda item: (item[0], sort_interface_list([item[1]])[0], item[2]))
    adapter: dict[str, Any] = {
        "endpoint_ports": [endpoint_port for _, _, endpoint_port in member_links],
        "switch_ports": [switch_port for _, switch_port, _ in member_links],
        "switches": [switch_name for switch_name, _, _ in member_links],
    }
    apply_lag_adapter_config(
        adapter,
        lag_node,
        mlag_active=mlag_active,
        evpn_lag_node=switch_lag_node,
        endpoint_lag_node=lag_node,
    )
    _apply_vlan_adapter_config(adapter, local_tagged_vlans, local_untagged_vlan)
    adapter["spanning_tree_portfast"] = "edge"
    return adapter


def _switch_lag_member_links(
    *,
    server_lag_node: object | None,
    fallback_switch_lag_node: object,
    fallback_local_interface: object,
    fallback_endpoint: object,
    hostname: str,
    skip_l2leaf_endpoints: bool = True,
) -> list[dict[str, Any]]:
    members = _edges(_field(server_lag_node, "lag_members")) if server_lag_node else []
    if not members:
        return [
            {
                "endpoint_port": _value(fallback_endpoint, "name"),
                "switch_port": _value(fallback_local_interface, "name"),
                "switch": hostname,
                "switch_lag": fallback_switch_lag_node,
                "vlan": _vlan_signature(fallback_local_interface),
            }
        ]

    links: list[dict[str, Any]] = []
    for member_edge in members:
        member = _node(member_edge)
        if not member:
            continue
        endpoint_port = _value(member, "name")
        connector = _node(_field(member, "connector"))
        if not endpoint_port or not connector:
            continue
        for endpoint_edge in _edges(_field(connector, "connected_endpoints")):
            endpoint = _node(endpoint_edge)
            if not endpoint or _field(endpoint, "id") == _field(member, "id"):
                continue
            if _typename(endpoint) != "InterfacePhysical":
                continue
            if skip_l2leaf_endpoints and _device_role(endpoint) == "l2leaf":
                continue
            switch_name = _device_name(endpoint)
            switch_port = _value(endpoint, "name")
            if not switch_name or not switch_port:
                continue
            switch_lag_node = _node(_field(endpoint, "lag")) or fallback_switch_lag_node
            links.append(
                {
                    "endpoint_port": endpoint_port,
                    "switch_port": switch_port,
                    "switch": switch_name,
                    "switch_lag": switch_lag_node,
                    "vlan": _vlan_signature(endpoint),
                }
            )

    return links


def _add_switch_lag_adapter(
    server: ServerEndpoint,
    groups: dict[tuple[str, int], dict[str, Any]],
    *,
    server_name: str,
    switch_lag_node: object,
    endpoint_lag_node: object | None,
    links: list[dict[str, Any]],
) -> None:
    channel_id = _lag_channel_id(switch_lag_node, require_port_channel_name=True)
    if channel_id is None:
        lag_name = _value(switch_lag_node, "name")
        raise ValueError(f"Switch LAG '{lag_name}' is missing channel_id and cannot derive one from its name")

    key = (server_name, channel_id)
    lacp_mode = _value(switch_lag_node, "lacp_mode")
    evpn_ethernet_segment = _value(switch_lag_node, "evpn_ethernet_segment")
    endpoint_port_channel = _value(endpoint_lag_node, "name") if endpoint_lag_node else None
    group = groups.setdefault(
        key,
        {
            "server": server,
            "channel_id": channel_id,
            "lacp_mode": lacp_mode,
            "evpn_ethernet_segment": evpn_ethernet_segment,
            "endpoint_port_channel": endpoint_port_channel,
            "links": {},
            "vlan": None,
        },
    )

    expected = {
        "channel_id": channel_id,
        "lacp_mode": lacp_mode,
        "evpn_ethernet_segment": evpn_ethernet_segment,
        "endpoint_port_channel": endpoint_port_channel,
    }
    for field, expected_value in expected.items():
        if group[field] != expected_value:
            raise ValueError(
                f"Conflicting switch LAG {field} for server '{server_name}' channel {channel_id}: "
                f"{group[field]!r} != {expected_value!r}"
            )

    for link in links:
        link_lag = link["switch_lag"]
        link_channel_id = _lag_channel_id(link_lag, require_port_channel_name=True)
        if link_channel_id != channel_id:
            raise ValueError(
                f"Conflicting switch LAG channel ID for server '{server_name}': {channel_id} != {link_channel_id}"
            )
        for field in ("lacp_mode", "evpn_ethernet_segment"):
            link_value = _value(link_lag, field)
            if link_value != group[field]:
                raise ValueError(
                    f"Conflicting switch LAG {field} for server '{server_name}' channel {channel_id}: "
                    f"{group[field]!r} != {link_value!r}"
                )
        if group["vlan"] is None:
            group["vlan"] = link["vlan"]
        elif group["vlan"] != link["vlan"]:
            raise ValueError(f"Conflicting VLANs for server '{server_name}' channel {channel_id}")
        group["links"][link["switch"], link["switch_port"], link["endpoint_port"]] = link


def _flush_switch_lag_groups(groups: dict[tuple[str, int], dict[str, Any]], *, mlag_active: bool) -> None:
    for group in groups.values():
        links = sorted(
            group["links"].values(),
            key=lambda item: (item["switch"], sort_interface_list([item["switch_port"]])[0], item["endpoint_port"]),
        )
        adapter: dict[str, Any] = {
            "endpoint_ports": [link["endpoint_port"] for link in links],
            "switch_ports": [link["switch_port"] for link in links],
            "switches": [link["switch"] for link in links],
            "port_channel": {
                "mode": LACP_MODE_MAP.get(group["lacp_mode"], "active"),
                "channel_id": group["channel_id"],
            },
            "spanning_tree_portfast": "edge",
        }
        if group["endpoint_port_channel"]:
            adapter["port_channel"]["endpoint_port_channel"] = group["endpoint_port_channel"]
        tagged_vlans, untagged_vlan = group["vlan"] or ((), None)
        _apply_vlan_adapter_config(adapter, list(tagged_vlans), untagged_vlan)
        if group["evpn_ethernet_segment"] is True and not mlag_active and len(set(adapter["switches"])) >= 2:
            adapter["ethernet_segment"] = {"short_esi": "auto"}
        group["server"]["adapters"].append(adapter)


def extract_connected_endpoints(  # noqa: C901
    interfaces: list[GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges],
    hostname: str,
    *,
    mlag_active: bool = False,
    skip_l2leaf_endpoints: bool = True,
) -> list[ServerEndpoint]:
    """Extract connected endpoints (servers) from device interfaces.

    Args:
        interfaces: List of interface edge dicts from GraphQL response
        hostname: Current device hostname (for switch_ports reference)
        mlag_active: Whether the current device is in an active MLAG pair
        skip_l2leaf_endpoints: Drop links whose remote device is an l2leaf. This is
            correct for an L3 leaf building downlinks (AVD models the downstream
            l2leaf via the l2leaf type, not connected_endpoints), but must be False
            when the current device is itself an l2leaf main tier — there its
            server legs land on sibling l2leaf switches of the same MLAG pair.

    Returns:
        List of server endpoint configs for pyAVD
    """
    servers: dict[str, ServerEndpoint] = {}  # Group by remote device name
    server_adapter_keys: dict[str, set[str]] = {}
    switch_lag_groups: dict[tuple[str, int], dict[str, Any]] = {}

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
        tagged_vlans, untagged_vlan = _extract_vlan_config(interface)
        switch_lag_node = _node(_field(interface, "lag"))

        endpoints = link.connected_endpoints.edges or []
        for ep_edge in endpoints:
            endpoint = ep_edge.node
            if not endpoint:
                continue
            # Skip this interface, find the remote one
            if endpoint.id != interface.id and hasattr(endpoint, "device"):
                remote_device = endpoint.device.node
                if remote_device:
                    if _device_typename(endpoint) != "ComputePhysicalServer":
                        continue
                    # Skip L2 leaf devices — AVD handles them via l2leaf type, not connected_endpoints
                    remote_role = getattr(remote_device, "role", None)
                    if skip_l2leaf_endpoints and remote_role and remote_role.value == "l2leaf":
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
                        server_adapter_keys[server_name] = set()

                    # Detect port-channel on the remote (server) endpoint
                    endpoint_lag = getattr(endpoint, "lag", None)
                    endpoint_lag_node = endpoint_lag.node if endpoint_lag and endpoint_lag.node else None
                    if switch_lag_node:
                        channel_id = _lag_channel_id(switch_lag_node, require_port_channel_name=True)
                        if channel_id is None:
                            lag_name = _value(switch_lag_node, "name")
                            raise ValueError(
                                f"Switch LAG '{lag_name}' is missing channel_id and cannot derive one from its name"
                            )
                        links = _switch_lag_member_links(
                            server_lag_node=endpoint_lag_node,
                            fallback_switch_lag_node=switch_lag_node,
                            fallback_local_interface=interface,
                            fallback_endpoint=endpoint,
                            hostname=hostname,
                            skip_l2leaf_endpoints=skip_l2leaf_endpoints,
                        )
                        _add_switch_lag_adapter(
                            servers[server_name],
                            switch_lag_groups,
                            server_name=server_name,
                            switch_lag_node=switch_lag_node,
                            endpoint_lag_node=endpoint_lag_node,
                            links=links,
                        )
                        continue

                    if endpoint_lag and endpoint_lag.node:
                        adapter_key = f"lag:{endpoint_lag.node.id}"
                        if adapter_key in server_adapter_keys[server_name]:
                            continue
                        lag_adapter = _lag_member_adapter(
                            lag_node=endpoint_lag.node,
                            switch_lag_node=switch_lag_node,
                            local_interface=interface,
                            mlag_active=mlag_active,
                            skip_l2leaf_endpoints=skip_l2leaf_endpoints,
                        )
                        if lag_adapter:
                            servers[server_name]["adapters"].append(lag_adapter)
                            server_adapter_keys[server_name].add(adapter_key)
                            continue

                    adapter_key = f"interface:{interface.id}:{endpoint.id}"
                    if adapter_key in server_adapter_keys[server_name]:
                        continue

                    # Build adapter config
                    adapter: dict[str, Any] = {
                        "endpoint_ports": [endpoint_port],
                        "switch_ports": [switch_port],
                        "switches": [hostname],
                    }

                    if endpoint_lag and endpoint_lag.node:
                        apply_lag_adapter_config(
                            adapter,
                            endpoint_lag.node,
                            mlag_active=mlag_active,
                            evpn_lag_node=switch_lag_node,
                            endpoint_lag_node=endpoint_lag.node,
                        )

                    # Determine mode and add VLAN config
                    _apply_vlan_adapter_config(adapter, tagged_vlans, untagged_vlan)

                    # Add spanning tree portfast for server ports
                    adapter["spanning_tree_portfast"] = "edge"

                    servers[server_name]["adapters"].append(adapter)
                    server_adapter_keys[server_name].add(adapter_key)

    _flush_switch_lag_groups(switch_lag_groups, mlag_active=mlag_active)
    return _sort_server_endpoints(servers)


class GenerateAVDDeviceHostvar(InfrahubGenerator):
    @staticmethod
    def _peer_name(peer: object) -> str | None:
        name = getattr(peer, "name", None)
        if not name:
            return None
        return name.value

    @classmethod
    def _build_svi_tags(cls, rack_tag_peers: list[object], avd_tag_peers: list[object]) -> list[str]:
        rack_tags = sorted({name for peer in rack_tag_peers if (name := cls._peer_name(peer))})
        rack_tag_set = set(rack_tags)
        avd_tags = sorted(
            {name for peer in avd_tag_peers if (name := cls._peer_name(peer)) and name not in rack_tag_set}
        )
        return [*rack_tags, *avd_tags]

    @classmethod
    async def _fetch_relationship_peers(cls, obj: object, relationship_name: str) -> list[object]:
        relationship = getattr(obj, relationship_name, None)
        if relationship is None:
            return []

        await relationship.fetch()
        return [peer.peer for peer in getattr(relationship, "peers", [])]

    async def _filter_or_fetch_peers(
        self,
        *,
        kind: str,
        filter_name: str,
        parent_id: str | None,
        relationship: object | None,
    ) -> list[object]:
        objects: list[object] = []
        if parent_id:
            try:
                objects = await self.client.filters(kind=kind, **{filter_name: [parent_id]})
            except (AttributeError, KeyError):
                objects = []

        if objects:
            return objects

        if relationship is None:
            return []

        await relationship.fetch()
        return [peer.peer for peer in getattr(relationship, "peers", [])]

    @classmethod
    async def _fetch_relationship_peer_names(cls, obj: object, relationship_name: str) -> list[str]:
        return sorted(
            {
                name
                for peer in await cls._fetch_relationship_peers(obj, relationship_name)
                if (name := cls._peer_name(peer))
            }
        )

    async def _fetch_rack_avd_tags(self, rack_id: str | None) -> list[str]:
        if not rack_id:
            return []

        rack = await self.client.get(kind="LocationRack", id=rack_id, include=["avd_tags"])
        return await self._fetch_relationship_peer_names(rack, "avd_tags")

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

            # Prefer child-side filters; fall back to parent relationship peers for SDK/test objects without IDs.
            vrfs = await self._filter_or_fetch_peers(
                kind="IpamVRF",
                filter_name="tenant__ids",
                parent_id=getattr(tenant, "id", None),
                relationship=getattr(tenant, "vrfs", None),
            )
            vrfs_list: list[dict[str, Any]] = []
            for vrf in vrfs:
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

                svis = await self._filter_or_fetch_peers(
                    kind="EvpnSvi",
                    filter_name="vrf__ids",
                    parent_id=getattr(vrf, "id", None),
                    relationship=getattr(vrf, "svis", None),
                )
                svis_list: list[dict[str, Any]] = []
                for svi in svis:
                    svi_data: dict[str, Any] = {
                        "id": svi.svi_id.value,
                        "name": svi.name.value,
                        "enabled": svi.enabled.value,
                    }
                    if svi.ip_address_virtual and svi.ip_address_virtual.value:
                        svi_data["ip_address_virtual"] = str(svi.ip_address_virtual.value)
                    rack_tag_peers = await self._fetch_relationship_peers(svi, "rack_tags")
                    avd_tag_peers = await self._fetch_relationship_peers(svi, "avd_tags")
                    svi_tags = self._build_svi_tags(rack_tag_peers, avd_tag_peers)
                    if svi_tags:
                        svi_data["tags"] = svi_tags
                    svis_list.append(svi_data)

                if svis_list:
                    vrf_data["svis"] = svis_list
                vrfs_list.append(vrf_data)

            if vrfs_list:
                tenant_data["vrfs"] = vrfs_list

            l2vlans = await self._filter_or_fetch_peers(
                kind="EvpnL2Vlan",
                filter_name="tenant__ids",
                parent_id=getattr(tenant, "id", None),
                relationship=getattr(tenant, "l2vlans", None),
            )
            l2vlans_list: list[dict[str, Any]] = []
            for l2vlan in l2vlans:
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

    @classmethod
    def _extract_custom_hostvars(cls, source: object) -> dict[str, Any]:
        """Parse custom pyAVD hostvars from a GraphQL object."""
        raw_value = cls._gql_val(source, "avd_custom_hostvars")
        if raw_value in (None, "", [], {}):
            return {}

        parsed = yaml.safe_load(raw_value) if isinstance(raw_value, str) else raw_value
        if parsed in (None, "", [], {}):
            return {}
        if not isinstance(parsed, dict):
            raise TypeError("avd_custom_hostvars must be a mapping")
        return deepcopy(parsed)

    @classmethod
    def _deep_merge(cls, base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge ``overlay`` over ``base`` without mutating either input."""
        merged = deepcopy(base)
        for key, value in overlay.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = cls._deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    @classmethod
    def _merge_custom_hostvars(cls, *scopes: dict[str, Any]) -> dict[str, Any]:
        """Merge custom hostvar scopes in ascending precedence order."""
        merged: dict[str, Any] = {}
        for scope in scopes:
            if scope:
                merged = cls._deep_merge(merged, scope)
        return merged

    @staticmethod
    def _extract_mlag_info(device: object) -> dict[str, Any]:
        """Extract MLAG domain info for a device, including peer names."""
        device_mlag_domain = getattr(device, "mlag_domain", None)
        if not device_mlag_domain or not device_mlag_domain.node:
            return {"domain_id": None, "bgp_asn": None, "virtual_router_mac": None, "peer_names": []}

        mlag_domain = device_mlag_domain.node
        domain_id = mlag_domain.domain_id.value if mlag_domain.domain_id else None
        mlag_asn_rel = getattr(mlag_domain, "asn", None)
        bgp_asn = mlag_asn_rel.node.asn.value if mlag_asn_rel and mlag_asn_rel.node and mlag_asn_rel.node.asn else None
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
            "bgp_asn": bgp_asn,
            "virtual_router_mac": vrmac.value if vrmac else None,
            "peer_names": peer_names,
        }

    @staticmethod
    def _extract_rack_info(device: object) -> RackInfo:
        """Extract rack grouping data for leaf node_groups."""
        device_rack = getattr(device, "rack", None)
        if not device_rack or not device_rack.node:
            return {"name": None, "mlag": None, "leaf_names": [], "avd_tags": []}

        rack = device_rack.node
        rack_name = rack.name.value if getattr(rack, "name", None) else None
        rack_mlag = rack.mlag.value if getattr(rack, "mlag", None) else None

        leaf_names: list[str] = []
        devices = getattr(rack, "devices", None)
        if devices and hasattr(devices, "edges"):
            for edge in devices.edges:
                node = edge.node
                if not node or not getattr(node, "name", None):
                    continue
                role = getattr(node, "role", None)
                if role and role.value not in LEAF_FAMILY_ROLES:
                    continue
                leaf_names.append(node.name.value)

        return {"name": rack_name, "mlag": rack_mlag, "leaf_names": sorted(leaf_names), "avd_tags": []}

    @staticmethod
    def _extract_evpn_gateway_payload(device: object, *, hostname: str, role: str) -> EvpnGatewayPayload | None:
        """Build a pyAVD EVPN Gateway payload for an eligible Border Leaf target."""
        gateway = _relationship_node(device, "evpn_gateway_group")
        if gateway is None:
            return None

        if role != "border_leaf":
            raise _gateway_error(
                gateway, hostname, f"target device role must be 'border_leaf'; actual role is {role!r}"
            )

        if _value(gateway, "resiliency_model") != "all_active_multihoming":
            raise _gateway_error(gateway, hostname, "resiliency_model must be 'all_active_multihoming'")

        context = _validate_gateway_group_context(gateway, hostname)
        _validate_gateway_group_members(
            gateway=gateway,
            device=device,
            hostname=hostname,
            group_pod_id=context.group_pod_id,
        )
        remote_peer_hostnames = _derive_remote_peer_hostnames(
            gateway=gateway,
            device=device,
            hostname=hostname,
            context=context,
        )

        return {
            "remote_peers": [{"hostname": peer_hostname} for peer_hostname in remote_peer_hostnames],
            "evpn_l2": {"enabled": bool(_value(gateway, "evpn_l2_enabled"))},
            "evpn_l3": {
                "enabled": bool(_value(gateway, "evpn_l3_enabled")),
                "inter_domain": bool(_value(gateway, "evpn_l3_inter_domain")),
            },
            "d_path": {
                "enabled": bool(_value(gateway, "d_path_enabled")),
                "local_domain_id": context.local_domain_id,
                "remote_domain_id": context.remote_domain_id,
            },
            "all_active_multihoming": {
                "enabled": bool(_value(gateway, "all_active_multihoming_enabled")),
                "evpn_ethernet_segment": {
                    "identifier": _require_gateway_field(gateway, hostname, "ethernet_segment_identifier"),
                    "rt_import": _require_gateway_field(gateway, hostname, "ethernet_segment_rt_import"),
                },
            },
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
        evpn_vlan_aware_bundles: bool | None = None,
        mlag_capable: bool = False,
        spanning_tree_mode: str | None,
        spanning_tree_priorities: dict[str, int],
        loopback_ipv4_offset: int | None,
        bgp_passwords: dict[str, str | None],
        management: dict[str, Any],
        pools: dict[str, str | None],
        uplinks: UplinkData,
        rack_info: RackInfo,
        mlag_info: dict[str, Any],
        tenants_data: list[dict[str, Any]],
        connected_endpoints: list[ServerEndpoint],
        dci_l3_edge_p2p_links: list[dict[str, Any]] | None = None,
        evpn_gateway: EvpnGatewayPayload | None = None,
        custom_hostvars: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the complete pyAVD hostvars structure."""
        avd_type = get_generator_avd_type(role)
        node_type_key = "super_spine" if role == "super_spine" else avd_type

        # Build node config
        node_config: dict[str, Any] = {"name": hostname}
        if node_id is not None:
            node_config["id"] = node_id
        # Super-spines act as EVPN route servers in the multi-pod (5-stage Clos)
        # design. This is fully determined by the role, so derive it here.
        if role == "super_spine":
            node_config["evpn_role"] = "server"
        is_leaf_family = role in LEAF_FAMILY_ROLES
        # Renders MLAG constructs (node-group, mlag_domain_id, peer-link) for the
        # L3LS leaf family AND the non-L3LS main tier (l2leaf/l2spine/l3spine) when
        # the caller flags this device as MLAG-capable for its design.
        renders_mlag = is_leaf_family or mlag_capable
        is_mlag_leaf = bool(mlag_info.get("domain_id")) and renders_mlag
        if bgp_asn is not None and not is_mlag_leaf:
            node_config["bgp_as"] = str(bgp_asn)
        if loopback_ip:
            node_config["loopback_ipv4_address"] = loopback_ip
            if pools.get("loopback_ipv4_pool"):
                node_config["loopback_ipv4_pool"] = pools["loopback_ipv4_pool"]
        if mgmt_ip:
            node_config["mgmt_ip"] = mgmt_ip
        if evpn_gateway:
            node_config["evpn_gateway"] = evpn_gateway

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
        if mlag_info["domain_id"] and renders_mlag and "mlag_peer_interfaces" in mlag_info:
            node_config["mlag_interfaces"] = mlag_info["mlag_peer_interfaces"]

        # Only devices that render anycast SVIs (ip_address_virtual) need
        # virtual_router_mac at node level: L3 leaves, the l3spine campus core, and
        # MPLS PE routers. Gated on the role so fabric transit roles that carry a
        # fabric virtual_router_mac but no SVIs (spine/super_spine/p/rr) keep their
        # existing mac-free node config — routed L3LS spines are unaffected.
        if role in SVI_RENDERING_ROLES and virtual_router_mac and tenants_data:
            node_config["virtual_router_mac_address"] = virtual_router_mac

        # Build hostvars
        hostvars: dict[str, Any] = {"type": avd_type, "fabric_name": fabric_name}

        if mgmt_gateway:
            hostvars["mgmt_gateway"] = mgmt_gateway
        if virtual_router_mac:
            hostvars["virtual_router_mac_address"] = virtual_router_mac
        # Some underlay values are Infrahub design sentinels (standalone L2LS
        # "none"), not real pyAVD underlay values; omit the key for those and
        # let the node-type behavior apply.
        if underlay_routing_protocol and underlay_routing_protocol not in NON_EMITTED_UNDERLAYS:
            hostvars["underlay_routing_protocol"] = underlay_routing_protocol
        if overlay_routing_protocol:
            hostvars["overlay_routing_protocol"] = overlay_routing_protocol
        if evpn_vlan_aware_bundles:
            hostvars["evpn_vlan_aware_bundles"] = True
        if p2p_uplinks_mtu is not None:
            hostvars["p2p_uplinks_mtu"] = p2p_uplinks_mtu
        if spanning_tree_mode:
            hostvars["spanning_tree_settings"] = {"mode": spanning_tree_mode}

        role_priority = spanning_tree_priorities.get(role)
        if role_priority is not None:
            hostvars.setdefault(node_type_key, {})
            hostvars[node_type_key]["defaults"] = hostvars[node_type_key].get("defaults", {})
            hostvars[node_type_key]["defaults"]["spanning_tree_priority"] = role_priority

        # Loopback offset for leaf devices
        if loopback_ipv4_offset is not None and is_leaf_family:
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

        # Assemble the leaf node_group. MLAG grouping is a per-pair concept, so an
        # MLAG leaf is grouped by its MLAG domain (which is pair-unique — a rack with
        # multiple pairs yields several domains) and lists only its peer pair. A
        # non-MLAG rack groups every rack leaf together and disables MLAG at the
        # node-group level rather than in l3leaf.defaults.
        if renders_mlag:
            avd_tags = sorted(dict.fromkeys(rack_info.get("avd_tags", [])))
            if mlag_info["domain_id"]:
                mlag_bgp_asn = mlag_info.get("bgp_asn")
                pair_names = sorted(dict.fromkeys([*mlag_info.get("peer_names", []), hostname]))
                node_group: dict[str, Any] = {
                    "group": mlag_info["domain_id"],
                    "nodes": [{"name": name} for name in pair_names],
                    "mlag_domain_id": mlag_info["domain_id"],
                }
                # L3 leaves run iBGP across the MLAG pair, so an ASN is mandatory.
                # A pure-L2 MLAG tier (l2leaf/l2spine) runs no BGP and has none.
                if mlag_bgp_asn is not None:
                    node_group["bgp_as"] = str(mlag_bgp_asn)
                elif is_leaf_family:
                    msg = f"MLAG domain {mlag_info['domain_id']} for leaf {hostname} has no BGP ASN"
                    raise ValueError(msg)
                effective_vrmac = mlag_info["virtual_router_mac"] or virtual_router_mac
                if effective_vrmac:
                    node_group["virtual_router_mac_address"] = effective_vrmac
                if avd_tags:
                    node_group["filter"] = {"tags": avd_tags}
                hostvars[node_type_key]["node_groups"] = [node_group]
            else:
                rack_name = rack_info.get("name")
                leaf_names = sorted(dict.fromkeys([*rack_info.get("leaf_names", []), hostname]))
                if rack_name:
                    node_group = {
                        "group": rack_name,
                        "nodes": [{"name": leaf_name} for leaf_name in leaf_names],
                    }
                    if avd_tags:
                        node_group["filter"] = {"tags": avd_tags}
                    if rack_info.get("mlag") is False:
                        node_group["mlag"] = False
                    hostvars[node_type_key]["node_groups"] = [node_group]

        if tenants_data:
            hostvars["tenants"] = tenants_data
        if connected_endpoints:
            hostvars["servers"] = connected_endpoints
        if dci_l3_edge_p2p_links:
            hostvars["l3_edge"] = {"p2p_links": dci_l3_edge_p2p_links}

        if custom_hostvars:
            hostvars = GenerateAVDDeviceHostvar._deep_merge(custom_hostvars, hostvars)

        return hostvars

    async def generate(self, data: dict) -> None:  # noqa: C901 — top-level generator orchestration
        raw_data = data
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
        bgp_asn = device.asn.node.asn.value if device.asn and device.asn.node and device.asn.node.asn else None
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

        # Determine uplink role based on device role. In standalone L2LS/campus
        # fabrics the main leaf tier (l2leaf) uplinks to the spine tier
        # (l2spine/l3spine) via interface role "spine"; the access-tier l2leaf
        # under an L3LS fabric uplinks to the L3 leaf via interface role "leaf".
        # l2spine/l3spine are top-of-fabric (no uplinks).
        fabric_underlay = self._get_attr_value(fabric, "underlay_routing_protocol")
        uplink_role = None
        if role == "spine":
            uplink_role = "super_spine"
        elif role in LEAF_FAMILY_ROLES or role in SPINE_UPLINK_LEAF_ROLES:
            uplink_role = "spine"
        elif role == "l2leaf":
            uplink_role = "spine" if fabric_underlay in SPINE_UPLINK_UNDERLAYS else "leaf"

        # Extract uplinks
        iface_edges = device.interfaces.edges or []
        uplinks = extract_uplinks_from_dict(iface_edges, uplink_role, device_id)

        is_l2leaf = role == "l2leaf"
        # In non-L3LS designs (standalone L2LS "none", campus "ospf") the main tier
        # (l2leaf/l2spine/l3spine) forms MLAG pairs and needs node-group / peer-link
        # rendering. Gated on the underlay so the L3LS access-tier l2leaf is untouched.
        mlag_capable = role in MLAG_MAIN_TIER_ROLES and fabric_underlay in SPINE_UPLINK_UNDERLAYS

        # Extract fabric L3LS settings (with backwards-compatible fallbacks)
        # L2 leafs don't participate in EVPN/BGP/VXLAN so skip most L3 settings
        virtual_router_mac = None if is_l2leaf else self._get_attr_value(fabric, "virtual_router_mac")
        underlay_routing_protocol = None if is_l2leaf else self._get_attr_value(fabric, "underlay_routing_protocol")
        overlay_routing_protocol = None if is_l2leaf else self._get_attr_value(fabric, "overlay_routing_protocol")
        evpn_vlan_aware_bundles = None if is_l2leaf else self._get_attr_value(fabric, "evpn_vlan_aware_bundles")
        p2p_uplinks_mtu = (
            None if is_l2leaf else self._get_first_attr_value(fabric, "p_2_p_uplinks_mtu", "p2p_uplinks_mtu")
        )
        spanning_tree_mode = self._get_attr_value(fabric, "spanning_tree_mode")
        spanning_tree_priorities: dict[str, int] = {}
        spanning_tree_priority_edges = getattr(getattr(fabric, "spanning_tree_priorities", None), "edges", None) or []
        for edge in spanning_tree_priority_edges:
            priority_node = edge.node
            if not priority_node:
                continue
            priority_role = self._get_attr_value(priority_node, "role")
            priority_value = self._get_attr_value(priority_node, "priority")
            if priority_role and priority_value is not None:
                spanning_tree_priorities[priority_role] = priority_value
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
        custom_hostvars = self._merge_custom_hostvars(
            self._extract_custom_hostvars(fabric),
            self._extract_custom_hostvars(pod),
            self._extract_custom_hostvars(device),
        )

        # Extract configurable IP pools. L2 leafs run no L3 underlay/overlay, so
        # the uplink/vtep/loopback/mlag-L3 pools stay unset. A main-tier l2leaf
        # (mlag_capable) still forms an MLAG pair, so it needs the pod's MLAG
        # peer-link pool — without it PyAVD cannot address the peer-link SVI.
        if is_l2leaf:
            pools: dict[str, str | None] = {
                "uplink_ipv4_pool": None,
                "vtep_loopback_ipv4_pool": None,
                "loopback_ipv4_pool": None,
                "mlag_peer_ipv4_pool": None,
                "mlag_peer_l3_ipv4_pool": None,
            }
            if mlag_capable:
                pools["mlag_peer_ipv4_pool"] = await self._extract_pool_prefix(
                    getattr(pod, "mlag_peer_pool", None), "CoreIPAddressPool"
                )
        else:
            pools = await self._extract_l3ls_pools(fabric, pod)

        # Extract rack and MLAG domain info. Applies to L3 leaf devices and to the
        # non-L3LS main tier (mlag_capable l2leaf); the L3LS access-tier l2leaf is skipped.
        rack_info: RackInfo = {"name": None, "mlag": None, "leaf_names": []}
        mlag_info: dict[str, Any] = {"domain_id": None, "bgp_asn": None, "virtual_router_mac": None, "peer_names": []}
        if not is_l2leaf or mlag_capable:
            rack_info = self._extract_rack_info(device)
            rack_info["avd_tags"] = await self._fetch_rack_avd_tags(device.rack.node.id if device.rack.node else None)
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

        # Extract connected endpoints (servers). Only an L3 leaf/border_leaf drops
        # l2leaf remotes (its downlinks to access switches); a main-tier l2leaf
        # serves endpoints directly and its dual-homed legs land on sibling l2leaf
        # switches of the same MLAG pair, which must be retained.
        connected_endpoints = extract_connected_endpoints(
            iface_edges,
            hostname,
            mlag_active=bool(mlag_info["domain_id"]),
            skip_l2leaf_endpoints=role in LEAF_FAMILY_ROLES,
        )

        # Fetch tenant/VLAN services. Skipped only for the L3LS access-tier
        # l2leaf (pure access under an EVPN fabric); in a standalone L2LS/campus
        # fabric the l2leaf is the main tier and carries the fabric's VLANs.
        tenants_data: list[dict[str, Any]] = []
        if not is_l2leaf or fabric_underlay in SPINE_UPLINK_UNDERLAYS:
            tenants_data = await self._build_tenants_hostvars(fabric.id)

        dci_l3_edge_p2p_links: list[dict[str, Any]] = []
        raw_dci_links = [
            edge.get("node")
            for edge in (raw_data.get("NetworkLink", {}).get("edges") or [])
            if isinstance(edge, dict) and edge.get("node")
        ]
        if raw_dci_links and role == "border_leaf":
            dci_l3_edge_p2p_links = await build_dci_l3_edge_p2p_links(
                self.client,
                dci_links=raw_dci_links,
                hostname=hostname,
                underlay_routing_protocol=underlay_routing_protocol,
            )

        evpn_gateway = self._extract_evpn_gateway_payload(device, hostname=hostname, role=role)

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
            evpn_vlan_aware_bundles=evpn_vlan_aware_bundles,
            mlag_capable=mlag_capable,
            p2p_uplinks_mtu=p2p_uplinks_mtu,
            spanning_tree_mode=spanning_tree_mode,
            spanning_tree_priorities=spanning_tree_priorities,
            loopback_ipv4_offset=loopback_ipv4_offset,
            bgp_passwords=bgp_passwords,
            management=management,
            pools=pools,
            uplinks=uplinks,
            rack_info=rack_info,
            mlag_info=mlag_info,
            tenants_data=tenants_data,
            connected_endpoints=connected_endpoints,
            dci_l3_edge_p2p_links=dci_l3_edge_p2p_links,
            evpn_gateway=evpn_gateway,
            custom_hostvars=custom_hostvars,
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
