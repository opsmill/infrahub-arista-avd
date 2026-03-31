"""Unit tests for deterministic interface ordering in hostvar generation."""

from __future__ import annotations

from generators import generate_avd_device_inputs_query as q
from generators.generate_avd_device_hostvar import (
    extract_connected_endpoints,
    extract_uplinks_from_dict,
)

# Short aliases for deeply nested Pydantic model types
IfaceEdge = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdges
IfaceNode = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNode
IfaceName = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeName
IfaceRole = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeRole
IfaceConnector = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeConnector
ConnectorNode = q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeConnectorNode
ConnectorEndpoints = (
    q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeConnectorNodeConnectedEndpoints
)
EndpointEdge = (
    q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeConnectorNodeConnectedEndpointsEdges
)
_ep = "GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeConnectorNodeConnectedEndpointsEdgesNode"
EndpointIface = getattr(q, f"{_ep}DcimInterface")
EndpointIfaceName = getattr(q, f"{_ep}DcimInterfaceName")
EndpointDevice = getattr(q, f"{_ep}DcimInterfaceDevice")
EndpointNetworkDevice = getattr(q, f"{_ep}DcimInterfaceDeviceNodeDcimDevice")
EndpointNetworkDeviceName = getattr(
    q, f"{_ep}DcimInterfaceDeviceNodeDcimDeviceName"
)
EndpointNetworkDeviceRole = getattr(
    q, f"{_ep}DcimInterfaceDeviceNodeDcimDeviceRole"
)
EndpointGenericDevice = getattr(
    q, f"{_ep}DcimInterfaceDeviceNodeDcimGenericDevice"
)
EndpointGenericDeviceName = getattr(
    q, f"{_ep}DcimInterfaceDeviceNodeDcimGenericDeviceName"
)
TaggedVlan = (
    q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeTaggedVlan
)
UntaggedVlan = (
    q.GenerateAvdDeviceInputsQueryDcimDeviceEdgesNodeInterfacesEdgesNodeUntaggedVlan
)


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
            id=iface_id,
            name=IfaceName(value=iface_name),
            role=IfaceRole(value=role),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            connector=IfaceConnector(
                node=ConnectorNode(
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
            id=iface_id,
            name=IfaceName(value=iface_name),
            role=IfaceRole(value="server"),
            tagged_vlan=TaggedVlan(edges=[]),
            untagged_vlan=UntaggedVlan(node=None),
            connector=IfaceConnector(
                node=ConnectorNode(
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
