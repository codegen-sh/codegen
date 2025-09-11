from collections.abc import Generator
from typing import Generic, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.compiled.autocommit import reader
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.shared.decorators.docs import noapidoc, ts_apidoc

Parent = TypeVar("Parent")


@ts_apidoc
class TSUndefinedType(Type[Parent], Generic[Parent]):
    """Undefined type. Represents the undefined keyword
    Examples:
        undefined
    """

    @noapidoc
    def _compute_dependencies(self, usage_type: UsageKind, dest: Importable):
        pass

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        yield from []
