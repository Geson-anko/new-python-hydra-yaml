"""Tests for Hydra YAML completion functionality."""

import pytest
from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.special_key import (
    get_hydra_special_key_completions,
    is_typing_key,
)
from hydra_yaml_lsp.constants import HydraSpecialKey


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


class TestGetHydraSpecialKeyCompletions:
    """Tests for the get_hydra_special_key_completions function."""

    def test_no_existing_keys(self, mocker):
        """Test completion suggestions when no keys exist in the current
        block."""
        # Create a document with an empty block
        doc = mocker.Mock(spec=Document)
        doc.lines = ["component:", "  "]  # Empty block with proper indentation
        position = lsp.Position(line=1, character=2)

        completions = get_hydra_special_key_completions(doc, position)

        # Should suggest all special keys
        assert (
            len(completions) == len(HydraSpecialKey) - 2
        )  # remove _args_ and _partial_

        # Check structure of a completion item
        item = completions[0]
        assert isinstance(item, lsp.CompletionItem)
        assert item.kind == lsp.CompletionItemKind.Keyword
        assert item.insert_text is not None
        assert item.insert_text.endswith(": ")

    def test_with_existing_keys(self, mocker):
        """Test completion with target key already existing in the block."""
        # Create a document with a block containing _target_
        doc = mocker.Mock(spec=Document)
        doc.lines = [
            "component:",
            "  _target_: sample.module",
            "  ",  # Current position
        ]
        position = lsp.Position(line=2, character=2)

        completions = get_hydra_special_key_completions(doc, position)

        # Should not suggest _target_ since it already exists
        assert len(completions) == len(HydraSpecialKey) - 1
        assert all(item.label != HydraSpecialKey.TARGET for item in completions)
        # Should suggest other keys
        assert len(completions) > 0

    def test_target_dependent_keys(self, mocker):
        """Test that target-dependent keys are only suggested when _target_
        exists."""
        # Without _target_
        doc_without_target = mocker.Mock(spec=Document)
        doc_without_target.lines = [
            "component:",
            "  ",  # Current position
        ]
        position = lsp.Position(line=1, character=2)

        completions_without_target = get_hydra_special_key_completions(
            doc_without_target, position
        )

        # Should not suggest _args_ or _partial_ without _target_
        target_dependent_keys = [HydraSpecialKey.ARGS, HydraSpecialKey.PARTIAL]
        assert not any(
            item.label in target_dependent_keys for item in completions_without_target
        )

        # With _target_
        doc_with_target = mocker.Mock(spec=Document)
        doc_with_target.lines = [
            "component:",
            "  _target_: sample.module",
            "  ",  # Current position
        ]

        completions_with_target = get_hydra_special_key_completions(
            doc_with_target, position
        )

        # Should now suggest _args_ and _partial_
        assert any(
            item.label == HydraSpecialKey.ARGS for item in completions_with_target
        )
        assert any(
            item.label == HydraSpecialKey.PARTIAL for item in completions_with_target
        )
