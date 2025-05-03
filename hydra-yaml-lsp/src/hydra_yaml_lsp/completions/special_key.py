from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.constants import HydraSpecialKey
from hydra_yaml_lsp.utils import get_yaml_block_lines


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


def _get_existing_keys_in_current_block(
    content_lines: list[str], lineno: int
) -> set[str]:
    """Get all existing keys in the current YAML block.

    Extracts all key names from the current YAML indentation block to avoid
    suggesting duplicate keys in completions.

    Args:
        content_lines: All lines of the document content
        lineno: The line number to identify the current block

    Returns:
        A set of existing key names in the current block
    """
    block_lines = get_yaml_block_lines(content_lines, lineno)
    existing_keys = set()

    for line in block_lines:
        line = line.lstrip()
        if line.startswith("- "):
            # Handle sequence items by removing the dash prefix
            line = line[2:].lstrip()

        if ":" in line:
            key = line.strip().split(":", 1)[0].strip()
            if key:
                existing_keys.add(key)

    return existing_keys


def get_hydra_special_key_completions(
    document: Document, position: lsp.Position
) -> list[lsp.CompletionItem]:
    """Create completion items for Hydra special keys.

    Generates completion suggestions for Hydra special keys (_target_, _args_, etc.)
    considering the context of the current YAML block.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        A list of completion items for applicable Hydra special keys
    """
    items = []
    existing_keys = _get_existing_keys_in_current_block(document.lines, position.line)

    # Some special keys (like _args_, _partial_) are only applicable
    # when _target_ is present in the same block
    has_target = HydraSpecialKey.TARGET in existing_keys
    for key in HydraSpecialKey:
        if key in existing_keys:
            continue

        if key in {HydraSpecialKey.ARGS, HydraSpecialKey.PARTIAL} and not has_target:
            continue

        item = lsp.CompletionItem(
            label=key,
            kind=lsp.CompletionItemKind.Keyword,
            detail=key.info["detail"],
            documentation=lsp.MarkupContent(
                kind=lsp.MarkupKind.Markdown,
                value=f"**{key}**\n\n{key.info['documentation']}",
            ),
            insert_text=f"{key}: ",
            insert_text_format=lsp.InsertTextFormat.PlainText,
        )
        items.append(item)
    return items
