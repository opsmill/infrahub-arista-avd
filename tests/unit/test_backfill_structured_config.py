# ruff: noqa: SLF001
"""Unit tests for backfill structured config generator."""

import ipaddress
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from infrahub_sdk.exceptions import NodeNotFoundError

from generators.backfill_structured_config import (
    INTERFACE_SECTIONS,
    ROUTING_SECTIONS,
    UNMODELED_SECTIONS,
    BackfillStructuredConfigGenerator,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQuery,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNode as InterfaceNode,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddress as IpAddress,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNode as IpAddressNode,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeIpAddressNodeAddress as IpAddressNodeAddress,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeMtu as Mtu,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeName as Name,
)
from generators.backfill_structured_config_query import (
    BackfillStructuredConfigQueryAvdArtifactEdgesNodeDeviceNodeInterfacesEdgesNodeRole as Role,
)
from solution_ai_dc.protocols import (
    CoreAccountGroup,
    IpamIPAddress,
    IpamPrefix,
    RoutingBGPNeighbor,
    RoutingBGPPeerGroup,
    RoutingPrefixList,
    RoutingPrefixListEntry,
    RoutingRouteMap,
    RoutingRouteMapEntry,
    RoutingStaticRoute,
)


def _make_interface(
    iface_id: str = "iface-1",
    name: str | None = "Ethernet1",
    role: str | None = "uplink",
    mtu: int | None = None,
    ip_node: IpAddressNode | None = None,
) -> InterfaceNode:
    """Helper to build an InterfaceNode for tests."""
    return InterfaceNode(
        __typename="InterfacePhysical",
        id=iface_id,
        name=Name(value=name) if name else None,
        role=Role(value=role) if role else None,
        mtu=Mtu(value=mtu) if mtu is not None else None,
        ip_address=IpAddress(node=ip_node),
    )


def _make_ip_node(address: str, ip_id: str = "ip-1") -> IpAddressNode:
    return IpAddressNode(id=ip_id, address=IpAddressNodeAddress(value=address))


def _make_generator() -> BackfillStructuredConfigGenerator:
    """Create a generator instance with a mocked client."""
    gen = BackfillStructuredConfigGenerator.__new__(BackfillStructuredConfigGenerator)
    gen.client = AsyncMock()
    gen.client.filters = AsyncMock(return_value=[])
    return gen


def _make_saveable_mock() -> MagicMock:
    """Create a MagicMock with an async save method."""
    mock = MagicMock()
    mock.save = AsyncMock()
    return mock


def _build_artifact_query_data(
    hostname: str = "leaf-1",
    identifier: str | None = "sc-id-123",
    interfaces: list | None = None,
    device_node: bool = True,
) -> dict:
    """Build a raw query data dict matching the AvdArtifact-rooted query shape."""
    device = None
    if device_node:
        device = {
            "__typename": "DcimDevice",
            "id": "dev-1",
            "name": {"value": hostname},
            "role": {"value": "leaf"},
            "interfaces": {"edges": interfaces or []},
        }

    return {
        "AvdArtifact": {
            "edges": [
                {
                    "node": {
                        "id": "art-1",
                        "structured_config_identifier": {"value": identifier},
                        "device": {"node": device},
                    }
                }
            ]
        }
    }


# --- Query model parsing ---


class TestQueryModelParsing:
    def test_parse_minimal_query_data(self) -> None:
        """Test parsing a minimal GraphQL response into the Pydantic model."""
        raw = _build_artifact_query_data()
        data = BackfillStructuredConfigQuery(**raw)
        artifact = data.avd_artifact.edges[0].node

        assert artifact.id == "art-1"
        assert artifact.structured_config_identifier.value == "sc-id-123"
        device = artifact.device.node
        assert device.id == "dev-1"
        assert device.name.value == "leaf-1"
        assert device.role.value == "leaf"
        assert device.interfaces.edges == []

    def test_parse_with_no_identifier(self) -> None:
        """Test parsing when structured_config_identifier is None."""
        raw = _build_artifact_query_data(identifier=None)
        data = BackfillStructuredConfigQuery(**raw)
        assert data.avd_artifact.edges[0].node.structured_config_identifier.value is None

    def test_parse_with_no_device(self) -> None:
        """Test parsing when device node is None."""
        raw = _build_artifact_query_data(device_node=False)
        data = BackfillStructuredConfigQuery(**raw)
        assert data.avd_artifact.edges[0].node.device.node is None

    def test_parse_interface_with_ip(self) -> None:
        """Test parsing an interface that has an IP address assigned."""
        interfaces = [
            {
                "node": {
                    "__typename": "InterfacePhysical",
                    "id": "iface-1",
                    "name": {"value": "Ethernet1"},
                    "role": {"value": "uplink"},
                    "mtu": {"value": 9214},
                    "ip_address": {
                        "node": {
                            "id": "ip-1",
                            "address": {"value": "10.0.0.1/31"},
                        }
                    },
                }
            }
        ]
        raw = _build_artifact_query_data(interfaces=interfaces)
        data = BackfillStructuredConfigQuery(**raw)
        iface = data.avd_artifact.edges[0].node.device.node.interfaces.edges[0].node

        assert iface.name.value == "Ethernet1"
        assert iface.mtu.value == 9214
        assert iface.ip_address.node.address.value == "10.0.0.1/31"


# --- Interface map building ---


