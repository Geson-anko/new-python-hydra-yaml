"""Tests for HydraUtilityFunctions class methods and properties."""

import pytest

from hydra_yaml_lsp.constants import HydraUtilityFunctions


class TestHydraUtilityFunctions:
    """Tests for HydraUtilityFunctions enum class methods and properties."""

    def test_import_path_property(self):
        """Test import_path property returns correct path string."""
        assert HydraUtilityFunctions.GET_OBJECT.import_path == "hydra.utils.get_object"
        assert HydraUtilityFunctions.GET_CLASS.import_path == "hydra.utils.get_class"
        assert HydraUtilityFunctions.GET_METHOD.import_path == "hydra.utils.get_method"
        assert (
            HydraUtilityFunctions.GET_STATIC_METHOD.import_path
            == "hydra.utils.get_static_method"
        )

    def test_is_hydra_utility_function(self):
        """Test is_hydra_utility_function classmethod correctly identifies
        utility functions."""
        # Valid utility function paths
        assert HydraUtilityFunctions.is_hydra_utility_function("hydra.utils.get_object")
        assert HydraUtilityFunctions.is_hydra_utility_function("hydra.utils.get_class")
        assert HydraUtilityFunctions.is_hydra_utility_function("hydra.utils.get_method")
        assert HydraUtilityFunctions.is_hydra_utility_function(
            "hydra.utils.get_static_method"
        )

        # Invalid utility function paths
        assert not HydraUtilityFunctions.is_hydra_utility_function(
            "hydra.utils.invalid"
        )
        assert not HydraUtilityFunctions.is_hydra_utility_function(
            "other.module.get_object"
        )
        assert not HydraUtilityFunctions.is_hydra_utility_function("get_class")
        assert not HydraUtilityFunctions.is_hydra_utility_function("")

    def test_from_import_path(self):
        """Test from_import_path classmethod returns correct enum value."""
        assert (
            HydraUtilityFunctions.from_import_path("hydra.utils.get_object")
            == HydraUtilityFunctions.GET_OBJECT
        )
        assert (
            HydraUtilityFunctions.from_import_path("hydra.utils.get_class")
            == HydraUtilityFunctions.GET_CLASS
        )
        assert (
            HydraUtilityFunctions.from_import_path("hydra.utils.get_method")
            == HydraUtilityFunctions.GET_METHOD
        )
        assert (
            HydraUtilityFunctions.from_import_path("hydra.utils.get_static_method")
            == HydraUtilityFunctions.GET_STATIC_METHOD
        )

    def test_from_import_path_invalid(self):
        """Test from_import_path raises ValueError for invalid paths."""
        with pytest.raises(ValueError) as excinfo:
            HydraUtilityFunctions.from_import_path("hydra.utils.invalid")
        assert "is not hydra utility function import path" in str(excinfo.value)

        with pytest.raises(ValueError):
            HydraUtilityFunctions.from_import_path("other.module.get_object")
