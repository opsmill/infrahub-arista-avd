from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TEMPLATE_FILES = [
    _REPO_ROOT / "objects" / "06_device_template.yml",
    _REPO_ROOT / "objects" / "06a_fabric_c_device_templates.yml",
]


def _documents(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [doc for doc in yaml.safe_load_all(handle) if doc]


def _interface_entries(template: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    interfaces = template.get("interfaces")
    if not isinstance(interfaces, dict) or interfaces.get("kind") != kind:
        return []
    return interfaces.get("data", [])


def test_seeded_loopback0_templates_are_virtual_not_physical() -> None:
    physical_loopbacks: list[str] = []
    virtual_loopbacks: list[str] = []

    for path in _TEMPLATE_FILES:
        for doc in _documents(path):
            if doc.get("spec", {}).get("kind") != "TemplateDcimDevice":
                continue
            for template in doc["spec"].get("data", []):
                physical_loopbacks.extend(
                    f"{path.name}:{template['template_name']}"
                    for entry in _interface_entries(template, "TemplateInterfacePhysical")
                    if entry.get("name") == "Loopback0"
                )
                virtual_loopbacks.extend(
                    f"{path.name}:{template['template_name']}"
                    for entry in _interface_entries(template, "TemplateInterfaceVirtual")
                    if entry.get("name") == "Loopback0"
                )

    assert physical_loopbacks == []
    assert virtual_loopbacks
