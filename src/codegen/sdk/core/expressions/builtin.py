from collections.abc import Generator
from typing import TYPE_CHECKING, Self, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.external_module import ExternalModule


@noapidoc
class Builtin(Chainable, HasAttribute):
    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        # TODO: resolve builtin type
        yield ResolutionStack(self)

    @noapidoc
    @override
    def resolve_attribute(self, name: str) -> "ExternalModule | None":
        # HACK/TODO
        return None
        # return ExternalModule(self.ts_node, self.file_node_id, self.ctx, name)
