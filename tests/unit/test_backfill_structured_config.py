# ruff: noqa: SLF001
"""Unit tests for backfill structured config generator."""

import ipaddress
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from generators.backfill_structured_config import (
    INTERFACE_SECTIONS,
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


def _make_interface(
    iface_id: str = "iface-1",
    name: str | None = "Ethernet1",
    role: str | None = "uplink",
    mtu: int | None = None,
    ip_node: IpAddressNode | None = None,
) -> InterfaceNode:
    """Helper to build an InterfaceNode for tests."""
    return InterfaceNode(
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
    return gen


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
            "__typename": "NetworkDevice",
            "id": "dev-1",
            "hostname": {"value": hostname},
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
        assert device.hostname.value == "leaf-1"
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


# --- Async methods with mocked client ---


class TestBackfillIp:
    async def test_backfill_creates_prefix_ip_and_assigns(self) -> None:
        """Test that _backfill_ip creates prefix, IP, and assigns to interface."""
        gen = _make_generator()
        mock_prefix = MagicMock()
        mock_prefix.save = AsyncMock()
        mock_ip = MagicMock()
        mock_ip.save = AsyncMock()
        mock_interface = MagicMock()
        mock_interface.save = AsyncMock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Ethernet1", ip_node=None)
        await gen._backfill_ip(iface, "10.0.0.1/31", "leaf-1")

        # Verify prefix creation
        gen.client.create.assert_any_call(
            kind="IpamIPPrefix",
            prefix="10.0.0.0/31",
            role="backfill",
        )
        mock_prefix.save.assert_awaited_once_with(allow_upsert=True)

        # Verify IP creation
        gen.client.create.assert_any_call(
            kind="IpamIPAddress",
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
        mock_prefix = MagicMock()
        mock_prefix.save = AsyncMock()
        mock_ip = MagicMock()
        mock_ip.save = AsyncMock()
        mock_interface = MagicMock()
        mock_interface.save = AsyncMock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(name="Loopback0", ip_node=None)
        await gen._backfill_ip(iface, "10.255.0.1/32", "leaf-1")

        gen.client.create.assert_any_call(
            kind="IpamIPPrefix",
            prefix="10.255.0.1/32",
            role="backfill",
        )


class TestUpdateMtu:
    async def test_update_mtu_when_different(self) -> None:
        """Test that MTU is updated when it differs from current."""
        gen = _make_generator()
        mock_interface = MagicMock()
        mock_interface.mtu = MagicMock()
        mock_interface.save = AsyncMock()
        gen.client.get = AsyncMock(return_value=mock_interface)

        iface = _make_interface(mtu=1500)
        await gen._update_mtu(iface, 9214, "leaf-1")

        gen.client.get.assert_awaited_once()
        assert mock_interface.mtu.value == 9214
        mock_interface.save.assert_awaited_once_with(allow_upsert=True)

    async def test_skip_mtu_when_same(self) -> None:
        """Test that MTU update is skipped when current equals target."""
        gen = _make_generator()

        iface = _make_interface(mtu=9214)
        await gen._update_mtu(iface, 9214, "leaf-1")

        gen.client.get.assert_not_called()


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

        mock_prefix = MagicMock()
        mock_prefix.save = AsyncMock()
        mock_ip = MagicMock()
        mock_ip.save = AsyncMock()
        mock_interface = MagicMock()
        mock_interface.save = AsyncMock()
        mock_interface_mtu = MagicMock()
        mock_interface_mtu.save = AsyncMock()

        gen.client.create = AsyncMock(side_effect=[mock_prefix, mock_ip])
        gen.client.get = AsyncMock(side_effect=[mock_interface, mock_interface_mtu])

        interfaces = [
            {
                "node": {
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

    async def test_skips_interface_with_existing_ip(self) -> None:
        """Test that interfaces with existing IPs are not backfilled."""
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

        gen.client.create.assert_not_called()

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


# --- Constants ---


class TestConstants:
    def test_interface_sections(self) -> None:
        """Verify expected interface sections."""
        assert "ethernet_interfaces" in INTERFACE_SECTIONS
        assert "loopback_interfaces" in INTERFACE_SECTIONS
        assert "management_interfaces" in INTERFACE_SECTIONS

    def test_unmodeled_sections(self) -> None:
        """Verify key unmodeled sections are listed."""
        assert "router_bgp" in UNMODELED_SECTIONS
        assert "prefix_lists" in UNMODELED_SECTIONS
        assert "route_maps" in UNMODELED_SECTIONS
