from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_type_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
export type Animal = {
    name: string;
    age: number;
};

export type Dog = Animal & {
    breed: string;
    bark(): void;
};

export type Cat = Animal & {
    color: string;
    meow(): void;
};

export type Pet = Dog | Cat;

export type PetOwner = {
    pets: Pet[];
    address: {
        street: string;
        city: string;
    };
};

export const animalTypes = ["dog", "cat"] as const;
export type AnimalType = typeof animalTypes[number];
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        # Test basic type dependencies
        pet_type = file.get_symbol("Pet")
        pet_deps = [dep.name for dep in pet_type.dependencies]
        assert "Dog" in pet_deps
        assert "Cat" in pet_deps
        assert len(pet_deps) == 2

        # Test nested type dependencies
        dog_type = file.get_symbol("Dog")
        dog_deps = [dep.name for dep in dog_type.dependencies]
        assert "Animal" in dog_deps
        assert len(dog_deps) == 1

        # Test const type dependencies
        animal_type = file.get_type("AnimalType")
        animal_deps = [dep.name for dep in animal_type.dependencies]
        assert "animalTypes" in animal_deps
        assert len(animal_deps) == 1

        # Test topological sorting
        sorted_symbols = file.symbols_sorted_topologically

        # Verify parent comes before child
        animal_idx = sorted_symbols.index(file.get_symbol("Animal"))
        dog_idx = sorted_symbols.index(file.get_symbol("Dog"))
        assert animal_idx > dog_idx

        # Verify no symbol depends on itself
        for symbol in file.symbols:
            assert symbol not in symbol.dependencies
