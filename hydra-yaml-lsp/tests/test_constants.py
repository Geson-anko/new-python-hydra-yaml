"""Tests for HydraUtilityFunction class methods and properties."""

import pytest

from hydra_yaml_lsp.constants import HydraUtilityFunction


class TestHydraUtilityFunction:
    """Tests for HydraUtilityFunction enum class methods and properties."""

    def test_import_path_property(self):
        """Test import_path property returns correct path string."""
        assert HydraUtilityFunction.GET_OBJECT.import_path == "hydra.utils.get_object"
        assert HydraUtilityFunction.GET_CLASS.import_path == "hydra.utils.get_class"
        assert HydraUtilityFunction.GET_METHOD.import_path == "hydra.utils.get_method"
        assert (
            HydraUtilityFunction.GET_STATIC_METHOD.import_path
            == "hydra.utils.get_static_method"
        )

    def test_is_hydra_utility_function(self):
        """Test is_hydra_utility_function classmethod correctly identifies
        utility functions."""
        # Valid utility function paths
        assert HydraUtilityFunction.is_hydra_utility_function("hydra.utils.get_object")
        assert HydraUtilityFunction.is_hydra_utility_function("hydra.utils.get_class")
        assert HydraUtilityFunction.is_hydra_utility_function("hydra.utils.get_method")
        assert HydraUtilityFunction.is_hydra_utility_function(
            "hydra.utils.get_static_method"
        )

        # Invalid utility function paths
        assert not HydraUtilityFunction.is_hydra_utility_function("hydra.utils.invalid")
        assert not HydraUtilityFunction.is_hydra_utility_function(
            "other.module.get_object"
        )
        assert not HydraUtilityFunction.is_hydra_utility_function("get_class")
        assert not HydraUtilityFunction.is_hydra_utility_function("")

    def test_from_import_path(self):
        """Test from_import_path classmethod returns correct enum value."""
        assert (
            HydraUtilityFunction.from_import_path("hydra.utils.get_object")
            == HydraUtilityFunction.GET_OBJECT
        )
        assert (
            HydraUtilityFunction.from_import_path("hydra.utils.get_class")
            == HydraUtilityFunction.GET_CLASS
        )
        assert (
            HydraUtilityFunction.from_import_path("hydra.utils.get_method")
            == HydraUtilityFunction.GET_METHOD
        )
        assert (
            HydraUtilityFunction.from_import_path("hydra.utils.get_static_method")
            == HydraUtilityFunction.GET_STATIC_METHOD
        )

    def test_from_import_path_invalid(self):
        """Test from_import_path raises ValueError for invalid paths."""
        with pytest.raises(ValueError) as excinfo:
            HydraUtilityFunction.from_import_path("hydra.utils.invalid")
        assert "is not hydra utility function import path" in str(excinfo.value)

        with pytest.raises(ValueError):
            HydraUtilityFunction.from_import_path("other.module.get_object")
