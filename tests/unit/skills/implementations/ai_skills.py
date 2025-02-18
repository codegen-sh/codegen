from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile

########################################################################################################################
# Codebase AI Skills
########################################################################################################################


RefactorClassPyTestCase = SkillTestCase([SkillTestCasePyFile(input="class MyClass:\n    a: str = 'a'")], sanity=True)


@skill(eval_skill=False, prompt="Refactor MyClass to be shorter and more readable.", uid="ec037fb2-3a3c-4fd5-b17d-8720ea8a0881")
class RefactorClass(Skill, ABC):
    """This skill refactors the given class to be shorter and more readable.
    It uses codebase to first find the class, then uses codebase AI to refactor the class.
    This is a trivial case of using Codebase AI to edit and generate new code that will
    then be applied to the codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[RefactorClassPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        my_class = codebase.get_symbol("MyClass", optional=True)
        if my_class is None:
            msg = "MyClass not found in codebase"
            raise ValueError(msg)
        my_class.edit(codebase.ai("Refactor the class to be shorter and more readable.", target=my_class))


GenerateDocstringsPyTestCase = SkillTestCase([SkillTestCasePyFile(input="class MyClass:\n    def my_method(self):\n        pass")], sanity=True)


@skill(eval_skill=False, prompt="Generate docstrings for all my class methods.", uid="ef667b42-7349-4a8e-aafd-7dd554e642f5")
class GenerateDocstrings(Skill, ABC):
    """This skill generates docstrings for all class methods.
    This is another example of Codebase AI, where is it being used to generate
    textual content that will then be used as the docstring for the class methods.

    This is also an example usecase of the context feature, where additional context
    is provided to the AI to help it generate the docstrings.
    """

    @staticmethod
    @skill_impl(test_cases=[GenerateDocstringsPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        for cls in codebase.classes:
            for method in cls.methods:
                new_docstring = codebase.ai(
                    f"""Generate a new docstring for the method {method.name} in the class {cls.name}.""",
                    target=method,
                    context={"class": cls},
                )
                method.set_docstring(new_docstring)


WriteTestPyTestCase = SkillTestCase([SkillTestCasePyFile(input="def my_function():\n    pass")], sanity=True)


@skill(eval_skill=False, prompt="Write a test for my_function called test_my_function.", uid="8f613d11-1ced-4379-ab13-217412c29c5a")
class WriteTest(Skill, ABC):
    """This skill writes a test for the given function.
    This is an example of Codebase AI generating brand new code that will then
    be added to the codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[WriteTestPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        my_function = codebase.get_function("my_function", optional=True)
        if my_function is None:
            msg = "my_function not found in codebase"
            raise ValueError(msg)

        test_function = codebase.ai(f"Write a test for the function {my_function.name} called test_my_function.", target=my_function)
        my_function.insert_after(test_function)


RenameMethodsPyTestCase = SkillTestCase([SkillTestCasePyFile(input="class MyClass:\n    def add_one(a:int):\n        return a + 2")], sanity=True)


@skill(eval_skill=False, prompt="Rename all my existing class method names to something better.", uid="adbb28ec-4384-4bbd-9e1f-8e33829fca7d")
class RenameMethods(Skill, ABC):
    """This skill renames all class methods to something better.
    This is an example of Codebase AI generating content that is not
    directly written to the codebase as-in, but is chained and applied to the codebase
    in a later step.

    In this case, the agent is asked to create a new name for each class method, then
    the new name is used to rename the method in the codebase.
    """

    @staticmethod
    @skill_impl(test_cases=[RenameMethodsPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        for cls in codebase.classes:
            for method in cls.methods:
                new_name = codebase.ai(f"Create a better name for the method {method.name}.", target=method)
                method.rename(new_name)


FlagCodePyTestCase = SkillTestCase([SkillTestCasePyFile(input="class MyClass:\n    def add_one(a:int):\n        return a + 2 # <- this is a bug")], sanity=True)


# @skill(eval_skill=False, prompt="Flag all code that may have a potential bug.", uid="0c87766c-228a-49e5-be7e-ef67b2f634f5")
# class FlagCode(Skill, ABC):
#     """This skill uses flag_ai to flag all code that may have a potential bug.
#     This is an example of Codebase AI being used to flag code that meets a certain criteria.
#     """

#     @staticmethod
#     @skill_impl(test_cases=[FlagCodePyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
#     @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
#     def skill_func(codebase: CodebaseType):
#         for cls in codebase.classes:
#             for method in cls.methods:
#                 if codebase.flag_ai("Flag this symbol if you think it may have a potential bug.", target=method):
#                     method.flag()


# @skill(eval_skill=False, prompt="Rename all functions that are incorrect or misleading.", uid="c27017ff-43c5-4ace-b107-241ab2da4c7d")
# class FlagAndRename(Skill, ABC):
#     """This skill uses both flag_ai and ai to flag and rename all functions that are incorrect or misleading.
#     The first step is to use flag_ai to flag the functions that are incorrect or misleading.
#     Then, the second step is to use ai to generate a new name for the function.
#     Finally, the function is renamed in the codebase.

#     This is an example of how codebase.flag_ai and codebase.ai can be used together to achieve a more complex task.
#     """

#     @staticmethod
#     @skill_impl(test_cases=[RenameMethodsPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
#     @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
#     def skill_func(codebase: CodebaseType):
#         for cls in codebase.classes:
#             for method in cls.methods:
#                 if codebase.flag_ai("Flag this method if you think the name is incorrect or misleading.", target=method):
#                     new_name = codebase.ai(f"Create a better name for the method {method.name}.", target=method)
#                     method.rename(new_name)
