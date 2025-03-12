from unittest.mock import MagicMock

import pytest

from codegen.sdk.core.interfaces.has_symbols import HasSymbols


@pytest.fixture
def fake_interface():
    class FakeHasSymbols(HasSymbols):
        def __init__(self, files):
            self._files = files

        def files_generator(self, *args, **kwargs):
            yield from self._files

    # File 1 with its fake attributes.
    file1 = MagicMock()
    file1.symbols = [MagicMock(), MagicMock()]
    file1.symbols[0].name = "symbol1"
    file1.symbols[1].name = "symbol2"
    file1.import_statements = [MagicMock()]
    file1.import_statements[0].name = "import_statement1"
    file1.global_vars = [MagicMock()]
    file1.global_vars[0].name = "global_variable1"
    file1.classes = [MagicMock()]
    file1.classes[0].name = "class1"
    file1.functions = [MagicMock()]
    file1.functions[0].name = "function1"
    file1.exports = [MagicMock()]
    file1.exports[0].name = "export_item1"
    file1.imports = [MagicMock()]
    file1.imports[0].name = "import1"

    # File 2 with its fake attributes.
    file2 = MagicMock()
    file2.symbols = [MagicMock()]
    file2.symbols[0].name = "symbol3"
    file2.import_statements = [MagicMock()]
    file2.import_statements[0].name = "import_statement2"
    file2.global_vars = [MagicMock(), MagicMock()]
    file2.global_vars[0].name = "global_variable2"
    file2.global_vars[1].name = "global_variable3"
    file2.classes = [MagicMock()]
    file2.classes[0].name = "class2"
    file2.functions = [MagicMock()]
    file2.functions[0].name = "function2"
    file2.exports = [MagicMock(), MagicMock()]
    file2.exports[0].name = "export_item2"
    file2.exports[1].name = "export_item3"
    file2.imports = [MagicMock()]
    file2.imports[0].name = "import2"

    fake_files = [file1, file2]
    return FakeHasSymbols(fake_files)


def test_files_generator_not_implemented():
    # Instantiating HasSymbols directly should cause files_generator to raise NotImplementedError.
    fi = HasSymbols()
    with pytest.raises(NotImplementedError):
        list(fi.files_generator())


def test_symbols_property(fake_interface):
    symbols = fake_interface.symbols
    names = sorted([item.name for item in symbols])
    assert names == ["symbol1", "symbol2", "symbol3"]


def test_import_statements_property(fake_interface):
    import_statements = fake_interface.import_statements
    names = sorted([item.name for item in import_statements])
    assert names == ["import_statement1", "import_statement2"]


def test_global_vars_property(fake_interface):
    global_vars = fake_interface.global_vars
    names = sorted([item.name for item in global_vars])
    assert names == ["global_variable1", "global_variable2", "global_variable3"]


def test_classes_property(fake_interface):
    classes = fake_interface.classes
    names = sorted([item.name for item in classes])
    assert names == ["class1", "class2"]


def test_functions_property(fake_interface):
    functions = fake_interface.functions
    names = sorted([item.name for item in functions])
    assert names == ["function1", "function2"]


def test_exports_property(fake_interface):
    exports = fake_interface.exports
    names = sorted([item.name for item in exports])
    assert names == ["export_item1", "export_item2", "export_item3"]


def test_imports_property(fake_interface):
    imports = fake_interface.imports
    names = sorted([item.name for item in imports])
    assert names == ["import1", "import2"]


def test_get_symbol(fake_interface):
    symbol = fake_interface.get_symbol("symbol1")
    assert symbol is not None
    assert symbol.name == "symbol1"
    assert fake_interface.get_symbol("nonexistent") is None


def test_get_import_statement(fake_interface):
    imp_stmt = fake_interface.get_import_statement("import_statement2")
    assert imp_stmt is not None
    assert imp_stmt.name == "import_statement2"
    assert fake_interface.get_import_statement("nonexistent") is None


def test_get_global_var(fake_interface):
    global_var = fake_interface.get_global_var("global_variable3")
    assert global_var is not None
    assert global_var.name == "global_variable3"
    assert fake_interface.get_global_var("nonexistent") is None


def test_get_class(fake_interface):
    cls = fake_interface.get_class("class2")
    assert cls is not None
    assert cls.name == "class2"
    assert fake_interface.get_class("nonexistent") is None


def test_get_function(fake_interface):
    func = fake_interface.get_function("function2")
    assert func is not None
    assert func.name == "function2"
    assert fake_interface.get_function("nonexistent") is None


def test_get_export(fake_interface):
    export_item = fake_interface.get_export("export_item3")
    assert export_item is not None
    assert export_item.name == "export_item3"
    assert fake_interface.get_export("nonexistent") is None


def test_get_import(fake_interface):
    imp = fake_interface.get_import("import1")
    assert imp is not None
    assert imp.name == "import1"
    assert fake_interface.get_import("nonexistent") is None
