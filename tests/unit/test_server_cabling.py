from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from generators.generate_server_cabling import ServerCablingGenerator
from solution_arista_avd.protocols import InterfacePhysical


def _make_generator(*, mock_cascade: bool = True) -> ServerCablingGenerator:
    """Create a generator instance with mocked client.

    Args:
        mock_cascade: If True, patch _trigger_avd_cascade to avoid needing
            rack→pod→fabric navigation setup in every test.
    """
    gen = ServerCablingGenerator.__new__(ServerCablingGenerator)
    gen.client = MagicMock()
    gen.client.filters = AsyncMock(return_value=[])
    gen.client.get = AsyncMock()
    gen.client.create = AsyncMock()
    if mock_cascade:
        gen._trigger_avd_cascade = AsyncMock()  # type: ignore[method-assign]
    gen._is_server_cabled = AsyncMock(return_value=False)  # type: ignore[method-assign]
    return gen


def _make_server_data(
    hostname: str = "server-1",
    rack_id: str = "rack-1",
    rack_name: str = "Rack-1",
    interfaces: list[dict] | None = None,
    no_rack: bool = False,
) -> dict:
    """Build a query response structure for a server."""
    if interfaces is None:
        interfaces = [_make_interface("iface-1", "Ethernet1")]

    server_node: dict = {
        "id": "server-1-id",
        "name": {"value": hostname},
        "role": {"value": "compute"},
        "status": {"value": "provisioning"},
        "interfaces": {"edges": [{"node": iface} for iface in interfaces]},
    }

    if no_rack:
        server_node["rack"] = None
    else:
        server_node["rack"] = {"node": {"id": rack_id, "name": {"value": rack_name}}}

    return {"ComputePhysicalServer": {"edges": [{"node": server_node}]}}


def _make_interface(
    iface_id: str = "iface-1",
    name: str = "Ethernet1",
    tagged_vlan_ids: list[dict] | None = None,
    untagged_vlan: dict | None = None,
    profile_tagged_vlan_ids: list[dict] | None = None,
    profile_untagged_vlan: dict | None = None,
) -> dict:
    """Build an interface node for the query response."""
    link: dict = {"node": None}

    tagged_edges = []
    if tagged_vlan_ids:
        tagged_edges = [{"node": v} for v in tagged_vlan_ids]

    profile_tagged_edges = []
    if profile_tagged_vlan_ids:
        profile_tagged_edges = [{"node": v} for v in profile_tagged_vlan_ids]

    profiles: dict = {"edges": []}
    if profile_tagged_vlan_ids or profile_untagged_vlan:
        profiles = {
            "edges": [
                {
                    "node": {
                        "id": "profile-1",
                        "profile_name": {"value": "profile-server-compute"},
                        "tagged_vlan": {"edges": profile_tagged_edges},
                        "untagged_vlan": profile_untagged_vlan or {"node": None},
                    }
                }
            ]
        }

    return {
        "__typename": "InterfacePhysical",
        "id": iface_id,
        "name": {"value": name},
        "role": {"value": "server"},
        "status": {"value": "inactive"},
        "link": link,
        "tagged_vlan": {"edges": tagged_edges},
        "untagged_vlan": untagged_vlan or {"node": None},
        "profiles": profiles,
    }


def _make_non_physical_interface(iface_id: str, typename: str) -> dict:
    """Build a non-physical interface node as returned outside the InterfacePhysical fragment."""
    return {
        "__typename": typename,
        "id": iface_id,
    }


def _make_mock_leaf(leaf_id: str = "leaf-1", hostname: str = "leaf-pod1-1-1") -> MagicMock:
    """Create a mock leaf switch."""
    leaf = MagicMock()
    leaf.id = leaf_id
    leaf.name.value = hostname
    leaf.mlag_domain = None
    leaf.mlag_domain_id = None
    return leaf


