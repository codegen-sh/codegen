from typing import Generic, TypeVar, override

from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

Parent = TypeVar("Parent", bound="Expression")


@apidoc
class Number(Expression[Parent], Builtin, Generic[Parent]):
    """A number value.

    eg. 1, 2.0, 3.14
    """

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        pass

    @property
    def __class__(self):
        return int
