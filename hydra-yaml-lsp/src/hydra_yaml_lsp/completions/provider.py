"""Hydra YAML completion provider implementation."""

import logging

from lsprotocol import types as lsp
from pygls.server import LanguageServer

from .special_key import get_hydra_special_key_completions, is_typing_key

logger = logging.getLogger(__name__)


def register(server: LanguageServer) -> None:
    """Register completion functionality to the server.

    Sets up completion providers for YAML files using LSP.

    Args:
        server: The language server instance to register the features with
    """

    @server.feature(
        lsp.TEXT_DOCUMENT_COMPLETION,
        lsp.CompletionOptions(trigger_characters=[" "]),
    )
    def special_key_completions(params: lsp.CompletionParams) -> lsp.CompletionList:
        document_uri = params.text_document.uri
        position = params.position

        document = server.workspace.get_document(document_uri)

        items: list[lsp.CompletionItem] = []

        try:
            # Check if user is typing a key (rather than a value)
            if is_typing_key(document, position):
                # Add Hydra special key completions (_target_, _args_, etc.)
                items.extend(get_hydra_special_key_completions(document, position))
        except Exception as e:
            logger.error(f"Error providing completions: {e}")

        return lsp.CompletionList(is_incomplete=False, items=items)
