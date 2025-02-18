import re
from abc import ABC
from pathlib import Path

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.python import PyFunction
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase

EVAL_SKILLS_TEST_DIR = Path(__file__).parent.parents[3] / "src" / "codemods" / "eval" / "test_files"


########################################################################################################################
# Evaluation Skills - Python
########################################################################################################################
@skill(
    eval_skill=True,
    prompt=r"Add the following header to all files in the codebase: 'Copyright (c) Codegen.\n All rights reserved.' Add comments as necessary.",
    uid="832b77c6-877e-4af0-a111-abf4c1a0b79d",
)
class AddCopyrightHeaderSkill(Skill, ABC):
    """Add a copyright header to all files in the codebase"""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_1")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        r"""Adds the following header to all files in the codebase: 'Copyright (c) Codegen.\nAll rights reserved.\n\n'"""
        for file in codebase.files:
            # Adds header to the file. Note: comments are added
            file.edit("# Copyright (c) Codegen.\n# All rights reserved.\n\n" + file.content)

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(EVAL_SKILLS_TEST_DIR / "sample_ts_1")], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        r"""Adds the following header to all files in the codebase: '// Copyright (c) Codegen.\n// All rights reserved.\n\n'"""
        for file in codebase.files:
            # Adds header to the file. Note: comments are added
            file.edit("// Copyright (c) Codegen.\n// All rights reserved.\n" + file.content)


@skill(eval_skill=True, prompt="Move all functions starting with 'foo' to a file named foo", uid="0c10e812-f19b-4a79-9f7c-6c1a41ae814a")
class MoveFooFunctionsSkill(Skill, ABC):
    """Moves all functions starting with 'foo' to a file named foo"""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_2")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Move all functions starting with 'foo' to foo.py."""
        # get the foo.py file if it exists, otherwise create it Note: extension is included in the file name
        foo_file = codebase.get_file("foo.py") if codebase.has_file("foo.py") else codebase.create_file("foo.py")

        # for each function in the codebase
        for function in codebase.functions:
            # if the function name starts with 'foo'
            if function.name.startswith("foo"):
                # move the function to the foo.py file
                function.move_to_file(foo_file)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        ...


@skill(eval_skill=True, prompt="Adds the following decorator to all functions starting with 'foo': '@decorator_function'", uid="600f0315-4375-49d8-9c3d-8bcd5be87a96")
class AddDecoratorToFooFunctionsSkill(Skill, ABC):
    """This skill adds a specified decorator to all functions within a codebase that start with a particular prefix, ensuring that the decorator is properly imported if not already present."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_3")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds the following decorator to all functions starting with 'foo': '@decorator_function'."""
        # get the decorator_function symbol
        decorator_symbol = codebase.get_symbol("decorator_function")
        # for each file in the codebase
        for file in codebase.files:
            # for each function in the file
            for function in file.functions:
                # if the function name starts with 'foo'
                if function.name.startswith("foo"):
                    # if the decorator is not imported or declared in the file
                    if not file.has_import("decorator_function") and decorator_symbol.file != file:
                        # add an import for the decorator function
                        file.add_symbol_import(decorator_symbol)
                    # add the decorator to the function
                    function.add_decorator(f"@{decorator_symbol.name}")

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        ...


@skill(eval_skill=True, prompt="Rename all functions starting with 'foo' to start with 'bar'", uid="0c266e31-22ce-4016-bc08-22f19f84a09f")
class RenameFooToBarSkill(Skill, ABC):
    """Renames all functions in the codebase that start with 'foo' to start with 'bar', ensuring consistent naming conventions throughout the code."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_4")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Renames all functions starting with 'foo' to start with 'bar'."""
        # for each function in the codebase
        for function in codebase.functions:
            # if the function name starts with 'foo'
            if function.name.startswith("foo"):
                # rename the function to start with 'bar'
                function.rename(function.name.replace("foo", "bar", 1))

    @staticmethod
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        # for each function in the codebase
        for function in codebase.functions:
            # if the function name starts with 'foo'
            if function.name.startswith("foo"):
                # rename the function to start with 'bar'
                function.rename(function.name.replace("foo", "bar", 1))


