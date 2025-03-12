from typing import Generic, TypeVar, override

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

Parent = TypeVar("Parent", bound="Expression")


@apidoc
class Boolean(Expression[Parent], Builtin, Generic[Parent]):
    """A boolean value eg.

    True, False
    """

    def __bool__(self):
        return self.ts_node.type == "true"

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        pass

    @property
    def __class__(self):
        return bool
