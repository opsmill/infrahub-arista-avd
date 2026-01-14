"""Unit tests for AVD utilities module."""

import pytest

from solution_ai_dc.avd import (
    ROLE_TO_AVD_TYPE,
    AvdInputsBuilder,
    get_avd_type,
)


class TestGetAvdType:
    """Tests for get_avd_type function."""

    @pytest.mark.parametrize(
        "role,expected",
        [
            ("super_spine", "super-spine"),
            ("spine", "spine"),
            ("leaf", "l3leaf"),
        ],
    )
    def test_valid_roles(self, role: str, expected: str) -> None:
        """Test that valid roles map to correct AVD types."""
        assert get_avd_type(role) == expected

    def test_invalid_role(self) -> None:
        """Test that invalid role raises ValueError."""
        with pytest.raises(ValueError, match="Unknown device role"):
            get_avd_type("invalid_role")


class TestRoleMapping:
    """Tests for role mapping dictionary."""

    def test_all_roles_defined(self) -> None:
        """Ensure all expected roles are defined."""
        expected_roles = {"super_spine", "spine", "leaf"}
        assert set(ROLE_TO_AVD_TYPE.keys()) == expected_roles


class TestAvdInputsBuilder:
    """Tests for AvdInputsBuilder class."""

    def test_init(self) -> None:
        """Test builder initialization."""
        builder = AvdInputsBuilder("test-fabric", "10.0.0.1")
        assert builder.fabric_name == "test-fabric"
        assert builder.mgmt_gateway == "10.0.0.1"

    def test_init_without_gateway(self) -> None:
        """Test builder initialization without management gateway."""
        builder = AvdInputsBuilder("test-fabric")
        assert builder.fabric_name == "test-fabric"
        assert builder.mgmt_gateway is None

    def test_build_device_hostvars_super_spine(self) -> None:
        """Test hostvars generation for super-spine device."""
        builder = AvdInputsBuilder("test-fabric", "10.0.0.1")
        hostvars = builder.build_device_hostvars(
            hostname="ss-test-1",
            role="super_spine",
            bgp_asn=65000,
            node_id=1,
            loopback_ip="10.1.0.1",
            mgmt_ip="10.255.0.1",
        )

        assert hostvars["type"] == "super-spine"
        assert hostvars["id"] == 1
        assert hostvars["bgp_as"] == "65000"
        assert hostvars["fabric_name"] == "test-fabric"
        assert hostvars["loopback_ipv4_address"] == "10.1.0.1"
        assert hostvars["mgmt_ip"] == "10.255.0.1"
        assert hostvars["mgmt_gateway"] == "10.0.0.1"
        # Super-spines should not have uplink info
        assert "uplink_interfaces" not in hostvars

    def test_build_device_hostvars_spine_with_uplinks(self) -> None:
        """Test hostvars generation for spine device with uplinks."""
        builder = AvdInputsBuilder("test-fabric")
        hostvars = builder.build_device_hostvars(
            hostname="spine-test-1",
            role="spine",
            bgp_asn=65001,
            node_id=2,
            loopback_ip="10.1.0.2",
            uplink_interfaces=["Ethernet1", "Ethernet2"],
            uplink_switches=["ss-test-1", "ss-test-2"],
            uplink_switch_interfaces=["Ethernet1", "Ethernet1"],
        )

        assert hostvars["type"] == "spine"
        assert hostvars["uplink_interfaces"] == ["Ethernet1", "Ethernet2"]
        assert hostvars["uplink_switches"] == ["ss-test-1", "ss-test-2"]
        assert hostvars["uplink_switch_interfaces"] == ["Ethernet1", "Ethernet1"]

    def test_build_device_hostvars_leaf_with_uplinks(self) -> None:
        """Test hostvars generation for leaf device with uplinks."""
        builder = AvdInputsBuilder("test-fabric")
        hostvars = builder.build_device_hostvars(
            hostname="leaf-test-1-1",
            role="leaf",
            bgp_asn=65002,
            node_id=3,
            uplink_interfaces=["Ethernet49", "Ethernet50"],
            uplink_switches=["spine-test-1", "spine-test-2"],
            uplink_switch_interfaces=["Ethernet1", "Ethernet1"],
        )

        assert hostvars["type"] == "l3leaf"
        assert hostvars["uplink_interfaces"] == ["Ethernet49", "Ethernet50"]

    def test_build_device_hostvars_optional_fields(self) -> None:
        """Test that optional fields are not included when not provided."""
        builder = AvdInputsBuilder("test-fabric")
        hostvars = builder.build_device_hostvars(
            hostname="ss-test-1",
            role="super_spine",
            bgp_asn=65000,
            node_id=1,
        )

        assert "loopback_ipv4_address" not in hostvars
        assert "mgmt_ip" not in hostvars
        assert "mgmt_gateway" not in hostvars

    def test_bgp_asn_is_string(self) -> None:
        """Test that BGP ASN is converted to string."""
        builder = AvdInputsBuilder("test-fabric")
        hostvars = builder.build_device_hostvars(
            hostname="test",
            role="spine",
            bgp_asn=65000,
            node_id=1,
        )

        assert hostvars["bgp_as"] == "65000"
        assert isinstance(hostvars["bgp_as"], str)