class TestBuildInterfaceMap:
    def test_basic_map(self) -> None:
        """Test building interface map from a list of interfaces."""
        gen = _make_generator()
        interfaces = [
            _make_interface(iface_id="1", name="Ethernet1"),
            _make_interface(iface_id="2", name="Ethernet2"),
            _make_interface(iface_id="3", name="Loopback0"),
        ]

        result = gen._build_interface_map(interfaces)

        assert len(result) == 3
        assert result["Ethernet1"].id == "1"
        assert result["Ethernet2"].id == "2"
        assert result["Loopback0"].id == "3"

    def test_skips_none_name(self) -> None:
        """Test that interfaces with no name are excluded."""
        gen = _make_generator()
        interfaces = [
            _make_interface(iface_id="1", name="Ethernet1"),
            _make_interface(iface_id="2", name=None),
        ]

        result = gen._build_interface_map(interfaces)

        assert len(result) == 1
        assert "Ethernet1" in result

    def test_empty_list(self) -> None:
        """Test with an empty list."""
        gen = _make_generator()
        assert gen._build_interface_map([]) == {}

    def test_duplicate_names_last_wins(self) -> None:
        """Test that duplicate names result in last-wins behavior."""
        gen = _make_generator()
        interfaces = [
            _make_interface(iface_id="1", name="Ethernet1"),
            _make_interface(iface_id="2", name="Ethernet1"),
        ]

        result = gen._build_interface_map(interfaces)

        assert len(result) == 1
        assert result["Ethernet1"].id == "2"


# --- IP parsing and prefix derivation ---


class TestIpParsing:
    @pytest.mark.parametrize(
        "ip_str,expected_prefix",
        [
            ("10.0.0.1/31", "10.0.0.0/31"),
            ("10.0.0.0/31", "10.0.0.0/31"),
            ("192.168.1.1/24", "192.168.1.0/24"),
            ("10.255.0.1/32", "10.255.0.1/32"),
            ("172.16.0.5/30", "172.16.0.4/30"),
        ],
    )
    def test_network_prefix_derivation(self, ip_str: str, expected_prefix: str) -> None:
        """Test that ip_interface correctly derives the network prefix."""
        ip_iface = ipaddress.ip_interface(ip_str)
        assert str(ip_iface.network) == expected_prefix

    def test_invalid_ip_raises_valueerror(self) -> None:
        """Test that invalid IP strings raise ValueError."""
        with pytest.raises(ValueError):
            ipaddress.ip_interface("not-an-ip")

    def test_shared_p2p_prefix(self) -> None:
        """Test that both ends of a /31 p2p link derive the same prefix."""
        a = ipaddress.ip_interface("10.0.0.0/31")
        b = ipaddress.ip_interface("10.0.0.1/31")
        assert str(a.network) == str(b.network) == "10.0.0.0/31"


# --- Gap-fill detection ---


class TestGapFillDetection:
    def test_interface_without_ip_needs_backfill(self) -> None:
        """An interface with no IP should be eligible for backfill."""
        iface = _make_interface(ip_node=None)
        assert iface.ip_address.node is None

    def test_interface_with_ip_skips_backfill(self) -> None:
        """An interface with an existing IP should not be backfilled."""
        ip_node = _make_ip_node("10.0.0.1/31")
        iface = _make_interface(ip_node=ip_node)
        assert iface.ip_address.node is not None


# --- MTU skip logic ---


class TestMtuSkipLogic:
    def test_same_mtu_is_noop(self) -> None:
        """When current MTU matches structured config MTU, no update needed."""
        iface = _make_interface(mtu=9214)
        current_mtu = iface.mtu.value
        assert current_mtu == 9214

    def test_different_mtu_needs_update(self) -> None:
        """When MTU differs, update is needed."""
        iface = _make_interface(mtu=1500)
        assert iface.mtu.value != 9214

    def test_no_mtu_needs_update(self) -> None:
        """When interface has no MTU set, update is needed."""
        iface = _make_interface(mtu=None)
        current_mtu = iface.mtu.value if iface.mtu else None
        assert current_mtu is None
        assert current_mtu != 9214


# --- _extract_optional helper ---


class TestExtractOptional:
    def test_extracts_present_keys(self) -> None:
        """Test that present keys are extracted."""
        config = {"type": "ipv4", "remote_as": 65000, "bfd": True}
        result = BackfillStructuredConfigGenerator._extract_optional(config, ["type", "remote_as", "bfd"])
        assert result == {"type": "ipv4", "remote_as": 65000, "bfd": True}

    def test_skips_none_keys(self) -> None:
        """Test that None values are skipped."""
        config = {"type": None, "remote_as": 65000}
        result = BackfillStructuredConfigGenerator._extract_optional(config, ["type", "remote_as"])
        assert result == {"remote_as": 65000}

    def test_skips_missing_keys(self) -> None:
        """Test that missing keys are skipped."""
        config = {"type": "ipv4"}
        result = BackfillStructuredConfigGenerator._extract_optional(config, ["type", "remote_as"])
        assert result == {"type": "ipv4"}

    def test_stringify_keys(self) -> None:
        """Test that stringify keys are converted to strings."""
        config = {"remote_as": 65000, "local_as": 65001}
        result = BackfillStructuredConfigGenerator._extract_optional(
            config, ["remote_as", "local_as"], stringify=["remote_as", "local_as"]
        )
        assert result == {"remote_as": "65000", "local_as": "65001"}

    def test_skips_empty_string(self) -> None:
        """Test that empty strings are skipped."""
        config = {"description": ""}
        result = BackfillStructuredConfigGenerator._extract_optional(config, ["description"])
        assert result == {}

    def test_preserves_false_and_zero(self) -> None:
        """Test that False and 0 are preserved (not skipped as falsy)."""
        config = {"bfd": False, "ebgp_multihop": 0}
        result = BackfillStructuredConfigGenerator._extract_optional(config, ["bfd", "ebgp_multihop"])
        assert result == {"bfd": False, "ebgp_multihop": 0}


