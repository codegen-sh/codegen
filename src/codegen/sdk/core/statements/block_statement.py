from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.statements.statement import Statement
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId


TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class BlockStatement(Statement[TCodeBlock], HasBlock, ABC, Generic[TCodeBlock]):
    """Statement which contains a block.

    Attributes:
        code_block: The code block contained within the statement, if it exists.
    """

    code_block: TCodeBlock | None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TCodeBlock, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        self.code_block = self._parse_code_block()
        if self.code_block:
            self.code_block.parse()

    @property
    @reader
    def nested_code_blocks(self) -> list[TCodeBlock]:
        """Returns all nested CodeBlocks within the statement.

        Gets all nested CodeBlocks contained within this BlockStatement. A BlockStatement may contain
        at most one code block.

        Args:
            None

        Returns:
            list[TCodeBlock]: A list containing the statement's code block if it exists, otherwise an empty list.
        """
        if self.code_block:
            return [self.code_block]
        return []

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Gets all function calls within the statement's code block.

        Returns a list of FunctionCall instances contained within the statement's code block. If the statement does not have a code block, returns an empty list.

        Returns:
            list[FunctionCall]: A list of function call instances within the code block.
        """
        if self.code_block:
            return self.code_block.function_calls
        return []

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.code_block:
            self.code_block._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = super().descendant_symbols
        if self.code_block:
            symbols.extend(self.code_block.descendant_symbols)
        return symbols
