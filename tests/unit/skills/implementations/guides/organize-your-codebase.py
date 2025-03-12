from abc import ABC

from codegen.sdk.core.codebase import CodebaseType, TSCodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

SplitFunctionsIntoSeparateFilesPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
NON_FUNCTION = 'This is not a function'
def function1():
    print("This is function 1")

def function2():
    print("This is function 2")

def function3():
    print("This is function 3")
""",
            output="""
            NON_FUNCTION = 'This is not a function'
""",
            filepath="path/to/file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def function1():
    print("This is function 1")
""",
            filepath="function1.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def function2():
    print("This is function 2")
""",
            filepath="function2.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def function3():
    print("This is function 3")
""",
            filepath="function3.py",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that retrieves a Python file from a codebase, iterates through its functions,
    creates a new file for each function using the function's name, and moves the function to the newly created file.""",
    guide=True,
    uid="5cead96b-7922-49db-b6dd-d48fb51680d2",
)
class SplitFunctionsIntoSeparateFiles(Skill, ABC):
    """This code snippet retrieves a Python file from the codebase and iterates through its functions. For each
    function, it creates a new file named after the function and moves the function's definition to the newly created
    file.
    """

    @staticmethod
    @skill_impl(test_cases=[SplitFunctionsIntoSeparateFilesPyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Retrieve the Python file from the codebase
        file = codebase.get_file("path/to/file.py")
        # Iterate through the functions in the file
        for function in file.functions:
            # Create a new file for each function using the function's name
            new_file = codebase.create_file(function.name + ".py")
            # Move the function to the newly created file
            function.move_to_file(new_file)


MoveSymbolDemonstrationPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def my_function():
    print("This is my function")

def another_function():
    my_function()
""",
            output="""
from path.to.dst.location import my_function

def another_function():
    my_function()
""",
            filepath="path/to/source_file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def my_function():
    print("This is my function")
""",
            filepath="path/to/dst/location.py",
        ),
    ]
)

MoveSymbolDemonstrationTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function myFunction() {
    console.log("This is my function");
}

function anotherFunction() {
    myFunction();
}
""",
            output="""
import { myFunction } from 'path/to/dst/location';

function anotherFunction() {
    myFunction();
}
""",
            filepath="path/to/source_file.ts",
        ),
        SkillTestCaseTSFile(
            input="",
            output="""
export function myFunction() {
    console.log("This is my function");
}
""",
            filepath="path/to/dst/location.ts",
        ),
    ]
)


@skill(prompt="Generate a code snippet that demonstrates how to move a symbol from one file to another in a codebase.", guide=True, uid="1f0182b7-d3c6-4cde-8ffd-d1bbe31e51be")
class MoveSymbolDemonstration(Skill, ABC):
    """This code snippet demonstrates how to move a symbol from one file to another in a codebase."""

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolDemonstrationPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        source_file = codebase.get_file("path/to/source_file.py")
        # =====[ Code Snippet ]=====
        # Get the symbol
        symbol_to_move = source_file.get_symbol("my_function")
        # Pick a destination file
        dst_file = codebase.get_file("path/to/dst/location.py")
        # Move the symbol, move all of its dependencies with it (remove from old file), and add an import of symbol into old file
        symbol_to_move.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolDemonstrationTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        source_file = codebase.get_file("path/to/source_file.ts")
        # =====[ Code Snippet ]=====
        # Get the symbol
        symbol_to_move = source_file.get_symbol("myFunction")
        # Pick a destination file
        dst_file = codebase.get_file("path/to/dst/location.ts")
        # Move the symbol, move all of its dependencies with it (remove from old file), and add an import of symbol into old file
        symbol_to_move.move_to_file(dst_file, include_dependencies=True, strategy="add_back_edge")


MoveSymbolWithUpdatedImportsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def symbol_to_move():
    print("This symbol will be moved")

def use_symbol():
    symbol_to_move()
""",
            output="""
from new_file import symbol_to_move

def use_symbol():
    symbol_to_move()
""",
            filepath="original_file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def symbol_to_move():
    print("This symbol will be moved")
