"""Test for detect_hydra_targets function."""

from textwrap import dedent

from hydra_yaml_lsp.constants import HydraUtilityFunctions
from hydra_yaml_lsp.core.detections.hydra_target_2 import (
    TargetValuePosition,
    detect_hydra_targets,
    detect_target_arg_keys,
    detect_target_paths,
    detect_target_values,
    get_object_type,
)


class TestGetObjectType:
    """Tests for the get_object_type function."""

    def test_module_detection(self):
        """Test detection of Python modules."""
        assert get_object_type("tests") == "module"
        assert get_object_type("tests.target_objects") == "module"

    def test_class_detection(self):
        """Test detection of Python classes."""
        assert get_object_type("tests.target_objects.Class") == "class"

    def test_function_detection(self):
        """Test detection of Python functions."""
        assert get_object_type("tests.target_objects.function") == "function"
        assert get_object_type("builtins.len") == "function"

    def test_static_method_detection(self):
        """Test detection of static methods."""
        assert get_object_type("tests.target_objects.Class.static_method") == "function"

    def test_class_method_detection(self):
        """Test detection of class methods."""
        assert get_object_type("tests.target_objects.Class.class_method") == "method"

    def test_variable_detection(self):
        """Test detection of Python variables."""
        assert get_object_type("tests.target_objects.variable") == "variable"
        assert get_object_type("tests.target_objects.Class.class_var") == "variable"

    def test_constant_detection(self):
        """Test detection of Python constants."""
        assert get_object_type("tests.target_objects.CONSTANT") == "constant"
        assert get_object_type("tests.target_objects.Class.CLASS_CONST") == "constant"

    def test_non_existent_object(self):
        """Test with non-existent objects or import paths."""
        assert get_object_type("tests.target_objects.not_found") == "other"
        assert get_object_type("non_existent_module") == "other"


class TestTargetValuePositionHighlights:
    """Tests for TargetValuePosition.get_highlights method."""

    def test_simple_path(self):
        """Test get_highlights with a simple dotted path."""
        target = TargetValuePosition(
            lineno=0, start=10, end=30, content="tests.target_objects"
        )
        highlights = target.get_highlights()

        assert len(highlights) == 2

        # First component - "tests"
        assert highlights[0].content == "tests"
        assert highlights[0].start == 10
        assert highlights[0].end == 15  # 10 + len("tests")
        assert highlights[0].object_type == "module"

        # Second component - "target_objects"
        assert highlights[1].content == "target_objects"
        assert highlights[1].start == 16  # 15 + 1 (for dot)
        assert highlights[1].end == 30  # 16 + len("target_objects")
        assert highlights[1].object_type == "module"

    def test_complex_path(self):
        """Test with a complex path including class, method."""
        target = TargetValuePosition(
            lineno=0,
            start=0,
            end=len("tests.target_objects.Class.class_method"),
            content="tests.target_objects.Class.class_method",
        )
        highlights = target.get_highlights()

        assert len(highlights) == 4

        # Check each component
        assert highlights[0].content == "tests"
        assert highlights[0].object_type == "module"

        assert highlights[1].content == "target_objects"
        assert highlights[1].object_type == "module"

        assert highlights[2].content == "Class"
        assert highlights[2].object_type == "class"

        assert highlights[3].content == "class_method"
        assert highlights[3].object_type == "method"

    def test_path_with_variable(self):
        """Test with path ending in a variable."""
        target = TargetValuePosition(
            lineno=0,
            start=0,
            end=len("tests.target_objects.variable"),
            content="tests.target_objects.variable",
        )
        highlights = target.get_highlights()

        assert highlights[-1].object_type == "variable"
        assert highlights[-1].content == "variable"

    def test_path_with_constant(self):
        """Test with path ending in a constant."""
        target = TargetValuePosition(
            lineno=0,
            start=0,
            end=len("tests.target_objects.CONSTANT"),
            content="tests.target_objects.CONSTANT",
        )
        highlights = target.get_highlights()

        assert highlights[-1].object_type == "constant"
        assert highlights[-1].content == "CONSTANT"

    def test_position_calculation(self):
        """Test correct position calculation for highlights."""
        target = TargetValuePosition(
            lineno=5, start=100, end=120, content="tests.target_objects"
        )
        highlights = target.get_highlights()

        # First component starts at target.start
        assert highlights[0].start == 100
        assert highlights[0].end == 105  # 100 + len("tests")

        # Second component accounts for the dot
        assert highlights[1].start == 106  # 105 + 1 (for dot)
        assert highlights[1].end == 120  # Full end of target

        # Check line numbers are preserved
        assert all(h.lineno == 5 for h in highlights)

    def test_non_existent_path(self):
        """Test with path that doesn't resolve to real objects."""
        target = TargetValuePosition(
            lineno=0, start=0, end=len("fake.module.Class"), content="fake.module.Class"
        )
        highlights = target.get_highlights()

        # All components should be classified as "other"
        assert highlights[0].object_type == "other"
        assert highlights[0].content == "fake"

        assert highlights[1].object_type == "other"
        assert highlights[1].content == "module"

        assert highlights[2].object_type == "other"
        assert highlights[2].content == "Class"


