from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).parents[2]


def _load_yaml(path: str) -> dict[str, Any]:
    with (REPO_ROOT / path).open() as fh:
        return yaml.safe_load(fh)


def _extension_node(schema: dict[str, Any], kind: str) -> dict[str, Any]:
    for node in schema.get("extensions", {}).get("nodes", []):
        if node["kind"] == kind:
            return node
    raise AssertionError(f"{kind} extension not found")


def _node(schema: dict[str, Any], namespace: str, name: str) -> dict[str, Any]:
    for node in schema.get("nodes", []):
        if node["namespace"] == namespace and node["name"] == name:
            return node
    raise AssertionError(f"{namespace}{name} node not found")


def _attrs(node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {attr["name"]: attr for attr in node.get("attributes", [])}


def _relationships(node: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rel["name"]: rel for rel in node.get("relationships", [])}


def test_device_role_choices_keep_existing_values_and_add_border_leaf() -> None:
    schema = _load_yaml("schemas/dcim_extensions.yml")
    device = _extension_node(schema, "DcimDevice")
    role = _attrs(device)["role"]

    choices = {choice["name"]: choice.get("label") for choice in role["choices"]}

    assert {"super_spine", "spine", "leaf", "l2leaf"}.issubset(choices)
    assert choices["border_leaf"] == "Border Leaf"


def test_network_link_reuses_dcim_connector_physical_endpoint_behavior() -> None:
    dcim_schema = _load_yaml("schemas/dcim_extensions.yml")
    network_link = _node(dcim_schema, "Network", "Link")

    assert "DcimConnector" in network_link["inherit_from"]
    assert network_link["include_in_menu"] is False
    assert network_link["human_friendly_id"] == ["name__value"]
    assert network_link["display_label"] == "name__value"


def test_network_link_role_supports_dci_choice_and_stays_optional() -> None:
    network_link = _node(_load_yaml("schemas/dcim_extensions.yml"), "Network", "Link")
    role = _attrs(network_link)["role"]

    choices = {choice["name"]: choice.get("label") for choice in role["choices"]}

    assert role["kind"] == "Dropdown"
    assert role["optional"] is True
    assert choices["dci"] == "DCI"


def test_interface_role_choices_include_peering_for_dci_endpoints() -> None:
    interface = _extension_node(_load_yaml("schemas/dcim_extensions.yml"), "DcimInterface")
    role = _attrs(interface)["role"]

    choices = {choice["name"]: choice.get("label") for choice in role["choices"]}

    assert {"server", "peering", "mlag_peer"}.issubset(choices)
    assert choices["peering"] == "Peering"


def test_network_link_defines_only_allowed_direct_dci_attributes() -> None:
    network_link = _node(_load_yaml("schemas/dcim_extensions.yml"), "Network", "Link")
    attrs = _attrs(network_link)

    assert set(attrs) == {"role", "include_in_underlay_protocol"}
    assert attrs["include_in_underlay_protocol"]["kind"] == "Boolean"
    assert attrs["include_in_underlay_protocol"]["default_value"] is True


def test_network_link_has_no_prohibited_direct_dci_fields() -> None:
    network_link = _node(_load_yaml("schemas/dcim_extensions.yml"), "Network", "Link")
    direct_fields = set(_attrs(network_link)) | set(_relationships(network_link))

    prohibited = {
        "enabled",
        "endpoint_a",
        "endpoint_b",
        "endpoint_1",
        "endpoint_2",
        "endpoint_1_bgp_asn",
        "endpoint_2_bgp_asn",
        "subnet",
        "p2p_pool",
        "p2p_link_id",
        "endpoint_ip",
        "endpoint_description",
        "speed",
        "bfd",
        "mtu",
        "routing_protocol",
        "external_network",
        "evpn_gateway",
    }

    assert direct_fields.isdisjoint(prohibited)


def test_network_fabric_dci_pool_is_optional_core_prefix_pool_relationship() -> None:
    fabric = _extension_node(_load_yaml("schemas/dci.yml"), "NetworkFabric")
    dci_pool = _relationships(fabric)["dci_pool"]

    assert dci_pool == {
        "name": "dci_pool",
        "label": "DCI IP Pool",
        "peer": "CoreIPPrefixPool",
        "kind": "Attribute",
        "cardinality": "one",
        "optional": True,
        "identifier": "fabric__dci_pool",
        "description": "Legacy DCI prefix pool. Prefer NetworkFabric.fabric_ip_pools with role dci.",
        "order_weight": 10700,
    }


def test_standalone_network_dci_link_schema_is_absent() -> None:
    stale_name = "Dci" + "Link"
    for schema_path in ("schemas/dci.yml", "schemas/dcim_extensions.yml"):
        schema = _load_yaml(schema_path)
        nodes = schema.get("nodes", [])
        assert not any(node["namespace"] == "Network" and node["name"] == stale_name for node in nodes)


def test_dci_links_menu_not_exposed_and_network_link_discovery_remains() -> None:
    menu = _load_yaml("menus/menu.yml")
    device_children = next(item for item in menu["spec"]["data"] if item["name"] == "DeviceMenu")["children"]["data"]

    stale_kind = "Network" + "Dci" + "Link"
    assert not any(item.get("kind") == stale_kind for item in device_children)
    network_link_menu = next(item for item in device_children if item.get("kind") == "NetworkLink")
    assert network_link_menu["label"] == "Connections"
