"""Module for detecting and handling Hydra special keys in YAML files."""

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from ruamel import yaml

REFERENCE_PATTERN = re.compile(r"\$\{([^{}]+)\}")
FUNCTION_PATTERN = re.compile(r"\$\{([^:{}]+):")
SPECIAL_KEY_PATTERN = re.compile(r"_\w+_")


@dataclass(frozen=True)
class SpecialKeyPosition:
    """Position and information about a special key in a YAML document.

    Attributes:
        lineno: Line number (0-indexed) where the special key appears.
        start: Column position where the special key starts.
        end: Column position where the special key ends.
        key: The special key text, including underscores.
    """

    lineno: int
    start: int
    end: int
    key: str


@dataclass(frozen=True)
class InterpolationHighlight:
    """Interpolation highlighting in a document.

    Attributes:
        start_line: Line number (0-indexed) where the highlight starts
        start_column: Column position where the highlight starts
        end_column: Column position where the highlight ends
        token_type: Type of token being highlighted ("reference" or "function")
        content: Content for highlight.
    """

    start_line: int
    start_column: int
    end_column: int
    token_type: Literal["reference", "function"]
    content: str


@dataclass(frozen=True)
class InterpolationPosition:
    """Position and information about a Hydra interpolation in a YAML document.

    Attributes:
        start_line: Line number (0-indexed) where the interpolation starts.
        start_col: Column position where the interpolation starts.
        end_line: Line number where the interpolation ends.
        end_col: Column position where the interpolation ends.
        content: The full interpolation text, including ${...} syntax.
    """

    start_line: int
    start_column: int
    end_line: int
    end_column: int
    content: str

    def get_highlight(self) -> InterpolationHighlight | None:
        """Get the appropriate highlight position from this interpolation.

        This method tries to find a suitable highlighting position by first
        checking for a reference pattern, then for a function pattern. It provides
        a single entry point for extracting highlightable elements from interpolations.

        Returns:
            HighlightPosition representing either a reference or function part
            of the interpolation, or None if neither is found
        """
        pos = self.get_reference_highlight()
        if pos:
            return pos
        pos = self.get_function_highlight()
        if pos:
            return pos

    def get_reference_highlight(self) -> InterpolationHighlight | None:
        """Extract reference part from interpolation as a highlight position.

        Returns:
            HighlightPosition representing the reference part of the interpolation,
            or None if this is a function call or no reference is found
        """
        # Don't highlight references for function calls
        if ":" in self.content:
            return None

        # Extract reference between ${...}
        match = REFERENCE_PATTERN.search(self.content)
        if not match:
            return None

        reference = match.group(1).strip()
        if not reference:
            return None

        # Reference must be contained in a single line
        lines = self.content.splitlines()
        for i, line in enumerate(lines):
            if reference in line:
                # Calculate reference position
                ref_start = line.find(reference)
                line_offset = self.start_column if i == 0 else 0

                return InterpolationHighlight(
                    start_line=self.start_line + i,
                    start_column=line_offset + ref_start,
                    end_column=line_offset + ref_start + len(reference),
                    token_type="reference",
                    content=reference,
                )

        return None

    def get_function_highlight(self) -> InterpolationHighlight | None:
        """Extract function part from interpolation as a highlight position.

        Returns:
            HighlightPosition representing the function part of the interpolation,
            or None if this is not a function call or no function is found
        """
        # Check if this is a function call
        match = FUNCTION_PATTERN.search(self.content)
        if not match:
            return None

        function = match.group(1).strip()
        if not function:
            return None

        # Find in which line the function appears
        lines = self.content.splitlines()
        for line_idx, line in enumerate(lines):
            func_start = line.find(function)
            if func_start != -1:
                # Calculate absolute position
                line_offset = self.start_line + line_idx
                col_offset = self.start_column if line_idx == 0 else 0

                return InterpolationHighlight(
                    start_line=line_offset,
                    start_column=col_offset + func_start,
                    end_column=col_offset + func_start + len(function),
                    token_type="function",
                    content=function,
                )

        return None


