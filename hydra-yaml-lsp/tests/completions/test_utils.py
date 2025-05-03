from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.utils import (
    is_typing_key,
)


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

    def test_after_colon(self, mocker):
        """Test when cursor is after the colon (typing a value)."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key: "]
        position = lsp.Position(line=0, character=10)

        assert is_typing_key(doc, position) is False

    def test_before_colon(self, mocker):
        """Test when cursor is before the colon (still typing a key)."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  my_key: value"]
        position = lsp.Position(line=0, character=9)

        assert is_typing_key(doc, position) is False

    def test_comment_line(self, mocker):
        """Test with a comment line."""
        doc = mocker.Mock(spec=Document)
        doc.lines = ["  # comment"]
        position = lsp.Position(line=0, character=10)

        assert is_typing_key(doc, position) is False
