#!/usr/bin/env python3
"""Feature-level comparison of rendered EOS configs against AVD's published examples.

The AVD project ships ``intended/configs/*.cfg`` for each example design
(single-dc-l3ls, dual-dc-l3ls, l2ls-fabric, campus-fabric, isis-ldp-ipvpn,
cv-pathfinder, ...). This repo renders EOS configs from Infrahub intent, and we
want to show that a rendered config is *structurally equivalent* to the AVD
example — i.e. it grows the same EOS feature sections (``router bgp``, ``vlan``,
``mlag configuration``, ``router isis``, ``mpls ldp``,
``router adaptive-virtual-topology``, ``dot1x``, ``vrf instance``, ...).

Byte-for-byte identity is intentionally NOT the goal: Infrahub allocates its own
addressing, hostnames, ASNs, and node ids, so those always differ from AVD's
static example inventories. This tool therefore normalises addressing-like tokens
away and compares at the feature-section level, reporting sections that appear in
both, only in ours, or only in the AVD example. That is the honest, repeatable
"does it match the example" check (issue #8).

Usage:
    # compare a single rendered config against an AVD example config
    python scripts/compare_avd_examples.py ours.cfg avd_example.cfg

    # compare two directories of *.cfg by matching basenames
    python scripts/compare_avd_examples.py rendered_dir/ avd_examples_dir/

    # run the built-in self-test (no inputs required)
    python scripts/compare_avd_examples.py --self-test

Fetch the AVD reference configs from the arista/avd repo, e.g.:
    ansible_collections/arista/avd/examples/<example>/intended/configs/*.cfg
(https://github.com/aristanetworks/avd).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Tokens that legitimately differ between our render and AVD's static examples;
# masked before comparison so they never show up as spurious differences.
_NORMALISERS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\b"), "<IP>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{2}[:.]){2,}[0-9a-fA-F]{2,4}\b"), "<MAC>"),
    (re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){2,}[0-9a-fA-F:]+\b"), "<IPV6>"),
    (re.compile(r"(?<=\basn )\d+"), "<ASN>"),
    (re.compile(r"(?<=\brouter bgp )\d+"), "<ASN>"),
    (re.compile(r"(?<=\bremote-as )\d+"), "<ASN>"),
    (re.compile(r"(?<=\blocal-as )\d+"), "<ASN>"),
]


def normalise_line(line: str) -> str:
    """Strip a config line of addressing-like tokens that are allowed to differ."""
    out = line.rstrip()
    for pattern, replacement in _NORMALISERS:
        out = pattern.sub(replacement, out)
    return out


def feature_sections(config: str) -> set[str]:
    """Return the set of top-level EOS feature sections present in a config.

    A feature section is introduced by a line at column 0 (no leading whitespace)
    that is not a comment. We keep the first two whitespace-delimited words so
    ``router bgp`` and ``router isis`` are distinct while ``interface Ethernet1``
    collapses to ``interface`` (a section family, not a per-object line).
    """
    sections: set[str] = set()
    for raw in config.splitlines():
        if not raw or raw[0].isspace() or raw.lstrip().startswith(("!", "#")):
            continue
        words = normalise_line(raw).split()
        if not words:
            continue
        # Single-object families collapse to their keyword; multi-word features keep two words.
        family_two_word = {"router", "mpls", "mlag", "spanning-tree", "vrf", "ip", "ipv6", "management"}
        key = f"{words[0]} {words[1]}" if words[0] in family_two_word and len(words) > 1 else words[0]
        sections.add(key)
    return sections


def compare_configs(ours: str, theirs: str) -> dict[str, set[str]]:
    """Compare two configs at the feature-section level."""
    ours_sections = feature_sections(ours)
    theirs_sections = feature_sections(theirs)
    return {
        "shared": ours_sections & theirs_sections,
        "only_ours": ours_sections - theirs_sections,
        "only_theirs": theirs_sections - ours_sections,
    }


def _format_report(name: str, result: dict[str, set[str]]) -> str:
    lines = [
        f"### {name}",
        f"  shared features ({len(result['shared'])}): {', '.join(sorted(result['shared'])) or '—'}",
        f"  only in AVD example: {', '.join(sorted(result['only_theirs'])) or '—'}",
        f"  only in our render:  {', '.join(sorted(result['only_ours'])) or '—'}",
    ]
    return "\n".join(lines)


def _iter_pairs(ours: Path, theirs: Path) -> list[tuple[str, Path, Path]]:
    if ours.is_file() and theirs.is_file():
        return [(ours.name, ours, theirs)]
    pairs: list[tuple[str, Path, Path]] = []
    theirs_by_name = {p.name: p for p in theirs.glob("*.cfg")}
    for ours_file in sorted(ours.glob("*.cfg")):
        match = theirs_by_name.get(ours_file.name)
        if match:
            pairs.append((ours_file.name, ours_file, match))
    return pairs


def _self_test() -> int:
    ours = "router bgp 65001\n   neighbor 10.0.0.1 remote-as 65002\nvlan 10\nmlag configuration\n   peer-link Port-Channel1\n"
    theirs = "router bgp 65500\n   neighbor 172.16.0.1 remote-as 65501\nvlan 10\nspanning-tree mode mstp\n"
    result = compare_configs(ours, theirs)
    assert result["shared"] == {"router bgp", "vlan"}, result["shared"]
    assert result["only_ours"] == {"mlag configuration"}, result["only_ours"]
    assert result["only_theirs"] == {"spanning-tree mode"}, result["only_theirs"]
    # Addressing/ASN differences must NOT create spurious section differences.
    assert normalise_line("   neighbor 10.0.0.1 remote-as 65002") == normalise_line(
        "   neighbor 172.16.9.9 remote-as 40000"
    )
    print("self-test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ours", nargs="?", help="Rendered config file or directory of *.cfg")
    parser.add_argument("theirs", nargs="?", help="AVD example config file or directory of *.cfg")
    parser.add_argument("--self-test", action="store_true", help="Run the built-in self-test and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.ours or not args.theirs:
        parser.error("provide OURS and THEIRS paths, or --self-test")

    ours_path, theirs_path = Path(args.ours), Path(args.theirs)
    pairs = _iter_pairs(ours_path, theirs_path)
    if not pairs:
        print("No matching *.cfg pairs found (match is by basename).", file=sys.stderr)
        return 1

    any_divergence = False
    for name, ours_file, theirs_file in pairs:
        result = compare_configs(ours_file.read_text(), theirs_file.read_text())
        print(_format_report(name, result))
        if result["only_theirs"]:
            any_divergence = True
    print(
        "\nNote: byte-identity is not expected — Infrahub allocates its own addressing, "
        "hostnames and ASNs. 'only in AVD example' sections are the real fidelity gaps to close."
    )
    return 1 if any_divergence else 0


if __name__ == "__main__":
    raise SystemExit(main())
