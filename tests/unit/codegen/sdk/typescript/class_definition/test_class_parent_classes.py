from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parent_classes_single(tmpdir) -> None:
    SUBCLASS = "test.ts"
    # language=typescript
    SUBCLASS_CONTENT = """
import {Animal} from "./animal";
class Dog extends Animal {
    bark() {
        console.log("Woof! Woof!");
    }
}
"""
    PARENT = "animal.ts"
    # language=typescript
    PARENT_CONTENT = """
export class Animal {
    eat() {
        console.log("Nom nom nom");
    }
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={SUBCLASS: SUBCLASS_CONTENT.strip(), PARENT: PARENT_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(SUBCLASS)
        dog_class = file.get_class("Dog")
        assert dog_class.superclasses
        assert len(dog_class.superclasses) == 1
        assert dog_class.superclasses[0].name == "Animal"
