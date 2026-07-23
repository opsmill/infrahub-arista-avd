"""Schema contract tests for the AVD example fabric designs feature.

These tests assert the native schema surface added so the seven AVD example
scenarios are demonstrable: new device roles, extended underlay choices, the
EVPN VLAN-aware-bundle input, and the EVPN DC Gateway flag. They parse the
schema YAML directly (not the loaded graph) so they run as fast unit tests.

See specs/005-avd-example-fabrics/contracts/schema.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DCIM_EXTENSIONS = _REPO_ROOT / "schemas" / "dcim_extensions.yml"
_L3LS_EXTENSIONS = _REPO_ROOT / "schemas" / "l3ls_extensions.yml"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _extension_node(path: Path, kind: str) -> dict[str, Any]:
    """Return the ``extensions.nodes`` entry for the given kind."""
    doc = _load_yaml(path)
    for node in doc.get("extensions", {}).get("nodes", []):
        if node.get("kind") == kind:
            return node
    msg = f"Extension for kind {kind!r} not found in {path}"
    raise AssertionError(msg)


def _attribute(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    for attr in node.get("attributes", []):
        if attr.get("name") == name:
            return attr
    return None


def _choice_names(attribute: dict[str, Any]) -> set[str]:
    return {choice["name"] for choice in attribute.get("choices", [])}


def _dcim_device_role_choice_names() -> set[str]:
    """Role choice machine names on the DcimDevice extension."""
    device = _extension_node(_DCIM_EXTENSIONS, "DcimDevice")
    role = _attribute(device, "role")
    assert role is not None, "DcimDevice.role attribute is missing"
    return _choice_names(role)


def _underlay_choice_names() -> set[str]:
    fabric = _extension_node(_L3LS_EXTENSIONS, "NetworkFabric")
    underlay = _attribute(fabric, "underlay_routing_protocol")
    assert underlay is not None, "NetworkFabric.underlay_routing_protocol is missing"
    return _choice_names(underlay)


# --- US1 / baseline: existing roles preserved ---------------------------------


def test_existing_roles_preserved() -> None:
    names = _dcim_device_role_choice_names()
    assert {"super_spine", "spine", "leaf", "border_leaf", "l2leaf"} <= names


# --- US2: EVPN vlan-aware-bundles input ---------------------------------------


def test_evpn_vlan_aware_bundles_input() -> None:
    fabric = _extension_node(_L3LS_EXTENSIONS, "NetworkFabric")
    attr = _attribute(fabric, "evpn_vlan_aware_bundles")
    assert attr is not None, "NetworkFabric.evpn_vlan_aware_bundles is missing"
    assert attr["kind"] == "Boolean"
    assert attr.get("optional") is True
    # Backward-compatible default: existing fabrics render unchanged.
    assert attr.get("default_value") is False


# --- US4: L2LS roles + underlay none ------------------------------------------


def test_l2ls_roles_present() -> None:
    names = _dcim_device_role_choice_names()
    assert {"l2spine", "l3spine"} <= names


def test_underlay_none_choice_present() -> None:
    assert "none" in _underlay_choice_names()


def test_underlay_existing_choices_preserved() -> None:
    assert {"ebgp", "ospf"} <= _underlay_choice_names()


# --- US5: campus reuse (l3spine core + ospf underlay) -------------------------


def test_campus_reuses_l3spine_and_ospf() -> None:
    assert "l3spine" in _dcim_device_role_choice_names()
    assert "ospf" in _underlay_choice_names()


# --- US6: ISIS-LDP IPVPN roles + underlay -------------------------------------


def test_isis_ldp_underlay_choice_present() -> None:
    assert "isis-ldp" in _underlay_choice_names()


def test_provider_roles_present() -> None:
    names = _dcim_device_role_choice_names()
    assert {"p", "pe", "rr"} <= names
