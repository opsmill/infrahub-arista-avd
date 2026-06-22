"""Unit tests for AVD utilities module."""

import pytest

from solution_arista_avd.avd import (
    ROLE_TO_AVD_TYPE,
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
            ("l2leaf", "l2leaf"),
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
        expected_roles = {"super_spine", "spine", "leaf", "l2leaf"}
        assert set(ROLE_TO_AVD_TYPE.keys()) == expected_roles
