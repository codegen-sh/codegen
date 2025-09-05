from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@ts_apidoc
class TSReturnTypePlaceholder(Placeholder[Parent], Generic[Parent]):
    """A placeholder class for function return type annotations in TypeScript.

    This class represents a placeholder for function return type annotations, allowing for modification
    and addition of return type annotations after the parameter list. It provides functionality to
    add or modify return type annotations with proper formatting.
    """

    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Modifies the return type annotation of a function.

        Adds or modifies the return type annotation of a function after its parameter list.

        Args:
            new_src (str): The return type annotation to add. If it doesn't start with ':', a ':' will be prepended.
            fix_indentation (bool, optional): Whether to fix the indentation of the added code. Defaults to False.
            priority (int, optional): The priority of this edit. Defaults to 0.
            dedupe (bool, optional): Whether to remove duplicate edits. Defaults to True.

        Returns:
            None

        Note:
            If new_src is empty or None, the method returns without making any changes.
        """
        if new_src == "" or new_src is None:
            return
        if not new_src.startswith(": "):
            new_src = ": " + new_src

        param_node = self._parent_node.child_by_field_name("parameters")
        param_node.insert_after(new_src, newline=False)
