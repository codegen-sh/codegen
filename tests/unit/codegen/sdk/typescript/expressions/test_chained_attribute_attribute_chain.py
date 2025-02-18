from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_attribute_chain_query_builder(tmpdir) -> None:
    # language=typescript
    content = """
function query() {
    // Test chained method calls with function at start
    QueryBuilder().select("name", "age").fromTable("users").where("age > 18").orderBy("name");
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        query = file.get_function("query")
        calls = query.function_calls
        assert len(calls) == 5
        order_by = calls[0]  # Last call in chain
        where = calls[1]
        from_table = calls[2]
        select = calls[3]
        query_builder = calls[4]  # First call in chain

        # Test attribute chain from different positions
        # From first call (QueryBuilder())
        chain = query_builder.attribute_chain
        assert len(chain) == 5
        assert chain[0] == query_builder
        assert chain[1] == select
        assert chain[2] == from_table
        assert chain[3] == where
        assert chain[4] == order_by

        # From middle call (from_table())
        chain = from_table.attribute_chain
        assert len(chain) == 5
        assert chain[0] == query_builder
        assert chain[1] == select
        assert chain[2] == from_table
        assert chain[3] == where
        assert chain[4] == order_by

        # From last call (order_by())
        chain = order_by.attribute_chain
        assert len(chain) == 5
        assert chain[0] == query_builder
        assert chain[1] == select
        assert chain[2] == from_table
        assert chain[3] == where
        assert chain[4] == order_by


def test_attribute_chain_mixed_properties(tmpdir) -> None:
    # language=typescript
    content = """
function query() {
    // Test mix of properties and function calls
    QueryBuilder().a.select("name", "age").fromTable("users").where("age > 18").b.orderBy("name").c;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        query = file.get_function("query")
        calls = query.function_calls

        # Get function calls in order
        order_by = calls[0]  # Last function call
        where = calls[1]
        from_table = calls[2]
        select = calls[3]
        query_builder = calls[4]  # First function call

        # Test from first call
        chain = query_builder.attribute_chain
        assert len(chain) == 8  # 5 function calls + 3 properties (a, b, c)
        assert chain[0] == query_builder
        assert chain[1].source == "a"  # Property
        assert chain[2] == select
        assert chain[3] == from_table
        assert chain[4] == where
        assert chain[5].source == "b"  # Property
        assert chain[6] == order_by
        assert chain[7].source == "c"  # Property


def test_attribute_chain_only_properties(tmpdir) -> None:
    # language=typescript
    content = """
function test() {
    // Test chain with only properties
    a.b.c.func();
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")
        calls = test.function_calls
        assert len(calls) == 1
        func = calls[0]

        chain = func.attribute_chain
        assert len(chain) == 4
        assert chain[0].source == "a"
        assert chain[1].source == "b"
        assert chain[2].source == "c"
        assert chain[3] == func


def test_attribute_chain_nested_calls(tmpdir) -> None:
    # language=typescript
    content = """
function test() {
    // Test nested function calls (not chained)
    a(b(c()));
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")
        calls = test.function_calls
        assert len(calls) == 3
        a = calls[0]
        b = calls[1]
        c = calls[2]

        # Each call should have its own single-element chain
        assert a.attribute_chain == [a]
        assert b.attribute_chain == [b]
        assert c.attribute_chain == [c]


def test_attribute_chain_promise_then(tmpdir) -> None:
    # language=typescript
    content = """
function test() {
    // Test Promise chain with multiple then calls
    fetch("https://api.example.com/data")
        .then(response => response.json())
        .then(data => processData(data))
        .then(result => console.log(result))
        .catch(error => handleError(error));
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")
        calls = test.function_calls

        # Get function calls in order (last to first)
        catch_call = calls[0]
        then3 = calls[1]  # console.log
        then2 = calls[2]  # processData
        then1 = calls[3]  # response.json
        fetch = calls[4]  # First call in chain

        # Test attribute chain from fetch
        chain = fetch.attribute_chain
        assert len(chain) == 5
        assert chain[0] == fetch
        assert chain[1] == then1
        assert chain[2] == then2
        assert chain[3] == then3
        assert chain[4] == catch_call

        # Test from middle of chain
        chain = then2.attribute_chain
        assert len(chain) == 5
        assert chain[0] == fetch
        assert chain[1] == then1
        assert chain[2] == then2
        assert chain[3] == then3
        assert chain[4] == catch_call


def test_attribute_chain_async_await_promise(tmpdir) -> None:
    # language=typescript
    content = """
async function test() {
    // Test Promise chain with mix of async/await and then
    const result = await axios.get("/api/data")
        .then(response => response.data)
        .then(data => transform(data));
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        test = file.get_function("test")
        calls = test.function_calls

        # Get function calls in order
        then2 = calls[0]  # transform
        then1 = calls[1]  # response.data
        get = calls[2]  # get
        axios = calls[3]  # axios

        # Test attribute chain
        chain = get.attribute_chain
        assert len(chain) == 4
        assert chain[0].source == "axios"
        assert chain[1] == get
        assert chain[2] == then1
        assert chain[3] == then2
