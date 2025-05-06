"""Hydra YAML Target Detection."""

from __future__ import annotations

import inspect
from collections.abc import Generator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Literal

import hydra.utils
from ruamel import yaml

from hydra_yaml_lsp.constants import HydraSpecialKey, HydraUtilityFunctions

# Type definitions for Python object classification
type ObjectType = Literal[
    "module",
    "class",
    "function",
    "method",
    "variable",
    "constant",
    "other",
]

# Type for YAML token stream iteration
type TokenStream = Generator[yaml.Token, None, None]


@dataclass(frozen=True)
class HydraTargetInfo:
    """Complete information about a _target_ declaration in Hydra YAML.

    This class aggregates all information related to a _target_ key including
    its position, the target value, and any arguments associated with it.

    Attributes:
        key: Position information for the _target_ key itself.
        value: Optional position information for the _target_ value.
        args: Tuple of associated argument keys and their values.
    """

    key: TargetKeyPosition
    value: ImportPathPosition | None
    args: tuple[ArgInfo, ...]


@dataclass
class ArgInfo:
    """Information about an argument associated with a _target_.

    Tracks both the argument key and its optional value in the YAML structure.

    Attributes:
        key: Position information for the argument key.
        value: Optional position information for the argument value.
    """

    key: ArgKeyPosition
    value: ArgValuePosition | None = None


@dataclass(frozen=True)
class HydraUtilityFunctionInfo:
    utility_function: HydraUtilityFunctions
    path: ImportPathPosition


@dataclass(frozen=True)
class Position:
    """Basic position information for text elements in YAML.

    Attributes:
        lineno: Zero-indexed line number in the document.
        start: Starting column position in the line.
        end: Ending column position in the line.
        content: The actual text content at this position.
    """

    lineno: int
    start: int
    end: int
    content: str


@dataclass(frozen=True)
class TargetKeyPosition(Position):
    """Position information specifically for _target_ keys."""

    pass


@dataclass(frozen=True)
class ArgKeyPosition(Position):
    """Position information specifically for argument keys."""

    pass


@dataclass(frozen=True)
class ArgValuePosition(Position):
    """Position information specifically for argument values."""

    pass


@dataclass(frozen=True)
class TargetValueHighlight(Position):
    """Highlight information for a part of a target value path.

    Represents a single segment of a dotted path (e.g., 'module.Class.method')
    with its determined object type for syntax highlighting.

    Attributes:
        object_type: The type of Python object this path segment represents.
    """

    object_type: ObjectType


@dataclass(frozen=True)
class ImportPathPosition(Position):
    """Position information for _target_ values.

    Represents the full value of a _target_ key, including methods to
    extract highlights for individual path components.
    """

    def get_highlights(self) -> list[TargetValueHighlight]:
        """Extract highlight positions for each part of the target value path.

        For example, "module.Class.method" would be split into three highlights:
        - "module" (module type)
        - "Class" (class type)
        - "method" (function type)

        Returns:
            A list of TargetValueHighlight objects, each representing a part
            of the target path with its object type.
        """
        results: list[TargetValueHighlight] = []
        path = ""
        prev_end = self.start

        # Process each dot-separated component
        for i, part in enumerate(self.content.split(".")):
            # Build up the full path progressively
            if i == 0:
                path = part
            else:
                path = f"{path}.{part}"

            # Determine what type of object this path represents
            object_type = get_object_type(path)
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
            prev_end = end + 1  # +1 to skip the dot separator
        return results


def get_object_type(path: str) -> ObjectType:
    """Determine the type of Python object for a given import path.

    Args:
        path: The import path to inspect, e.g., "module.submodule.Class".

    Returns:
        An ObjectType value representing the type of the object.
    """
    try:
        object = hydra.utils.get_object(path)

        # Classify using Python's inspection capabilities
        if inspect.ismodule(object):
            return "module"
        elif inspect.isclass(object):
            return "class"
        elif inspect.isfunction(object):
            return "function"
        elif inspect.ismethod(object):
            return "method"
        elif inspect.isbuiltin(object):
            return "function"
        elif path.rsplit(".", maxsplit=1)[-1].isupper():
            # Convention: UPPER_CASE names are usually constants
            return "constant"
        else:
            return "variable"
    except ImportError:
        # Object doesn't exist or can't be imported
        return "other"