class TestDetectHydraTargets:
    """End-to-end tests for detect_hydra_targets function."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_hydra_targets("")
        assert result == ()

    def test_single_target_without_arguments(self):
        """Test document with a single _target_ key without arguments."""
        content = dedent("""
            component:
              _target_: sample_python_project.YourClass
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 1

        target_info = result[0]
        assert target_info.key.content == "_target_"
        assert target_info.value is not None
        assert target_info.value.content == "sample_python_project.YourClass"
        assert target_info.value.lineno == 1
        assert len(target_info.args) == 0

    def test_single_target_with_arguments(self):
        """Test document with a _target_ key and associated arguments."""
        content = dedent("""
            component:
              _target_: sample_python_project.YourClass
              arg1: 10
              arg2: "test"
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 1

        target_info = result[0]
        assert target_info.key.content == "_target_"
        assert target_info.value is not None
        assert target_info.value.content == "sample_python_project.YourClass"
        assert len(target_info.args) == 2

        # Check arguments
        arg_info = target_info.args[0]
        assert arg_info.key.content == "arg1"
        assert arg_info.value is not None
        assert arg_info.value.content == "10"

        arg_info = target_info.args[1]
        assert arg_info.key.content == "arg2"
        assert arg_info.value is not None
        assert arg_info.value.content == "test"

    def test_multiple_targets(self):
        """Test document with multiple _target_ keys."""
        content = dedent("""
            component1:
              _target_: sample_python_project.YourClass
              arg1: 5

            component2:
              _target_: sample_python_project.hello
              message: "Hello"
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 2

        # First component
        assert result[0].key.content == "_target_"
        assert result[0].value is not None
        assert result[0].value.content == "sample_python_project.YourClass"
        assert len(result[0].args) == 1
        assert result[0].args[0].key.content == "arg1"

        # Second component
        assert result[1].key.content == "_target_"
        assert result[1].value is not None
        assert result[1].value.content == "sample_python_project.hello"
        assert len(result[1].args) == 1
        assert result[1].args[0].key.content == "message"

    def test_nested_targets(self):
        """Test document with nested _target_ keys."""
        content = dedent("""
            parent:
              _target_: sample_python_project.YourClass
              child:
                _target_: sample_python_project.hello
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 2

        # Parent target
        assert result[0].key.content == "_target_"
        assert result[0].value is not None
        assert result[0].value.content == "sample_python_project.hello"

        # Child target
        assert result[1].key.content == "_target_"
        assert result[1].value is not None
        assert result[1].value.content == "sample_python_project.YourClass"

    def test_target_with_special_keys(self):
        """Test that other special keys are ignored and not counted as
        arguments."""
        content = dedent("""
            component:
              _target_: sample_python_project.YourClass
              _args_: [1, 2, 3]
              _partial_: true
              arg1: value
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 1

        target_info = result[0]
        assert target_info.key.content == "_target_"
        assert target_info.value is not None
        assert target_info.value.content == "sample_python_project.YourClass"

        # Only non-special keys should be counted as arguments
        assert len(target_info.args) == 1
        assert target_info.args[0].key.content == "arg1"

    def test_position_information(self):
        """Test that position information is correctly captured."""
        content = dedent("""
            component:
              _target_: sample_python_project.YourClass
              arg1: 10
        """).strip()

        result = detect_hydra_targets(content)
        target_info = result[0]

        # Check key position
        key_pos = target_info.key
        assert key_pos.lineno == 1
        assert key_pos.start == 2  # Position of "_target_" in the line
        assert key_pos.end == 10  # End position

        # Check value position
        value_pos = target_info.value
        assert value_pos is not None
        assert value_pos.lineno == 1
        assert value_pos.start > key_pos.end  # Should be after the key

        # Check argument position
        arg_pos = target_info.args[0].key
        assert arg_pos.lineno == 2
        assert arg_pos.start == 2  # Position of "arg1" in the line

    def test_target_without_value(self):
        """Test malformed YAML where _target_ has no value."""
        content = dedent("""
            component:
              _target_:
              arg1: value
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 1

        target_info = result[0]
        assert target_info.key.content == "_target_"
        assert target_info.value is None  # No value provided
        assert len(target_info.args) == 1

    def test_argument_without_value(self):
        """Test argument key without a value."""
        content = dedent("""
            component:
              _target_: sample_python_project.YourClass
              arg1:
              arg2: value
        """).strip()

        result = detect_hydra_targets(content)
        target_info = result[0]

        assert len(target_info.args) == 2

        # First argument has no value
        assert target_info.args[0].key.content == "arg1"
        assert target_info.args[0].value is None

        # Second argument has value
        assert target_info.args[1].key.content == "arg2"
        assert target_info.args[1].value is not None
        assert target_info.args[1].value.content == "value"

    def test_deeply_nested_structure(self):
        """Test with deeply nested mapping structures."""
        content = dedent("""
            level1:
              level2:
                level3:
                  _target_: sample_python_project.YourClass
                  deep_arg: value
        """).strip()

        result = detect_hydra_targets(content)
        assert len(result) == 1

        target_info = result[0]
        assert target_info.key.content == "_target_"
        assert target_info.value is not None
        assert target_info.value.content == "sample_python_project.YourClass"
        assert len(target_info.args) == 1
        assert target_info.args[0].key.content == "deep_arg"


class TestDetectTargetValues:
    """Tests for detect_target_values function."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_values("")
        assert result == []

    def test_single_target(self):
        """Test with a single target."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
        """).strip()

        result = detect_target_values(content)
        assert len(result) == 1
        assert result[0].content == "tests.target_objects.Class"
        assert result[0].lineno == 1

    def test_multiple_targets(self):
        """Test with multiple targets."""
        content = dedent("""
            comp1:
              _target_: tests.target_objects.function
            comp2:
              _target_: tests.target_objects.CONSTANT
        """).strip()

        result = detect_target_values(content)
        assert len(result) == 2
        assert result[0].content == "tests.target_objects.function"
        assert result[1].content == "tests.target_objects.CONSTANT"

    def test_target_without_value(self):
        """Test with target key but no value."""
        content = dedent("""
            component:
              _target_:
        """).strip()

        result = detect_target_values(content)
        assert result == []


class TestDetectTargetArgKeys:
    """Tests for detect_target_arg_keys function."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_arg_keys("")
        assert result == []

    def test_no_arguments(self):
        """Test with target but no arguments."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
        """).strip()

        result = detect_target_arg_keys(content)
        assert result == []

    def test_single_argument(self):
        """Test with single argument."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
              arg1: value1
        """).strip()

        result = detect_target_arg_keys(content)
        assert len(result) == 1
        assert result[0].content == "arg1"
        assert result[0].lineno == 2

    def test_multiple_arguments(self):
        """Test with multiple arguments."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
              arg1: value1
              arg2: value2
              path: some.path
        """).strip()

        result = detect_target_arg_keys(content)
        assert len(result) == 3
        assert result[0].content == "arg1"
        assert result[1].content == "arg2"
        assert result[2].content == "path"

    def test_arguments_without_values(self):
        """Test with arguments that have no values."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
              arg1:
              arg2: value2
        """).strip()

        result = detect_target_arg_keys(content)
        assert len(result) == 2
        assert result[0].content == "arg1"
        assert result[1].content == "arg2"

    def test_multiple_components(self):
        """Test with multiple components having arguments."""
        content = dedent("""
            comp1:
              _target_: tests.target_objects.Class
              arg1: value1
            comp2:
              _target_: tests.target_objects.function
              param: test
              option: 123
        """).strip()

        result = detect_target_arg_keys(content)
        assert len(result) == 3
        assert result[0].content == "arg1"
        assert result[1].content == "param"
        assert result[2].content == "option"


class TestDetectTargetPaths:
    """Tests for detect_target_paths function."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_paths("")
        assert result == []

    def test_no_utility_functions(self):
        """Test with targets that are not utility functions."""
        content = dedent("""
            component:
              _target_: tests.target_objects.Class
              path: some.path
        """).strip()

        result = detect_target_paths(content)
        assert result == []

    def test_utility_function_with_path(self):
        """Test with utility function target and path argument."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_class
              path: tests.target_objects.Class
        """).strip()

        result = detect_target_paths(content)
        assert len(result) == 1
        assert result[0].utility_function == HydraUtilityFunctions.GET_CLASS
        assert result[0].path.content == "tests.target_objects.Class"

    def test_multiple_utility_functions(self):
        """Test with multiple utility functions with path arguments."""
        content = dedent("""
            comp1:
              _target_: hydra.utils.get_method
              path: tests.target_objects.function
            comp2:
              _target_: hydra.utils.get_class
              path: tests.target_objects.Class
        """).strip()

        result = detect_target_paths(content)
        assert len(result) == 2

        # First utility function
        assert result[0].utility_function == HydraUtilityFunctions.GET_METHOD
        assert result[0].path.content == "tests.target_objects.function"

        # Second utility function
        assert result[1].utility_function == HydraUtilityFunctions.GET_CLASS
        assert result[1].path.content == "tests.target_objects.Class"

    def test_utility_function_missing_path(self):
        """Test with utility function target but no path argument."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_method
              other_arg: value
        """).strip()

        result = detect_target_paths(content)
        assert result == []

    def test_utility_function_empty_path(self):
        """Test with utility function target and empty path argument."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_class
              path:
        """).strip()

        result = detect_target_paths(content)
        assert result == []

    def test_all_utility_function_types(self):
        """Test with all types of Hydra utility functions."""
        content = dedent("""
            get_object:
              _target_: hydra.utils.get_object
              path: tests.target_objects

            get_class:
              _target_: hydra.utils.get_class
              path: tests.target_objects.Class

            get_method:
              _target_: hydra.utils.get_method
              path: tests.target_objects.function

            get_static_method:
              _target_: hydra.utils.get_static_method
              path: tests.target_objects.Class.static_method
        """).strip()

        result = detect_target_paths(content)
        assert len(result) == 4

        # Check utility function types are correctly identified
        utility_functions = [info.utility_function for info in result]
        assert HydraUtilityFunctions.GET_OBJECT in utility_functions
        assert HydraUtilityFunctions.GET_CLASS in utility_functions
        assert HydraUtilityFunctions.GET_METHOD in utility_functions
        assert HydraUtilityFunctions.GET_STATIC_METHOD in utility_functions
