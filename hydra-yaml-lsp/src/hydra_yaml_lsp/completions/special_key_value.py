"""Hydra YAML special key value completion functionality."""

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.utils import is_typing_value
from hydra_yaml_lsp.constants import HydraConvertValue, HydraSpecialKey


def extract_special_key_from_line(line: str, character_position: int) -> str | None:
    """Extract Hydra special key from a line if present.

    Args:
        line: The document line to analyze
        character_position: Current cursor position in the line

    Returns:
        Identified special key or None if not found
    """
    line_prefix = line[:character_position]

    if ":" not in line_prefix:
        return None

    key_name = line_prefix.split(":", 1)[0].strip()

    if key_name in HydraSpecialKey:
        return key_name

    return None


def get_partial_completions() -> list[lsp.CompletionItem]:
    """Get completion items for _partial_ values.

    Returns:
        Completion items with true prioritized
    """
    return [
        lsp.CompletionItem(
            label="true",
            kind=lsp.CompletionItemKind.Value,
            sort_text="0",  # Lower sort text gives higher priority
        ),
        lsp.CompletionItem(
            label="false",
            kind=lsp.CompletionItemKind.Value,
            sort_text="1",
        ),
    ]


def get_recursive_completions() -> list[lsp.CompletionItem]:
    """Get completion items for _recursive_ values.

    Returns:
        Completion items with false prioritized
    """
    return [
        lsp.CompletionItem(
            label="false",
            kind=lsp.CompletionItemKind.Value,
            sort_text="0",  # Lower sort text gives higher priority
        ),
        lsp.CompletionItem(
            label="true",
            kind=lsp.CompletionItemKind.Value,
            sort_text="1",
        ),
    ]


def get_convert_completions() -> list[lsp.CompletionItem]:
    """Get completion items for _convert_ values.

    Returns:
        Completion items for convert options
    """
    items = []
    for idx, value in enumerate(HydraConvertValue):
        items.append(
            lsp.CompletionItem(
                label=value,
                kind=lsp.CompletionItemKind.Value,
                documentation=value.info["detail"],
                sort_text=str(idx),
            )
        )
    return items


def get_args_completions() -> list[lsp.CompletionItem]:
    """Get completion items for _args_ values.

    Returns:
        Completion items for args sequence options
    """
    return [
        lsp.CompletionItem(
            label="[]",
            kind=lsp.CompletionItemKind.Snippet,
            insert_text="[$0]",
            insert_text_format=lsp.InsertTextFormat.Snippet,
        ),
        lsp.CompletionItem(
            label="- item",
            kind=lsp.CompletionItemKind.Snippet,
            insert_text="\n- $0",
            insert_text_format=lsp.InsertTextFormat.Snippet,
            insert_text_mode=lsp.InsertTextMode.AdjustIndentation,
        ),
    ]


def get_hydra_special_key_value_completions(
    document: Document, position: lsp.Position
) -> list[lsp.CompletionItem]:
    """Create completion items for values of Hydra special keys.

    Generates completion suggestions for values of Hydra special keys
    (_partial_, _recursive_, _convert_, _args_) based on the key.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        A list of completion items for the special key values
    """
    # Only provide completions if typing a value
    if not is_typing_value(document, position):
        return []

    # Get the line and extract the key
    if position.line >= len(document.lines):
        return []

    line = document.lines[position.line]
    key_name = extract_special_key_from_line(line, position.character)

    if not key_name:
        return []

    # Dispatch to appropriate completion function based on key name
    match key_name:
        case HydraSpecialKey.PARTIAL:
            return get_partial_completions()
        case HydraSpecialKey.ARGS:
            return get_args_completions()
        case HydraSpecialKey.CONVERT:
            return get_convert_completions()
        case HydraSpecialKey.RECURSIVE:
            return get_recursive_completions()
        case _:
            return []
