"""Code smell detector for Python and TypeScript codebases."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.file import File, SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.extensions.code_smells.smells import (
    CodeSmell,
    CodeSmellCategory,
    CodeSmellSeverity,
    ComplexConditional,
    DataClump,
    DeadCode,
    DuplicateCode,
    LongFunction,
    LongParameterList,
)
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class DetectionConfig:
    """Configuration for code smell detection."""

    # Thresholds for different code smells
    long_function_lines: int = 50
    long_function_complexity_threshold: int = 15
    long_parameter_list_threshold: int = 5
    duplicate_code_min_lines: int = 6
    duplicate_code_similarity_threshold: float = 0.8
    complex_conditional_depth_threshold: int = 3
    complex_conditional_operators_threshold: int = 4
    data_clump_min_fields: int = 3
    data_clump_min_classes: int = 2

    # Enable/disable specific detectors
    detect_long_functions: bool = True
    detect_long_parameter_lists: bool = True
    detect_duplicate_code: bool = True
    detect_dead_code: bool = True
    detect_complex_conditionals: bool = True
    detect_data_clumps: bool = True


class CodeSmellDetector:
    """Detector for common code smells in Python and TypeScript codebases."""

    def __init__(self, codebase: Codebase, config: Optional[DetectionConfig] = None):
        """Initialize the code smell detector.

        Args:
            codebase: The codebase to analyze
            config: Configuration for detection thresholds and enabled detectors
        """
        self.codebase = codebase
        self.config = config or DetectionConfig()
        self._smells: list[CodeSmell] = []

        # Register detection methods
        self._detectors: dict[str, Callable[[], list[CodeSmell]]] = {
            "long_functions": self._detect_long_functions,
            "long_parameter_lists": self._detect_long_parameter_lists,
            "duplicate_code": self._detect_duplicate_code,
            "dead_code": self._detect_dead_code,
            "complex_conditionals": self._detect_complex_conditionals,
            "data_clumps": self._detect_data_clumps,
        }

    def detect_all(self) -> list[CodeSmell]:
        """Run all enabled code smell detectors.

        Returns:
            A list of all detected code smells
        """
        self._smells = []

        if self.config.detect_long_functions:
            self._smells.extend(self._detect_long_functions())

        if self.config.detect_long_parameter_lists:
            self._smells.extend(self._detect_long_parameter_lists())

        if self.config.detect_duplicate_code:
            self._smells.extend(self._detect_duplicate_code())

        if self.config.detect_dead_code:
            self._smells.extend(self._detect_dead_code())

        if self.config.detect_complex_conditionals:
            self._smells.extend(self._detect_complex_conditionals())

        if self.config.detect_data_clumps:
            self._smells.extend(self._detect_data_clumps())

        return self._smells

    def detect_by_category(self, category: CodeSmellCategory) -> list[CodeSmell]:
        """Detect code smells of a specific category.

        Args:
            category: The category of code smells to detect

        Returns:
            A list of detected code smells in the specified category
        """
        all_smells = self.detect_all()
        return [smell for smell in all_smells if smell.category == category]

    def detect_by_severity(self, severity: CodeSmellSeverity) -> list[CodeSmell]:
        """Detect code smells of a specific severity.

        Args:
            severity: The severity level of code smells to detect

        Returns:
            A list of detected code smells with the specified severity
        """
        all_smells = self.detect_all()
        return [smell for smell in all_smells if smell.severity == severity]

    def detect_in_file(self, file: SourceFile) -> list[CodeSmell]:
        """Detect code smells in a specific file.

        Args:
            file: The file to analyze

        Returns:
            A list of detected code smells in the specified file
        """
        all_smells = self.detect_all()
        return [smell for smell in all_smells if (isinstance(smell.symbol, File) and smell.symbol == file) or (hasattr(smell.symbol, "file") and smell.symbol.file == file)]

    def _detect_long_functions(self) -> list[CodeSmell]:
        """Detect functions that are too long.

        Returns:
            A list of LongFunction code smells
        """
        smells = []

        for function in self.codebase.functions:
            # Skip functions without a body
            if not function.body:
                continue

            # Count lines in function body
            line_count = len(function.body.split("\n"))

            # Simple complexity metric: count if/for/while statements
            complexity = 0
            if function.body:
                # Count control flow statements as a simple complexity metric
                complexity += function.body.count("if ")
                complexity += function.body.count("for ")
                complexity += function.body.count("while ")
                complexity += function.body.count("except ")
                complexity += function.body.count("case ")

            if line_count > self.config.long_function_lines:
                severity = CodeSmellSeverity.MEDIUM
                if line_count > self.config.long_function_lines * 2:
                    severity = CodeSmellSeverity.HIGH

                smell = LongFunction(
                    symbol=function,
                    severity=severity,
                    category=CodeSmellCategory.BLOATERS,
                    description=f"Function is {line_count} lines long (threshold: {self.config.long_function_lines})",
                    line_count=line_count,
                    complexity=complexity,
                )

                # Add refactoring suggestions
                if complexity > self.config.long_function_complexity_threshold:
                    smell.refactoring_suggestions.append("Extract complex logic into smaller helper functions")
                else:
                    smell.refactoring_suggestions.append("Split function into smaller, more focused functions")

                smells.append(smell)

        return smells

    def _detect_long_parameter_lists(self) -> list[CodeSmell]:
        """Detect functions with too many parameters.

        Returns:
            A list of LongParameterList code smells
        """
        smells = []

        for function in self.codebase.functions:
            param_count = len(function.parameters)

            if param_count > self.config.long_parameter_list_threshold:
                severity = CodeSmellSeverity.MEDIUM
                if param_count > self.config.long_parameter_list_threshold + 3:
                    severity = CodeSmellSeverity.HIGH

                smell = LongParameterList(
                    symbol=function,
                    severity=severity,
                    category=CodeSmellCategory.BLOATERS,
                    description=f"Function has {param_count} parameters (threshold: {self.config.long_parameter_list_threshold})",
                    parameter_count=param_count,
                )

                # Add refactoring suggestions
                if self.codebase.language == ProgrammingLanguage.PYTHON:
                    smell.refactoring_suggestions.append("Use a dataclass or named tuple to group related parameters")
                elif self.codebase.language in (ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT):
                    smell.refactoring_suggestions.append("Use an options object pattern to group related parameters")

                smell.refactoring_suggestions.append("Consider if the function is doing too much and should be split")

                smells.append(smell)

        return smells

    def _detect_duplicate_code(self) -> list[CodeSmell]:
        """Detect duplicate code across files.

        This is a simplified implementation that looks for exact duplicates.
        A more sophisticated implementation would use techniques like:
        - Abstract syntax tree comparison
        - Normalized token sequence comparison
        - Fuzzy matching algorithms

        Returns:
            A list of DuplicateCode code smells
        """
        smells = []
        min_lines = self.config.duplicate_code_min_lines

        # Extract code blocks from all files (simplified approach)
        code_blocks = []
        for file in self.codebase.files:
            if not isinstance(file, SourceFile) or not file.content:
                continue

            lines = file.content.split("\n")
            # Extract blocks of min_lines consecutive lines
            for i in range(len(lines) - min_lines + 1):
                block = "\n".join(lines[i : i + min_lines])
                # Skip blocks that are too short or just whitespace
                if len(block.strip()) < 30:
                    continue
                code_blocks.append((file, i + 1, i + min_lines, block))

        # Find duplicates (exact matches for simplicity)
        block_map = defaultdict(list)
        for file, start, end, block in code_blocks:
            # Normalize whitespace for comparison
            normalized = re.sub(r"\s+", " ", block.strip())
            block_map[normalized].append((file, start, end))

        # Create code smell for each set of duplicates
        for normalized_block, locations in block_map.items():
            if len(locations) < 2:
                continue

            # First location is the "original"
            original_file, original_start, original_end = locations[0]
            duplicate_locations = [(loc[0], loc[1], loc[2]) for loc in locations[1:]]

            severity = CodeSmellSeverity.MEDIUM
            if len(locations) > 3:
                severity = CodeSmellSeverity.HIGH

            smell = DuplicateCode(
                symbol=original_file,
                severity=severity,
                category=CodeSmellCategory.DISPENSABLES,
                description=f"Duplicate code found in {len(locations)} locations",
                duplicate_locations=duplicate_locations,
                similarity_score=1.0,  # Exact match
            )

            # Add refactoring suggestions
            if self.codebase.language == ProgrammingLanguage.PYTHON:
                smell.refactoring_suggestions.append("Extract duplicated code into a shared function")
            elif self.codebase.language in (ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT):
                smell.refactoring_suggestions.append("Extract duplicated code into a shared utility function")

            smells.append(smell)

        return smells

    def _detect_dead_code(self) -> list[CodeSmell]:
        """Detect unused code (functions, classes, variables).

        Returns:
            A list of DeadCode code smells
        """
        smells = []

        # Find symbols that are never used
        for symbol in self.codebase._symbols():
            # Skip symbols that are likely meant to be public API
            if symbol.name.startswith("__") and symbol.name.endswith("__"):
                continue

            # Skip symbols that are imported but not defined in this codebase
            if not hasattr(symbol, "file") or not symbol.file:
                continue

            # Check if the symbol has any usages
            if not symbol.usages:
                severity = CodeSmellSeverity.LOW

                # Increase severity for larger unused code
                if isinstance(symbol, Class) or isinstance(symbol, Function):
                    if hasattr(symbol, "body") and symbol.body and len(symbol.body.split("\n")) > 20:
                        severity = CodeSmellSeverity.MEDIUM

                smell = DeadCode(
                    symbol=symbol,
                    severity=severity,
                    category=CodeSmellCategory.DISPENSABLES,
                    description=f"Unused {symbol.__class__.__name__.lower()} '{symbol.name}'",
                )

                # Add refactoring suggestions
                smell.refactoring_suggestions.append(f"Remove unused {symbol.__class__.__name__.lower()} '{symbol.name}'")

                if isinstance(symbol, Function) and symbol.is_public:
                    smell.refactoring_suggestions.append("If this is part of a public API, document it clearly or mark as deprecated")

                smells.append(smell)

        return smells

    def _detect_complex_conditionals(self) -> list[CodeSmell]:
        """Detect overly complex conditional expressions.

        Returns:
            A list of ComplexConditional code smells
        """
        smells = []

        for function in self.codebase.functions:
            if not function.body:
                continue

            # Simple heuristic for conditional complexity
            lines = function.body.split("\n")
            max_indent = 0
            current_indent = 0

            # Count boolean operators
            boolean_operators = function.body.count(" and ") + function.body.count(" or ")
            boolean_operators += function.body.count("&&") + function.body.count("||")

            # Estimate nesting depth
            for line in lines:
                stripped = line.lstrip()
                if not stripped or stripped.startswith(("#", "//", "/*", "*")):
                    continue

                indent = len(line) - len(stripped)
                current_indent = indent
                max_indent = max(max_indent, current_indent)

            # Estimate nesting depth (divide by typical indent size)
            indent_size = 4 if self.codebase.language == ProgrammingLanguage.PYTHON else 2
            nesting_depth = max_indent // indent_size

            if nesting_depth > self.config.complex_conditional_depth_threshold or boolean_operators > self.config.complex_conditional_operators_threshold:
                severity = CodeSmellSeverity.MEDIUM
                if nesting_depth > self.config.complex_conditional_depth_threshold + 2:
                    severity = CodeSmellSeverity.HIGH

                smell = ComplexConditional(
                    symbol=function,
                    severity=severity,
                    category=CodeSmellCategory.CHANGE_PREVENTERS,
                    description=f"Complex conditionals with nesting depth {nesting_depth} and {boolean_operators} boolean operators",
                    condition_depth=nesting_depth,
                    boolean_operators=boolean_operators,
                )

                # Add refactoring suggestions
                smell.refactoring_suggestions.append("Extract complex conditions into well-named predicate methods")
                smell.refactoring_suggestions.append("Consider using early returns to reduce nesting")
                if boolean_operators > self.config.complex_conditional_operators_threshold:
                    smell.refactoring_suggestions.append("Break complex boolean expressions into smaller, named variables")

                smells.append(smell)

        return smells

    def _detect_data_clumps(self) -> list[CodeSmell]:
        """Detect data clumps (same fields appearing in multiple classes).

        Returns:
            A list of DataClump code smells
        """
        smells = []

        if not self.codebase.classes:
            return smells

        # Build a map of field names to the classes they appear in
        field_to_classes: dict[str, set[Class]] = defaultdict(set)

        for cls in self.codebase.classes:
            # Get fields from class
            fields = set()

            # For Python, look at instance variables in __init__
            if self.codebase.language == ProgrammingLanguage.PYTHON:
                init_method = next((m for m in cls.methods if m.name == "__init__"), None)
                if init_method and init_method.body:
                    # Simple regex to find self.attr = ... assignments
                    for match in re.finditer(r"self\.(\w+)\s*=", init_method.body):
                        fields.add(match.group(1))

            # For TypeScript, look at class properties
            elif self.codebase.language in (ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT):
                if hasattr(cls, "properties"):
                    for prop in cls.properties:
                        fields.add(prop.name)

            # Add fields to the map
            for field in fields:
                field_to_classes[field].add(cls)

        # Find groups of fields that appear together in multiple classes
        field_groups: dict[frozenset, set[Class]] = defaultdict(set)

        # Start with individual fields that appear in multiple classes
        candidate_fields = {field for field, classes in field_to_classes.items() if len(classes) >= self.config.data_clump_min_classes}

        # Skip if we don't have enough candidate fields
        if len(candidate_fields) < self.config.data_clump_min_fields:
            return smells

        # Build field groups (this is a simplified approach)
        # A more sophisticated approach would use frequent itemset mining algorithms
        for cls in self.codebase.classes:
            # Get fields from this class that are in our candidate set
            cls_fields = {field for field in candidate_fields if cls in field_to_classes[field]}

            # Skip if not enough fields
            if len(cls_fields) < self.config.data_clump_min_fields:
                continue

            # Add all combinations of min_fields fields
            for i in range(self.config.data_clump_min_fields, len(cls_fields) + 1):
                # This is inefficient for large numbers of fields, but works for demonstration
                from itertools import combinations

                for combo in combinations(cls_fields, i):
                    field_group = frozenset(combo)
                    field_groups[field_group].add(cls)

        # Create code smells for field groups that appear in multiple classes
        for field_group, classes in field_groups.items():
            if len(classes) < self.config.data_clump_min_classes:
                continue

            # Use the first class as the "primary" class for the smell
            primary_class = next(iter(classes))
            other_classes = set(classes) - {primary_class}

            severity = CodeSmellSeverity.MEDIUM
            if len(field_group) > self.config.data_clump_min_fields + 2:
                severity = CodeSmellSeverity.HIGH

            smell = DataClump(
                symbol=primary_class,
                severity=severity,
                category=CodeSmellCategory.COUPLERS,
                description=f"Data clump: fields {', '.join(field_group)} appear together in {len(classes)} classes",
                clumped_fields=list(field_group),
                appears_in_classes=list(classes),
            )

            # Add refactoring suggestions
            if self.codebase.language == ProgrammingLanguage.PYTHON:
                smell.refactoring_suggestions.append(f"Extract fields {', '.join(field_group)} into a new class")
                smell.refactoring_suggestions.append("Consider using composition instead of duplicating these fields")
            elif self.codebase.language in (ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT):
                smell.refactoring_suggestions.append(f"Extract fields {', '.join(field_group)} into a new interface or type")
                smell.refactoring_suggestions.append("Use composition to share this data structure between classes")

            smells.append(smell)

        return smells
