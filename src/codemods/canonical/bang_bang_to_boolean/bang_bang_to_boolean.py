from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a TypeScript codemod that transforms instances of '!!(expression)' into 'Boolean(expression)'. The codemod should search through all
TypeScript files in a codebase, using a regular expression to identify the pattern. Upon finding a match, it should replace '!!' with 'Boolean(' and
append a closing parenthesis to complete the transformation.""",
    uid="d1ece8d3-7da9-4696-9288-4087737e2952",
)
@canonical
class BangBangToBoolean(Codemod, Skill):
    """This codemod converts !!(expression) to Boolean(expression)"""

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase) -> None:
        # Regular expression pattern as a string to find '!!' followed by an identifier or any bracketed expression
        pattern = r"!!\s*(\w+|\([^\)]*\))"

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Check if the file is a TypeScript file
            if file.extension == ".ts":
                # Search for the pattern in the file's source code using the string pattern
                matches = file.search(pattern, include_strings=False, include_comments=False)
                for match in matches:
                    # Replace the '!!' with 'Boolean('
                    match.replace("!!", "Boolean(", count=1)
                    # Wrap the expression in closing parenthesis
                    match.insert_after(")", newline=False)
