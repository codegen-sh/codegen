from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.statements.block_statement import BlockStatement
from codegen.sdk.shared.decorators.docs import apidoc
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock

if TYPE_CHECKING:
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock

Parent = TypeVar("Parent", bound="TSCodeBlock")


@apidoc
class TSBlockStatement(BlockStatement[Parent], TSHasBlock, Generic[Parent]):
    """Statement which contains a block."""
