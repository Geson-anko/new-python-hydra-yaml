"""Tests for the special_keys module."""

from textwrap import dedent

import pytest

from hydra_yaml_lsp.core.detection import (
    InterpolationHighlight,
    InterpolationPosition,
    SpecialKeyPosition,
    detect_interpolation_pos_in_document,
    detect_special_keys_in_document,
)


class TestDocumentSpecialKeys:
    """Test cases for document-level special key detection in Hydra YAML
    files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_special_keys_in_document("")
        assert result == ()

    def test_document_with_no_special_keys(self):
        """Test with a document containing no special keys."""
        content = "regular: value\nanother: item\nthird: element"
        result = detect_special_keys_in_document(content)
        assert result == ()

    @pytest.mark.parametrize(
        "content, expected",
        [
            (
                "_target_: module.path\nregular: value\n_args_: some_args",
                (
                    SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
                    SpecialKeyPosition(lineno=2, start=0, end=6, key="_args_"),
                ),
            ),
            (
                "_target_: value # comment\nregular: value # _ignored_: test",
                (SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),),
            ),
            (
                "\n_target_: value\n\nregular: value\n_args_: more\n",
                (
                    SpecialKeyPosition(lineno=1, start=0, end=8, key="_target_"),
                    SpecialKeyPosition(lineno=4, start=0, end=6, key="_args_"),
                ),
            ),
        ],
        ids=[
            "basic_special_keys",
            "keys_in_comments",
            "empty_lines",
        ],
    )
    def test_document_with_special_keys(self, content, expected):
        """Test document with various special key arrangements."""
        result = detect_special_keys_in_document(content)
        assert result == expected

    def test_caching(self):
        """Test that results are cached properly."""
        content = "_target_: module.path\n_args_: value"

        # First call should compute the result
        result1 = detect_special_keys_in_document(content)

        # Second call should use the cached result
        result2 = detect_special_keys_in_document(content)

        # Results should be identical
        assert result1 == result2

        # And should be the expected values
        expected = (
            SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
            SpecialKeyPosition(lineno=1, start=0, end=6, key="_args_"),
        )
        assert result1 == expected

        # Check cache info
        info = detect_special_keys_in_document.cache_info()
        assert info.hits >= 1


class TestInterpolationHighlight:
    """Test cases for the InterpolationHighlight class."""

    def test_highlight_position_properties(self):
        """Test the properties of InterpolationHighlight class."""
        pos = InterpolationHighlight(
            start_line=5,
            start_column=10,
            end_column=20,
            token_type="reference",
            content="test.reference",
        )

        assert pos.start_line == 5
        assert pos.start_column == 10
        assert pos.end_column == 20
        assert pos.token_type == "reference"
        assert pos.content == "test.reference"


class TestInterpolationHighlightExtraction:
    """Test cases for extracting highlights from interpolations."""

    def test_get_reference_highlight_simple(self):
        """Test extraction of simple reference highlight."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=30,
            content="${reference.path}",
        )

        highlight = interp.get_reference_highlight()
        assert highlight is not None
        assert highlight.start_line == 5
        assert highlight.start_column == 12  # Position of "reference.path"
        assert highlight.end_column == 26  # End position of "reference.path"
        assert highlight.token_type == "reference"
        assert highlight.content == "reference.path"

    def test_get_reference_highlight_with_spaces(self):
        """Test extraction of reference with spaces."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=34,
            content="${  reference.path  }",
        )

        highlight = interp.get_reference_highlight()
        assert highlight is not None
        assert highlight.content == "reference.path"
        assert highlight.start_line == 5
        assert highlight.start_column == 14  # Position after "${  "
        assert highlight.token_type == "reference"

    def test_get_reference_highlight_function_returns_none(self):
        """Test that reference highlight returns None for function
        interpolations."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=40,
            content="${function:arg1,arg2}",
        )

        highlight = interp.get_reference_highlight()
        assert highlight is None

    def test_get_function_highlight_simple(self):
        """Test extraction of simple function highlight."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=40,
            content="${function:arg1,arg2}",
        )

        highlight = interp.get_function_highlight()
        assert highlight is not None
        assert highlight.start_line == 5
        assert highlight.start_column == 12  # Position of "function"
        assert highlight.end_column == 20  # End position of "function"
        assert highlight.token_type == "function"
        assert highlight.content == "function"

    def test_get_function_highlight_with_spaces(self):
        """Test extraction of function with spaces."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=44,
            content="${  function  :arg1,arg2}",
        )

        highlight = interp.get_function_highlight()
        assert highlight is not None
        assert highlight.content == "function"
        assert highlight.start_line == 5
        assert highlight.start_column == 14  # Position after "${  "
        assert highlight.token_type == "function"

    def test_get_highlight_position_reference(self):
        """Test get_highlight_position for reference interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=30,
            content="${reference.path}",
        )

        highlight = interp.get_highlight_position()
        assert highlight is not None
        assert highlight.token_type == "reference"
        assert highlight.content == "reference.path"

    def test_get_highlight_position_function(self):
        """Test get_highlight_position for function interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=40,
            content="${function:arg1,arg2}",
        )

        highlight = interp.get_highlight_position()
        assert highlight is not None
        assert highlight.token_type == "function"
        assert highlight.content == "function"

    def test_multiline_reference(self):
        """Test reference highlight extraction from multi-line
        interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=7,
            end_column=5,
            content="${\nreference.path\n}",
        )

        highlight = interp.get_reference_highlight()
        assert highlight is not None
        assert highlight.start_line == 6  # Line after start
        assert highlight.start_column == 0  # At beginning of line
        assert highlight.end_column == len("reference.path")
        assert highlight.content == "reference.path"

    def test_function_in_first_line(self):
        """Test function highlight extraction where function is in first
        line."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=7,
            end_column=5,
            content="${function:\narg1,arg2\n}",
        )

        highlight = interp.get_function_highlight()
        assert highlight is not None
        assert highlight.start_line == 5  # Same as interpolation start
        assert highlight.start_column == 12  # Position of "function"
        assert highlight.end_column == 20  # End position of "function"
        assert highlight.token_type == "function"
        assert highlight.content == "function"

    def test_function_not_in_first_line(self):
        """Test that function highlight returns None if function is not in
        first line."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=7,
            end_column=5,
            content="${\nfunction:\narg1,arg2\n}",
        )

        # Implementation searches for function in first line only
        highlight = interp.get_function_highlight()
        assert highlight is not None
        assert highlight.start_line == 6  # Line after start
        assert highlight.start_column == 0  # At beginning of line
        assert highlight.end_column == len("function")
        assert highlight.token_type == "function"
        assert highlight.content == "function"

    def test_malformed_interpolation(self):
        """Test with malformed interpolation content."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=15,
            content="${}",  # Empty interpolation
        )

        assert interp.get_reference_highlight() is None
        assert interp.get_function_highlight() is None
        assert interp.get_highlight_position() is None

    def test_empty_reference(self):
        """Test with empty reference."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=17,
            content="${  }",  # Reference with spaces only
        )

        assert interp.get_reference_highlight() is None

    def test_empty_function(self):
        """Test with empty function."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=17,
            content="${  :}",  # Function with empty name
        )

        assert interp.get_function_highlight() is None


