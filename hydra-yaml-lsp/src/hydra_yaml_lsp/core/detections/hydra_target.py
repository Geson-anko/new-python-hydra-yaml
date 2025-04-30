import inspect
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import hydra.utils
from ruamel import yaml

from hydra_yaml_lsp.constants import HydraSpecialKey

# Type for Python object classification
type ObjectType = Literal[
    "module",
    "class",
    "function",
    "method",
    "variable",
    "constant",
    "other",
]


@dataclass
class TargetValueHighlight:
    """Highlight information for a part of a target value path.

    Attributes:
        lineno: Line number (0-indexed) where the highlight appears.
        start: Column position where the highlight starts.
        end: Column position where the highlight ends.
        content: The part of the path being highlighted.
        object_type: The type of the Python object represented by the path.
    """

    lineno: int
    start: int
    end: int
    content: str
    object_type: ObjectType


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

    def get_highlights(self) -> list[TargetValueHighlight]:
        """Extract highlight positions for each part of the target value path.

        Splits the target path by dots and creates a highlight for each part,
        identifying the object type for each segment of the import path.

        Returns:
            A list of TargetValueHighlight objects, each representing a part
            of the target path with its object type.
        """
        results: list[TargetValueHighlight] = []
        path = ""
        prev_end = self.start
        for i, part in enumerate(self.content.split(".")):
            if i == 0:
                path = part
            else:
                path = f"{path}.{part}"

            object_type = _get_object_type(path)
            end = prev_end + len(part)
            results.append(
                TargetValueHighlight(
                    lineno=self.lineno,
                    start=prev_end,
                    end=end,
                    content=part,
                    object_type=object_type,
                )
            )
            prev_end = end + 1  # +1 for ignore `.`
        return results


def _get_object_type(path: str) -> ObjectType:
    """Determine the type of Python object for a given import path.

    Args:
        path: The import path to inspect, e.g., "module.submodule.Class".

    Returns:
        An ObjectType value representing the type of the object.
        If the object cannot be imported, returns "other".
    """
    try:
        object = hydra.utils.get_object(path)
        if inspect.ismodule(object):
            return "module"
        elif inspect.isclass(object):
            return "class"
        elif inspect.isfunction(object):
            return "function"
        elif inspect.ismethod(object):
            return "method"
        elif path.rsplit(".", maxsplit=1)[-1].isupper():
            return "constant"
        else:
            return "variable"
    except ImportError:
        return "other"


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
