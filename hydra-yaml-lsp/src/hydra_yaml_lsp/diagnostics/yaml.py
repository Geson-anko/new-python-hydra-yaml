from lsprotocol import types as lsp
from pygls.workspace import Document

from hydra_yaml_lsp.core.lint import validate_yaml

from .utils import message_type_to_severity


def get_yaml_diagnostics(document: Document) -> list[lsp.Diagnostic]:
    """Convert YAML validation messages to LSP diagnostics.

    Validates the document content and transforms any lint messages into
    LSP diagnostic objects that can be displayed in the editor.

    Args:
        document: The document to validate

    Returns:
        A list of LSP Diagnostic objects representing detected issues
    """
    results: list[lsp.Diagnostic] = []
    for msg in validate_yaml(document.source):
        results.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(
                        msg.position.start_line,
                        msg.position.start_column,
                    ),
                    end=lsp.Position(
                        msg.position.end_line,
                        msg.position.end_column,
                    ),
                ),
                message=msg.content,
                severity=message_type_to_severity(msg.type),
            )
        )
    return results