@lru_cache
def detect_special_keys_in_document(content: str) -> tuple[SpecialKeyPosition, ...]:
    """Detect all Hydra special keys in a YAML document.

    Searches through each line of the document and identifies all keys
    surrounded by underscores (e.g., _target_, _args_) followed by colons.

    Args:
        content: A string representing the entire YAML document.

    Returns:
        A list of SpecialKeyPosition objects, each containing information
        about a special key found in the document.

    Examples:
        >>> content = "_target_: module.path\\nregular: value\\n  _args_: value"
        >>> result = detect_special_keys_in_document(content)
        >>> [(pos.lineno, pos.start, pos.end, pos.key) for pos in result]
        [(0, 0, 8, '_target_'), (2, 2, 8, '_args_')]
    """
    results: list[SpecialKeyPosition] = []

    prev_token_type = None
    token: yaml.Token
    for token in yaml.YAML().scan(content):
        if prev_token_type is yaml.KeyToken and isinstance(token, yaml.ScalarToken):
            val = str(token.value)
            if SPECIAL_KEY_PATTERN.match(val):
                results.append(
                    SpecialKeyPosition(
                        token.start_mark.line,
                        token.start_mark.column,
                        token.end_mark.column,
                        val,
                    )
                )

        prev_token_type = type(token)
    return tuple(results)


@lru_cache
def detect_interpolation_pos_in_document(
    content: str,
) -> tuple[InterpolationPosition, ...]:
    """Detect all Hydra interpolations (${...}) in a YAML document.

    Searches for interpolation patterns in scalar values within the YAML document.
    Handles both single-line and multi-line interpolations.

    Args:
        content: A string representing the entire YAML document.

    Returns:
        A tuple of InterpolationPosition objects, each containing information
        about an interpolation found in the document.
    """
    results: list[InterpolationPosition] = []

    prev_token_type = None
    content_lines = content.splitlines()

    for token in yaml.YAML().scan(content):
        if prev_token_type is yaml.ValueToken and isinstance(token, yaml.ScalarToken):
            results.extend(_extract_interpolation_pos_in_value(token, content_lines))
        prev_token_type = type(token)
    return tuple(results)


def _extract_interpolation_pos_in_value(
    value: yaml.ScalarToken, content_lines: list[str]
) -> list[InterpolationPosition]:
    """Extract interpolation positions from a scalar value in YAML.

    Args:
        value: The scalar token to analyze.
        content_lines: All lines of the document for context.

    Returns:
        A list of InterpolationPosition objects representing found interpolations.
    """
    results: list[InterpolationPosition] = []

    start_line, end_line = value.start_mark.line, value.end_mark.line
    start_col, end_col = value.start_mark.column, value.end_mark.column

    value_lines = content_lines[start_line : end_line + 1]
    if start_line == end_line:
        value_lines[0] = value_lines[0][start_col:end_col]
    else:
        value_lines[0] = value_lines[0][start_col:]
        value_lines[-1] = value_lines[-1][: end_col + 1]
    stack = []
    bracket_balance = 0

    for line_idx, line in enumerate(value_lines, start=start_line):
        col_offset = start_col if line_idx == start_line else 0

        for char_idx, char in enumerate(line):
            col_idx = char_idx + col_offset

            # Check for interpolation start "${" pattern
            if char == "$" and char_idx + 1 < len(line) and line[char_idx + 1] == "{":
                stack.append((line_idx, col_idx))
                bracket_balance += 1

            # Check for closing "}" bracket
            elif char == "}" and bracket_balance > 0:
                bracket_balance -= 1
                interp_start_line, interp_start_col = stack.pop()

                # Extract the interpolation content
                if interp_start_line == line_idx:
                    # Single-line interpolation
                    interp_content = content_lines[line_idx][
                        interp_start_col : col_idx + 1
                    ]
                else:
                    # Multi-line interpolation
                    interp_lines = [content_lines[interp_start_line][interp_start_col:]]
                    for i in range(interp_start_line + 1, line_idx):
                        interp_lines.append(content_lines[i])
                    interp_lines.append(content_lines[line_idx][: col_idx + 1])
                    interp_content = "\n".join(interp_lines)

                results.append(
                    InterpolationPosition(
                        start_line=interp_start_line,
                        start_column=interp_start_col,
                        end_line=line_idx,
                        end_column=col_idx + 1,
                        content=interp_content,
                    )
                )
    results.reverse()  # Order is outer to inner
    return results
