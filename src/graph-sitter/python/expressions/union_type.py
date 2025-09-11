from typing import Generic, TypeVar

from codegen.sdk.core.expressions.union_type import UnionType
from codegen.sdk.shared.decorators.docs import py_apidoc

Parent = TypeVar("Parent")


@py_apidoc
class PyUnionType(UnionType["PyType", Parent], Generic[Parent]):
    """Union type

    Examples:
        str | int
    """

    pass
