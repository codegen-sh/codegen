from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_extended_source_in_chain(tmpdir) -> None:
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

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "a(b(c()))"
        assert b.source == "b(c())"
        assert c.source == "c()"
        assert a.extended_source == "a(b(c()))"
        assert b.extended_source == "b(c())"
        assert c.extended_source == "c()"

        # Check bar
        bar = file.get_function("bar")
        calls = bar.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "a()"
        assert b.source == "b()"
        assert c.source == "c()"
        assert a.extended_source == "a()"
        assert b.extended_source == "a().b()"
        assert c.extended_source == "a().b().c()"

        # Check bat
        bat = file.get_function("bat")
        calls = bat.function_calls
        assert len(calls) == 1
        func = calls[0]

        assert func.predecessor is None
        assert func.full_name == "x.y.z.func"
        assert func.source == "x.y.z.func()"
        assert func.extended_source == "x.y.z.func()"

        # Check baz
        baz = file.get_function("baz")
        calls = baz.function_calls
        assert len(calls) == 3
        c = calls[0]
        b = calls[1]
        a = calls[2]

        assert a.name == "a"
        assert b.name == "b"
        assert c.name == "c"
        assert a.source == "x.a()"
        assert b.source == "y.b()"
        assert c.source == "z.c()"
        assert a.extended_source == "x.a()"
        assert b.extended_source == "x.a().y.b()"
        assert c.extended_source == "x.a().y.b().z.c()"


def test_function_call_extended_source_multiline_statement(tmpdir) -> None:
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

        # Check names
        assert limit.name == "limit"
        assert order_by.name == "orderBy"
        assert group_by.name == "groupBy"
        assert where.name == "where"
        assert select.name == "select"

        # Check sources
        assert limit.source == "limit(10)"
        assert "orderBy(" in order_by.source
        assert "groupBy(" not in order_by.source

        # Check extended sources
        assert "orderBy(" in order_by.extended_source
        assert "groupBy(" in order_by.extended_source

        # Check parameters
        assert limit.args[0].value == "10"
        assert len(order_by.args) == 2
        assert select.args[0].value == "Table"
        assert where.args[0].name == "condition1"
        assert where.args[0].value == "1"