def _make_mock_leaf_interface(
    iface_id: str = "leaf-iface-1",
    name: str = "Ethernet1",
    leaf: MagicMock | None = None,
    has_connector: bool = False,
) -> MagicMock:
    """Create a mock leaf interface for sorted interface maps."""
    iface = MagicMock()
    iface.id = iface_id
    iface.name.value = name
    iface.save = AsyncMock()
    if leaf:
        iface.device.peer = leaf
        iface.device.id = leaf.id
        iface.device.display_label = leaf.name.value
    else:
        iface.device.peer = _make_mock_leaf()
        iface.device.id = iface.device.peer.id
        iface.device.display_label = "leaf-pod1-1-1"
    iface.connector.id = "existing-link" if has_connector else None
    return iface


class TestSingleHomedCabling:
    """T008: Test single-homed server cabling (1 interface -> 1 leaf)."""

    @pytest.mark.asyncio
    async def test_single_homed_creates_one_link(self) -> None:
        gen = _make_generator()

        iface = _make_interface(
            "iface-1", "Ethernet1", tagged_vlan_ids=[{"id": "vlan-300", "name": {"value": "Servers"}}]
        )
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        leaf_iface = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)

        # Mock server SDK interface for create_sorted_device_interface_map
        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.name.value = "Ethernet1"
        mock_server_iface.device.peer = MagicMock()
        mock_server_iface.device.display_label = "server-1"

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],  # leaf switches in rack
                [mock_server_iface],  # server DcimInterface objects
                [leaf_iface],  # leaf InterfacePhysical objects
            ]
        )
        gen.client.get = AsyncMock(return_value=mock_server_iface)

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            gen._assign_vlans = AsyncMock()
            await gen.generate(data)

            mock_connect.assert_called_once()
            cabling_plan = mock_connect.call_args.kwargs["cabling_plan"]
            assert len(cabling_plan) == 1


class TestIdempotency:
    """Re-running the generator on an already-cabled server reconciles generated state."""

    @pytest.mark.asyncio
    async def test_already_cabled_server_reconciles_without_reconnecting(self) -> None:
        gen = _make_generator()
        gen._is_server_cabled = AsyncMock(return_value=True)  # type: ignore[method-assign]
        gen._assign_vlans = AsyncMock()  # type: ignore[method-assign]
        gen._create_server_port_channel = AsyncMock()  # type: ignore[method-assign]

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])
        mock_leaf = _make_mock_leaf()
        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.name.value = "Ethernet1"
        mock_server_iface.device.peer = MagicMock()
        mock_server_iface.device.display_label = "server-1"
        leaf_iface = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)
        gen._existing_cabling_plan = AsyncMock(return_value=[(mock_server_iface, leaf_iface)])  # type: ignore[method-assign]

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],
                [mock_server_iface],
                [leaf_iface],
            ]
        )

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            await gen.generate(data)

        mock_connect.assert_not_called()
        gen._assign_vlans.assert_awaited_once()
        gen._create_server_port_channel.assert_awaited_once()
        gen._trigger_avd_cascade.assert_awaited_once_with("rack-1", "server-1", ["leaf-1"])

    @pytest.mark.asyncio
    async def test_already_cabled_server_ignores_non_physical_interfaces(self) -> None:
        gen = _make_generator()
        gen._is_server_cabled = AsyncMock(return_value=True)  # type: ignore[method-assign]
        gen._assign_vlans = AsyncMock()  # type: ignore[method-assign]
        gen._create_server_port_channel = AsyncMock()  # type: ignore[method-assign]

        data = _make_server_data(
            interfaces=[
                _make_interface("iface-1", "Ethernet1"),
                _make_non_physical_interface("bond-1", "InterfaceLag"),
                _make_non_physical_interface("vlan-100", "InterfaceVirtual"),
            ]
        )
        mock_leaf = _make_mock_leaf()
        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.name.value = "Ethernet1"
        mock_server_iface.device.peer = MagicMock()
        mock_server_iface.device.display_label = "server-1"
        leaf_iface = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)
        gen._existing_cabling_plan = AsyncMock(return_value=[(mock_server_iface, leaf_iface)])  # type: ignore[method-assign]

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],
                [mock_server_iface],
                [leaf_iface],
            ]
        )

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            await gen.generate(data)

        mock_connect.assert_not_called()
        gen._is_server_cabled.assert_awaited_once_with(
            [
                {
                    "id": "iface-1",
                    "name": "Ethernet1",
                    "tagged_vlan_ids": [],
                    "untagged_vlan_id": None,
                }
            ]
        )
        assert gen.client.filters.await_args_list[1].kwargs["kind"] is InterfacePhysical
        gen._assign_vlans.assert_awaited_once()
        gen._create_server_port_channel.assert_awaited_once()


