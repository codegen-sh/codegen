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
    unpack: Unpack[Self] | None = None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent, delimiter: str = ",", pair_type: type[Pair] = Pair) -> None:
        # TODO: handle spread_element
        super().__init__(ts_node, file_node_id, ctx, parent)
        children = [pair_type(child, file_node_id, ctx, self) for child in ts_node.named_children if child.type not in (None, "comment", "spread_element", "dictionary_splat") and not child.is_error]
        if unpack := self.child_by_field_types({"spread_element", "dictionary_splat"}):
            children.append(unpack)
            self.unpack = unpack
        if len(children) > 1:
            first_child = children[0].ts_node.end_byte - ts_node.start_byte
            second_child = children[1].ts_node.start_byte - ts_node.start_byte
            delimiter = ts_node.text[first_child:second_child].decode("utf-8").rstrip()
        self._underlying = Collection(ts_node, file_node_id, ctx, parent, delimiter=delimiter, children=children)

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(list(elem for elem in self._underlying if isinstance(elem, Pair)))

    def __iter__(self) -> Iterator[str]:
        for pair in self._underlying:
            if isinstance(pair, Pair):
                if pair.key is not None:
                    if isinstance(pair.key, String):
                        yield pair.key.content
                    else:
                        yield pair.key.source

    def __getitem__(self, __key) -> TExpression:
        for pair in self._underlying:
            if isinstance(pair, Pair):
                if isinstance(pair.key, String):
                    if pair.key.content == str(__key):
                        return pair.value
                elif pair.key is not None:
                    if pair.key.source == str(__key):
                        return pair.value
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
