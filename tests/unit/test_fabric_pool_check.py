from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

from checks.fabric_pool_check import FabricPoolValidationCheck


def _attr(value: object) -> dict:
    return {"value": value}


def _edge(node: dict) -> dict:
    return {"node": node}


def _resource(role: str, prefix: str = "10.0.0.0/24") -> dict:
    return _edge({"__typename": "IpamPrefix", "role": _attr(role), "prefix": _attr(prefix)})


def _pool(name: str, typename: str, roles: list[str], *, prefix: str = "10.0.0.0/24") -> dict:
    return {
        "__typename": typename,
        "id": name,
        "name": _attr(name),
        "resources": {"edges": [_resource(role, prefix) for role in roles]},
    }


def _fabric(pools: list[dict], *, underlay: str = "ebgp", overlay: str = "ebgp") -> dict:
    return {
        "NetworkFabric": {
            "edges": [
                _edge(
                    {
                        "id": "fabric-a",
                        "name": _attr("Fabric-A"),
                        "underlay_routing_protocol": _attr(underlay),
                        "overlay_routing_protocol": _attr(overlay),
                        "fabric_ip_pools": {"edges": [_edge(pool) for pool in pools]},
                    }
                )
            ]
        },
        "NetworkLink": {"edges": []},
    }


def _dci_link_for_fabric(fabric_id: str) -> dict:
    return _edge(
        {
            "id": f"dci-{fabric_id}",
            "connected_endpoints": {
                "edges": [
                    _edge(
                        {
                            "__typename": "InterfacePhysical",
                            "device": {
                                "node": {"id": "device-a", "pod": {"node": {"parent": {"node": {"id": fabric_id}}}}}
                            },
                        }
                    )
                ]
            },
        }
    )


def _pod_data(
    *,
    pod_pools: list[dict],
    fabric_pools: list[dict],
    underlay: str | None = "ebgp",
    rack_mlag: bool | None = None,
) -> dict:
    fabric = {
        "id": "fabric-a",
        "name": _attr("Fabric-A"),
        "underlay_routing_protocol": _attr(underlay),
        "fabric_ip_pools": {"edges": [_edge(pool) for pool in fabric_pools]},
    }
    racks = []
    if rack_mlag is not None:
        racks.append(_edge({"id": "rack-a", "mlag": _attr(rack_mlag)}))
    return {
        "NetworkFabric": {"edges": [_edge({**fabric, "overlay_routing_protocol": _attr("ebgp")})]},
        "NetworkPod": {
            "edges": [
                _edge(
                    {
                        "id": "pod-a",
                        "name": _attr("Pod-A"),
                        "parent": {"node": fabric},
                        "pod_ip_pools": {"edges": [_edge(pool) for pool in pod_pools]},
                        "racks": {"edges": racks},
                    }
                )
            ]
        },
        "NetworkLink": {"edges": []},
    }


def _check() -> FabricPoolValidationCheck:
    check = FabricPoolValidationCheck.__new__(FabricPoolValidationCheck)
    check.log_error = Mock()  # type: ignore[method-assign]
    check.log_info = Mock()  # type: ignore[method-assign]
    return check


async def test_fabric_pool_check_accepts_complete_fabric_pool_roles() -> None:
    check = _check()

    await check.validate(
        _fabric(
            [
                _pool("mgmt", "CoreIPAddressPool", ["management"]),
                _pool("loopback", "CoreIPPrefixPool", ["loopback"]),
                _pool("vtep", "CoreIPPrefixPool", ["loopback-vtep"]),
                _pool("uplink", "CoreIPPrefixPool", ["fabric_point_to_point"]),
            ]
        )
    )

    check.log_error.assert_not_called()


