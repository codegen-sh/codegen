from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_interface_dependencies_includes_extends(tmpdir) -> None:
    file = """
interface Animal {
  name: string;
  age: number;
  makeSound(): void;
}

interface Dog extends Animal {
  breed: string;
  wagTail(): void;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 2
        assert symbols[0].name == "Animal"
        assert symbols[1].name == "Dog"
        interface_with_dependencies = symbols[1]
        assert len(interface_with_dependencies.dependencies) == 1
        assert interface_with_dependencies.dependencies[0].name == "Animal"


def test_interface_dependencies_includes_implements(tmpdir) -> None:
    file = """
interface Animal {
  name: string;
  age: number;
  makeSound(): void;
}

interface Dog extends Animal {
  breed: string;
  wagTail(): void;
}

export class Labrador implements Dog {
  name: string;
  age: number;
  breed: string;

  constructor(name: string, age: number, breed: string) {
    this.name = name;
    this.age = age;
    this.breed = breed;
  }

  makeSound(): void {
    console.log("Woof!");
  }

  wagTail(): void {
    console.log("Wagging tail...");
  }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 3
        assert symbols[0].name == "Animal"
        assert symbols[1].name == "Dog"
        assert symbols[2].name == "Labrador"
        interface_with_dependencies = symbols[1]
        assert len(interface_with_dependencies.dependencies) == 1
        assert interface_with_dependencies.dependencies[0].name == "Animal"
        class_with_dependencies = symbols[2]
        assert len(class_with_dependencies.dependencies) == 1
        assert class_with_dependencies.dependencies[0].name == "Dog"