class TestDualHomedCabling:
    """T009: Test dual-homed server cabling (2 interfaces -> 2 different leaves)."""

    @pytest.mark.asyncio
    async def test_dual_homed_distributes_across_leaves(self) -> None:
        gen = _make_generator()

        iface1 = _make_interface("iface-1", "Ethernet1")
        iface2 = _make_interface("iface-2", "Ethernet2")
        data = _make_server_data(interfaces=[iface1, iface2])

        mock_leaf1 = _make_mock_leaf("leaf-1", "leaf-pod1-1-1")
        mock_leaf2 = _make_mock_leaf("leaf-2", "leaf-pod1-1-2")

        leaf1_iface = _make_mock_leaf_interface("leaf1-eth1", "Ethernet1", leaf=mock_leaf1)
        leaf2_iface = _make_mock_leaf_interface("leaf2-eth1", "Ethernet1", leaf=mock_leaf2)

        mock_server_iface1 = MagicMock()
        mock_server_iface1.id = "iface-1"
        mock_server_iface1.name.value = "Ethernet1"
        mock_server_iface1.device.peer = MagicMock()
        mock_server_iface1.device.display_label = "server-1"

        mock_server_iface2 = MagicMock()
        mock_server_iface2.id = "iface-2"
        mock_server_iface2.name.value = "Ethernet2"
        mock_server_iface2.device.peer = mock_server_iface1.device.peer
        mock_server_iface2.device.display_label = "server-1"

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf1, mock_leaf2],  # leaf switches
                [mock_server_iface1, mock_server_iface2],  # server DcimInterface objects
                [leaf1_iface, leaf2_iface],  # leaf InterfacePhysical objects
            ]
        )
        gen.client.get = AsyncMock(return_value=mock_server_iface1)

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            gen._assign_vlans = AsyncMock()
            gen._create_server_port_channel = AsyncMock()
            await gen.generate(data)

            mock_connect.assert_called_once()
            cabling_plan = mock_connect.call_args.kwargs["cabling_plan"]
            assert len(cabling_plan) == 2

    @pytest.mark.asyncio
    async def test_dual_homed_creates_server_and_switch_lags(self) -> None:
        gen = _make_generator()

        mock_leaf1 = _make_mock_leaf("leaf-1", "leaf-pod1-1-1")
        mock_leaf2 = _make_mock_leaf("leaf-2", "leaf-pod1-1-2")
        leaf1_iface = _make_mock_leaf_interface("leaf1-eth17", "Ethernet1/1/17", leaf=mock_leaf1)
        leaf2_iface = _make_mock_leaf_interface("leaf2-eth17", "Ethernet1/1/17", leaf=mock_leaf2)

        server_device = MagicMock()
        server_device.id = "server-1-id"
        server_iface1 = MagicMock()
        server_iface1.id = "iface-1"
        server_iface1.name.value = "Ethernet1"
        server_iface1.device.id = server_device.id
        server_iface1.save = AsyncMock()
        server_iface2 = MagicMock()
        server_iface2.id = "iface-2"
        server_iface2.name.value = "Ethernet2"
        server_iface2.device.id = server_device.id
        server_iface2.save = AsyncMock()

        server_lag = MagicMock()
        server_lag.id = "server-bond-id"
        server_lag.save = AsyncMock()
        leaf1_lag = MagicMock()
        leaf1_lag.id = "leaf1-po-id"
        leaf1_lag.save = AsyncMock()
        leaf2_lag = MagicMock()
        leaf2_lag.id = "leaf2-po-id"
        leaf2_lag.save = AsyncMock()

        gen.client.get = AsyncMock(side_effect=[server_iface1, server_iface1, server_iface2, leaf1_iface, leaf2_iface])
        gen.client.create = AsyncMock(side_effect=[server_lag, leaf1_lag, leaf2_lag])

        await gen._create_server_port_channel(
            "server-1",
            [(server_iface1, leaf1_iface), (server_iface2, leaf2_iface)],
        )

        create_calls = gen.client.create.await_args_list
        assert create_calls[0].kwargs == {
            "name": "Bond1",
            "device": {"id": "server-1-id"},
            "lacp_mode": "active",
            "lacp_rate": "fast",
            "status": "active",
            "role": "server",
        }
        assert create_calls[0].args == ("InterfaceLag",)
        assert create_calls[1].kwargs["name"] == "Port-Channel1117"
        assert create_calls[1].kwargs["channel_id"] == 1117
        assert create_calls[1].kwargs["evpn_ethernet_segment"] is True
        assert create_calls[2].kwargs["name"] == "Port-Channel1117"
        assert create_calls[2].kwargs["channel_id"] == 1117
        assert create_calls[2].kwargs["evpn_ethernet_segment"] is True
        assert leaf1_iface.lag == {"id": "leaf1-po-id"}
        assert leaf2_iface.lag == {"id": "leaf2-po-id"}


