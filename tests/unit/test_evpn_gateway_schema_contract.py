"""Schema contract tests for EVPN Gateway intent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path("schemas/evpn/evpn_gateway.yml")
DCIM_EXTENSIONS_PATH = Path("schemas/dcim_extensions.yml")
LOGICAL_DESIGN_PATH = Path("schemas/logical_design.yml")


def _schema() -> dict[str, Any]:
    return yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))


def _node(schema: dict[str, Any], name: str) -> dict[str, Any]:
    return next(node for node in schema["nodes"] if node["name"] == name and node["namespace"] == "Evpn")


def _extension(schema: dict[str, Any], kind: str) -> dict[str, Any]:
    return next(node for node in schema["extensions"]["nodes"] if node["kind"] == kind)


def _node_kind(schema: dict[str, Any], namespace: str, name: str) -> dict[str, Any]:
    return next(node for node in schema["nodes"] if node["namespace"] == namespace and node["name"] == name)


def _by_name(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in items}


def test_evpn_gateway_schema_defines_required_nodes() -> None:
    schema = _schema()
    assert schema["version"] == "1.0"

    domain = _node(schema, "Domain")
    gateway_group = _node(schema, "GatewayGroup")

    assert domain["label"] == "EVPN Domain"
    assert domain["include_in_menu"] is False
    assert gateway_group["label"] == "EVPN Gateway Group"
    assert gateway_group["include_in_menu"] is False
    assert all(node["name"] != "Gateway" for node in schema["nodes"])


def test_domain_contract() -> None:
    domain = _node(_schema(), "Domain")
    attrs = _by_name(domain["attributes"])
    rels = _by_name(domain["relationships"])

    assert attrs["name"]["kind"] == "Text"
    assert attrs["domain_id"]["kind"] == "Text"
    assert "fabric_name" not in attrs
    assert "unique" not in attrs["domain_id"]
    assert attrs["description"]["optional"] is True
    assert rels["fabric"]["peer"] == "NetworkFabric"
    assert rels["fabric"]["cardinality"] == "one"
    assert rels["fabric"]["kind"] == "Parent"
    assert rels["fabric"]["optional"] is False
    assert rels["fabric"]["identifier"] == "fabric__evpn_domains"
    assert rels["pods"]["peer"] == "NetworkPod"
    assert rels["pods"]["identifier"] == "evpn_domain__pods"
    assert rels["remote_gateway_groups"]["peer"] == "EvpnGatewayGroup"
    assert rels["remote_gateway_groups"]["identifier"] == "evpn_gateway_group__remote_domain"
    assert list(domain["uniqueness_constraints"]) == [
        ["fabric", "domain_id__value"],
        ["fabric", "name__value"],
    ]


def test_gateway_contract_and_all_active_only_choice() -> None:
    gateway = _node(_schema(), "GatewayGroup")
    attrs = _by_name(gateway["attributes"])
    rels = _by_name(gateway["relationships"])

    assert attrs["resiliency_model"]["kind"] == "Dropdown"
    assert attrs["resiliency_model"]["default_value"] == "all_active_multihoming"
    assert attrs["resiliency_model"]["choices"] == [
        {"name": "all_active_multihoming", "label": "All-Active Multihoming"}
    ]
    assert "mlag" not in {choice["name"] for choice in attrs["resiliency_model"]["choices"]}
    assert "anycast_ip" not in {choice["name"] for choice in attrs["resiliency_model"]["choices"]}

    for attr_name in (
        "evpn_l2_enabled",
        "evpn_l3_enabled",
        "evpn_l3_inter_domain",
        "d_path_enabled",
        "all_active_multihoming_enabled",
    ):
        assert attrs[attr_name]["kind"] == "Boolean"
        assert attrs[attr_name]["default_value"] is True

    assert attrs["ethernet_segment_identifier"]["kind"] == "Text"
    assert attrs["ethernet_segment_rt_import"]["kind"] == "Text"
    assert "local_domain" not in rels
    assert rels["pod"]["peer"] == "NetworkPod"
    assert rels["pod"]["identifier"] == "pod__evpn_gateway_groups"
    assert rels["remote_domain"]["peer"] == "EvpnDomain"
    assert rels["remote_domain"]["identifier"] == "evpn_gateway_group__remote_domain"
    assert rels["members"]["peer"] == "DcimDevice"
    assert rels["members"]["identifier"] == "evpn_gateway_group__members"
    assert rels["members"]["optional"] is False
    assert gateway["uniqueness_constraints"] == [["pod", "name__value"]]


def test_inverse_relationship_extensions_are_additive() -> None:
    schema = _schema()
    fabric_rels = _by_name(_extension(schema, "NetworkFabric")["relationships"])
    pod_rels = _by_name(_extension(schema, "NetworkPod")["relationships"])
    device_rels = _by_name(_extension(schema, "DcimDevice")["relationships"])
    logical_schema = yaml.safe_load(LOGICAL_DESIGN_PATH.read_text(encoding="utf-8"))
    pod_base_rels = _by_name(_node_kind(logical_schema, "Network", "Pod")["relationships"])

    assert fabric_rels["evpn_domains"]["peer"] == "EvpnDomain"
    assert fabric_rels["evpn_domains"]["cardinality"] == "many"
    assert fabric_rels["evpn_domains"]["optional"] is True
    assert fabric_rels["evpn_domains"]["identifier"] == "fabric__evpn_domains"

    assert pod_base_rels["evpn_domain"]["peer"] == "EvpnDomain"
    assert pod_base_rels["evpn_domain"]["cardinality"] == "one"
    assert pod_base_rels["evpn_domain"]["optional"] is True
    assert pod_base_rels["evpn_domain"]["identifier"] == "evpn_domain__pods"
    assert pod_rels["evpn_gateway_groups"]["peer"] == "EvpnGatewayGroup"
    assert pod_rels["evpn_gateway_groups"]["identifier"] == "pod__evpn_gateway_groups"

    assert device_rels["evpn_gateway_group"]["peer"] == "EvpnGatewayGroup"
    assert device_rels["evpn_gateway_group"]["cardinality"] == "one"
    assert device_rels["evpn_gateway_group"]["optional"] is True
    assert device_rels["evpn_gateway_group"]["identifier"] == "evpn_gateway_group__members"


def test_display_metadata_is_human_friendly() -> None:
    schema = _schema()
    domain = _node(schema, "Domain")
    gateway = _node(schema, "GatewayGroup")

    assert domain["human_friendly_id"] == ["fabric__name__value", "domain_id__value"]
    assert "fabric__name__value" in domain["display_label"]
    assert "domain_id__value" in domain["display_label"]

    assert gateway["human_friendly_id"] == [
        "pod__name__value",
        "name__value",
    ]
    assert "pod__name__value" in gateway["display_label"]
    assert "remote_domain__domain_id__value" in gateway["display_label"]


def test_schema_does_not_add_display_only_local_domain_helpers() -> None:
    logical_schema = yaml.safe_load(LOGICAL_DESIGN_PATH.read_text(encoding="utf-8"))
    pod = _node_kind(logical_schema, "Network", "Pod")
    pod_attrs = _by_name(pod["attributes"])
    domain_attrs = _by_name(_node(_schema(), "Domain")["attributes"])

    assert "evpn_domain_id" not in pod_attrs
    assert "fabric_name" not in domain_attrs


def test_border_leaf_dependency_is_present_in_device_role_choices() -> None:
    schema = yaml.safe_load(DCIM_EXTENSIONS_PATH.read_text(encoding="utf-8"))
    dcim_device = next(node for node in schema["extensions"]["nodes"] if node["kind"] == "DcimDevice")
    role_attr = next(attr for attr in dcim_device["attributes"] if attr["name"] == "role")

    choices = {choice["name"]: choice.get("label") for choice in role_attr["choices"]}
    assert choices["border_leaf"] == "Border Leaf"
