import logging

from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.server import HydraYamlLanguageServer

from .yaml import get_yaml_diagnostics

logger = logging.getLogger(__name__)


def register(server: HydraYamlLanguageServer) -> None:
    """Register diagnostics functionality to the server.

    Sets up document validation that triggers on open and change events.

    Args:
        server: The language server instance to register diagnostics with
    """

    def publish_diagnostics(document: Document) -> None:
        if not server.is_in_config_dir(document.uri):
            return

        diag = get_yaml_diagnostics(document)
        server.publish_diagnostics(document.uri, diag)
        logger.info(f"Published diagnostics: {len(diag)}")

    @server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
    async def did_open(params: lsp.DidOpenTextDocumentParams) -> None:
        """Validate document when opened."""
        publish_diagnostics(Document(params.text_document.uri))

    @server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
    async def did_change(params: lsp.DidChangeTextDocumentParams) -> None:
        publish_diagnostics(Document(params.text_document.uri))
