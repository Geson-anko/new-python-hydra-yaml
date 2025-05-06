"""Hydra YAML import path completion functionality."""

import inspect
import logging
import pkgutil
from functools import lru_cache

import hydra.utils
from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.completions.utils import is_typing_value
from hydra_yaml_lsp.constants import HydraSpecialKey, HydraUtilityFunction
from hydra_yaml_lsp.utils import get_yaml_block_lines

logger = logging.getLogger(__name__)


def is_typing_path_value(document: Document, position: lsp.Position) -> bool:
    """Check if the user is typing a path value in a YAML block that has a
    Hydra utility function _target_.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        True if the user is typing a path value, False otherwise
    """

    line = document.lines[position.line]
    line_prefix = line[: position.character].strip()
    if not (line.strip().startswith("path:") or "path:" in line_prefix):
        return False

    # Get the current YAML block
    block_lines = get_yaml_block_lines(document.source.splitlines(), position.line)

    # Look for a _target_ line with Hydra utility function
    for block_line in block_lines:
        if HydraSpecialKey.TARGET in block_line:
            # Extract the target value
            target_parts = block_line.split(f"{HydraSpecialKey.TARGET}:", 1)
            if len(target_parts) < 2:
                continue

            target_value = target_parts[1].strip()

            # Check if target is a Hydra utility function
            return HydraUtilityFunction.is_hydra_utility_function(target_value)

    return False


def is_typing_target_value(document: Document, position: lsp.Position) -> bool:
    """Check if the user is typing a _target_ value in a YAML document.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        True if the user is typing a _target_ value, False otherwise
    """
    # First check if typing a value

    line = document.lines[position.line]
    line_prefix = line[: position.character].strip()
    return (
        line.strip().startswith(f"{HydraSpecialKey.TARGET}:")
        or f"{HydraSpecialKey.TARGET}:" in line_prefix
    )


def extract_import_path(document: Document, position: lsp.Position) -> str:
    """Extract the current import path prefix from the document.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        The import path prefix
    """
    line = document.lines[position.line].strip()

    if ":" not in line:
        return ""

    return line.split(":", 1)[1].strip()


def get_module_members(
    module_path: str,
) -> tuple[tuple[str, lsp.CompletionItemKind], ...]:
    """Get members of a module by its import path.

    Args:
        module_path: Import path to the module

    Returns:
        Tuple of (name, kind) pairs
    """
    try:
        obj = hydra.utils.get_object(module_path)

        members = []
        for name in dir(obj):
            if name.startswith("_"):
                continue

            member = getattr(obj, name)
            if inspect.ismodule(member):
                kind = lsp.CompletionItemKind.Module
            elif inspect.isclass(member):
                kind = lsp.CompletionItemKind.Class
            elif inspect.ismethod(member):
                kind = lsp.CompletionItemKind.Method
            elif inspect.isfunction(member) or inspect.isbuiltin(member):
                kind = lsp.CompletionItemKind.Function
            elif name.isupper():
                kind = lsp.CompletionItemKind.Constant
            else:
                kind = lsp.CompletionItemKind.Variable
            members.append((name, kind))

        return tuple(members)
    except (ImportError, AttributeError):
        # Module not found or attribute error
        return tuple()


@lru_cache
def get_top_level_modules() -> tuple[str, ...]:
    """Get list of top-level Python modules.

    Returns:
        Tuple of module names
    """
    return tuple(m.name for m in pkgutil.iter_modules() if not m.name.startswith("_"))


def get_completion_for_import_path(prefix: str) -> list[lsp.CompletionItem]:
    """Get completion items for a Python import path.

    Args:
        prefix: The import path prefix

    Returns:
        List of completion items
    """
    items: list[lsp.CompletionItem] = []

    # If empty prefix, return top-level modules
    if not prefix:
        modules = get_top_level_modules()
        return [
            lsp.CompletionItem(
                label=module,
                kind=lsp.CompletionItemKind.Module,
                insert_text=module,
            )
            for module in modules
        ]

    # If prefix contains dots, we're looking for members of a module
    if "." in prefix:
        # Split into parent path and current part
        parent_path, current = prefix.rsplit(".", 1)

        # Get members of parent module
        members = get_module_members(parent_path)

        # Filter by current part if needed
        if current:
            members = [
                (name, kind) for name, kind in members if name.startswith(current)
            ]

        # Create completion items
        for name, kind in members:
            items.append(
                lsp.CompletionItem(
                    label=name,
                    kind=kind,
                    insert_text=name,
                )
            )

        return items

    # Otherwise, filter top-level modules
    modules = get_top_level_modules()
    filtered_modules = [m for m in modules if m.startswith(prefix)]

    return [
        lsp.CompletionItem(
            label=module,
            kind=lsp.CompletionItemKind.Module,
            insert_text=module,
        )
        for module in filtered_modules
    ]


def get_import_path_completions(
    document: Document, position: lsp.Position
) -> list[lsp.CompletionItem]:
    """Create completion items for Python import paths in a path field.

    Args:
        document: The document being edited
        position: The cursor position in the document

    Returns:
        A list of completion items for Python import paths
    """
    # First check if typing a value
    if not is_typing_value(document, position):
        return []

    # Check if current line contains "path:"
    if position.line >= len(document.lines):
        return []

    try:
        # Check if we are in a path value field
        if is_typing_path_value(document, position) or is_typing_target_value(
            document, position
        ):
            import_path = extract_import_path(document, position)
            return get_completion_for_import_path(import_path)

        return []

    except Exception as e:
        logger.error(f"Error generating import path completions: {e}")
        return []
