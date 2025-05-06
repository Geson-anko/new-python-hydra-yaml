"""Tests for YAML utility functions."""

from hydra_yaml_lsp.utils import clean_yaml_block_lines, get_yaml_block_lines


class TestGetYamlBlockLines:
    """Test cases for get_yaml_block_lines function."""

    def test_basic_block(self):
        """Test basic extraction of a simple YAML block."""
        yaml_content = [
            "key1: value1",
            "key2: value2",
            "key3: value3",
        ]
        result = get_yaml_block_lines(yaml_content, 1)
        assert result == yaml_content

    def test_nested_block(self):
        """Test extraction of a nested block."""
        yaml_content = [
            "parent:",
            "  child1: value1",
            "  child2: value2",
            "another_parent:",
            "  another_child: value",
        ]
        result = get_yaml_block_lines(yaml_content, 1)
        assert result == ["  child1: value1", "  child2: value2"]

    def test_sequence_blocks_backward(self):
        """Test how sequence blocks are handled in backward search."""
        yaml_content = [
            "items:",
            "  - item1: value1",
            "  - item2: value2",
            "  regular_key: value",
            "other_key: value",
        ]
        # According to the function, backward search includes sequences at the same level
        result = get_yaml_block_lines(yaml_content, 3)
        # This should include the sequence items since backward search doesn't exclude them
        assert result == ["  regular_key: value"]

    def test_sequence_blocks_forward(self):
        """Test how sequence blocks are handled in forward search."""
        yaml_content = [
            "items:",
            "  regular_key: value",
            "  - item1: value1",
            "  - item2: value2",
            "other_key: value",
        ]
        # According to the function, forward search excludes sequences at the same level
        result = get_yaml_block_lines(yaml_content, 1)
        # This should NOT include the sequence items since forward search excludes them
        assert result == ["  regular_key: value"]

    def test_sequence_item_properties(self):
        """Test extraction of sequence item properties."""
        yaml_content = [
            "items:",
            "  - item1: value1",
            "    item1_prop: prop1",
            "  - item2: value2",
            "    item2_prop: prop2",
        ]
        result = get_yaml_block_lines(yaml_content, 2)
        assert result == ["  - item1: value1", "    item1_prop: prop1"]

    def test_with_comments_and_empty_lines(self):
        """Test with comments and empty lines."""
        yaml_content = [
            "key1: value1",
            "",
            "# This is a comment",
            "key2: value2",
            "# Another comment",
            "key3: value3",
        ]
        result = get_yaml_block_lines(yaml_content, 3)
        assert result == ["key1: value1", "key2: value2", "key3: value3"]

    def test_first_line(self):
        """Test when specified line is the first line."""
        yaml_content = [
            "key1: value1",
            "key2: value2",
        ]
        result = get_yaml_block_lines(yaml_content, 0)
        assert result == yaml_content

    def test_last_line(self):
        """Test when specified line is the last line."""
        yaml_content = [
            "key1: value1",
            "key2: value2",
        ]
        result = get_yaml_block_lines(yaml_content, 1)
        assert result == yaml_content

    def test_empty_yaml(self):
        """Test with an empty YAML file."""
        assert get_yaml_block_lines([], 0) == []

    def test_line_out_of_range(self):
        """Test with a line number out of range."""
        yaml_content = ["key: value"]
        assert get_yaml_block_lines(yaml_content, 1) == []

    def test_mixed_indent_levels(self):
        """Test with mixed indentation levels."""
        yaml_content = [
            "key1:",
            "  nested1: value1",
            "    deeply_nested: value",
            "  nested2: value2",
            "key2: value",
        ]
        # Test for a deeply nested item
        result = get_yaml_block_lines(yaml_content, 2)
        assert result == ["    deeply_nested: value"]

        # Test for a regular nested item
        result = get_yaml_block_lines(yaml_content, 1)
        assert result == ["  nested1: value1", "  nested2: value2"]

    def test_line_with_sequence_marker(self):
        """Test when the specified line starts with a sequence marker."""
        yaml_content = ["list:", "  - item1", "  - item2", "  - item3", "other: value"]
        result = get_yaml_block_lines(yaml_content, 2)
        # This should include all items at the same level
        assert result == ["  - item2"]

    def test_multiline_strings(self):
        """Test with multiline strings."""
        yaml_content = [
            "multiline_key: >",
            "  This is a multiline",
            "  string in YAML",
            "  that spans multiple lines",
            "next_key: value",
        ]
        # The function treats each line separately based on indentation
        result = get_yaml_block_lines(yaml_content, 0)
        # This would include only lines at the same indent level as line 0
        assert result == ["multiline_key: >", "next_key: value"]

        # Lines of the multiline string at the same indent level would be grouped
        result = get_yaml_block_lines(yaml_content, 1)
        assert result == [
            "  This is a multiline",
            "  string in YAML",
            "  that spans multiple lines",
        ]


class TestCleanYamlBlockLines:
    """Test cases for clean_yaml_block_lines function."""

    def test_basic_indentation_and_sequence_markers(self):
        """Test with basic indentation and sequence markers."""
        block_lines = ["  - aaa: 0", "     bbb: 1", "     ccc: 2"]
        result = clean_yaml_block_lines(block_lines)
        assert result == ["aaa: 0", "bbb: 1", "ccc: 2"]

    def test_mixed_indentation(self):
        """Test with mixed indentation styles."""
        block_lines = ["  key1: value1", "    key2: value2", "  - key3: value3"]
        result = clean_yaml_block_lines(block_lines)
        assert result == ["key1: value1", "key2: value2", "key3: value3"]

    def test_with_empty_lines(self):
        """Test with empty lines that should be filtered out."""
        block_lines = ["  key1: value1", "", "  key2: value2"]
        result = clean_yaml_block_lines(block_lines)
        assert result == ["key1: value1", "key2: value2"]

    def test_empty_input(self):
        """Test with empty input list."""
        assert clean_yaml_block_lines([]) == []