# --- Async methods with mocked client ---


class TestBackfillIp:
    async def test_backfill_creates_prefix_ip_and_assigns(self) -> None:
        """Test that _backfill_ip creates prefix, IP, and assigns to interface."""
        gen = _make_generator()
        mock_prefix = _make_saveable_mock()
        mock_ip = _make_saveable_mock()
        mock_interface = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Ethernet1", ip_node=None)
        await gen._backfill_ip(iface, "10.0.0.1/31", "leaf-1")

        # Verify prefix creation
        gen.client.create.assert_any_call(
            IpamPrefix,
            prefix="10.0.0.0/31",
            role="backfill",
        )
        mock_prefix.save.assert_awaited_once_with(allow_upsert=True)

        # Verify IP creation
        gen.client.create.assert_any_call(
            IpamIPAddress,
            address="10.0.0.1/31",
            ip_prefix=mock_prefix,
        )
        mock_ip.save.assert_awaited_once_with(allow_upsert=True)

        # Verify interface assignment
        gen.client.get.assert_awaited_once()
        assert mock_interface.ip_address == mock_ip
        mock_interface.save.assert_awaited_once_with(allow_upsert=True)

    async def test_backfill_skips_invalid_ip(self) -> None:
        """Test that invalid IP format is skipped without error."""
        gen = _make_generator()
        iface = _make_interface(name="Ethernet1", ip_node=None)

        await gen._backfill_ip(iface, "not-an-ip", "leaf-1")

        gen.client.create.assert_not_called()

    async def test_backfill_loopback_ip(self) -> None:
        """Test backfill with a /32 loopback address."""
        gen = _make_generator()
        mock_prefix = _make_saveable_mock()
        mock_ip = _make_saveable_mock()
        mock_interface = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Loopback0", ip_node=None)
        await gen._backfill_ip(iface, "10.255.0.1/32", "leaf-1")

        gen.client.create.assert_any_call(
            IpamPrefix,
            prefix="10.255.0.1/32",
            role="backfill",
        )


class TestUpdateMtu:
    async def test_update_mtu_when_different(self) -> None:
        """Test that MTU is updated when it differs from current."""
        gen = _make_generator()
        mock_interface = _make_saveable_mock()
        mock_interface.mtu = MagicMock()
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(mtu=1500)
        await gen._update_mtu(iface, 9214, "leaf-1")

        gen.client.get.assert_awaited_once()
        assert mock_interface.mtu.value == 9214
        mock_interface.save.assert_awaited_once_with(allow_upsert=True)

    async def test_upserts_mtu_when_same(self) -> None:
        """Test that MTU is always saved even when current equals target."""
        gen = _make_generator()
        mock_interface = _make_saveable_mock()
        mock_interface.mtu = MagicMock(value=9214)
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(mtu=9214)
        await gen._update_mtu(iface, 9214, "leaf-1")

        gen.client.get.assert_awaited_once()
        mock_interface.save.assert_awaited_once_with(allow_upsert=True)


# --- BGP backfill ---


class TestBackfillBgpPeerGroups:
    async def test_creates_peer_group(self) -> None:
        """Test that a BGP peer group is created from structured config."""
        gen = _make_generator()
        mock_pg = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_pg)

        bgp_config = {
            "peer_groups": [
                {
                    "name": "IPv4-UNDERLAY-PEERS",
                    "type": "ipv4",
                    "remote_as": "65000",
                    "send_community": "all",
                    "maximum_routes": 12000,
                }
            ]
        }
        result = await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1")

        gen.client.create.assert_called_once_with(
            RoutingBGPPeerGroup,
            name="IPv4-UNDERLAY-PEERS",
            device="dev-1",
            type="ipv4",
            remote_as="65000",
            send_community="all",
            maximum_routes=12000,
        )
        mock_pg.save.assert_awaited_once_with(allow_upsert=True)
        assert "IPv4-UNDERLAY-PEERS" in result

    async def test_creates_evpn_peer_group_with_bfd(self) -> None:
        """Test peer group with BFD and multihop settings."""
        gen = _make_generator()
        mock_pg = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_pg)

        bgp_config = {
            "peer_groups": [
                {
                    "name": "EVPN-OVERLAY-PEERS",
                    "type": "evpn",
                    "remote_as": "65000",
                    "bfd": True,
                    "ebgp_multihop": 3,
                    "update_source": "Loopback0",
                }
            ]
        }
        result = await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1")

        gen.client.create.assert_called_once_with(
            RoutingBGPPeerGroup,
            name="EVPN-OVERLAY-PEERS",
            device="dev-1",
            type="evpn",
            remote_as="65000",
            bfd=True,
            ebgp_multihop=3,
            update_source="Loopback0",
        )
        assert "EVPN-OVERLAY-PEERS" in result

    async def test_skips_peer_group_without_name(self) -> None:
        """Test that peer groups without name are skipped."""
        gen = _make_generator()
        bgp_config = {"peer_groups": [{"type": "ipv4"}]}
        result = await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1")

        gen.client.create.assert_not_called()
        assert result == {}

    async def test_empty_peer_groups(self) -> None:
        """Test with no peer_groups key."""
        gen = _make_generator()
        bgp_config = {}
        result = await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1")

        gen.client.create.assert_not_called()
        assert result == {}

    async def test_peer_group_integer_as_stringified(self) -> None:
        """Test that integer remote_as is converted to string."""
        gen = _make_generator()
        mock_pg = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_pg)

        bgp_config = {"peer_groups": [{"name": "PG1", "remote_as": 65000}]}
        await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1")

        gen.client.create.assert_called_once()
        call_kwargs = gen.client.create.call_args.kwargs
        assert call_kwargs["remote_as"] == "65000"


