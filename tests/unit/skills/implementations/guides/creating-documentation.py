import textwrap
from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

UpdateFunctionDocstringPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def my_function():
    '''Old docstring.'''
    pass
""",
            output="""
def my_function():
    '''Hello, world!'''
    pass
""",
            filepath="path/to/file.py",
        ),
    ]
)

UpdateFunctionDocstringTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
/* Old docstring. */
function myFunction(): void {
    return "Hello, world!";
}
""",
            output="""
/* Hello, world! */
function myFunction(): void {
    return "Hello, world!";
}
""",
            filepath="path/to/file.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that retrieves a specific function from a file in a codebase and updates its
docstring to a new value.""",
    guide=True,
    uid="19db38ad-38a6-4b1e-b6f6-ece73ec7a97c",
)
class UpdateFunctionDocstring(Skill, ABC):
    """Retrieves a specific function from a file in the codebase and updates its docstring to a new value."""

    @staticmethod
    @skill_impl(test_cases=[UpdateFunctionDocstringPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Get a specific function
        function = codebase.get_file("path/to/file.py").get_function("my_function")
        # Update its docstring
        function.set_docstring("Hello, world!")

    @staticmethod
    @skill_impl(test_cases=[UpdateFunctionDocstringTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Get a specific function
        function = codebase.get_file("path/to/file.ts").get_function("myFunction")
        # Update its docstring
        function.set_docstring("Hello, world!")


CalculateDocumentationCoveragePyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def func1():
    \"\"\"Documented function.\"\"\"
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    return a + b + c + d + e

def func2():
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    return a + b + c + d + e

def short_func():
    pass
""",
            filepath="example.py",
        ),
    ],
    sanity=True,
)

CalculateDocumentationCoverageTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function func1() {
    /**
     * Documented function.
     */
    const a = 1;
    const b = 2;
    const c = 3;
    const d = 4;
    const e = 5;
    return a + b + c + d + e;
}

function func2() {
    const a = 1;
    const b = 2;
    const c = 3;
    const d = 4;
    const e = 5;
    return a + b + c + d + e;
}

