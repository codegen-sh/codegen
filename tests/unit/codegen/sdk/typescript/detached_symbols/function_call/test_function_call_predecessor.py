from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_predecessor_single_line(tmpdir) -> None:
    file = """
function foo() {
    a(b(c()));
}

function bar() {
    a().b().c();
}

function bat() {
    x.y.z.func();
}

function baz() {
    x.a().y.b().z.c();
}
    """

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 3
        a = calls[0]
        b = calls[1]
        c = calls[2]

        assert a.predecessor is None
        assert b.predecessor is None
        assert c.predecessor is None
        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"

        # Check bar
        bar = file.get_function("bar")
        calls = bar.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.predecessor is None
        assert b.predecessor == a
        assert c.predecessor == b
        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"

        # Check bat
        bat = file.get_function("bat")
        calls = bat.function_calls
        assert len(calls) == 1
        func = calls[0]

        assert func.predecessor is None
        assert func.full_name == "x.y.z.func"

        # Check baz
        baz = file.get_function("baz")
        calls = baz.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.predecessor is None
        assert b.predecessor == a
        assert c.predecessor == b
        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"


def test_function_call_predecessor_multiline(tmpdir) -> None:
    file = """
function foo() {
    select(Table)
    .where(
        condition1 = 1,
        condition2 = thing().otherThing().getThing()
    )
    .groupBy(
        column1,
        column2
    ).orderBy(
        column1,
        column2
    ).limit(10);
}
    """

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        # Check foo
        foo = file.get_function("foo")
        calls = foo.function_calls
        assert len(calls) == 8
        limit = calls[0]
        order_by = calls[1]
        group_by = calls[2]
        where = calls[3]
        select = calls[4]

        # Check predecessors
        assert limit.predecessor == order_by
        assert order_by.predecessor == group_by
        assert group_by.predecessor == where
        assert where.predecessor == select
        assert select.predecessor is None

        # Check names
        assert limit.name == "limit"
        assert order_by.name == "orderBy"
        assert group_by.name == "groupBy"
        assert where.name == "where"
        assert select.name == "select"

        # Check parameters
        assert limit.args[0].value == "10"
        assert len(order_by.args) == 2
        assert select.args[0].value == "Table"
        assert where.args[0].name == "condition1"
        assert where.args[0].value == "1"
