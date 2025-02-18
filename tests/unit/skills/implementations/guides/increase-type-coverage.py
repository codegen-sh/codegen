from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

CountTypedParametersPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def no_params():
    pass

def all_typed(a: int, b: str, c: float):
    pass

def no_typed(a, b, c):
    pass

def mixed_typed(a: int, b, c: float, d):
    pass

print("Start of output")
""",
            filepath="example.py",
        ),
    ],
    sanity=True,
)

CountTypedParametersTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function noParams(): void {
    // No parameters
}

function allTyped(a: number, b: string, c: boolean): void {
    // All parameters typed
}

function noTyped(a, b, c): void {
    // No parameters typed
}

function mixedTyped(a: number, b, c: boolean, d): void {
    // Mix of typed and untyped parameters
}

console.log("Start of output");
""",
            filepath="example.ts",
        ),
    ],
    sanity=True,
)


@skill(
    eval_skill=False,
    prompt="""Count the total number of parameters for functions in my codebase, as well as the total number of typed
    parameters. Then print out the percentage of parameters that have type hints.""",
    guide=True,
    uid="8fc00ff0-1c7c-4cb5-a254-6ba0a8a8a71a",
)
class CountTypedParametersSkill(Skill, ABC):
    """Calculates the percentage of function parameters in a codebase that have type hints. It initializes counters
    for total and typed parameters, iterates through all files and functions in the codebase to count the parameters,
    and computes the percentage of those that are typed. Finally, it prints the percentage of function arguments with
    type hints.
    """

    @staticmethod
    @skill_impl(test_cases=[CountTypedParametersPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[CountTypedParametersTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Initialize counters for total parameters and typed parameters
        total_parameters = 0
        typed_parameters = 0

        # Iterate through all functions in the file
        for function in codebase.functions:
            # Count the total number of parameters
            total_parameters += len(function.parameters)
            # Count the number of parameters that have type hints
            typed_parameters += sum(1 for param in function.parameters if param.is_typed)

        # Calculate the percentage of parameters with type hints
        if total_parameters > 0:
            percentage_typed = (typed_parameters / total_parameters) * 100
        else:
            percentage_typed = 0

        # Print the result
        print(f"Percentage of function arguments with type hints: {percentage_typed:.2f}%")


SetReturnTypeToNoneForFunctionsWithoutReturnsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_without_return():
    print("This function has no return")

def function_with_return():
    return "This function has a return"

def function_with_existing_return_type() -> str:
    print("This function has an existing return type")
""",
            output="""
def function_without_return() -> None:
    print("This function has no return")

def function_with_return():
    return "This function has a return"

def function_with_existing_return_type() -> None:
    print("This function has an existing return type")
""",
            filepath="app/example.py",
        ),
        SkillTestCasePyFile(
            input="""
def function_in_non_app_file():
    print("This function is in a non-app file")
""",
            output="""
def function_in_non_app_file():
    print("This function is in a non-app file")
""",
            filepath="example.py",
        ),
    ]
)

SetReturnTypeToNoneForFunctionsWithoutReturnsTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function functionWithoutReturn() {
    console.log("This function has no return");
}

function functionWithReturn(): string {
    return "This function has a return";
}

function functionWithExistingReturnType(): void {
    console.log("This function has an existing return type");
}
""",
            output="""
function functionWithoutReturn(): null {
    console.log("This function has no return");
}

function functionWithReturn(): string {
    return "This function has a return";
}

function functionWithExistingReturnType(): null {
    console.log("This function has an existing return type");
}
""",
            filepath="app/example.ts",
        ),
        SkillTestCaseTSFile(
            input="""
function functionInNonAppFile() {
    console.log("This function is in a non-app file");
}
""",
            output="""
function functionInNonAppFile() {
    console.log("This function is in a non-app file");
}
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    eval_skill=False,
    prompt="""For all files with 'app' in the filepath, convert all functions that lack return statements to have an
    explicit return type (None in Python codebases, null in TypeScript ones).""",
    guide=True,
    uid="32b64c46-51d9-427e-af0b-c13fa62618d7",
)
class SetReturnTypeToNoneForFunctionsWithoutReturns(Skill, ABC):
    """Iterates through all files in the codebase, checking for files that contain 'app' in their filepath. For each
    of these files, it examines all functions and sets the return type to None for those that do not have any return
    statements.
    """

    @staticmethod
    @skill_impl(test_cases=[SetReturnTypeToNoneForFunctionsWithoutReturnsPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Iterate through all files in the codebase
        for file in codebase.files:
            # Check if 'app' is in the file's filepath
            if "app" in file.filepath:
                # Iterate through all functions in the file
                for function in file.functions:
                    # Check if the function has no return statements
                    if len(function.return_statements) == 0:
                        # Set the return type to None
                        function.set_return_type("None")

    @staticmethod
    @skill_impl(test_cases=[SetReturnTypeToNoneForFunctionsWithoutReturnsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Iterate through all files in the codebase
        for file in codebase.files:
            # Check if 'app' is in the file's filepath
            if "app" in file.filepath:
                # Iterate through all functions in the file
                for function in file.functions:
                    # Check if the function has no return statements
                    if len(function.return_statements) == 0:
                        # Set the return type to None
                        function.set_return_type("null")


ModifyReturnTypeSkillPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
from path.to.module import a, b
def function_name() -> a | b:
    return "Hello" if some_condition else 42
""",
            output="""
from path.to.module import a, b, c

def function_name() -> a | b | c:
    return "Hello" if some_condition else 42
""",
            filepath="path/to/file.py",
        ),
        SkillTestCasePyFile(
            input="""
class a:
    pass
class b:
    pass
class c:
    pass
""",
            unchanged=True,
            filepath="path/to/module.py",
        ),
    ]
)

ModifyReturnTypeSkillTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
import { a, b } from 'path/to/module';
function functionName(): a | b {
    return someCondition ? a() : b();
}
""",
            output="""
import { c } from 'path/to/module';
import { a, b } from 'path/to/module';

function functionName(): a | b | c {
    return someCondition ? a() : b();
}
""",
            filepath="path/to/file.ts",
        ),
        SkillTestCaseTSFile(
            input="""
export class a {
// Some implementation
}
export class b {
// Some implementation
}
export class c {
    // Some implementation
}
""",
            unchanged=True,
            filepath="path/to/module.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to modify the return type of a function in a Python file.
    The snippet should include the following steps: 1. Retrieve a specific function from a file in the codebase. 2.
    Modify the return type of that function by appending a new option to it.""",
    guide=True,
    uid="9b1339e2-85ab-4bb7-933e-fd7a1cc1ff5c",
)
class ModifyReturnTypeSkill(Skill, ABC):
    """Modifies the return type of a specified function by appending a new option to it. The function is retrieved
    from a file in the codebase, and the new return type option is added to the existing return types.
    """

    @staticmethod
    @skill_impl(test_cases=[ModifyReturnTypeSkillPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        target_file = codebase.get_file("path/to/file.py")
        function = target_file.get_function("function_name")
        # def function_name() -> a | b: ...

        # import c from module
        c = codebase.get_file("path/to/module.py").get_symbol("c")
        target_file.add_symbol_import(c)

        # Add a new option to the return type
        function.return_type.append("c")

    @staticmethod
    @skill_impl(test_cases=[ModifyReturnTypeSkillTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        target_file = codebase.get_file("path/to/file.ts")
        function = target_file.get_function("functionName")
        # function functionName(): a | b: ...
        c = codebase.get_file("path/to/module.ts").get_symbol("c")
        target_file.add_symbol_import(c)

        # Add a new option to the return type
        function.return_type.append("c")


ModifyReturnTypeWithNewParameterTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_name() -> tuple[int, str]:
    return 42, "Hello"

def another_function():
    result = function_name()
    print(result)
""",
            output="""
from typing import Tuple

def function_name() -> tuple[int, str, float]:
    return 42, "Hello"

def another_function():
    result = function_name()
    print(result)
""",
            filepath="path/to/file.py",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to modify the return type of a function in a Python file.
    The snippet should include the following steps: 1. Retrieve a specific function from a file in the codebase. 2.
    Modify the return type of that function by adding a new parameter to it.""",
    guide=True,
    uid="1c45967b-7ad9-4746-b239-e64dcff3f1cb",
)
class ModifyReturnTypeWithNewParameter(Skill, ABC):
    """Modifies the return type of a specified function by adding a new parameter to it. The function is retrieved
    from a file in the codebase, and the new parameter is appended to the existing return type parameters.
    """

    @staticmethod
    @skill_impl(test_cases=[ModifyReturnTypeWithNewParameterTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        function = codebase.get_file("path/to/file.py").get_function("function_name")
        # def function_name() -> tuple[a, b]: ...

        # Add a new parameter to the return type
        function.return_type.parameters.append("float")


InspectFunctionReturnTypePyTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_name() -> tuple[int, str]:
    return 42, "Hello"

def another_function():
    result = function_name()
    print(result)
""",
            filepath="path/to/file.py",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that performs the following tasks: 1. Retrieve a specific function from a
    Python file in a codebase using its path and function name. 2. Check if a specific parameter ("a") is present in
    the function's return type parameters. The function should be defined to return a tuple containing two elements.""",
    guide=True,
    uid="0d9ddb37-6ebb-4f86-b4c0-8b029e777206",
)
class InspectFunctionReturnType(Skill, ABC):
    """This code snippet retrieves a specific function from a Python file in the codebase and checks if a parameter
    named 'a' is included in the function's return type parameters.
    """

    @staticmethod
    @skill_impl(test_cases=[InspectFunctionReturnTypePyTest], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Find the symbol to inspect
        function = codebase.get_file("path/to/file.py").get_function("function_name")
        # def function_name() -> tuple[a, b]: ...

        # Check if "a" is in the function's return_type's parameters
        if "a" in function.return_type.parameters:
            # type "a" is present in the return type parameters
            print("type 'a' is present in the return type parameters.")


InspectResolveFunctionReturnTypePySanityTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
from xyz import MyContainer, a, b

def function_name() -> MyContainer[a, b]:
    pass

print("Start of output")
""",
            output="""
from xyz import MyContainer, a, b

def function_name() -> MyContainer[a, b]:
    pass

print("Start of output")
MyContainer
a
b
""",
            filepath="path/to/file.py",
        ),
        SkillTestCasePyFile(
            input="""
class MyContainer:
    pass

class a:
    pass

class b:
    pass
""",
            filepath="xyz.py",
        ),
    ],
    sanity=True,
)

InspectResolveFunctionReturnTypeTSSanityTest = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
import { MyContainer, a, b } from './types';

function functionName(): MyContainer<a, b> {
    // Implementation
}

console.log("Start of output");
""",
            output="""
import { MyContainer, a, b } from './types';

function functionName(): MyContainer<a, b> {
    // Implementation
}

console.log("Start of output");
console.log("MyContainer");
console.log("a");
console.log("b");
""",
            filepath="path/to/file.ts",
        ),
        SkillTestCaseTSFile(
            input="""
export class MyContainer<T, U> {
    // Implementation
}

export class a {
    // Implementation
}

export class b {
    // Implementation
}
""",
            filepath="types.ts",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Demonstrate how to inspect the return type of a function codebase. 1. Retrieve a specific function from
    a file in the codebase. 2. Print the resolved symbol of the function's return type. 3. Iterate over the parameters
    of the return type and print their resolved symbols.""",
    guide=True,
    uid="2c984701-9766-43d7-939d-200fa8f47842",
)
class InspectResolveFunctionReturnType(Skill, ABC):
    """Retrieves the function specified by its name from a given file in the codebase and inspects its return type.
    It prints the resolved symbol of the return type and iterates through the parameters of the return type,
    printing each resolved symbol.
    """

    @staticmethod
    @skill_impl(test_cases=[InspectResolveFunctionReturnTypePySanityTest], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Find the symbol to inspect
        function = codebase.get_file("path/to/file.py").get_function("function_name")
        # from xyz import MyContainer, a, b
        # def function_name() -> MyContainer[a, b]: ...
        print(function.return_type.resolved_types)  # Resolves to MyContainer
        for parameter in function.return_type.parameters:
            print(parameter.resolved_types)  # Resolves to a and b

    @staticmethod
    @skill_impl(test_cases=[InspectResolveFunctionReturnTypeTSSanityTest], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Find the symbol to inspect
        function = codebase.get_file("path/to/file.ts").get_function("functionName")
        # import { MyContainer, a, b } './types'
        # function function_name(): MyContainer<a, b> { ... }
        print(function.return_type.resolved_types)  # Resolves to MyContainer
        for parameter in function.return_type.parameters:
            print(parameter.resolved_types)  # Resolves to a and b


ResolveAndRenameGlobalVariableTypeTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class MyType:
    pass

class MyNewType:
    pass

a: MyType = MyType()
""",
            output="""
class MyType:
    pass

class MyNewType:
    pass

a: MyNewType = MyType()
""",
            filepath="path/to/file.py",
        )
    ]
)


@skill(
    prompt="""Generate a code snippet that retrieves a global variable named 'a' from a file located at
    'path/to/file', prints its resolved type, and then renames that resolved type to 'MyNewType'. Ensure to
    include type annotations where appropriate.""",
    guide=True,
    uid="902bda71-1598-4f0a-a547-e31a9ce9ee4c",
)
class ResolveAndRenameGlobalVariableType(Skill, ABC):
    """Retrieves a global variable 'a' from a specified file in the codebase and prints its resolved type. The
    resolved type is then renamed to 'MyNewType'.
    """

    @staticmethod
    @skill_impl(test_cases=[ResolveAndRenameGlobalVariableTypeTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        a = codebase.get_file("path/to/file.py").get_global_var("a")
        # a: MyType = ...
        print(a.type)  # Resolves to MyType
        a.type.rename("MyNewType")  # Renames the symbol `MyType` to `MyNewType` throughout the codebase
