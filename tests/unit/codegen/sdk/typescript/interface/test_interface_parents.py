from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_interfaces_inheritance(tmpdir) -> None:
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
        assert symbols[0].parent_interfaces is None
        assert symbols[0].implementations == [symbols[1], symbols[2]]
        assert symbols[1].parent_interfaces == ["Animal"]
        assert symbols[1].implementations == [symbols[2]]
        assert symbols[1].extends("Animal")
        assert symbols[1].extends(symbols[0])
        assert not symbols[1].extends(symbols[2])
        assert symbols[2].parent_classes == ["Dog"]
        assert symbols[2].is_subclass_of(symbols[1])
        assert symbols[2].is_subclass_of(symbols[0])
        assert symbols[2].subclasses == []
        assert not symbols[2].is_subclass_of(symbols[0], max_depth=0)