class TestVlanAssignment:
    """T010: Test VLAN assignment via _assign_vlans."""

    @pytest.mark.asyncio
    async def test_tagged_vlans_copied_to_leaf(self) -> None:
        gen = _make_generator()

        server_ifaces = [
            {"id": "s1", "name": "Ethernet1", "tagged_vlan_ids": ["vlan-300", "vlan-400"], "untagged_vlan_id": None},
        ]

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_leaf_iface)

        mock_server_iface_obj = MagicMock()
        cabling_plan = [(mock_server_iface_obj, mock_leaf_iface)]

        await gen._assign_vlans(cabling_plan, server_ifaces)

        mock_leaf_iface.tagged_vlan.extend.assert_called_once_with(["vlan-300", "vlan-400"])

    @pytest.mark.asyncio
    async def test_untagged_vlan_copied_to_leaf(self) -> None:
        gen = _make_generator()

        server_ifaces = [
            {"id": "s1", "name": "Ethernet1", "tagged_vlan_ids": [], "untagged_vlan_id": "vlan-100"},
        ]

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_leaf_iface)

        mock_server_iface_obj = MagicMock()
        cabling_plan = [(mock_server_iface_obj, mock_leaf_iface)]

        await gen._assign_vlans(cabling_plan, server_ifaces)

        mock_leaf_iface.untagged_vlan.add.assert_called_once_with("vlan-100")


class TestNoLeafSwitches:
    """T012: Test warning when no leaf switches in rack."""

    @pytest.mark.asyncio
    async def test_no_leaves_logs_warning(self) -> None:
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        # No leaf switches returned
        gen.client.filters = AsyncMock(return_value=[])

        with patch.object(gen.logger, "warning") as mock_warn:
            await gen.generate(data)
            mock_warn.assert_called_once()
            assert "No leaf switches found" in mock_warn.call_args[0][0]


class TestInsufficientInterfaces:
    """T013: Test that insufficient leaf interfaces cables what it can."""

    @pytest.mark.asyncio
    async def test_insufficient_interfaces_cables_partial(self) -> None:
        gen = _make_generator()

        iface1 = _make_interface("iface-1", "Ethernet1")
        iface2 = _make_interface("iface-2", "Ethernet2")
        data = _make_server_data(interfaces=[iface1, iface2])

        mock_leaf = _make_mock_leaf()
        leaf_iface = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)

        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.name.value = "Ethernet1"
        mock_server_iface.device.peer = MagicMock()
        mock_server_iface.device.display_label = "server-1"

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],  # leaf switches
                [mock_server_iface],  # server DcimInterface objects
                [leaf_iface],  # leaf InterfacePhysical objects
            ]
        )
        gen.client.get = AsyncMock(return_value=mock_server_iface)

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            gen._assign_vlans = AsyncMock()
            await gen.generate(data)

            # Only one server interface in the SDK map (1 DcimInterface returned)
            # pairs with the single leaf interface
            mock_connect.assert_called_once()
            cabling_plan = mock_connect.call_args.kwargs["cabling_plan"]
            assert len(cabling_plan) == 1


