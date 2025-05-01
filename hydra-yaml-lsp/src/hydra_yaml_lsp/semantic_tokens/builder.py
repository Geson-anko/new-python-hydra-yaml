"""Hydra YAML semantic token definitions and utilities."""

from dataclasses import dataclass, field
from enum import IntEnum, IntFlag
from typing import Self

from hydra_yaml_lsp.core.detections import (
    HydraPackagePosition,
    InterpolationHighlight,
    SpecialKeyPosition,
    TargetValueHighlight,
    TargetValuePosition,
)


class TokenType(IntEnum):
    """Definition of semantic token types."""

    SPECIAL_KEY = 0
    TARGET_VALUE = 1
    INTERPOLATION_REF = 2
    INTERPOLATION_FUNC = 3
    INTERPOLATION_BRACKET = 4
    PACKAGE_DIRECTIVE = 5
    PACKAGE_NAME = 6

    @classmethod
    def get_legend(cls) -> list[str]:
        """Return the legend for token types."""
        return [
            "specialKey",  # Hydra special keys (_target_, _args_, etc.)
            "targetValue",  # Values of _target_ fields
            "interpolationRef",  # Interpolation references (reference parts in ${path.to.value})
            "interpolationFunc",  # Interpolation functions (function name in ${func:args})
            "interpolationBracket",  # Interpolation brackets
            "packageDirective",  # @package directive
            "packageName",  # Package name
        ]


class TokenModifier(IntFlag):
    """Definition of semantic token modifiers."""

    NONE = 0
    DECLARATION = 1 << 0
    REFERENCE = 1 << 1
    FUNCTION = 1 << 2
    MODULE = 1 << 3
    CLASS = 1 << 4
    VARIABLE = 1 << 5
    CONSTANT = 1 << 6

    @classmethod
    def get_legend(cls) -> list[str]:
        """Return the legend for token modifiers."""
        return [
            "declaration",  # Declaration
            "reference",  # Reference
            "function",  # Function
            "module",  # Module
            "class",  # Class
            "variable",  # Variable
            "constant",  # Constant
        ]


@dataclass(frozen=True)
class SemanticToken:
    """Basic information for a semantic token.

    Attributes:
        line: Line number of the token (0-indexed)
        start: Starting column of the token
        length: Length of the token
        token_type: Index of the token type
        token_modifiers: Bit flags for token modifiers
    """

    line: int
    start: int
    length: int
    token_type: int
    token_modifiers: int

    def __lt__(self, other: Self) -> bool:
        """Compare tokens by line and column."""
        if not isinstance(other, SemanticToken):
            return NotImplemented
        return (self.line, self.start) < (other.line, other.start)

    @classmethod
    def from_special_key(cls, key: SpecialKeyPosition) -> Self:
        """Create a semantic token from a special key."""
        return cls(
            line=key.lineno,
            start=key.start,
            length=key.end - key.start,
            token_type=TokenType.SPECIAL_KEY,
            token_modifiers=TokenModifier.DECLARATION,
        )

    @classmethod
    def from_target_value(cls, target: TargetValuePosition) -> Self:
        """Create a semantic token from a target value."""
        return cls(
            line=target.lineno,
            start=target.start,
            length=target.end - target.start,
            token_type=TokenType.TARGET_VALUE,
            token_modifiers=TokenModifier.REFERENCE,
        )

    @classmethod
    def from_target_highlight(cls, highlight: TargetValueHighlight) -> Self:
        """Create a semantic token from a target highlight."""
        # Determine modifiers based on object type
        modifiers = TokenModifier.NONE
        match highlight.object_type:
            case "module":
                modifiers = TokenModifier.MODULE
            case "class":
                modifiers = TokenModifier.CLASS
            case "function":
                modifiers = TokenModifier.FUNCTION
            case "variable":
                modifiers = TokenModifier.VARIABLE
            case "constant":
                modifiers = TokenModifier.CONSTANT

        return cls(
            line=highlight.lineno,
            start=highlight.start,
            length=highlight.end - highlight.start,
            token_type=TokenType.TARGET_VALUE,
            token_modifiers=modifiers,
        )

    @classmethod
    def from_interpolation_highlight(cls, highlight: InterpolationHighlight) -> Self:
        """Create a semantic token from an interpolation highlight."""
        token_type = TokenType.INTERPOLATION_BRACKET
        modifiers = TokenModifier.NONE

        match highlight.token_type:
            case "reference":
                token_type = TokenType.INTERPOLATION_REF
                modifiers = TokenModifier.REFERENCE
            case "function":
                token_type = TokenType.INTERPOLATION_FUNC
                modifiers = TokenModifier.FUNCTION

        return cls(
            line=highlight.start_line,
            start=highlight.start_column,
            length=highlight.end_column - highlight.start_column,
            token_type=token_type,
            token_modifiers=modifiers,
        )

    @classmethod
    def from_package_directive(cls, package: HydraPackagePosition) -> tuple[Self, Self]:
        """Create semantic tokens from a package declaration."""
        directive_token = cls(
            line=0,  # Always in the first line
            start=package.directive.start,
            length=len(package.directive.content),
            token_type=TokenType.PACKAGE_DIRECTIVE,
            token_modifiers=TokenModifier.DECLARATION,
        )

        name_token = cls(
            line=0,  # Always in the first line
            start=package.name.start,
            length=len(package.name.content),
            token_type=TokenType.PACKAGE_NAME,
            token_modifiers=TokenModifier.MODULE,
        )

        return (directive_token, name_token)


@dataclass
class SemanticTokensBuilder:
    """Builder for a collection of semantic tokens.

    This class manages a collection of semantic tokens and
    converts them to the data format required by the Language Server Protocol
    (a continuous array of integers).

    Attributes:
        tokens: List of semantic tokens
    """

    tokens: list[SemanticToken] = field(default_factory=list)

    def add_tokens(self, *tokens: SemanticToken) -> None:
        """Add multiple tokens to the collection."""
        self.tokens.extend(tokens)

    def build(self) -> list[int]:
        """Convert tokens to LSP data format.

        Returns:
            Data array in LSP format (each token is represented as 5 consecutive numbers)
        """
        if not self.tokens:
            return []

        # Sort tokens by line and column
        sorted_tokens = sorted(self.tokens)

        # Convert to the data format required by LSP
        data: list[int] = []
        prev_line = 0
        prev_start = 0

        for token in sorted_tokens:
            # Calculate line offset (difference from previous token)
            delta_line = token.line - prev_line

            # Calculate column offset if on same line, or absolute position if on a new line
            delta_start = token.start - prev_start if delta_line == 0 else token.start

            # Add 5 values to the data array
            data.extend(
                [
                    delta_line,
                    delta_start,
                    token.length,
                    token.token_type,
                    token.token_modifiers,
                ]
            )

            # Update current position
            prev_line = token.line
            prev_start = token.start

        return data
