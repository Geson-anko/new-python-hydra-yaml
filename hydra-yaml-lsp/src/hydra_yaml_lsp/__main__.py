"""Launch the Language Server."""

import logging

from pygls.server import LanguageServer

from . import __version__ as version

if __name__ != "__main__":
    raise RuntimeError("This file must run as main script.")

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

server = LanguageServer("hydra-yaml-language-server", version)

server.start_tcp("127.0.0.1", 8080)
