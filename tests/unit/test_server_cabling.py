from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from generators.generate_server_cabling import ServerCablingGenerator
from solution_ai_dc.protocols import DcimConnector


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
        gen._trigger_avd_cascade = AsyncMock()  # type: ignore[method-assign]  # noqa: SLF001
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
        "id": iface_id,
        "name": {"value": name},
        "role": {"value": "server"},
        "status": {"value": "inactive"},
        "link": link,
        "tagged_vlan": {"edges": tagged_edges},
        "untagged_vlan": untagged_vlan or {"node": None},
        "profiles": profiles,
    }


def _make_mock_leaf(leaf_id: str = "leaf-1", hostname: str = "leaf-pod1-1-1") -> MagicMock:
    """Create a mock leaf switch."""
    leaf = MagicMock()
    leaf.id = leaf_id
    leaf.name.value = hostname
    return leaf


def _make_mock_leaf_interface(
    iface_id: str = "leaf-iface-1",
    name: str = "Ethernet1",
) -> MagicMock:
    """Create a mock leaf interface."""
    iface = MagicMock()
    iface.id = iface_id
    iface.name.value = name
    iface.save = AsyncMock()
    iface.device.display_label = "leaf-pod1-1-1"
    return iface


class TestSingleHomedCabling:
    """T008: Test single-homed server cabling (1 interface -> 1 leaf)."""

    @pytest.mark.asyncio
    async def test_single_homed_creates_one_link(self) -> None:
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1", tagged_vlan_ids=[{"id": "vlan-300", "name": {"value": "Servers"}}])
        data = _make_server_data(interfaces=[iface])

        # Mock leaf switch in rack
        mock_leaf = _make_mock_leaf()
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],  # leaf switches in rack
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],  # leaf interfaces
        ])

        # Mock interface re-fetches
        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.status = MagicMock()
        mock_server_iface.save = AsyncMock()

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.name.value = "Ethernet1"
        mock_leaf_iface.device.display_label = "leaf-pod1-1-1"
        mock_leaf_iface.status = MagicMock()
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(side_effect=[
            mock_server_iface,  # get server interface
            mock_leaf_iface,  # get leaf interface (with link include)
            mock_server_iface,  # re-fetch server interface after link
            mock_leaf_iface,  # re-fetch leaf interface after link
        ])

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        # Verify link was created with protocol class
        gen.client.create.assert_called_once()
        call_args = gen.client.create.call_args
        assert call_args.args[0] is DcimConnector
        assert call_args.kwargs["medium"] == "copper"


class TestDualHomedCabling:
    """T009: Test dual-homed server cabling (2 interfaces -> 2 different leaves)."""

    @pytest.mark.asyncio
    async def test_dual_homed_distributes_across_leaves(self) -> None:
        gen = _make_generator()

        iface1 = _make_interface("iface-1", "Ethernet1")
        iface2 = _make_interface("iface-2", "Ethernet2")
        data = _make_server_data(interfaces=[iface1, iface2])

        # Two leaf switches
        mock_leaf1 = _make_mock_leaf("leaf-1", "leaf-pod1-1-1")
        mock_leaf2 = _make_mock_leaf("leaf-2", "leaf-pod1-1-2")

        mock_leaf1_iface = _make_mock_leaf_interface("leaf1-eth1", "Ethernet1")
        mock_leaf2_iface = _make_mock_leaf_interface("leaf2-eth1", "Ethernet1")

        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf1, mock_leaf2],  # leaf switches
            [mock_leaf1_iface],  # leaf1 interfaces
            [mock_leaf2_iface],  # leaf2 interfaces
        ])

        # Mock re-fetches for _cable_interface (called twice)
        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.status = MagicMock()
        mock_server_iface.save = AsyncMock()

        mock_cable_leaf_iface = MagicMock()
        mock_cable_leaf_iface.id = "leaf-eth"
        mock_cable_leaf_iface.name.value = "Ethernet1"
        mock_cable_leaf_iface.device.display_label = "leaf-pod1-1-1"
        mock_cable_leaf_iface.status = MagicMock()
        mock_cable_leaf_iface.tagged_vlan = MagicMock()
        mock_cable_leaf_iface.tagged_vlan.set = MagicMock()
        mock_cable_leaf_iface.untagged_vlan = MagicMock()
        mock_cable_leaf_iface.untagged_vlan.set = MagicMock()
        mock_cable_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_cable_leaf_iface)

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        # Verify two links were created
        assert gen.client.create.call_count == 2


