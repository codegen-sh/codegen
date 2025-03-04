from typing import TYPE_CHECKING
from unittest.mock import patch

from codegen.sdk.codebase.factory.get_session import get_codebase_session

if TYPE_CHECKING:
    from codegen.sdk.core.file import SourceFile


def test_remove_unpacking_assignment(tmpdir) -> None:
    # language=python
    content = """foo,bar,buzz = (a, b, c)"""

    with get_codebase_session(tmpdir=tmpdir, files={"test1.py": content, "test2.py": content, "test3.py": content}) as codebase:
        file1 = codebase.get_file("test1.py")
        file2 = codebase.get_file("test2.py")
        file3 = codebase.get_file("test3.py")

        foo = file1.get_symbol("foo")
        foo.remove()
        codebase.commit()

        assert len(file1.symbols) == 2
        statement = file1.symbols[0].parent
        assert len(statement.assignments) == 2
        assert len(statement.value) == 2
        assert file1.source == """bar,buzz = (b, c)"""
        bar = file2.get_symbol("bar")
        bar.remove()
        codebase.commit()
        assert len(file2.symbols) == 2
        statement = file2.symbols[0].parent
        assert len(statement.assignments) == 2
        assert len(statement.value) == 2
        assert file2.source == """foo,buzz = (a, c)"""

        buzz = file3.get_symbol("buzz")
        buzz.remove()
        codebase.commit()

        assert len(file3.symbols) == 2
        statement = file3.symbols[0].parent
        assert len(statement.assignments) == 2
        assert len(statement.value) == 2
        assert file3.source == """foo,bar = (a, b)"""

        file1_bar = file1.get_symbol("bar")

        file1_bar.remove()
        codebase.commit()
        assert file1.source == """buzz = c"""

        file1_buzz = file1.get_symbol("buzz")
        file1_buzz.remove()

        codebase.commit()
        assert len(file1.symbols) == 0
        assert file1.source == """"""


def test_remove_unpacking_assignment_funct(tmpdir) -> None:
    # language=python
    content = """foo,bar,buzz = f()"""

    with get_codebase_session(tmpdir=tmpdir, files={"test1.py": content, "test2.py": content, "test3.py": content}) as codebase:
        file1 = codebase.get_file("test1.py")
        file2 = codebase.get_file("test2.py")
        file3 = codebase.get_file("test3.py")

        foo = file1.get_symbol("foo")
        foo.remove()
        codebase.commit()

        assert len(file1.symbols) == 3
        statement = file1.symbols[0].parent
        assert len(statement.assignments) == 3
        assert file1.source == """_,bar,buzz = f()"""
        bar = file2.get_symbol("bar")
        bar.remove()
        codebase.commit()
        assert len(file2.symbols) == 3
        statement = file2.symbols[0].parent
        assert len(statement.assignments) == 3
        assert file2.source == """foo,_,buzz = f()"""

        buzz = file3.get_symbol("buzz")
        buzz.remove()
        codebase.commit()

        assert len(file3.symbols) == 3
        statement = file3.symbols[0].parent
        assert len(statement.assignments) == 3
        assert file3.source == """foo,bar,_ = f()"""

        file1_bar = file1.get_symbol("bar")
        file1_buzz = file1.get_symbol("buzz")

        file1_bar.remove()
        file1_buzz.remove()
        codebase.commit()
        assert len(file1.symbols) == 0
        assert file1.source == """"""


def test_remove_unpacking_assignment_num(tmpdir) -> None:
    # language=python
    content = """a,b,c,d,e,f = (1, 2, 2, 4, 5, 3)"""

    with get_codebase_session(tmpdir=tmpdir, files={"test1.py": content, "test2.py": content}) as codebase:
        file1 = codebase.get_file("test1.py")

        a = file1.get_symbol("a")
        d = file1.get_symbol("d")

        a.remove()
        d.remove()
        codebase.commit()

        assert len(file1.symbols) == 4
        statement = file1.symbols[0].parent
        assert len(statement.assignments) == 4
        assert file1.source == """b,c,e,f = (2, 2, 5, 3)"""

        e = file1.get_symbol("e")
        c = file1.get_symbol("c")

        e.remove()
        c.remove()
        codebase.commit()

        assert len(file1.symbols) == 2
        statement = file1.symbols[0].parent
        assert len(statement.assignments) == 2
        assert file1.source == """b,f = (2, 3)"""

        f = file1.get_symbol("f")

        f.remove()
        codebase.commit()

        assert len(file1.symbols) == 1
        statement = file1.symbols[0].parent
        assert len(statement.assignments) == 1
        assert file1.source == """b = 2"""
        file2 = codebase.get_file("test2.py")
        a = file2.get_symbol("a")
        d = file2.get_symbol("d")
        e = file2.get_symbol("e")
        c = file2.get_symbol("c")
        f = file2.get_symbol("f")
        b = file2.get_symbol("b")

        a.remove()
        b.remove()
        c.remove()
        d.remove()
        e.remove()
        f.remove()

        codebase.commit()

        assert len(file2.symbols) == 0
        assert file2.source == """"""


@patch("codegen.sdk.python.assignment.logger")
def test_unpacking_function_with_underscore_removal(mock_logger, tmpdir: str) -> None:
    # language=python
    content1 = """
    args, _ = parser.parse_known_args() ##args gets deleted
    with open(args.template_path) as f:
        print('test')
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file1.py": content1,
        },
    ) as codebase:
        file1: SourceFile = codebase.get_file("file1.py")

        for symbol in codebase.symbols:
            if not symbol.usages:
                symbol.remove()
        codebase.commit()
        assert len(file1.symbols) != 0
        assert mock_logger.warning.call_count == 1