@lru_cache
def detect_hydra_targets(content: str) -> tuple[HydraTargetInfo, ...]:
    """Detect all Hydra _target_ declarations in a YAML document.

    This function parses a YAML document to find all _target_ keys and collects
    associated information including the target value and any arguments that
    appear in the same block. It maintains block context by using a stack to
    track nested structures.

    Args:
        content: The YAML document content as a string.

    Returns:
        A tuple of HydraTargetInfo objects containing detected target information.
    """
    results: list[HydraTargetInfo] = []

    @dataclass
    class Info:
        """Internal tracking structure for target information within blocks."""

        key: TargetKeyPosition | None = None
        value: ImportPathPosition | None = None
        args: list[ArgInfo] = field(default_factory=list)

    # Stacks for tracking nested structure
    info_stack: list[Info] = []  # Track target info per block
    block_map_started_stack = []  # Track whether block started with mapping

    stream = yaml.YAML().scan(content)

    def next_to_value_scalar_token(stream: TokenStream) -> yaml.Token:
        """Advance stream to the next value scalar token."""
        if not isinstance(token := next(stream), yaml.ValueToken):
            return token
        if not isinstance(token := next(stream), yaml.ScalarToken):
            return token
        return token

    def process_token(token: yaml.Token, stream: TokenStream):
        """Process a single YAML token and update tracking state."""
        # Block tracking - maintain context for nested structures
        if isinstance(token, yaml.BlockMappingStartToken):
            block_map_started_stack.append(True)
            info_stack.append(Info())
        elif isinstance(token, yaml.BlockSequenceStartToken):
            block_map_started_stack.append(False)

        # Block ending - check if we have a complete target to report
        if (
            isinstance(token, yaml.BlockEndToken)
            and len(block_map_started_stack) > 0
            and block_map_started_stack.pop()
        ):
            info = info_stack.pop()
            key, value = info.key, info.value
            if key is not None:
                # We found a _target_ key, create the result
                results.append(HydraTargetInfo(key, value, tuple(info.args)))

        # Key processing - detect _target_ keys and other argument keys
        if isinstance(token, yaml.KeyToken):
            token = next(stream)
            if isinstance(token, yaml.ScalarToken):
                if token.value == HydraSpecialKey.TARGET:
                    # Found a _target_ key - record its position
                    info_stack[-1].key = TargetKeyPosition(
                        token.start_mark.line,
                        token.start_mark.column,
                        token.end_mark.column,
                        token.value,
                    )

                    # Try to get the corresponding value
                    token = next_to_value_scalar_token(stream)
                    if isinstance(token, yaml.ScalarToken):
                        info_stack[-1].value = ImportPathPosition(
                            token.start_mark.line,
                            token.start_mark.column,
                            token.end_mark.column,
                            token.value,
                        )

                elif token.value not in HydraSpecialKey:
                    # Found a non-special key - treat as argument
                    arg_info = ArgInfo(
                        ArgKeyPosition(
                            token.start_mark.line,
                            token.start_mark.column,
                            token.end_mark.column,
                            token.value,
                        )
                    )

                    # Try to get the argument value
                    token = next_to_value_scalar_token(stream)

                    if isinstance(token, yaml.ScalarToken):
                        arg_info.value = ArgValuePosition(
                            token.start_mark.line,
                            token.start_mark.column,
                            token.end_mark.column,
                            token.value,
                        )

                    # Add to current block's argument list
                    info_stack[-1].args.append(arg_info)

            # Process recursively for next token.
            process_token(token, stream)

    # Main processing loop - handle each token in the stream
    while (token := next(stream, None)) is not None:
        process_token(token, stream)

    return tuple(results)


def detect_target_values(content: str) -> list[ImportPathPosition]:
    """Extract all target values from a YAML document.

    Args:
        content: The YAML document content as a string.

    Returns:
        A list of TargetValuePosition objects representing all _target_ values found.

    Examples:
        >>> content = "_target_: my.module.Class"
        >>> detect_target_values(content)
        [TargetValuePosition(lineno=0, start=9, end=24, content="my.module.Class")]
    """
    results: list[ImportPathPosition] = []

    for info in detect_hydra_targets(content):
        if info.value is not None:
            results.append(info.value)
    return results


def detect_target_arg_keys(content: str) -> list[ArgKeyPosition]:
    """Extract all argument keys associated with targets in a YAML document.

    Args:
        content: The YAML document content as a string.

    Returns:
        A list of ArgKeyPosition objects representing all argument keys found
        in target configurations.

    Examples:
        >>> content = '''
        ... component:
        ...   _target_: my.Class
        ...   arg1: value
        ...   arg2: value
        ... '''
        >>> arg_keys = detect_target_arg_keys(content)
        >>> [arg.content for arg in arg_keys]
        ['arg1', 'arg2']
    """
    results: list[ArgKeyPosition] = []
    for info in detect_hydra_targets(content):
        for arg_info in info.args:
            results.append(arg_info.key)
    return results


def detect_target_paths(content: str) -> list[HydraUtilityFunctionInfo]:
    results: list[HydraUtilityFunctionInfo] = []

    for info in detect_hydra_targets(content):
        if info.value is None or not HydraUtilityFunctions.is_hydra_utility_function(
            info.value.content
        ):
            continue
        for arg in info.args:
            if arg.value is None:
                continue
            if arg.key.content == "path":
                results.append(
                    HydraUtilityFunctionInfo(
                        HydraUtilityFunctions.from_import_path(info.value.content),
                        ImportPathPosition(
                            arg.value.lineno,
                            arg.value.start,
                            arg.value.end,
                            arg.value.content,
                        ),
                    )
                )
    return results
