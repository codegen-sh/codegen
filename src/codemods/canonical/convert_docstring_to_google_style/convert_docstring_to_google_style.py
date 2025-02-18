from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a Python codemod class named `ConvertDocstringToGoogleStyle` that inherits from `Codemod` and `Skill`. The class should have a docstring
explaining its purpose: converting docstrings of functions and classes to Google style if they aren't already. The `execute` method should iterate
over the functions in a given `codebase`, check if each function has a docstring, and if so, convert it to Google style using a method
`to_google_docstring`.""",
    uid="99da3cd9-6ba8-4a4e-8ceb-8c1b2a60562d",
)
@canonical
class ConvertDocstringToGoogleStyle(Codemod, Skill):
    """This codemod converts docstrings on any function or class to Google docstring style if they aren't already.

    A Google docstring style is one that specifies the args, return value, and raised exceptions in a structured format.
    """

    language = ProgrammingLanguage.PYTHON

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.PYTHON)
    def execute(self, codebase: Codebase) -> None:
        for function in codebase.functions:
            if (docstring := function.docstring) is not None:
                function.set_docstring(docstring.to_google_docstring(function))
