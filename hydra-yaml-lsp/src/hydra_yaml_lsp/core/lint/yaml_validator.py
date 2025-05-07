"""YAML validation utilities."""

import logging
from functools import lru_cache

from ruamel import yaml
from ruamel.yaml import composer, constructor, scanner
from ruamel.yaml.error import StringMark

from hydra_yaml_lsp.core.lint.message import Message, MessageType, Position

logger = logging.getLogger(__name__)


@lru_cache
def validate_yaml(content: str) -> tuple[Message, ...]:
    """Validate YAML content for syntax errors.

    Uses ruamel.yaml to parse the content and catches any parsing errors.
    Results are cached to improve performance for repeated validations.

    Args:
        content: The YAML content to validate.

    Returns:
        A list of Message objects describing any errors found.
    """
    messages: list[Message] = []

    if not content.strip():
        return ()

    try:
        yaml.YAML().load(content)
        return ()
    except (
        scanner.ScannerError,
        composer.ComposerError,
        constructor.DuplicateKeyError,
    ) as e:
        # Extract error position information
        problem_mark = e.problem_mark
        print(e.context)
        print(type(problem_mark), type(e))
        if not isinstance(problem_mark, StringMark):
            return ()
        print(e)

        # Create a helpful error message
        match e:
            case scanner.ScannerError():
                error_msg = f"YAML syntax error: {e.problem}"
                if e.context:
                    error_msg += f"\nContext: {e.context}"
            case composer.ComposerError():
                error_msg = f"YAML composition error: {str(e)}"
            case constructor.DuplicateKeyError():
                error_msg = f"YAML constructor error: {str(e)}"
        position = Position(
            start_line=problem_mark.line,
            end_line=problem_mark.line,
            start_column=problem_mark.column,
            end_column=problem_mark.column + 1,
        )

        messages.append(
            Message(content=error_msg, type=MessageType.ERROR, position=position)
        )
    except Exception as e:
        print(type(e))
        # Catch any other exceptions
        logger.error(f"Unexpected error during YAML validation: {str(e)}")
        messages.append(
            Message(
                content=f"YAML validation error: {str(e)}",
                type=MessageType.ERROR,
                position=Position(0, 0, 0, 0),
            )
        )

    return tuple(messages)
