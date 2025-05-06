"""Hydra YAML callable argument completion functionality."""

import inspect
import logging

import hydra.utils
from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.constants import HydraSpecialKey
from hydra_yaml_lsp.utils import get_yaml_block_lines

from .utils import is_typing_key

logger = logging.getLogger(__name__)


def extract_target_value_from_block(block_lines: list[str]) -> str | None:
    """Extract the _target_ value from a YAML block.

    Args:
        block_lines: List of lines in the current YAML block

    Returns:
        The _target_ value or None if not found
    """
    for line in block_lines:
        if HydraSpecialKey.TARGET in line and ":" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                return parts[1].strip()
    return None


def get_existing_keys_in_block(block_lines: list[str]) -> set[str]:
    """Get all existing keys in the current YAML block.

    Args:
        block_lines: List of lines in the current YAML block

    Returns:
        Set of existing key names
    """
    existing_keys = set()
    for line in block_lines:
        # Skip lines that don't have a colon
        if ":" not in line:
            continue

        # Skip special keys
        line = line.strip()
        # Extract key
        key = line.split(":", 1)[0].strip()
        if key in HydraSpecialKey:
            continue

        if key:
            existing_keys.add(key)

    return existing_keys


def get_callable_args(import_path: str) -> list[str] | None:
    """Get the argument names of a callable identified by its import path.

    Args:
        import_path: Import path to the callable

    Returns:
        List of argument names or None if not found
    """
    try:
        obj = hydra.utils.get_object(import_path)

        # Check if object is callable
        if not callable(obj):
            return None

        # Get signature
        sig = inspect.signature(obj)

        # Extract parameter names, filtering out positional-only and **kwargs
        arg_names = []
        for name, param in sig.parameters.items():
            # Skip positional-only and **kwargs parameters
            if param.kind in [
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            ]:
                arg_names.append(name)

        return arg_names
    except ImportError:
        return None


def get_callable_arg_completions(
    document: Document, position: lsp.Position
) -> list[lsp.CompletionItem]:
    """Create completion items for callable arguments.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        A list of completion items for callable arguments
    """
    # Only provide completions if typing a key
    if not is_typing_key(document, position):
        return []

    # Get the current YAML block
    try:
        current_line = min(position.line, len(document.lines) - 1)
        block_lines = get_yaml_block_lines(document.source.splitlines(), current_line)

        # Extract _target_ value
        target_value = extract_target_value_from_block(block_lines)
        if not target_value:
            return []

        # Get callable arguments
        args = get_callable_args(target_value)
        if not args:
            return []

        # Get existing keys to exclude
        existing_keys = get_existing_keys_in_block(block_lines)

        # Create completion items for each argument not already used
        items = []
        for arg in args:
            if arg not in existing_keys:
                item = lsp.CompletionItem(
                    label=arg,
                    kind=lsp.CompletionItemKind.Property,
                    insert_text=f"{arg}: ${{1}}",
                    insert_text_format=lsp.InsertTextFormat.Snippet,
                    insert_text_mode=lsp.InsertTextMode.AdjustIndentation,
                    documentation=f"Argument for {target_value}",
                )
                items.append(item)

        return items
    except Exception as e:
        logger.error(f"Error providing callable arg completions: {e}")
        return []