class TestBackfillBgpNeighbors:
    async def test_creates_neighbor_with_peer_group(self) -> None:
        """Test that a BGP neighbor is created and linked to peer group."""
        gen = _make_generator()
        mock_nb = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_nb)

        mock_pg = _make_saveable_mock()
        peer_group_map = {"IPv4-UNDERLAY-PEERS": mock_pg}

        bgp_config = {
            "neighbors": [
                {
                    "ip_address": "172.31.255.0",
                    "peer_group": "IPv4-UNDERLAY-PEERS",
                    "remote_as": "65000",
                    "description": "spine-1_Ethernet1",
                }
            ]
        }
        await gen._backfill_bgp_neighbors(bgp_config, "dev-1", "leaf-1", peer_group_map)

        gen.client.create.assert_called_once_with(
            RoutingBGPNeighbor,
            peer_address="172.31.255.0",
            device="dev-1",
            remote_as="65000",
            description="spine-1_Ethernet1",
            peer_group=mock_pg,
        )
        mock_nb.save.assert_awaited_once_with(allow_upsert=True)

    async def test_creates_neighbor_without_peer_group(self) -> None:
        """Test neighbor creation when peer_group is not in map."""
        gen = _make_generator()
        mock_nb = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_nb)

        bgp_config = {
            "neighbors": [
                {
                    "ip_address": "10.0.0.1",
                    "peer_group": "UNKNOWN-PG",
                    "remote_as": "65001",
                }
            ]
        }
        await gen._backfill_bgp_neighbors(bgp_config, "dev-1", "leaf-1", {})

        gen.client.create.assert_called_once()
        call_kwargs = gen.client.create.call_args.kwargs
        assert "peer_group" not in call_kwargs

    async def test_skips_neighbor_without_ip(self) -> None:
        """Test that neighbors without ip_address are skipped."""
        gen = _make_generator()
        bgp_config = {"neighbors": [{"peer_group": "PG1"}]}
        await gen._backfill_bgp_neighbors(bgp_config, "dev-1", "leaf-1", {})

        gen.client.create.assert_not_called()

    async def test_creates_multiple_neighbors(self) -> None:
        """Test creating multiple BGP neighbors."""
        gen = _make_generator()
        mock_nb = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_nb)

        bgp_config = {
            "neighbors": [
                {"ip_address": "172.31.255.0", "remote_as": "65000"},
                {"ip_address": "172.31.255.2", "remote_as": "65000"},
            ]
        }
        await gen._backfill_bgp_neighbors(bgp_config, "dev-1", "leaf-1", {})

        assert gen.client.create.call_count == 2


class TestBackfillBgp:
    async def test_full_bgp_backfill(self) -> None:
        """Test that _backfill_bgp processes both peer groups and neighbors."""
        gen = _make_generator()
        mock_pg = _make_saveable_mock()
        mock_nb = _make_saveable_mock()
        gen.client.create = AsyncMock(side_effect=[mock_pg, mock_nb])

        bgp_config = {
            "peer_groups": [{"name": "PG1", "type": "ipv4", "remote_as": "65000"}],
            "neighbors": [{"ip_address": "10.0.0.1", "peer_group": "PG1"}],
        }
        await gen._backfill_bgp(bgp_config, "dev-1", "leaf-1")

        assert gen.client.create.call_count == 2
        # Verify peer group was created first
        first_call = gen.client.create.call_args_list[0]
        assert first_call.args[0] is RoutingBGPPeerGroup
        # Verify neighbor was created second
        second_call = gen.client.create.call_args_list[1]
        assert second_call.args[0] is RoutingBGPNeighbor


# --- Prefix list backfill ---


class TestBackfillPrefixLists:
    async def test_creates_prefix_list_with_entries(self) -> None:
        """Test creating a prefix list and its entries."""
        gen = _make_generator()
        mock_pl = _make_saveable_mock()
        mock_entry = _make_saveable_mock()
        gen.client.create = AsyncMock(side_effect=[mock_pl, mock_entry])

        prefix_lists = [
            {
                "name": "PL-LOOPBACKS-EVPN-OVERLAY",
                "sequence_numbers": [
                    {"sequence": 10, "action": "permit 10.255.0.0/27 eq 32"},
                ],
            }
        ]
        await gen._backfill_prefix_lists(prefix_lists, "dev-1", "leaf-1")

        assert gen.client.create.call_count == 2
        gen.client.create.assert_any_call(
            RoutingPrefixList,
            name="PL-LOOPBACKS-EVPN-OVERLAY",
            device="dev-1",
        )
        gen.client.create.assert_any_call(
            RoutingPrefixListEntry,
            sequence=10,
            action="permit 10.255.0.0/27 eq 32",
            prefix_list=mock_pl,
        )

    async def test_creates_prefix_list_with_multiple_entries(self) -> None:
        """Test prefix list with multiple sequence entries."""
        gen = _make_generator()
        mock_pl = _make_saveable_mock()
        mock_e1 = _make_saveable_mock()
        mock_e2 = _make_saveable_mock()
        gen.client.create = AsyncMock(side_effect=[mock_pl, mock_e1, mock_e2])

        prefix_lists = [
            {
                "name": "PL-TEST",
                "sequence_numbers": [
                    {"sequence": 10, "action": "permit 10.0.0.0/8 le 24"},
                    {"sequence": 20, "action": "deny 0.0.0.0/0 le 32"},
                ],
            }
        ]
        await gen._backfill_prefix_lists(prefix_lists, "dev-1", "leaf-1")

        assert gen.client.create.call_count == 3

    async def test_skips_prefix_list_without_name(self) -> None:
        """Test that prefix lists without name are skipped."""
        gen = _make_generator()
        prefix_lists = [{"sequence_numbers": [{"sequence": 10, "action": "permit any"}]}]
        await gen._backfill_prefix_lists(prefix_lists, "dev-1", "leaf-1")

        gen.client.create.assert_not_called()

    async def test_skips_entry_without_sequence(self) -> None:
        """Test that entries without sequence number are skipped."""
        gen = _make_generator()
        mock_pl = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_pl)

        prefix_lists = [
            {
                "name": "PL-TEST",
                "sequence_numbers": [{"action": "permit any"}],
            }
        ]
        await gen._backfill_prefix_lists(prefix_lists, "dev-1", "leaf-1")

        # Only the prefix list itself, no entries
        gen.client.create.assert_called_once()

    async def test_empty_prefix_lists(self) -> None:
        """Test with empty list."""
        gen = _make_generator()
        await gen._backfill_prefix_lists([], "dev-1", "leaf-1")
        gen.client.create.assert_not_called()


