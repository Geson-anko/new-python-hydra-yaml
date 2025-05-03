from lsprotocol import types as lsp
from pygls.workspace import Document


def is_typing_comment(document: Document, position: lsp.Position) -> bool:
    """Check if the user is currently typing a comment in YAML.

    Determines if the cursor position is in a YAML comment line.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        True if the user is typing in a comment line, False otherwise
    """
    if len(document.lines) <= position.line:  # End of file.
        return False

    line = document.lines[position.line]
    line_prefix = line[: position.character]
    return line_prefix.strip().startswith("#")


def is_typing_key(document: Document, position: lsp.Position) -> bool:
    """Check if the user is currently typing a key in YAML.

    Determines if the cursor position is in the key part of a YAML key-value pair,
    by analyzing the text to the left of the cursor.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        True if the user appears to be typing a key, False otherwise
    """
    if is_typing_comment(document, position):
        return False

    if len(document.lines) <= position.line:  # End of file.
        return True

    line = document.lines[position.line]
    line_prefix = line[: position.character]

    # Key typing detection logic:
    # - Either no colon in the line (just indentation and key name)
    # - Or cursor is to the left of any colon
    return line_prefix.find(":") == -1


def is_typing_value(document: Document, position: lsp.Position) -> bool:
    """Check if the user is currently typing a value in YAML.

    Determines if the cursor position is in the value part of a YAML key-value pair.
    This is true if the cursor is not in a comment and not typing a key.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        True if the user appears to be typing a value, False otherwise
    """
    if is_typing_comment(document, position):
        return False
    return not is_typing_key(document, position)
