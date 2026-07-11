# ruff: noqa: INP001
"""Compare selected Infrahub seed objects with a live Infrahub instance.

The script compares the object fields that are explicitly present in the seed
YAML. It intentionally ignores generated reverse relationships and UUIDs so the
report stays focused on data that belongs in objects/*.yml.
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml
from infrahub_sdk import InfrahubClient
from infrahub_sdk.config import Config

QUERY = """
query SeedComparable {
  OrganizationManufacturer { edges { node { name { value } } } }
  DcimDeviceType { edges { node { name { value } manufacturer { node { name { value } } } } } }
  CoreStandardGroup { edges { node { name { value } } } }
  CoreAccountGroup { edges { node { name { value } } } }
  NetworkDnsServer { edges { node { name { value } ip_address { value } } } }
  NetworkNtpServer { edges { node { name { value } } } }
  NetworkLocalUser {
    edges { node {
      name { value } privilege { value } role { value } password_type { value } password { value }
    } }
  }
  IpamPrefix { edges { node { prefix { value } role { value } } } }
  CoreIPPrefixPool {
    edges { node {
      name { value } default_member_type { value } default_prefix_type { value } default_prefix_length { value }
      ip_namespace { node { name { value } } }
      resources { edges { node { prefix { value } } } }
    } }
  }
  CoreIPAddressPool {
    edges { node {
      name { value } default_address_type { value } default_prefix_length { value }
      ip_namespace { node { name { value } } }
      resources { edges { node { prefix { value } } } }
    } }
  }
  CoreNumberPool {
    edges { node {
      name { value } node { value } node_attribute { value } start_range { value } end_range { value }
    } }
  }
  ProfileDcimInterface {
    edges { node { profile_name { value } role { value } mtu { value } } }
  }
  TemplateDcimDevice {
    edges { node {
      template_name { value } role { value }
      device_type { node { name { value } manufacturer { node { name { value } } } } }
    } }
  }
  NetworkFabric {
    edges { node {
      name { value } index { value } amount_of_super_spines { value }
      fabric_interface_sorting_method { value } virtual_router_mac { value } mgmt_gateway { value }
      underlay_routing_protocol { value } overlay_routing_protocol { value } p2p_uplinks_mtu { value }
      spanning_tree_mode { value } spanning_tree_priority { value } avd_custom_hostvars { value }
      asn_pool { node { name { value } } }
      node_id_pool { node { name { value } } }
      mgmt_pool { node { name { value } } }
      uplink_pool { node { name { value } } }
      vtep_pool { node { name { value } } }
      loopback_pool { node { name { value } } }
      dns_servers { edges { node { name { value } } } }
      ntp_servers { edges { node { name { value } } } }
      local_users { edges { node { name { value } } } }
      children { edges { node { name { value } } } }
      member_of_groups { edges { node { name { value } } } }
    } }
  }
  NetworkPod {
    edges { node {
      name { value } index { value } amount_of_spines { value } loopback_ipv4_offset { value }
      spine_switch_template { node { template_name { value } } }
      parent { node { name { value } } }
      member_of_groups { edges { node { name { value } } } }
    } }
  }
  LocationHall { edges { node { name { value } index { value } } } }
  LocationRack {
    edges { node {
      name { value } index { value } rack_type { value } amount_of_leafs { value } mlag { value }
      pod { node { name { value } } }
      parent { node { name { value } } }
      leaf_switch_template { node { template_name { value } } }
      member_of_groups { edges { node { name { value } } } }
    } }
  }
  IpamVRF {
    edges { node {
      name { value } vrf_vni { value } namespace { node { name { value } } }
    } }
  }
  EvpnTenant {
    edges { node {
      name { value } mac_vrf_vni_base { value }
      fabrics { edges { node { name { value } } } }
      vrfs { edges { node { name { value } } } }
    } }
  }
  EvpnSvi {
    edges { node {
      name { value } svi_id { value } ip_address_virtual { value } enabled { value }
      fabric_tags { value } vrf { node { name { value } } }
    } }
  }
}
"""

KEY_FIELDS = {
    "CoreAccountGroup": "name",
    "CoreStandardGroup": "name",
    "OrganizationManufacturer": "name",
    "DcimDeviceType": "name",
    "NetworkDnsServer": "name",
    "NetworkNtpServer": "name",
    "NetworkLocalUser": "name",
    "IpamPrefix": "prefix",
    "CoreIPPrefixPool": "name",
    "CoreIPAddressPool": "name",
    "CoreNumberPool": "name",
    "ProfileDcimInterface": "profile_name",
    "TemplateDcimDevice": "template_name",
    "NetworkFabric": "name",
    "NetworkPod": "name",
    "LocationHall": "name",
    "LocationRack": "name",
    "IpamVRF": "name",
    "EvpnTenant": "name",
    "EvpnSvi": "name",
}

EXTRA_KINDS = {
    "AvdEvpn",
    "CloudvisionWorkspace",
    "ComputePhysicalServer",
    "EvpnL2Vlan",
    "IpamVLAN",
    "VirtualizationVirtualMachine",
}

GENERATED_GROUP_PREFIXES = ("avd_device_hostvar__", "generate-")
IGNORED_RECORDS = {
    "CoreAccountGroup": {"Infrahub Users", "Super Administrators"},
}
IGNORED_FIELDS = {
    # The object loader expands template interface ranges into individual
    # TemplateDcimInterface objects. Compare the device template's seed-level
    # scalar/relationship fields here; keep expanded template-interface export
    # as a separate concern.
    "TemplateDcimDevice": {"interfaces"},
}


def value(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, dict):
        if "value" in data:
            return data["value"]
        if "node" in data:
            return node_label(data["node"])
        if "edges" in data:
            return [node_label(edge["node"]) for edge in data["edges"]]
    return data


def node_label(node: dict[str, Any]) -> Any:
    for field in ("name", "template_name", "profile_name", "prefix"):
        if field in node:
            return value(node[field])
    return None


def normalize_live_node(kind: str, node: dict[str, Any]) -> dict[str, Any]:
    item = {key: value(raw) for key, raw in node.items()}

    if kind == "DcimDeviceType" and isinstance(item.get("manufacturer"), str):
        item["manufacturer"] = item["manufacturer"]

    if kind == "TemplateDcimDevice":
        device_type = node.get("device_type", {}).get("node")
        if device_type:
            manufacturer = value(device_type.get("manufacturer"))
            name = value(device_type.get("name"))
            item["device_type"] = [manufacturer, name] if manufacturer else name

    if kind == "NetworkFabric":
        groups = item.get("member_of_groups") or []
        item["member_of_groups"] = [
            group for group in groups if not group.startswith(GENERATED_GROUP_PREFIXES)
        ]

    if kind in {"NetworkPod", "LocationRack"}:
        groups = item.get("member_of_groups") or []
        item["member_of_groups"] = [
            group for group in groups if not group.startswith(GENERATED_GROUP_PREFIXES)
        ]

    return drop_empty(item)


def drop_empty(item: dict[str, Any]) -> dict[str, Any]:
    return {key: val for key, val in item.items() if val not in (None, [], {})}


def flatten_seed_item(kind: str, item: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    base = dict(item)
    ignored = IGNORED_FIELDS.get(kind, set())
    flattened = [
        (
            kind,
            drop_empty({k: v for k, v in base.items() if k != "children" and k not in ignored}),
        )
    ]

    children = item.get("children")
    if isinstance(children, dict):
        child_kind = children["kind"]
        for child in children.get("data") or []:
            child_item = dict(child)
            child_item.setdefault("parent", item.get("name"))
            flattened.extend(flatten_seed_item(child_kind, child_item))

    return flattened


def read_seed(seed_dir: Path) -> dict[str, dict[str, dict[str, Any]]]:
    records: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for path in sorted(seed_dir.glob("*.yml")):
        for doc in yaml.safe_load_all(path.read_text()):
            if not doc or doc.get("kind") != "Object":
                continue
            kind = doc["spec"]["kind"]
            for item in doc["spec"].get("data") or []:
                for out_kind, out_item in flatten_seed_item(kind, item):
                    key_field = KEY_FIELDS.get(out_kind)
                    if key_field and key_field in out_item:
                        key = str(out_item[key_field])
                        if key not in IGNORED_RECORDS.get(out_kind, set()):
                            records[out_kind][key] = out_item
    return records


def read_live(data: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    records: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for kind, payload in data.items():
        key_field = KEY_FIELDS.get(kind)
        if not key_field:
            continue
        for edge in payload.get("edges") or []:
            item = normalize_live_node(kind, edge["node"])
            key = item.get(key_field)
            if key is not None:
                key = str(key)
                if key not in IGNORED_RECORDS.get(kind, set()):
                    records[kind][key] = item
    return records


def project_live_to_seed_fields(
    live: dict[str, dict[str, dict[str, Any]]],
    seed: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    projected: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for kind, items in live.items():
        seed_fields = set()
        for seed_item in seed.get(kind, {}).values():
            seed_fields.update(seed_item)
        if not seed_fields:
            seed_fields.update(next(iter(items.values())).keys() if items else [])
        for key, item in items.items():
            projected[kind][key] = {field: item[field] for field in item if field in seed_fields}
    return projected


def as_yaml(records: dict[str, dict[str, dict[str, Any]]]) -> str:
    payload = {
        kind: [items[key] for key in sorted(items)]
        for kind, items in sorted(records.items())
        if items
    }
    return yaml.safe_dump(payload, sort_keys=True, allow_unicode=False)


def build_candidate_seed(
    live: dict[str, dict[str, dict[str, Any]]],
    seed: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    docs = []
    for kind in sorted(live):
        missing = [item for key, item in sorted(live[kind].items()) if key not in seed.get(kind, {})]
        if missing:
            docs.append({"apiVersion": "infrahub.app/v1", "kind": "Object", "spec": {"kind": kind, "data": missing}})
    return docs


async def count_extra_kinds(client: InfrahubClient, branch: str | None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for kind in sorted(EXTRA_KINDS):
        result = await client.execute_graphql(
            query=f"query Count{kind} {{ {kind} {{ count }} }}",
            branch_name=branch,
        )
        counts[kind] = result[kind]["count"]
    return counts


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default=os.getenv("INFRAHUB_ADDRESS", "http://black.tfd:8000"))
    parser.add_argument("--branch", default=os.getenv("INFRAHUB_BRANCH"))
    parser.add_argument("--seed-dir", type=Path, default=Path("objects"))
    parser.add_argument("--out-dir", type=Path, default=Path(tempfile.gettempdir()) / "infrahub-seed-diff")
    parser.add_argument("--username", default=os.getenv("INFRAHUB_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("INFRAHUB_PASSWORD", "infrahub"))
    parser.add_argument("--api-token", default=os.getenv("INFRAHUB_API_TOKEN"))
    args = parser.parse_args()

    config_kwargs = {"address": args.address}
    if args.api_token:
        config_kwargs["api_token"] = args.api_token
    else:
        config_kwargs["username"] = args.username
        config_kwargs["password"] = args.password

    client = InfrahubClient(config=Config(**config_kwargs))
    live_data = await client.execute_graphql(query=QUERY, branch_name=args.branch)
    live = read_live(live_data)
    seed = read_seed(args.seed_dir)
    projected_live = project_live_to_seed_fields(live, seed)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    seed_text = as_yaml(seed)
    live_text = as_yaml(projected_live)
    diff_text = "".join(
        difflib.unified_diff(
            seed_text.splitlines(keepends=True),
            live_text.splitlines(keepends=True),
            fromfile="seed",
            tofile=f"live:{args.address}",
        )
    )

    (args.out_dir / "seed-normalized.yml").write_text(seed_text)
    (args.out_dir / "live-normalized.yml").write_text(live_text)
    (args.out_dir / "seed-vs-live.diff").write_text(diff_text)

    candidate_docs = build_candidate_seed(projected_live, seed)
    candidate_text = "\n---\n".join(
        yaml.safe_dump(doc, sort_keys=False, allow_unicode=False).rstrip()
        for doc in candidate_docs
    )
    (args.out_dir / "candidate-missing-seed.yml").write_text(candidate_text + ("\n" if candidate_text else ""))

    extra_counts = await count_extra_kinds(client, args.branch)
    summary = {
        "address": args.address,
        "branch": args.branch or "default",
        "seed_records": sum(len(items) for items in seed.values()),
        "live_records": sum(len(items) for items in projected_live.values()),
        "missing_from_seed": sum(
            1 for kind, items in projected_live.items() for key in items if key not in seed.get(kind, {})
        ),
        "missing_from_live": sum(
            1 for kind, items in seed.items() for key in items if key not in projected_live.get(kind, {})
        ),
        "extra_kind_counts": extra_counts,
    }
    summary_text = yaml.safe_dump(summary, sort_keys=False, allow_unicode=False)
    (args.out_dir / "summary.yml").write_text(summary_text)
    print(summary_text, end="")
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
