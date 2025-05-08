from lsprotocol import types as lsp

from hydra_yaml_lsp.core.lint import MessageType


def message_type_to_severity(msg_type: MessageType) -> lsp.DiagnosticSeverity:
    """Convert MessageType to LSP DiagnosticSeverity.

    Args:
        msg_type: The message type from the lint module

    Returns:
        The corresponding LSP DiagnosticSeverity
    """
    match msg_type:
        case MessageType.ERROR:
            return lsp.DiagnosticSeverity.Error
        case MessageType.WARNING:
            return lsp.DiagnosticSeverity.Warning
        case MessageType.INFO:
            return lsp.DiagnosticSeverity.Information
