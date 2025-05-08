from dataclasses import dataclass
from enum import StrEnum, auto


class MessageType(StrEnum):
    """Message type for linting."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass(frozen=True)
class Position:
    """Position information in a document.

    Attributes:
        start_line: Zero-indexed line number where the issue starts.
        end_line: Zero-indexed line number where the issue ends.
        start_column: Zero-indexed column number where the issue starts.
        end_column: Zero-indexed column number where the issue ends.
    """

    start_line: int
    end_line: int
    start_column: int
    end_column: int


@dataclass(frozen=True)
class Message:
    """Lint message with position and severity information.

    Attributes:
        content: The message text explaining the issue.
        type: The severity level of the message.
        position: The position of the issue in the document.
    """

    content: str
    type: MessageType
    position: Position
