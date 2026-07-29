from __future__ import annotations

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


def _pod_data(*, pod_pools: list[dict], fabric_pools: list[dict]) -> dict:
    fabric = {
        "id": "fabric-a",
        "name": _attr("Fabric-A"),
        "fabric_ip_pools": {"edges": [_edge(pool) for pool in fabric_pools]},
    }
    return {
        "NetworkFabric": {
            "edges": [
                _edge({**fabric, "underlay_routing_protocol": _attr("ebgp"), "overlay_routing_protocol": _attr("ebgp")})
            ]
        },
        "NetworkPod": {
            "edges": [
                _edge(
                    {
                        "id": "pod-a",
                        "name": _attr("Pod-A"),
                        "parent": {"node": fabric},
                        "pod_ip_pools": {"edges": [_edge(pool) for pool in pod_pools]},
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
