from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

RenameFunctionAndUpdateReferencesPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""def old_function_name():
    pass

def foo():
    old_function_name()
""",
            output="""def new_function_name():
    pass

def foo():
    new_function_name()
""",
            filepath="path/to/file.py",
        )
    ]
)

RenameFunctionAndUpdateReferencesTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""function old_function_name() {
    return "string";
}

function foo() {
    old_function_name();
}
""",
            output="""function new_function_name() {
    return "string";
}

function foo() {
    new_function_name();
}
""",
            filepath="path/to/file.ts",
        )
    ]
)


@skill(
    eval_skill=False,
    prompt="""Generate a code snippet that performs the following tasks: 1. Retrieve a function named
    'old_function_name' from a specified file located at 'path/to/file'. 2. Rename the retrieved function
    to 'new_function_name' and ensure that all references to the old function name are updated accordingly.""",
    guide=True,
    uid="df4a7075-7b8a-4f16-8543-6dce4aa29f32",
)
class RenameFunctionAndUpdateReferences(Skill, ABC):
    """Renames a specified function in a codebase and updates all its references. The function is retrieved from a
    given file path, and its name is changed from 'old_function_name' to 'new_function_name'.
    """

    @staticmethod
    @skill_impl(test_cases=[RenameFunctionAndUpdateReferencesPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        # Find the symbol to rename
        old_function = codebase.get_file("path/to/file.py").get_function("old_function_name")

        # Rename the function and update all references
        old_function.rename("new_function_name")

    @staticmethod
    @skill_impl(test_cases=[RenameFunctionAndUpdateReferencesTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        # Find the symbol to rename
        old_function = codebase.get_file("path/to/file.ts").get_function("old_function_name")

        # Rename the function and update all references
        old_function.rename("new_function_name")


@skill(
    prompt="""Generate a code snippet that demonstrates how to rename a function in a codebase using a hypothetical
    API. The snippet should include the following steps: 1. Retrieve a function by its old name from a specified file
    path. 2. Rename the function to a new name. 3. Automatically update all call sites of the function to reflect the
    new name. 4. Print the source of each call site to show the updated function name.""",
    guide=True,
    uid="d40a6350-49b1-492d-a47d-0cd92e945ed8",
)
class AutoRenameFunction(Skill, ABC):
    """Renames a function in the codebase and updates all its call sites. The function is retrieved from a specified
    file, and its name is changed to a new name. After renaming, all call sites that reference the function are
    automatically updated to reflect the new name, and the updated call site source code is printed.
    """

    @staticmethod
    @skill_impl(test_cases=[RenameFunctionAndUpdateReferencesPyTestCase], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        function = codebase.get_file("path/to/file.py").get_function("old_function_name")
        function.rename("new_function_name")

        # All call sites are automatically updated
        for call_site in function.call_sites:
            # The call_site will now use the new name
            print(call_site.source)  # This will show "new_name(...)"

    @staticmethod
    @skill_impl(test_cases=[RenameFunctionAndUpdateReferencesTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        function = codebase.get_file("path/to/file.ts").get_function("old_function_name")
        function.rename("new_function_name")

        # All call sites are automatically updated
        for call_site in function.call_sites:
            # The call_site will now use the new name
            print(call_site.source)  # This will show "new_name(...)"


AutoRenameClassPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class OldClassName:
    def old_method(self):
        pass

foo = OldClassName()
""",
            output="""
class NewClassName:
    def old_method(self):
        pass

foo = NewClassName()
""",
            filepath="path/to/file.py",
        )
    ]
)

AutoRenameClassTSTestCase = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
class OldClassName {
    old_method() {
        return "string";
    }
}

const foo = new OldClassName();
""",
            output="""
class NewClassName {
    old_method() {
        return "string";
    }
}

const foo = new NewClassName();
""",
            filepath="path/to/file.ts",
        )
    ]
)


@skill(
    prompt="""Generate a code snippet that demonstrates how to rename a class in a codebase using a hypothetical API.
    The snippet should include the following steps: 1. Retrieve a class named 'OldClassName' from a specified file
    path. 2. Rename the class to 'NewClassName'. 3. Automatically update all references to the renamed class. 4.
    Iterate through the usages of the renamed class and print the source of each usage, ensuring that the output
    reflects the new class name.""",
    guide=True,
    uid="3d2152ef-23fd-48c9-bcef-7deff9b4d6db",
)
class AutomaticClassRenamingWithReferenceUpdate(Skill, ABC):
    """Renames a class in the codebase and updates all its references.

    This code snippet retrieves a class named 'OldClassName' from a specified file, renames it to 'NewClassName',
    and then iterates through all usages of the class. Each usage is printed, showing the updated class name
    'NewClassName' instead of the old name.
    """

    @staticmethod
    @skill_impl(test_cases=[AutoRenameClassPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[AutoRenameClassTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        old_class = codebase.get_class("OldClassName")
        old_class.rename("NewClassName")

        # All references are automatically updated
        for usage in old_class.symbol_usages:
            # This could be a subclass, an instantiation, or any other reference
            print(usage.source)  # This will show "NewClassName" instead of "OldClassName"


RemoveDeprecatedPrefixfromFunctionsPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
def deprecated_old_function():
    pass

def normal_function():
    pass

def deprecated_another_old_function():
    pass
""",
            output="""
def old_function():
    pass

def normal_function():
    pass

def another_old_function():
    pass
""",
            filepath="path/to/file.py",
        ),
    ]
)


RemoveDeprecatedPrefixfromFunctionsTSTestCase = SkillTestCase(
    files=[
        SkillTestCaseTSFile(
            input="""
function deprecated_oldFunction(): void {
    console.log("Old function");
}

function normalFunction(): void {
    console.log("Normal function");
}

function deprecated_anotherOldFunction(): string {
    return "Another old function";
}
""",
            output="""
function oldFunction(): void {
    console.log("Old function");
}

function normalFunction(): void {
    console.log("Normal function");
}

function anotherOldFunction(): string {
    return "Another old function";
}
""",
        )
    ]
)


@skill(
    prompt="""Generate a code snippet that iterates through all files in a codebase. For each file, iterate through
    its functions and check if the function name starts with 'deprecated_'. If it does, create a new name by removing
    the 'deprecated_' prefix and rename the function to this new name.""",
    guide=True,
    uid="577e22de-b0c7-4281-8f3b-8c1c07b5e824",
)
class RemoveDeprecatedPrefixfromFunctions(Skill, ABC):
    """Iterates through all files in the codebase and checks each function's name. If a function's name starts with
    'deprecated_', it renames the function by removing the 'deprecated_' prefix.
    """

    @staticmethod
    @skill_impl(test_cases=[RemoveDeprecatedPrefixfromFunctionsPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RemoveDeprecatedPrefixfromFunctionsTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        # Iterate over all codebase functions
        for function in codebase.functions:
            # Filter for functions starting with deprecated_
            if function.name.startswith("deprecated_"):
                # Remove the deprecated_ prefix
                new_name = function.name.replace("deprecated_", "")
                function.rename(new_name)


RenameMethodPyTestCase = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class BaseClass:
    def old_method(self):
        print("Base old method")

class SubClass1(BaseClass):
    def old_method(self):
        print("SubClass1 old method")

class SubClass2(BaseClass):
    pass

class SubClass3(BaseClass):
    def old_method(self):
        print("SubClass3 old method")
""",
            output="""
class BaseClass:
    def new_method(self):
        print("Base old method")

class SubClass1(BaseClass):
    def new_method(self):
        print("SubClass1 old method")

class SubClass2(BaseClass):
    pass

class SubClass3(BaseClass):
    def new_method(self):
        print("SubClass3 old method")
""",
            filepath="base.py",
        ),
    ]
)

RenameMethodTSTestCase = SkillTestCase(
    files=[
        SkillTestCaseTSFile(
            input="""
class BaseClass {
    old_method(): void {
        console.log("Base old method");
    }
}

class SubClass1 extends BaseClass {
    old_method(): void {
        console.log("SubClass1 old method");
    }
}

class SubClass2 extends BaseClass {}

class SubClass3 extends BaseClass {
    old_method(): void {
        console.log("SubClass3 old method");
    }
}
""",
            output="""
class BaseClass {
    new_method(): void {
        console.log("Base old method");
    }
}

class SubClass1 extends BaseClass {
    new_method(): void {
        console.log("SubClass1 old method");
    }
}

class SubClass2 extends BaseClass {}

class SubClass3 extends BaseClass {
    new_method(): void {
        console.log("SubClass3 old method");
    }
}
""",
            filepath="base.ts",
        )
    ]
)


@skill(
    prompt="""Generate a code snippet that performs the following tasks: 1. Retrieve a class named 'BaseClass' from a
    file named 'base.py' in a codebase. 2. Get a method named 'old_method' from 'BaseClass'. 3. Rename 'old_method'
    to 'new_method' in 'BaseClass'. 4. Iterate through all subclasses of 'BaseClass' and check if they have a method
    named 'old_method'. 5. If they do, rename 'old_method' to 'new_method' in those subclasses.""",
    guide=True,
    uid="2a1ec775-daab-46dc-a2e1-6b8fd910d263",
)
class RenameMethodInBaseAndSubclasses(Skill, ABC):
    """Renames a method in the base class and updates all its subclasses.

    This code snippet retrieves the base class from a specified file and accesses a method named 'old_method'. It
    then renames this method to 'new_method' in the base class. Subsequently, it iterates through all subclasses of
    the base class, checking if they contain the 'old_method'. If they do, it renames 'old_method' to 'new_method' in
    each subclass.
    """

    @staticmethod
    @skill_impl(test_cases=[RenameMethodPyTestCase], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[RenameMethodTSTestCase], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        base_class = codebase.get_class("BaseClass")
        old_method = base_class.get_method("old_method")

        # Rename in base class
        old_method.rename("new_method")

        # Update in all subclasses
        for subclass in base_class.subclasses:
            if old_method := subclass.get_method("old_method"):
                old_method.rename("new_method")
