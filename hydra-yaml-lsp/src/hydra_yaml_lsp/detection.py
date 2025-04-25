"""Module for detecting and handling Hydra special keys in YAML files."""

import re

# Cached pattern
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
