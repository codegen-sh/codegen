from collections.abc import Iterator, MutableMapping
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.importable import Importable


TExpression = TypeVar("TExpression", bound="Expression")
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Pair(Editable[Parent], HasValue, Generic[TExpression, Parent]):
    """An abstract representation of a key, value pair belonging to a `Dict`.

    Attributes:
        key: The key expression of the pair, expected to be of type TExpression.
    """

    key: TExpression

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.key, self._value_node = self._get_key_value()
        if self.key is None:
            self._log_parse(f"{self} {self.ts_node} in {self.filepath} has no key")
        if self.ts_node_type != "shorthand_property_identifier" and self.value is None:
            self._log_parse(f"{self} {self.ts_node} in {self.filepath} has no value")

    def _get_key_value(self) -> tuple[Expression[Self] | None, Expression[Self] | None]:
        return self.child_by_field_name("key"), self.child_by_field_name("value")

    @property
    def name(self) -> str:
        """Returns the source text of the key expression in the pair.

        This property provides access to the textual representation of the pair's key, which is
        stored in the `key` attribute. The key is expected to be an Expression type that has
        a `source` property containing the original source code text.

        Returns:
            str: The source text of the key expression.

        Note:
            This property assumes that self.key has been properly initialized in __init__
            and has a valid `source` attribute. In cases where key initialization failed
            (key is None), accessing this property may raise an AttributeError.
        """
        return self.key.source

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.key:
            self.key._compute_dependencies(usage_type, dest)
        if self.value and self.value is not self.key:
            self.value._compute_dependencies(usage_type, dest)


