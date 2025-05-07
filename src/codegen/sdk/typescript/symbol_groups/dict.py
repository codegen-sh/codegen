from typing import TYPE_CHECKING, Self, TypeVar, override

from tree_sitter import Node as TSNode

from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.dict import Dict, Pair
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc, noapidoc, ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext

Parent = TypeVar("Parent", bound="Editable")
TExpression = TypeVar("TExpression", bound=Expression)

logger = get_logger(__name__)


@ts_apidoc
class TSPair(Pair):
    """A TypeScript pair node that represents key-value pairs in object literals.

    A specialized class extending `Pair` for handling TypeScript key-value pairs,
    particularly in object literals. It provides functionality for handling both
    regular key-value pairs and shorthand property identifiers, with support for
    reducing boolean conditions.

    Attributes:
        shorthand (bool): Indicates whether this pair uses shorthand property syntax.
    """

    shorthand: bool

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.shorthand = ts_node.type == "shorthand_property_identifier"

    def _get_key_value(self) -> tuple[Expression[Self] | None, Expression[Self] | None]:
        from codegen.sdk.typescript.function import TSFunction

        key, value = None, None

        if self.ts_node.type == "pair":
            key = self.child_by_field_name("key")
            value = self.child_by_field_name("value")
            if TSFunction.is_valid_node(value.ts_node):
                value = self._parse_expression(value.ts_node)
        elif self.ts_node.type == "shorthand_property_identifier":
            key = value = self._parse_expression(self.ts_node)
        elif TSFunction.is_valid_node(self.ts_node):
            value = self._parse_expression(self.ts_node)
            key = value.get_name()
        else:
            return super()._get_key_value()
        return key, value

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Reduces an editable to the following condition"""
        if self.shorthand and node == self.value:
            # Object shorthand
            self.parent[self.key.source] = self.ctx.node_classes.bool_conversion[bool_condition]
        else:
            super().reduce_condition(bool_condition, node)


@apidoc
class TSDict(Dict[Expression, Parent]):
    """A typescript dict object. You can use standard operations to operate on this dict (IE len, del, set, get, etc)"""

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", pair_type: type[Pair] = TSPair) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, delimiter=delimiter, pair_type=pair_type)

    def __getitem__(self, __key: str) -> Expression:
        for pair in self._underlying:
            pair_match = None

            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        pair_match = pair
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        pair_match = pair

                if pair_match:
                    if pair_match.value is not None:
                        return pair_match.value
                    else:
                        return pair_match.key
        msg = f"Key {__key} not found in {list(self.keys())} {self._underlying!r}"
        raise KeyError(msg)

    def __setitem__(self, __key: str, __value: TExpression) -> None:
        new_value = __value.source if isinstance(__value, Editable) else str(__value)
        for pair in self._underlying:
            pair_match = None

            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        pair_match = pair
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        pair_match = pair

                if pair_match:
                    # CASE: {a: b}
                    if not pair_match.shorthand:
                        if __key == new_value:
                            pair_match.edit(f"{__key}")
                        else:
                            pair_match.value.edit(f"{new_value}")
                    # CASE: {a}
                    else:
                        if __key == new_value:
                            pair_match.edit(f"{__key}")
                        else:
                            pair_match.edit(f"{__key}: {new_value}")
                    break
        # CASE: {}
        else:
            if not self.ctx.node_classes.int_dict_key:
                try:
                    int(__key)
                    __key = f"'{__key}'"
                except ValueError:
                    pass
            if __key == new_value:
                self._underlying.append(f"{__key}")
            else:
                self._underlying.append(f"{__key}: {new_value}")

    @reader
    @noapidoc
    @override
    def resolve_attribute(self, name: str) -> "Expression | None":
        return self.get(name, None)

    def merge(self, *others: "Dict[Expression, Parent] | str") -> None:
        """Merge multiple dictionaries into a new dictionary.

        Preserves spread operators and function calls in their original form.
        Later dictionaries take precedence over earlier ones for duplicate keys.
        In TypeScript, duplicate keys and spreads are allowed - later ones override earlier ones.

        Args:
            *others: Other Dict objects or dictionary strings.
                    The strings can be either Python dicts (e.g. "{'x': 1}")
                    or TypeScript objects (e.g. "{x: 1}")

        Returns:
            None
        """
        # Keep track of all items in order
        merged_items = []

        # First add all items from this dictionary
        for child in self._underlying:
            if isinstance(child, Unpack):
                merged_items.append(child.source)
            elif child.key is not None:
                merged_items.append(f"{child.key.source}: {child.value.source}")

        # Then add items from other dictionaries
        for other in others:
            if isinstance(other, Dict):
                # Handle Dict objects from our SDK
                for child in other._underlying:
                    if isinstance(child, Unpack):
                        merged_items.append(child.source)
                    elif child.key is not None:
                        merged_items.append(f"{child.key.source}: {child.value.source}")
            elif isinstance(other, str):
                # Handle dictionary string
                content = other.strip().strip("{}").strip()
                if not content:  # Skip empty dicts
                    continue

                # Parse the content
                parts = content.split(",")
                for part in parts:
                    part = part.strip()
                    merged_items.append(part)
            else:
                msg = f"Cannot merge with object of type {type(other)}"
                raise TypeError(msg)

        # Create merged source
        merged_source = "{" + ", ".join(merged_items) + "}"

        # Replace this dict's source with merged source
        self.edit(merged_source)
