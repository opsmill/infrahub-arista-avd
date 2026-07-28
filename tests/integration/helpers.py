"""Shared helpers for the end-to-end pipeline integration test.

These utilities back ``test_e2e_pipeline.py``: a bounded-wait poller with
diagnostic failure messages, the generator/artifact name constants sourced from
``.infrahub.yml``, and small helpers for deriving expected counts from the loaded
seed data (rather than hardcoding brittle literals).
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, TypeVar

from infrahub_sdk.exceptions import GraphQLError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from infrahub_sdk import InfrahubClient

T = TypeVar("T")

# --- Generator definition names (from .infrahub.yml `generator_definitions`) ---
GENERATOR_FABRIC = "generate-fabric"
GENERATOR_POD = "generate-pod"
GENERATOR_RACK = "generate-rack"
GENERATOR_SERVER_CABLING = "generate-server-cabling"
GENERATOR_AVD_STRUCTURED_CONFIG = "generate-avd-device-structured-config"
GENERATOR_BACKFILL = "backfill-structured-config"

# Ordered topology chain. `infrahubctl generator <name>` with no variables
# iterates every member of the generator's target group, so one call per
# generator processes the whole fabric.
TOPOLOGY_GENERATOR_CHAIN = [
    GENERATOR_FABRIC,
    GENERATOR_POD,
    GENERATOR_RACK,
    GENERATOR_SERVER_CABLING,
]

# --- Artifact instance names (from .infrahub.yml `artifact_definitions` -> `artifact_name`) ---
ARTIFACT_CABLING_PLAN = "Cabling Plan"
ARTIFACT_AVD_EOS_CONFIG = "AVD EOS Configuration"
ARTIFACT_AVD_FABRIC_DOC = "AVD Fabric Documentation"
ARTIFACT_AVD_DEVICE_DOC = "AVD Device Documentation"
ARTIFACT_AVD_ANTA_CATALOG = "AVD ANTA Catalog"
ARTIFACT_CONTAINERLAB_TOPOLOGY = "ContainerLab Topology"

ALL_ARTIFACT_NAMES = [
    ARTIFACT_CABLING_PLAN,
    ARTIFACT_AVD_EOS_CONFIG,
    ARTIFACT_AVD_FABRIC_DOC,
    ARTIFACT_AVD_DEVICE_DOC,
    ARTIFACT_AVD_ANTA_CATALOG,
    ARTIFACT_CONTAINERLAB_TOPOLOGY,
]

# Arista device types + object templates seeded for issue #70, with the interface
# count each object template must expand to (Ethernet ports + 1 Loopback0).
ARISTA_DEVICE_TYPES = ("Arista 7050SX3-48YC8C", "Arista 7050CX3-32C")
ARISTA_TEMPLATE_INTERFACE_COUNTS = {
    "arista-7050cx3-32c-spine-switch": 33,  # 32x 100G QSFP + Loopback0
    "arista-7050sx3-48yc8c-leaf-switch": 57,  # 48x 25G + 8x 100G QSFP + Loopback0
}

# Marker the ANTA transform emits when the fabric has ANTA disabled
# (transforms/avd_anta_catalog.py). Used to assert the catalog is *populated*.
ANTA_DISABLED_MARKER = "# ANTA disabled"

# Default bounded-wait budgets (seconds). Kept generous for CI runners.
SCHEMA_TIMEOUT = 120
OBJECT_LOAD_TIMEOUT = 300
GROUP_TIMEOUT = 60
REPO_SYNC_INTERVAL = 10
REPO_SYNC_RETRIES = 60  # 10s * 60 = 600s
GENERATOR_TIMEOUT = 600
ARTIFACT_TIMEOUT = 600
POLL_INTERVAL = 10


def _summarize(value: Any) -> str:
    """Render an observed value compactly for a diagnostic failure message."""
    if isinstance(value, (list, tuple, set)):
        return f"{type(value).__name__} of length {len(value)}"
    if isinstance(value, dict):
        compact = repr(value)
        if len(compact) <= 500:
            return compact
        return f"dict with keys {sorted(value)[:10]}"
    text = repr(value)
    return text if len(text) <= 200 else f"{text[:200]}..."


async def wait_until(
    fetch: Callable[[], Awaitable[T]],
    ready: Callable[[T], bool],
    *,
    timeout: int,  # noqa: ASYNC109 (deliberate polling budget, not an asyncio.timeout scope)
    interval: int,
    describe: str,
) -> T:
    """Poll ``fetch`` until ``ready`` is satisfied or ``timeout`` elapses.

    Returns the observed value once ``ready(value)`` is truthy. On timeout raises
    ``AssertionError`` including the last observed value so the failing stage is
    diagnosable without a rerun (FR-015 / FR-019).
    """
    deadline = time.monotonic() + timeout
    last: Any = None
    while True:
        try:
            last = await fetch()
        except GraphQLError as exc:
            last = exc
        else:
            if ready(last):
                return last
        if time.monotonic() >= deadline:
            msg = f"{describe}: timed out after {timeout}s; last observed: {_summarize(last)}"
            raise AssertionError(msg)
        await asyncio.sleep(interval)


async def device_design_mismatches(client: InfrahubClient, branch: str) -> list[str]:
    """Compare each pod's and rack's generated devices against its device designs.

    Device designs are the sole source of sizing, so for each container and each
    design role the number of devices produced must equal ``device_quantity``.
    The design ``role`` names a tier, which the generators map onto a device role
    using the fabric's underlay (non-L3LS example fabrics use l2spine / l3spine /
    p / pe / l2leaf), so the same mapping is applied here.

    The fabric tier is covered separately by ``expected_super_spine_count``.

    Returns a list of human-readable mismatch descriptions; empty means parity.
    """
    from solution_arista_avd.avd import LEAF_ROLE_BY_UNDERLAY, SPINE_ROLE_BY_UNDERLAY

    def device_role(design_role: str, underlay: str | None) -> str:
        if underlay is None:
            return design_role
        if design_role == "spine":
            return SPINE_ROLE_BY_UNDERLAY.get(underlay, "spine")
        if design_role == "leaf":
            return LEAF_ROLE_BY_UNDERLAY.get(underlay, "leaf")
        return design_role

    # Underlay per pod (from its fabric) and per rack (from its pod).
    underlay_by_pod: dict[str, str | None] = {}
    pods = await client.all(kind="NetworkPod", branch=branch)
    for pod in pods:
        fabric = await client.get(kind="NetworkFabric", id=pod.parent.id, branch=branch)
        protocol = getattr(fabric, "underlay_routing_protocol", None)
        underlay_by_pod[pod.id] = protocol.value if protocol else None
    racks = await client.all(kind="LocationRack", branch=branch)
    underlay_by_rack = {rack.id: underlay_by_pod.get(rack.pod.id) if rack.pod else None for rack in racks}

    # Devices bucketed by their rack, else by their pod (spines and super-spines).
    per_rack: dict[str, dict[str, int]] = {}
    per_pod: dict[str, dict[str, int]] = {}
    for device in await client.all(kind="DcimDevice", branch=branch, prefetch_relationships=False):
        bucket = per_rack.setdefault(device.rack.id, {}) if device.rack.id else None
        if bucket is None and device.pod.id:
            bucket = per_pod.setdefault(device.pod.id, {})
        if bucket is not None:
            bucket[device.role.value] = bucket.get(device.role.value, 0) + 1

    mismatches: list[str] = []

    async def check(design_kind: str, parent_attr: str, container_kind: str) -> None:
        for design in await client.all(kind=design_kind, branch=branch):
            container_id = getattr(design, parent_attr).id
            role = design.role.value
            want = int(design.device_quantity.value)
            if parent_attr == "rack":
                actual, underlay = per_rack.get(container_id, {}), underlay_by_rack.get(container_id)
            else:
                actual, underlay = per_pod.get(container_id, {}), underlay_by_pod.get(container_id)
            mapped = device_role(role, underlay)
            got = actual.get(mapped, 0)
            if got != want:
                container = await client.get(kind=container_kind, id=container_id, branch=branch)
                mismatches.append(
                    f"{container_kind} {container.name.value} design_role={role} -> "
                    f"device_role={mapped}: design={want} actual={got}"
                )

    await check("NetworkPodDeviceDesign", "pod", "NetworkPod")
    await check("NetworkRackDeviceDesign", "rack", "LocationRack")
    return mismatches


async def expected_super_spine_count(client: InfrahubClient, branch: str) -> int:
    """Sum the ``super_spine`` design quantities across all fabrics.

    Derives the expected count from the fabrics' ``device_designs`` rather than
    hardcoding it; a fabric with no ``super_spine`` design contributes nothing.
    """
    designs = await client.all(kind="NetworkFabricDeviceDesign", branch=branch)
    total = 0
    for design in designs:
        if design.role.value != "super_spine":
            continue
        if design.device_quantity.value is not None:
            total += int(design.device_quantity.value)
    return total
