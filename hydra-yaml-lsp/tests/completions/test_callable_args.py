"""Tests for Hydra YAML callable argument completion functionality."""

from textwrap import dedent

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.callable_arg import (
    extract_target_value_from_block,
    get_callable_arg_completions,
    get_callable_args,
    get_existing_keys_in_block,
)


class TestExtractTargetValueFromBlock:
    """Tests for extract_target_value_from_block function."""

    def test_with_target(self):
        """Test with block containing _target_."""
        block = ["  _target_: sample_python_project.YourClass", "  arg1: value"]
        result = extract_target_value_from_block(block)
        assert result == "sample_python_project.YourClass"

    def test_without_target(self):
        """Test with block not containing _target_."""
        block = ["  key1: value1", "  key2: value2"]
        result = extract_target_value_from_block(block)
        assert result is None

    def test_with_indented_target(self):
        """Test with indented _target_."""
        block = ["      _target_: sample_python_project.YourClass", "      arg1: value"]
        result = extract_target_value_from_block(block)
        assert result == "sample_python_project.YourClass"


class TestGetExistingKeysInBlock:
    """Tests for get_existing_keys_in_block function."""

    def test_with_keys(self):
        """Test with block containing keys."""
        block = ["  arg1: value1", "  arg2: value2", "  _target_: module.Class"]
        result = get_existing_keys_in_block(block)
        assert result == {"arg1", "arg2"}

    def test_with_no_keys(self):
        """Test with block containing no keys."""
        block = ["  # Comment", "  "]
        result = get_existing_keys_in_block(block)
        assert result == set()

    def test_with_special_keys(self):
        """Test that special keys are not included."""
        block = [
            "  _target_: module.Class",
            "  _args_: [1, 2]",
            "  arg1: value",
            "  _partial_: true",
        ]
        result = get_existing_keys_in_block(block)
        assert result == {"arg1"}


class TestGetCallableArgs:
    """Tests for get_callable_args function."""

    def test_valid_function(self):
        """Test with a valid function."""
        # Using a sample function from the test modules
        result = get_callable_args("tests.target_objects.function_with_args")
        assert "arg0" in result
        assert "arg1" in result
        assert "args" not in result
        assert "kwds" not in result

    def test_valid_class(self):
        """Test with a valid class."""
        # Using a sample class from sample_python_project
        result = get_callable_args("tests.target_objects.Class")
        assert "self" not in result
        assert "arg" in result

    def test_class_method(self):
        """Test with a class method."""
        result = get_callable_args("tests.target_objects.Class.class_method_with_args")
        assert "arg" in result
        # cls should be filtered out
        assert "cls" not in result

    def test_non_callable(self):
        """Test with a non-callable object."""
        result = get_callable_args("tests.target_objects.CONSTANT")
        assert result is None

    def test_nonexistent_path(self):
        """Test with a non-existent import path."""
        result = get_callable_args("nonexistent.module.path")
        assert result is None


class TestGetCallableArgCompletions:
    """Tests for get_callable_arg_completions function."""

    def test_with_valid_callable(self, mocker):
        """Test completions with a valid callable."""
        yaml_content = dedent("""\
            component:
              _target_: tests.target_objects.function_with_args
              a
            """)
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=2)  # New line after _target_

        completions = get_callable_arg_completions(doc, position)

        assert len(completions) == 2
        labels = [item.label for item in completions]
        assert "arg0" in labels
        assert "arg1" in labels

    def test_with_existing_args(self, mocker):
        """Test completions with some args already present."""
        yaml_content = dedent("""\
            component:
              _target_: tests.target_objects.function_with_args
              arg0: 10
              a
            """)
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=3, character=2)  # New line after arg1

        completions = get_callable_arg_completions(doc, position)

        # Should only have arg2 since arg1 is already used
        assert len(completions) == 1
        assert completions[0].label == "arg1"

    def test_not_typing_key(self, mocker):
        """Test when not typing a key."""
        yaml_content = dedent("""\
            component:
              _target_: tests.target_objects.Class
              arg:
            """)
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=10)  # After the colon in arg1

        completions = get_callable_arg_completions(doc, position)
        assert completions == []

    def test_no_target_in_block(self, mocker):
        """Test with no _target_ in the block."""
        yaml_content = dedent("""\
            component:
              regular_key: value
              a
            """)
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=2)

        completions = get_callable_arg_completions(doc, position)
        assert completions == []

    def test_non_callable_target(self, mocker):
        """Test with a non-callable _target_."""
        yaml_content = dedent("""\
            component:
              _target_: tests.target_objects.CONSTANT
              a
            """)
        doc = Document("file:///test.yaml", yaml_content)
        position = lsp.Position(line=2, character=2)

        completions = get_callable_arg_completions(doc, position)
        assert completions == []
