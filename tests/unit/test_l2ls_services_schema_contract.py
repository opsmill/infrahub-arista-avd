"""Schema contract tests for L2LS Fabric Example Conformance (feature 001).

These tests assert the schema surface that lets the AVD ``l2ls-fabric`` example be
modeled as pure Layer-2, tag-scoped services with access/edge switchport intent:

- C2: ``Evpn.Tenant.mac_vrf_vni_base`` is optional (overlay-free tenants).
- C3: ``Evpn.L2Vlan`` carries ``rack_tags``/``avd_tags`` scoping (mirrors ``Evpn.Svi``).
- C4: the Layer-2 interface exposes edge PortFast intent for host access ports.

They parse the schema YAML directly (not the loaded graph) so they run as fast
unit tests. See specs/001-l2ls-example-conformance/contracts/schema-contract.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_EVPN_SERVICES = _REPO_ROOT / "schemas" / "evpn" / "evpn_services.yml"
_BASE_DCIM = _REPO_ROOT / "schemas" / "base" / "dcim.yml"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _node(path: Path, namespace: str, name: str) -> dict[str, Any]:
    doc = _load_yaml(path)
    for node in doc.get("nodes", []):
        if node.get("namespace") == namespace and node.get("name") == name:
            return node
    msg = f"Node {namespace}{name!r} not found in {path}"
    raise AssertionError(msg)


def _generic(path: Path, namespace: str, name: str) -> dict[str, Any]:
    doc = _load_yaml(path)
    for gen in doc.get("generics", []):
        if gen.get("namespace") == namespace and gen.get("name") == name:
            return gen
    msg = f"Generic {namespace}{name!r} not found in {path}"
    raise AssertionError(msg)


def _attribute(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    for attr in node.get("attributes", []):
        if attr.get("name") == name:
            return attr
    return None


def _relationship(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    for rel in node.get("relationships", []):
        if rel.get("name") == name:
            return rel
    return None


def _choice_names(attribute: dict[str, Any]) -> set[str]:
    return {choice["name"] for choice in attribute.get("choices", [])}


# --- C2: overlay-free tenant --------------------------------------------------


def test_tenant_mac_vrf_vni_base_is_optional() -> None:
    tenant = _node(_EVPN_SERVICES, "Evpn", "Tenant")
    attr = _attribute(tenant, "mac_vrf_vni_base")
    assert attr is not None, "Evpn.Tenant.mac_vrf_vni_base attribute is missing"
    assert attr.get("optional") is True, "mac_vrf_vni_base must be optional for overlay-free tenants"


# --- C3: L2 VLAN tag scoping (mirrors Evpn.Svi) -------------------------------


def test_l2vlan_has_rack_tags_scoping() -> None:
    l2vlan = _node(_EVPN_SERVICES, "Evpn", "L2Vlan")
    rel = _relationship(l2vlan, "rack_tags")
    assert rel is not None, "Evpn.L2Vlan.rack_tags relationship is missing"
    assert rel.get("peer") == "LocationRack"
    assert rel.get("cardinality") == "many"
    assert rel.get("optional") is True


def test_l2vlan_has_avd_tags_scoping() -> None:
    l2vlan = _node(_EVPN_SERVICES, "Evpn", "L2Vlan")
    rel = _relationship(l2vlan, "avd_tags")
    assert rel is not None, "Evpn.L2Vlan.avd_tags relationship is missing"
    assert rel.get("peer") == "AvdTag"
    assert rel.get("cardinality") == "many"
    assert rel.get("optional") is True


def test_l2vlan_tag_scoping_mirrors_svi() -> None:
    """The L2 VLAN tag relationships mirror the SVI shape (same peers)."""
    svi = _node(_EVPN_SERVICES, "Evpn", "Svi")
    l2vlan = _node(_EVPN_SERVICES, "Evpn", "L2Vlan")
    for rel_name, peer in (("rack_tags", "LocationRack"), ("avd_tags", "AvdTag")):
        svi_rel = _relationship(svi, rel_name)
        l2_rel = _relationship(l2vlan, rel_name)
        assert svi_rel is not None and l2_rel is not None
        assert svi_rel.get("peer") == l2_rel.get("peer") == peer


# --- C4: access/edge switchport intent ---------------------------------------


def test_layer2_interface_exposes_portfast() -> None:
    layer2 = _generic(_BASE_DCIM, "Interface", "Layer2")
    attr = _attribute(layer2, "spanning_tree_portfast")
    assert attr is not None, "Interface.Layer2.spanning_tree_portfast attribute is missing"
    assert attr.get("optional") is True
    assert "edge" in _choice_names(attr)


def test_layer2_interface_mode_supports_access_and_trunk() -> None:
    layer2 = _generic(_BASE_DCIM, "Interface", "Layer2")
    attr = _attribute(layer2, "l2_mode")
    assert attr is not None, "Interface.Layer2.l2_mode attribute is missing"
    assert {"access", "trunk"} <= _choice_names(attr)