class TestVlanAssignment:
    """T010: Test VLAN assignment from server interface profiles to leaf interfaces."""

    @pytest.mark.asyncio
    async def test_tagged_vlans_copied_to_leaf(self) -> None:
        gen = _make_generator()

        tagged_vlans = [{"id": "vlan-300", "name": {"value": "Servers"}}, {"id": "vlan-400", "name": {"value": "Storage"}}]
        iface = _make_interface("iface-1", "Ethernet1", profile_tagged_vlan_ids=tagged_vlans)
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.status = MagicMock()
        mock_server_iface.save = AsyncMock()

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.name.value = "Ethernet1"
        mock_leaf_iface.device.display_label = "leaf-pod1-1-1"
        mock_leaf_iface.status = MagicMock()
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(side_effect=[
            mock_server_iface,
            mock_leaf_iface,
            mock_server_iface,
            mock_leaf_iface,
        ])

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        # Verify tagged VLANs were set on leaf interface
        mock_leaf_iface.tagged_vlan.extend.assert_called_once_with(["vlan-300", "vlan-400"])

    @pytest.mark.asyncio
    async def test_untagged_vlan_copied_to_leaf(self) -> None:
        gen = _make_generator()

        untagged = {"node": {"id": "vlan-100", "name": {"value": "MGMT"}}}
        iface = _make_interface("iface-1", "Ethernet1", profile_untagged_vlan=untagged)
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.status = MagicMock()
        mock_server_iface.save = AsyncMock()

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.name.value = "Ethernet1"
        mock_leaf_iface.device.display_label = "leaf-pod1-1-1"
        mock_leaf_iface.status = MagicMock()
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(side_effect=[
            mock_server_iface,
            mock_leaf_iface,
            mock_server_iface,
            mock_leaf_iface,
        ])

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        mock_leaf_iface.untagged_vlan.add.assert_called_once_with("vlan-100")


class TestInterfaceStatusActive:
    """T011: Test interface status set to 'active' after cabling."""

    @pytest.mark.asyncio
    async def test_interfaces_set_to_active(self) -> None:
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_server_iface = MagicMock()
        mock_server_iface.id = "iface-1"
        mock_server_iface.status = MagicMock()
        mock_server_iface.save = AsyncMock()

        mock_leaf_iface = MagicMock()
        mock_leaf_iface.id = "leaf-eth1"
        mock_leaf_iface.name.value = "Ethernet1"
        mock_leaf_iface.device.display_label = "leaf-pod1-1-1"
        mock_leaf_iface.status = MagicMock()
        mock_leaf_iface.tagged_vlan = MagicMock()
        mock_leaf_iface.tagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.tagged_vlan.extend = MagicMock()
        mock_leaf_iface.untagged_vlan = MagicMock()
        mock_leaf_iface.untagged_vlan.fetch = AsyncMock()
        mock_leaf_iface.untagged_vlan.add = MagicMock()
        mock_leaf_iface.save = AsyncMock()

        gen.client.get = AsyncMock(side_effect=[
            mock_server_iface,
            mock_leaf_iface,
            mock_server_iface,
            mock_leaf_iface,
        ])

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        # Verify both interfaces set to active
        assert mock_server_iface.status.value == "active"
        assert mock_leaf_iface.status.value == "active"


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
        # Only one available interface for two server interfaces
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_iface = MagicMock()
        mock_iface.id = "iface-1"
        mock_iface.name.value = "Ethernet1"
        mock_iface.device.display_label = "leaf-pod1-1-1"
        mock_iface.status = MagicMock()
        mock_iface.tagged_vlan = MagicMock()
        mock_iface.tagged_vlan.fetch = AsyncMock()
        mock_iface.tagged_vlan.extend = MagicMock()
        mock_iface.untagged_vlan = MagicMock()
        mock_iface.untagged_vlan.fetch = AsyncMock()
        mock_iface.untagged_vlan.add = MagicMock()
        mock_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_iface)

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        with patch.object(gen.logger, "warning") as mock_warn:
            await gen.generate(data)
            assert any("Insufficient" in str(call) for call in mock_warn.call_args_list)

        # One link created (for the one available leaf interface)
        assert gen.client.create.call_count == 1


