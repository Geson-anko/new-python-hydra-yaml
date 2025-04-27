"""Hydra YAML Language Server implementation."""

import logging

from pygls.server import LanguageServer

logger = logging.getLogger("hydra-yaml-lsp")


class HydraYamlLanguageServer(LanguageServer):
    """Language Server for Hydra YAML files.

    Provides completions, diagnostics, and other LSP features for YAML
    files that use Hydra configuration.
    """

    def __init__(self) -> None:
        """Initialize the Hydra YAML language server."""
        super().__init__("hydra-yaml-server", "v0.1")

        logger.info("Hydra YAML Language Server initialized")


def start_server() -> None:
    """Start the LSP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    server = HydraYamlLanguageServer()
    server.start_io()
