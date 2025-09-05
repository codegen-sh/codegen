from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.shared.decorators.docs import apidoc


@apidoc
class HasValue:
    """An interface for any node object that has a value."""

    _value_node: Expression | None

    @property
    @reader
    def value(self) -> Expression | None:
        """Gets the value node of the object.

        Returns:
            Expression | None: The value node of the object. None if no value is set.
        """
        return self._value_node

    @writer
    def set_value(self, value: str) -> None:
        """Sets the value of the node's value Expression.

        Updates the value of the underlying Expression node if it exists. No action is taken if the value node is None.

        Args:
            value (str): The new value to set.

        Returns:
            None
        """
        if self._value_node is not None:
            self._value_node.edit(value)
