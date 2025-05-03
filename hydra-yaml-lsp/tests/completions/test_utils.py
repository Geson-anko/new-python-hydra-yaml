"""Tests for YAML completion utility functions."""

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.utils import (
    is_typing_comment,
    is_typing_key,
    is_typing_value,
)


class TestIsTypingComment:
    """Tests for the is_typing_comment function."""

    def test_empty_line(self, mocker):
        """Test with an empty line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=0, character=0)

        assert is_typing_comment(doc, position) is False

    def test_comment_line(self, mocker):
        """Test with a comment line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  # comment"]
        position = lsp.Position(line=0, character=10)

        assert is_typing_comment(doc, position) is True

    def test_non_comment_line(self, mocker):
        """Test with a non-comment line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  key: value"]
        position = lsp.Position(line=0, character=5)

        assert is_typing_comment(doc, position) is False

    def test_line_out_of_range(self, mocker):
        """Test when line is out of range."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=1, character=0)

        assert is_typing_comment(doc, position) is False


class TestIsTypingKey:
    """Tests for the is_typing_key function."""

    def test_empty_line(self, mocker):
        """Test with an empty line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=0, character=0)

        assert is_typing_key(doc, position) is True

    def test_typing_key_no_colon(self, mocker):
        """Test when typing a key without a colon yet."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key"]
        position = lsp.Position(line=0, character=8)

        assert is_typing_key(doc, position) is True

    def test_cursor_before_colon(self, mocker):
        """Test when cursor is before the colon in a key-value pair."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key: value"]
        position = lsp.Position(line=0, character=6)  # Before the colon

        assert is_typing_key(doc, position) is True

    def test_cursor_at_colon(self, mocker):
        """Test when cursor is at the colon in a key-value pair."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key: value"]
        position = lsp.Position(line=0, character=len("  my_key:"))  # At the colon

        assert is_typing_key(doc, position) is False

    def test_cursor_after_colon(self, mocker):
        """Test when cursor is after the colon in a key-value pair."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key: value"]
        position = lsp.Position(line=0, character=9)  # After the colon

        assert is_typing_key(doc, position) is False

    def test_comment_line(self, mocker):
        """Test with a comment line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  # comment"]
        position = lsp.Position(line=0, character=10)

        assert is_typing_key(doc, position) is False

    def test_line_out_of_range(self, mocker):
        """Test when line is out of range."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=1, character=0)

        assert is_typing_key(doc, position) is True


class TestIsTypingValue:
    """Tests for the is_typing_value function."""

    def test_empty_line(self, mocker):
        """Test with an empty line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=0, character=0)

        assert is_typing_value(doc, position) is False

    def test_typing_value(self, mocker):
        """Test when typing a value."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  key: value"]
        position = lsp.Position(line=0, character=10)

        assert is_typing_value(doc, position) is True

    def test_typing_key(self, mocker):
        """Test when typing a key."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  key"]
        position = lsp.Position(line=0, character=5)

        assert is_typing_value(doc, position) is False

    def test_comment_line(self, mocker):
        """Test with a comment line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  # comment"]
        position = lsp.Position(line=0, character=10)

        assert is_typing_value(doc, position) is False

    def test_line_out_of_range(self, mocker):
        """Test when line is out of range."""
        doc = mocker.Mock(spec=Document)
        doc.lines = [""]
        position = lsp.Position(line=1, character=0)

        assert is_typing_value(doc, position) is False
