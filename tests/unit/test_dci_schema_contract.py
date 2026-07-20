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


def test_network_dci_link_reuses_dcim_connector_physical_endpoint_behavior() -> None:
    dcim_schema = _load_yaml("schemas/dcim_extensions.yml")
    dci_schema = _load_yaml("schemas/dci.yml")

    network_link = _node(dcim_schema, "Network", "Link")
    dci_link = _node(dci_schema, "Network", "DciLink")

    assert "DcimConnector" in network_link["inherit_from"]
    assert "DcimConnector" in dci_link["inherit_from"]
    assert dci_link["include_in_menu"] is False
    assert dci_link["human_friendly_id"] == ["name__value"]
    assert dci_link["display_label"] == "name__value"


def test_network_dci_link_defines_only_allowed_direct_dci_attributes() -> None:
    dci_link = _node(_load_yaml("schemas/dci.yml"), "Network", "DciLink")
    attrs = _attrs(dci_link)

    assert set(attrs) == {"include_in_underlay_protocol", "endpoint_1_bgp_asn", "endpoint_2_bgp_asn"}
    assert attrs["include_in_underlay_protocol"]["kind"] == "Boolean"
    assert attrs["include_in_underlay_protocol"]["default_value"] is True
    assert attrs["endpoint_1_bgp_asn"]["kind"] == "Number"
    assert attrs["endpoint_2_bgp_asn"]["kind"] == "Number"


def test_network_dci_link_has_no_prohibited_direct_fields() -> None:
    dci_link = _node(_load_yaml("schemas/dci.yml"), "Network", "DciLink")
    direct_fields = set(_attrs(dci_link)) | set(_relationships(dci_link))

    prohibited = {
        "enabled",
        "endpoint_a",
        "endpoint_b",
        "endpoint_1",
        "endpoint_2",
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
        "description": "IP prefix pool used to allocate /31 point-to-point prefixes for DCI links.",
        "order_weight": 10700,
    }


def test_dci_link_uniqueness_constraints_use_infrahub_constraint_syntax() -> None:
    dci_link = _node(_load_yaml("schemas/dci.yml"), "Network", "DciLink")

    assert ["name__value"] in dci_link["uniqueness_constraints"]
    for constraint in dci_link["uniqueness_constraints"]:
        for field in constraint:
            if field == "name__value":
                continue
            assert "__value" not in field


def test_dci_links_menu_points_to_network_dci_link() -> None:
    menu = _load_yaml("menus/menu.yml")
    device_children = next(item for item in menu["spec"]["data"] if item["name"] == "DeviceMenu")["children"]["data"]
    dci_menu = next(item for item in device_children if item["name"] == "DciLinks")

    assert dci_menu["label"] == "DCI Links"
    assert dci_menu["kind"] == "NetworkDciLink"
