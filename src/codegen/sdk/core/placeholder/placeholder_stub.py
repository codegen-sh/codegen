from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.interfaces.editable import Editable

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class StubPlaceholder(Placeholder[Parent], Generic[Parent]):
    """A placeholder for a stub that does not exist.
    Can be populated using the `edit` method.
    """

    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Edits the source code of this placeholder node.

        Modifies the source code with the provided new source code.

        Args:
            new_src (str): The new source code to replace the current source code.
            fix_indentation (bool, optional): Whether to automatically fix the indentation of the new source code. Defaults to False.
            priority (int, optional): The priority of this edit operation. Higher priority edits are applied first. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate this edit against other pending edits. Defaults to True.

        Returns:
            None
        """
        raise NotImplementedError
