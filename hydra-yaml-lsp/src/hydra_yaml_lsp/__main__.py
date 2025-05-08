"""Main entry point for the Hydra YAML Language Server."""

import logging
from collections.abc import Mapping
from typing import Any

from lsprotocol import types as lsp

from .completions import register as register_completion_items
from .diagnostics import register as register_diagnostics
from .semantic_tokens import register as register_semantic_tokens
from .server import HydraYamlLanguageServer

logger = logging.getLogger("hydra-yaml-lsp")


def start_server() -> None:
    """Start the LSP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    server = HydraYamlLanguageServer()

    @server.feature(lsp.INITIALIZE)
    def initialize(params: lsp.InitializeParams) -> None:
        options = params.initialization_options
        if options is None or not isinstance(options, Mapping):
            return

        update_configuration(options)

    @server.feature("custom/updateConfiguration")
    def update_configuration(params: Any) -> None:
        if "configDir" in params:
            config_dir = params["configDir"]
            if isinstance(config_dir, str):
                server.config_dir = config_dir
                logger.info(
                    f"Configured Hydra YAML root directory: {server.config_dir}"
                )

    register_semantic_tokens(server)
    register_completion_items(server)
    register_diagnostics(server)

    server.start_io()


if __name__ == "__main__":
    start_server()
