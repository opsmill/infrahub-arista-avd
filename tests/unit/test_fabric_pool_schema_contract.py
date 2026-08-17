from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parents[2]


def _load_yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load((REPO_ROOT / path).read_text(encoding="utf-8"))


def _nodes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return list(schema.get("nodes", []))


def _extension_nodes(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return list(schema.get("extensions", {}).get("nodes", []))


def _node(schema: dict[str, Any], namespace: str, name: str) -> dict[str, Any]:
    for node in _nodes(schema):
        if node.get("namespace") == namespace and node.get("name") == name:
            return node
    raise AssertionError(f"{namespace}{name} node not found")


def _extension_node(schema: dict[str, Any], kind: str) -> dict[str, Any]:
    for node in _extension_nodes(schema):
        if node.get("kind") == kind:
            return node
    raise AssertionError(f"{kind} extension not found")


def _attributes(node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {attr["name"]: attr for attr in node.get("attributes", [])}


def _relationships(node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rel["name"]: rel for rel in node.get("relationships", [])}


def _choice_names(attribute: dict[str, Any]) -> set[str]:
    return {choice["name"] for choice in attribute.get("choices", [])}


def _ipam_prefix_role_choices() -> set[str]:
    ipam_prefix = _extension_node(_load_yaml("schemas/ipam_extensions.yml"), "IpamPrefix")
    return _choice_names(_attributes(ipam_prefix)["role"])


def test_no_replacement_network_fabric_or_network_pod_node_is_introduced() -> None:
    schema_files = [
        "schemas/ipam_extensions.yml",
        "schemas/logical_design.yml",
        "schemas/l3ls_extensions.yml",
        "schemas/dci.yml",
    ]
    definitions: dict[str, list[str]] = {"NetworkFabric": [], "NetworkPod": []}

    for schema_file in schema_files:
        schema = _load_yaml(schema_file)
        for node in _nodes(schema):
            kind = f"{node.get('namespace')}{node.get('name')}"
            if kind in definitions:
                definitions[kind].append(schema_file)

    assert definitions == {
        "NetworkFabric": ["schemas/logical_design.yml"],
        "NetworkPod": ["schemas/logical_design.yml"],
    }


def test_legacy_ipam_prefix_roles_remain_available_during_migration() -> None:
    assert {
        "supernet",
        "pod_super_spine_spine",
        "pod_leaf_spine",
        "loopback",
        "loopback-vtep",
        "technical",
        "management",
        "backfill",
    }.issubset(_ipam_prefix_role_choices())


def test_ipam_prefix_role_choices_include_new_fabric_pool_roles() -> None:
    assert {
        "fabric_supernet",
        "fabric_point_to_point",
        "dci",
    }.issubset(_ipam_prefix_role_choices())


def test_ipam_prefix_role_choices_include_mlag_pool_roles() -> None:
    assert {"mlag", "mlag_peering"}.issubset(_ipam_prefix_role_choices())


def test_network_fabric_fabric_ip_pools_relationship_shape() -> None:
    fabric = _node(_load_yaml("schemas/logical_design.yml"), "Network", "Fabric")
    fabric_ip_pools = _relationships(fabric)["fabric_ip_pools"]

    assert fabric_ip_pools == {
        "name": "fabric_ip_pools",
        "label": "Fabric IP Pools",
        "peer": "CoreResourcePool",
        "branch": "aware",
        "kind": "Attribute",
        "cardinality": "many",
        "optional": True,
        "identifier": "fabric__ip_pools",
        "description": "Role-driven fabric-scope IP pool collection; legacy pool relationships remain as migration fallback.",
        "order_weight": 8050,
    }


def test_network_pod_pod_ip_pools_relationship_shape() -> None:
    pod = _extension_node(_load_yaml("schemas/l3ls_extensions.yml"), "NetworkPod")
    pod_ip_pools = _relationships(pod)["pod_ip_pools"]

    assert pod_ip_pools == {
        "name": "pod_ip_pools",
        "label": "Pod IP Pools",
        "peer": "CoreResourcePool",
        "kind": "Attribute",
        "cardinality": "many",
        "optional": True,
        "identifier": "pod__ip_pools",
        "description": "Role-driven pod-scope IP pool collection for loopback, VTEP, uplink, and MLAG pools.",
        "order_weight": 7950,
    }


def test_ipam_prefix_display_label_includes_role_context() -> None:
    prefix = _node(_load_yaml("schemas/base/ipam.yml"), "Ipam", "Prefix")

    assert prefix["display_label"] == "{{ prefix__value }} ({{ role__value }})"


def test_legacy_fabric_pool_relationships_remain_optional_for_migration() -> None:
    logical_fabric = _node(_load_yaml("schemas/logical_design.yml"), "Network", "Fabric")
    logical_relationships = _relationships(logical_fabric)
    l3ls_fabric = _extension_node(_load_yaml("schemas/l3ls_extensions.yml"), "NetworkFabric")
    l3ls_relationships = _relationships(l3ls_fabric)
    dci_fabric = _extension_node(_load_yaml("schemas/dci.yml"), "NetworkFabric")
    dci_relationships = _relationships(dci_fabric)

    assert logical_relationships["mgmt_pool"]["optional"] is True
    assert l3ls_relationships["uplink_pool"]["optional"] is True
    assert l3ls_relationships["vtep_pool"]["optional"] is True
    assert l3ls_relationships["loopback_pool"]["optional"] is True
    assert dci_relationships["dci_pool"]["optional"] is True


def test_legacy_pod_mlag_relationships_remain_optional_for_migration() -> None:
    pod = _extension_node(_load_yaml("schemas/l3ls_extensions.yml"), "NetworkPod")
    relationships = _relationships(pod)

    assert relationships["mlag_peer_pool"]["optional"] is True
    assert relationships["mlag_peer_pool"]["description"] == (
        "Legacy MLAG peer-link pool. Prefer NetworkPod.pod_ip_pools with role mlag."
    )
    assert relationships["mlag_l3_pool"]["optional"] is True
    assert relationships["mlag_l3_pool"]["description"] == (
        "Legacy MLAG L3 peering pool. Prefer NetworkPod.pod_ip_pools with role mlag_peering."
    )