class TestIdempotency:
    """T014: Test idempotency - re-running upserts the same links."""

    @pytest.mark.asyncio
    async def test_rerun_upserts_same_link(self) -> None:
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        mock_leaf = _make_mock_leaf()
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_iface = MagicMock()
        mock_iface.id = "iface-1"
        mock_iface.name.value = "Ethernet1"
        mock_iface.device.display_label = "leaf-pod1-1-1"
        mock_iface.status = MagicMock()
        mock_iface.tagged_vlan = MagicMock()
        mock_iface.tagged_vlan.fetch = AsyncMock()
        mock_iface.tagged_vlan.extend = MagicMock()
        mock_iface.untagged_vlan = MagicMock()
        mock_iface.untagged_vlan.fetch = AsyncMock()
        mock_iface.untagged_vlan.add = MagicMock()
        mock_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_iface)

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        # Link created with allow_upsert
        assert gen.client.create.call_count == 1
        mock_link.save.assert_called_once_with(allow_upsert=True)


class TestSingleLeafDualHomed:
    """T015: Test single leaf with dual-homed server."""

    @pytest.mark.asyncio
    async def test_both_interfaces_connect_to_single_leaf(self) -> None:
        gen = _make_generator()

        iface1 = _make_interface("iface-1", "Ethernet1")
        iface2 = _make_interface("iface-2", "Ethernet2")
        data = _make_server_data(interfaces=[iface1, iface2])

        mock_leaf = _make_mock_leaf("leaf-1", "leaf-pod1-1-1")
        mock_leaf_iface1 = _make_mock_leaf_interface("leaf-eth1", "Ethernet1")
        mock_leaf_iface2 = _make_mock_leaf_interface("leaf-eth2", "Ethernet2")

        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],  # Single leaf
            [mock_leaf_iface1, mock_leaf_iface2],  # Two available interfaces
        ])

        mock_iface = MagicMock()
        mock_iface.id = "iface"
        mock_iface.name.value = "Ethernet1"
        mock_iface.device.display_label = "leaf-pod1-1-1"
        mock_iface.status = MagicMock()
        mock_iface.tagged_vlan = MagicMock()
        mock_iface.tagged_vlan.fetch = AsyncMock()
        mock_iface.tagged_vlan.extend = MagicMock()
        mock_iface.untagged_vlan = MagicMock()
        mock_iface.untagged_vlan.fetch = AsyncMock()
        mock_iface.untagged_vlan.add = MagicMock()
        mock_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_iface)

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        with patch.object(gen.logger, "info") as mock_info:
            await gen.generate(data)
            assert any("Only one leaf switch" in str(call) for call in mock_info.call_args_list)

        # Both interfaces connected
        assert gen.client.create.call_count == 2


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


