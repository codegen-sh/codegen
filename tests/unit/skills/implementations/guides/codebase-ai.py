from abc import ABC
from typing import TYPE_CHECKING

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function

MethodSummaryGeneratorPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class MyClass:
    def target_method(self):
        '''Old summary'''
        pass

def call_target_method():
    obj = MyClass()
    obj.target_method()
"""
        )
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a new one-line summary or description for the specified method, considering the context of its
    parent class and its call sites. The tone of the summary should be either formal or informal based on the
    provided parameter.""",
    guide=True,
    uid="6e92719e-7371-44bd-b1e4-fffd70b5c3c8",
)
class MethodSummaryGenerator(Skill, ABC):
    """Generates a new one-line summary or description for the specified method based on its context, including the
    parent class and call sites.
    """

    @staticmethod
    @skill_impl(test_cases=[MethodSummaryGeneratorPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # get the method and its parent class
        method: Function = codebase.get_class("MyClass").get_method("target_method")
        parent_class = method.parent

        summary = codebase.ai(
            prompt="Generate a new one-line summary / description for this method.",
            target=method,
            context={
                "Parent Class": parent_class,
                "Callsites": method.call_sites,
                "Tone": "formal",
            },
        )

        print(summary)


FlagRestrictedMethodPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class MyClass:
    def target_method(self):
        '''This method contains restricted words'''
        words = ["to", "restrict"]
        print("This method is quite long and contains words to restrict")

def another_method():
    pass
"""
        )
    ],
    sanity=True,
)


# @skill(
#     prompt="""Generate a code snippet that defines a method to flag another method based on specific criteria. The
#     method should check if the target method contains any restricted words from a provided list or if its length
#     exceeds a certain limit. The flagging should be done using a function called `flag_ai`, which takes a message,
#     the method to be flagged, and a context dictionary containing the parent class and the list of restricted words.""",
#     guide=True,
#     uid="d4b9998f-3594-4b67-859e-6dc58c849b53",
# )
# class FlagRestrictedMethod(Skill, ABC):
#     """Flags the method if it contains any restricted words or exceeds a specified length. The context includes
#     information about the parent class and the list of restricted words.
#     """

#     @staticmethod
#     @skill_impl(test_cases=[FlagRestrictedMethodPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
#     @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
#     def skill_func(codebase: CodebaseType):
#         # get the method and its parent class
#         method: Function = codebase.get_class("MyClass").get_method("target_method")
#         parent_class = method.parent

#         # Define the restricted words
#         restricted_words = ["words", "to", "restrict"]

#         if codebase.flag_ai(
#             "Flag this method if it contains a restricted word or if it is too long.",
#             target=method,
#             context={
#                 "Parent Class": parent_class,
#                 "Restricted Words": restricted_words,
#             },
#         ):
#             # Operate on the method here
#             print(f"{method.name} has been flagged.")


FunctionDecompositionPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def large_function():
    print("Step 1")
    print("Step 2")
    print("Step 3")
    print("Step 4")
    print("Step 5")
"""
        )
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that retrieves a function named 'large_function' from a codebase, then uses an
    AI tool to break this function into smaller functions, and finally edits the original 'large_function' with the
    newly created smaller functions.""",
    guide=True,
    uid="cad3f90d-d445-4ea9-9fb4-70368763e765",
)
class FunctionDecomposition(Skill, ABC):
    """This code snippet retrieves a function named 'large_function' from the codebase and then uses an AI tool to
    break it up into smaller, more manageable functions. Finally, it edits the original 'large_function' with the
    newly created smaller functions.
    """

    @staticmethod
    @skill_impl(test_cases=[FunctionDecompositionPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Get the large function
        large_function = codebase.get_function("large_function")

        # Split the function into smaller functions
        broken_up_function = codebase.ai(
            "Break up this function into smaller functions.",
            target=large_function,
        )

        large_function.edit(broken_up_function)


DocstringGeneratorPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_without_docstring():
    pass

def function_with_docstring():
    '''This is a docstring'''
"""
        )
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that loops through all methods in a codebase, generates a new one-line summary
    or description for each function using an AI model, and then adds the generated docstring to the respective
    function.""",
    guide=True,
    uid="486171b3-039d-496a-944c-c00fd56bc4d6",
)
class DocstringGenerator(Skill, ABC):
    """Loops through all functions in the codebase, generates a new one-line summary or description for each function
    using an AI model, and sets the generated docstring for the respective function.
    """

    @staticmethod
    @skill_impl(test_cases=[DocstringGeneratorPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Loop through all functions in the codebase
        for function in codebase.functions:
            # Generate a new docstring for the function
            docstring = codebase.ai(
                "Generate a new one-line summary / description for this function.",
                target=function,
            )
            # Add the docstring to the function
            function.set_docstring(docstring)


DocstringFormatterPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_without_docstring():
    pass

def function_with_docstring():
    '''This is a docstring'''
"""
        )
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that loops through all functions in a codebase, converts each function's
    docstring to the Google style docstring format using an AI tool, and then sets the converted docstring back to
    the respective function.""",
    guide=True,
    uid="a2bff776-9d53-4297-9b43-935cc2104c47",
)
class DocstringFormatter(Skill, ABC):
    """Loops through all functions in the codebase and converts their docstrings to the Google style docstring
    format, updating each function with the new docstring.
    """

    @staticmethod
    @skill_impl(test_cases=[DocstringFormatterPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Loop through all functions in the codebase
        for function in codebase.functions:
            # Convert the docstring to the new format
            docstring = codebase.ai(
                "Convert the docstring to the Google style docstring format.",
                target=function,
            )
            # Add the docstring to the function
            function.set_docstring(docstring)


FlagUndocumentedFunctionsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def undocumented_function():
    pass
"""
        )
    ],
    sanity=True,
)


# @skill(
#     prompt="""Generate a code snippet that iterates through all functions in a codebase. For each function,
#     check if it lacks sufficient documentation using a flagging mechanism. If a function is flagged, add a comment
#     indicating that documentation needs to be added, assigning the task to a specific user.""",
#     guide=True,
#     uid="fcf7e563-7ca0-4cec-8f4e-942feba6c406",
# )
# class FlagUndocumentedFunctions(Skill, ABC):
#     """Checks if the specified function has sufficient documentation in the codebase. If not, it flags the function
#     and adds a comment indicating that documentation needs to be added.
#     """

#     @staticmethod
#     @skill_impl(test_cases=[FlagUndocumentedFunctionsPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
#     @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
#     def skill_func(codebase: CodebaseType):
#         for function in codebase.functions:
#             if codebase.flag_ai(
#                 "Flag this function if it does not include enough documentation in the codebase.",
#                 target=function,
#             ):
#                 function.add_comment("TODO @johndoe: Add documentation to this function.")


RenameMisleadingSymbolsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def get_user_info(user: User):
    return user.user_details

def get_user_details(user: User):
    return user.user_status
"""
        )
    ],
    sanity=True,
)


# @skill(
#     prompt="""Generate a code snippet that iterates through all functions in a codebase. For each function,
#     check if the name of the function is misleading or incorrect using a flagging mechanism. If flagged,
#     use an AI tool to generate a new name for the function and rename it accordingly.""",
#     guide=True,
#     uid="fc46b5f9-ef12-4f96-8674-0e1917102b74",
# )
# class RenameMisleadingSymbols(Skill, ABC):
#     """This function checks if the name of a given symbol is incorrect or misleading. If so, it generates a new name
#     for the symbol using an AI service and renames the function accordingly.
#     """

#     @staticmethod
#     @skill_impl(test_cases=[RenameMisleadingSymbolsPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
#     @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
#     def skill_func(codebase: CodebaseType):
#         for function in codebase.functions:
#             if codebase.flag_ai("Flag this symbol if the name of the symbol is wrong or misleading.", target=function):
#                 new_name = codebase.ai("Generate a new name for this symbol.", target=function)
#                 function.rename(new_name)
