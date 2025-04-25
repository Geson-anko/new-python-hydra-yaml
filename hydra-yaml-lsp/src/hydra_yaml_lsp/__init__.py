from importlib import metadata

from hydra_yaml_lsp._core import hello_from_bin

__version__ = metadata.version(__name__.replace("_", "-"))


def hello() -> str:
    return hello_from_bin()
