"""Unit tests for deterministic interface ordering in hostvar generation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from generators import generate_avd_device_inputs_query as q
from generators.generate_avd_device_hostvar import (
    build_dci_l3_edge_p2p_links,
    extract_connected_endpoints,
    extract_uplinks_from_dict,
)

# Short aliases for deeply nested Pydantic model types
IfaceEdge = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges
IfaceNode = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysical
IfaceName = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalName
IfaceRole = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalRole
IfaceConnector = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnector
ConnectorNode = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNode
ConnectorEndpoints = (
    q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpoints
)
EndpointEdge = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdges
_ep = "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalConnectorNodeConnectedEndpointsEdgesNode"
EndpointIface = getattr(q, f"{_ep}DcimInterface")
EndpointIfaceName = getattr(q, f"{_ep}DcimInterfaceName")
EndpointDevice = getattr(q, f"{_ep}DcimInterfaceDevice")
EndpointNetworkDevice = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimDevice")
EndpointNetworkDeviceName = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimDeviceName")
EndpointNetworkDeviceRole = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimDeviceRole")
EndpointGenericDevice = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimGenericDevice")
EndpointGenericDeviceName = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimGenericDeviceName")
EndpointPhysical = getattr(q, f"{_ep}InterfacePhysical")
EndpointPhysicalName = getattr(q, f"{_ep}InterfacePhysicalName")
EndpointPhysicalDevice = getattr(q, f"{_ep}InterfacePhysicalDevice")
EndpointPhysicalGenericDevice = getattr(q, f"{_ep}InterfacePhysicalDeviceNodeDcimGenericDevice")
EndpointPhysicalGenericDeviceName = getattr(q, f"{_ep}InterfacePhysicalDeviceNodeDcimGenericDeviceName")
EndpointPhysicalLag = getattr(q, f"{_ep}InterfacePhysicalLag")
EndpointPhysicalLagNode = getattr(q, f"{_ep}InterfacePhysicalLagNode")
EndpointPhysicalLagNodeName = getattr(q, f"{_ep}InterfacePhysicalLagNodeName")
EndpointPhysicalLagNodeLacpMode = getattr(q, f"{_ep}InterfacePhysicalLagNodeLacpMode")
EndpointPhysicalLagNodeEvpnEthernetSegment = getattr(q, f"{_ep}InterfacePhysicalLagNodeEvpnEthernetSegment")
TaggedVlan = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalTaggedVlan
UntaggedVlan = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeInterfacePhysicalUntaggedVlan


def _attr(value: object) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _dci_endpoint(endpoint_id: str, device_id: str, device_name: str, interface_name: str) -> dict:
    return {
        "__typename": "InterfacePhysical",
        "id": endpoint_id,
        "name": {"value": interface_name},
        "device": {
            "node": {
                "__typename": "DcimDevice",
                "id": device_id,
                "name": {"value": device_name},
                "role": {"value": "border_leaf"},
            }
        },
    }


def _dci_link(link_id: str, name: str, local_interface: str, remote_interface: str) -> dict:
    return {
        "__typename": "NetworkLink",
        "id": link_id,
        "display_label": name,
        "name": {"value": name},
        "role": {"value": "dci"},
        "include_in_underlay_protocol": {"value": True},
        "endpoint_1_bgp_asn": {"value": 65101},
        "endpoint_2_bgp_asn": {"value": 65201},
        "connected_endpoints": {
            "edges": [
                {
                    "node": _dci_endpoint(
                        f"local-{local_interface}",
                        "dc1-leaf1",
                        "ih-dc1-leaf1a",
                        local_interface,
                    )
                },
                {
                    "node": _dci_endpoint(
                        f"remote-{remote_interface}",
                        "dc2-leaf1",
                        "ih-dc2-leaf1a",
                        remote_interface,
                    )
                },
            ]
        },
    }


def _make_uplink_edge(
    iface_id: str,
    iface_name: str,
    role: str,
    remote_iface_id: str,
    remote_iface_name: str,
    remote_device_id: str,
    remote_hostname: str,
) -> IfaceEdge:
    """Helper to build a single uplink interface edge for testing."""
    return IfaceEdge(
        node=IfaceNode(
            __typename="InterfacePhysical",
            id=iface_id,
            name=IfaceName(value=iface_name),
            role=IfaceRole(value=role),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            lag={"node": None},
            connector=IfaceConnector(
                node=ConnectorNode(
                    __typename="NetworkLink",
                    id=f"link-{iface_id}",
                    connected_endpoints=ConnectorEndpoints(
                        edges=[
                            EndpointEdge(
                                node=EndpointIface(
                                    __typename="DcimInterface",
                                    id=remote_iface_id,
                                    name=EndpointIfaceName(value=remote_iface_name),
                                    device=EndpointDevice(
                                        node=EndpointNetworkDevice(
                                            __typename="DcimDevice",
                                            id=remote_device_id,
                                            name=EndpointNetworkDeviceName(value=remote_hostname),
                                            role=EndpointNetworkDeviceRole(value="spine"),
                                        )
                                    ),
                                )
                            )
                        ]
                    ),
                )
            ),
        )
    )


def _make_server_edge(
    iface_id: str,
    iface_name: str,
    remote_iface_id: str,
    remote_iface_name: str,
    remote_device_id: str,
    remote_hostname: str,
) -> IfaceEdge:
    """Helper to build a single server interface edge for testing."""
    return IfaceEdge(
        node=IfaceNode(
            __typename="InterfacePhysical",
            id=iface_id,
            name=IfaceName(value=iface_name),
            role=IfaceRole(value="server"),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            lag={"node": None},
            connector=IfaceConnector(
                node=ConnectorNode(
                    __typename="NetworkLink",
                    id=f"link-{iface_id}",
                    connected_endpoints=ConnectorEndpoints(
                        edges=[
                            EndpointEdge(
                                node=EndpointIface(
                                    __typename="DcimInterface",
                                    id=remote_iface_id,
                                    name=EndpointIfaceName(value=remote_iface_name),
                                    device=EndpointDevice(
                                        node=EndpointGenericDevice(
                                            __typename="ComputePhysicalServer",
                                            id=remote_device_id,
                                            name=EndpointGenericDeviceName(value=remote_hostname),
                                        )
                                    ),
                                )
                            )
                        ]
                    ),
                )
            ),
        )
    )


def _make_lagged_server_edge() -> IfaceEdge:
    """Build one local leaf link whose server-side LAG spans two switches."""
    lag = EndpointPhysicalLagNode.model_construct(
        typename__="InterfaceLag",
        id="lag-1",
        name=EndpointPhysicalLagNodeName(value="Bond1"),
        channel_id=None,
        lacp_mode=EndpointPhysicalLagNodeLacpMode(value="active"),
        evpn_ethernet_segment=EndpointPhysicalLagNodeEvpnEthernetSegment(value=False),
        lag_members={
            "edges": [
                {
                    "node": {
                        "__typename": "InterfacePhysical",
                        "id": "server-eth1",
                        "name": {"value": "Ethernet1"},
                        "connector": {
                            "node": {
                                "__typename": "NetworkLink",
                                "id": "link-1",
                                "connected_endpoints": {
                                    "edges": [
                                        {"node": {"__typename": "InterfacePhysical", "id": "server-eth1"}},
                                        {
                                            "node": {
                                                "__typename": "InterfacePhysical",
                                                "id": "leaf1-eth17",
                                                "name": {"value": "Ethernet1/1/17"},
                                                "device": {
                                                    "node": {
                                                        "__typename": "DcimDevice",
                                                        "id": "leaf1",
                                                        "name": {"value": "leaf-pod-b2-1-1"},
                                                        "role": {"value": "leaf"},
                                                    }
                                                },
                                            }
                                        },
                                    ]
                                },
                            }
                        },
                    }
                },
                {
                    "node": {
                        "__typename": "InterfacePhysical",
                        "id": "server-eth2",
                        "name": {"value": "Ethernet2"},
                        "connector": {
                            "node": {
                                "__typename": "NetworkLink",
                                "id": "link-2",
                                "connected_endpoints": {
                                    "edges": [
                                        {"node": {"__typename": "InterfacePhysical", "id": "server-eth2"}},
                                        {
                                            "node": {
                                                "__typename": "InterfacePhysical",
                                                "id": "leaf2-eth17",
                                                "name": {"value": "Ethernet1/1/17"},
                                                "device": {
                                                    "node": {
                                                        "__typename": "DcimDevice",
                                                        "id": "leaf2",
                                                        "name": {"value": "leaf-pod-b2-1-2"},
                                                        "role": {"value": "leaf"},
                                                    }
                                                },
                                            }
                                        },
                                    ]
                                },
                            }
                        },
                    }
                },
            ]
        },
    )

    return IfaceEdge(
        node=IfaceNode(
            __typename="InterfacePhysical",
            id="leaf1-eth17",
            name=IfaceName(value="Ethernet1/1/17"),
            role=IfaceRole(value="server"),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            lag={
                "node": {
                    "__typename": "InterfaceLag",
                    "id": "leaf1-po1117",
                    "name": {"value": "Port-Channel1117"},
                    "channel_id": {"value": 1117},
                    "lacp_mode": {"value": "active"},
                    "evpn_ethernet_segment": {"value": True},
                }
            },
            connector=IfaceConnector(
                node=ConnectorNode(
                    __typename="NetworkLink",
                    id="link-1",
                    connected_endpoints=ConnectorEndpoints(
                        edges=[
                            EndpointEdge(
                                node=EndpointPhysical(
                                    __typename="InterfacePhysical",
                                    id="server-eth1",
                                    name=EndpointPhysicalName(value="Ethernet1"),
                                    lag=EndpointPhysicalLag(node=lag),
                                    device=EndpointPhysicalDevice(
                                        node=EndpointPhysicalGenericDevice(
                                            __typename="ComputePhysicalServer",
                                            id="server-1",
                                            name=EndpointPhysicalGenericDeviceName(value="server-b2-1-aa-esi-1"),
                                        )
                                    ),
                                )
                            )
                        ]
                    ),
                )
            ),
        )
    )


def _make_switch_lagged_server_edge(
    *,
    iface_id: str,
    iface_name: str,
    switch_name: str,
    server_iface_id: str,
    server_iface_name: str,
    channel_id: int,
) -> IfaceEdge:
    """Build a local leaf link with only a switch-side LAG modeled."""
    return IfaceEdge(
        node=IfaceNode(
            __typename="InterfacePhysical",
            id=iface_id,
            name=IfaceName(value=iface_name),
            role=IfaceRole(value="server"),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            lag={
                "node": {
                    "__typename": "InterfaceLag",
                    "id": f"{switch_name}-po{channel_id}",
                    "name": {"value": f"Port-Channel{channel_id}"},
                    "channel_id": {"value": channel_id},
                    "lacp_mode": {"value": "active"},
                    "evpn_ethernet_segment": {"value": True},
                }
            },
            connector=IfaceConnector(
                node=ConnectorNode(
                    __typename="NetworkLink",
                    id=f"link-{iface_id}",
                    connected_endpoints=ConnectorEndpoints(
                        edges=[
                            EndpointEdge(
                                node=EndpointPhysical(
                                    __typename="InterfacePhysical",
                                    id=server_iface_id,
                                    name=EndpointPhysicalName(value=server_iface_name),
                                    lag=EndpointPhysicalLag(node=None),
                                    device=EndpointPhysicalDevice(
                                        node=EndpointPhysicalGenericDevice(
                                            __typename="ComputePhysicalServer",
                                            id="server-1",
                                            name=EndpointPhysicalGenericDeviceName(value="server-a"),
                                        )
                                    ),
                                )
                            )
                        ]
                    ),
                )
            ),
        )
    )


class TestExtractUplinksOrdering:
    """Tests for deterministic ordering in extract_uplinks_from_dict()."""

    def test_uplinks_sorted_by_interface_name(self) -> None:
        """Uplink lists should be sorted by local interface name."""
        # Interfaces deliberately in reverse order
        edges = [
            _make_uplink_edge("i3", "Ethernet3", "spine", "r3", "Ethernet1", "d3", "spine-3"),
            _make_uplink_edge("i1", "Ethernet1", "spine", "r1", "Ethernet3", "d1", "spine-1"),
            _make_uplink_edge("i2", "Ethernet2", "spine", "r2", "Ethernet2", "d2", "spine-2"),
        ]

        result = extract_uplinks_from_dict(edges, "spine", "local-device-id")

        assert result["uplink_interfaces"] == ["Ethernet1", "Ethernet2", "Ethernet3"]
        assert result["uplink_switches"] == ["spine-1", "spine-2", "spine-3"]
        assert result["uplink_switch_interfaces"] == ["Ethernet3", "Ethernet2", "Ethernet1"]

    def test_uplinks_lockstep_after_sort(self) -> None:
        """The three uplink lists must remain in lockstep after sorting."""
        edges = [
            _make_uplink_edge("i2", "Ethernet50", "spine", "r2", "Ethernet5", "d2", "spine-2"),
            _make_uplink_edge("i1", "Ethernet49", "spine", "r1", "Ethernet3", "d1", "spine-1"),
        ]

        result = extract_uplinks_from_dict(edges, "spine", "local-device-id")

        assert result["uplink_interfaces"] == ["Ethernet49", "Ethernet50"]
        assert result["uplink_switches"] == ["spine-1", "spine-2"]
        assert result["uplink_switch_interfaces"] == ["Ethernet3", "Ethernet5"]

    def test_uplinks_already_sorted(self) -> None:
        """Already-sorted input should produce identical output."""
        edges = [
            _make_uplink_edge("i1", "Ethernet1", "spine", "r1", "Ethernet1", "d1", "spine-1"),
            _make_uplink_edge("i2", "Ethernet2", "spine", "r2", "Ethernet2", "d2", "spine-2"),
        ]

        result = extract_uplinks_from_dict(edges, "spine", "local-device-id")

        assert result["uplink_interfaces"] == ["Ethernet1", "Ethernet2"]
        assert result["uplink_switches"] == ["spine-1", "spine-2"]

    def test_empty_uplinks(self) -> None:
        """Empty interface list should return empty uplink lists."""
        result = extract_uplinks_from_dict([], "spine", "local-device-id")
        assert result["uplink_interfaces"] == []
        assert result["uplink_switches"] == []
        assert result["uplink_switch_interfaces"] == []

    def test_no_uplink_role(self) -> None:
        """None uplink_role should return empty lists."""
        result = extract_uplinks_from_dict([], None, "local-device-id")
        assert result["uplink_interfaces"] == []

    def test_single_uplink(self) -> None:
        """Single uplink should be returned as-is."""
        edges = [
            _make_uplink_edge("i1", "Ethernet49", "spine", "r1", "Ethernet1", "d1", "spine-1"),
        ]
        result = extract_uplinks_from_dict(edges, "spine", "local-device-id")
        assert result["uplink_interfaces"] == ["Ethernet49"]
        assert result["uplink_switches"] == ["spine-1"]

    def test_mixed_roles_only_uplinks_sorted(self) -> None:
        """Non-uplink interfaces should be excluded; uplinks should be sorted."""
        uplink_edge = _make_uplink_edge("i2", "Ethernet2", "spine", "r2", "Ethernet1", "d2", "spine-1")
        uplink_edge2 = _make_uplink_edge("i1", "Ethernet1", "spine", "r1", "Ethernet2", "d1", "spine-2")
        # A server interface should be ignored
        server_edge = _make_server_edge("s1", "Ethernet49", "rs1", "eth0", "ds1", "server-1")

        edges = [uplink_edge, server_edge, uplink_edge2]
        result = extract_uplinks_from_dict(edges, "spine", "local-device-id")

        assert result["uplink_interfaces"] == ["Ethernet1", "Ethernet2"]
        assert result["uplink_switches"] == ["spine-2", "spine-1"]

    def test_different_input_orders_produce_same_output(self) -> None:
        """Verify idempotency: different orderings of the same interfaces produce identical results."""
        edge1 = _make_uplink_edge("i1", "Ethernet1", "spine", "r1", "Ethernet5", "d1", "spine-1")
        edge2 = _make_uplink_edge("i2", "Ethernet2", "spine", "r2", "Ethernet4", "d2", "spine-2")
        edge3 = _make_uplink_edge("i3", "Ethernet3", "spine", "r3", "Ethernet3", "d3", "spine-3")

        result_abc = extract_uplinks_from_dict([edge1, edge2, edge3], "spine", "x")
        result_cab = extract_uplinks_from_dict([edge3, edge1, edge2], "spine", "x")
        result_bca = extract_uplinks_from_dict([edge2, edge3, edge1], "spine", "x")

        assert result_abc == result_cab == result_bca


@pytest.mark.anyio
async def test_dci_links_are_sorted_by_link_and_endpoint_identity() -> None:
    client = AsyncMock()
    client.allocate_next_ip_prefix = AsyncMock(
        side_effect=[
            SimpleNamespace(prefix=_attr("172.16.0.0/31")),
            SimpleNamespace(prefix=_attr("172.16.0.2/31")),
        ]
    )

    result = await build_dci_l3_edge_p2p_links(
        client,
        fabric={"dci_pool": {"node": SimpleNamespace(id="pool-1")}},
        dci_links=[
            _dci_link("dci-2", "DCI-2", "Ethernet6", "Ethernet6"),
            _dci_link("dci-1", "DCI-1", "Ethernet5", "Ethernet5"),
        ],
        hostname="ih-dc1-leaf1a",
    )

    assert [link["interfaces"] for link in result] == [["Ethernet5", "Ethernet5"], ["Ethernet6", "Ethernet6"]]
    assert [link["ip"] for link in result] == [["172.16.0.0/31", "172.16.0.1/31"], ["172.16.0.2/31", "172.16.0.3/31"]]


class TestExtractConnectedEndpointsOrdering:
    """Tests for deterministic ordering in extract_connected_endpoints()."""

    def test_servers_sorted_by_name(self) -> None:
        """Servers should be sorted alphabetically by name."""
        edges = [
            _make_server_edge("s2", "Ethernet50", "rs2", "eth0", "ds2", "server-b"),
            _make_server_edge("s1", "Ethernet49", "rs1", "eth0", "ds1", "server-a"),
        ]

        result = extract_connected_endpoints(edges, "leaf-1")

        assert len(result) == 2
        assert result[0]["name"] == "server-a"
        assert result[1]["name"] == "server-b"

    def test_adapters_sorted_by_switch_port(self) -> None:
        """Adapters within a server should be sorted by switch port name."""
        edges = [
            _make_server_edge("s2", "Ethernet51", "rs2", "eth1", "ds1", "server-a"),
            _make_server_edge("s1", "Ethernet49", "rs1", "eth0", "ds1", "server-a"),
            _make_server_edge("s3", "Ethernet50", "rs3", "eth2", "ds1", "server-a"),
        ]

        result = extract_connected_endpoints(edges, "leaf-1")

        assert len(result) == 1
        assert result[0]["name"] == "server-a"
        adapters = result[0]["adapters"]
        assert len(adapters) == 3
        assert adapters[0]["switch_ports"] == ["Ethernet49"]
        assert adapters[1]["switch_ports"] == ["Ethernet50"]
        assert adapters[2]["switch_ports"] == ["Ethernet51"]

    def test_empty_server_list(self) -> None:
        """No server interfaces should return empty list."""
        result = extract_connected_endpoints([], "leaf-1")
        assert result == []

    def test_different_input_orders_produce_same_output(self) -> None:
        """Different orderings of server edges produce identical results."""
        edge_a = _make_server_edge("s1", "Ethernet49", "rs1", "eth0", "ds1", "server-a")
        edge_b = _make_server_edge("s2", "Ethernet50", "rs2", "eth0", "ds2", "server-b")
        edge_c = _make_server_edge("s3", "Ethernet51", "rs3", "eth1", "ds1", "server-a")

        result_abc = extract_connected_endpoints([edge_a, edge_b, edge_c], "leaf-1")
        result_cba = extract_connected_endpoints([edge_c, edge_b, edge_a], "leaf-1")
        result_bac = extract_connected_endpoints([edge_b, edge_a, edge_c], "leaf-1")

        assert result_abc == result_cba == result_bac

    def test_uplink_edges_excluded(self) -> None:
        """Uplink interfaces should not appear in connected endpoints."""
        uplink = _make_uplink_edge("i1", "Ethernet1", "spine", "r1", "Ethernet1", "d1", "spine-1")
        server = _make_server_edge("s1", "Ethernet49", "rs1", "eth0", "ds1", "server-a")

        result = extract_connected_endpoints([uplink, server], "leaf-1")

        assert len(result) == 1
        assert result[0]["name"] == "server-a"

    def test_evpn_multihomed_lag_collapses_to_multi_switch_adapter(self) -> None:
        """Server LAG members on different non-MLAG leaves must emit one EVPN MH adapter."""
        result = extract_connected_endpoints([_make_lagged_server_edge()], "leaf-pod-b2-1-1")

        assert result == [
            {
                "name": "server-b2-1-aa-esi-1",
                "adapters": [
                    {
                        "endpoint_ports": ["Ethernet1", "Ethernet2"],
                        "switch_ports": ["Ethernet1/1/17", "Ethernet1/1/17"],
                        "switches": ["leaf-pod-b2-1-1", "leaf-pod-b2-1-2"],
                        "port_channel": {
                            "mode": "active",
                            "channel_id": 1117,
                            "endpoint_port_channel": "Bond1",
                        },
                        "ethernet_segment": {"short_esi": "auto"},
                        "spanning_tree_portfast": "edge",
                    }
                ],
            }
        ]

    def test_switch_lag_without_server_bond_emits_port_channel(self) -> None:
        """Switch-side Port-Channel modeling is enough to emit pyAVD port_channel."""
        edges = [
            _make_switch_lagged_server_edge(
                iface_id="leaf1-eth17",
                iface_name="Ethernet1/1/17",
                switch_name="leaf-pod-b2-1-1",
                server_iface_id="server-eth1",
                server_iface_name="Ethernet1",
                channel_id=1117,
            ),
            _make_switch_lagged_server_edge(
                iface_id="leaf2-eth17",
                iface_name="Ethernet1/1/17",
                switch_name="leaf-pod-b2-1-2",
                server_iface_id="server-eth2",
                server_iface_name="Ethernet2",
                channel_id=1117,
            ),
        ]

        result = extract_connected_endpoints(edges, "leaf-pod-b2-1-1")

        assert result[0]["adapters"] == [
            {
                "endpoint_ports": ["Ethernet1", "Ethernet2"],
                "switch_ports": ["Ethernet1/1/17", "Ethernet1/1/17"],
                "switches": ["leaf-pod-b2-1-1", "leaf-pod-b2-1-1"],
                "port_channel": {"mode": "active", "channel_id": 1117},
                "spanning_tree_portfast": "edge",
            }
        ]
