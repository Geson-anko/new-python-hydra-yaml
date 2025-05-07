"""Hydra YAML completion provider implementation."""

import logging

from lsprotocol import types as lsp

from hydra_yaml_lsp.server import HydraYamlLanguageServer

from .callable_arg import get_callable_arg_completions
from .import_path import get_import_path_completions
from .special_key import get_hydra_special_key_completions
from .special_key_value import get_hydra_special_key_value_completions

logger = logging.getLogger(__name__)


def register(server: HydraYamlLanguageServer) -> None:
    """Register completion functionality to the server.

    Sets up completion providers for YAML files using LSP.

    Args:
        server: The language server instance to register the features with
    """

    @server.feature(
        lsp.TEXT_DOCUMENT_COMPLETION,
        lsp.CompletionOptions(trigger_characters=[" ", "."]),
    )
    def completions(params: lsp.CompletionParams) -> lsp.CompletionList:
        document_uri = params.text_document.uri
        if not server.is_in_config_dir(document_uri):
            return lsp.CompletionList(False, [])

        position = params.position

        document = server.workspace.get_document(document_uri)

        items: list[lsp.CompletionItem] = []

        try:
            # Add Hydra special key completions (_target_, _args_, etc.)
            items.extend(get_hydra_special_key_completions(document, position))
            # Add Hydra special key value completions
            items.extend(get_hydra_special_key_value_completions(document, position))
            # Add Python import path completions
            items.extend(get_import_path_completions(document, position))
            # Add callable argument completions
            items.extend(get_callable_arg_completions(document, position))
        except Exception as e:
            logger.error(f"Error providing completions: {e}")

        return lsp.CompletionList(is_incomplete=False, items=items)
