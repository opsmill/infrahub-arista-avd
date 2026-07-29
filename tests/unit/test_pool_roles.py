from __future__ import annotations

import pytest

from solution_arista_avd.pool_roles import (
    FABRIC_POOL_ROLES,
    LEGACY_ROLE_ALIASES,
    POOL_ROLE_BY_PREFIX_ROLE,
    PoolRoleResolutionError,
    ResourceRole,
    fabric_required_roles,
    missing_fabric_roles,
    pod_required_mlag_roles,
    resolve_resource_role,
    validate_pod_pool_containment,
    validate_unique_roles,
)


def test_prefix_role_aliases_map_legacy_values_to_authoritative_roles() -> None:
    assert LEGACY_ROLE_ALIASES["supernet"] == ResourceRole.FABRIC_SUPERNET
    assert LEGACY_ROLE_ALIASES["pod_leaf_spine"] == ResourceRole.FABRIC_POINT_TO_POINT
    assert LEGACY_ROLE_ALIASES["pod_super_spine_spine"] == ResourceRole.FABRIC_POINT_TO_POINT


def test_pool_role_mapping_covers_fabric_required_roles() -> None:
    mapped_roles = set(POOL_ROLE_BY_PREFIX_ROLE.values())

    assert FABRIC_POOL_ROLES.issubset(mapped_roles)


def test_resolve_resource_role_rejects_mixed_authoritative_roles() -> None:
    with pytest.raises(PoolRoleResolutionError, match="mixed roles"):
        resolve_resource_role(["loopback", "loopback-vtep"], scope="fabric", pool_name="Mixed-Pool")


def test_resolve_resource_role_rejects_non_fabric_role_for_fabric_scope() -> None:
    with pytest.raises(PoolRoleResolutionError, match="does not satisfy fabric pool requirements"):
        resolve_resource_role(["backfill"], scope="fabric", pool_name="Backfill-Pool")


def test_resolve_resource_role_accepts_homogeneous_role_aliases() -> None:
    assert (
        resolve_resource_role(["pod_leaf_spine", "fabric_point_to_point"], scope="fabric", pool_name="P2P-Pool")
        == ResourceRole.FABRIC_POINT_TO_POINT
    )


def test_fabric_required_roles_follow_routing_and_dci_intent() -> None:
    assert fabric_required_roles(
        overlay_routing_protocol="ebgp",
        underlay_routing_protocol="ebgp",
        has_dci_links=True,
    ) == {
        ResourceRole.MANAGEMENT,
        ResourceRole.LOOPBACK,
        ResourceRole.LOOPBACK_VTEP,
        ResourceRole.FABRIC_POINT_TO_POINT,
        ResourceRole.DCI,
    }


def test_fabric_required_roles_exclude_underlay_when_none() -> None:
    assert ResourceRole.FABRIC_POINT_TO_POINT not in fabric_required_roles(
        overlay_routing_protocol="ebgp",
        underlay_routing_protocol="none",
        has_dci_links=False,
    )


def test_validate_unique_roles_rejects_duplicate_fabric_roles() -> None:
    with pytest.raises(PoolRoleResolutionError, match="duplicate"):
        validate_unique_roles(
            {
                "Loopback-A": ResourceRole.LOOPBACK,
                "Loopback-B": ResourceRole.LOOPBACK,
            },
            scope="fabric",
        )


def test_missing_fabric_roles_require_fabric_supernet_fallback() -> None:
    missing = missing_fabric_roles(
        required_roles={ResourceRole.MANAGEMENT, ResourceRole.LOOPBACK},
        available_roles={ResourceRole.MANAGEMENT, ResourceRole.FABRIC_SUPERNET},
    )

    assert missing == {ResourceRole.LOOPBACK}


def test_missing_fabric_roles_reject_missing_supernet_fallback() -> None:
    with pytest.raises(PoolRoleResolutionError, match="Fabric Supernet"):
        missing_fabric_roles(
            required_roles={ResourceRole.MANAGEMENT, ResourceRole.LOOPBACK},
            available_roles={ResourceRole.MANAGEMENT},
        )


def test_resolve_resource_role_rejects_management_role_for_pod_scope() -> None:
    with pytest.raises(PoolRoleResolutionError, match="does not satisfy pod pool requirements"):
        resolve_resource_role(["management"], scope="pod", pool_name="Pod-Mgmt-Pool")


def test_resolve_resource_role_accepts_allowed_pod_roles() -> None:
    assert (
        resolve_resource_role(["loopback-vtep"], scope="pod", pool_name="Pod-VTEP-Pool") == ResourceRole.LOOPBACK_VTEP
    )


def test_validate_pod_pool_containment_accepts_matching_fabric_subnet() -> None:
    validate_pod_pool_containment(
        pod_role_prefixes={ResourceRole.LOOPBACK: ["10.0.0.0/25"]},
        fabric_role_prefixes={ResourceRole.LOOPBACK: ["10.0.0.0/24"]},
    )


def test_validate_pod_pool_containment_rejects_prefix_outside_matching_fabric_pool() -> None:
    with pytest.raises(PoolRoleResolutionError, match="not contained"):
        validate_pod_pool_containment(
            pod_role_prefixes={ResourceRole.FABRIC_POINT_TO_POINT: ["10.0.1.0/24"]},
            fabric_role_prefixes={ResourceRole.FABRIC_POINT_TO_POINT: ["10.0.0.0/24"]},
        )


def test_pod_required_mlag_roles_require_peer_for_l2_fabric() -> None:
    assert pod_required_mlag_roles(underlay_routing_protocol="none", has_mlag_enabled_rack=False) == {ResourceRole.MLAG}


def test_pod_required_mlag_roles_require_peer_and_l3_peering_for_l3_mlag_pod() -> None:
    assert pod_required_mlag_roles(underlay_routing_protocol="ebgp", has_mlag_enabled_rack=True) == {
        ResourceRole.MLAG,
        ResourceRole.MLAG_PEERING,
    }
