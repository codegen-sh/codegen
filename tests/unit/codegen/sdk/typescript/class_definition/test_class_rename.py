from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_rename(tmpdir) -> None:
    # language=typescript
    content1 = """
export class MyClass {
    constructor() {}

    myMethod(): void {
        // Implementation here
    }
}

let myGlobalVar: MyClass = new MyClass();

function myFunction(arg: MyClass | null = null): void {
    // Implementation here
}
"""
    # language=typescript
    content2 = """
import { MyClass } from './file1';

let myOtherGlobalVar: MyClass = new MyClass();

function myOtherFunction(arg: MyClass | null = null): void {
    // Implementation here
}

class MyOtherClass {
    myAttr: MyClass;

    constructor() {
        this.myAttr = new MyClass();
    }

    myMethod(arg: MyClass | null = null): void {
        // Implementation here
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")

        symbol = file1.get_class("MyClass")
        symbol.rename("MyRenamedClass")

    # language=typescript
    assert (
        file1.content
        == """
export class MyRenamedClass {
    constructor() {}

    myMethod(): void {
        // Implementation here
    }
}

let myGlobalVar: MyRenamedClass = new MyRenamedClass();

function myFunction(arg: MyRenamedClass | null = null): void {
    // Implementation here
}
"""
    )
    # language=typescript
    assert (
        file2.content
        == """
import { MyRenamedClass } from './file1';

let myOtherGlobalVar: MyRenamedClass = new MyRenamedClass();

function myOtherFunction(arg: MyRenamedClass | null = null): void {
    // Implementation here
}

class MyOtherClass {
    myAttr: MyRenamedClass;

    constructor() {
        this.myAttr = new MyRenamedClass();
    }

    myMethod(arg: MyRenamedClass | null = null): void {
        // Implementation here
    }
}
"""
    )