function shortFunc() {
    // Short function
}
""",
            filepath="example.ts",
        )
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a Python code snippet that initializes counters for total and documented functions/classes.
    The code should iterate over all functions in a given codebase, checking if each function has more than 5 lines
    of code. If so, it should increment the total count. Additionally, it should check if the function has a
    docstring and increment the documented count accordingly. Finally, calculate the documentation coverage
    percentage and print it in a formatted string.""",
    guide=True,
    uid="ad9ffd9e-5cbe-467b-bd97-d12849ab16fe",
)
class CalculateDocumentationCoverage(Skill, ABC):
    """Calculates the documentation coverage percentage of functions in a codebase. It initializes counters for total
    and documented functions, iterates through all functions, and checks if each function has more than five lines of
    code. If so, it increments the total count and checks for the presence of a docstring, incrementing the
    documented count accordingly. Finally, it computes and prints the documentation coverage as a percentage.
    """

    @staticmethod
    @skill_impl(test_cases=[CalculateDocumentationCoveragePyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[CalculateDocumentationCoverageTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Initialize counters for total and documented functions/classes
        count_total = 0
        count_documented = 0

        # Iterate over all functions in the codebase
        for function in codebase.functions:
            # Check if the function has more than 5 lines
            if len(function.source.splitlines()) > 5:
                count_total += 1  # Increment total count
                # Check if the function has a docstring
                if function.docstring is not None:
                    count_documented += 1  # Increment documented count

        # Calculate documentation coverage percentage
        coverage_percentage = (count_documented / count_total) * 100
        print(f"Documentation coverage: {coverage_percentage:.2f}%")


DocstringEnhancerPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_with_docstring():
    '''This is an existing docstring.'''
    pass

def function_without_docstring():
    pass
""",
            filepath="example.py",
        ),
    ],
    sanity=True,
)

DocstringEnhancerTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function functionWithDocstring() {
    /**
     * This is an existing docstring.
     */
}

function functionWithoutDocstring() {
}
""",
            filepath="example.ts",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that iterates through all files in a codebase, and for each function in those
    files, checks if a docstring exists. If a docstring exists, update it to be more descriptive using an AI model,
    appending the current date to the updated docstring. If no docstring exists, create a new one using the AI model,
    also appending the creation date. Finally, set the new or updated docstring for the function.""",
    guide=True,
    uid="97b40839-7c21-49e8-afc3-23875e962b85",
)
class DocstringEnhancer(Skill, ABC):
    """Iterates through all files in the codebase and processes each function's docstring. If a function already has
    a docstring, it updates it to be more descriptive; otherwise, it adds a new docstring. The updated or newly
    created docstring includes a timestamp indicating when the change was made.
    """

    @staticmethod
    @skill_impl(test_cases=[DocstringEnhancerPyTestCase], skip_test=True, language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[DocstringEnhancerTSTestCase], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        for function in codebase.functions:
            current_docstring = function.docstring
            if current_docstring:
                # Update existing docstring
                new_docstring = codebase.ai(f"Update the docstring for {function.name} to be more descriptive.", target=function)
                new_docstring += "\n\nUpdated on: Sept 11, 2024"
            else:
                # Add new docstring
                new_docstring = codebase.ai(f"Add a docstring for {function.name}.", target=function)
                new_docstring += "\n\nCreated on: Sept 11, 2024"
            function.set_docstring(new_docstring)


StaticDocstringGeneratorPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def function_with_params(param1, param2):
    pass

def function_without_params():
    pass

def function_with_existing_docstring():
    '''This docstring should not be modified.'''
    pass
""",
            output="""
def function_with_params(param1, param2):
    '''Docstring for function_with_params.

    Args:
        param1, param2

    Returns:
        Description of the return value
    '''
    pass

def function_without_params():
    '''Docstring for function_without_params.

    Args:


    Returns:
        Description of the return value
    '''
    pass

def function_with_existing_docstring():
    '''This docstring should not be modified.'''
    pass
""",
            filepath="example.py",
        ),
    ]
)

StaticDocstringGeneratorTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
function functionWithParams(param1: string, param2: number) {
    return "Hello, world!";
}

function functionWithoutParams() {
    return "Hello, world!";
}
/**
* This docstring should not be modified.
*/
function functionWithExistingDocstring() {

    return "Hello, world!";
}
""",
            output="""
/**
* Docstring for functionWithParams.
*
* Args:
*     param1, param2
*
* Returns:
*     Description of the return value
*/
function functionWithParams(param1: string, param2: number) {
    return "Hello, world!";
}
/**
* Docstring for functionWithoutParams.
*
* Args:
*
*
* Returns:
*     Description of the return value
*/
function functionWithoutParams() {
    return "Hello, world!";
}
/**
* This docstring should not be modified.
*/
function functionWithExistingDocstring() {
    return "Hello, world!";
}
""",
            filepath="example.ts",
        ),
    ]
)


@skill(
    prompt="""Generate a code snippet that iterates through a list of functions in a codebase. For each function,
    check if it has a docstring. If it does not, create a new docstring that includes the function's name,
    a list of its parameters, and a description of the return value. Finally, set the newly created docstring for the
    function.""",
    guide=True,
    uid="6b75f5be-b2af-4960-8419-83d2fc8610a7",
)
class StaticDocstringGenerator(Skill, ABC):
    """Generates a docstring for a function if it does not already have one. The docstring includes the function's
    name, a list of its parameters, and a placeholder for the return value description.
    """

    @staticmethod
    @skill_impl(test_cases=[StaticDocstringGeneratorPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[StaticDocstringGeneratorTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate through all functions in the codebase
        for function in codebase.functions:
            # Check if the function has a docstring
            if not function.docstring:
                # Create a new docstring
                updated_docstring = textwrap.dedent(f"""
    Docstring for {function.name}.

    Args:
        {", ".join(param.name for param in function.parameters)}

    Returns:
        Description of the return value
                """)
                # Set the new docstring for the function
                function.set_docstring(updated_docstring)
