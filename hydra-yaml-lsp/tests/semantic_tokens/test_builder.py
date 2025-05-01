"""Tests for semantic token builder functionality."""

import pytest

from hydra_yaml_lsp.core.detections import (
    InterpolationHighlight,
    SpecialKeyPosition,
    TargetValueHighlight,
)
from hydra_yaml_lsp.core.detections.hydra_package import (
    HydraPackagePosition,
    PackageDirective,
    PackageName,
)
from hydra_yaml_lsp.semantic_tokens.builder import (
    SemanticToken,
    SemanticTokensBuilder,
    TokenModifier,
    TokenType,
    to_camel_case,
)


class TestToCamelCase:
    """Tests for to_camel_case utility function."""

    def test_empty_string(self):
        """Test with empty string."""
        assert to_camel_case("") == ""

    def test_single_word(self):
        """Test with a single word."""
        assert to_camel_case("WORD") == "word"

    def test_multiple_words(self):
        """Test with multiple words."""
        assert to_camel_case("SPECIAL_KEY") == "specialKey"
        assert to_camel_case("MULTIPLE_WORD_TEST") == "multipleWordTest"


class TestTokenTypeLegend:
    """Tests for TokenType legend generation."""

    def test_get_legend(self):
        """Test that legend contains correct camelCase values for all enum
        members."""
        legend = TokenType.get_legend()

        # Check all enum members are represented in the legend
        assert len(legend) == len(TokenType)

        # Check specific values
        assert "specialKey" in legend
        assert "targetValue" in legend
        assert "interpolationRef" in legend
        assert "packageName" in legend


class TestTokenModifierLegend:
    """Tests for TokenModifier legend generation."""

    def test_get_legend(self):
        """Test that legend contains correct camelCase values for all enum
        members."""
        legend = TokenModifier.get_legend()

        # Check specific values (excluding NONE)
        assert "declaration" in legend
        assert "reference" in legend
        assert "function" in legend
        assert "module" in legend
        assert "class" in legend
        assert "variable" in legend
        assert "constant" in legend


class TestSemanticToken:
    """Tests for SemanticToken class."""

    def test_comparison(self):
        """Test token comparison logic."""
        token1 = SemanticToken(
            line=0, start=0, length=5, token_type=0, token_modifiers=0
        )
        token2 = SemanticToken(
            line=0, start=10, length=5, token_type=0, token_modifiers=0
        )
        token3 = SemanticToken(
            line=1, start=0, length=5, token_type=0, token_modifiers=0
        )

        # Same line, different column
        assert token1 < token2
        assert not token2 < token1

        # Different line
        assert token1 < token3
        assert token2 < token3

    def test_from_special_key(self):
        """Test creating token from SpecialKeyPosition."""
        key_pos = SpecialKeyPosition(lineno=5, start=10, end=18, key="_target_")
        token = SemanticToken.from_special_key(key_pos)

        assert token.line == 5
        assert token.start == 10
        assert token.length == 8
        assert token.token_type == TokenType.SPECIAL_KEY
        assert token.token_modifiers == TokenModifier.DECLARATION

    def test_from_target_highlight(self):
        """Test creating token from TargetValueHighlight with different object
        types."""
        # Test module highlight
        module_highlight = TargetValueHighlight(
            lineno=1, start=10, end=15, content="module", object_type="module"
        )
        token = SemanticToken.from_target_highlight(module_highlight)
        assert token.token_type == TokenType.TARGET_VALUE
        assert token.token_modifiers == TokenModifier.MODULE

        # Test class highlight
        class_highlight = TargetValueHighlight(
            lineno=2, start=10, end=15, content="Class", object_type="class"
        )
        token = SemanticToken.from_target_highlight(class_highlight)
        assert token.token_modifiers == TokenModifier.CLASS

        # Test function highlight
        function_highlight = TargetValueHighlight(
            lineno=3, start=10, end=18, content="function", object_type="function"
        )
        token = SemanticToken.from_target_highlight(function_highlight)
        assert token.token_modifiers == TokenModifier.FUNCTION

        # Test variable highlight
        variable_highlight = TargetValueHighlight(
            lineno=4, start=10, end=18, content="variable", object_type="variable"
        )
        token = SemanticToken.from_target_highlight(variable_highlight)
        assert token.token_modifiers == TokenModifier.VARIABLE

        # Test constant highlight
        constant_highlight = TargetValueHighlight(
            lineno=5, start=10, end=18, content="CONSTANT", object_type="constant"
        )
        token = SemanticToken.from_target_highlight(constant_highlight)
        assert token.token_modifiers == TokenModifier.CONSTANT

        # Test other object type
        other_highlight = TargetValueHighlight(
            lineno=6, start=10, end=15, content="other", object_type="other"
        )
        token = SemanticToken.from_target_highlight(other_highlight)
        assert token.token_modifiers == TokenModifier.NONE

    def test_from_interpolation_highlight(self):
        """Test creating token from InterpolationHighlight with different token
        types."""
        # Test reference highlight
        ref_highlight = InterpolationHighlight(
            start_line=1,
            start_column=10,
            end_column=20,
            token_type="reference",
            content="path.to.value",
        )
        token = SemanticToken.from_interpolation_highlight(ref_highlight)
        assert token.token_type == TokenType.INTERPOLATION_REF
        assert token.token_modifiers == TokenModifier.REFERENCE

        # Test function highlight
        func_highlight = InterpolationHighlight(
            start_line=2,
            start_column=10,
            end_column=18,
            token_type="function",
            content="function",
        )
        token = SemanticToken.from_interpolation_highlight(func_highlight)
        assert token.token_type == TokenType.INTERPOLATION_FUNC
        assert token.token_modifiers == TokenModifier.FUNCTION

        # Test bracket highlight
        bracket_highlight = InterpolationHighlight(
            start_line=3,
            start_column=10,
            end_column=12,
            token_type="bracket_open",
            content="${",
        )
        token = SemanticToken.from_interpolation_highlight(bracket_highlight)
        assert token.token_type == TokenType.INTERPOLATION_BRACKET
        assert token.token_modifiers == TokenModifier.NONE

    def test_from_package_directive(self):
        """Test creating tokens from HydraPackagePosition."""
        package_position = HydraPackagePosition(
            name=PackageName(content="foo.bar", start=12, end=19),
            directive=PackageDirective(start=2, end=10),
            content="# @package foo.bar",
        )
        directive_token, name_token = SemanticToken.from_package_directive(
            package_position
        )

        # Check directive token
        assert directive_token.line == 0
        assert directive_token.start == 2
        assert directive_token.length == 8  # @package
        assert directive_token.token_type == TokenType.PACKAGE_DIRECTIVE
        assert directive_token.token_modifiers == TokenModifier.DECLARATION

        # Check name token
        assert name_token.line == 0
        assert name_token.start == 12
        assert name_token.length == 7  # foo.bar
        assert name_token.token_type == TokenType.PACKAGE_NAME
        assert name_token.token_modifiers == TokenModifier.MODULE


