from codegen.sdk.codebase.node_classes.node_classes import NodeClasses
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.file import File
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.statements.comment import Comment

GenericNodeClasses = NodeClasses(
    file_cls=File,
    class_cls=Class,
    function_cls=Function,
    import_cls=Import,
    parameter_cls=Parameter,
    comment_cls=Comment,
    code_block_cls=CodeBlock,
    function_call_cls=FunctionCall,
    bool_conversion={},
    dynamic_import_parent_types={},
)