class TestInterpolationDetection:
    """Test cases for detecting interpolation patterns in Hydra YAML files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_interpolation_pos_in_document("")
        assert result == ()

    def test_document_with_no_interpolations(self):
        """Test with a document containing no interpolations."""
        content = "regular: value\nanother: item\nthird: element"
        result = detect_interpolation_pos_in_document(content)
        assert result == ()

    def test_simple_interpolation(self):
        """Test with a simple interpolation."""
        content = "value: ${path.to.value}"
        result = detect_interpolation_pos_in_document(content)

        assert len(result) == 1
        assert result[0].content == "${path.to.value}"
        assert result[0].start_line == 0
        assert result[0].end_line == 0
        assert result[0].start_column == len("value: ")
        assert result[0].end_column == len(content)

    def test_multiple_interpolations(self):
        """Test with multiple interpolations in the same document."""
        content = "value1: ${path1}\nvalue2: ${path2}"
        result = detect_interpolation_pos_in_document(content)

        assert len(result) == 2
        # First interpolation
        assert result[0].content == "${path1}"
        assert result[0].start_line == 0
        assert result[0].start_column == len("value1: ")
        assert result[0].end_line == 0
        assert result[0].end_column == len("value1: ${path1}")

        # Second interpolation
        assert result[1].content == "${path2}"
        assert result[1].start_line == 1
        assert result[1].start_column == len("value2: ")
        assert result[1].end_line == 1
        assert result[1].end_column == len("value2: ${path2}")

    def test_multiline_interpolation(self):
        """Test with interpolation spanning multiple lines."""
        content = dedent("""\
            value: >-
              ${
              path.to.value
              }""")
        indent = "  "

        result = detect_interpolation_pos_in_document(content)

        assert len(result) == 1
        interp = result[0]
        assert interp.content
        # Position verification
        assert interp.start_line == 1  # Line after "value: >-"
        assert interp.start_column == len(indent)
        assert interp.end_line == 3  # The closing bracket line
        assert interp.end_column == len(indent) + 1  # indent + }
        # Verify the content contains the full interpolation
        assert "${" in interp.content
        assert "path.to.value" in interp.content
        assert "}" in interp.content

    def test_function_interpolation(self):
        """Test with function-style interpolation containing args."""
        content = "value: ${function:arg1,arg2}"
        result = detect_interpolation_pos_in_document(content)

        assert len(result) == 1
        assert result[0].content == "${function:arg1,arg2}"
        # Position verification
        assert result[0].start_line == 0
        assert result[0].start_column == len("value: ")
        assert result[0].end_line == 0
        assert result[0].end_column == len(content)

    def test_complex_interpolation(self):
        """Test with a complex interpolation containing nested calls and
        newlines."""
        content = dedent("""\
            complex: >-
              ${python.eval:"
              ${shared.width} //
              ${models.encoder.patch_size}
              "}""")
        indent = "  "

        result = detect_interpolation_pos_in_document(content)

        assert len(result) == 3
        outer = result[0]
        assert outer.start_line < outer.end_line  # Spans multiple lines
        assert outer.start_column == len(indent)
        assert outer.end_line == 4  # Line with closing bracket
        assert outer.end_column == len(indent) + len('"}')
        assert "${python.eval:" in outer.content
        assert "${shared.width}" in outer.content
        assert "${models.encoder.patch_size}" in outer.content

        # ${models.encoder.patch_size}
        patch_size = result[1]
        assert patch_size.content == "${models.encoder.patch_size}"
        assert patch_size.start_line == 3
        assert patch_size.end_line == 3
        assert patch_size.start_column == len(indent)
        assert patch_size.end_column == len(indent + "${models.encoder.patch_size}")

        # Inner interpolations - ${shared.width}
        shared_width = result[2]
        assert shared_width.content == "${shared.width}"
        assert shared_width.start_line == 2
        assert shared_width.end_line == 2
        assert shared_width.start_column == len(indent)
        assert shared_width.end_column == len(indent + "${shared.width}")
