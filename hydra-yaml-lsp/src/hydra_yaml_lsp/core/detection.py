"""Module for detecting and handling Hydra special keys in YAML files."""

import re
from dataclasses import dataclass
from functools import lru_cache

from ruamel import yaml


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


SPECIAL_KEY_PATTERN = re.compile(r"_\w+_")


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
