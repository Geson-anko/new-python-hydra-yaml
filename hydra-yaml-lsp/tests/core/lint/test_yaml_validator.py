"""Tests for YAML validation utilities."""

from textwrap import dedent

import pytest
from ruamel import yaml

from hydra_yaml_lsp.core.lint.message import MessageType
from hydra_yaml_lsp.core.lint.yaml_validator import validate_yaml


class TestYamlValidator:
    """Test suite for YAML validation functionality."""

    def test_valid_yaml(self):
        """Test validation with valid YAML content."""
        content = dedent("""
            key1: value1
            key2: value2
            nested:
              inner_key: inner_value
        """)

        messages = validate_yaml(content)
        assert len(messages) == 0

    def test_empty_content(self):
        """Test validation with empty content."""
        messages = validate_yaml("")
        assert len(messages) == 0

        messages = validate_yaml("   ")
        assert len(messages) == 0

    def test_scanner_error(self):
        """Test validation with a YAML syntax error."""
        content = dedent("""
            key1: value1
              wrong_indent: value
            key2: value2
        """)
        messages = validate_yaml(content)
        assert len(messages) == 1
        assert messages[0].type == MessageType.ERROR
        assert "YAML syntax error" in messages[0].content
        assert messages[0].position.start_line == 2  # 0-indexed, so line 3

    def test_constructor_error(self):
        """Test validation with duplicate keys."""
        content = dedent("""
            key1: value1
            key1: value2
        """)

        messages = validate_yaml(content)
        assert len(messages) == 1
        assert messages[0].type == MessageType.ERROR
        assert "YAML constructor error" in messages[0].content

    def test_cache_hit(self):
        """Test the lru_cache functionality."""
        content = "key: value"

        # First call should compute result
        validate_yaml(content)

        # Mock YAML.load to verify it's not called again
        original_load = yaml.YAML.load

        def mock_load(*args, **kwargs):
            pytest.fail("YAML.load should not be called due to cache hit")

        yaml.YAML.load = mock_load
        try:
            # Second call should use cached result
            validate_yaml(content)
        finally:
            # Restore original function
            yaml.YAML.load = original_load