class TestSemanticTokensBuilder:
    """Tests for SemanticTokensBuilder class."""

    def test_empty_builder(self):
        """Test builder with no tokens."""
        builder = SemanticTokensBuilder()
        assert builder.build() == []

    def test_add_tokens(self):
        """Test adding tokens to builder."""
        builder = SemanticTokensBuilder()
        token1 = SemanticToken(
            line=0, start=0, length=5, token_type=0, token_modifiers=0
        )
        token2 = SemanticToken(
            line=0, start=10, length=3, token_type=1, token_modifiers=2
        )

        builder.add_tokens(token1, token2)
        assert len(builder.tokens) == 2
        assert builder.tokens[0] == token1
        assert builder.tokens[1] == token2

    def test_build_single_token(self):
        """Test building LSP data with single token."""
        builder = SemanticTokensBuilder()
        token = SemanticToken(
            line=0, start=5, length=8, token_type=2, token_modifiers=3
        )

        builder.add_tokens(token)
        data = builder.build()
        assert data == [0, 5, 8, 2, 3]

    def test_build_multiple_tokens_same_line(self):
        """Test building LSP data with multiple tokens on same line."""
        builder = SemanticTokensBuilder()
        token1 = SemanticToken(
            line=0, start=5, length=8, token_type=2, token_modifiers=3
        )
        token2 = SemanticToken(
            line=0, start=15, length=4, token_type=1, token_modifiers=2
        )

        builder.add_tokens(token1, token2)
        data = builder.build()
        # Format: [line_delta, start_delta, length, token_type, token_modifiers]
        assert data == [
            0,
            5,
            8,
            2,
            3,  # First token
            0,
            10,
            4,
            1,
            2,  # Second token (delta_start = 15 - 5 = 10)
        ]

    def test_build_multiple_tokens_different_lines(self):
        """Test building LSP data with multiple tokens on different lines."""
        builder = SemanticTokensBuilder()
        token1 = SemanticToken(
            line=0, start=5, length=8, token_type=2, token_modifiers=3
        )
        token2 = SemanticToken(
            line=2, start=3, length=4, token_type=1, token_modifiers=2
        )

        builder.add_tokens(token1, token2)
        data = builder.build()
        # Format: [line_delta, start_delta, length, token_type, token_modifiers]
        assert data == [
            0,
            5,
            8,
            2,
            3,  # First token
            2,
            3,
            4,
            1,
            2,  # Second token (line_delta = 2, start = absolute position)
        ]

    def test_build_unsorted_tokens(self):
        """Test building LSP data with tokens added in unsorted order."""
        builder = SemanticTokensBuilder()
        token1 = SemanticToken(
            line=2, start=5, length=8, token_type=2, token_modifiers=3
        )
        token2 = SemanticToken(
            line=1, start=3, length=4, token_type=1, token_modifiers=2
        )
        token3 = SemanticToken(
            line=1, start=10, length=2, token_type=0, token_modifiers=1
        )

        # Add tokens in unsorted order
        builder.add_tokens(token1, token2, token3)
        data = builder.build()

        # Expected order: token2, token3, token1
        # Format: [line_delta, start_delta, length, token_type, token_modifiers]
        assert data == [
            1,
            3,
            4,
            1,
            2,  # token2
            0,
            7,
            2,
            0,
            1,  # token3 (delta_start = 10 - 3 = 7)
            1,
            5,
            8,
            2,
            3,  # token1 (line_delta = 1, start = absolute position)
        ]