async def test_fabric_pool_check_scopes_dci_requirement_to_endpoint_fabric() -> None:
    check = _check()
    fabric_a = {
        "id": "fabric-a",
        "name": _attr("Fabric-A"),
        "underlay_routing_protocol": _attr("ebgp"),
        "overlay_routing_protocol": _attr("ebgp"),
        "fabric_ip_pools": {
            "edges": [
                _edge(_pool("mgmt-a", "CoreIPAddressPool", ["management"])),
                _edge(_pool("loopback-a", "CoreIPPrefixPool", ["loopback"])),
                _edge(_pool("vtep-a", "CoreIPPrefixPool", ["loopback-vtep"])),
                _edge(_pool("uplink-a", "CoreIPPrefixPool", ["fabric_point_to_point"])),
                _edge(_pool("dci-a", "CoreIPPrefixPool", ["dci"])),
            ]
        },
    }
    fabric_b = {
        "id": "fabric-b",
        "name": _attr("Fabric-B"),
        "underlay_routing_protocol": _attr("ebgp"),
        "overlay_routing_protocol": _attr("ebgp"),
        "fabric_ip_pools": {
            "edges": [
                _edge(_pool("mgmt-b", "CoreIPAddressPool", ["management"])),
                _edge(_pool("loopback-b", "CoreIPPrefixPool", ["loopback"])),
                _edge(_pool("vtep-b", "CoreIPPrefixPool", ["loopback-vtep"])),
                _edge(_pool("uplink-b", "CoreIPPrefixPool", ["fabric_point_to_point"])),
            ]
        },
    }

    await check.validate(
        {
            "NetworkFabric": {"edges": [_edge(fabric_a), _edge(fabric_b)]},
            "NetworkLink": {"edges": [_dci_link_for_fabric("fabric-a")]},
            "NetworkPod": {"edges": []},
        }
    )

    check.log_error.assert_not_called()


async def test_fabric_pool_check_rejects_missing_required_role_without_supernet() -> None:
    check = _check()

    await check.validate(_fabric([_pool("mgmt", "CoreIPAddressPool", ["management"])]))

    check.log_error.assert_called()
    assert "Fabric Supernet" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_allows_missing_prefix_roles_with_supernet() -> None:
    check = _check()

    await check.validate(
        _fabric(
            [
                _pool("mgmt", "CoreIPAddressPool", ["management"]),
                _pool("supernet", "CoreIPPrefixPool", ["fabric_supernet"], prefix="10.0.0.0/16"),
            ]
        )
    )

    check.log_error.assert_not_called()


async def test_fabric_pool_check_rejects_fabric_supernet_exhaustion() -> None:
    check = _check()

    await check.validate(
        _fabric(
            [
                _pool("mgmt", "CoreIPAddressPool", ["management"]),
                _pool("supernet", "CoreIPPrefixPool", ["fabric_supernet"], prefix="10.0.0.0/30"),
            ]
        )
    )

    assert "unable to allocate" in str(check.log_error.call_args_list)
    assert "/27" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_duplicate_roles() -> None:
    check = _check()

    await check.validate(
        _fabric(
            [
                _pool("mgmt-a", "CoreIPAddressPool", ["management"]),
                _pool("mgmt-b", "CoreIPAddressPool", ["management"]),
            ]
        )
    )

    assert "duplicate" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_mixed_role_pool() -> None:
    check = _check()

    await check.validate(
        _fabric(
            [
                _pool("mgmt", "CoreIPAddressPool", ["management"]),
                _pool("mixed", "CoreIPPrefixPool", ["loopback", "loopback-vtep"]),
            ]
        )
    )

    assert "mixed roles" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_non_ip_pool_members() -> None:
    check = _check()

    await check.validate(_fabric([_pool("number-pool", "CoreNumberPool", ["management"])]))

    assert "non-IP pool" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_accepts_contained_pod_pools() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/25")],
            fabric_pools=[
                _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24"),
                _pool("loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/24"),
                _pool("vtep", "CoreIPPrefixPool", ["loopback-vtep"], prefix="10.0.1.0/24"),
                _pool("uplink", "CoreIPPrefixPool", ["fabric_point_to_point"], prefix="10.0.2.0/24"),
            ],
        )
    )

    check.log_error.assert_not_called()


async def test_fabric_pool_check_rejects_pod_pool_outside_matching_fabric_pool() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-uplink", "CoreIPPrefixPool", ["fabric_point_to_point"], prefix="10.0.3.0/24")],
            fabric_pools=[
                _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24"),
                _pool("loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/24"),
                _pool("vtep", "CoreIPPrefixPool", ["loopback-vtep"], prefix="10.0.1.0/24"),
                _pool("uplink", "CoreIPPrefixPool", ["fabric_point_to_point"], prefix="10.0.2.0/24"),
            ],
        )
    )

    assert "not contained" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_management_pool_at_pod_scope() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
            fabric_pools=[_pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
        )
    )

    assert "does not satisfy pod pool requirements" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_duplicate_pod_roles() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[
                _pool("pod-loopback-a", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/25"),
                _pool("pod-loopback-b", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.128/25"),
            ],
            fabric_pools=[
                _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24"),
                _pool("loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/24"),
            ],
        )
    )

    assert "duplicate" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_rejects_mlag_prefix_pool_kind() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-mlag", "CoreIPPrefixPool", ["mlag"], prefix="169.254.0.0/31")],
            fabric_pools=[_pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
        )
    )

    assert "must be CoreIPAddressPool" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_requires_mlag_and_mlag_peering_for_mlag_rack_with_underlay() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-mlag", "CoreIPAddressPool", ["mlag"], prefix="169.254.0.0/31")],
            fabric_pools=[_pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
            underlay="ebgp",
            rack_mlag=True,
        )
    )

    assert "missing required MLAG pool roles: mlag_peering" in str(check.log_error.call_args_list)


