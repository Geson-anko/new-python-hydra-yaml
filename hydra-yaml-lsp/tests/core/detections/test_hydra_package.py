from hydra_yaml_lsp.core.detections.hydra_package import (
    AT_PACKAGE,
    detect_hydra_package,
)


class TestHydraPackageDetection:
    """Test cases for Hydra package declaration detection."""

    def test_empty_content(self):
        """Test with empty content."""
        result = detect_hydra_package("")
        assert result is None

    def test_no_package_declaration(self):
        """Test with content having no package declaration."""
        content = "# This is a regular comment\nkey: value"
        result = detect_hydra_package(content)
        assert result is None

    def test_simple_package_declaration(self):
        """Test with a simple package declaration."""
        content = "# @package foo\nkey: value"
        result = detect_hydra_package(content)

        assert result is not None
        assert result.package_name.content == "foo"
        assert result.package_name.start == content.find("foo")
        assert result.package_name.end == content.find("foo") + len("foo")
        assert result.at_package_start == content.find(AT_PACKAGE)
        assert result.at_package_end == content.find(AT_PACKAGE) + len(AT_PACKAGE)
        assert result.content == "# @package foo"

    def test_hierarchical_package_declaration(self):
        """Test with a hierarchical package declaration."""
        content = "# @package foo.bar.baz\nkey: value"
        result = detect_hydra_package(content)

        assert result is not None
        assert result.package_name.content == "foo.bar.baz"
        assert result.package_name.start == content.find("foo.bar.baz")
        assert result.package_name.end == content.find("foo.bar.baz") + len(
            "foo.bar.baz"
        )

    def test_package_with_extra_whitespace(self):
        """Test with package declaration containing extra whitespace."""
        content = "#    @package    foo   \nkey: value"
        result = detect_hydra_package(content)

        assert result is not None
        assert result.package_name.content == "foo"

    def test_package_with_trailing_comment(self):
        """Test with package declaration containing trailing comment."""
        content = "# @package foo # another comment\nkey: value"
        result = detect_hydra_package(content)
        assert result is not None
        assert result.package_name.content == "foo"

    def test_incorrect_format(self):
        """Test with incorrectly formatted package declarations."""
        # No space after @package
        content = "# @packagefoo\nkey: value"
        result = detect_hydra_package(content)
        assert result is None

        # No space after #
        content = "#@package foo\nkey: value"
        result = detect_hydra_package(content)
        assert result is None

        # No package name
        content = "# @package\nkey: value"
        result = detect_hydra_package(content)
        assert result is None
