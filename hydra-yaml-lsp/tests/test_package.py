"""Tests package top level features."""

import tomllib
from pathlib import Path

import hydra_yaml_lsp

PROJECT_ROOT = Path(__file__).parent.parent


def test_version():
    with open(PROJECT_ROOT / "pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)

    assert hydra_yaml_lsp.__version__ == pyproject["project"]["version"]