async def test_fabric_pool_check_requires_only_mlag_when_parent_underlay_is_none() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[],
            fabric_pools=[_pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
            underlay="none",
            rack_mlag=False,
        )
    )

    assert "missing required MLAG pool roles: mlag" in str(check.log_error.call_args_list)
    assert "mlag_peering" not in str(check.log_error.call_args_list)


def test_fabric_pool_check_query_scopes_pods_to_the_target_fabric() -> None:
    """An unfiltered NetworkPod would make every fabric report every other fabric's pods."""
    query = (Path(__file__).parents[2] / "checks" / "fabric_pool_check.gql").read_text(encoding="utf-8")

    assert "NetworkPod(parent__name__value: $name)" in query


async def test_fabric_pool_check_accepts_unmigrated_fabric_using_legacy_relationships() -> None:
    """A fabric that has not moved its pools into fabric_ip_pools still generates, so it must still pass."""
    check = _check()
    fabric = {
        "id": "fabric-a",
        "name": _attr("Fabric-A"),
        "underlay_routing_protocol": _attr("ebgp"),
        "overlay_routing_protocol": _attr("ebgp"),
        "fabric_ip_pools": {"edges": []},
        "mgmt_pool": {"node": _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")},
        "loopback_pool": {"node": _pool("loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/24")},
        "vtep_pool": {"node": _pool("vtep", "CoreIPPrefixPool", ["loopback-vtep"], prefix="10.0.1.0/24")},
        "uplink_pool": {"node": _pool("uplink", "CoreIPPrefixPool", ["fabric_point_to_point"], prefix="10.0.2.0/24")},
    }

    await check.validate({"NetworkFabric": {"edges": [_edge(fabric)]}, "NetworkLink": {"edges": []}})

    check.log_error.assert_not_called()
    assert "legacy" in str(check.log_info.call_args_list)


async def test_fabric_pool_check_accepts_legacy_pod_mlag_relationships() -> None:
    check = _check()
    data = _pod_data(
        pod_pools=[],
        fabric_pools=[_pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24")],
        underlay="ebgp",
        rack_mlag=True,
    )
    pod = data["NetworkPod"]["edges"][0]["node"]
    pod["mlag_peer_pool"] = {"node": _pool("mlag", "CoreIPAddressPool", ["mlag"], prefix="169.254.0.0/24")}
    pod["mlag_l3_pool"] = {"node": _pool("mlag-l3", "CoreIPAddressPool", ["mlag_peering"], prefix="10.0.9.0/24")}

    await check.validate(data)

    assert "missing required MLAG pool roles" not in str(check.log_error.call_args_list)


async def test_fabric_pool_check_allows_pod_pool_when_fabric_defers_to_its_supernet() -> None:
    """The fabric carves this role on demand, so there is no fabric pool to contain against yet."""
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/25")],
            fabric_pools=[
                _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24"),
                _pool("supernet", "CoreIPPrefixPool", ["fabric_supernet"], prefix="10.0.0.0/16"),
            ],
        )
    )

    check.log_error.assert_not_called()


async def test_fabric_pool_check_still_rejects_pod_pool_when_fabric_has_no_supernet() -> None:
    check = _check()

    await check.validate(
        _pod_data(
            pod_pools=[_pool("pod-loopback", "CoreIPPrefixPool", ["loopback"], prefix="10.0.0.0/25")],
            fabric_pools=[
                _pool("mgmt", "CoreIPAddressPool", ["management"], prefix="192.0.2.0/24"),
                _pool("uplink", "CoreIPPrefixPool", ["fabric_point_to_point"], prefix="10.0.2.0/24"),
            ],
        )
    )

    assert "no matching fabric pool for containment" in str(check.log_error.call_args_list)
