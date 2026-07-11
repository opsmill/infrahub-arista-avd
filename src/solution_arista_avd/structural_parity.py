"""Structural comparison helpers for generated EOS configurations.

The verifier intentionally ignores literal values and compares normalized
command shapes. This catches missing configuration families while tolerating
seed-data differences such as hostnames, IP addresses, ASNs, VLANs, and VNIs.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pyavd

VALUE = "<value>"
IFACE = "<interface>"
NUMBER = "<number>"
IP = "<ip>"
MAC = "<mac>"
NAME = "<name>"
VRF = "<vrf>"

_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b")
_MAC_RE = re.compile(r"\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b|\b[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\b")
_ESI_RE = re.compile(r"\b[0-9a-fA-F]{4}(?::[0-9a-fA-F]{4}){4}\b")
_INTERFACE_RE = re.compile(r"\b(?:Ethernet|Management|Loopback|Vlan|Port-Channel)\d+(?:/\d+)*(?:-\d+(?:/\d+)*)?\b")
_ASN_PAIR_RE = re.compile(r"\b\d{1,10}:\d{1,10}\b")
_NUMBER_RE = re.compile(r"\b\d+\b")


@dataclass(frozen=True)
class StructuralParityResult:
    """Result for a single generated/intended config comparison."""

    name: str
    missing: Counter[str]
    unexpected: Counter[str]

    @property
    def ok(self) -> bool:
        return not self.missing


def normalize_config(config: str) -> Counter[str]:
    """Normalize an EOS CLI config into a multiset of structural command shapes."""
    shapes: Counter[str] = Counter()
    context: list[tuple[int, str]] = []

    for raw_line in config.splitlines():
        if not raw_line.strip() or raw_line.strip() in {"!", "end"}:
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        command = _normalize_command(raw_line.strip())
        while context and context[-1][0] >= indent:
            context.pop()

        path = tuple(ctx_command for _, ctx_command in context)
        shapes[" > ".join((*path, command))] += 1
        context.append((indent, command))

    return shapes


def compare_configs(name: str, generated: str, intended: str) -> StructuralParityResult:
    """Compare generated CLI config against intended CLI config by command shape."""
    generated_shapes = normalize_config(generated)
    intended_shapes = normalize_config(intended)
    missing = intended_shapes - generated_shapes
    unexpected = generated_shapes - intended_shapes
    return StructuralParityResult(name=name, missing=missing, unexpected=unexpected)


def compare_config_dirs(generated_dir: Path, intended_dir: Path) -> list[StructuralParityResult]:
    """Compare matching ``*.cfg`` files in two directories."""
    results: list[StructuralParityResult] = []
    for intended_path in sorted(intended_dir.glob("*.cfg")):
        generated_path = generated_dir / intended_path.name
        if not generated_path.exists():
            results.append(StructuralParityResult(intended_path.name, Counter({"<missing-file>": 1}), Counter()))
            continue
        results.append(compare_configs(intended_path.name, generated_path.read_text(), intended_path.read_text()))
    return results


def render_structured_configs(structured_config_dir: Path, output_dir: Path) -> None:
    """Render JSON structured config files to EOS CLI config files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for structured_path in sorted(structured_config_dir.glob("*.json")):
        structured_config = json.loads(structured_path.read_text())
        output_path = output_dir / f"{structured_path.stem}.cfg"
        output_path.write_text(pyavd.get_device_config(structured_config))


def _normalize_command(command: str) -> str:
    command = _normalize_descriptions(command)
    command = _normalize_vrf_names(command)
    command = _IPV4_RE.sub(IP, command)
    command = _MAC_RE.sub(MAC, command)
    command = _ESI_RE.sub(VALUE, command)
    command = _INTERFACE_RE.sub(IFACE, command)
    command = _ASN_PAIR_RE.sub(f"{NUMBER}:{NUMBER}", command)
    command = _NUMBER_RE.sub(NUMBER, command)
    return re.sub(r"\s+", " ", command).strip()


def _normalize_descriptions(command: str) -> str:
    if command.startswith("description "):
        return f"description {VALUE}"
    if " description " in command:
        return re.sub(r" description .+$", f" description {VALUE}", command)
    if command.startswith("hostname "):
        return f"hostname {NAME}"
    if command.startswith("username "):
        return re.sub(r"^username \S+", f"username {NAME}", command)
    if command.startswith("alias "):
        return "alias"
    if command.startswith("exec /usr/bin/TerminAttr "):
        return "exec /usr/bin/TerminAttr"
    return command


def _normalize_vrf_names(command: str) -> str:
    command = re.sub(r"^(no )?ip routing vrf \S+", rf"\1ip routing vrf {VRF}", command)
    command = re.sub(r"^ip route vrf \S+", f"ip route vrf {VRF}", command)
    command = re.sub(r"^ip (?:domain lookup|name-server) vrf \S+", lambda match: match.group(0).rsplit(" ", 1)[0] + f" {VRF}", command)
    command = re.sub(r"^ntp (?:local-interface|server) vrf \S+", lambda match: match.group(0).rsplit(" ", 1)[0] + f" {VRF}", command)
    command = re.sub(r"^vrf instance \S+", f"vrf instance {VRF}", command)
    command = re.sub(r"^vrf \S+", f"vrf {VRF}", command)
    return re.sub(r"^vxlan vrf \S+", f"vxlan vrf {VRF}", command)


def _format_results(results: list[StructuralParityResult], include_unexpected: bool) -> str:
    lines: list[str] = []
    for result in results:
        if result.ok and (not include_unexpected or not result.unexpected):
            continue
        lines.append(f"{result.name}:")
        for shape, count in result.missing.most_common():
            lines.append(f"  missing x{count}: {shape}")
        if include_unexpected:
            for shape, count in result.unexpected.most_common():
                lines.append(f"  unexpected x{count}: {shape}")
    return "\n".join(lines)


async def _download_structured_configs(output_dir: Path) -> None:
    from infrahub_sdk import InfrahubClient

    from solution_arista_avd.protocols import AvdStructuredConfigFile

    client = InfrahubClient()
    files = await client.all(kind=AvdStructuredConfigFile)
    await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
    for file_obj in files:
        content = await file_obj.download_file()
        name = getattr(file_obj, "name", None)
        filename = name.value if name and name.value else f"{file_obj.id}.json"
        output_path = output_dir / filename
        await asyncio.to_thread(output_path.write_bytes, content if isinstance(content, bytes) else content.encode())


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Infrahub AVD structural parity against intended configs.")
    parser.add_argument("--intended", type=Path, default=Path("../labs/infrahub-avd/avd/intended/configs"))
    parser.add_argument("--structured", type=Path, help="Directory containing structured-config JSON artifacts.")
    parser.add_argument("--generated", type=Path, default=Path(".tmp/avd-structural-parity/generated-configs"))
    parser.add_argument("--download", action="store_true", help="Download AvdStructuredConfigFile artifacts first.")
    parser.add_argument("--show-unexpected", action="store_true", help="Show extra generated command shapes.")
    args = parser.parse_args()

    structured_dir = args.structured or Path(".tmp/avd-structural-parity/structured-configs")
    if args.download:
        asyncio.run(_download_structured_configs(structured_dir))

    if structured_dir.exists():
        render_structured_configs(structured_dir, args.generated)

    results = compare_config_dirs(args.generated, args.intended)
    report = _format_results(results, args.show_unexpected)
    if report:
        print(report)
        return 1
    print(f"Structural parity passed for {len(results)} configs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
