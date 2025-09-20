from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, IntFlag, auto, unique
from typing import TYPE_CHECKING

from dataclasses_json import dataclass_json

from codegen.sdk.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.expressions import Name
    from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol


@apidoc
@dataclass_json
@dataclass(frozen=True)
class Usage:
    """A reference to an exportable object in a file.

    Attributes:
        match: The exact match of the usage
        usage_symbol: The symbol this object is used in
        imported_by: The import statement that brought this symbol into scope, or None if not imported
        usage_type: How this symbol was used
        kind: Where this symbol was used (IE: in a type parameter or in the body of the class, etc)
    """

    match: Name | ChainedAttribute | FunctionCall
    usage_symbol: Import | Symbol | Export | SourceFile
    imported_by: Import | None
    usage_type: UsageType
    kind: UsageKind


@unique
@apidoc
class UsageType(IntFlag):
    """Describes how a symbol is used elsewhere. Used in conjunction with get_usages

    Attributes:
        DIRECT: Direct imports and usages within the same file
        CHAINED: Chained references (ie: module.foo)
        INDIRECT:  Indirect usages with the same name
        ALIASED: Aliased indirect usages
    """

    DIRECT = auto()
    CHAINED = auto()
    INDIRECT = auto()
    ALIASED = auto()


@apidoc
class UsageKind(IntEnum):
    """SymbolUsageType is an enumeration class that defines different types of symbol usage within Python code.

    Attributes:
        SUBCLASS: Used in symbol inheritance.
        TYPED_PARAMETER: Used as a typed parameter in a function/method.
        TYPE_ANNOTATION: Used as a type annotation on a parameter or assignment statement.
        BODY: Usage within the body of a function/method.
        DECORATOR: Usage within a decorator.
        RETURN_TYPE: Used as a return type annotation.
        TYPE_DEFINITION: Used in a type alias.
        EXPORTED_SYMBOL: Used in an export statement.
        EXPORTED_WILDCARD: Re-exported by a wildcard export.
        GENERIC: Used as a type parameter to another type.
        IMPORTED: Imported with an import statement.
        IMPORTED_WILDCARD: Imported with a wildcard import statement.
        DEFAULT_VALUE: Represents a default value in a function/method parameter.
    """

    SUBCLASS = auto()
    TYPED_PARAMETER = auto()
    TYPE_ANNOTATION = auto()
    BODY = auto()
    DECORATOR = auto()
    RETURN_TYPE = auto()
    TYPE_DEFINITION = auto()
    EXPORTED_SYMBOL = auto()
    EXPORTED_WILDCARD = auto()
    GENERIC = auto()
    IMPORTED = auto()
    IMPORTED_WILDCARD = auto()
    DEFAULT_VALUE = auto()
