from collections import defaultdict
from dataclasses import dataclass, field
from typing import Generic, TypeVar

from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.function import Function

TFunction = TypeVar("TFunction", bound=Function)


@dataclass
class MultiGraph(Generic[TFunction]):
    """Mapping of API endpoints to their definitions and usages across languages."""

    api_definitions: dict[str, TFunction] = field(default_factory=dict)
    usages: defaultdict[str, list[FunctionCall]] = field(default_factory=lambda: defaultdict(list))
