from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.typescript.placeholder.placeholder_return_type import TSReturnTypePlaceholder
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_deasyncify_basic(tmpdir):
    # language=typescript
    content = """
function foo(): void {
    return;
}

async function bar(): Promise<void> {
    return;
}

class MyClass {
    async baz(): Promise<void> {
        return;
    }

    qux(): void {
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        bar = file.get_function("bar")
        my_class = file.get_class("MyClass")
        baz = my_class.get_method("baz")
        qux = my_class.get_method("qux")

        assert not foo.is_async
        assert bar.is_async
        assert baz.is_async
        assert not qux.is_async

        foo.deAsyncify()
        bar.deAsyncify()
        baz.deAsyncify()
        qux.deAsyncify()

    # language=typescript
    assert (
        file.content
        == """
function foo(): void {
    return;
}

function bar(): void {
    return;
}

class MyClass {
    baz(): void {
        return;
    }

    qux(): void {
        return;
    }
}
    """
    )


def test_deasyncify_extended(tmpdir):
    # language=typescript
    content = """
/** Docstring */
function foo(): void {
    return;
}

/** Docstring */
async function bar(): Promise<void> {
    return;
}

/** Docstring */
@my_decorator
class MyClass {
    /** Docstring */
    @my_decorator
    async baz(): Promise<void> {
        return;
    }

    /** Docstring */
    @my_decorator
    qux(): void {
        return;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        bar = file.get_function("bar")
        my_class = file.get_class("MyClass")
        baz = my_class.get_method("baz")
        qux = my_class.get_method("qux")

        assert not foo.is_async
        assert bar.is_async
        assert baz.is_async
        assert not qux.is_async

        foo.deAsyncify()
        bar.deAsyncify()
        baz.deAsyncify()
        qux.deAsyncify()

    # language=typescript
    assert (
        file.content
        == """
/** Docstring */
function foo(): void {
    return;
}

/** Docstring */
function bar(): void {
    return;
}

/** Docstring */
@my_decorator
class MyClass {
    /** Docstring */
    @my_decorator
    baz(): void {
        return;
    }

    /** Docstring */
    @my_decorator
    qux(): void {
        return;
    }
}
    """
    )


def test_deasyncify_other_syntax(tmpdir):
    # language=typescript
    content = """
// Arrow functions
const foo = (): void => {
    return;
};

const fooAsync = async (): Promise<void> => {
    return;
};


// Static functions
class MathOperations {
    static add(a: number, b: number): number {
        return a + b;
    }
    static async addAsync(userId: string): Promise<number> {
        return a + b;
    }
}

// Generic functions
function bar<T>(arg: T): T {
    return arg;
}
async function barAsync<T>(arg: T): Promise<T> {
    return arg;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")
        foo_async = file.get_function("fooAsync")
        add = file.get_class("MathOperations").get_method("add")
        add_async = file.get_class("MathOperations").get_method("addAsync")
        bar = file.get_function("bar")
        bar_async = file.get_function("barAsync")

        assert not foo.is_async
        assert foo_async.is_async
        assert not add.is_async
        assert add_async.is_async
        assert not bar.is_async
        assert bar_async.is_async

        foo.deAsyncify()
        foo_async.deAsyncify()
        add.deAsyncify()
        add_async.deAsyncify()
        bar.deAsyncify()
        bar_async.deAsyncify()

    # language=typescript
    assert (
        file.content
        == """
// Arrow functions
const foo = (): void => {
    return;
};

const fooAsync = (): void => {
    return;
};


// Static functions
class MathOperations {
    static add(a: number, b: number): number {
        return a + b;
    }
    static addAsync(userId: string): number {
        return a + b;
    }
}

// Generic functions
function bar<T>(arg: T): T {
    return arg;
}
function barAsync<T>(arg: T): T {
    return arg;
}
    """
    )


def test_deasyncify_unwraps_promise_return_type(tmpdir) -> None:
    # ========= = [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
async function getData(): Promise<string> {
    return "hello";
}
"""
    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
function getData(): string {
    return "hello";
}
"""

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"test.ts": BEFORE_CONTENT},
    ) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("getData")

        # Initial state should be async
        assert func.is_async
        assert func.return_type.source == "Promise<string>"

        # After deAsyncify, should be non-async and return type unwrapped from Promise
        func.deAsyncify()
        codebase.commit()

        # Check file content directly
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_deasyncify_already_non_async(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    function getData(): string {
        return "hello";
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    function getData(): string {
        return "hello";
    }
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"test.ts": BEFORE_CONTENT},
    ) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("getData")

        # Initial state should be non-async
        assert not func.is_async
        assert func.return_type.source == "string"

        # After deAsyncify, should remain unchanged
        func.deAsyncify()
        codebase.commit()

        # Check file content directly
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_deasyncify_void_return_type(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    async function processData(): Promise<void> {
        console.log("processing");
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    function processData(): void {
        console.log("processing");
    }
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"test.ts": BEFORE_CONTENT},
    ) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("processData")

        # Initial state should be async with Promise<void> return type
        assert func.is_async
        assert func.return_type.source == "Promise<void>"

        # After deAsyncify, should be non-async with void return type
        func.deAsyncify()
        codebase.commit()

        # Check file content directly
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_deasyncify_no_return_type(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    async function processData() {
        console.log("processing");
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    function processData() {
        console.log("processing");
    }
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"test.ts": BEFORE_CONTENT},
    ) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("processData")

        # Initial state should be async with no return type
        assert func.is_async
        assert isinstance(func.return_type, TSReturnTypePlaceholder)

        # After deAsyncify, should be non-async with no return type
        func.deAsyncify()
        codebase.commit()

        # Check file content directly
        assert file.content.strip() == EXPECTED_CONTENT.strip()
