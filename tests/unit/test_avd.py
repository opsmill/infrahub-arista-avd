"""Unit tests for AVD utilities module."""

import pytest

from solution_arista_avd.avd import (
    LEAF_ROLE_BY_UNDERLAY,
    MLAG_MAIN_TIER_ROLES,
    ROLE_TO_AVD_TYPE,
    SPINE_ROLE_BY_UNDERLAY,
    SPINE_UPLINK_UNDERLAYS,
    get_avd_type,
)
from tests.unit.test_avd_example_fabrics_schema_contract import (
    _dcim_device_role_choice_names,
)


class TestGetAvdType:
    """Tests for get_avd_type function."""

    @pytest.mark.parametrize(
        "role,expected",
        [
            ("super_spine", "super-spine"),
            ("spine", "spine"),
            ("leaf", "l3leaf"),
            ("border_leaf", "l3leaf"),
            ("l2leaf", "l2leaf"),
            ("l2spine", "l2spine"),
            ("l3spine", "l3spine"),
            ("p", "p"),
            ("pe", "pe"),
            ("rr", "rr"),
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
        expected_roles = {
            "super_spine",
            "spine",
            "leaf",
            "border_leaf",
            "l2leaf",
            "l2spine",
            "l3spine",
            "p",
            "pe",
            "rr",
        }
        assert set(ROLE_TO_AVD_TYPE.keys()) == expected_roles

    def test_every_role_maps_to_non_empty_type(self) -> None:
        """Every mapped role must resolve to a non-empty AVD node type."""
        for role, avd_type in ROLE_TO_AVD_TYPE.items():
            assert avd_type, f"Role {role!r} maps to an empty AVD node type"
            assert get_avd_type(role) == avd_type

    def test_schema_roles_all_mapped(self) -> None:
        """Every DcimDevice.role choice in the schema must have a mapping.

        Guards against adding a role choice without a matching
        ``ROLE_TO_AVD_TYPE`` entry (which would leave devices without a
        valid AVD node type). See SC-005.
        """
        schema_roles = _dcim_device_role_choice_names()
        missing = schema_roles - set(ROLE_TO_AVD_TYPE)
        assert not missing, f"Schema roles missing ROLE_TO_AVD_TYPE mapping: {sorted(missing)}"


class TestUnderlayRoleMapping:
    """Tests for the underlay-driven spine/leaf role selection."""

    @pytest.mark.parametrize(
        "underlay,expected_spine,expected_leaf",
        [
            ("none", "l2spine", "l2leaf"),
            ("ospf", "l3spine", "l2leaf"),
            ("isis-ldp", "p", "pe"),
        ],
    )
    def test_non_l3ls_underlays_map_to_design_roles(
        self, underlay: str, expected_spine: str, expected_leaf: str
    ) -> None:
        """Each non-L3LS underlay selects the design-specific spine/leaf roles."""
        assert SPINE_ROLE_BY_UNDERLAY[underlay] == expected_spine
        assert LEAF_ROLE_BY_UNDERLAY[underlay] == expected_leaf

    def test_l3ls_underlay_falls_back_to_default_roles(self) -> None:
        """Routed L3LS (ebgp) is absent from the maps, so generators fall back to
        the default spine/leaf roles via ``.get(underlay, default)``."""
        assert SPINE_ROLE_BY_UNDERLAY.get("ebgp", "spine") == "spine"
        assert LEAF_ROLE_BY_UNDERLAY.get("ebgp", "leaf") == "leaf"

    def test_mapped_underlays_are_spine_uplink_underlays(self) -> None:
        """Every underlay with a design-role mapping must also be a spine-uplink
        underlay, so the main leaf tier uplinks to the spine tier consistently."""
        assert set(SPINE_ROLE_BY_UNDERLAY) <= SPINE_UPLINK_UNDERLAYS
        assert set(LEAF_ROLE_BY_UNDERLAY) <= SPINE_UPLINK_UNDERLAYS

    def test_role_maps_resolve_to_known_avd_types(self) -> None:
        """Every role produced by the underlay maps must have an AVD type."""
        for role in {*SPINE_ROLE_BY_UNDERLAY.values(), *LEAF_ROLE_BY_UNDERLAY.values()}:
            assert get_avd_type(role)

    def test_mlag_main_tier_roles_are_known_and_non_l3ls(self) -> None:
        """The MLAG main-tier roles are the non-L3LS access/core tiers, all mapped."""
        assert {"l2leaf", "l2spine", "l3spine"} == MLAG_MAIN_TIER_ROLES
        for role in MLAG_MAIN_TIER_ROLES:
            assert get_avd_type(role)
