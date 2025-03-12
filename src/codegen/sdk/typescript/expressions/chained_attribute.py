from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Expression, Name
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@ts_apidoc
class TSChainedAttribute(ChainedAttribute[Expression, Name, Parent], Generic[Parent]):
    """A TypeScript chained attribute class representing member access expressions.

    This class handles the representation and analysis of chained attribute access expressions in TypeScript,
    such as 'object.property' or 'object.method()'. It provides functionality for accessing the object
    and property components of the expression, as well as analyzing function calls made on the object.
    """

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent=parent, object=ts_node.child_by_field_name("object"), attribute=ts_node.child_by_field_name("property"))

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of function calls associated with this chained attribute's object.

        Retrieves all function calls made on the object component of this chained attribute.
        This is useful for analyzing call sites and call patterns in code analysis and refactoring tasks.

        Returns:
            list[FunctionCall]: A list of function calls made on this chained attribute's object.
        """
        # Move the parent reference to its own parent to skip over an identifier type in parent chain
        return self._object.function_calls
