"""Tests for Hydra YAML special key value completion functionality."""

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.special_key_value import (
    extract_special_key_from_line,
    get_args_completions,
    get_convert_completions,
    get_hydra_special_key_value_completions,
    get_partial_completions,
    get_recursive_completions,
)
from hydra_yaml_lsp.constants import HydraConvertValue, HydraSpecialKey


class TestExtractSpecialKeyFromLine:
    """Tests for extracting Hydra special key from a line."""

    def test_valid_special_key(self):
        """Test with a valid special key."""
        line = "  _target_: module.path"
        result = extract_special_key_from_line(line, 15)
        assert result == HydraSpecialKey.TARGET

    def test_no_colon(self):
        """Test with line without a colon."""
        line = "  _target_ module.path"
        result = extract_special_key_from_line(line, 15)
        assert result is None

    def test_not_a_special_key(self):
        """Test with a non-special key."""
        line = "  regular_key: value"
        result = extract_special_key_from_line(line, 15)
        assert result is None

    def test_cursor_before_colon(self):
        """Test with cursor before the colon."""
        line = "  _target_: value"
        result = extract_special_key_from_line(line, 5)
        assert result is None


class TestGetPartialCompletions:
    """Tests for _partial_ value completions."""

    def test_completion_items(self):
        """Test completion items structure."""
        items = get_partial_completions()

        assert len(items) == 2
        assert items[0].label == "true"
        assert items[1].label == "false"
        # True should have higher priority
        assert items[0].sort_text < items[1].sort_text
        assert items[0].kind == lsp.CompletionItemKind.Value


class TestGetRecursiveCompletions:
    """Tests for _recursive_ value completions."""

    def test_completion_items(self):
        """Test completion items structure."""
        items = get_recursive_completions()

        assert len(items) == 2
        assert items[0].label == "false"
        assert items[1].label == "true"
        # False should have higher priority
        assert items[0].sort_text < items[1].sort_text
        assert items[0].kind == lsp.CompletionItemKind.Value


class TestGetConvertCompletions:
    """Tests for _convert_ value completions."""

    def test_completion_items(self):
        """Test completion items structure."""
        items = get_convert_completions()

        assert len(items) == 4
        values = [item.label for item in items]

        # Check all values are present
        for value in HydraConvertValue:
            assert value in values

        # Check ordering by sort_text
        for i, item in enumerate(items):
            assert item.sort_text == str(i)
            assert item.kind == lsp.CompletionItemKind.Value


class TestGetArgsCompletions:
    """Tests for _args_ value completions."""

    def test_completion_items(self):
        """Test completion items structure."""
        items = get_args_completions()

        assert len(items) == 2

        # List brackets option
        list_brackets = next(item for item in items if item.label == "[]")
        assert list_brackets.insert_text == "[$0]"
        assert list_brackets.insert_text_format == lsp.InsertTextFormat.Snippet

        # List item option
        list_item = next(item for item in items if item.label == "- item")
        assert list_item.insert_text == "\n- $0"
        assert list_item.insert_text_format == lsp.InsertTextFormat.Snippet
        assert list_item.insert_text_mode == lsp.InsertTextMode.AdjustIndentation


class TestGetHydraSpecialKeyValueCompletions:
    """Tests for the get_hydra_special_key_value_completions function."""

    def test_partial_value_completions(self, mocker):
        """Test completions for _partial_ values."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  _partial_: "]
        position = lsp.Position(line=0, character=12)

        # Mock is_typing_value to return True

        completions = get_hydra_special_key_value_completions(doc, position)

        assert len(completions) == 2
        assert completions[0].label == "true"
        assert completions[1].label == "false"

    def test_recursive_value_completions(self, mocker):
        """Test completions for _recursive_ values."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  _recursive_: "]
        position = lsp.Position(line=0, character=14)

        # Mock is_typing_value to return True

        completions = get_hydra_special_key_value_completions(doc, position)

        assert len(completions) == 2
        assert completions[0].label == "false"
        assert completions[1].label == "true"

    def test_convert_value_completions(self, mocker):
        """Test completions for _convert_ values."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  _convert_: "]
        position = lsp.Position(line=0, character=12)

        # Mock is_typing_value to return True

        completions = get_hydra_special_key_value_completions(doc, position)

        assert len(completions) == 4
        labels = [item.label for item in completions]
        for value in HydraConvertValue:
            assert value in labels

    def test_args_value_completions(self, mocker):
        """Test completions for _args_ values."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  _args_: "]
        position = lsp.Position(line=0, character=10)

        # Mock is_typing_value to return True

        completions = get_hydra_special_key_value_completions(doc, position)

        assert len(completions) == 2
        assert any(item.label == "[]" for item in completions)
        assert any(item.label == "- item" for item in completions)

    def test_not_typing_value(self, mocker):
        """Test when not typing a value."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  _partial_: "]
        position = lsp.Position(line=0, character=5)

        # Mock is_typing_value to return False

        completions = get_hydra_special_key_value_completions(doc, position)
        assert len(completions) == 0

    def test_line_out_of_range(self, mocker):
        """Test when line is out of range."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=1, character=0)

        # Mock is_typing_value to return True

        completions = get_hydra_special_key_value_completions(doc, position)
        assert len(completions) == 0