class TestSingleLeafDualHomed:
    """T015: Test single leaf with dual-homed server."""

    @pytest.mark.asyncio
    async def test_both_interfaces_connect_to_single_leaf(self) -> None:
        gen = _make_generator()

        iface1 = _make_interface("iface-1", "Ethernet1")
        iface2 = _make_interface("iface-2", "Ethernet2")
        data = _make_server_data(interfaces=[iface1, iface2])

        mock_leaf = _make_mock_leaf("leaf-1", "leaf-pod1-1-1")
        leaf_iface1 = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)
        leaf_iface2 = _make_mock_leaf_interface("leaf-eth2", "Ethernet2", leaf=mock_leaf)

        mock_server_iface1 = MagicMock()
        mock_server_iface1.id = "iface-1"
        mock_server_iface1.name.value = "Ethernet1"
        mock_server_iface1.device.peer = MagicMock()
        mock_server_iface1.device.display_label = "server-1"
        mock_server_iface2 = MagicMock()
        mock_server_iface2.id = "iface-2"
        mock_server_iface2.name.value = "Ethernet2"
        mock_server_iface2.device.peer = mock_server_iface1.device.peer
        mock_server_iface2.device.display_label = "server-1"

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],  # leaf switches
                [mock_server_iface1, mock_server_iface2],  # server DcimInterface objects
                [leaf_iface1, leaf_iface2],  # leaf InterfacePhysical objects
            ]
        )
        gen.client.get = AsyncMock(return_value=mock_server_iface1)

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock) as mock_connect:
            gen._assign_vlans = AsyncMock()
            await gen.generate(data)

            # Both interfaces connected to same leaf at index 0
            mock_connect.assert_called_once()
            cabling_plan = mock_connect.call_args.kwargs["cabling_plan"]
            assert len(cabling_plan) == 2


class TestNoInterfaces:
    """T016: Test server with zero interfaces."""

    @pytest.mark.asyncio
    async def test_no_interfaces_logs_warning(self) -> None:
        gen = _make_generator()

        data = _make_server_data(interfaces=[])

        with patch.object(gen.logger, "warning") as mock_warn:
            await gen.generate(data)
            assert any("no interfaces" in str(call) for call in mock_warn.call_args_list)

        gen.client.create.assert_not_called()


class TestNoRack:
    """Test server without rack assignment."""

    @pytest.mark.asyncio
    async def test_no_rack_logs_warning(self) -> None:
        gen = _make_generator()

        data = _make_server_data(no_rack=True)

        with patch.object(gen.logger, "warning") as mock_warn:
            await gen.generate(data)
            assert any("no rack" in str(call) for call in mock_warn.call_args_list)

        gen.client.create.assert_not_called()


class TestBuildServerCablingPlan:
    """Test the cabling plan construction logic from cabling.py."""

    def test_round_robin_with_two_leaves(self) -> None:
        from solution_arista_avd.cabling import build_server_cabling_plan

        server = MagicMock()
        s1 = MagicMock()
        s1.id = "s1"
        s1.name.value = "Ethernet1"
        s1.device.peer = server

        leaf1 = _make_mock_leaf("leaf-1", "leaf-1")
        leaf2 = _make_mock_leaf("leaf-2", "leaf-2")
        l1_iface = _make_mock_leaf_interface("l1-e1", "Ethernet1", leaf=leaf1)
        l2_iface = _make_mock_leaf_interface("l2-e1", "Ethernet1", leaf=leaf2)

        plan = build_server_cabling_plan(
            server_index=0,
            src_interface_map={server: [s1]},
            dst_interface_map={leaf1: [l1_iface], leaf2: [l2_iface]},
        )

        assert len(plan) == 1
        assert plan[0][0].id == "s1"
        assert plan[0][1].id == "l1-e1"

    def test_dual_nic_across_two_leaves(self) -> None:
        from solution_arista_avd.cabling import build_server_cabling_plan

        server = MagicMock()
        s1 = MagicMock()
        s1.id = "s1"
        s1.name.value = "Ethernet1"
        s1.device.peer = server
        s2 = MagicMock()
        s2.id = "s2"
        s2.name.value = "Ethernet2"
        s2.device.peer = server

        leaf1 = _make_mock_leaf("leaf-1", "leaf-1")
        leaf2 = _make_mock_leaf("leaf-2", "leaf-2")
        l1_iface = _make_mock_leaf_interface("l1-e1", "Ethernet1", leaf=leaf1)
        l2_iface = _make_mock_leaf_interface("l2-e1", "Ethernet1", leaf=leaf2)

        plan = build_server_cabling_plan(
            server_index=0,
            src_interface_map={server: [s1, s2]},
            dst_interface_map={leaf1: [l1_iface], leaf2: [l2_iface]},
        )

        # s1 -> leaf1[0], s2 -> leaf2[0]
        assert len(plan) == 2
        assert plan[0][1].id == "l1-e1"
        assert plan[1][1].id == "l2-e1"


