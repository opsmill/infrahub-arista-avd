"""Menu contract tests for EVPN Gateway navigation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

MENU_PATH = Path("menus/menu.yml")
SCHEMA_DIR = Path("schemas")


def _menu() -> dict[str, Any]:
    return yaml.safe_load(MENU_PATH.read_text(encoding="utf-8"))


def _evpn_services_items() -> list[dict[str, Any]]:
    menu = _menu()
    evpn_menu = next(
        item for item in menu["spec"]["data"] if item["namespace"] == "Evpn" and item["name"] == "EvpnMenu"
    )
    return evpn_menu["children"]["data"]


def _schema_kinds() -> set[str]:
    kinds: set[str] = set()
    for schema_path in SCHEMA_DIR.rglob("*.yml"):
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
        for section in ("nodes", "generics"):
            kinds.update(f"{item['namespace']}{item['name']}" for item in schema.get(section, []) or [])
    return kinds


def _menu_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    for item in items:
        flattened.append(item)
        flattened.extend(_menu_items(item.get("children", {}).get("data", [])))
    return flattened


def test_domains_menu_item_exists_once_under_evpn_services() -> None:
    domain_items = [item for item in _evpn_services_items() if item.get("kind") == "EvpnDomain"]

    assert domain_items == [
        {
            "namespace": "Evpn",
            "name": "Domains",
            "label": "Domains",
            "kind": "EvpnDomain",
            "icon": "mdi:domain",
        }
    ]

    assert not any(item.get("kind") == "EvpnGatewayGroup" for item in _evpn_services_items())


def test_existing_evpn_services_items_are_preserved() -> None:
    items_by_kind = {item["kind"]: item["label"] for item in _evpn_services_items()}

    assert items_by_kind["EvpnTenant"] == "Tenants"
    assert items_by_kind["EvpnSvi"] == "SVIs"
    assert items_by_kind["EvpnL2Vlan"] == "L2 VLANs"
    assert items_by_kind["EvpnDomain"] == "Domains"


def test_menu_kind_references_exist_in_repository_schemas() -> None:
    schema_kinds = _schema_kinds()
    menu_kind_refs = {item["kind"] for item in _menu_items(_menu()["spec"]["data"]) if item.get("kind")}

    assert menu_kind_refs <= schema_kinds
    assert "EvpnDomain" in menu_kind_refs
    assert "EvpnGatewayGroup" not in menu_kind_refs
    assert "EvpnGateway" not in menu_kind_refs
