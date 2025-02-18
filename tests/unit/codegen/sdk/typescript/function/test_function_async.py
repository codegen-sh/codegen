from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.typescript.placeholder.placeholder_return_type import TSReturnTypePlaceholder
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_is_async_basic(tmpdir):
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

        foo.asyncify()
        bar.asyncify()
        baz.asyncify()
        qux.asyncify()

    # language=typescript
    assert (
        file.content
        == """
async function foo(): Promise<void> {
    return;
}

async function bar(): Promise<void> {
    return;
}

class MyClass {
    async baz(): Promise<void> {
        return;
    }

    async qux(): Promise<void> {
        return;
    }
}
    """
    )


def test_function_is_async_extended(tmpdir):
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

        foo.asyncify()
        bar.asyncify()
        baz.asyncify()
        qux.asyncify()

    # language=typescript
    assert (
        file.content
        == """
/** Docstring */
async function foo(): Promise<void> {
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
    async qux(): Promise<void> {
        return;
    }
}
    """
    )


def test_function_is_async_other_syntax(tmpdir):
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

        foo.asyncify()
        foo_async.asyncify()
        add.asyncify()
        add_async.asyncify()
        bar.asyncify()
        bar_async.asyncify()

    # language=typescript
    assert (
        file.content
        == """
// Arrow functions
const foo = async (): Promise<void> => {
    return;
};

const fooAsync = async (): Promise<void> => {
    return;
};


// Static functions
class MathOperations {
    static async add(a: number, b: number): Promise<number> {
        return a + b;
    }
    static async addAsync(userId: string): Promise<number> {
        return a + b;
    }
}

// Generic functions
async function bar<T>(arg: T): Promise<T> {
    return arg;
}
async function barAsync<T>(arg: T): Promise<T> {
    return arg;
}
    """
    )


def test_asyncify_wraps_non_promise_return_type(tmpdir) -> None:
    # ========= = [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
function getData(): string {
    return "hello";
}
"""
    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
async function getData(): Promise<string> {
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

        # After asyncify, should be async and return type wrapped in Promise
        func.asyncify()
        codebase.commit()

        # Check file content directly instead of func.is_async
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_asyncify_already_promise_return_type(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    function getData(): Promise<string> {
        return Promise.resolve("hello");
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    async function getData(): Promise<string> {
        return Promise.resolve("hello");
    }
    """

    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"test.ts": BEFORE_CONTENT},
    ) as codebase:
        file = codebase.get_file("test.ts")
        func = file.get_function("getData")

        # Initial state should be non-async but already have Promise return type
        assert not func.is_async
        assert func.return_type.source == "Promise<string>"

        # After asyncify, should be async but return type should remain unchanged
        func.asyncify()
        codebase.commit()

        # Check file content directly instead of func.is_async
        print(file.content)
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_asyncify_void_return_type(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    function processData(): void {
        console.log("processing");
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    async function processData(): Promise<void> {
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

        # Initial state should be non-async with void return type
        assert not func.is_async
        assert func.return_type.source == "void"

        # After asyncify, should be async and return Promise<void>
        func.asyncify()
        codebase.commit()
        # Check file content directly instead of func.is_async
        assert file.content.strip() == EXPECTED_CONTENT.strip()


def test_asyncify_no_return_type(tmpdir) -> None:
    # ========== [ BEFORE ] ==========
    # language=typescript
    BEFORE_CONTENT = """
    function processData() {
        console.log("processing");
    }
    """

    # ========== [ AFTER ] ==========
    # language=typescript
    EXPECTED_CONTENT = """
    async function processData() {
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

        # Initial state should be non-async with no return type
        assert not func.is_async
        assert isinstance(func.return_type, TSReturnTypePlaceholder)

        # After asyncify, should be async but no return type added
        func.asyncify()
        codebase.commit()
        # Check file content directly instead of func.is_async
        assert file.content.strip() == EXPECTED_CONTENT.strip()