class TestExtractVlans:
    """Test VLAN extraction from interface and profile data."""

    def test_extracts_tagged_vlans_from_interface(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {
                "edges": [
                    {"node": {"id": "vlan-300", "name": {"value": "Servers"}}},
                    {"node": {"id": "vlan-400", "name": {"value": "Storage"}}},
                ]
            },
            "untagged_vlan": {"node": None},
            "profiles": {"edges": []},
        }

        result = gen._extract_vlans(interface_node)
        assert result["tagged"] == ["vlan-300", "vlan-400"]
        assert result["untagged"] is None

    def test_extracts_tagged_vlans_from_profile(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {"edges": []},
            "untagged_vlan": {"node": None},
            "profiles": {
                "edges": [
                    {
                        "node": {
                            "id": "profile-1",
                            "profile_name": {"value": "profile-server-compute"},
                            "tagged_vlan": {
                                "edges": [
                                    {"node": {"id": "vlan-300", "name": {"value": "Servers"}}},
                                    {"node": {"id": "vlan-400", "name": {"value": "Storage"}}},
                                ]
                            },
                            "untagged_vlan": {"node": None},
                        }
                    }
                ]
            },
        }

        result = gen._extract_vlans(interface_node)
        assert result["tagged"] == ["vlan-300", "vlan-400"]

    def test_merges_vlans_from_interface_and_profile(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {"edges": [{"node": {"id": "vlan-300", "name": {"value": "Servers"}}}]},
            "untagged_vlan": {"node": None},
            "profiles": {
                "edges": [
                    {
                        "node": {
                            "id": "profile-1",
                            "profile_name": {"value": "profile-server-compute"},
                            "tagged_vlan": {
                                "edges": [
                                    {"node": {"id": "vlan-300", "name": {"value": "Servers"}}},
                                    {"node": {"id": "vlan-400", "name": {"value": "Storage"}}},
                                ]
                            },
                            "untagged_vlan": {"node": None},
                        }
                    }
                ]
            },
        }

        result = gen._extract_vlans(interface_node)
        assert result["tagged"] == ["vlan-300", "vlan-400"]  # no duplicates

    def test_extracts_untagged_vlan_from_profile(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {"edges": []},
            "untagged_vlan": {"node": None},
            "profiles": {
                "edges": [
                    {
                        "node": {
                            "id": "profile-1",
                            "profile_name": {"value": "profile-server-compute"},
                            "tagged_vlan": {"edges": []},
                            "untagged_vlan": {"node": {"id": "vlan-100", "name": {"value": "MGMT"}}},
                        }
                    }
                ]
            },
        }

        result = gen._extract_vlans(interface_node)
        assert result["untagged"] == "vlan-100"

    def test_no_vlans_returns_empty(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {"edges": []},
            "untagged_vlan": {"node": None},
            "profiles": {"edges": []},
        }

        result = gen._extract_vlans(interface_node)
        assert result["tagged"] == []
        assert result["untagged"] is None


class TestNoServerInQuery:
    """Test empty query response."""

    @pytest.mark.asyncio
    async def test_no_server_logs_warning(self) -> None:
        gen = _make_generator()

        with patch.object(gen.logger, "warning") as mock_warn:
            await gen.generate({})
            mock_warn.assert_called_once()
            assert "No server found" in mock_warn.call_args[0][0]


