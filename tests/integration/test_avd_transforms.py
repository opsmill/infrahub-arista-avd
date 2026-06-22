"""Integration tests for AVD transforms.

These tests verify the AVD pipeline components are importable and functional.
Note: Full pipeline tests require a complete AVD inventory structure.
"""

import pyavd
import pytest


class TestPyAvdBasics:
    """Basic tests for pyAVD integration."""

    def test_pyavd_import(self) -> None:
        """Test that pyavd is importable."""
        assert hasattr(pyavd, "get_avd_facts")
        assert hasattr(pyavd, "get_device_structured_config")
        assert hasattr(pyavd, "get_device_config")
        assert hasattr(pyavd, "get_fabric_documentation")
        assert hasattr(pyavd, "validate_inputs")
        assert hasattr(pyavd, "validate_structured_config")

    def test_simple_hostvars_validation(self) -> None:
        """Test that a simple hostvars structure validates.

        Note: pyavd.validate_inputs expects partial validation,
        returning issues rather than raising errors for missing fields.
        """
        hostvars = {
            "type": "spine",
            "id": 1,
            "bgp_as": "65000",
        }

        # validate_inputs returns a ValidationResult, should not raise
        result = pyavd.validate_inputs(hostvars)
        assert result is not None


class TestAvdPipelineFunctions:
    """Tests for AVD pipeline function availability.

    Full pyAVD pipeline requires complete AVD inventory with:
    - Node type configurations (super_spine:, spine:, l3leaf:)
    - Defaults and node group definitions
    - Complete uplink/downlink topology

    These tests verify the functions exist and can be called,
    but the actual config generation requires Infrahub data.
    """

    def test_get_device_config_function_exists(self) -> None:
        """Test get_device_config accepts structured config dict."""
        # Minimal structured config
        minimal_config = {
            "hostname": "test-device",
        }

        # This should return a string (even if minimal)
        result = pyavd.get_device_config(minimal_config)
        assert isinstance(result, str)

    def test_validate_structured_config(self) -> None:
        """Test structured config validation."""
        minimal_config = {
            "hostname": "test-device",
        }

        result = pyavd.validate_structured_config(minimal_config)
        assert result is not None

    @pytest.mark.skip(reason="Requires full AVD inventory structure from Infrahub")
    def test_full_pipeline_with_inventory(self) -> None:
        """Test full pipeline - requires complete AVD inventory.

        This test is skipped because it requires:
        1. A running Infrahub instance with AVD data
        2. Complete node type configurations
        3. Full fabric topology with uplinks/downlinks

        The actual integration is tested when running the generators
        against a real Infrahub instance.
        """


class TestAvdTransformImports:
    """Test that AVD transform modules are importable."""

    def test_import_avd_eos_config_transform(self) -> None:
        """Test AvdEosConfigTransform is importable."""
        from transforms.avd_eos_config import AvdEosConfigTransform

        assert AvdEosConfigTransform is not None
        assert hasattr(AvdEosConfigTransform, "transform")

    def test_import_avd_fabric_doc_transform(self) -> None:
        """Test AvdFabricDocTransform is importable."""
        from transforms.avd_fabric_doc import AvdFabricDocTransform

        assert AvdFabricDocTransform is not None
        assert hasattr(AvdFabricDocTransform, "transform")


class TestAvdGeneratorImports:
    """Test that AVD generator modules are importable."""

    def test_import_avd_inputs_generator(self) -> None:
        """Test the AVD device hostvar generator is importable."""
        from generators.generate_avd_device_hostvar import GenerateAVDDeviceHostvar

        assert GenerateAVDDeviceHostvar is not None
        assert hasattr(GenerateAVDDeviceHostvar, "generate")

    def test_import_avd_structured_config_generator(self) -> None:
        """Test the AVD device structured config generator is importable."""
        from generators.generate_avd_device_structured_config import AvdDeviceStructuredConfigGenerator

        assert AvdDeviceStructuredConfigGenerator is not None
        assert hasattr(AvdDeviceStructuredConfigGenerator, "generate")
