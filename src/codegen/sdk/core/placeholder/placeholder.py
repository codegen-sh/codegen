from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from codegen.sdk.core.autocommit import repr_func
from codegen.sdk.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable


Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Placeholder(ABC, Generic[Parent]):
    """A placeholder for a node that does not exist yet.

    Use bool checks (ie is node) to check if the node exists. You can call edit to replace the
    placeholder with a real node and it will automatically insert formatting.
    """

    _parent_node: Parent

    def __init__(self, parent: Parent) -> None:
        self._parent_node = parent

    def __bool__(self) -> Literal[False]:
        return False

    def __str__(self) -> str:
        return self.__repr__()

    @repr_func
    def __repr__(self) -> str:
        """Represents the object as a string for logging purposes.

        Returns:
            str: The class name of the object.
        """
        return f"{self.__class__.__name__}"

    def remove(self, *args, **kwargs) -> None:
        """Removes this element from its parent container.

        Args:
            *args: Variable length argument list. Unused.
            **kwargs: Arbitrary keyword arguments. Unused.

        Returns:
            None
        """
        pass

    @abstractmethod
    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Replaces the content of a placeholder node with new source code.

        Modifies the parent node to include the new source code. Can optionally fix
        indentation and handle deduplication.

        Args:
            new_src (str): The new source code to replace the placeholder with.
            fix_indentation (bool, optional): Whether to automatically fix the
                indentation of the new source. Defaults to False.
            priority (int, optional): Priority value for conflict resolution.
                Defaults to 0.
            dedupe (bool, optional): Whether to prevent duplicate insertions.
                Defaults to True.

        Returns:
            None
        """
        pass
