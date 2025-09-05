from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.shared.decorators.docs import py_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@py_apidoc
class PyReturnTypePlaceholder(Placeholder[Parent], Generic[Parent]):
    """A placeholder for a python return type that does not exist.
    Can be populated using the `edit` method.
    """

    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Edits or creates a return type annotation for a method or function.

        Used to modify or create a return type annotation in Python functions and methods. If the new source is not empty,
        it will be appended after the parameters with the ' -> ' prefix.

        Args:
            new_src (str): The new return type annotation text to be added.
            fix_indentation (bool, optional): Whether to fix the indentation of the new source. Defaults to False.
            priority (int, optional): Priority of the edit operation. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate the edit operation. Defaults to True.

        Returns:
            None
        """
        new_src = new_src.removeprefix(" -> ")
        # Case: return type node DOES NOT exist and new_return_type is not empty, append return type
        if new_src:
            new_return_type = " -> " + new_src  # Add -> prefix b/c it will be missing if return type node does not exist
            param_node = self._parent_node.child_by_field_name("parameters")
            param_node.insert_after(new_return_type, newline=False)