class TestDistributeInterfaces:
    """Test the interface distribution logic."""

    def test_round_robin_with_two_leaves(self) -> None:
        gen = _make_generator()

        server_ifaces = [
            {"id": "s1", "name": "Ethernet1", "tagged_vlan_ids": [], "untagged_vlan_id": None},
            {"id": "s2", "name": "Ethernet2", "tagged_vlan_ids": [], "untagged_vlan_id": None},
        ]

        leaf1 = _make_mock_leaf("leaf-1", "leaf-1")
        leaf2 = _make_mock_leaf("leaf-2", "leaf-2")

        available = [
            {"id": "l1-e1", "leaf_id": "leaf-1", "leaf_hostname": "leaf-1", "name": "Ethernet1"},
            {"id": "l2-e1", "leaf_id": "leaf-2", "leaf_hostname": "leaf-2", "name": "Ethernet1"},
        ]

        pairings = gen._distribute_interfaces(server_ifaces, available, [leaf1, leaf2])  # noqa: SLF001

        assert len(pairings) == 2
        # First server iface goes to leaf-1, second to leaf-2
        assert pairings[0][1] == "l1-e1"
        assert pairings[1][1] == "l2-e1"

    def test_single_leaf_sequential(self) -> None:
        gen = _make_generator()

        server_ifaces = [
            {"id": "s1", "name": "Ethernet1", "tagged_vlan_ids": [], "untagged_vlan_id": None},
            {"id": "s2", "name": "Ethernet2", "tagged_vlan_ids": [], "untagged_vlan_id": None},
        ]

        leaf1 = _make_mock_leaf("leaf-1", "leaf-1")

        available = [
            {"id": "l1-e1", "leaf_id": "leaf-1", "leaf_hostname": "leaf-1", "name": "Ethernet1"},
            {"id": "l1-e2", "leaf_id": "leaf-1", "leaf_hostname": "leaf-1", "name": "Ethernet2"},
        ]

        pairings = gen._distribute_interfaces(server_ifaces, available, [leaf1])  # noqa: SLF001

        assert len(pairings) == 2
        assert pairings[0][1] == "l1-e1"
        assert pairings[1][1] == "l1-e2"


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

        result = gen._extract_vlans(interface_node)  # noqa: SLF001
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

        result = gen._extract_vlans(interface_node)  # noqa: SLF001
        assert result["tagged"] == ["vlan-300", "vlan-400"]

    def test_merges_vlans_from_interface_and_profile(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {
                "edges": [{"node": {"id": "vlan-300", "name": {"value": "Servers"}}}]
            },
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

        result = gen._extract_vlans(interface_node)  # noqa: SLF001
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

        result = gen._extract_vlans(interface_node)  # noqa: SLF001
        assert result["untagged"] == "vlan-100"

    def test_no_vlans_returns_empty(self) -> None:
        gen = _make_generator()

        interface_node = {
            "tagged_vlan": {"edges": []},
            "untagged_vlan": {"node": None},
            "profiles": {"edges": []},
        }

        result = gen._extract_vlans(interface_node)  # noqa: SLF001
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
        gen.client.filters = AsyncMock(side_effect=[
            [mock_leaf],
            [_make_mock_leaf_interface("leaf-eth1", "Ethernet1")],
        ])

        mock_iface = MagicMock()
        mock_iface.id = "iface-1"
        mock_iface.name.value = "Ethernet1"
        mock_iface.device.display_label = "leaf-pod1-1-1"
        mock_iface.status = MagicMock()
        mock_iface.tagged_vlan = MagicMock()
        mock_iface.tagged_vlan.fetch = AsyncMock()
        mock_iface.tagged_vlan.extend = MagicMock()
        mock_iface.untagged_vlan = MagicMock()
        mock_iface.untagged_vlan.fetch = AsyncMock()
        mock_iface.untagged_vlan.add = MagicMock()
        mock_iface.save = AsyncMock()

        gen.client.get = AsyncMock(return_value=mock_iface)

        mock_link = MagicMock()
        mock_link.save = AsyncMock()
        gen.client.create = AsyncMock(return_value=mock_link)

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_awaited_once_with("rack-1", "server-1")  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_rack(self) -> None:
        """When server has no rack, cascade must not be called."""
        gen = _make_generator()

        data = _make_server_data(no_rack=True)

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_interfaces(self) -> None:
        """When server has no interfaces, cascade must not be called."""
        gen = _make_generator()

        data = _make_server_data(interfaces=[])

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()  # noqa: SLF001

    @pytest.mark.asyncio
    async def test_cascade_not_called_when_no_leaf_switches(self) -> None:
        """When no leaf switches in rack, cascade must not be called."""
        gen = _make_generator()

        iface = _make_interface("iface-1", "Ethernet1")
        data = _make_server_data(interfaces=[iface])

        gen.client.filters = AsyncMock(return_value=[])

        await gen.generate(data)

        gen._trigger_avd_cascade.assert_not_awaited()  # noqa: SLF001

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

        await gen._trigger_avd_cascade("rack-1", "server-1")  # noqa: SLF001

        # Verify hostvars set to False and hostvar generation triggered
        mock_set_ready.assert_awaited_once_with(gen.client, "fabric-1", False)
        mock_trigger.assert_awaited_once_with(gen.client)
