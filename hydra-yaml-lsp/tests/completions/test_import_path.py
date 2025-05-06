"""Tests for Hydra YAML import path completion functionality."""

from textwrap import dedent

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.import_path import (
    extract_import_path,
    get_completion_for_import_path,
    get_import_path_completions,
    get_module_members,
    get_top_level_modules,
    is_typing_path_value,
    is_typing_target_value,
)
from hydra_yaml_lsp.constants import HydraSpecialKey


class TestIsTypingPathValue:
    """Tests for is_typing_path_value function."""

    def test_not_path_line(self):
        """Test when not on a path line."""
        doc = Document("file:///test.yaml", "  other_key: value")
        position = lsp.Position(line=0, character=12)

        result = is_typing_path_value(doc, position)
        assert result is False

    def test_no_target_in_block(self):
        """Test when no _target_ with utility function in block."""
        yaml_content = dedent("""\
            component:
            regular_key: value
            path: some.module
            """).strip()
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=15)

        result = is_typing_path_value(doc, position)
        assert result is False

    def test_with_target_utility_function(self):
        """Test with _target_ containing a utility function."""
        yaml_content = dedent("""\
            component:
            _target_: hydra.utils.get_method
            path: some.module
            """).strip()
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=15)

        result = is_typing_path_value(doc, position)
        assert result is True


class TestIsTypingTargetValue:
    """Tests for is_typing_target_value function."""

    def test_not_target_line(self):
        """Test when not on a _target_ line."""
        doc = Document("file:///test.yaml", "  other_key: value")
        position = lsp.Position(line=0, character=12)

        result = is_typing_target_value(doc, position)
        assert result is False

    def test_is_target_line(self):
        """Test when on a _target_ line."""
        doc = Document("file:///test.yaml", f"  {HydraSpecialKey.TARGET}: module")
        position = lsp.Position(line=0, character=20)

        result = is_typing_target_value(doc, position)
        assert result is True


class TestExtractImportPath:
    """Tests for extract_import_path function."""

    def test_extract_path(self):
        """Test extracting path from line."""
        doc = Document("file:///test.yaml", "  path: module.submodule")
        position = lsp.Position(line=0, character=20)

        path = extract_import_path(doc, position)
        assert path == "module.submodule"

    def test_extract_target(self):
        """Test extracting target from line."""
        doc = Document("file:///test.yaml", f"  {HydraSpecialKey.TARGET}: module.Class")
        position = lsp.Position(line=0, character=25)

        path = extract_import_path(doc, position)
        assert path == "module.Class"

    def test_no_value(self):
        """Test when line has no value part."""
        doc = Document("file:///test.yaml", "  key_without_colon")
        position = lsp.Position(line=0, character=10)

        path = extract_import_path(doc, position)
        assert path == ""


class TestGetModuleMembers:
    """Tests for get_module_members function."""

    def test_os_module(self):
        """Test with the os module."""
        members = get_module_members("os")

        # Verify some known members of os
        member_names = [name for name, _ in members]
        assert "path" in member_names
        assert "environ" in member_names
        assert "getcwd" in member_names

        # Verify types
        member_dict = {name: kind for name, kind in members}
        assert member_dict["path"] == lsp.CompletionItemKind.Module
        assert member_dict["getcwd"] == lsp.CompletionItemKind.Function

    def test_os_path_module(self):
        """Test with the os.path module."""
        members = get_module_members("os.path")

        member_names = [name for name, _ in members]
        assert "join" in member_names
        assert "exists" in member_names
        assert "isfile" in member_names

    def test_module_not_found(self):
        """Test with a non-existent module."""
        members = get_module_members("non_existent_module_xyz123")
        assert members == tuple()


class TestGetTopLevelModules:
    """Tests for get_top_level_modules function."""

    def test_standard_modules_included(self):
        """Test that standard modules are included."""
        modules = get_top_level_modules()

        # Check some modules that should always be available
        assert "os" in modules
        assert "sys" in modules
        assert "builtins" in modules
        assert "inspect" in modules
        assert "json" in modules


class TestGetCompletionForImportPath:
    """Tests for get_completion_for_import_path function."""

    def test_empty_prefix(self):
        """Test with empty prefix."""
        completions = get_completion_for_import_path("")

        # Should have many modules
        assert len(completions) > 20

        # Check some common modules
        completion_labels = [item.label for item in completions]
        assert "os" in completion_labels
        assert "json" in completion_labels

        # Check completion item properties
        os_item = next(item for item in completions if item.label == "os")
        assert os_item.kind == lsp.CompletionItemKind.Module
        assert os_item.insert_text == "os"

    def test_module_prefix(self):
        """Test with a module prefix."""
        completions = get_completion_for_import_path("j")

        completion_labels = [item.label for item in completions]
        assert "json" in completion_labels
        assert all(label.startswith("j") for label in completion_labels)

    def test_dotted_path(self):
        """Test with a dotted path."""
        completions = get_completion_for_import_path("os.path.")

        completion_labels = [item.label for item in completions]
        assert "join" in completion_labels
        assert "exists" in completion_labels
        assert "isfile" in completion_labels


class TestGetImportPathCompletions:
    """Tests for get_import_path_completions function."""

    def test_not_typing_value(self):
        """Test when not typing a value."""
        doc = Document("file:///test.yaml", "key")
        position = lsp.Position(line=0, character=1)

        completions = get_import_path_completions(doc, position)
        assert completions == []

    def test_path_value_with_utility_target(self):
        """Test completions when typing a path value with utility target."""
        yaml_content = dedent("""\
            component:
            _target_: hydra.utils.get_method
            path: os.
            """).strip()
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=10)  # Just after "os."

        completions = get_import_path_completions(doc, position)

        # Should have os module members
        completion_labels = [item.label for item in completions]
        assert "path" in completion_labels
        assert "environ" in completion_labels
        assert "getcwd" in completion_labels

    def test_target_value(self):
        """Test completions when typing a target value."""
        doc = Document("file:///test.yaml", f"  {HydraSpecialKey.TARGET}: os.")
        position = lsp.Position(line=0, character=13)  # Just after "os."

        completions = get_import_path_completions(doc, position)

        # Should have os module members
        completion_labels = [item.label for item in completions]
        assert "path" in completion_labels
        assert "environ" in completion_labels

    def test_line_out_of_range(self):
        """Test when line is out of range."""
        doc = Document("file:///test.yaml", "")
        position = lsp.Position(line=1, character=0)  # Line doesn't exist

        # Should return empty list without error
        completions = get_import_path_completions(doc, position)
        assert completions == []

    def test_fully_qualified_path(self):
        """Test with a fully qualified path."""
        yaml_content = dedent("""\
            component:
            _target_: hydra.utils.get_method
            path: os.path.join
            """).strip()
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=17)  # End of "os.path.join"

        # Should not error, might not find completions depending on cursor position
        get_import_path_completions(doc, position)