class TestAvdCascadeTrigger:
    """Test AVD cascade trigger after server cabling."""

    @pytest.mark.asyncio
    async def test_cascade_called_after_successful_cabling(self) -> None:
        """After cabling completes, _trigger_avd_cascade must be called."""
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        leaf_iface = _make_mock_leaf_interface("leaf-eth1", "Ethernet1", leaf=mock_leaf)

        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.name.value = "Ethernet1"
        mock_server_iface.device.peer = MagicMock()
        mock_server_iface.device.display_label = "server-1"

        gen.client.filters = AsyncMock(
            side_effect=[
                [mock_leaf],  # leaf switches
                [mock_server_iface],  # server DcimInterface objects
                [leaf_iface],  # leaf InterfacePhysical objects
            ]
        )
        gen.client.get = AsyncMock(return_value=mock_server_iface)

        with patch("generators.generate_server_cabling.connect_interface_maps", new_callable=AsyncMock):
            gen._assign_vlans = AsyncMock()
            await gen.generate(data)

        gen._trigger_avd_cascade.assert_awaited_once_with("rack-1", "server-1", ["leaf-1"])

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_rack(self) -> None:
        """When server has no rack, cascade must not be called."""
        gen = _make_generator()

        data = _make_server_data(no_rack=True)

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_interfaces(self) -> None:
        """When server has no interfaces, cascade must not be called."""
        gen = _make_generator()

        data = _make_server_data(interfaces=[])

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_leaf_switches(self) -> None:
        """When no leaf switches in rack, cascade must not be called."""
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        gen.client.filters = AsyncMock(return_value=[])

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()

    @pytest.mark.asyncio
    @patch("generators.generate_server_cabling.trigger_hostvar_generation", new_callable=AsyncMock)
    @patch("generators.generate_server_cabling.set_fabric_avd_hostvars_ready", new_callable=AsyncMock)
    async def test_trigger_avd_cascade_navigates_to_fabric(
        self,
        mock_set_ready: AsyncMock,
        mock_trigger: AsyncMock,
    ) -> None:
        """_trigger_avd_cascade navigates rack→pod→fabric and triggers cascade."""
        gen = _make_generator(mock_cascade=False)

        # Build mock chain: rack.pod.peer → pod, pod.parent.peer → fabric
        mock_fabric = MagicMock()
        mock_fabric.id = "fabric-1"
        mock_fabric.name.value = "Fabric-A"

        mock_pod = MagicMock()
        mock_pod.parent.fetch = AsyncMock()
        mock_pod.parent.peer = mock_fabric

        mock_rack = MagicMock()
        mock_rack.pod.fetch = AsyncMock()
        mock_rack.pod.peer.id = "pod-1"

        gen.client.get = AsyncMock(side_effect=[mock_rack, mock_pod])

        await gen._trigger_avd_cascade("rack-1", "server-1", ["leaf-1", "leaf-2"])

        # Verify hostvars set to False
        mock_set_ready.assert_awaited_once_with(gen.client, "fabric-1", False)
        mock_trigger.assert_awaited_once_with(gen.client, node_ids=["leaf-1", "leaf-2"])

    @pytest.mark.asyncio
    @patch("generators.generate_server_cabling.trigger_hostvar_generation", new_callable=AsyncMock)
    @patch("generators.generate_server_cabling.set_fabric_avd_hostvars_ready", new_callable=AsyncMock)
    async def test_trigger_avd_cascade_skips_hostvars_without_leaf_targets(
        self,
        mock_set_ready: AsyncMock,
        mock_trigger: AsyncMock,
    ) -> None:
        """_trigger_avd_cascade marks fabric stale but skips hostvars without leaf targets."""
        gen = _make_generator(mock_cascade=False)

        mock_fabric = MagicMock()
        mock_fabric.id = "fabric-1"
        mock_fabric.name.value = "Fabric-A"

        mock_pod = MagicMock()
        mock_pod.parent.fetch = AsyncMock()
        mock_pod.parent.peer = mock_fabric

        mock_rack = MagicMock()
        mock_rack.pod.fetch = AsyncMock()
        mock_rack.pod.peer.id = "pod-1"

        gen.client.get = AsyncMock(side_effect=[mock_rack, mock_pod])

        await gen._trigger_avd_cascade("rack-1", "server-1", [])

        mock_set_ready.assert_awaited_once_with(gen.client, "fabric-1", False)
        mock_trigger.assert_not_awaited()
