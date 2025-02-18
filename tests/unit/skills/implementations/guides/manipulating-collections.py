from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.symbol_groups.list import List
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

AddParameterToFunctionPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_name():
    pass
""",
            output="""
def function_name(new_param: int):
    pass
""",
            filepath="path/to/file.py",
        ),
    ]
)

AddParameterToFunctionTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function functionName() {
    // Function body
}
""",
            output="""
function functionName(newParam: string) {
    // Function body
}
""",
            filepath="path/to/file.ts",
        ),
    ]
)


@skill(
    prompt="""Append a parameter to a function retrieved from a file""",
    guide=True,
    uid="dbf2e2d0-491c-4c25-9c58-ed61d611a994",
)
class AddParameterToFunction(Skill, ABC):
    """This code snippet retrieves a specific function from a Python file in the codebase and adds a new parameter
    named 'new_param' of type 'int' to the function's parameter list.
    """

    @staticmethod
    @skill_impl(test_cases=[AddParameterToFunctionPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        function = codebase.get_file("path/to/file.py").get_function("function_name")

        # Add a new parameter to the function
        function.parameters.append("new_param: int")

    @staticmethod
    @skill_impl(test_cases=[AddParameterToFunctionTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        function = codebase.get_file("path/to/file.ts").get_function("functionName")

        # Add a new parameter to the function
        function.parameters.append("newParam: string")


ModifyDictionaryValuePyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
foo = {"example_key": "example_value"}
""",
            output="""
foo = {"example_key": "xyz"}
""",
            filepath="path/to/file.py",
        ),
    ]
)

ModifyDictionaryValueTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
const foo = {"example_key": "example_value"};
""",
            output="""
const foo = {"example_key": "xyz"};
""",
            filepath="path/to/file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to access and modify a global variable in a file.
    The snippet should include the following steps: 1) Retrieve a global variable named 'foo' from an example
    file path. 2) Access the value of a dictionary associated with the variable using a specific key, 'example_key',
    in two different ways. 3) Update the value of the dictionary for 'example_key' to 'xyz'.""",
    guide=True,
    uid="af9a2877-020a-4638-85a4-41515aa4c376",
)
class ModifyDictionaryValue(Skill, ABC):
    """This code snippet retrieves a global variable from a specified file in the codebase, accesses a specific key
    in its dictionary value, and updates that key's value to "xyz". It demonstrates two methods for retrieving the
    value associated with the key "example_key" from the dictionary.
    """

    @staticmethod
    @skill_impl(test_cases=[ModifyDictionaryValuePyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # var = {"example_key": "example_value"}
        # Find the symbol to modify
        var = codebase.get_file("path/to/file.py").get_global_var("foo")

        # Get the value of the dictionary for key "example_key"
        example = var.value["example_key"]
        assert example == "example_value"

        # Alternatively
        example = var.value.get("example_key", None)
        assert example == "example_value"

        # Set the value of the dictionary for key "example_key" to "xyz"
        var.value["example_key"] = '"xyz"'

    @staticmethod
    @skill_impl(test_cases=[ModifyDictionaryValueTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # var = {"example_key": "example_value"}
        # Find the symbol to modify
        var = codebase.get_file("path/to/file.ts").get_global_var("foo")

        # Get the value of the dictionary for key "example_key"
        example = var.value["example_key"]
        assert example == "example_value"

        # Alternatively
        example = var.value.get("example_key", None)
        assert example == "example_value"

        # Set the value of the dictionary for key "example_key" to "xyz"
        var.value["example_key"] = '"xyz"'


ConvertVariableToSchemaPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
var_name = {"key1": "value1", "key2": "value2", "excluded": "value3"}
""",
            output="""
var_name = Schema(key1=value1, key2=value2)
""",
            filepath="path/to/file.py",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that performs the following tasks: 1. Retrieve a global variable named
    'var_name' from a specified Python file located at 'path/to/file.py'. 2. Convert the value of this variable into
    a Schema format, ensuring that the keys and values are formatted correctly. 3. Provide an alternative method to
    convert the variable's value into a Schema format while excluding a specific key named 'excluded'.""",
    guide=True,
    uid="a6b53298-570a-4c6e-8b7a-8fcbc1bb5d87",
)
class ConvertVariableToSchema(Skill, ABC):
    """This code snippet retrieves a global variable from a specified file in the codebase and modifies its value by
    converting it into a Schema format. It provides two options for setting the value: one that includes all
    key-value pairs from the variable's current value, and another that excludes a specified key from the conversion.
    """

    @staticmethod
    @skill_impl(test_cases=[ConvertVariableToSchemaPyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        var = codebase.get_file("path/to/file.py").get_global_var("var_name")

        # Convert its assignment to a Schema and excludes certain keys
        var.set_value(f"Schema({', '.join(f'{k}={v}' for k, v in var.value.items() if k != 'excluded')})")


AppendToGlobalVariableListPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
foo = ["item1", "item2"]
""",
            output="""
foo = ["item1", "item2", "bar"]
""",
            filepath="path/to/file.py",
        ),
    ]
)

AppendToGlobalVariableListTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
const foo = ["item1", "item2"];
""",
            output="""
const foo = ["item1", "item2", "bar"];
""",
            filepath="path/to/file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that retrieves a global variable named 'foo' from a file located at
    'path/to/file' and appends a new item, 'bar', to that variable's value, which is expected to be a list/array.""",
    guide=True,
    uid="8c5aebf6-6e1b-47d1-b4a5-04e699775c62",
)
class AppendToGlobalVariableList(Skill, ABC):
    """This code snippet retrieves a global variable named 'var_name' from a specified file in the codebase and
    appends a new item, 'new_item', to the list stored in that variable.
    """

    @staticmethod
    @skill_impl(test_cases=[AppendToGlobalVariableListPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        var = codebase.get_file("path/to/file.py").get_global_var("foo")

        # Assert the type is List (a GraphSitter type)
        if not isinstance(var.value, List):
            msg = f"Expected a list, but found {type(var.value)}"
            raise ValueError(msg)

        # Append to the list
        var.value.append('"bar"')

    @staticmethod
    @skill_impl(test_cases=[AppendToGlobalVariableListTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        var = codebase.get_file("path/to/file.ts").get_global_var("foo")

        # Assert the type is List (a GraphSitter type, equivalent to an array in TypeScript)
        if not isinstance(var.value, List):
            msg = f"Expected an array, but found {type(var.value)}"
            raise ValueError(msg)

        # Append to the list
        var.value.append('"bar"')


CheckFunctionDecoratorPresencePyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
@cache
def function_name():
    pass

def another_function():
    pass
""",
            unchanged=True,
            filepath="path/to/file.py",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that retrieves a specific function from a Python file in a codebase and checks
    if that function has a decorator named '@cache'. The code should include the following steps: 1. Use a method to
    get the file from the codebase by providing the file path. 2. Retrieve the function by its name from the file. 3.
    Check if the function's decorators list contains the '@cache' decorator.""",
    guide=True,
    uid="f165c144-2164-437a-8741-72b75d5b4aa4",
)
class CheckFunctionDecoratorPresence(Skill, ABC):
    """Checks if a specific function in a Python file has a decorator named '@cache'. If the decorator is present,
    it proceeds with further actions (currently a placeholder with 'pass').
    """

    @staticmethod
    @skill_impl(test_cases=[CheckFunctionDecoratorPresencePyTestCase], language=ProgrammingLanguage.PYTHON)
    def skill_func(codebase: CodebaseType):
        # Find the symbol to modify
        function = codebase.get_file("path/to/file.py").get_function("function_name")

        # Check if the function has a decorator named "@cache"
        if "@cache" in function.decorators:
            print(f"Function: {function.name} has a @cache decorator")
