from textwrap import dedent

from hydra_yaml_lsp.core.detections.hydra_target import (
    TargetValuePosition,
    detect_target_path,
    detect_target_values,
)


class TestTargetValueDetection:
    """Test cases for target value detection in Hydra YAML files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_values("")
        assert result == ()

    def test_document_with_no_target_values(self):
        """Test with a document containing no target values."""
        content = dedent("""
            regular: value
            another: item
            third: element
        """).strip()
        result = detect_target_values(content)
        assert result == ()

    def test_document_with_single_target_value(self):
        """Test with a document containing a single target value."""
        content = "_target_: module.path\nregular: value"
        result = detect_target_values(content)

        assert len(result) == 1
        assert result[0].lineno == 0
        assert result[0].start == len("_target_: ")
        assert result[0].end == len("_target_: module.path")
        assert result[0].content == "module.path"

    def test_document_with_multiple_target_values(self):
        """Test with a document containing multiple target values."""
        content = dedent("""
            component1:
              _target_: path.to.component1
            component2:
              _target_: path.to.component2
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 2
        # First target value
        assert result[0].content == "path.to.component1"
        # Second target value
        assert result[1].content == "path.to.component2"

    def test_document_with_nested_target_values(self):
        """Test with a document containing nested structures with target
        values."""
        content = dedent("""
            outer:
              _target_: outer.module
              nested:
                _target_: nested.module
                deeper:
                  _target_: deepest.module
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 3
        assert result[0].content == "outer.module"
        assert result[1].content == "nested.module"
        assert result[2].content == "deepest.module"

    def test_document_with_target_and_other_special_keys(self):
        """Test with a document containing both target and other special
        keys."""
        content = dedent("""
            component:
              _target_: path.to.class
              _args_: [1, 2, 3]
              _partial_: true
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 1
        assert result[0].content == "path.to.class"

    def test_multiline_target_value(self):
        """Test with a target value spanning multiple lines."""
        content = dedent("""
            component:
              _target_: >-
                very.long.path.to.module.with.
                line.breaks.ClassName
        """).strip()
        result = detect_target_values(content)

        assert len(result) == 1
        assert "very.long.path" in result[0].content
        assert "line.breaks.ClassName" in result[0].content

    def test_caching(self):
        """Test that results are cached properly."""
        content = "_target_: module.path"

        # First call should compute the result
        result1 = detect_target_values(content)

        # Second call should use the cached result
        result2 = detect_target_values(content)

        # Results should be identical
        assert result1 == result2

        # And should be the expected values
        expected = (
            TargetValuePosition(
                lineno=0,
                start=len("_target_: "),
                end=len("_target_: module.path"),
                content="module.path",
            ),
        )
        assert result1 == expected

        # Check cache info
        info = detect_target_values.cache_info()
        assert info.hits >= 1


class TestTargetValueHighlights:
    """Tests for target value highlights functionality."""

    def test_module_detection(self):
        """Test detection of Python modules."""
        yaml_content = """
        module:
          _target_: tests.target_objects
        """
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # Verify correct number of components
        assert len(highlights) == 2

        # Verify all components are detected as modules
        assert all(h.object_type == "module" for h in highlights)

        # Verify content of components
        assert [h.content for h in highlights] == ["tests", "target_objects"]

    def test_variable_detection(self):
        """Test detection of Python variables."""
        yaml_content = """
        var:
          _target_: tests.target_objects.variable
        """
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # Verify the last component is a variable
        assert highlights[-1].object_type == "variable"
        assert highlights[-1].content == "variable"

    def test_constant_detection(self):
        """Test detection of Python constants."""
        yaml_content = """
        const:
          _target_: tests.target_objects.CONSTANT
        """
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # Verify the last component is a constant
        assert highlights[-1].object_type == "constant"
        assert highlights[-1].content == "CONSTANT"

    def test_function_detection(self):
        """Test detection of Python functions."""
        yaml_content = """
        func:
          _target_: tests.target_objects.function
        """
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # Verify the last component is a function
        assert highlights[-1].object_type == "function"
        assert highlights[-1].content == "function"

    def test_class_detection(self):
        """Test detection of Python classes."""
        yaml_content = """
        class:
          _target_: tests.target_objects.Class
        """
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # Verify the last component is a class
        assert highlights[-1].object_type == "class"
        assert highlights[-1].content == "Class"

    def test_class_attribute_detection(self):
        """Test detection of class attributes."""
        yaml_content = """
        class_var:
          _target_: tests.target_objects.Class.class_var
        class_const:
          _target_: tests.target_objects.Class.CLASS_CONST
        """
        targets = detect_target_values(yaml_content)

        # Test class variable
        var_highlights = targets[0].get_highlights()
        assert var_highlights[-1].object_type == "variable"
        assert var_highlights[-1].content == "class_var"

        # Test class constant
        const_highlights = targets[1].get_highlights()
        assert const_highlights[-1].object_type == "constant"
        assert const_highlights[-1].content == "CLASS_CONST"

    def test_class_method_detection(self):
        """Test detection of class methods."""
        yaml_content = """
        static_method:
          _target_: tests.target_objects.Class.static_method
        class_method:
          _target_: tests.target_objects.Class.class_method
        """
        targets = detect_target_values(yaml_content)

        # Test static method
        static_highlights = targets[0].get_highlights()
        assert static_highlights[-1].object_type == "function"
        assert static_highlights[-1].content == "static_method"

        # Test class method
        class_method_highlights = targets[1].get_highlights()
        assert class_method_highlights[-1].object_type == "method"
        assert class_method_highlights[-1].content == "class_method"

    def test_other_detection(self):
        yaml_content = "_target_: tests.target_object.not_found"
        targets = detect_target_values(yaml_content)

        highlight = targets[0].get_highlights()[-1]
        assert highlight.content == "not_found"
        assert highlight.object_type == "other"

    def test_position_calculation(self):
        """Test correct position calculation of highlights."""
        yaml_content = "_target_: tests.core"
        target = detect_target_values(yaml_content)[0]
        highlights = target.get_highlights()

        # First component starts at target.start
        assert highlights[0].start == len("_target_: ")
        assert highlights[0].end == len("_target_: tests")

        # Second component accounts for the dot
        assert highlights[1].start == len("_target_: tests.")
        assert highlights[1].end == highlights[1].start + len("core")


class TestTargetPathDetection:
    """Test cases for target path detection in Hydra YAML files."""

    def test_empty_document(self):
        """Test with an empty document."""
        result = detect_target_path("")
        assert result == ()

    def test_document_with_no_targets_or_paths(self):
        """Test with a document containing no targets or paths."""
        content = dedent("""
            regular: value
            another: item
            third: element
        """).strip()
        result = detect_target_path(content)
        assert result == ()

    def test_document_with_target_but_no_path(self):
        """Test with a document containing a target but no path."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_method
              arg1: value1
        """).strip()
        result = detect_target_path(content)
        assert result == ()

    def test_document_with_path_but_no_target(self):
        """Test with a document containing a path but no target."""
        content = dedent("""
            component:
              path: module.path.function
              arg1: value1
        """).strip()
        result = detect_target_path(content)
        assert result == ()

    def test_document_with_non_utility_target_and_path(self):
        """Test with a document containing a non-utility target and path."""
        content = dedent("""
            component:
              _target_: regular.module.Class
              path: module.path.function
        """).strip()
        result = detect_target_path(content)
        assert result == ()

    def test_document_with_utility_target_and_path(self):
        """Test with a document containing a utility target and path."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_method
              path: tests.target_objects.function
        """).strip()
        result = detect_target_path(content)

        assert len(result) == 1
        assert result[0].content == "tests.target_objects.function"

    def test_document_with_multiple_utility_blocks(self):
        """Test with a document containing multiple utility blocks."""
        content = dedent("""
            component1:
              _target_: hydra.utils.get_method
              path: module1.path.function

            component2:
              _target_: regular.module.Class
              path: module2.path.function

            component3:
              _target_: hydra.utils.get_class
              path: module3.path.Class
        """).strip()
        result = detect_target_path(content)

        assert len(result) == 2
        assert result[0].content == "module1.path.function"
        assert result[1].content == "module3.path.Class"

    def test_document_with_nested_blcoks(self):
        content = dedent("""
            component1:
              _target_: hydra.utils.get_method
              path: module1.path.function

              component2:
                _target_: regular.module.Class
                path: module2.path.function

              component3:
                _target_: hydra.utils.get_class
                path: module3.path.Class
        """).strip()

        result = detect_target_path(content)
        assert len(result) == 2

        assert result[0].content in ["module3.path.Class", "module1.path.function"]
        assert result[1].content in ["module3.path.Class", "module1.path.function"]

    def test_caching(self):
        """Test that results are cached properly."""
        content = dedent("""
            component:
              _target_: hydra.utils.get_method
              path: module.path.function
        """).strip()

        # First call should compute the result
        result1 = detect_target_path(content)

        # Second call should use the cached result
        result2 = detect_target_path(content)

        # Results should be identical
        assert result1 == result2
        assert len(result1) == 1
        assert result1[0].content == "module.path.function"

        # Check cache info
        info = detect_target_path.cache_info()
        assert info.hits >= 1
