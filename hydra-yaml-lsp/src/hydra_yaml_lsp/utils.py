"""Utility functions for working with YAML documents."""

from collections import deque


def get_yaml_block_lines(yaml_lines: list[str], lineno: int) -> list[str]:
    """Extract a complete YAML block at the same indentation level as the
    specified line.

    This function identifies and retrieves all lines that belong to the same YAML block
    as the specified line number. It handles sequence blocks (starting with '- ') and
    maintains the original indentation. Empty lines and comment lines are excluded.

    When searching backward, all lines at the same indent level are included.
    When searching forward, sequence items at the same indent level are excluded.

    Args:
        yaml_lines: A list of strings representing the YAML file content, with each string
            being a line of the file.
        lineno: The line number (0-indexed) to identify the block from.

    Returns:
        A list of strings representing the complete YAML block.
    """
    if len(yaml_lines) <= lineno or yaml_lines == []:
        return []

    current_line = yaml_lines[lineno]

    # Special handling for sequence block headers (lines starting with "- ")
    if current_line.lstrip().startswith("- "):
        current_indent = len(current_line) - len(current_line.lstrip()[2:].lstrip())
    else:
        current_indent = len(current_line) - len(current_line.lstrip())

    block_lines = deque([current_line])

    # Check previous lines
    line_num = lineno - 1
    while line_num >= 0 and not current_line.strip().startswith("- "):
        line = yaml_lines[line_num]
        # Skip empty lines or comment lines
        if not line.strip() or line.strip().startswith("#"):
            line_num -= 1
            continue

        # Check indentation
        # Special handling for sequence block headers
        if line.lstrip().startswith("- "):
            indent = len(line) - len(line.lstrip()[2:].lstrip())
        else:
            indent = len(line) - len(line.lstrip())

        # Exit if we've left the current block
        if indent < current_indent:
            break

        # Extract lines at the same indent level
        if indent == current_indent:
            block_lines.appendleft(line)
        if line.lstrip().startswith("- "):
            break

        line_num -= 1

    # Check following lines
    line_num = lineno + 1
    while line_num < len(yaml_lines):
        line = yaml_lines[line_num]
        # Skip empty lines or comment lines
        if not line.strip() or line.strip().startswith("#"):
            line_num += 1
            continue

        # Check indentation
        indent = len(line) - len(line.lstrip())

        # Exit if we've left the current block
        if indent < current_indent:
            break

        # Extract lines at the same indent level that aren't part of a sequence
        if indent == current_indent and not line.lstrip().startswith("- "):
            block_lines.append(line)

        line_num += 1

    return list(block_lines)
