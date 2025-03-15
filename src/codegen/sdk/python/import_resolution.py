from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.expressions import Name
from codegen.sdk.core.import_resolution import ExternalImportResolver, Import, ImportResolution
from codegen.sdk.enums import ImportType, NodeType
from codegen.shared.decorators.docs import noapidoc, py_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.exportable import Exportable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.import_statement import ImportStatement
    from codegen.sdk.python.file import PyFile
    from src.codegen.sdk.core.file import SourceFile


logger = get_logger(__name__)


@py_apidoc
class PyImport(Import["PyFile"]):
    """Extends Import for Python codebases."""

    @reader
    def is_module_import(self) -> bool:
        """Determines if the import is a module-level or wildcard import.

        Checks whether the import is either a module import (e.g. 'import foo') or a wildcard import (e.g. 'from foo import *').

        Returns:
            bool: True if the import is a module-level or wildcard import, False otherwise.
        """
        return self.import_type in [ImportType.MODULE, ImportType.WILDCARD]

    @property
    @reader
    def namespace(self) -> str | None:
        """Returns the namespace of the import if it imports a file, or None otherwise.

        This property determines the namespace for file imports. It returns None for wildcard imports. For file
        imports (where resolved_symbol is a FILE), it returns the alias source. For all other cases, it returns None.

        Returns:
            str | None: The namespace string for file imports, None for wildcard imports or non-file imports.
        """
        if self.is_wildcard_import():
            return None

        resolved_symbol = self.resolved_symbol
        if resolved_symbol is not None and resolved_symbol.node_type == NodeType.FILE:
            return self.alias.source
        return None

    @property
    @reader
    def imported_exports(self) -> list[Exportable]:
        """Returns a list of exports from an import statement.

        Returns the enumerated list of symbols imported from a module import. If the import is
        not a module import, returns a list containing just the single imported symbol.
        For imports that don't resolve to any symbol, returns an empty list.

        Returns:
            list[Exportable]: A list of exported symbols. For module imports, contains all symbols
                and imports from the imported module. For non-module imports, contains a single imported
                symbol. For unresolved imports, returns empty list.
        """
        if self.imported_symbol is None:
            return []

        if not self.is_module_import():
            return [self.imported_symbol]

        return self.imported_symbol.symbols + self.imported_symbol.imports

    @noapidoc
    @reader
    def resolve_import(self, base_path: str | None = None, *, add_module_name: str | None = None) -> ImportResolution[PyFile] | None:
        try:
            base_path = base_path or self.ctx.projects[0].base_path or ""
            module_source = self.module.source if self.module else ""
            symbol_name = self.symbol_name.source if self.symbol_name else ""
            if add_module_name:
                module_source += f".{symbol_name}"
                symbol_name = add_module_name
            # If import is relative, convert to absolute path
            if module_source.startswith("."):
                module_source = self._relative_to_absolute_import(module_source)

            # =====[ Check if we are importing an entire file ]=====
            if self.is_module_import():
                # covers `import a.b.c` case and `from a.b.c import *` case
                filepath = os.path.join(base_path, module_source.replace(".", "/") + ".py")
            else:
                # This is the case where you do:
                # `from a.b.c import foo`
                filepath = os.path.join(
                    base_path,
                    module_source.replace(".", "/") + "/" + symbol_name + ".py",
                )

            # =====[ Check if we are importing an entire file with custom resolve path or sys.path enabled ]=====
            if len(self.ctx.config.import_resolution_paths) > 0 or self.ctx.config.py_resolve_syspath:
                # Handle resolve overrides first if both is set
                resolve_paths: list[str] = self.ctx.config.import_resolution_paths + (sys.path if self.ctx.config.py_resolve_syspath else [])
                if file := self._file_by_custom_resolve_paths(resolve_paths, filepath):
                    return ImportResolution(from_file=file, symbol=None, imports_file=True)

            # =====[ Default path ]=====
            if file := self.ctx.get_file(filepath):
                return ImportResolution(from_file=file, symbol=None, imports_file=True)

            filepath = filepath.replace(".py", "/__init__.py")
            if file := self.ctx.get_file(filepath):
                # TODO - I think this is another edge case, due to `dao/__init__.py` etc.
                # You can't do `from a.b.c import foo` => `foo.utils.x` right now since `foo` is just a file...
                return ImportResolution(from_file=file, symbol=None, imports_file=True)

            # =====[ Check if `module.py` file exists in the graph with custom resolve path or sys.path enabled  ]=====
            filepath = module_source.replace(".", "/") + ".py"
            if len(self.ctx.config.import_resolution_paths) > 0 or self.ctx.config.py_resolve_syspath:
                # Handle resolve overrides first if both is set
                resolve_paths: list[str] = self.ctx.config.import_resolution_paths + (sys.path if self.ctx.config.py_resolve_syspath else [])
                if file := self._file_by_custom_resolve_paths(resolve_paths, filepath):
                    symbol = file.get_node_by_name(symbol_name)
                    return ImportResolution(from_file=file, symbol=symbol)

            # =====[ Check if `module.py` file exists in the graph ]=====
            filepath = os.path.join(base_path, filepath)
            if file := self.ctx.get_file(filepath):
                symbol = file.get_node_by_name(symbol_name)
                if symbol is None:
                    if file.get_node_from_wildcard_chain(symbol_name):
                        return ImportResolution(from_file=file, symbol=None, imports_file=True)
                    else:
                        # This is most likely a broken import
                        return ImportResolution(from_file=file, symbol=None)
                else:
                    return ImportResolution(from_file=file, symbol=symbol)

            # =====[ Check if `module/__init__.py` file exists in the graph with custom resolve path or sys.path enabled ]=====
            filepath = filepath.replace(".py", "/__init__.py")
            if len(self.ctx.config.import_resolution_paths) > 0 or self.ctx.config.py_resolve_syspath:
                # Handle resolve overrides first if both is set
                resolve_paths: list[str] = self.ctx.config.import_resolution_paths + (sys.path if self.ctx.config.py_resolve_syspath else [])
                if from_file := self._file_by_custom_resolve_paths(resolve_paths, filepath):
                    symbol = from_file.get_node_by_name(symbol_name)
                    if symbol is None:
                        if from_file.get_node_from_wildcard_chain(symbol_name):
                            return ImportResolution(from_file=from_file, symbol=None, imports_file=True)
                        else:
                            # This is most likely a broken import
                            return ImportResolution(from_file=from_file, symbol=None)

                    else:
                        return ImportResolution(from_file=from_file, symbol=symbol)

            # =====[ Check if `module/__init__.py` file exists in the graph ]=====
            if from_file := self.ctx.get_file(filepath):
                symbol = from_file.get_node_by_name(symbol_name)
                if symbol is None:
                    if from_file.get_node_from_wildcard_chain(symbol_name):
                        return ImportResolution(from_file=from_file, symbol=None, imports_file=True)
                    else:
                        # This is most likely a broken import
                        return ImportResolution(from_file=from_file, symbol=None)

                else:
                    return ImportResolution(from_file=from_file, symbol=symbol)

            # =====[ Case: Can't resolve the import ]=====
            if base_path == "":
                # Try to resolve with "src" as the base path
                return self.resolve_import(base_path="src", add_module_name=add_module_name)
            if base_path == "src":
                # Try "test" next
                return self.resolve_import(base_path="test", add_module_name=add_module_name)

            # if not G_override:
            #     for resolver in ctx.import_resolvers:
            #         if imp := resolver.resolve(self):
            #             return imp

            return None
            # # =====[ Check if we are importing an external module in the graph ]=====
            # if ext := self.ctx.get_external_module(self.source, self._unique_node.source):
            #     return ImportResolution(symbol=ext)
            # # Implies we are not importing the symbol from the current repo.
            # # In these cases, consider the import as an ExternalModule and add to graph
            # ext = ExternalModule.from_import(self)
            # return ImportResolution(symbol=ext)
        except AssertionError:
            # Codebase is probably trying to import file from outside repo
            return None

    @noapidoc
    @reader
    def _file_by_custom_resolve_paths(self, resolve_paths: list[str], filepath: str) -> SourceFile | None:
        """Check if a certain file import can be found within a set sys.path

        Returns either None or the SourceFile.
        """
        for resolve_path in resolve_paths:
            filepath_new: str = os.path.join(resolve_path, filepath)
            try:
                file = self.ctx.get_file(filepath_new)
            except AssertionError as e:
                file = None
            if file:
                return file

        return None

    @noapidoc
    @reader
    def _relative_to_absolute_import(self, relative_import: str) -> str:
        """Helper to go from a relative import to an absolute one.
        Ex: ".foo.bar" in "src/file.py" would be -> "src.foo.bar"
        Ex: "..foo.bar" in "project/src/file.py" would be -> "project.foo.bar"
        """
        # Get the directory of the current file
        current_dir = os.path.dirname(self.to_file.file_path)

        # Count the number of dots at the start of the relative import
        dot_count = 0
        while relative_import.startswith("."):
            dot_count += 1
            relative_import = relative_import[1:]

        # Go up in the directory structure based on the number of dots
        for _ in range(dot_count - 1):
            current_dir = os.path.dirname(current_dir)

        # Convert the remaining path to a Python import path
        base_path = os.path.normpath(current_dir).replace(os.sep, ".")

        # Remove any leading '.' from the base_path
        while base_path.startswith("."):
            base_path = base_path[1:]

        # Combine the base path with the relative import
        if relative_import:
            return f"{base_path}.{relative_import}" if base_path else relative_import
        else:
            return base_path

    @classmethod
    @noapidoc
    def from_import_statement(cls, import_statement: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: ImportStatement) -> list[PyImport]:
        imports = []
        for module_node in import_statement.children_by_field_name("name"):
            if module_node.type == "dotted_name":
                imports.append(cls(import_statement, file_node_id, ctx, parent, module_node=module_node, name_node=module_node, alias_node=module_node, import_type=ImportType.MODULE))
            elif module_node.type == "aliased_import":
                module = module_node.child_by_field_name("name")
                symbol_name = module
                alias = module_node.child_by_field_name("alias")
                imports.append(cls(import_statement, file_node_id, ctx, parent, module_node=module, name_node=symbol_name, alias_node=alias, import_type=ImportType.MODULE))
            else:
                logger.error(f"Unsupported import statement: {import_statement.text.decode('utf-8')}")
        return imports

    @classmethod
    @noapidoc
    def from_import_from_statement(cls, import_statement: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: ImportStatement) -> list[PyImport]:
        module_node = import_statement.child_by_field_name("module_name")
        import_symbols = import_statement.children_by_field_name("name")
        if len(import_symbols) == 0:
            wildcard_import = next((node for node in import_statement.children if node.type == "wildcard_import"), None)
            if wildcard_import is None:
                msg = f"Unsupported import statement: {import_statement.text.decode('utf-8')}"
                raise ValueError(msg)
            return [cls(import_statement, file_node_id, ctx, parent, module_node=module_node, name_node=module_node, alias_node=module_node, import_type=ImportType.WILDCARD)]

        imports = []
        for import_symbol in import_symbols:
            if import_symbol.type == "dotted_name":
                imp = cls(import_statement, file_node_id, ctx, parent, module_node=module_node, name_node=import_symbol, alias_node=import_symbol, import_type=ImportType.NAMED_EXPORT)
            elif import_symbol.type == "aliased_import":
                symbol_name = import_symbol.child_by_field_name("name")
                alias = import_symbol.child_by_field_name("alias")
                imp = cls(import_statement, file_node_id, ctx, parent, module_node=module_node, name_node=symbol_name, alias_node=alias, import_type=ImportType.NAMED_EXPORT)
            else:
                msg = f"Unsupported import statement: {import_statement.text.decode('utf-8')}"
                raise ValueError(msg)
            imports.append(imp)
        return imports

    @classmethod
    @noapidoc
    def from_future_import_statement(cls, import_statement: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: ImportStatement) -> list[PyImport]:
        imports = []
        for module_node in import_statement.children_by_field_name("name"):
            imp = cls(import_statement, file_node_id, ctx, parent, module_node=module_node, name_node=module_node, alias_node=module_node, import_type=ImportType.SIDE_EFFECT)
            imports.append(imp)
        return imports

    @property
    @reader
    def import_specifier(self) -> Editable:
        """Retrieves the import specifier node for this import.

        Finds and returns the import specifier node that matches either the alias or symbol name of this import.

        Args:
            None

        Returns:
            Editable: The import specifier node as a Name object if found, None otherwise.
        """
        import_specifiers = self.ts_node.children_by_field_name("name")
        for import_specifier in import_specifiers:
            if import_specifier.type == "aliased_import":
                is_match = self.alias.source == import_specifier.child_by_field_name("alias").text.decode("utf-8")
            else:
                is_match = self.symbol_name.source == import_specifier.text.decode("utf-8")
            if is_match:
                return Name(import_specifier, self.file_node_id, self.ctx, self)

    @reader
    def get_import_string(
        self,
        alias: str | None = None,
        module: str | None = None,
        import_type: ImportType = ImportType.UNKNOWN,
        is_type_import: bool = False,
    ) -> str:
        """Generates an import string for a Python import statement.

        Creates a formatted import statement string based on the provided parameters. The generated string can represent different types of imports including wildcard imports and aliased imports.

        Args:
            alias (str | None): Optional alias name for the imported symbol.
            module (str | None): Optional module name to import from. If not provided, uses the file's import module name.
            import_type (ImportType): Type of import to generate. Defaults to UNKNOWN.
            is_type_import (bool): Whether this is a type import. Defaults to False.

        Returns:
            str: A formatted import statement string.
        """
        import_module = module if module is not None else self.file.import_module_name
        if import_type == ImportType.WILDCARD:
            file_as_module = self.file.name
            return f"from {import_module} import * as {file_as_module}"
        elif alias is not None and alias != self.name:
            return f"from {import_module} import {self.name} as {alias}"
        else:
            return f"from {import_module} import {self.name}"


class PyExternalImportResolver(ExternalImportResolver):
    def __init__(self, from_alias: str, to_context: CodebaseContext) -> None:
        self.from_alias = from_alias
        self.to_context = to_context

    def resolve(self, imp: PyImport) -> str | None:
        module_source = imp.module.source if imp.module else ""
        if module_source.startswith(self.from_alias):
            return imp.resolve_import(G_override=self.to_context)
