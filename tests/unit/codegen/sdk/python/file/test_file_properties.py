from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.enums import SymbolType
from codegen.sdk.python import PyAssignment, PyClass, PyFile, PyFunction, PyImport

default_content = """
from some_file import x, y, z
import numpy as np

global_var_1 = 1
global_var_2 = 2

def foo():
    return bar()

def bar():
    return 42

class MyClass:
    def __init__(self):
        pass

class MySubClass(MyClass):
    def __init__(self):
        super().__init__()
        pass
"""


def test_file_get_extensions(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_extensions() == [".py"]


def test_file_extension(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.extension == ".py"


def test_file_from_content(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        new_file = PyFile.from_content("test_new.py", default_content, codebase.ctx)
        assert new_file.name == "test_new"
        assert new_file.content == default_content
        assert codebase.ctx.has_node(new_file.node_id)


def test_file_from_content_invalid_syntax(tmpdir) -> None:
    # language=python
    content = """
def calculate_average(numbers)
    total == 0
    for num in numbers
        total += num
    return total / len(numbers
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        new_file = PyFile.from_content("test_new.py", content, codebase.ctx)
        assert new_file is None


def test_file_create_from_filepath(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        new_file = PyFile.create_from_filepath("test_new.py", codebase.ctx)
        assert new_file.name == "test_new"
        assert new_file.content == ""
        assert codebase.ctx.has_node(new_file.node_id)


def test_file_content(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.content == default_content


def test_file_content_bytes(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.content_bytes == default_content.encode()


def test_file_write(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        new_content = "new content"
        file.write(new_content)
        assert file.content == new_content


def test_file_write_bytes(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        new_content = "new content"
        file.write_bytes(new_content.encode())
        assert file.content == new_content


def test_file_inbound_symbol_imports(tmpdir) -> None:
    """Tests that symbol imports are correctly identified"""
    # language=python
    content2 = """
from dir1.file1 import foo as f, bar as b

def buzz():
    return f()

def fizz():
    return b()
    """
    # language=python
    content3 = """
from dir2.file2 import buzz
from dir2.file2 import fizz as f
from dir1.file1 import MyClass, global_var_2

def fizzle():
    return MyClass() + global_var_2
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir1/file1.py": default_content, "dir2/file2.py": content2, "dir3/file3.py": content3}) as codebase:
        file1 = codebase.get_file("dir1/file1.py")
        file2 = codebase.get_file("dir2/file2.py")

        assert all(isinstance(imp, PyImport) for imp in file1.inbound_imports)
        assert len(file1.inbound_imports) == 4
        assert set((imp.file.name, imp.name) for imp in file1.inbound_imports) == {("file2", "f"), ("file2", "b"), ("file3", "MyClass"), ("file3", "global_var_2")}

        assert all(isinstance(imp, PyImport) for imp in file2.inbound_imports)
        assert len(file2.inbound_imports) == 2
        assert set((imp.file.name, imp.name) for imp in file2.inbound_imports) == {("file3", "buzz"), ("file3", "f")}


def test_file_inbound_indirect_imports(tmpdir) -> None:
    """Tests that indirect imports are correctly identified"""
    # language=python
    content2 = """
from dir1.file1 import np
from dir1.file1 import x as new_x
from dir1.file1 import y, z

def buzz():
    return np.random()

def fizz():
    return new_x()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir1/file1.py": default_content, "dir2/file2.py": content2}) as codebase:
        file1 = codebase.get_file("dir1/file1.py")
        assert all(isinstance(imp, PyImport) for imp in file1.inbound_imports)
        assert len(file1.inbound_imports) == 4
        assert set(imp.name for imp in file1.inbound_imports) == {"np", "new_x", "y", "z"}


def test_file_inbound_module_imports(tmpdir) -> None:
    """Tests that file as module imports are correctly identified"""
    # language=python
    content2 = """
from dir1 import file1

def buzz():
    return file1.foo()

def fizz():
    return file1.bar()
    """
    # language=python
    content3 = """
from dir2.file2 import file1

def fizzle():
    return file1.foo() + file1.global_var_2
    """
    # language=python
    content4 = """
from dir2 import file2 as f2
from dir1 import file1

def baz():
    return f2.fizzle() + file1.global_var_1
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir1/file1.py": default_content, "dir2/file2.py": content2, "dir3/file3.py": content3, "dir4/file4.py": content4}) as codebase:
        file1 = codebase.get_file("dir1/file1.py")
        file2 = codebase.get_file("dir2/file2.py")

        assert all(isinstance(imp, PyImport) for imp in file1.inbound_imports)
        assert len(file1.inbound_imports) == 2
        assert set((imp.file.name, imp.name) for imp in file1.inbound_imports) == {("file2", "file1"), ("file4", "file1")}

        assert all(isinstance(imp, PyImport) for imp in file2.inbound_imports)
        assert len(file2.inbound_imports) == 2
        assert set((imp.file.name, imp.name) for imp in file2.inbound_imports) == {("file3", "file1"), ("file4", "f2")}


def test_file_inbound_imports_wildcard_import(tmpdir) -> None:
    """Tests that file as module imports correctly identified when using wildcard imports"""
    # language=python
    content2 = """
from dir1.file1 import *

def buzz():
    return foo()

def fizz():
    return bar()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir1/file1.py": default_content, "dir2/file2.py": content2}) as codebase:
        file1 = codebase.get_file("dir1/file1.py")
        file2 = codebase.get_file("dir2/file2.py")
        assert all(isinstance(imp, PyImport) for imp in file1.inbound_imports)
        assert len(file1.inbound_imports) == 1
        assert len(file2.imports) == 1
        assert file1.inbound_imports[0].source == "from dir1.file1 import *"
        assert file2.get_import("dir1.file1") == file1.inbound_imports[0]

        foo = file1.get_symbol("foo")
        assert set(foo.symbol_usages) == {file2.get_symbol("buzz")}
        assert foo.symbol_usages == [file2.get_symbol("buzz")]


def test_file_importers(tmpdir) -> None:
    # language=python
    content1 = """
def foo():
    return 42

def bar():
    return 24
"""
    # language=python
    content2 = """
from dir import file1

def baz():
    return file1.foo() + file1.bar()
"""
    # language=python
    content3 = """
from dir import file1
from dir import file2

def fizzle():
    return file1.foo() + file2.baz()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/file2.py": content2, "dir/file3.py": content3}) as codebase:
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("dir/file2.py")
        file3 = codebase.get_file("dir/file3.py")
        assert all(isinstance(importer, PyImport) for importer in file1.importers)
        assert all(isinstance(importer, PyImport) for importer in file2.importers)
        assert all(isinstance(importer, PyImport) for importer in file3.importers)
        assert [imp.source for imp in file1.importers] == [file2.get_import("file1").source, file3.get_import("file1").source]
        assert [imp.source for imp in file2.importers] == [file3.get_import("file2").source]
        assert file3.importers == []


def test_file_importers_wildcard_import(tmpdir) -> None:
    # language=python
    content1 = """
def foo():
    return 42

def bar():
    return 24
"""
    # language=python
    content2 = """
from dir.file1 import *

def baz():
    return file1.foo() + file1.bar()
"""
    # language=python
    content3 = """
from dir import file1
from dir import file2

def fizzle():
    return file1.foo() + file2.baz()
"""
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.py": content1, "dir/file2.py": content2, "dir/file3.py": content3}) as codebase:
        file1 = codebase.get_file("dir/file1.py")
        file2 = codebase.get_file("dir/file2.py")
        file3 = codebase.get_file("dir/file3.py")
        assert all(isinstance(importer, PyImport) for importer in file1.importers)
        assert all(isinstance(importer, PyImport) for importer in file2.importers)
        assert all(isinstance(importer, PyImport) for importer in file3.importers)
        assert [imp.source for imp in file1.importers] == [file2.get_import("dir.file1").source, file3.get_import("file1").source]
        assert [imp.source for imp in file2.importers] == [file3.get_import("file2").source]
        assert file3.importers == []


def test_file_imports(tmpdir) -> None:
    # language=python
    content = """
from dir import file1
from dir import file2 as f2
from dir.file3 import foo, bar as b
from dir.file4 import *
import file5
import numpy as np
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.imports) == 7
        assert all(isinstance(import_, PyImport) for import_ in file.imports)
        assert [imp.source for imp in file.imports] == [
            "from dir import file1",
            "from dir import file2 as f2",
            "from dir.file3 import foo, bar as b",
            "from dir.file3 import foo, bar as b",
            "from dir.file4 import *",
            "import file5",
            "import numpy as np",
        ]


def test_file_get_import(tmpdir) -> None:
    # language=python
    content = """
from dir import file1
from dir import file2 as f2
from dir.file3 import foo, bar as b
from dir.file4 import *
import file5
import numpy as np
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_import("file1").source == "from dir import file1"
        assert file.get_import("f2").source == "from dir import file2 as f2"
        assert file.get_import("foo").source == "from dir.file3 import foo, bar as b"
        assert file.get_import("b").source == "from dir.file3 import foo, bar as b"
        assert file.get_import("dir.file4").source == "from dir.file4 import *"
        assert file.get_import("file5").source == "import file5"
        assert file.get_import("np").source == "import numpy as np"


def test_file_symbols(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.symbols) == 6
        assert [sym.name for sym in file.symbols] == ["global_var_1", "global_var_2", "foo", "bar", "MyClass", "MySubClass"]


def test_file_symbol_ordering(tmpdir) -> None:
    # Test Python file
    # language=python
    python_code = """
def foo():
    bar()

def fizzle():
    return baz() + bar()

def bar():
    return 42

def baz():
    return foo() + bar()

"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": python_code}) as codebase:
        file = codebase.get_file("test.py")

        # =====[ Start position sort ]=====
        symbols = file.symbols
        assert len(symbols) == 4
        assert [s.name for s in symbols] == ["foo", "fizzle", "bar", "baz"]

        # =====[ Topological sort ]=====
        ordered_symbols = file.symbols_sorted_topologically
        parent = file.get_symbol("foo")
        child = file.get_symbol("bar")
        assert ordered_symbols.index(parent) < ordered_symbols.index(child)

        parent = file.get_symbol("fizzle")
        child = file.get_symbol("baz")
        assert ordered_symbols.index(parent) < ordered_symbols.index(child)
        child2 = file.get_symbol("bar")
        assert ordered_symbols.index(parent) < ordered_symbols.index(child2)

        parent = file.get_symbol("baz")
        child = file.get_symbol("foo")
        assert ordered_symbols.index(parent) < ordered_symbols.index(child)
        child2 = file.get_symbol("bar")
        assert ordered_symbols.index(parent) < ordered_symbols.index(child2)


def test_file_get_symbol(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")

        global_var = file.get_symbol("global_var_1")
        assert global_var.name == "global_var_1"
        assert global_var.symbol_type == SymbolType.GlobalVar

        foo = file.get_symbol("foo")
        assert foo.name == "foo"
        assert foo.symbol_type == SymbolType.Function

        bar = file.get_symbol("bar")
        assert bar.name == "bar"
        assert bar.symbol_type == SymbolType.Function

        my_class = file.get_symbol("MyClass")
        assert my_class.name == "MyClass"
        assert my_class.symbol_type == SymbolType.Class


def test_file_get_symbol_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_symbol("__init__") is None


def test_file_global_vars(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.global_vars) == 2
        assert all(isinstance(global_var, PyAssignment) for global_var in file.global_vars)
        assert [global_var.name for global_var in file.global_vars] == ["global_var_1", "global_var_2"]


def test_file_get_global_var(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_global_var("global_var_1").name == "global_var_1"
        assert file.get_global_var("global_var_2").name == "global_var_2"


def test_file_get_global_var_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_global_var("not_found") is None


def test_file_classes(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.classes) == 2
        assert all(isinstance(cls, PyClass) for cls in file.classes)
        assert [cls.name for cls in file.classes] == ["MyClass", "MySubClass"]


def test_file_get_class(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_class("MyClass").name == "MyClass"
        assert file.get_class("MySubClass").name == "MySubClass"


def test_file_get_class_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_class("not_found") is None


def test_file_functions(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert len(file.functions) == 2
        assert all(isinstance(func, PyFunction) for func in file.functions)
        assert [func.name for func in file.functions] == ["foo", "bar"]


def test_file_get_function(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_function("foo").name == "foo"
        assert file.get_function("bar").name == "bar"


def test_file_get_function_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_function("__init__") is None


def test_file_get_node_by_name(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_node_by_name("x").name == "x"
        assert file.get_node_by_name("y").name == "y"
        assert file.get_node_by_name("z").name == "z"
        assert file.get_node_by_name("foo").name == "foo"
        assert file.get_node_by_name("bar").name == "bar"
        assert file.get_node_by_name("MyClass").name == "MyClass"
        assert file.get_node_by_name("MySubClass").name == "MySubClass"
        assert file.get_node_by_name("global_var_1").name == "global_var_1"
        assert file.get_node_by_name("global_var_2").name == "global_var_2"


def test_file_get_node_by_name_not_found(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.get_node_by_name("not_found") is None


def test_file_valid_symbol_names(tmpdir) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": default_content}) as codebase:
        file = codebase.get_file("test.py")
        assert file.valid_symbol_names == {
            "x": file.get_import("x"),
            "y": file.get_import("y"),
            "z": file.get_import("z"),
            "np": file.get_import("np"),
            "foo": file.get_function("foo"),
            "bar": file.get_function("bar"),
            "MyClass": file.get_class("MyClass"),
            "MySubClass": file.get_class("MySubClass"),
            "global_var_1": file.get_global_var("global_var_1"),
            "global_var_2": file.get_global_var("global_var_2"),
        }
