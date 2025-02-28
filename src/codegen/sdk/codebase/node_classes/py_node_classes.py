from tree_sitter import Node as TSNode

from codegen.sdk.codebase.node_classes.node_classes import NodeClasses
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import String, Type
from codegen.sdk.core.expressions.await_expression import AwaitExpression
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.expressions.none_type import NoneType
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.core.expressions.parenthesized_expression import ParenthesizedExpression
from codegen.sdk.core.expressions.subscript_expression import SubscriptExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.function import Function
from codegen.sdk.core.statements.comment import Comment
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.switch_statement import SwitchStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.core.symbol_groups.list import List
from codegen.sdk.core.symbol_groups.tuple import Tuple
from codegen.sdk.core.symbol_groups.type_parameters import TypeParameters
from codegen.sdk.python import PyClass, PyFile, PyFunction, PyImport, PySymbol
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.parameter import PyParameter
from codegen.sdk.python.expressions.chained_attribute import PyChainedAttribute
from codegen.sdk.python.expressions.conditional_expression import PyConditionalExpression
from codegen.sdk.python.expressions.generic_type import PyGenericType
from codegen.sdk.python.expressions.named_type import PyNamedType
from codegen.sdk.python.expressions.string import PyString
from codegen.sdk.python.expressions.union_type import PyUnionType
from codegen.sdk.python.statements.import_statement import PyImportStatement
from codegen.sdk.python.statements.match_case import PyMatchCase
from codegen.sdk.python.statements.with_statement import WithStatement


def parse_subscript(node: TSNode, file_node_id, ctx, parent):
    if (node.prev_named_sibling and node.prev_named_sibling.text.decode("utf-8") == "TypeAlias") or isinstance(parent, Type):
        return PyGenericType(node, file_node_id, ctx, parent)
    return SubscriptExpression(node, file_node_id, ctx, parent)


PyExpressionMap = {
    "string": PyString,
    "dictionary": Dict,
    "list": List,
    "name": Name,
    "true": Boolean,
    "false": Boolean,
    "integer": Number,
    "float": Number,
    "identifier": Name,
    "attribute": PyChainedAttribute,
    "call": FunctionCall,
    "binary_operator": BinaryExpression,
    "boolean_operator": BinaryExpression,
    "comparison_operator": ComparisonExpression,
    "string_content": String,
    "parenthesized_expression": ParenthesizedExpression,
    "await": AwaitExpression,
    "function_definition": PyFunction,
    "list_splat": Unpack,
    "dictionary_splat": Unpack,
    "tuple": Tuple,
    "conditional_expression": PyConditionalExpression,
    "not_operator": UnaryExpression,
    "subscript": parse_subscript,
    "type_parameter": TypeParameters,
    "pattern_list": List,
    # "assignment": PyAssignment.from_assignment,
    # "augmented_assignment": PyAssignment.from_assignment,
    # "named_expression": PyAssignment.from_named_expression,
}

PyStatementMap = {
    "import_statement": PyImportStatement,
    "import_from_statement": PyImportStatement,
    "future_import_statement": PyImportStatement,
}

PySymbolMap = {
    "decorated_definition": PySymbol.from_decorated_definition,
    "function_definition": PyFunction,
    "class_definition": PyClass,
}

PyNodeClasses = NodeClasses(
    file_cls=PyFile,
    class_cls=PyClass,
    function_cls=PyFunction,
    import_cls=PyImport,
    parameter_cls=PyParameter,
    comment_cls=Comment,
    code_block_cls=PyCodeBlock,
    function_call_cls=FunctionCall,
    symbol_map=PySymbolMap,
    expression_map=PyExpressionMap,
    type_map={
        "union_type": PyUnionType,
        "binary_operator": PyUnionType,
        "generic_type": PyGenericType,
        "subscript": PyGenericType,
        "none": NoneType,
        "identifier": PyNamedType,
        "attribute": PyNamedType,
        "string": PyNamedType,  # TODO: handle string types (IE postponed annotations)
    },
    keywords=["async"],
    type_node_type="type",
    int_dict_key=True,
    bool_conversion={
        True: "True",
        False: "False",
    },
    dynamic_import_parent_types={
        Function,
        IfBlockStatement,
        TryCatchStatement,
        WithStatement,
        ForLoopStatement,
        WhileStatement,
        SwitchStatement,
        PyMatchCase,
    },
)
