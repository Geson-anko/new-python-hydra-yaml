"""Tests for the special_keys module."""

import pytest

from hydra_yaml_lsp.core.detection import detect_special_key


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
