from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

########################################################################################################################
# ADD FUNCTION DECORATOR
########################################################################################################################

test_cases = [
    SkillTestCase(
        files=[
            SkillTestCasePyFile(input="def my_function():\n    pass", output="from my_decorator_module import my_decorator\n@my_decorator\ndef my_function():\n    pass", filepath="file1.py"),
            SkillTestCasePyFile(
                input="def my_decorator(func):\n    def wrapper(*args, **kwargs):\n        return func(*args, **kwargs)\n    return wrapper\n",
                output="def my_decorator(func):\n    def wrapper(*args, **kwargs):\n        return func(*args, **kwargs)\n    return wrapper\n",
                filepath="my_decorator_module.py",
            ),
        ]
    ),
    SkillTestCase(
        files=[
            SkillTestCasePyFile(
                input="class MyClass:\n    def my_method(self):\n        pass",
                output="from my_decorator_module import my_decorator\nclass MyClass:\n    @my_decorator\n    def my_method(self):\n        pass",
                filepath="file1.py",
            ),
            SkillTestCasePyFile(
                input="def my_decorator(func):\n    def wrapper(*args, **kwargs):\n        return func(*args, **kwargs)\n    return wrapper\n",
                output="def my_decorator(func):\n    def wrapper(*args, **kwargs):\n        return func(*args, **kwargs)\n    return wrapper\n",
                filepath="my_decorator_module.py",
            ),
        ]
    ),
]


@skill(prompt="Add the following decorator to all functions and methods: '@my_decorator'", uid="c1452d22-c8f7-4c58-8bc5-d026a8ef4a86")
class AddDecoratorToFunction(Skill, ABC):
    """Adds a specified decorator to all functions and methods in a codebase, ensuring that it is not already present, and handles the necessary imports for the decorator."""

    @staticmethod
    @skill_impl(test_cases, language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Adds a decorator to each function or method in the codebase if they do not already have it."""
        # get the decorator symbol
        decorator_symbol = codebase.get_symbol("my_decorator")

        # iterate through each file
        for file in codebase.files:
            # if the file does not have the decorator symbol and the decorator symbol is not in the same file
            if not file.has_import(decorator_symbol.name) and decorator_symbol.file != file:
                # import the decorator symbol
                file.add_symbol_import(decorator_symbol)

            # iterate through each function in the file
            for function in file.functions:
                # if the function is the decorator symbol, skip
                if function == decorator_symbol:
                    continue
                # add the decorator to the function, don't add the decorator if it already exists
                function.add_decorator(f"@{decorator_symbol.name}", skip_if_exists=True)
            # iterate through each class in the file
            for cls in file.classes:
                # iterate through each method in the class
                for method in cls.methods:
                    # add the decorator to the method, don't add the decorator if it already exists
                    method.add_decorator(f"@{decorator_symbol.name}", skip_if_exists=True)

    @staticmethod
    @skill_impl(test_cases=[], ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """TODO: Implement this method @Rishi Desai"""
        ...


py_input = '''
class MyClass:
    @with_user
    def my_method(self):
        """This is a method"""
        print('This is a method')
'''

py_output = '''
class MyClass:
    @with_user
    def my_method(self):
        """This is a method
            OPERATES ON USER DATA
        """
        print('This is a method')
'''

ts_input = """
class MyClass {
    /**
     * This is a method
     */
    @withUser
    public myMethod(): void {
        console.log('This is a method');
    }
}
"""

ts_output = """
class MyClass {
    /**
     * This is a method
     * OPERATES ON USER DATA
     */
    @withUser
    public myMethod(): void {
        console.log('This is a method');
    }
}
"""

py_test_cases = [SkillTestCase(files=[SkillTestCasePyFile(input=py_input, output=py_output)])]
ts_test_cases = [SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input, output=ts_output)])]


@skill(uid="331d5b5d-cb6c-4cdb-8296-325ed27d73b9")
class UpdateDocStringOfDecoratedMethods(Skill, ABC):
    """Updates the docstring of methods whose decorator has with_user/withUser in their name by appending 'OPERATES ON USER DATA'."""

    @staticmethod
    @skill_impl(
        test_cases=py_test_cases,
        language=ProgrammingLanguage.PYTHON,
        prompt="Update the docstring of class methods if it has a decarators containing `with_user` in its name by appending 'OPERATES ON USER DATA'.",
    )
    def python_skill_func(codebase: CodebaseType):
        for cls in codebase.classes:
            for method in cls.methods:
                if method.decorators and any(["with_user" in dec.name for dec in method.decorators]):
                    method.set_docstring(f"{method.docstring.text}\nOPERATES ON USER DATA")

    @staticmethod
    @skill_impl(
        test_cases=ts_test_cases,
        language=ProgrammingLanguage.TYPESCRIPT,
        prompt="Update the docstring of class methods if it has a decarators containing `withUser` in its name by appending 'OPERATES ON USER DATA'.",
    )
    def typescript_skill_func(codebase: CodebaseType):
        for cls in codebase.classes:
            for method in cls.methods:
                if method.decorators and any(["withUser" in dec.name for dec in method.decorators]):
                    current_docstring = method.docstring.text if method.docstring else ""
                    new_docstring = f"{current_docstring}\nOPERATES ON USER DATA" if current_docstring else "OPERATES ON USER DATA"
                    method.set_docstring(new_docstring)
