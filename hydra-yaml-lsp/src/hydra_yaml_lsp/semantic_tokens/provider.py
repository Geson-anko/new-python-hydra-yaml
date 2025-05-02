"""Hydra YAML semantic token provider implementation."""

from lsprotocol import types as lsp
from pygls.server import LanguageServer
from pygls.workspace import Document

from hydra_yaml_lsp.core.detections import (
    detect_hydra_package,
    detect_interpolation_positions,
    detect_special_keys,
    detect_target_values,
)

from .builder import (
    SemanticToken,
    SemanticTokensBuilder,
    TokenModifier,
    TokenType,
)


def register(server: LanguageServer) -> None:
    """Register semantic token functionality to the server."""

    @server.feature(
        lsp.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
        lsp.SemanticTokensLegend(
            token_types=TokenType.get_legend(),
            token_modifiers=TokenModifier.get_legend(),
        ),
    )
    def semantic_tokens_full(params: lsp.SemanticTokensParams) -> lsp.SemanticTokens:
        """Provide semantic tokens for YAML documents."""
        document_uri = params.text_document.uri
        document = server.workspace.get_document(document_uri)

        data = get_tokens_data_for_document(document)
        return lsp.SemanticTokens(data=data)


def get_tokens_data_for_document(document: Document) -> list[int]:
    """Extract semantic token data from a document.

    Args:
        document: The document to process

    Returns:
        Semantic token data array in LSP format
    """
    text = document.source
    builder = SemanticTokensBuilder()

    # Add special keys
    for key in detect_special_keys(text):
        builder.add_tokens(SemanticToken.from_special_key(key))

    # Add target values
    for target in detect_target_values(text):
        # Add tokens from highlight information
        for highlight in target.get_highlights():
            builder.add_tokens(SemanticToken.from_target_highlight(highlight))

    # Add interpolations
    for interp in detect_interpolation_positions(text):
        for highlight in interp.get_highlights():
            builder.add_tokens(SemanticToken.from_interpolation_highlight(highlight))

    # Add package declaration
    package_info = detect_hydra_package(text)
    if package_info:
        builder.add_tokens(*SemanticToken.from_package_directive(package_info))

    # Build and get data
    return builder.build()
