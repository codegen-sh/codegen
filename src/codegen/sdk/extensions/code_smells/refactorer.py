"""Code smell refactoring tools for Python and TypeScript codebases."""

import re
from abc import ABC, abstractmethod
from typing import Optional, cast

from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.function import Function
from codegen.sdk.extensions.code_smells.smells import (
    CodeSmell,
    DeadCode,
    LongFunction,
    LongParameterList,
)
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RefactoringStrategy(ABC):
    """Base class for all refactoring strategies."""

    @abstractmethod
    def can_refactor(self, smell: CodeSmell) -> bool:
        """Check if this strategy can refactor the given code smell."""
        pass

    @abstractmethod
    def refactor(self, smell: CodeSmell) -> bool:
        """Refactor the code smell.

        Returns:
            True if refactoring was successful, False otherwise
        """
        pass


class LongFunctionRefactoring(RefactoringStrategy):
    """Strategy for refactoring long functions."""

    def __init__(self, codebase: Codebase):
        """Initialize the refactoring strategy.

        Args:
            codebase: The codebase to refactor
        """
        self.codebase = codebase

    def can_refactor(self, smell: CodeSmell) -> bool:
        """Check if this strategy can refactor the given code smell."""
        return isinstance(smell, LongFunction) and smell.can_auto_refactor()

    def refactor(self, smell: CodeSmell) -> bool:
        """Refactor a long function by extracting parts into helper functions.

        This is a simplified implementation that extracts code blocks based on
        indentation patterns. A more sophisticated implementation would:
        - Use AST analysis to identify logical blocks
        - Analyze variable usage to determine parameters and return values
        - Generate appropriate function names based on the extracted code

        Returns:
            True if refactoring was successful, False otherwise
        """
        if not self.can_refactor(smell):
            return False

        long_function = cast(LongFunction, smell)
        function = long_function.symbol

        if not function.body:
            return False

        # Simple approach: look for blocks with consistent indentation
        lines = function.body.split("\n")

        # Find indentation blocks (simplified)
        blocks = []
        current_block = []
        current_indent = None

        for line in lines:
            if not line.strip():
                current_block.append(line)
                continue

            indent = len(line) - len(line.lstrip())

            if current_indent is None:
                current_indent = indent
                current_block.append(line)
            elif indent == current_indent:
                current_block.append(line)
            else:
                # New indentation level, finish current block if it's substantial
                if len(current_block) >= 5:  # Only extract blocks of reasonable size
                    blocks.append((current_indent, current_block))
                current_block = [line]
                current_indent = indent

        # Add the last block if it's substantial
        if current_block and len(current_block) >= 5:
            blocks.append((current_indent, current_block))

        # Skip if we couldn't identify good extraction candidates
        if not blocks:
            return False

        # Sort blocks by size (largest first) and extract the largest ones
        blocks.sort(key=lambda b: len(b[1]), reverse=True)

        # Extract up to 2 blocks (to avoid over-refactoring)
        extracted_count = 0
        new_body_lines = lines.copy()

        for indent, block in blocks[:2]:
            # Skip if block is too small after filtering blank lines
            content_lines = [l for l in block if l.strip()]
            if len(content_lines) < 5:
                continue

            # Generate a helper function name based on first line content
            first_content_line = next((l for l in block if l.strip()), "")
            helper_name = self._generate_helper_name(first_content_line, function.name)

            # Determine the start and end indices in the original function
            start_idx = lines.index(block[0])
            end_idx = start_idx + len(block) - 1

            # Create the helper function
            helper_function = self._create_helper_function(function, helper_name, block, indent)

            if helper_function:
                # Replace the block with a call to the helper
                call_line = " " * indent + f"{helper_name}()"  # Simplified, should include params
                new_body_lines[start_idx : end_idx + 1] = [call_line]
                extracted_count += 1

        if extracted_count == 0:
            return False

        # Update the original function body
        function.body = "\n".join(new_body_lines)
        return True

    def _generate_helper_name(self, first_line: str, parent_name: str) -> str:
        """Generate a name for the extracted helper function."""
        # Strip leading whitespace and common prefixes
        clean_line = first_line.lstrip()
        for prefix in ["if ", "for ", "while ", "try:", "with "]:
            if clean_line.startswith(prefix):
                clean_line = clean_line[len(prefix) :].strip()
                break

        # Extract meaningful words (simplified)
        words = []
        for word in clean_line.split()[:3]:  # Use first 3 words max
            # Clean up the word
            word = "".join(c for c in word if c.isalnum())
            if word and not word.isdigit():
                words.append(word.lower())

        if not words:
            return f"_{parent_name}_helper"

        # Combine words into a function name
        return f"_{parent_name}_{'_'.join(words)}"

    def _create_helper_function(self, parent: Function, name: str, block_lines: list[str], base_indent: int) -> Optional[Function]:
        """Create a helper function from the extracted block."""
        # Determine the file to add the helper to
        if not parent.file:
            return None

        # Remove the base indentation from all lines
        dedented_lines = []
        for line in block_lines:
            if not line.strip():
                dedented_lines.append("")
            else:
                # Ensure we don't have negative indentation
                current_indent = len(line) - len(line.lstrip())
                new_indent = max(0, current_indent - base_indent)
                dedented_lines.append(" " * new_indent + line.lstrip())

        # Create the helper function body
        helper_body = "\n".join(dedented_lines)

        # Add the helper function to the file
        if self.codebase.language == ProgrammingLanguage.PYTHON:
            # For Python, add the helper after the parent function
            helper = parent.file.add_function(
                name=name,
                body=helper_body,
                parameters=[],  # Simplified, should analyze needed parameters
                after=parent,
            )
        else:
            # For other languages, add at the end of the file
            helper = parent.file.add_function(
                name=name,
                body=helper_body,
                parameters=[],  # Simplified, should analyze needed parameters
            )

        return helper


