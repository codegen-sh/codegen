from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.placeholder.placeholder_type import TypePlaceholder
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

CountUntypedAttributesInCodebasePyTest = SkillTestCase(
    [
        SkillTestCasePyFile(
            input="""
class ClassWithMixedAttributes:
    untyped_attr1 = 10
    typed_attr1: int = 20
    untyped_attr2 = "Hello"
    typed_attr2: str = "World"

    def __init__(self):
        self.untyped_attr3 = []
        self.typed_attr3: list = []

class ClassWithOnlyUntypedAttributes:
    attr1 = 1
    attr2 = "Two"

    def __init__(self):
        self.attr3 = 3.0

class ClassWithOnlyTypedAttributes:
    attr1: int = 1
    attr2: str = "Two"

    def __init__(self):
        self.attr3: float = 3.0

class EmptyClass:
    pass
""",
            filepath="classes.py",
        ),
        SkillTestCasePyFile(
            input="""
class AnotherClass:
    untyped_attr = "Untyped"
    typed_attr: str = "Typed"
""",
            filepath="more_classes.py",
        ),
    ],
    sanity=True,
)

CountUntypedAttributesInCodebaseTSTest = SkillTestCase(
    [
        SkillTestCaseTSFile(
            input="""
class ClassWithMixedAttributes {
    untypedAttr1 = 10;
    typedAttr1: number = 20;
    untypedAttr2 = "Hello";
    typedAttr2: string = "World";

    constructor() {
        this.untypedAttr3 = [];
        this.typedAttr3: any[] = [];
    }
}

class ClassWithOnlyUntypedAttributes {
    attr1 = 1;
    attr2 = "Two";

    constructor() {
        this.attr3 = 3.0;
    }
}

class ClassWithOnlyTypedAttributes {
    attr1: number = 1;
    attr2: string = "Two";

    constructor() {
        this.attr3: number = 3.0;
    }
}

class EmptyClass {}
""",
            filepath="classes.ts",
        ),
        SkillTestCaseTSFile(
            input="""
class AnotherClass {
    untypedAttr = "Untyped";
    typedAttr: string = "Typed";
}
""",
            filepath="more_classes.ts",
        ),
    ],
    sanity=True,
)


@skill(
    prompt="""Generate a code snippet that iterates through all files in a codebase, and for each file,
    iterates through all classes within that file. For each class, count the number of attributes that do not have a
    type specified. Finally, print the total count of untyped attributes.""",
    guide=True,
    uid="ab608bb6-7731-4f3a-9fc8-4a467561532c",
)
class CountUntypedAttributesInCodebase(Skill, ABC):
    """Counts the number of untyped attributes across all classes in the codebase. It iterates through each file in
    the codebase, then through each class in those files, and sums up the attributes that do not have a specified
    type. Finally, it prints the total count of untyped attributes.
    """

    @staticmethod
    @skill_impl(test_cases=[CountUntypedAttributesInCodebasePyTest], language=ProgrammingLanguage.PYTHON)
    @skill_impl(test_cases=[CountUntypedAttributesInCodebaseTSTest], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        untyped_attributes_count = 0
        typed_attributes_count = 0

        # Iterate through all classes in the file
        for cls in codebase.classes:
            # Count the number of attributes that are not typed
            untyped_attributes_count += sum(1 for attr in cls.attributes if isinstance(attr.assignment.type, TypePlaceholder))
            typed_attributes_count += sum(1 for attr in cls.attributes if not isinstance(attr.assignment.type, TypePlaceholder))

        print(f"# untyped: {untyped_attributes_count}")
        print(f"# typed: {typed_attributes_count}")
