from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.interfaces.editable import Editable
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parent_class_names_single(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Dog extends Animal {
    bark() {
        console.log("Woof! Woof!");
    }
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        dog_class = file.get_symbol("Dog")
        assert dog_class.parent_class_names
        assert len(dog_class.parent_class_names) == 1
        assert dog_class.parent_class_names[0] == "Animal"


def test_class_extends_generic_class(tmpdir) -> None:
    FILENAME = "test.ts"
    FILE_CONTENT = """
class Collection<T> {
  protected items: T[];

  constructor(items: T[] = []) {
    this.items = items;
  }

  add(item: T): void {
    this.items.push(item);
  }
}

class NumberCollection extends Collection<number> {
  sum(): number {
    return this.items.reduce((total, num) => total + num, 0);
  }

  average(): number {
    return this.sum() / this.items.length;
  }
}
"""


def test_class_inherits_generic_interface(tmpdir) -> None:
    FILENAME = "test.ts"
    FILE_CONTENT = """
interface Comparable<T> {
  compareTo(other: T): number;
}

class Person implements Comparable<Person> {
  private name: string;
  private age: number;

  constructor(name: string, age: number) {
    this.name = name;
    this.age = age;
  }

  compareTo(other: Person): number {
    if (this.age < other.age) {
      return -1;
    } else if (this.age > other.age) {
      return 1;
    } else {
      return 0;
    }
  }
}
"""


def test_class_extends_and_inherits(tmpdir) -> None:
    FILENAME = "test.ts"
    FILE_CONTENT = """
interface Flyable {
  fly(): void;
}

class Animal {
  protected name: string;

  constructor(name: string) {
    this.name = name;
  }

  move(distanceInMeters: number = 0) {
    console.log(`${this.name} moved ${distanceInMeters}m.`);
  }
}

class Bird extends Animal implements Flyable {
  private wingspan: number;

  constructor(name: string, wingspan: number) {
    super(name);
    this.wingspan = wingspan;
  }

  fly(): void {
    console.log(`${this.name} is flying with a wingspan of ${this.wingspan}cm.`);
  }
}

const bird = new Bird("Sparrow", 30);
bird.move(10); // Output: Sparrow moved 10m.
bird.fly();    // Output: Sparrow is flying with a wingspan of 30cm.
"""


def test_class_nested_parent_classes(tmpdir) -> None:
    FILENAME = "test.ts"
    FILE_CONTENT = """
abstract class Shape {
  protected color: string;

  constructor(color: string) {
    this.color = color;
  }

  abstract getArea(): number;
}

class TwoDimensionalShape extends Shape {
  constructor(color: string) {
    super(color);
  }
}

class ThreeDimensionalShape extends Shape {
  constructor(color: string) {
    super(color);
  }

  abstract getVolume(): number;
}

class Rectangle extends TwoDimensionalShape {
  private width: number;
  private height: number;

  constructor(color: string, width: number, height: number) {
    super(color);
    this.width = width;
    this.height = height;
  }

  getArea(): number {
    return this.width * this.height;
  }
}

class Circle extends TwoDimensionalShape {
  private radius: number;

  constructor(color: string, radius: number) {
    super(color);
    this.radius = radius;
  }

  getArea(): number {
    return Math.PI * this.radius ** 2;
  }
}

class Cube extends ThreeDimensionalShape {
  private sideLength: number;

  constructor(color: string, sideLength: number) {
    super(color);
    this.sideLength = sideLength;
  }

  getArea(): number {
    return 6 * this.sideLength ** 2;
  }

  getVolume(): number {
    return this.sideLength ** 3;
  }
}
"""


def test_class_edit_parent_class_names(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Cube extends ThreeDimensionalShape {
  private sideLength: number;

  constructor(color: string, sideLength: number) {
    super(color);
    this.sideLength = sideLength;
  }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={FILENAME: FILE_CONTENT}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(FILENAME)
        cube = file.get_class("Cube")
        assert len(cube.parent_class_names) == 1
        assert isinstance(cube.parent_class_names[0], Editable)
        cube.parent_class_names[0].source = "ThreeDimensionalShape"
        cube.parent_class_names[0].edit("FourDimensionalShape")
        codebase.commit()

        cube = file.get_class("Cube")
        assert cube.parent_class_names[0].source == "FourDimensionalShape"
