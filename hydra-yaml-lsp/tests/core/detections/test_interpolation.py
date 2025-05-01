from textwrap import dedent

from hydra_yaml_lsp.core.detections.interpolation import (
    InterpolationHighlight,
    InterpolationPosition,
    detect_interpolation_positions,
)


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

    def test_get_highlights_reference(self):
        """Test get_highlights for reference interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=30,
            content="${reference.path}",
        )

        highlights = interp.get_highlights()
        assert len(highlights) == 3

        # Check opening bracket
        assert highlights[0].token_type == "bracket_open"
        assert highlights[0].content == "${"
        assert highlights[0].start_line == 5
        assert highlights[0].start_column == 10
        assert highlights[0].end_column == 12

        # Check reference
        assert highlights[1].token_type == "reference"
        assert highlights[1].content == "reference.path"

        # Check closing bracket
        assert highlights[2].token_type == "bracket_close"
        assert highlights[2].content == "}"
        assert highlights[2].start_line == 5
        assert highlights[2].start_column == 29
        assert highlights[2].end_column == 30

    def test_get_highlights_function(self):
        """Test get_highlights for function interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=5,
            end_column=40,
            content="${function:arg1,arg2}",
        )

        highlights = interp.get_highlights()
        assert len(highlights) == 3

        # Check opening bracket
        assert highlights[0].token_type == "bracket_open"

        # Check function
        assert highlights[1].token_type == "function"
        assert highlights[1].content == "function"

        # Check closing bracket
        assert highlights[2].token_type == "bracket_close"
        assert highlights[2].content == "}"

    def test_get_highlights_multiline(self):
        """Test get_highlights for multiline interpolation."""
        interp = InterpolationPosition(
            start_line=5,
            start_column=10,
            end_line=7,
            end_column=5,
            content="${\nreference.path\n}",
        )

        highlights = interp.get_highlights()
        assert len(highlights) == 3

        # Check opening bracket
        assert highlights[0].start_line == 5
        assert highlights[0].start_column == 10

        # Check reference
        assert highlights[1].token_type == "reference"
        assert highlights[1].start_line == 6

        # Check closing bracket
        assert highlights[2].token_type == "bracket_close"
        assert highlights[2].start_line == 7
        assert highlights[2].end_column == 5


class TestInterpolationDetection:
    """Test cases for detecting interpolation patterns in Hydra YAML files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_interpolation_positions("")
        assert result == ()

    def test_document_with_no_interpolations(self):
        """Test with a document containing no interpolations."""
        content = "regular: value\nanother: item\nthird: element"
        result = detect_interpolation_positions(content)
        assert result == ()

    def test_simple_interpolation(self):
        """Test with a simple interpolation."""
        content = "value: ${path.to.value}"
        result = detect_interpolation_positions(content)

        assert len(result) == 1
        assert result[0].content == "${path.to.value}"
        assert result[0].start_line == 0
        assert result[0].end_line == 0
        assert result[0].start_column == len("value: ")
        assert result[0].end_column == len(content)

    def test_multiple_interpolations(self):
        """Test with multiple interpolations in the same document."""
        content = "value1: ${path1}\nvalue2: ${path2}"
        result = detect_interpolation_positions(content)

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

        result = detect_interpolation_positions(content)

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
        result = detect_interpolation_positions(content)

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

        result = detect_interpolation_positions(content)

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
