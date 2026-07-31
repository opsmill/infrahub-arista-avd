from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parents[2]
OBJECT_FILES = sorted((REPO_ROOT / "objects").glob("*.yml"))


def _documents(path: Path) -> list[dict[str, Any]]:
    return [document for document in yaml.safe_load_all(path.read_text(encoding="utf-8")) if isinstance(document, dict)]


def _object_rows(kind: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for object_file in OBJECT_FILES:
        for document in _documents(object_file):
            spec = document.get("spec", {})
            if spec.get("kind") == kind:
                rows.extend(spec.get("data", []))
    return rows


def test_every_network_fabric_legacy_pool_assignment_is_in_fabric_ip_pools() -> None:
    legacy_fields = ["mgmt_pool", "uplink_pool", "vtep_pool", "loopback_pool", "dci_pool"]

    for fabric in _object_rows("NetworkFabric"):
        fabric_ip_pools = set(fabric.get("fabric_ip_pools", []))
        for field in legacy_fields:
            legacy_pool = fabric.get(field)
            if legacy_pool:
                assert legacy_pool in fabric_ip_pools, f"{fabric['name']} missing {field} in fabric_ip_pools"


def test_every_network_pod_legacy_mlag_assignment_is_in_pod_ip_pools() -> None:
    for fabric in _object_rows("NetworkFabric"):
        for pod in fabric.get("children", {}).get("data", []):
            pod_ip_pools = set(pod.get("pod_ip_pools", []))
            for field in ("mlag_peer_pool", "mlag_l3_pool"):
                legacy_pool = pod.get(field)
                if legacy_pool:
                    assert legacy_pool in pod_ip_pools, f"{pod['name']} missing {field} in pod_ip_pools"


def test_migrated_prefix_roles_use_explicit_fabric_and_mlag_roles() -> None:
    roles_by_prefix = {row["prefix"]: row["role"] for row in _object_rows("IpamPrefix")}

    assert roles_by_prefix["10.0.0.0/8"] == "fabric_supernet"
    assert "pod_leaf_spine" not in set(roles_by_prefix.values())
    assert "pod_super_spine_spine" not in set(roles_by_prefix.values())
    assert "technical" not in {
        roles_by_prefix[prefix]
        for prefix in (
            "172.16.0.0/28",
            "10.60.4.0/24",
            "10.61.4.0/24",
            "10.64.4.0/24",
            "10.64.5.0/24",
        )
    }
    assert roles_by_prefix["172.16.0.0/28"] == "dci"
    assert roles_by_prefix["10.64.4.0/24"] == "mlag"
    assert roles_by_prefix["10.64.5.0/24"] == "mlag_peering"
