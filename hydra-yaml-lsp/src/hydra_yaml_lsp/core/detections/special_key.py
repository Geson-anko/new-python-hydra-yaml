import re
from dataclasses import dataclass
from functools import lru_cache

from ruamel import yaml

from hydra_yaml_lsp.constants import HydraSpecialKey

REFERENCE_PATTERN = re.compile(r"\$\{([^{}]+)\}")
FUNCTION_PATTERN = re.compile(r"\$\{([^:{}]+):")


@dataclass(frozen=True)
class SpecialKeyPosition:
    """Position and information about a special key in a YAML document.

    Attributes:
        lineno: Line number (0-indexed) where the special key appears.
        start: Column position where the special key starts.
        end: Column position where the special key ends.
        key: The special key text, including underscores.
    """

    lineno: int
    start: int
    end: int
    key: str


@lru_cache
def detect_special_keys(content: str) -> tuple[SpecialKeyPosition, ...]:
    """Detect all Hydra special keys in a YAML document.

    Searches through each line of the document and identifies all keys
    surrounded by underscores (e.g., _target_, _args_) followed by colons.

    Args:
        content: A string representing the entire YAML document.

    Returns:
        A list of SpecialKeyPosition objects, each containing information
        about a special key found in the document.

    Examples:
        >>> content = "_target_: module.path\\nregular: value\\n  _args_: value"
        >>> result = detect_special_keys_in_document(content)
        >>> [(pos.lineno, pos.start, pos.end, pos.key) for pos in result]
        [(0, 0, 8, '_target_'), (2, 2, 8, '_args_')]
    """
    results: list[SpecialKeyPosition] = []

    stream = yaml.YAML().scan(content)
    while (token := next(stream, None)) is not None:
        if isinstance(token, yaml.KeyToken):
            next_token: yaml.ScalarToken = next(stream)
            val = str(next_token.value)
            if val in HydraSpecialKey:
                results.append(
                    SpecialKeyPosition(
                        next_token.start_mark.line,
                        next_token.start_mark.column,
                        next_token.end_mark.column,
                        val,
                    )
                )
    return tuple(results)
