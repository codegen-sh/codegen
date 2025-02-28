from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, Protocol, Self, TypeVar

from rich.console import Console

from codegen.sdk.core.expressions.placeholder_type import PlaceholderType
from codegen.sdk.core.expressions.value import Value
from codegen.sdk.core.statements.symbol_statement import SymbolStatement
from codegen.sdk.utils import find_first_function_descendant, find_import_node

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.node_classes.node_classes import NodeClasses
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


Parent = TypeVar("Parent", bound="Editable")


class CanParse(Protocol, Generic[Parent]):
    def __init__(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None: ...


Expression = TypeVar("Expression", bound="CanParse")
Parent = TypeVar("Parent", bound="Editable")


@dataclass
class Parser(Generic[Expression]):
    symbol_map: dict[str, type[Symbol]]
    expressions: dict[str, type[Expression]]
    types: dict[str, type[Type] | dict[str, type[Type]]]
    type_node: str
    _uncovered_nodes: set[str] = field(default_factory=set)
    _should_log: bool = False
    _console: Console = field(default_factory=lambda: Console())

    def _process_type(self, expr_type: type[Type] | dict[str, type[Type]], node: TSNode) -> tuple[type[Type], TSNode]:
        if isinstance(expr_type, dict):
            for child in node.named_children:
                if v := expr_type.get(child.type, None):
                    return v, child
            if node.type not in self._uncovered_nodes:
                self.log(f"Cannot handle nested type {node.type}, {expr_type}, {node.named_children}")
                self._uncovered_nodes.add(node.type)
            return PlaceholderType, node
        return expr_type, node

    @classmethod
    def from_node_classes(cls, node_classes: NodeClasses, log_parse_warnings: bool = False) -> Self:
        return cls(symbol_map=node_classes.symbol_map, expressions=node_classes.expression_map, types=node_classes.type_map, type_node=node_classes.type_node_type, _should_log=log_parse_warnings)

    def parse_expression(self, node: TSNode | None, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, *args, default: type[Expression] = Value, **kwargs) -> Expression[Parent] | None:
        if node is None:
            return None
        if node.type == self.type_node:
            return self.parse_type(node, file_node_id, ctx, parent)
        assert default is not None
        if default == Value:
            if previous := parent.file._range_index.get_canonical_for_range(node.range, node.kind_id):
                return previous
        if symbol_cls := self.symbol_map.get(node.type, None):
            ret = symbol_cls(node, file_node_id, ctx, parent, *args, **kwargs)
        else:
            expr_type = self.expressions.get(node.type, default)
            ret = expr_type(node, file_node_id, ctx, parent)
        if default == Value:
            ret.file._range_index.mark_as_canonical(ret)
            if isinstance(ret, Value):
                ret.children
        return ret

    def log_unparsed(self, node: TSNode) -> None:
        if self._should_log and node.is_named and node.type not in self._uncovered_nodes:
            self._uncovered_nodes.add(node.type)
            self.log(f"Encountered unimplemented node {node.type} with text {node.text.decode('utf-8')}")

    def parse_type(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> Type:
        if node.type == self.type_node:
            return self.parse_type(node.named_children[0], file_node_id, ctx, parent)
        if expr_type := self.types.get(node.type, None):
            expr_type, node = self._process_type(expr_type, node)
            return expr_type(node, file_node_id, ctx, parent)
        self.log_unparsed(node)
        from codegen.sdk.core.expressions.placeholder_type import PlaceholderType

        return PlaceholderType(node, file_node_id, ctx, parent)

    def parse_ts_statements(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock) -> list[Statement]:
        from codegen.sdk.core.statements.export_statement import ExportStatement
        from codegen.sdk.core.statements.expression_statement import ExpressionStatement
        from codegen.sdk.core.statements.return_statement import ReturnStatement
        from codegen.sdk.core.statements.statement import Statement
        from codegen.sdk.core.statements.symbol_statement import SymbolStatement
        from codegen.sdk.typescript.function import _VALID_TYPE_NAMES
        from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
        from codegen.sdk.typescript.statements.attribute import TSAttribute
        from codegen.sdk.typescript.statements.comment import TSComment
        from codegen.sdk.typescript.statements.for_loop_statement import TSForLoopStatement
        from codegen.sdk.typescript.statements.if_block_statement import TSIfBlockStatement
        from codegen.sdk.typescript.statements.import_statement import TSImportStatement
        from codegen.sdk.typescript.statements.labeled_statement import TSLabeledStatement
        from codegen.sdk.typescript.statements.switch_statement import TSSwitchStatement
        from codegen.sdk.typescript.statements.try_catch_statement import TSTryCatchStatement
        from codegen.sdk.typescript.statements.while_statement import TSWhileStatement

        statements = []

        if node.type in self.expressions or node.type == "expression_statement":
            return [ExpressionStatement(node, file_node_id, ctx, parent, 0, expression_node=node)]

        for child in node.named_children:
            # =====[ Functions + Methods ]=====
            if child.type in _VALID_TYPE_NAMES:
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))
            elif child.type == "import_statement":
                statements.append(TSImportStatement(child, file_node_id, ctx, parent, len(statements)))
            # =====[ Classes ]=====
            elif child.type in ("class_declaration", "abstract_class_declaration"):
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Interface Declarations ]=====
            elif child.type == "interface_declaration":
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Type Alias Declarations ]=====
            elif child.type == "type_alias_declaration":
                if import_node := find_import_node(child):
                    statements.append(TSImportStatement(child, file_node_id, ctx, parent, len(statements), source_node=import_node))
                else:
                    statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Enum Declarations ]=====
            elif child.type == "enum_declaration":
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Exports ]=====
            elif child.type == "export_statement" or child.text.decode("utf-8") == "export *;":
                statements.append(ExportStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Non-symbol statements ] =====
            elif child.type == "comment":
                statements.append(TSComment.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "return_statement":
                statements.append(ReturnStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "if_statement":
                statements.append(TSIfBlockStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type in ["while_statement", "do_statement"]:
                statements.append(TSWhileStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type in ["for_statement", "for_in_statement"]:
                statements.append(TSForLoopStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "try_statement":
                statements.append(TSTryCatchStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "switch_statement":
                statements.append(TSSwitchStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "labeled_statement":
                statements.append(TSLabeledStatement(child, file_node_id, ctx, parent, len(statements)))
            elif child.type in ["lexical_declaration", "variable_declaration"]:
                if function_node := find_first_function_descendant(child):
                    statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements), function_node))
                elif import_node := find_import_node(child):
                    statements.append(TSImportStatement(child, file_node_id, ctx, parent, len(statements), source_node=import_node))
                else:
                    statements.append(
                        TSAssignmentStatement.from_assignment(
                            child, file_node_id, ctx, parent, pos=len(statements), assignment_node=next(var for var in child.named_children if var.type == "variable_declarator")
                        )
                    )
            elif child.type in ["public_field_definition", "property_signature", "enum_assignment"]:
                statements.append(TSAttribute(child, file_node_id, ctx, parent, pos=len(statements)))
            elif child.type == "expression_statement":
                if import_node := find_import_node(child):
                    statements.append(TSImportStatement(child, file_node_id, ctx, parent, pos=len(statements), source_node=import_node))
                    continue

                for var in child.named_children:
                    if var.type == "string":
                        statements.append(TSComment.from_code_block(var, parent, pos=len(statements)))
                    elif var.type in ["assignment_expression", "augmented_assignment_expression"]:
                        statements.append(TSAssignmentStatement.from_assignment(child, file_node_id, ctx, parent, pos=len(statements), assignment_node=var))
                    else:
                        statements.append(ExpressionStatement(child, file_node_id, ctx, parent, pos=len(statements), expression_node=var))
            elif child.type in self.expressions:
                statements.append(ExpressionStatement(child, file_node_id, ctx, parent, len(statements), expression_node=child))
            else:
                self.log("Couldn't parse statement with type: %s", child.type)
                statements.append(Statement.from_code_block(child, parent, pos=len(statements)))
                statements[-1].nested_code_blocks

        return statements

    def parse_py_statements(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: PyCodeBlock) -> list[Statement]:
        from codegen.sdk.core.statements.expression_statement import ExpressionStatement
        from codegen.sdk.core.statements.raise_statement import RaiseStatement
        from codegen.sdk.core.statements.return_statement import ReturnStatement
        from codegen.sdk.core.statements.statement import Statement
        from codegen.sdk.python.statements.assignment_statement import PyAssignmentStatement
        from codegen.sdk.python.statements.attribute import PyAttribute
        from codegen.sdk.python.statements.break_statement import PyBreakStatement
        from codegen.sdk.python.statements.comment import PyComment
        from codegen.sdk.python.statements.for_loop_statement import PyForLoopStatement
        from codegen.sdk.python.statements.if_block_statement import PyIfBlockStatement
        from codegen.sdk.python.statements.import_statement import PyImportStatement
        from codegen.sdk.python.statements.match_statement import PyMatchStatement
        from codegen.sdk.python.statements.pass_statement import PyPassStatement
        from codegen.sdk.python.statements.try_catch_statement import PyTryCatchStatement
        from codegen.sdk.python.statements.while_statement import PyWhileStatement
        from codegen.sdk.python.statements.with_statement import WithStatement

        statements = []

        # Handles a Tree sitter anomaly where comments in the block are not included in the block node
        prev_sibling = node.prev_sibling
        top_comments = []
        while prev_sibling and prev_sibling.type == "comment":
            top_comments.insert(0, prev_sibling)
            prev_sibling = prev_sibling.prev_sibling

        for comment in top_comments:
            statements.append(PyComment.from_code_block(comment, parent, pos=len(statements)))

        for child in node.named_children:
            # =====[ Decorated definitions ]=====
            if child.type == "decorated_definition":
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Functions ]=====
            elif child.type == "function_definition":
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Classes ]=====
            elif child.type == "class_definition":
                statements.append(SymbolStatement(child, file_node_id, ctx, parent, len(statements)))

            # =====[ Imports ] =====
            elif child.type in ["import_statement", "import_from_statement", "future_import_statement"]:
                statements.append(PyImportStatement(child, file_node_id, ctx, parent, len(statements)))
            # =====[ Non-symbol statements ] =====
            elif child.type == "comment":
                statements.append(PyComment.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "raise_statement":
                statements.append(RaiseStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "return_statement":
                statements.append(ReturnStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "if_statement":
                statements.append(PyIfBlockStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "with_statement":
                statements.append(WithStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "pass_statement":
                statements.append(PyPassStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "break_statement":
                statements.append(PyBreakStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "while_statement":
                statements.append(PyWhileStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "for_statement":
                statements.append(PyForLoopStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "match_statement":
                statements.append(PyMatchStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "try_statement":
                statements.append(PyTryCatchStatement.from_code_block(child, parent, pos=len(statements)))
            elif child.type == "expression_statement":
                for var in child.named_children:
                    if var.type == "string":
                        statements.append(PyComment.from_code_block(var, parent, pos=len(statements)))
                    elif var.type in ["assignment", "augmented_assignment"]:
                        from codegen.sdk.core.class_definition import Class

                        if isinstance(parent.parent, Class):
                            statements.append(PyAttribute(child, file_node_id, ctx, parent, len(statements), var))
                        else:
                            statements.append(PyAssignmentStatement.from_assignment(child, file_node_id, ctx, parent, pos=len(statements), assignment_node=var))
                    else:
                        statements.append(ExpressionStatement(child, file_node_id, ctx, parent, pos=len(statements), expression_node=var))
            else:
                self.log("Couldn't parse statement with type: %s", node.type)
                statements.append(Statement.from_code_block(child, parent, pos=len(statements)))
                statements[-1].nested_code_blocks
        return statements

    def report(self):
        if self._uncovered_nodes:
            self._console.print(f"Encountered unimplemented nodes {self._uncovered_nodes}")

    def log(self, message: str, *args):
        if self._should_log:
            try:
                self._console.log(message % args)
            except (KeyError, IndexError, ValueError, TypeError):
                self._console.log(message, *args)
                pass
