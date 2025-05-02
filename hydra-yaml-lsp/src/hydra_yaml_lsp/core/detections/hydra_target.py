import inspect
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, TypedDict

import hydra.utils
from ruamel import yaml

from hydra_yaml_lsp.constants import HydraSpecialKey, HydraUtilityFunctions

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


@lru_cache
def detect_target_path(content: str) -> tuple[TargetValuePosition, ...]:
    """Detect 'path' values associated with Hydra utility functions in a YAML
    document.

    When Hydra utility functions (e.g., hydra.utils.get_method) are specified in a
    _target_ field, they require a corresponding 'path' field in the same block that
    contains an import path. This function detects these path values.

    Args:
        content: A string representing the entire YAML document.

    Returns:
        A tuple of TargetValuePosition objects, each containing information
        about a path value associated with a Hydra utility function.

    Examples:
        >>> content = '''
        ... utility:
        ...   _target_: hydra.utils.get_method
        ...   path: module.path.function
        ... '''
        >>> result = detect_target_path(content)
        >>> len(result)
        1
        >>> result[0].content
        'module.path.function'
    """
    results: list[TargetValuePosition] = []
    stream = yaml.YAML().scan(content)

    class TargetPathInfo(TypedDict, total=False):
        target_exists: bool
        path_value_pos: TargetValuePosition

    target_path_info_stack: list[TargetPathInfo] = []
    block_map_started_stack: list[bool] = []

    while (token := next(stream, None)) is not None:
        if isinstance(token, yaml.BlockMappingStartToken):
            block_map_started_stack.append(True)
            target_path_info_stack.append({})

        if isinstance(token, yaml.BlockSequenceStartToken):
            block_map_started_stack.append(False)

        if isinstance(token, yaml.BlockEndToken) and block_map_started_stack.pop():
            target_path_info = target_path_info_stack.pop()
            path_value_pos = target_path_info.get("path_value_pos")
            if path_value_pos and target_path_info.get("target_exists"):
                results.append(path_value_pos)

        if isinstance(token, yaml.KeyToken):
            token = next(stream)
            if not isinstance(token, yaml.ScalarToken):
                continue
            match token.value:
                case HydraSpecialKey.TARGET:
                    if not isinstance((token := next(stream)), yaml.ValueToken):
                        continue
                    if not isinstance((token := next(stream)), yaml.ScalarToken):
                        continue
                    if HydraUtilityFunctions.is_hydra_utility_function(token.value):
                        target_path_info_stack[-1]["target_exists"] = True
                case "path":
                    if not isinstance((token := next(stream)), yaml.ValueToken):
                        continue
                    if not isinstance((token := next(stream)), yaml.ScalarToken):
                        continue
                    target_path_info_stack[-1]["path_value_pos"] = TargetValuePosition(
                        lineno=token.start_mark.line,
                        start=token.start_mark.column,
                        end=token.end_mark.column,
                        content=token.value,
                    )
                case _:
                    pass
    return tuple(results)
