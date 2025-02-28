from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.statements.import_statement import ImportStatement
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.file import TSFile


@ts_apidoc
class TSImportStatement(ImportStatement["TSFile", TSImport, "TSCodeBlock"], Builtin):
    """A class representing an import statement in TypeScript, managing both static and dynamic imports.

    This class handles various types of TypeScript imports including regular import statements,
    dynamic imports, and export statements. It provides functionality to manage and track imports
    within a TypeScript file, enabling operations like analyzing dependencies, moving imports,
    and modifying import statements.

    Attributes:
        imports (Collection): A collection of TypeScript imports contained within the statement.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int, *, source_node: TSNode | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos)
        imports = []
        if ts_node.type == "import_statement":
            imports.extend(TSImport.from_import_statement(ts_node, file_node_id, ctx, self))
        elif ts_node.type in ["call_expression", "lexical_declaration", "expression_statement", "type_alias_declaration"]:
            import_call_node = source_node.child_by_field_name("function")
            arguments = source_node.child_by_field_name("arguments")
            imports.extend(TSImport.from_dynamic_import_statement(import_call_node, arguments, file_node_id, ctx, self))
        elif ts_node.type == "export_statement":
            imports.extend(TSImport.from_export_statement(source_node, file_node_id, ctx, self))
        self.imports = Collection(ts_node, file_node_id, ctx, self, delimiter="\n", children=imports)
        for imp in self.imports:
            imp.import_statement = self
