from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.has_name import HasName

Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Value(Expression[Parent], Generic[Parent]):
    """Editable attribute on code objects that has a value.

    For example, Functions, Classes, Assignments, Interfaces, Expressions, Arguments and Parameters all have values.

    See also HasValue.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx.parser.log_unparsed(self.ts_node)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None):
        for node in self.children:
            node._compute_dependencies(usage_type, dest=dest)
