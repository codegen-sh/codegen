from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_attribute_chain_query_builder(tmpdir) -> None:
    # language=python
    content = """
def query():
    # Test chained method calls with function at start
    QueryBuilder().select("name", "age").from_table("users").where("age > 18").order_by("name")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
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
    # language=python
    content = """
def query():
    # Test mix of properties and function calls
    QueryBuilder().a.select("name", "age").from_table("users").where("age > 18").b.order_by("name").c
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
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
    # language=python
    content = """
def test():
    # Test chain with only properties
    a.b.c.func()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
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
    # language=python
    content = """
def test():
    # Test nested function calls (not chained)
    a(b(c()))
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
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
