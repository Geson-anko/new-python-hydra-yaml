"""Hydra YAML Language Server implementation."""

import logging
from pathlib import Path

from pygls.server import LanguageServer
from pygls.uris import to_fs_path


class HydraYamlLanguageServer(LanguageServer):
    """Language Server for Hydra YAML files."""

    config_dir: str = ""

    def __init__(self) -> None:
        """Initialize the Hydra YAML language server."""
        super().__init__("hydra-yaml-server", "v0.1")
        self.logger = logging.getLogger("hydra-yaml-server")
        self.logger.info("Hydra YAML Language Server initialized")

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
