from dataclasses import dataclass
from functools import lru_cache

from ruamel import yaml

from hydra_yaml_lsp.constants import HydraSpecialKey


@dataclass(frozen=True)
class TargetValuePosition:
    """Position and information about a _target_ value in a YAML document.

    Attributes:
        lineno: Line number (0-indexed) where the target value appears.
        start: Column position where the target value starts.
        end: Column position where the target value ends.
        content: The actual content of the target value.
    """

    lineno: int
    start: int
    end: int
    content: str


@lru_cache
def detect_target_values(content: str) -> tuple[TargetValuePosition, ...]:
    """Detect all Hydra _target_ values in a YAML document.

    Searches through the document and identifies values associated with
    the _target_ special key.

    Args:
        content: A string representing the entire YAML document.

    Returns:
        A tuple of TargetValuePosition objects, each containing information
        about a target value found in the document.

    Examples:
        >>> content = "_target_: module.path\\nregular: value"
        >>> result = detect_target_values(content)
        >>> [(pos.lineno, pos.start, pos.end, pos.content) for pos in result]
        [(0, 9, 20, 'module.path')]
    """

    results: list[TargetValuePosition] = []
    stream = yaml.YAML().scan(content)

    while (token := next(stream, None)) is not None:
        if (
            isinstance(token, yaml.KeyToken)
            and next(stream).value == HydraSpecialKey.TARGET
            and isinstance(next(stream), yaml.ValueToken)
        ):
            value_token: yaml.ScalarToken = next(stream)
            results.append(
                TargetValuePosition(
                    lineno=value_token.start_mark.line,
                    start=value_token.start_mark.column,
                    end=value_token.end_mark.column,
                    content=value_token.value,
                )
            )
    return tuple(results)
