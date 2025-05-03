from lsprotocol import types as lsp
from pygls.workspace import Document


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
    if len(document.lines) <= position.line:  # End of file.
        return True

    line = document.lines[position.line]
    line_prefix = line[: position.character]

    # Key typing detection logic:
    # - Either no colon in the line (just indentation and key name)
    # - Or cursor is to the left of any colon
    colon_pos = line_prefix.find(":")
    if colon_pos == -1:
        # No colon yet - potentially typing a key
        return not line_prefix.strip().startswith("#")  # Exclude comment lines
    else:
        # If colon exists and cursor is after it, user is typing a value
        return False