# --- Route map backfill ---


class TestBackfillRouteMaps:
    async def test_creates_route_map_with_entry(self) -> None:
        """Test creating a route map with a sequence entry."""
        gen = _make_generator()
        mock_rm = _make_saveable_mock()
        mock_entry = _make_saveable_mock()
        gen.client.create = AsyncMock(side_effect=[mock_rm, mock_entry])

        route_maps = [
            {
                "name": "RM-CONN-2-BGP",
                "sequence_numbers": [
                    {
                        "sequence": 10,
                        "type": "permit",
                        "match": ["ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY"],
                    },
                ],
            }
        ]
        await gen._backfill_route_maps(route_maps, "dev-1", "leaf-1")

        assert gen.client.create.call_count == 2
        gen.client.create.assert_any_call(
            RoutingRouteMap,
            name="RM-CONN-2-BGP",
            device="dev-1",
        )
        gen.client.create.assert_any_call(
            RoutingRouteMapEntry,
            sequence=10,
            type="permit",
            route_map=mock_rm,
            match=["ip address prefix-list PL-LOOPBACKS-EVPN-OVERLAY"],
        )

    async def test_creates_route_map_entry_with_set(self) -> None:
        """Test route map entry with set actions."""
        gen = _make_generator()
        mock_rm = _make_saveable_mock()
        mock_entry = _make_saveable_mock()
        gen.client.create = AsyncMock(side_effect=[mock_rm, mock_entry])

        route_maps = [
            {
                "name": "RM-SET-COMMUNITY",
                "sequence_numbers": [
                    {
                        "sequence": 10,
                        "type": "permit",
                        "description": "Set community",
                        "match": ["community COMM-LIST"],
                        "set": ["community 65000:100", "local-preference 200"],
                    },
                ],
            }
        ]
        await gen._backfill_route_maps(route_maps, "dev-1", "leaf-1")

        entry_call = gen.client.create.call_args_list[1]
        assert entry_call.kwargs["description"] == "Set community"
        assert entry_call.kwargs["set"] == ["community 65000:100", "local-preference 200"]

    async def test_skips_route_map_without_name(self) -> None:
        """Test that route maps without name are skipped."""
        gen = _make_generator()
        route_maps = [{"sequence_numbers": [{"sequence": 10, "type": "permit"}]}]
        await gen._backfill_route_maps(route_maps, "dev-1", "leaf-1")

        gen.client.create.assert_not_called()

    async def test_skips_entry_without_type(self) -> None:
        """Test that entries without type are skipped."""
        gen = _make_generator()
        mock_rm = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_rm)

        route_maps = [{"name": "RM-TEST", "sequence_numbers": [{"sequence": 10}]}]
        await gen._backfill_route_maps(route_maps, "dev-1", "leaf-1")

        # Only the route map itself, no entries
        gen.client.create.assert_called_once()


# --- Static route backfill ---


class TestBackfillStaticRoutes:
    async def test_creates_static_route_with_gateway(self) -> None:
        """Test creating a static route with gateway."""
        gen = _make_generator()
        mock_route = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [
            {
                "destination_address_prefix": "0.0.0.0/0",
                "gateway": "192.168.0.1",
                "vrf": "MGMT",
            }
        ]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        gen.client.create.assert_called_once_with(
            RoutingStaticRoute,
            prefix="0.0.0.0/0",
            device="dev-1",
            gateway="192.168.0.1",
            vrf="MGMT",
        )
        mock_route.save.assert_awaited_once_with(allow_upsert=True)

    async def test_uses_prefix_field_as_fallback(self) -> None:
        """Test that prefix field is used when destination_address_prefix is absent."""
        gen = _make_generator()
        mock_route = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [{"prefix": "10.0.0.0/24", "next_hop": "192.168.1.1"}]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        gen.client.create.assert_called_once()
        call_kwargs = gen.client.create.call_args.kwargs
        assert call_kwargs["prefix"] == "10.0.0.0/24"
        assert call_kwargs["next_hop"] == "192.168.1.1"

    async def test_defaults_vrf_to_default(self) -> None:
        """Test that VRF defaults to 'default' when not specified."""
        gen = _make_generator()
        mock_route = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [{"destination_address_prefix": "10.0.0.0/24", "gateway": "1.1.1.1"}]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        call_kwargs = gen.client.create.call_args.kwargs
        assert call_kwargs["vrf"] == "default"

    async def test_includes_optional_fields(self) -> None:
        """Test that optional fields like distance, tag, name are included."""
        gen = _make_generator()
        mock_route = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [
            {
                "destination_address_prefix": "10.0.0.0/24",
                "gateway": "1.1.1.1",
                "distance": 10,
                "tag": 100,
                "name": "Route to DC2",
                "interface": "Ethernet1",
            }
        ]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        call_kwargs = gen.client.create.call_args.kwargs
        assert call_kwargs["distance"] == 10
        assert call_kwargs["tag"] == 100
        assert call_kwargs["route_name"] == "Route to DC2"
        assert call_kwargs["interface"] == "Ethernet1"

    async def test_skips_route_without_prefix(self) -> None:
        """Test that routes without prefix or destination_address_prefix are skipped."""
        gen = _make_generator()
        static_routes = [{"gateway": "1.1.1.1", "vrf": "MGMT"}]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        gen.client.create.assert_not_called()

    async def test_creates_multiple_static_routes(self) -> None:
        """Test creating multiple static routes."""
        gen = _make_generator()
        mock_route = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [
            {"destination_address_prefix": "0.0.0.0/0", "gateway": "192.168.0.1", "vrf": "MGMT"},
            {"destination_address_prefix": "10.0.0.0/8", "gateway": "172.16.0.1"},
        ]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1")

        assert gen.client.create.call_count == 2