class DeadCodeRefactoring(RefactoringStrategy):
    """Strategy for refactoring dead code."""

    def __init__(self, codebase: Codebase):
        """Initialize the refactoring strategy."""
        self.codebase = codebase

    def can_refactor(self, smell: CodeSmell) -> bool:
        """Check if this strategy can refactor the given code smell."""
        return isinstance(smell, DeadCode) and smell.can_auto_refactor()

    def refactor(self, smell: CodeSmell) -> bool:
        """Refactor dead code by removing it.

        Returns:
            True if refactoring was successful, False otherwise
        """
        if not self.can_refactor(smell):
            return False

        dead_code = cast(DeadCode, smell)
        symbol = dead_code.symbol

        # Remove the symbol
        try:
            symbol.delete()
            return True
        except Exception as e:
            logger.exception(f"Failed to remove dead code {symbol.name}: {e}")
            return False


class LongParameterListRefactoring(RefactoringStrategy):
    """Strategy for refactoring functions with long parameter lists."""

    def __init__(self, codebase: Codebase):
        """Initialize the refactoring strategy."""
        self.codebase = codebase

    def can_refactor(self, smell: CodeSmell) -> bool:
        """Check if this strategy can refactor the given code smell."""
        return isinstance(smell, LongParameterList) and smell.can_auto_refactor()

    def refactor(self, smell: CodeSmell) -> bool:
        """Refactor a function with a long parameter list by introducing a parameter object.

        This is a simplified implementation that groups parameters into a class/object.
        A more sophisticated implementation would:
        - Analyze parameter usage to determine logical groupings
        - Update all call sites to use the new parameter object

        Returns:
            True if refactoring was successful, False otherwise
        """
        if not self.can_refactor(smell):
            return False

        long_param_list = cast(LongParameterList, smell)
        function = long_param_list.symbol

        if not function.parameters or not function.file:
            return False

        # Create a name for the parameter object
        param_object_name = f"{function.name.title().replace('_', '')}Params"

        # Group parameters (simplified approach)
        # In a real implementation, we would analyze parameter usage patterns
        # to determine logical groupings
        params = function.parameters

        # Skip if we don't have enough parameters to refactor
        if len(params) <= 3:
            return False

        # Create the parameter object
        if self.codebase.language == ProgrammingLanguage.PYTHON:
            return self._refactor_python(function, params, param_object_name)
        elif self.codebase.language in (ProgrammingLanguage.TYPESCRIPT, ProgrammingLanguage.JAVASCRIPT):
            return self._refactor_typescript(function, params, param_object_name)
        else:
            return False

    def _refactor_python(self, function: Function, params: list, param_object_name: str) -> bool:
        """Refactor a Python function with a long parameter list."""
        if not function.file:
            return False

        # Create a dataclass for the parameters
        dataclass_def = [
            "@dataclass",
            f"class {param_object_name}:",
            '    """Parameter object for {function.name}"""',
        ]

        # Add fields for each parameter
        for param in params:
            # Skip self/cls for methods
            if param.name in ("self", "cls"):
                continue

            # Add type hint if available
            type_hint = f": {param.type_annotation}" if hasattr(param, "type_annotation") and param.type_annotation else ""
            default = f" = {param.default}" if hasattr(param, "default") and param.default is not None else ""
            dataclass_def.append(f"    {param.name}{type_hint}{default}")

        # Add the dataclass to the file
        dataclass_body = "\n".join(dataclass_def)

        # Add import for dataclass if needed
        has_dataclass_import = any("from dataclasses import dataclass" in imp.source for imp in function.file.imports if hasattr(imp, "source"))

        if not has_dataclass_import:
            function.file.add_import("from dataclasses import dataclass")

        # Add the dataclass to the file
        function.file.add_class(
            name=param_object_name,
            body="\n".join(dataclass_def[2:]),  # Skip the decorator and class line
            decorators=["dataclass"],
            before=function,
        )

        # Update the function signature
        # Keep special parameters like self/cls
        special_params = [p for p in params if p.name in ("self", "cls")]
        new_params = [*special_params, f"params: {param_object_name}"]

        # Update function body to use the params object
        if function.body:
            body_lines = function.body.split("\n")
            for i, line in enumerate(body_lines):
                for param in params:
                    # Skip self/cls
                    if param.name in ("self", "cls"):
                        continue

                    # Replace parameter references with params.parameter
                    # This is a simplified approach and might need more sophisticated regex
                    body_lines[i] = re.sub(r"\b" + param.name + r"\b", f"params.{param.name}", line)

            function.body = "\n".join(body_lines)

        # Update the function signature
        function.parameters = new_params

        return True

    def _refactor_typescript(self, function: Function, params: list, param_object_name: str) -> bool:
        """Refactor a TypeScript function with a long parameter list."""
        if not function.file:
            return False

        # Create an interface for the parameters
        interface_def = [
            f"interface {param_object_name} {{",
        ]

        # Add fields for each parameter
        for param in params:
            # Add type annotation if available
            type_annotation = f": {param.type}" if hasattr(param, "type") and param.type else ": any"
            interface_def.append(f"  {param.name}{type_annotation};")

        interface_def.append("}")

        # Add the interface to the file
        interface_body = "\n".join(interface_def)
        function.file.add_interface(
            name=param_object_name,
            body="\n".join(interface_def[1:-1]),  # Skip the interface line and closing brace
            before=function,
        )

        # Update the function signature
        new_params = [f"params: {param_object_name}"]

        # Update function body to use the params object
        if function.body:
            body_lines = function.body.split("\n")
            for i, line in enumerate(body_lines):
                for param in params:
                    # Replace parameter references with params.parameter
                    body_lines[i] = re.sub(r"\b" + param.name + r"\b", f"params.{param.name}", line)

            function.body = "\n".join(body_lines)

        # Update the function signature
        function.parameters = new_params

        return True