TExpression = TypeVar("TExpression", bound="Expression")
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Dict(Expression[Parent], Builtin, MutableMapping[str, TExpression], Generic[TExpression, Parent]):
    """Represents a dict (object) literal the source code.

    Attributes:
        unpack: An optional unpacking element, if present.
    """

    _underlying: Collection[Pair[TExpression, Self] | Unpack[Self], Parent]
    unpacks: list[Unpack[Self]] = []  # Store all spread elements

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", pair_type: type[Pair] = Pair) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        children = []
        self.unpacks = []  # Store all spread elements

        for child in ts_node.named_children:
            if child.type in (None, "comment") or child.is_error:
                continue
            if child.type in ("spread_element", "dictionary_splat"):
                unpack = Unpack(child, file_node_id, ctx, self)
                children.append(unpack)
                self.unpacks.append(unpack)  # Keep track of all spread elements
            else:
                children.append(pair_type(child, file_node_id, ctx, self))

        if len(children) > 1:
            first_child = children[0].ts_node.end_byte - ts_node.start_byte
            second_child = children[1].ts_node.start_byte - ts_node.start_byte
            delimiter = ts_node.text[first_child:second_child].decode("utf-8").rstrip()
        self._underlying = Collection(ts_node, file_node_id, ctx, parent, delimiter=delimiter, children=children)

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(list(elem for elem in self._underlying if isinstance(elem, Pair)))

    def _get_unpacked_items(self) -> Iterator[tuple[str, TExpression]]:
        """Get key-value pairs from all unpacked dictionaries."""
        for unpack in self.unpacks:
            if isinstance(unpack.value, Dict):
                yield from unpack.value.items()

    def __iter__(self) -> Iterator[str]:
        # First yield keys from regular pairs
        for pair in self._underlying:
            if isinstance(pair, Pair):
                if pair.key is not None:
                    if isinstance(pair.key, String):
                        yield pair.key.content
                    else:
                        yield pair.key.source
        # Then yield keys from unpacked dictionaries
        for unpack in self.unpacks:
            for key, _ in self._get_unpacked_items():
                yield key

    def __getitem__(self, __key) -> TExpression:
        # First try regular pairs
        try:
            for pair in self._underlying:
                if isinstance(pair, Pair):
                    if isinstance(pair.key, String):
                        if pair.key.content == str(__key):
                            return pair.value
                    elif pair.key is not None:
                        if pair.key.source == str(__key):
                            return pair.value
            # Then try unpacked dictionaries
            for unpack in self.unpacks:
                for key, value in self._get_unpacked_items():
                    if key == str(__key):
                        return value
            raise KeyError
        except KeyError:
            msg = f"Key {__key} not found in {list(self.keys())} {self._underlying!r}"
            raise KeyError(msg)

    def __setitem__(self, __key, __value: TExpression) -> None:
        new_value = __value.source if isinstance(__value, Editable) else str(__value)
        if value := self.get(__key, None):
            value.edit(new_value)
        else:
            if not self.ctx.node_classes.int_dict_key:
                try:
                    int(__key)
                    __key = f"'{__key}'"
                except ValueError:
                    pass
            self._underlying.append(f"{__key}: {new_value}")

    def __delitem__(self, __key) -> None:
        for idx, pair in enumerate(self._underlying):
            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        del self._underlying[idx]
                        return
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        del self._underlying[idx]
                        return
        msg = f"Key {__key} not found in {list(self.keys())} {self._underlying!r}"
        raise KeyError(msg)

    def _removed_child_commit(self):
        return self._underlying._removed_child_commit()

    def _removed_child(self):
        return self._underlying._removed_child()

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        self._underlying._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list["Importable"]:
        ret = []
        for child in self._underlying.symbols:
            if child.value:
                ret.extend(child.value.descendant_symbols)
        return ret

    @property
    def __class__(self):
        return dict

    def __repr__(self) -> str:
        """Return a string representation of the dictionary including spread elements."""
        items = []

        # Add spread elements in their original position
        for child in self._underlying:
            if isinstance(child, Unpack):
                items.append(child.source)
            else:  # Regular key-value pair
                if child.key is not None:
                    if isinstance(child.key, String):
                        key = child.key.content
                    else:
                        key = child.key.source
                    items.append(f"{key}: {child.value.source}")

        return "{" + ", ".join(items) + "}"

    def __str__(self) -> str:
        return self.__repr__()

    def _get_all_unpacks_and_keys(self, seen_unpacks: set, seen_keys: set) -> None:
        """Recursively get all unpacks and their keys from this dictionary and its dependencies.

        Args:
            seen_unpacks: Set to store all found unpacks
            seen_keys: Set to store all keys from unpacked dictionaries
        """
        for child in self._underlying:
            if isinstance(child, Unpack):
                # Get the name being unpacked (e.g., "base1" from "**base1")
                unpack_name = child.source.strip("*")
                seen_unpacks.add(unpack_name)

                unpacked_dict = self.file.get_symbol(unpack_name).value
                if isinstance(unpacked_dict, Dict):
                    # Add all keys from this dict
                    for unpacked_child in unpacked_dict._underlying:
                        if not isinstance(unpacked_child, Unpack) and unpacked_child.key is not None:
                            seen_keys.add(unpacked_child.key.source)
                    # Recursively check its unpacks
                    unpacked_dict._get_all_unpacks_and_keys(seen_unpacks, seen_keys)

    def merge(self, *others: "Dict[TExpression, Parent] | str") -> None:
        """Merge multiple dictionaries into a new dictionary

        Preserves spread operators and function calls in their original form.
        Later dictionaries take precedence over earlier ones for duplicate keys.

        Args:
            *others: Other Dict objects or dictionary strings.
                    The strings can be either Python dicts (e.g. "{'x': 1}")
                    or TypeScript objects (e.g. "{x: 1}")

        Raises:
            ValueError: If attempting to merge dictionaries with duplicate keys or unpacks

        Returns:
            None
        """
        # Track seen keys and unpacks to prevent duplicates
        seen_keys = set()
        seen_unpacks = set()

        # Get all unpacks and their keys from its dependencies
        self._get_all_unpacks_and_keys(seen_unpacks, seen_keys)

        # Keep track of all items in order
        merged_items = []

        # First add all items from this dictionary
        for child in self._underlying:
            if isinstance(child, Unpack):
                unpack_source = child.source
                merged_items.append(unpack_source)
            else:  # Regular key-value pair
                if child.key is not None:
                    key = child.key.source
                    if key in seen_keys:
                        msg = f"Duplicate key found: {key}"
                        raise ValueError(msg)
                    seen_keys.add(key)
                    merged_items.append(f"{key}: {child.value.source}")

        # Add items from other dictionaries
        for other in others:
            if isinstance(other, Dict):
                # Handle Dict objects from our SDK
                for child in other._underlying:
                    if isinstance(child, Unpack):
                        unpack_source = child.source
                        # Get the name being unpacked (e.g., "base1" from "**base1")
                        unpack_name = unpack_source.strip("*")
                        if unpack_name in seen_unpacks:
                            msg = f"Duplicate unpack found: {unpack_source}"
                            raise ValueError(msg)
                        seen_unpacks.add(unpack_name)
                        merged_items.append(unpack_source)
                    else:  # Regular key-value pair
                        if child.key is not None:
                            key = child.key.source
                            if key in seen_keys:
                                msg = f"Duplicate key found: {key}"
                                raise ValueError(msg)
                            seen_keys.add(key)
                            merged_items.append(f"{key}: {child.value.source}")
            elif isinstance(other, str):
                # Handle dictionary string
                # Strip curly braces and whitespace
                content = other.strip().strip("{}").strip()
                if not content:  # Skip empty dicts
                    continue

                # Parse the content to check for duplicates
                parts = content.split(",")
                for part in parts:
                    part = part.strip()
                    if part.startswith("**"):
                        # Get the name being unpacked (e.g., "base1" from "**base1")
                        unpack_name = part.strip("*").strip()  # Fix unpack name extraction
                        if unpack_name in seen_unpacks:
                            msg = f"Duplicate unpack found: {part}"
                            raise ValueError(msg)

                        unpacked_dict = self.file.get_symbol(unpack_name).value
                        if isinstance(unpacked_dict, Dict):
                            # Add all keys from this dict
                            for unpacked_child in unpacked_dict._underlying:
                                if not isinstance(unpacked_child, Unpack) and unpacked_child.key is not None:
                                    if unpacked_child.key.source in seen_keys:
                                        msg = f"Duplicate key found: {unpacked_child.key.source}"
                                        raise ValueError(msg)

                        seen_unpacks.add(unpack_name)
                        merged_items.append(part)
                    else:
                        # It's a key-value pair
                        key = part.split(":")[0].strip()
                        if key in seen_keys:
                            msg = f"Duplicate key found: {key}"
                            raise ValueError(msg)
                        seen_keys.add(key)
                        merged_items.append(part)
            else:
                msg = f"Cannot merge with object of type {type(other)}"
                raise TypeError(msg)

        # Create merged source
        merged_source = "{" + ", ".join(merged_items) + "}"

        # Replace this dict's source with merged source
        self.edit(merged_source)

    def add(self, typescript_dict: str) -> None:
        """Add a TypeScript dictionary string to this dictionary

        Args:
            typescript_dict: A TypeScript dictionary string e.g. "{a: 1, b: 2}"

        Returns:
            None
        """
        # Get current items
        merged_items = []

        # Add all items from this dictionary first
        for child in self._underlying:
            if isinstance(child, Unpack):
                merged_items.append(child.source)
            elif child.key is not None:
                merged_items.append(f"{child.key.source}: {child.value.source}")

        # Add the TypeScript dictionary content
        typescript_dict = typescript_dict.strip().strip("{}").strip()
        if typescript_dict:  # Only add if not empty
            merged_items.append(typescript_dict)

        # Create merged source
        merged_source = "{" + ", ".join(merged_items) + "}"

        # Replace this dict's source with merged source
        self.edit(merged_source)

    def unwrap(self) -> None:
        """Unwrap all spread elements in this dictionary.

        This will replace all spread elements with their actual key-value pairs.
        For example:
            {'a': 1, ...dict2, 'b': 2} -> {'a': 1, 'c': 3, 'd': 4, 'b': 2}

        Returns:
            None
        """
        # Process all spread elements
        for unpack in list(self.unpacks):  # Make a copy since we'll modify during iteration
            unpack.unwrap()
