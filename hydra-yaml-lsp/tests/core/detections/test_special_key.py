import pytest

from hydra_yaml_lsp.core.detections.special_key import (
    SpecialKeyPosition,
    detect_special_keys,
)


class TestDocumentSpecialKeys:
    """Test cases for document-level special key detection in Hydra YAML
    files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_special_keys("")
        assert result == ()

    def test_document_with_no_special_keys(self):
        """Test with a document containing no special keys."""
        content = "regular: value\nanother: item\nthird: element"
        result = detect_special_keys(content)
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
        result = detect_special_keys(content)
        assert result == expected

    def test_not_hydra_special_key(self):
        result = detect_special_keys("_nothydraspecial_: value")
        assert len(result) == 0

    def test_caching(self):
        """Test that results are cached properly."""
        content = "_target_: module.path\n_args_: value"

        # First call should compute the result
        result1 = detect_special_keys(content)

        # Second call should use the cached result
        result2 = detect_special_keys(content)

        # Results should be identical
        assert result1 == result2

        # And should be the expected values
        expected = (
            SpecialKeyPosition(lineno=0, start=0, end=8, key="_target_"),
            SpecialKeyPosition(lineno=1, start=0, end=6, key="_args_"),
        )
        assert result1 == expected

        # Check cache info
        info = detect_special_keys.cache_info()
        assert info.hits >= 1
