from textwrap import dedent

import pytest

from hydra_yaml_lsp.core.detections.target_value import (
    TargetValuePosition,
    detect_target_values,
)


class TestTargetValueDetection:
    """Test cases for target value detection in Hydra YAML files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_values("")
        assert result == ()

    def test_document_with_no_target_values(self):
        """Test with a document containing no target values."""
        content = dedent("""
            regular: value
            another: item
            third: element
        """).strip()
        result = detect_target_values(content)
        assert result == ()

    def test_document_with_single_target_value(self):
        """Test with a document containing a single target value."""
        content = "_target_: module.path\nregular: value"
        result = detect_target_values(content)

        assert len(result) == 1
        assert result[0].lineno == 0
        assert result[0].start == len("_target_: ")
        assert result[0].end == len("_target_: module.path")
        assert result[0].content == "module.path"

    def test_document_with_multiple_target_values(self):
        """Test with a document containing multiple target values."""
        content = dedent("""
            component1:
              _target_: path.to.component1
            component2:
              _target_: path.to.component2
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 2
        # First target value
        assert result[0].content == "path.to.component1"
        # Second target value
        assert result[1].content == "path.to.component2"

    def test_document_with_nested_target_values(self):
        """Test with a document containing nested structures with target
        values."""
        content = dedent("""
            outer:
              _target_: outer.module
              nested:
                _target_: nested.module
                deeper:
                  _target_: deepest.module
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 3
        assert result[0].content == "outer.module"
        assert result[1].content == "nested.module"
        assert result[2].content == "deepest.module"

    def test_document_with_target_and_other_special_keys(self):
        """Test with a document containing both target and other special
        keys."""
        content = dedent("""
            component:
              _target_: path.to.class
              _args_: [1, 2, 3]
              _partial_: true
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 1
        assert result[0].content == "path.to.class"

    def test_multiline_target_value(self):
        """Test with a target value spanning multiple lines."""
        content = dedent("""
            component:
              _target_: >-
                very.long.path.to.module.with.
                line.breaks.ClassName
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 1
        assert "very.long.path" in result[0].content
        assert "line.breaks.ClassName" in result[0].content

    def test_caching(self):
        """Test that results are cached properly."""
        content = "_target_: module.path"

        # First call should compute the result
        result1 = detect_target_values(content)

        # Second call should use the cached result
        result2 = detect_target_values(content)

        # Results should be identical
        assert result1 == result2

        # And should be the expected values
        expected = (
            TargetValuePosition(
                lineno=0,
                start=len("_target_: "),
                end=len("_target_: module.path"),
                content="module.path",
            ),
        )
        assert result1 == expected

        # Check cache info
        info = detect_target_values.cache_info()
        assert info.hits >= 1
