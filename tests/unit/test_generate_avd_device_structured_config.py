# ruff: noqa: SLF001
"""Unit tests for AVD device structured config generator."""

import json
from unittest.mock import AsyncMock

import pytest
from pyavd import validate_inputs

from generators.generate_avd_device_structured_config import (
    AvdDeviceStructuredConfigGenerator,
)
from generators.generate_avd_inputs_query import (
    GenerateAvdInputsQuery,
    GenerateAvdInputsQueryNetworkFabric,
    GenerateAvdInputsQueryNetworkFabricEdges,
    GenerateAvdInputsQueryNetworkFabricEdgesNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFile,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFileNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFile,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFileNode,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName,
    GenerateAvdInputsQueryNetworkFabricEdgesNodeName,
)

# --- Helpers to build query data ---


def _make_pod_device(
    hostname: str, device_id: str, has_hostvar: bool = False
) -> GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges:
    """Create a pod-level device edge."""
    hostvar_file = None
    if has_hostvar:
        hostvar_file = GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFile(
            node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNodeHostvarFileNode(
                id="file-123"
            )
        )

    artifact_node = None
    if has_hostvar:
        artifact_node = (
            GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifactNode(
                hostvar_file=hostvar_file
            )
        )

    return GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdges(
        node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNode(
            id=device_id,
            name=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeName(
                value=hostname
            ),
            avd_artifact=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevicesEdgesNodeAvdArtifact(
                node=artifact_node
            ),
        )
    )


def _make_rack_device(
    hostname: str, device_id: str, has_hostvar: bool = False
) -> GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges:
    """Create a rack-level device edge."""
    hostvar_file = None
    if has_hostvar:
        hostvar_file = GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFile(
            node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNodeHostvarFileNode(
                id="file-456"
            )
        )

    artifact_node = None
    if has_hostvar:
        artifact_node = GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifactNode(
            hostvar_file=hostvar_file
        )

    return GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdges(
        node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDevice(
            __typename="DcimDevice",
            id=device_id,
            name=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceName(
                value=hostname
            ),
            avd_artifact=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevicesEdgesNodeDcimDeviceAvdArtifact(
                node=artifact_node
            ),
        )
    )


def _make_rack(
    devices: list,
) -> GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges:
    """Create a rack edge with devices."""
    return GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdges(
        node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNode(
            devices=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacksEdgesNodeDevices(
                edges=devices
            )
        )
    )


def _make_pod(
    pod_devices: list | None = None,
    racks: list | None = None,
) -> GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges:
    """Create a pod edge with devices and racks."""
    return GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdges(
        node=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPod(
            __typename="NetworkPod",
            devices=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodDevices(
                edges=pod_devices or []
            ),
            racks=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildrenEdgesNodeNetworkPodRacks(edges=racks or []),
        )
    )


def _make_fabric_query(
    pods: list,
) -> GenerateAvdInputsQuery:
    """Build a full query response with given pods."""
    return GenerateAvdInputsQuery(
        NetworkFabric=GenerateAvdInputsQueryNetworkFabric(
            edges=[
                GenerateAvdInputsQueryNetworkFabricEdges(
                    node=GenerateAvdInputsQueryNetworkFabricEdgesNode(
                        id="fabric-1",
                        name=GenerateAvdInputsQueryNetworkFabricEdgesNodeName(value="Fabric-A"),
                        children=GenerateAvdInputsQueryNetworkFabricEdgesNodeChildren(edges=pods),
                    )
                )
            ]
        )
    )


def _make_generator() -> AvdDeviceStructuredConfigGenerator:
    """Create a generator instance with a mocked client."""
    gen = AvdDeviceStructuredConfigGenerator.__new__(AvdDeviceStructuredConfigGenerator)
    gen.client = AsyncMock()
    return gen


# --- Tests for _extract_devices_from_fabric ---