@skill(eval_skill=True, prompt="Add an int return type hint to all functions starting with 'foo'", uid="9d49107e-2723-4b38-8a2e-735e3e183ad7")
class AddReturnTypeHintSkill(Skill, ABC):
    """Adds an integer return type hint to all functions whose names start with 'foo'."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_5")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds an int return type hint to all functions starting with 'foo'."""
        # for each function in the codebase
        for function in codebase.functions:
            # if the function name starts with 'foo'
            if function.name.startswith("foo"):
                # add an int return type hint to the function
                function.return_type.edit("int")

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        ...


@skill(
    eval_skill=True,
    prompt="""Move any enums within a file into a file called: `enums.py`. Create an `enums.py` file if it does not
    exist. If the original file only contains enums rename it to`enums.py`""",
    uid="9d752b32-9204-420b-b985-fefd9241cbce",
)
class MoveEnumsToSeparateFileSkill(Skill, ABC):
    """Moves any enumerations found within a file into a separate file named `enums.py`. If the original file
    contains only enumerations, it renames that file to `enums.py`. If the `enums.py` file does not exist,
    it creates one.
    """

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_7")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Moves any enums within a file into a file called: `enums.py`. Creates the `enums.py` if it does not
        exist. If the original file only contains enums this skill renames it to `enums.py`
        """
        # for each file in the codebase
        for file in codebase.files:
            # skip the file if it is already named enums.py
            if file.name == "enums.py":
                continue
            # get all enum classes in the file
            enum_classes = [cls for cls in file.classes if cls.is_subclass_of("Enum")]

            if enum_classes:
                # construct the path for the enums file. Note: extension is added to the filepath
                parent_dir = Path(file.filepath).parent
                new_filepath = str(parent_dir / "enums.py")

                # if the file only contains enums rename it
                if len(file.symbols) == len(enum_classes):
                    file.update_filepath(new_filepath)
                else:
                    # get the enums file if it exists, otherwise create it
                    dst_file = codebase.get_file(new_filepath) if codebase.has_file(new_filepath) else codebase.create_file(new_filepath, "from enum import Enum\n\n")
                    # for each enum class in the file
                    for enum_class in enum_classes:
                        # move the enum class to the enums file
                        enum_class.move_to_file(dst_file)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        ...


@skill(eval_skill=True, prompt="Replace Optional[type] with type | None in all functions.", uid="51070237-774f-484e-83d5-9b0ca6be19fc")
class UpdateOptionalTypeHintsSkill(Skill, ABC):
    """This skill replaces type hints in functions and methods by updating instances of Optional[type] to type | None, ensuring compatibility with modern type hinting practices."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_8")], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Replaces Optional[type] with type | None in all functions."""
        # pattern to match Optional[type]
        optional_type_pattern = re.compile(r"Optional\[(.*?)]")

        # update optional parameter type hints
        def update_optional_parameter_type_hints(function: PyFunction):
            # for each parameter in the function
            for parameter in function.parameters:
                # if the parameter is typed
                if parameter.is_typed:
                    # get the old type
                    old_type = parameter.type
                    # if the old type is Optional[type]
                    if "Optional[" in old_type:
                        # replace Optional[type] with type | None
                        new_type = optional_type_pattern.sub(r"\1 | None", old_type)
                        # update the parameter type hint
                        parameter.set_type_annotation(new_type)

        def update_optional_return_type_hints(function: PyFunction):
            # if the function has a return type
            if function.return_type:
                # get the old return type
                old_return_type = function.return_type.source
                # if the old return type is Optional[type]
                if "Optional[" in old_return_type:
                    # replace Optional[type] with type | None
                    new_return_type = optional_type_pattern.sub(r"\1 | None", old_return_type)
                    # update the return type hint
                    function.return_type.edit(new_return_type)

        # for each function in the codebase
        for function in codebase.functions:
            # update optional parameter type hints
            update_optional_parameter_type_hints(function)
            # update optional return type hints
            update_optional_return_type_hints(function)

        # for each class in the codebase
        for cls in codebase.classes:
            # for each method in the class
            for method in cls.methods:
                # update optional parameter type hints
                update_optional_parameter_type_hints(method)
                # update optional return type hints
                update_optional_return_type_hints(method)

    @staticmethod
    @skill_impl([], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """Not Implemented"""
        ...


@skill(
    eval_skill=True,
    prompt="Delete all unused symbols in the codebase that don't start with `bar` (case insensitive) and delete files if they don't have any remaining symbols.",
    uid="cc9d96b0-b614-41c0-8a1d-f64740389913",
)
class DeleteUnusedSymbolsSkill(Skill, ABC):
    """Deletes all unused symbols in the codebase except for those starting with `bar` (case insensitive) and deletes all files without any remaining symbols."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(EVAL_SKILLS_TEST_DIR / "sample_ts_3")], language=ProgrammingLanguage.TYPESCRIPT)
    @skill_impl([SkillTestCase.from_dir(filepath=EVAL_SKILLS_TEST_DIR / "sample_py_6")], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # for each symbol in the codebase
        for symbol in codebase.symbols:
            # if the symbol has no usages
            if not symbol.symbol_usages and not symbol.name.lower().startswith("bar"):
                # remove the symbol
                symbol.remove()

        # Commit symbol deletions to the codebase (NECESSARY to check if files are empty)
        codebase.commit()

        # for each file in the codebase
        for file in codebase.files:
            # if the file does not have symbols
            if not file.symbols:
                # remove the file
                file.remove()


@skill(eval_skill=True, prompt="Mark functions only used within the app directory as internal with @internal in the docs", uid="b75d483f-c060-4896-8551-c5e512043cfe")
class MarkInternalFunctionsSkill(Skill, ABC):
    """This skill identifies functions that are exclusively used within the application directory and marks them as internal by appending an @internal tag to their docstrings."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(EVAL_SKILLS_TEST_DIR / "sample_ts_7")], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Marks all functions that are only used in the `app` directory as an internal function. Marks functions as
        internal by adding the @internal tag to the bottom of the docstring.
        """
        # for each file in the codebase
        for file in codebase.files:
            # skip files that are not in the app directory
            if "app" not in file.filepath.split("/"):
                continue
            # for each function in the file
            for function in file.functions:
                is_internal = True
                # for each usage of the function
                for usage in function.usages:
                    # resolve the usage symbol
                    usage_symbol = usage.usage_symbol
                    # if the usage symbol is not in the app directory
                    if "app" not in usage_symbol.filepath.split("/"):
                        # the function is not internal
                        is_internal = False
                        break
                # if the function is internal
                if is_internal:
                    # if the function does not have a docstring add one
                    if function.docstring is None:
                        updated_docstring = "\n@internal\n"
                    else:
                        # add the @internal tag to the bottom of the docstring
                        current_docstring = function.docstring.text or ""
                        updated_docstring = current_docstring.strip() + "\n\n@internal\n"
                    # update the function docstring
                    function.set_docstring(updated_docstring)

    @staticmethod
    @skill_impl([], ignore=True)
    def python_skill_func(codebase: CodebaseType):
        """Not implemented for Python"""
        ...


########################################################################################################################
# Evaluation Skills - TypeScript Specific Skills
########################################################################################################################


@skill(
    eval_skill=True, prompt="Move all JSX components that are not exported by default into a new file that is in the same directory as the original file.", uid="3af98bae-1336-48e5-9ab1-ff1677f61557"
)
class MoveNonDefaultExportedJSXComponentsSkill(Skill, ABC):
    """Moves all JSX components that are not exported by default into a new file located in the same directory as the original file."""

    @staticmethod
    @skill_impl([SkillTestCase.from_dir(EVAL_SKILLS_TEST_DIR / "sample_ts_2")], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Moves all JSX components that are not exported by default into a new file that is in the same directory as the original file."""
        # for each file in the codebase
        for file in codebase.files:
            # skip files that do not have default exports
            if not file.default_exports:
                continue
            # list to store non-default exported components
            non_default_exported_components = []
            # get the names of the default exports
            default_exports = [export.name for export in file.default_exports]
            # for each function in the file
            for function in file.functions:
                # if the function is a JSX component and is not a default export
                if function.is_jsx and function.name not in default_exports:
                    # add the function to the list of non-default exported components
                    non_default_exported_components.append(function)
            # if there are non-default exported components
            if non_default_exported_components:
                for component in non_default_exported_components:
                    # create a new file in the same directory as the original file
                    component_dir = Path(file.filepath).parent
                    # create a new file path for the component
                    new_file_path = component_dir / f"{component.name}.tsx"
                    # if the file does not exist create it
                    new_file = codebase.create_file(str(new_file_path))
                    # add an import for React
                    new_file.add_import_from_import_string('import React from "react";')
                    # move the component to the new file
                    component.move_to_file(new_file)

    @staticmethod
    @skill_impl([], ignore=True)
    def python_skill_func(codebase: CodebaseType):
        """Not implemented for Python"""
        ...
