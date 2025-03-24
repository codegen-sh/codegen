"""Code smell definitions for the code smell detector and refactorer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Generic, TypeVar

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol import Symbol


class CodeSmellSeverity(Enum):
    """Severity levels for code smells."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class CodeSmellCategory(Enum):
    """Categories of code smells."""

    BLOATERS = auto()  # Code, methods, classes that have grown too large
    OBJECT_ORIENTATION_ABUSERS = auto()  # Cases where code doesn't follow OO principles
    CHANGE_PREVENTERS = auto()  # Things that make changing code difficult
    DISPENSABLES = auto()  # Code that isn't necessary and can be removed
    COUPLERS = auto()  # Excessive coupling between classes/modules


T = TypeVar("T", bound=Symbol)


@dataclass
class CodeSmell(Generic[T], ABC):
    """Base class for all code smells."""

    symbol: T
    severity: CodeSmellSeverity
    category: CodeSmellCategory
    description: str = ""
    refactoring_suggestions: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Get the name of the code smell."""
        return self.__class__.__name__

    @abstractmethod
    def can_auto_refactor(self) -> bool:
        """Check if this code smell can be automatically refactored."""
        pass

    def __str__(self) -> str:
        """String representation of the code smell."""
        return f"{self.name} ({self.severity.name}) in {self.symbol.name}: {self.description}"


@dataclass
class DuplicateCode(CodeSmell[SourceFile]):
    """Duplicate code smell - when the same code appears in multiple places."""

    duplicate_locations: list[tuple[SourceFile, int, int]] = field(default_factory=list)
    similarity_score: float = 0.0

    def can_auto_refactor(self) -> bool:
        """Check if this duplicate code can be automatically refactored."""
        return len(self.duplicate_locations) > 0 and self.similarity_score > 0.8


@dataclass
class LongFunction(CodeSmell[Function]):
    """Long function smell - when a function is too long and should be split."""

    line_count: int = 0
    complexity: int = 0

    def can_auto_refactor(self) -> bool:
        """Check if this long function can be automatically refactored."""
        # Long but simple functions are easier to refactor automatically
        return self.line_count > 50 and self.complexity < 10


@dataclass
class LongParameterList(CodeSmell[Function]):
    """Long parameter list smell - when a function has too many parameters."""

    parameter_count: int = 0

    def can_auto_refactor(self) -> bool:
        """Check if this long parameter list can be automatically refactored."""
        return self.parameter_count > 5


@dataclass
class DeadCode(CodeSmell[Symbol]):
    """Dead code smell - code that is never executed or used."""

    def can_auto_refactor(self) -> bool:
        """Check if this dead code can be automatically refactored."""
        return True  # Dead code can usually be safely removed


@dataclass
class ComplexConditional(CodeSmell[Function]):
    """Complex conditional smell - when conditionals are too complex."""

    condition_depth: int = 0
    boolean_operators: int = 0

    def can_auto_refactor(self) -> bool:
        """Check if this complex conditional can be automatically refactored."""
        return self.condition_depth <= 3  # Deep nesting is harder to auto-refactor


@dataclass
class DataClump(CodeSmell[Class]):
    """Data clump smell - when the same group of fields appears in multiple classes."""

    clumped_fields: list[str] = field(default_factory=list)
    appears_in_classes: list[Class] = field(default_factory=list)

    def can_auto_refactor(self) -> bool:
        """Check if this data clump can be automatically refactored."""
        return len(self.clumped_fields) >= 3 and len(self.appears_in_classes) >= 2
