from typing import TYPE_CHECKING

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.extensions.lsp.codemods.base import CodeAction

if TYPE_CHECKING:
    from codegen.sdk.extensions.lsp.server import GraphSitterLanguageServer


class MoveSymbolToFile(CodeAction):
    name = "Move Symbol to File"

    def is_applicable(self, server: "GraphSitterLanguageServer", node: Editable) -> bool:
        return True

    def execute(self, server: "GraphSitterLanguageServer", node: Editable) -> None:
        target_file = server.window_show_message_request(
            "Select the file to move the symbol to",
            server.codebase.files,
        ).result(timeout=10)
        if target_file is None:
            return
        server.codebase.move_symbol(node.parent_symbol, target_file)
