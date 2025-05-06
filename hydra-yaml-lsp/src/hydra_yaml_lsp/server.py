"""Hydra YAML Language Server implementation."""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from lsprotocol import types as lsp
from pygls.server import LanguageServer
from pygls.uris import to_fs_path

from .completions import register as register_completion_items
from .semantic_tokens import register as register_semantic_tokens

logger = logging.getLogger("hydra-yaml-lsp")


class HydraYamlLanguageServer(LanguageServer):
    """Language Server for Hydra YAML files."""

    config_dir: str = ""

    def __init__(self) -> None:
        """Initialize the Hydra YAML language server."""
        super().__init__("hydra-yaml-server", "v0.1")

        logger.info("Hydra YAML Language Server initialized")

    def is_in_config_dir(self, file_uri: str) -> bool:
        """Check if file is in the configured directory."""
        if not self.config_dir:
            return False  # If no config dir set, process no files

        path = to_fs_path(file_uri)
        if path is None:
            return False
        file_path = Path(path).absolute()
        config_path = Path(self.config_dir).absolute()

        # Handle absolute and relative paths
        return str(file_path).startswith(str(config_path))


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

    server.start_io()