""",
            filepath="new_file.py",
        ),
    ]
)

MoveSymbolWithUpdatedImportsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function symbolToMove() {
    console.log("This symbol will be moved");
}

function useSymbol() {
    symbolToMove();
}
""",
            output="""
import { symbolToMove } from 'new_file';

function useSymbol() {
    symbolToMove();
}
""",
            filepath="original_file.ts",
        ),
        SkillTestCaseTSFile(
            input="",
            output="""
export function symbolToMove() {
    console.log("This symbol will be moved");
}
""",
            filepath="new_file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to use a method called `move_to_file` on an object named
    `symbol_to_move`. The method should take two parameters: `dest_file`, which represents the destination file path,
    and `strategy`, which should be set to the string value "update_all_imports".""",
    guide=True,
    uid="d24a61b5-212e-4567-87b0-f6ab586b42c1",
)
class MoveSymbolWithUpdatedImports(Skill, ABC):
    """Moves the symbol to the specified destination file using the given strategy. The default strategy is to update
    all imports.
    """

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolWithUpdatedImportsPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        symbol_to_move = codebase.get_symbol("symbol_to_move")
        dst_file = codebase.create_file("new_file.py")
        symbol_to_move.move_to_file(dst_file, strategy="update_all_imports")

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolWithUpdatedImportsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType) -> callable:
        symbol_to_move = codebase.get_symbol("symbolToMove")
        dst_file = codebase.create_file("new_file.ts")
        symbol_to_move.move_to_file(dst_file, strategy="update_all_imports")


MoveSymbolWithAddBackEdgeStrategyPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def symbol_to_move():
    print("This symbol will be moved")

def use_symbol():
    symbol_to_move()
""",
            output="""
from new_file import symbol_to_move

def use_symbol():
    symbol_to_move()
""",
            filepath="original_file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def symbol_to_move():
    print("This symbol will be moved")
""",
            filepath="new_file.py",
        ),
    ]
)

MoveSymbolWithAddBackEdgeStrategyTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function symbolToMove() {
    console.log("This symbol will be moved");
}

function useSymbol() {
    symbolToMove();
}
""",
            output="""
import { symbolToMove } from 'new_file';

function useSymbol() {
    symbolToMove();
}
""",
            filepath="original_file.ts",
        ),
        SkillTestCaseTSFile(
            input="",
            output="""
export function symbolToMove() {
    console.log("This symbol will be moved");
}
""",
            filepath="new_file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that calls a method named 'move_to_file' on an object named 'symbol_to_move'.
    The method should take two arguments: 'dest_file' and a keyword argument 'strategy' with the value
    'add_back_edge'.""",
    guide=True,
    uid="f6c21eea-a9f5-4c30-b797-ff8fc3646d00",
)
class MoveSymbolWithAddBackEdgeStrategy(Skill, ABC):
    """Moves the symbol to the specified destination file using the given strategy. The default strategy is to add a
    back edge during the move.
    """

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolWithAddBackEdgeStrategyPyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        symbol_to_move = codebase.get_symbol("symbol_to_move")
        dst_file = codebase.create_file("new_file.py")
        symbol_to_move.move_to_file(dst_file, strategy="add_back_edge")

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolWithAddBackEdgeStrategyTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType) -> callable:
        symbol_to_move = codebase.get_symbol("symbolToMove")
        dst_file = codebase.create_file("new_file.ts")
        symbol_to_move.move_to_file(dst_file, strategy="add_back_edge")


MoveSymbolToFileWithDependenciesPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def dependency_function():
    print("I'm a dependency")

def my_symbol():
    dependency_function()
    print("This is my symbol")

def use_symbol():
    my_symbol()
""",
            output="""
from new_file import my_symbol

def use_symbol():
    my_symbol()
""",
            filepath="original_file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def dependency_function():
    print("I'm a dependency")

def my_symbol():
    dependency_function()
    print("This is my symbol")
""",
            filepath="new_file.py",
        ),
    ]
)

MoveSymbolToFileWithDependenciesTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function dependencyFunction() {
    console.log("I'm a dependency");
}

function mySymbol() {
    dependencyFunction();
    console.log("This is my symbol");
}

function useSymbol() {
    mySymbol();
}
""",
            output="""
import { mySymbol } from 'new_file';

function useSymbol() {
    mySymbol();
}
""",
            filepath="original_file.ts",
        ),
        SkillTestCaseTSFile(
            input="",
            output="""
export function dependencyFunction() {
    console.log("I'm a dependency");
}

export function mySymbol() {
    dependencyFunction();
    console.log("This is my symbol");
}
""",
            filepath="new_file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to use a method called `move_to_file` on an object named
    `my_symbol`. The method should take two parameters: `dest_file`, which specifies the destination file,
    and `include_dependencies`, which is a boolean parameter set to `True`.""",
    guide=True,
    uid="0665e746-fa10-4d63-893f-be305202bab2",
)
class MoveSymbolToFileWithDependencies(Skill, ABC):
    """Moves the symbol to the specified destination file.

    If include_dependencies is set to True, any dependencies associated with the symbol will also be moved to the
    destination file.
    """

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolToFileWithDependenciesPyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        my_symbol = codebase.get_symbol("my_symbol")
        dst_file = codebase.create_file("new_file.py")
        my_symbol.move_to_file(dst_file, include_dependencies=True)

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolToFileWithDependenciesTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: TSCodebaseType):
        my_symbol = codebase.get_symbol("mySymbol")
        dst_file = codebase.create_file("new_file.ts")
        my_symbol.move_to_file(dst_file, include_dependencies=True)


MoveSymbolsWithDependenciesPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def dependency_function():
    print("I'm a dependency")

def my_function():
    dependency_function()
    print("This is my function")

class MyClass:
    def __init__(self):
        self.value = dependency_function()

def use_symbols():
    my_function()
    obj = MyClass()
""",
            output="""
from path.to.destination_file import my_function, MyClass

def use_symbols():
    my_function()
    obj = MyClass()
""",
            filepath="path/to/source_file.py",
        ),
        SkillTestCasePyFile(
            input="",
            output="""
def dependency_function():
    print("I'm a dependency")

def my_function():
    dependency_function()
    print("This is my function")

class MyClass:
    def __init__(self):
        self.value = dependency_function()
""",
            filepath="path/to/destination_file.py",
        ),
    ]
)


@skill(
    prompt="""Generate a Python code snippet that creates a list of symbols to move from a source file to a
    destination file. The symbols should include a function named 'my_function' and a class named 'MyClass' from the
    source file. Then, iterate over the list of symbols and move each symbol to the destination file, ensuring to
    include dependencies and update all imports.""",
    guide=True,
    uid="0895acd3-3788-44a6-8450-d1a5c9cea564",
)
class MoveSymbolsWithDependencies(Skill, ABC):
    """Moves specified symbols from the source file to the destination file.

    This code snippet retrieves a function and a class from the source file and stores them in a list. It then
    iterates over this list, moving each symbol to the destination file while including dependencies and updating all
    imports accordingly.
    """

    @staticmethod
    @skill_impl(test_cases=[MoveSymbolsWithDependenciesPyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Retrieve the source and destination files
        source_file = codebase.get_file("path/to/source_file.py")
        dest_file = codebase.get_file("path/to/destination_file.py")
        # Create a list of symbols to move
        symbols_to_move = [source_file.get_function("my_function"), source_file.get_class("MyClass")]
        # Move each symbol to the destination file
        for symbol in symbols_to_move:
            symbol.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")