class TestExtractDevicesFromFabric:
    def test_empty_fabric(self):
        gen = _make_generator()
        data = GenerateAvdInputsQuery(NetworkFabric=GenerateAvdInputsQueryNetworkFabric(edges=[]))
        result = gen._extract_devices_from_fabric(data)
        assert result == []

    def test_pod_devices_only(self):
        gen = _make_generator()
        data = _make_fabric_query(
            pods=[
                _make_pod(
                    pod_devices=[
                        _make_pod_device("spine-1", "dev-1"),
                        _make_pod_device("spine-2", "dev-2", has_hostvar=True),
                    ]
                )
            ]
        )
        result = gen._extract_devices_from_fabric(data)
        assert len(result) == 2
        hostnames = {d["hostname"] for d in result}
        assert hostnames == {"spine-1", "spine-2"}

        spine2 = next(d for d in result if d["hostname"] == "spine-2")
        assert spine2["has_hostvar"] is True
        assert spine2["id"] == "dev-2"

        spine1 = next(d for d in result if d["hostname"] == "spine-1")
        assert spine1["has_hostvar"] is False

    def test_rack_devices_only(self):
        gen = _make_generator()
        data = _make_fabric_query(
            pods=[
                _make_pod(
                    racks=[
                        _make_rack(
                            devices=[
                                _make_rack_device("leaf-1", "dev-10", has_hostvar=True),
                                _make_rack_device("leaf-2", "dev-11"),
                            ]
                        )
                    ]
                )
            ]
        )
        result = gen._extract_devices_from_fabric(data)
        assert len(result) == 2
        leaf1 = next(d for d in result if d["hostname"] == "leaf-1")
        assert leaf1["has_hostvar"] is True

    def test_mixed_pod_and_rack_devices(self):
        gen = _make_generator()
        data = _make_fabric_query(
            pods=[
                _make_pod(
                    pod_devices=[
                        _make_pod_device("spine-1", "dev-1", has_hostvar=True),
                    ],
                    racks=[
                        _make_rack(
                            devices=[
                                _make_rack_device("leaf-1", "dev-10", has_hostvar=True),
                            ]
                        )
                    ],
                )
            ]
        )
        result = gen._extract_devices_from_fabric(data)
        assert len(result) == 2
        hostnames = {d["hostname"] for d in result}
        assert hostnames == {"spine-1", "leaf-1"}

    def test_deduplication_by_hostname(self):
        """If the same hostname appears in pod and rack, it should be deduped."""
        gen = _make_generator()
        data = _make_fabric_query(
            pods=[
                _make_pod(
                    pod_devices=[
                        _make_pod_device("device-1", "dev-1"),
                    ],
                    racks=[
                        _make_rack(
                            devices=[
                                _make_rack_device("device-1", "dev-1-rack"),
                            ]
                        )
                    ],
                )
            ]
        )
        result = gen._extract_devices_from_fabric(data)
        assert len(result) == 1
        # Rack version overwrites pod version (dict key overwrite)
        assert result[0]["id"] == "dev-1-rack"

    def test_multiple_pods(self):
        gen = _make_generator()
        data = _make_fabric_query(
            pods=[
                _make_pod(
                    pod_devices=[_make_pod_device("spine-1", "dev-1")],
                ),
                _make_pod(
                    pod_devices=[_make_pod_device("spine-2", "dev-2")],
                ),
            ]
        )
        result = gen._extract_devices_from_fabric(data)
        assert len(result) == 2


# --- Tests for _fetch_hostvars_from_storage ---


class TestFetchHostvarsFromStorage:
    @pytest.mark.anyio
    async def test_skips_devices_without_hostvars(self):
        gen = _make_generator()
        devices = [
            {"hostname": "spine-1", "id": "dev-1", "has_hostvar": False},
            {"hostname": "spine-2", "id": "dev-2", "has_hostvar": False},
        ]
        result = await gen._fetch_hostvars_from_storage(devices)
        assert result == {}
        gen.client.get.assert_not_called()

    @pytest.mark.anyio
    async def test_fetches_hostvars_for_devices_with_artifacts(self):
        gen = _make_generator()
        hostvars_data = {"hostname": "spine-1", "router_bgp": {"as": "65001"}}

        mock_artifact = AsyncMock()
        mock_artifact.hostvar_file.peer.download_file = AsyncMock(return_value=json.dumps(hostvars_data))
        gen.client.get = AsyncMock(return_value=mock_artifact)

        devices = [
            {"hostname": "spine-1", "id": "dev-1", "has_hostvar": True},
        ]
        result = await gen._fetch_hostvars_from_storage(devices)
        assert "spine-1" in result
        assert result["spine-1"] == hostvars_data

    @pytest.mark.anyio
    async def test_handles_fetch_failure_gracefully(self):
        gen = _make_generator()
        gen.client.get = AsyncMock(side_effect=Exception("connection error"))

        devices = [
            {"hostname": "spine-1", "id": "dev-1", "has_hostvar": True},
        ]
        result = await gen._fetch_hostvars_from_storage(devices)
        assert result == {}


# --- Tests for pyavd validate_inputs API ---


class TestValidateInputsAPI:
    """Verify the pyavd validate_inputs API we use in the generator."""

    def test_minimal_valid_inputs_have_no_violations(self):
        """validate_inputs with minimal valid inputs should have no violations."""
        inputs = {"hostname": "test-device", "type": "l3leaf", "fabric_name": "test-fabric"}
        validated = validate_inputs(inputs)
        assert not validated.validation_result.violations

    def test_validated_data_result_has_expected_attributes(self):
        """Ensure the API shape we depend on exists."""
        validated = validate_inputs({})
        assert hasattr(validated, "validation_result")
        assert hasattr(validated, "validated_data")
        assert hasattr(validated.validation_result, "violations")

    def test_validated_data_result_has_no_failed_attribute(self):
        """Confirm the old .failed API no longer exists (regression guard)."""
        validated = validate_inputs({})
        assert not hasattr(validated, "failed")
