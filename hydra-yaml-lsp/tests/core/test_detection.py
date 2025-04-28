"""Tests for the special_keys module."""

import pytest

from hydra_yaml_lsp.core.detection import (
    SpecialKeyPosition,
    detect_special_key,
    detect_special_keys_in_document,
)


class TestSpecialKeys:
    """Test cases for special key detection in Hydra YAML files."""

    @pytest.mark.parametrize(
        "line, expected_result",
        [
            ("_target_: path.to.class", (0, 8, "_target_")),
            ("  _args_: some args", (2, 8, "_args_")),
            ("- _arg_: value", (2, 7, "_arg_")),
            ("_config_   : value", (0, 8, "_config_")),
            ("normal: value", None),
            ("normal: value # _comment_: ignored", None),
            ("_target_: value # This is a comment", (0, 8, "_target_")),
        ],
        ids=[
            "simple_key",
            "indented_key",
            "list_item_key",
            "key_with_spaces",
            "no_special_key",
            "key_in_comment",
            "key_with_comment",
        ],
    )
    def test_detect_special_key(self, line, expected_result):
        """Test the detect_special_key function with various inputs."""
        result = detect_special_key(line)
        assert result == expected_result


class TestDocumentSpecialKeys:
    """Test cases for document-level special key detection in Hydra YAML
    files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_special_keys_in_document("")
        assert result == []

    def test_document_with_no_special_keys(self):
        """Test with a document containing no special keys."""
        content = "regular: value\nanother: item\nthird: element"
        result = detect_special_keys_in_document(content)
        assert result == []

    @pytest.mark.parametrize(
        "content, expected",
        [
            (
                "_target_: module.path\nregular: value\n  _args_: some args",
                [
                    SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
                    SpecialKeyPosition(lineno=2, start=2, end=8, key="_args_"),
                ],
            ),
            (
                "_target_: value # comment\nregular: value # _ignored_: test",
                [
                    SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
                ],
            ),
            (
                "\n_target_: value\n\nregular: value\n_args_: more\n",
                [
                    SpecialKeyPosition(lineno=1, start=0, end=8, key="_target_"),
                    SpecialKeyPosition(lineno=4, start=0, end=6, key="_args_"),
                ],
            ),
            (
                "_target_: value _arg_: test\n_more_: content",
                [
                    SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
                    SpecialKeyPosition(lineno=1, start=0, end=6, key="_more_"),
                ],
            ),
        ],
        ids=[
            "basic_special_keys",
            "keys_in_comments",
            "empty_lines",
            "multiple_keys_per_line",
        ],
    )
    def test_document_with_special_keys(self, content, expected):
        """Test document with various special key arrangements."""
        result = detect_special_keys_in_document(content)
        assert result == expected
