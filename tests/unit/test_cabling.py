"""Unit tests for the index-based cabling-plan builders in cabling.py.

These validate the pure topology algorithms (no Infrahub client needed) using
lightweight mock interface/device objects, mirroring TestBuildServerCablingPlan
in test_server_cabling.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from solution_arista_avd.cabling import build_pod_cabling_plan, build_rack_cabling_plan


def _iface(iface_id: str) -> MagicMock:
    """A mock interface identified by .id (all the builders read off it)."""
    iface = MagicMock()
    iface.id = iface_id
    return iface


def _device(index: int | None = None) -> MagicMock:
    """A mock device; build_rack_cabling_plan reads device.index.value."""
    device = MagicMock()
    if index is not None:
        device.index.value = index
    return device


def _ids(plan: list[tuple[MagicMock, MagicMock]]) -> list[tuple[str, str]]:
    return [(src.id, dst.id) for src, dst in plan]


class TestBuildPodCablingPlan:
    """spine -> super-spine cabling, offset per pod_index."""

    def test_two_spines_two_super_spines_first_pod(self) -> None:
        spine1, spine2 = _device(), _device()
        ss1, ss2 = _device(), _device()

        # Each spine has one interface per super-spine.
        src_map = {
            spine1: [_iface("sp1-i0"), _iface("sp1-i1")],
            spine2: [_iface("sp2-i0"), _iface("sp2-i1")],
        }
        # Each super-spine has a column of spine-facing interfaces.
        dst_map = {
            ss1: [_iface("ss1-0"), _iface("ss1-1"), _iface("ss1-2"), _iface("ss1-3")],
            ss2: [_iface("ss2-0"), _iface("ss2-1"), _iface("ss2-2"), _iface("ss2-3")],
        }

        plan = build_pod_cabling_plan(pod_index=2, src_interface_map=src_map, dst_interface_map=dst_map)

        # pod_index 2 -> base column 0. Spine N uses column N across every super-spine.
        assert _ids(plan) == [
            ("sp1-i0", "ss1-0"),
            ("sp1-i1", "ss2-0"),
            ("sp2-i0", "ss1-1"),
            ("sp2-i1", "ss2-1"),
        ]

    def test_pod_index_offsets_super_spine_column(self) -> None:
        spine1, spine2 = _device(), _device()
        ss1, ss2 = _device(), _device()
        src_map = {
            spine1: [_iface("sp1-i0"), _iface("sp1-i1")],
            spine2: [_iface("sp2-i0"), _iface("sp2-i1")],
        }
        dst_map = {
            ss1: [_iface("ss1-0"), _iface("ss1-1"), _iface("ss1-2"), _iface("ss1-3")],
            ss2: [_iface("ss2-0"), _iface("ss2-1"), _iface("ss2-2"), _iface("ss2-3")],
        }

        plan = build_pod_cabling_plan(pod_index=3, src_interface_map=src_map, dst_interface_map=dst_map)

        # pod_index 3 -> base = (3-2)*2 = column 2, so this pod consumes a
        # distinct block of super-spine ports from pod_index 2.
        assert _ids(plan) == [
            ("sp1-i0", "ss1-2"),
            ("sp1-i1", "ss2-2"),
            ("sp2-i0", "ss1-3"),
            ("sp2-i1", "ss2-3"),
        ]


class TestBuildRackCablingPlan:
    """leaf -> spine cabling, windowed per rack_index and indexed by leaf index."""

    def test_two_leaves_two_spines_first_rack(self) -> None:
        leaf1, leaf2 = _device(index=1), _device(index=2)
        spine1, spine2 = _device(), _device()
        src_map = {
            leaf1: [_iface("l1-i0"), _iface("l1-i1")],
            leaf2: [_iface("l2-i0"), _iface("l2-i1")],
        }
        dst_map = {
            spine1: [_iface("sp1-0"), _iface("sp1-1"), _iface("sp1-2"), _iface("sp1-3")],
            spine2: [_iface("sp2-0"), _iface("sp2-1"), _iface("sp2-2"), _iface("sp2-3")],
        }

        plan = build_rack_cabling_plan(rack_index=1, src_interface_map=src_map, dst_interface_map=dst_map)

        # rack_index 1 -> window [0:2] on each spine; leaf index selects within it.
        assert _ids(plan) == [
            ("l1-i0", "sp1-0"),
            ("l1-i1", "sp2-0"),
            ("l2-i0", "sp1-1"),
            ("l2-i1", "sp2-1"),
        ]

    def test_rack_index_shifts_spine_window(self) -> None:
        leaf1, leaf2 = _device(index=1), _device(index=2)
        spine1, spine2 = _device(), _device()
        src_map = {
            leaf1: [_iface("l1-i0"), _iface("l1-i1")],
            leaf2: [_iface("l2-i0"), _iface("l2-i1")],
        }
        dst_map = {
            spine1: [_iface("sp1-0"), _iface("sp1-1"), _iface("sp1-2"), _iface("sp1-3")],
            spine2: [_iface("sp2-0"), _iface("sp2-1"), _iface("sp2-2"), _iface("sp2-3")],
        }

        plan = build_rack_cabling_plan(rack_index=2, src_interface_map=src_map, dst_interface_map=dst_map)

        # rack_index 2 -> window [2:4]; a different rack lands on different spine ports.
        assert _ids(plan) == [
            ("l1-i0", "sp1-2"),
            ("l1-i1", "sp2-2"),
            ("l2-i0", "sp1-3"),
            ("l2-i1", "sp2-3"),
        ]
