from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.supports_generic import SupportsGenerics
from codegen.sdk.enums import SymbolType
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.attribute import Attribute
    from codegen.sdk.core.statements.statement import Statement


TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")
TAttribute = TypeVar("TAttribute", bound="Attribute")
Parent = TypeVar("Parent", bound="HasBlock")


@apidoc
class TypeAlias(SupportsGenerics, HasValue, HasBlock, HasAttribute[TAttribute], Generic[TCodeBlock, TAttribute]):
    """Abstract representation of a Type object.

    Only applicable for some programming languages like TypeScript.

    Attributes:
        symbol_type: The type of symbol, set to SymbolType.Interface.
        code_block: The code block associated with this type alias.
    """

    symbol_type = SymbolType.Interface
    code_block: TCodeBlock

    def __init__(
        self,
        ts_node: TSNode,
        file_node_id: NodeId,
        ctx: CodebaseContext,
        parent: Statement[CodeBlock[Parent, ...]],
    ) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        value_node = self.ts_node.child_by_field_name("value")
        self._value_node = self._parse_type(value_node) if value_node else None
        self.type_parameters = self.child_by_field_name("type_parameters")

    @property
    @abstractmethod
    @reader
    def attributes(self) -> list[TAttribute]:
        """List of expressions defined in this Type object."""

    @reader
    def get_attribute(self, name: str) -> TAttribute | None:
        """Get attribute by name."""
        return next((x for x in self.attributes if x.name == name), None)

    @noapidoc
    @reader
    @override
    def resolve_attribute(self, name: str) -> TAttribute | None:
        return self.get_attribute(name)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        return super().descendant_symbols + self.value.descendant_symbols
