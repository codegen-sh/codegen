from codegen.sdk.extensions.lsp.codemods.base import CodeAction
from codegen.sdk.extensions.lsp.codemods.split_tests import SplitTests

ACTIONS: list[CodeAction] = [SplitTests()]
