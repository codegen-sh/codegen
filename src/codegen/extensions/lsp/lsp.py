import logging

from lsprotocol import types

import codegen
from codegen.extensions.lsp.definition import go_to_definition
from codegen.extensions.lsp.document_symbol import get_document_symbol
from codegen.extensions.lsp.protocol import CodegenLanguageServerProtocol
from codegen.extensions.lsp.range import get_range
from codegen.extensions.lsp.server import CodegenLanguageServer
from codegen.extensions.lsp.utils import get_path
from codegen.sdk.codebase.diff_lite import ChangeType, DiffLite
from codegen.sdk.core.file import SourceFile
from codegen.shared.logging.get_logger import get_logger

version = getattr(codegen, "__version__", "v0.1")
server = CodegenLanguageServer("codegen", version, protocol_cls=CodegenLanguageServerProtocol)
logger = get_logger(__name__)


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: CodegenLanguageServer, params: types.DidOpenTextDocumentParams) -> None:
    """Handle document open notification."""
    logger.info(f"Document opened: {params.text_document.uri}")
    # The document is automatically added to the workspace by pygls
    # We can perform any additional processing here if needed
    path = get_path(params.text_document.uri)
    server.io.update_file(path, params.text_document.version)
    file = server.codebase.get_file(str(path), optional=True)
    if not isinstance(file, SourceFile) and path.suffix in server.codebase.ctx.extensions:
        sync = DiffLite(change_type=ChangeType.Added, path=path)
        server.codebase.ctx.apply_diffs([sync])


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: CodegenLanguageServer, params: types.DidChangeTextDocumentParams) -> None:
    """Handle document change notification."""
    logger.info(f"Document changed: {params.text_document.uri}")
    # The document is automatically updated in the workspace by pygls
    # We can perform any additional processing here if needed
    path = get_path(params.text_document.uri)
    server.io.update_file(path, params.text_document.version)
    sync = DiffLite(change_type=ChangeType.Modified, path=path)
    server.codebase.ctx.apply_diffs([sync])


@server.feature(types.WORKSPACE_TEXT_DOCUMENT_CONTENT)
def workspace_text_document_content(server: CodegenLanguageServer, params: types.TextDocumentContentParams) -> types.TextDocumentContentResult:
    """Handle workspace text document content notification."""
    logger.debug(f"Workspace text document content: {params.uri}")
    path = get_path(params.uri)
    if not server.io.file_exists(path):
        logger.warning(f"File does not exist: {path}")
        return types.TextDocumentContentResult(
            text="",
        )
    content = server.io.read_text(path)
    return types.TextDocumentContentResult(
        text=content,
    )


@server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: CodegenLanguageServer, params: types.DidCloseTextDocumentParams) -> None:
    """Handle document close notification."""
    logger.info(f"Document closed: {params.text_document.uri}")
    # The document is automatically removed from the workspace by pygls
    # We can perform any additional cleanup here if needed
    path = get_path(params.text_document.uri)
    server.io.close_file(path)


@server.feature(
    types.TEXT_DOCUMENT_RENAME,
    options=types.RenameOptions(work_done_progress=True),
)
def rename(server: CodegenLanguageServer, params: types.RenameParams) -> types.RenameResult:
    symbol = server.get_symbol(params.text_document.uri, params.position)
    if symbol is None:
        logger.warning(f"No symbol found at {params.text_document.uri}:{params.position}")
        return
    logger.info(f"Renaming symbol {symbol.name} to {params.new_name}")
    task = server.progress_manager.begin_with_token(f"Renaming symbol {symbol.name} to {params.new_name}", params.work_done_token)
    symbol.rename(params.new_name)
    task.update("Committing changes")
    server.codebase.commit()
    task.end()
    return server.io.get_workspace_edit()


@server.feature(
    types.TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    options=types.DocumentSymbolOptions(work_done_progress=True),
)
def document_symbol(server: CodegenLanguageServer, params: types.DocumentSymbolParams) -> types.DocumentSymbolResult:
    file = server.get_file(params.text_document.uri)
    symbols = []
    task = server.progress_manager.begin_with_token(f"Getting document symbols for {params.text_document.uri}", params.work_done_token, count=len(file.symbols))
    for idx, symbol in enumerate(file.symbols):
        task.update(f"Getting document symbols for {params.text_document.uri}", count=idx)
        symbols.append(get_document_symbol(symbol))
    task.end()
    return symbols


@server.feature(
    types.TEXT_DOCUMENT_DEFINITION,
    options=types.DefinitionOptions(work_done_progress=True),
)
def definition(server: CodegenLanguageServer, params: types.DefinitionParams):
    node = server.get_node_under_cursor(params.text_document.uri, params.position)
    task = server.progress_manager.begin_with_token(f"Getting definition for {params.text_document.uri}", params.work_done_token)
    resolved = go_to_definition(node, params.text_document.uri, params.position)
    task.end()
    return types.Location(
        uri=resolved.file.path.as_uri(),
        range=get_range(resolved),
    )


@server.feature(
    types.TEXT_DOCUMENT_CODE_ACTION,
    options=types.CodeActionOptions(resolve_provider=True, work_done_progress=True),
)
def code_action(server: CodegenLanguageServer, params: types.CodeActionParams) -> types.CodeActionResult:
    logger.info(f"Received code action: {params}")
    actions = server.get_actions_for_range(params)
    return actions


@server.feature(
    types.CODE_ACTION_RESOLVE,
)
def code_action_resolve(server: CodegenLanguageServer, params: types.CodeAction) -> types.CodeAction:
    return server.resolve_action(params)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server.start_io()
