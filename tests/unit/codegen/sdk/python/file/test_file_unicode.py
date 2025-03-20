from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_unicode_move_symbol(tmpdir) -> None:
    # language=python
    content1 = """
def external_dep():
    return "🎇" + 42
"""
    # language=python
    content2 = """
from file1 import external_dep

def foo():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"

def bar():
    return external_dep() + bar_dep() + "🔗"

def bar_dep():
    return "😀"
"""
    # language=python
    content3 = """
from file2 import bar

def baz():
    return bar() + "🤯" + 1
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.py": content1, "file2.py": content2, "file3.py": content3},
    ) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        file3 = codebase.get_file("file3.py")

        bar = file2.get_function("bar")
        bar.move_to_file(file3, include_dependencies=True, strategy="add_back_edge")

    assert file1.content == content1
    # language=python
    assert (
        file2.content
        == """
from file1 import external_dep

def foo():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"
"""
    )

    # language=python
    assert (
        file3.content
        == """
from file1 import external_dep
def baz():
    return bar() + "🤯" + 1

def bar_dep():
    return "😀"

def bar():
    return external_dep() + bar_dep() + "🔗"
"""
    )


def test_unicode_rename_local(tmpdir) -> None:
    # language=python
    content = """
def helper_func_a(param_a):
    return "✨" + param_a
def helper_func_b(param_a):
    return "🎊" + param_a
def main_func(input_id):
    var_a = input_id
    var_b = "🍃"
    id_a = var_a.attr_a
    result_a = helper_func_a(param_a = var_a)
    var_c = (
        helper_func_b(
            param_a=var_b+"😑"
        )
    )
    config = {
            "id": var_b.attr_a if var_b else None,
    }
    return var_a
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file.py": content},
    ) as codebase:
        for function in codebase.functions:
            local_vars = function.code_block.get_local_var_assignments("var", fuzzy_match=True)
            for local_var in local_vars:
                local_var.rename(local_var.name.replace("var", "renamed_var"))

    # language=python
    expected_content = """
def helper_func_a(param_a):
    return "✨" + param_a
def helper_func_b(param_a):
    return "🎊" + param_a
def main_func(input_id):
    renamed_var_a = input_id
    renamed_var_b = "🍃"
    id_a = renamed_var_a.attr_a
    result_a = helper_func_a(param_a = renamed_var_a)
    renamed_var_c = (
        helper_func_b(
            param_a=renamed_var_b+"😑"
        )
    )
    config = {
            "id": renamed_var_b.attr_a if renamed_var_b else None,
    }
    return renamed_var_a
    """
    assert codebase.get_file("file.py").content == expected_content


def test_unicode_rename_function(tmpdir) -> None:
    # language=python
    content1 = """
from file2 import foo

def external_usage():
    return "🎇" + foo()
"""
    # language=python
    content2 = """
def baz():
    return foo() + "🤯" + 1

def foo():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"

def bar():
    return "🦄" + foo() + "🔗"
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.py": content1, "file2.py": content2},
    ) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")

        foo = file2.get_function("foo")
        foo.rename("foo_renamed")

    # language=python
    assert (
        file1.content
        == """
from file2 import foo_renamed

def external_usage():
    return "🎇" + foo_renamed()
"""
    )
    # language=python
    assert (
        file2.content
        == """
def baz():
    return foo_renamed() + "🤯" + 1

def foo_renamed():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"

def bar():
    return "🦄" + foo_renamed() + "🔗"
"""
    )


def test_unicode_replace(tmpdir) -> None:
    # language=python
    content = """
def baz():
    return foo() + "🤯" + 1

def foo():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"

def bar():
    return "🦄" + foo() + "🔗"
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file.py": content},
    ) as codebase:
        file = codebase.get_file("file.py")
        file.replace("foo()", "foo_renamed()")

    # language=python
    assert (
        file.content
        == """
def baz():
    return foo_renamed() + "🤯" + 1

def foo_renamed():
    return foo_dep() + 1 + "🐍"

def foo_dep():
    return 24 + "🐲"

def bar():
    return "🦄" + foo_renamed() + "🔗"
"""
    )
