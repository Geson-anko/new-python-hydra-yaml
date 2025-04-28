"""Module for detecting and handling Hydra special keys in YAML files."""

import re
from typing import NamedTuple

# Cached pattern


class SpecialKeyPosition(NamedTuple):
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


SPECIAL_KEY_PATTERN = re.compile(r"(_[a-zA-Z0-9_]+_)\s*:")


def detect_special_key(line: str) -> tuple[int, int, str] | None:
    """Detect Hydra special keys in a YAML line.

    Finds the first key surrounded by underscores (e.g., _target_, _args_) in a YAML line
    that is followed by a colon, indicating it's a YAML key. Ignores keys inside comments.

    Args:
        line: A string representing a line in a YAML file.

    Returns:
        A tuple containing (start_position, end_position, key) if a special key is found,
        or None if no special key is found.

    Examples:
        >>> detect_special_key("_target_: path.to.class")
        (0, 8, '_target_')
        >>> detect_special_key("some:")
        None
        >>> detect_special_key("  _args_:")
        (2, 8, '_args_')
        >>> detect_special_key("- _arg_: value")
        (2, 7, '_arg_')
    """
    # First, check if there's a comment in the line
    comment_pos = line.find("#")

    # If there's a comment, only search in the part before the comment
    search_line = line if comment_pos == -1 else line[:comment_pos]

    # Pattern for keys surrounded by underscores followed by a colon

    # Search for the pattern in the line
    match = SPECIAL_KEY_PATTERN.search(search_line)

    if match:
        # Return the start position, end position, and the matched key
        return match.start(1), match.end(1), match.group(1)

    # Return None if no match is found
    return None


def detect_special_keys_in_document(content: str) -> list[SpecialKeyPosition]:
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

    # Split the content into lines
    lines = content.splitlines()

    for lineno, line in enumerate(lines):
        # Detect special key in the current line
        key_result = detect_special_key(line)

        if key_result:
            # Unpack the result
            start_in_line, end_in_line, key = key_result

            # Create a SpecialKeyPosition instance
            position = SpecialKeyPosition(
                lineno=lineno, start=start_in_line, end=end_in_line, key=key
            )

            # Add to results
            results.append(position)

    return results