class CodeSmellRefactorer:
    """Refactorer for common code smells in Python and TypeScript codebases."""

    def __init__(self, codebase: Codebase):
        """Initialize the code smell refactorer.

        Args:
            codebase: The codebase to refactor
        """
        self.codebase = codebase

        # Register refactoring strategies
        self._strategies: dict[type[CodeSmell], RefactoringStrategy] = {
            LongFunction: LongFunctionRefactoring(codebase),
            DeadCode: DeadCodeRefactoring(codebase),
            LongParameterList: LongParameterListRefactoring(codebase),
            # Add more strategies as they are implemented
        }

    def can_refactor(self, smell: CodeSmell) -> bool:
        """Check if a code smell can be automatically refactored.

        Args:
            smell: The code smell to check

        Returns:
            True if the smell can be refactored, False otherwise
        """
        for smell_type, strategy in self._strategies.items():
            if isinstance(smell, smell_type) and strategy.can_refactor(smell):
                return True
        return False

    def refactor(self, smell: CodeSmell) -> bool:
        """Refactor a code smell.

        Args:
            smell: The code smell to refactor

        Returns:
            True if refactoring was successful, False otherwise
        """
        for smell_type, strategy in self._strategies.items():
            if isinstance(smell, smell_type) and strategy.can_refactor(smell):
                return strategy.refactor(smell)
        return False

    def refactor_all(self, smells: list[CodeSmell]) -> dict[CodeSmell, bool]:
        """Refactor all refactorable code smells.

        Args:
            smells: List of code smells to refactor

        Returns:
            Dictionary mapping code smells to refactoring success status
        """
        results = {}
        for smell in smells:
            if self.can_refactor(smell):
                success = self.refactor(smell)
                results[smell] = success
        return results