# --- Generate method ---


class TestGenerate:
    async def test_early_return_no_identifier(self) -> None:
        """Test that generate returns early when identifier is empty."""
        gen = _make_generator()
        data = _build_artifact_query_data(identifier=None)
        await gen.generate(data)

        gen.client.object_store.get.assert_not_called()

    async def test_early_return_no_device(self) -> None:
        """Test that generate returns early when no device is linked."""
        gen = _make_generator()
        data = _build_artifact_query_data(device_node=False)
        await gen.generate(data)

        gen.client.object_store.get.assert_not_called()

    async def test_processes_ethernet_interfaces(self) -> None:
        """Test that generate processes ethernet_interfaces from structured config."""
        gen = _make_generator()

        structured_config = {
            "ethernet_interfaces": [
                {"name": "Ethernet1", "ip_address": "10.0.0.1/31", "mtu": 9214},
            ]
        }
        gen.client.object_store.get = AsyncMock(return_value=json.dumps(structured_config))

        mock_prefix = _make_saveable_mock()
        mock_ip = _make_saveable_mock()
        mock_avd_group = MagicMock()
        mock_avd_group.id = "avd-group-id"
        mock_interface = _make_saveable_mock()
        mock_interface_mtu = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(side_effect=[mock_avd_group, mock_interface, mock_interface_mtu])

        interfaces = [
            {
                "node": {
                    "__typename": "InterfacePhysical",
                    "id": "iface-1",
                    "name": {"value": "Ethernet1"},
                    "role": {"value": "uplink"},
                    "mtu": {"value": 1500},
                    "ip_address": {"node": None},
                }
            }
        ]
        data = _build_artifact_query_data(interfaces=interfaces)
        await gen.generate(data)

        # Should have created prefix and IP
        assert gen.client.create.call_count == 2

    async def test_upserts_interface_with_existing_ip(self) -> None:
        """Test that interfaces with existing IPs are still upserted."""
        gen = _make_generator()

        structured_config = {
            "ethernet_interfaces": [
                {"name": "Ethernet1", "ip_address": "10.0.0.1/31"},
            ]
        }
        gen.client.object_store.get = AsyncMock(return_value=json.dumps(structured_config))

        interfaces = [
            {
                "node": {
                    "__typename": "InterfacePhysical",
                    "id": "iface-1",
                    "name": {"value": "Ethernet1"},
                    "role": {"value": "uplink"},
                    "mtu": None,
                    "ip_address": {
                        "node": {
                            "id": "ip-1",
                            "address": {"value": "10.0.0.1/31"},
                        }
                    },
                }
            }
        ]
        data = _build_artifact_query_data(interfaces=interfaces)
        await gen.generate(data)

        # Should create prefix and IP even though interface already has one
        assert gen.client.create.call_count == 2

    async def test_skips_unmatched_interface(self) -> None:
        """Test that structured config interfaces not in data model are skipped."""
        gen = _make_generator()

        structured_config = {
            "ethernet_interfaces": [
                {"name": "Ethernet99", "ip_address": "10.0.0.1/31"},
            ]
        }
        gen.client.object_store.get = AsyncMock(return_value=json.dumps(structured_config))

        interfaces = [
            {
                "node": {
                    "__typename": "InterfacePhysical",
                    "id": "iface-1",
                    "name": {"value": "Ethernet1"},
                    "role": {"value": "uplink"},
                    "mtu": None,
                    "ip_address": {"node": None},
                }
            }
        ]
        data = _build_artifact_query_data(interfaces=interfaces)
        await gen.generate(data)

        gen.client.create.assert_not_called()

    async def test_processes_routing_sections(self) -> None:
        """Test that generate processes BGP, prefix lists, route maps, and static routes."""
        gen = _make_generator()

        structured_config = {
            "router_bgp": {
                "as": 65001,
                "peer_groups": [{"name": "PG1", "type": "ipv4"}],
                "neighbors": [{"ip_address": "10.0.0.1", "peer_group": "PG1"}],
            },
            "prefix_lists": [
                {"name": "PL1", "sequence_numbers": [{"sequence": 10, "action": "permit any"}]},
            ],
            "route_maps": [
                {"name": "RM1", "sequence_numbers": [{"sequence": 10, "type": "permit"}]},
            ],
            "static_routes": [
                {"destination_address_prefix": "0.0.0.0/0", "gateway": "1.1.1.1"},
            ],
        }
        gen.client.object_store.get = AsyncMock(return_value=json.dumps(structured_config))
        mock_obj = _make_saveable_mock()
        gen.client.create = AsyncMock(return_value=mock_obj)

        data = _build_artifact_query_data()
        await gen.generate(data)

        # Verify all routing protocol classes were used
        created_types = [c.args[0] for c in gen.client.create.call_args_list]
        assert RoutingBGPPeerGroup in created_types
        assert RoutingBGPNeighbor in created_types
        assert RoutingPrefixList in created_types
        assert RoutingPrefixListEntry in created_types
        assert RoutingRouteMap in created_types
        assert RoutingRouteMapEntry in created_types
        assert RoutingStaticRoute in created_types


