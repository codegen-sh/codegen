import re
from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

RemoveUnusedSymbolsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def used_function():
    return "I am used"

def unused_function():
    return "I am not used"

used_variable = "I am used"
unused_variable = "I am not used"

class UsedClass:
    def method(self):
        pass

class UnusedClass:
    def method(self):
        pass

print(used_function())
print(used_variable)
obj = UsedClass()
obj.method()
""",
            output="""
def used_function():
    return "I am used"

used_variable = "I am used"

class UsedClass:
    def method(self):
        pass

print(used_function())
print(used_variable)
obj = UsedClass()
obj.method()
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedSymbolsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function usedFunction(): string {
    return "I am used";
}

function unusedFunction(): string {
    return "I am not used";
}

const usedVariable: string = "I am used";
const unusedVariable: string = "I am not used";

class UsedClass {
    method(): void {
        // Used method
    }
}

class UnusedClass {
    method(): void {
        // Unused method
    }
}

console.log(usedFunction());
console.log(usedVariable);
const obj = new UsedClass();
obj.method();
""",
            output="""
function usedFunction(): string {
    return "I am used";
}

const usedVariable: string = "I am used";

class UsedClass {
    method(): void {
        // Used method
    }
}

console.log(usedFunction());
console.log(usedVariable);
const obj = new UsedClass();
obj.method();
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""Delete all symbols that are "dead code", i.e. they have no usages.""",
    guide=True,
    uid="d1f2582f-adc4-4574-bf99-7bf76728bea8",
)
class RemoveUnusedSymbols(Skill, ABC):
    """Iterates through all files in the codebase and checks each function for usages. If a function has no usages
    and no call sites, it is removed from the codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedSymbolsPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveUnusedSymbolsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all symbols in the codebase
        for symbol in codebase.symbols:
            # Check if the symbols has no usages
            if not symbol.usages:
                # Remove the unused symbols
                symbol.remove()


RemoveUnusedFunctionsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def used_function():
    print("This function is used")

def unused_function():
    print("This function is not used")

used_function()
""",
            output="""
def used_function():
    print("This function is used")

used_function()
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedFunctionsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function usedFunction() {
    console.log("This function is used");
}

function unusedFunction() {
    console.log("This function is not used");
}

usedFunction();
""",
            output="""
function usedFunction() {
    console.log("This function is used");
}

usedFunction();
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""Remove all 'dead' functions - i.e. they have no usages or call-sites.""",
    guide=True,
    uid="f60fedfd-9a94-438e-bb12-f106aa851169",
)
class RemoveUnusedFunctions(Skill, ABC):
    """Iterates through all files in the codebase and checks each function for usages and call sites. If a function
    is found to be unused (i.e., it has no usages and no call sites), it prints a message indicating that the
    function will be removed and subsequently removes the function from the file.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedFunctionsPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveUnusedFunctionsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all functions in the codebase
        for function in codebase.functions:
            # Check if the function has no usages and no call sites
            if not function.usages and not function.call_sites:
                # Print a message indicating the removal of the function
                print(f"Removing unused function: {function.name}")
                # Remove the function from the file
                function.remove()


RemoveUnusedImportsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
import os
import sys
from math import pi

print(os.getcwd())
""",
            output="""
import os

print(os.getcwd())
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedImportsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
import { readFile, writeFile } from 'fs';
import { join } from 'path';
import { pi } from 'math';

console.log(readFile('example.txt'));
""",
            output="""
import { readFile } from 'fs';

console.log(readFile('example.txt'));
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""Remove all of the imports from the codebase that are not actually being used (they are dead code)""",
    guide=True,
    uid="905b2229-ed9a-47e1-ad48-f372fe6a759b",
)
class RemoveUnusedImports(Skill, ABC):
    """Removes unused import statements from files in the codebase.

    Iterates through each file and checks the import statements. If an import statement has no usages, it prints a
    message indicating the removal of the unused import and proceeds to remove it from the file.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedImportsPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveUnusedImportsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all imports in the codebase
        for import_stmt in codebase.imports:
            # Check if the import statement has no usages
            if not import_stmt.usages:
                # Print a message indicating the removal of the unused import
                print(f"Removing unused import: {import_stmt.name}")
                # Remove the import statement from the file
                import_stmt.remove()


RemoveUnusedLocalVariableAssignmentsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def example_function():
    used_var = 10
    unused_var = 20
    print(used_var)

example_function()
""",
            output="""
def example_function():
    used_var = 10
    print(used_var)

example_function()
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedLocalVariableAssignmentsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function exampleFunction() {
    let usedVar = 10;
    let unusedVar = 20;
    console.log(usedVar);
}

exampleFunction();
""",
            output="""
function exampleFunction() {
    let usedVar = 10;
    console.log(usedVar);
}

exampleFunction();
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""For each top-levle function in the codebase (not methods), if any local variable assignment has no usages, remove that assignment from the function.""",
    guide=True,
    uid="28753ecf-f576-4729-8590-9aaafd507802",
)
class RemoveUnusedLocalVariableAssignments(Skill, ABC):
    """Iterates through all functions in the codebase and checks their local variable assignments. If any local
    variable assignment has no usages within the function, it removes that assignment from the code block.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedLocalVariableAssignmentsPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveUnusedLocalVariableAssignmentsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all functions in the codebase
        for func in codebase.functions:
            # Iterate through local variable assignments in the function
            for var_assignments in func.code_block.local_var_assignments:
                # Check if the local variable assignment has no usages
                if not var_assignments.local_usages:
                    # Remove the local variable assignment
                    var_assignments.remove()


RemoveUnusedParametersAndArgumentsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def example_function(used_param, unused_param):
    print(used_param)

example_function(10, 20)
""",
            output="""
def example_function(used_param):
    print(used_param)

example_function(10)
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedParametersAndArgumentsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function exampleFunction(usedParam: number, unusedParam: number): void {
    console.log(usedParam);
}

exampleFunction(10, 20);
""",
            output="""
function exampleFunction(usedParam: number): void {
    console.log(usedParam);
}

exampleFunction(10);
""",
            filepath="example.ts",
        ),
    ]
)


# TODO: The skill below currently is not supported by the GraphSitter API
@skill(
    prompt="""For all functions in the codebase, and for each function in those, checks parameters for any that are unused.
    If an unused parameter is found, print a message indicating its removal from the function.
    Additionally, update all call sites of the function to remove the corresponding argument for the unused parameter.""",
    guide=True,
    uid="e63cfb69-ca85-4a3c-ab3f-99b9e0e22c7a",
)
class RemoveUnusedParametersAndArguments(Skill, ABC):
    """Iterates through all files in the codebase and checks each function's parameters for usage. If a parameter is
    found to be unused, it prints a message indicating the removal of the parameter from the function. Additionally,
    it updates all call sites of the function to remove the corresponding argument associated with the unused
    parameter.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedParametersAndArgumentsPyTestCase], language=ProgrammingLanguage.PYTHON, ignore=True)
    @skill_impl(test_cases=[RemoveUnusedParametersAndArgumentsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT, ignore=True)
    def skill_func(codebase: CodebaseType):
        # iterate through all functions in the codebase
        for function in codebase.functions:
            for param in function.parameters:
                if not param.usages:
                    print(f"✂️ Removing unused parameter: {param.name} from {function.name}")
                    param.remove()


RemoveUnusedClassesPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class UsedClass:
    def method(self):
        print("This class is used")

class UnusedClass:
    def method(self):
        print("This class is not used")

obj = UsedClass()
obj.method()
""",
            output="""
class UsedClass:
    def method(self):
        print("This class is used")

obj = UsedClass()
obj.method()
""",
            filepath="example.py",
        ),
    ]
)

RemoveUnusedClassesTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
class UsedClass {
    method() {
        console.log("This class is used");
    }
}

class UnusedClass {
    method() {
        console.log("This class is not used");
    }
}

const obj = new UsedClass();
obj.method();
""",
            output="""
class UsedClass {
    method() {
        console.log("This class is used");
    }
}

const obj = new UsedClass();
obj.method();
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""Delete all the classes in the codebase that have no usages (and are therefore dead code)""",
    guide=True,
    uid="d6f29742-649a-4018-8ef8-b013ef80a27b",
)
class RemoveUnusedClasses(Skill, ABC):
    """Iterates through all files in the codebase and checks each class for usages. If a class has no usages,
    it prints a message indicating that the class is being removed and then removes the class from the file.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveUnusedClassesPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveUnusedClassesTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all classes in the codebase
        for cls in codebase.classes:
            # Check if the class has no usages
            if not cls.usages:
                # Print a message indicating the removal of the unused class
                print(f"Removing unused class: {cls.name}")
                # Remove the class from the file
                cls.remove()


CleanUpCodebasePyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def example_function():
    print("Hello")



print("World")


""",
            output="""
def example_function():
    print("Hello")

print("World")
""",
            filepath="non_empty_file.py",
        ),
        SkillTestCasePyFile(
            input="""

""",
            output="",
            filepath="empty_file.py",
        ),
    ]
)

CleanUpCodebaseTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function exampleFunction(): void {
    console.log("Hello");
}



console.log("World");


""",
            output="""
function exampleFunction(): void {
    console.log("Hello");
}

console.log("World");
""",
            filepath="non_empty_file.ts",
        ),
        SkillTestCaseTSFile(
            input="""

""",
            output="",
            filepath="empty_file.ts",
        ),
    ]
)


@skill(
    prompt="""Eliminate all empty files. In addition, eliminate all redundant newlines in the file content, ensuring that no more than two consecutive newlines remain.""",
    guide=True,
    uid="74382f37-ebec-4481-831f-556589927d68",
)
class CleanUpCodebase(Skill, ABC):
    """Removes empty files from the codebase and reduces redundant newlines in the content of each file. The first
    loop iterates through all files, checking if their content is empty and removing them if so. The second loop
    processes each file's content, replacing instances of three or more consecutive newlines with two newlines.
    """

    @staticmethod
    @skill_impl(test_cases=[CleanUpCodebasePyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[CleanUpCodebaseTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # iterate through all files in the codebase
        for file in codebase.files:
            # Check if the file is empty
            if not file.content.strip():
                # Print a message indicating the removal of the empty file
                print(f"Removing empty file: {file.filepath}")
                # Remove the empty file
                file.remove()

        # commit is NECESSARY to remove the files from the codebase
        codebase.commit()

        # Remove redundant newlines
        for file in codebase.files:
            # Replace three or more consecutive newlines with two newlines
            file.edit(re.sub(r"\n{3,}", "\n\n", file.content))