# --- AVD Source Attribution ---


class TestGetAvdSource:
    async def test_returns_group_id_when_found(self) -> None:
        """Test that _get_avd_source returns the group ID when CoreAccountGroup exists."""
        gen = _make_generator()
        mock_group = MagicMock()
        mock_group.id = "avd-group-123"
        gen.client.get = AsyncMock(return_value=mock_group)

        result = await gen._get_avd_source()

        assert result == "avd-group-123"
        gen.client.get.assert_awaited_once_with(CoreAccountGroup, name__value="AVD")

    async def test_returns_none_when_not_found(self) -> None:
        """Test that _get_avd_source returns None when CoreAccountGroup is missing."""
        gen = _make_generator()
        gen.client.get = AsyncMock(side_effect=NodeNotFoundError(identifier={"name": ["AVD"]}))

        result = await gen._get_avd_source()

        assert result is None


class TestSetSource:
    def test_sets_source_on_all_attributes(self) -> None:
        """Test that _set_source sets source on all node attributes."""
        node = MagicMock()
        attr1 = MagicMock()
        attr2 = MagicMock()
        node._attributes = ["attr1", "attr2"]
        node.attr1 = attr1
        node.attr2 = attr2

        BackfillStructuredConfigGenerator._set_source(node, "avd-group-123")

        assert attr1.source is not None
        assert attr1.source.id == "avd-group-123"
        assert attr2.source is not None
        assert attr2.source.id == "avd-group-123"

    def test_noop_when_source_is_none(self) -> None:
        """Test that _set_source is a no-op when source_id is None."""
        node = MagicMock()
        attr1 = MagicMock()
        node._attributes = ["attr1"]
        node.attr1 = attr1
        original_source = attr1.source

        BackfillStructuredConfigGenerator._set_source(node, None)

        assert attr1.source is original_source


class TestSourceAttributionIp:
    async def test_backfill_ip_sets_source_on_prefix_and_address(self) -> None:
        """Test that _backfill_ip sets AVD source on IpamIPPrefix and IpamIPAddress."""
        gen = _make_generator()
        mock_prefix = MagicMock()
        mock_prefix.save = AsyncMock()
        mock_prefix._attributes = ["prefix", "role"]
        mock_prefix.prefix = MagicMock()
        mock_prefix.role = MagicMock()

        mock_ip = MagicMock()
        mock_ip.save = AsyncMock()
        mock_ip._attributes = ["address"]
        mock_ip.address = MagicMock()

        mock_interface = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Ethernet1", ip_node=None)
        await gen._backfill_ip(iface, "10.0.0.1/31", "leaf-1", avd_source="avd-123")

        assert mock_prefix.prefix.source.id == "avd-123"
        assert mock_prefix.role.source.id == "avd-123"
        assert mock_ip.address.source.id == "avd-123"

    async def test_backfill_ip_no_source_when_none(self) -> None:
        """Test that _backfill_ip does not set source when avd_source is None."""
        gen = _make_generator()
        mock_prefix = _make_saveable_mock()
        mock_ip = _make_saveable_mock()
        mock_interface = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Ethernet1", ip_node=None)
        await gen._backfill_ip(iface, "10.0.0.1/31", "leaf-1", avd_source=None)

        # save should still be called, but source not set
        mock_prefix.save.assert_awaited_once()
        mock_ip.save.assert_awaited_once()


class TestSourceAttributionMtu:
    async def test_update_mtu_sets_source(self) -> None:
        """Test that _update_mtu sets AVD source on the MTU attribute."""
        gen = _make_generator()
        mock_interface = _make_saveable_mock()
        mock_interface.mtu = MagicMock()
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(mtu=1500)
        await gen._update_mtu(iface, 9214, "leaf-1", avd_source="avd-123")

        assert mock_interface.mtu.source.id == "avd-123"


class TestSourceAttributionBgp:
    async def test_bgp_peer_group_sets_source(self) -> None:
        """Test that _backfill_bgp_peer_groups sets AVD source on peer groups."""
        gen = _make_generator()
        mock_pg = MagicMock()
        mock_pg.save = AsyncMock()
        mock_pg._attributes = ["name", "type"]
        mock_pg.name = MagicMock()
        mock_pg.type = MagicMock()
        gen.client.create = AsyncMock(return_value=mock_pg)

        bgp_config = {"peer_groups": [{"name": "PG1", "type": "ipv4"}]}
        await gen._backfill_bgp_peer_groups(bgp_config, "dev-1", "leaf-1", avd_source="avd-123")

        assert mock_pg.name.source.id == "avd-123"
        assert mock_pg.type.source.id == "avd-123"

    async def test_bgp_neighbor_sets_source(self) -> None:
        """Test that _backfill_bgp_neighbors sets AVD source on neighbors."""
        gen = _make_generator()
        mock_nb = MagicMock()
        mock_nb.save = AsyncMock()
        mock_nb._attributes = ["peer_address"]
        mock_nb.peer_address = MagicMock()
        gen.client.create = AsyncMock(return_value=mock_nb)

        bgp_config = {"neighbors": [{"ip_address": "10.0.0.1"}]}
        await gen._backfill_bgp_neighbors(bgp_config, "dev-1", "leaf-1", {}, avd_source="avd-123")

        assert mock_nb.peer_address.source.id == "avd-123"


class TestSourceAttributionRouting:
    async def test_prefix_list_sets_source(self) -> None:
        """Test that _backfill_prefix_lists sets AVD source on prefix lists and entries."""
        gen = _make_generator()
        mock_pl = MagicMock()
        mock_pl.save = AsyncMock()
        mock_pl._attributes = ["name"]
        mock_pl.name = MagicMock()

        mock_entry = MagicMock()
        mock_entry.save = AsyncMock()
        mock_entry._attributes = ["sequence", "action"]
        mock_entry.sequence = MagicMock()
        mock_entry.action = MagicMock()

        gen.client.create = AsyncMock(side_effect=[mock_pl, mock_entry])

        prefix_lists = [
            {"name": "PL1", "sequence_numbers": [{"sequence": 10, "action": "permit any"}]}
        ]
        await gen._backfill_prefix_lists(prefix_lists, "dev-1", "leaf-1", avd_source="avd-123")

        assert mock_pl.name.source.id == "avd-123"
        assert mock_entry.sequence.source.id == "avd-123"
        assert mock_entry.action.source.id == "avd-123"

    async def test_route_map_sets_source(self) -> None:
        """Test that _backfill_route_maps sets AVD source on route maps and entries."""
        gen = _make_generator()
        mock_rm = MagicMock()
        mock_rm.save = AsyncMock()
        mock_rm._attributes = ["name"]
        mock_rm.name = MagicMock()

        mock_entry = MagicMock()
        mock_entry.save = AsyncMock()
        mock_entry._attributes = ["sequence", "type"]
        mock_entry.sequence = MagicMock()
        mock_entry.type = MagicMock()

        gen.client.create = AsyncMock(side_effect=[mock_rm, mock_entry])

        route_maps = [{"name": "RM1", "sequence_numbers": [{"sequence": 10, "type": "permit"}]}]
        await gen._backfill_route_maps(route_maps, "dev-1", "leaf-1", avd_source="avd-123")

        assert mock_rm.name.source.id == "avd-123"
        assert mock_entry.sequence.source.id == "avd-123"

    async def test_static_route_sets_source(self) -> None:
        """Test that _backfill_static_routes sets AVD source on static routes."""
        gen = _make_generator()
        mock_route = MagicMock()
        mock_route.save = AsyncMock()
        mock_route._attributes = ["prefix", "vrf"]
        mock_route.prefix = MagicMock()
        mock_route.vrf = MagicMock()
        gen.client.create = AsyncMock(return_value=mock_route)

        static_routes = [{"destination_address_prefix": "0.0.0.0/0", "gateway": "1.1.1.1"}]
        await gen._backfill_static_routes(static_routes, "dev-1", "leaf-1", avd_source="avd-123")

        assert mock_route.prefix.source.id == "avd-123"
        assert mock_route.vrf.source.id == "avd-123"


class TestSourceAttributionGracefulDegradation:
    async def test_generate_continues_without_source_when_group_missing(self) -> None:
        """Test that generate works correctly when CoreAccountGroup is not found."""
        gen = _make_generator()

        structured_config = {
            "ethernet_interfaces": [
                {"name": "Ethernet1", "ip_address": "10.0.0.1/31"},
            ]
        }
        gen.client.object_store.get = AsyncMock(return_value=json.dumps(structured_config))

        mock_prefix = _make_saveable_mock()
        mock_ip = _make_saveable_mock()
        mock_interface = _make_saveable_mock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])

        # First get call is for CoreAccountGroup (not found), rest for interface
        gen.client.get = AsyncMock(
            side_effect=[NodeNotFoundError(identifier={"name": ["AVD"]}), mock_interface]
        )

        interfaces = [
            {
                "node": {
                    "__typename": "InterfacePhysical",
                    "id": "iface-1",
                    "name": {"value": "Ethernet1"},
                    "role": {"value": "uplink"},
                    "mtu": None,
                    "ip_address": {"node": None},
                }
            }
        ]
        data = _build_artifact_query_data(interfaces=interfaces)
        await gen.generate(data)

        # Should still create prefix and IP, just without source
        assert gen.client.create.call_count == 2


# --- Constants ---


class TestConstants:
    def test_interface_sections(self) -> None:
        """Verify expected interface sections."""
        assert "ethernet_interfaces" in INTERFACE_SECTIONS
        assert "loopback_interfaces" in INTERFACE_SECTIONS
        assert "management_interfaces" in INTERFACE_SECTIONS

    def test_routing_sections(self) -> None:
        """Verify expected routing sections."""
        assert "router_bgp" in ROUTING_SECTIONS
        assert "prefix_lists" in ROUTING_SECTIONS
        assert "route_maps" in ROUTING_SECTIONS
        assert "static_routes" in ROUTING_SECTIONS

    def test_unmodeled_sections_no_routing(self) -> None:
        """Verify routing sections have been removed from unmodeled list."""
        assert "router_bgp" not in UNMODELED_SECTIONS
        assert "prefix_lists" not in UNMODELED_SECTIONS
        assert "route_maps" not in UNMODELED_SECTIONS
        assert "static_routes" not in UNMODELED_SECTIONS

    def test_remaining_unmodeled_sections(self) -> None:
        """Verify remaining unmodeled sections are still tracked."""
        assert "ip_routing" in UNMODELED_SECTIONS
        assert "spanning_tree" in UNMODELED_SECTIONS
        assert "ntp" in UNMODELED_SECTIONS
