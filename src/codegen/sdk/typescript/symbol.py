from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Self, Unpack

from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Value
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.interfaces.exportable import Exportable
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.type_alias import TypeAlias
from codegen.sdk.enums import ImportType, NodeType
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.statements.comment import TSComment, TSCommentType
from codegen.sdk.typescript.symbol_groups.comment_group import TSCommentGroup
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.flagging.code_flag import CodeFlag
    from codegen.sdk.codebase.flagging.enums import FlagKwargs
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.interfaces.has_block import TSHasBlock


@ts_apidoc
class TSSymbol(Symbol["TSHasBlock", "TSCodeBlock"], Exportable):
    """A TypeScript symbol representing a code element with advanced manipulation capabilities.

    This class extends Symbol and Exportable to provide TypeScript-specific functionality for managing
    code symbols. It offers methods for handling imports, comments, code refactoring, and file operations
    like moving symbols between files while maintaining their dependencies and references.

    The class provides functionality for managing both inline and block comments, setting and retrieving
    import strings, and maintaining semicolon presence. It includes capabilities for moving symbols between
    files with options to handle dependencies and import strategy selection.
    """

    @reader
    def get_import_string(self, alias: str | None = None, module: str | None = None, import_type: ImportType = ImportType.UNKNOWN, is_type_import: bool = False) -> str:
        """Generates the appropriate import string for a symbol.

        Constructs and returns an import statement string based on the provided parameters, formatting it according
        to TypeScript import syntax rules.

        Args:
            alias (str | None, optional): The alias to use for the imported symbol. Defaults to None.
            module (str | None, optional): The module to import from. If None, uses the file's import module name.
                Defaults to None.
            import_type (ImportType, optional): The type of import to generate (e.g., WILDCARD). Defaults to
                ImportType.UNKNOWN.
            is_type_import (bool, optional): Whether this is a type-only import. Defaults to False.

        Returns:
            str: A formatted import statement string.
        """
        type_prefix = "type " if is_type_import else ""
        import_module = module if module is not None else self.file.import_module_name

        if import_type == ImportType.WILDCARD:
            file_as_module = self.file.name
            return f"import {type_prefix}* as {file_as_module} from {import_module};"
        elif alias is not None and alias != self.name:
            return f"import {type_prefix}{{ {self.name} as {alias} }} from {import_module};"
        else:
            return f"import {type_prefix}{{ {self.name} }} from {import_module};"

    @property
    @reader(cache=False)
    def extended_nodes(self) -> list[Editable]:
        """Returns the list of nodes associated with this symbol including extended nodes.

        This property returns a list of Editable nodes that includes any wrapping or extended symbols like `export`, `public`, or decorators.
        For example, if the symbol is within an `export_statement` or `lexical_declaration`, those nodes will be included in the list.

        Args:
            No arguments.

        Returns:
            list[Editable]: A list of Editable nodes including the symbol's extended nodes like export statements and decorators.
        """
        nodes = super().extended_nodes

        # Check if the symbol is wrapped by another node like 'export_statement'
        new_ts_node = self.ts_node
        while (parent := new_ts_node.parent).type in ("export_statement", "lexical_declaration", "variable_declarator"):
            new_ts_node = parent

        return [Value(new_ts_node, self.file_node_id, self.ctx, self.parent) if node.ts_node == self.ts_node else node for node in nodes]

    @property
    @reader
    def comment(self) -> TSCommentGroup | None:
        """Retrieves the comment group associated with the symbol.

        Returns the TSCommentGroup object that contains any comments associated with the symbol.
        A comment group represents one or more related comments that precede the symbol in the code.

        Returns:
            TSCommentGroup | None: The comment group for the symbol if one exists, None otherwise.
        """
        return TSCommentGroup.from_symbol_comments(self)

    @property
    @reader
    def inline_comment(self) -> TSCommentGroup | None:
        """Property that retrieves the inline comment group associated with the symbol.

        Args:
            None

        Returns:
            TSCommentGroup | None: The inline comment group associated with the symbol if it exists,
                otherwise None.
        """
        return TSCommentGroup.from_symbol_inline_comments(self)

    @writer
    def set_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True, comment_type: TSCommentType = TSCommentType.DOUBLE_SLASH) -> None:
        """Sets a comment to the symbol.

        Adds or updates a comment for a code symbol. If a comment already exists, it will be edited. If no
        comment exists, a new comment group will be created.

        Args:
            comment (str): The comment text to be added.
            auto_format (bool, optional): Whether to automatically format the text into a comment syntax.
                Defaults to True.
            clean_format (bool, optional): Whether to clean the format of the comment before inserting.
                Defaults to True.
            comment_type (TSCommentType, optional): The style of comment to add.
                Defaults to TSCommentType.DOUBLE_SLASH.

        Returns:
            None

        Raises:
            None
        """
        if clean_format:
            comment = TSComment.clean_comment(comment)

        # If comment already exists, add the comment to the existing comment group
        if self.comment:
            if auto_format:
                self.comment.edit_text(comment)
            else:
                self.comment.edit(comment, fix_indentation=True)
        else:
            if auto_format:
                comment = TSComment.generate_comment(comment, comment_type)
            self.insert_before(comment, fix_indentation=True)

    @writer
    def add_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True, comment_type: TSCommentType = TSCommentType.DOUBLE_SLASH) -> None:
        """Adds a new comment to the symbol.

        Appends a comment to an existing comment group or creates a new comment group if none exists.

        Args:
            comment (str): The comment text to be added.
            auto_format (bool): Whether to automatically format the text into a comment style. Defaults to True.
            clean_format (bool): Whether to clean the format of the comment before inserting. Defaults to True.
            comment_type (TSCommentType): Type of comment to add. Defaults to TSCommentType.DOUBLE_SLASH.

        Returns:
            None

        Raises:
            None
        """
        if clean_format:
            comment = TSComment.clean_comment(comment)
        if auto_format:
            comment = TSComment.generate_comment(comment, comment_type)

        # If comment already exists, add the comment to the existing comment group
        if self.comment:
            self.comment.insert_after(comment, fix_indentation=True)
        else:
            self.insert_before(comment, fix_indentation=True)

    @writer
    def set_inline_comment(self, comment: str, auto_format: bool = True, clean_format: bool = True, node: TSNode | None = None) -> None:
        """Sets an inline comment to the symbol.

        Sets or replaces an inline comment for a symbol at its current position. If an inline comment
        already exists, it is replaced with the new comment. If no inline comment exists, a new one
        will be created adjacent to the symbol.

        Args:
            comment (str): The inline comment text to be added.
            auto_format (bool, optional): Whether to automatically format the text as a comment.
                Defaults to True.
            clean_format (bool, optional): Whether to clean the comment format before inserting.
                Defaults to True.
            node (TSNode | None, optional): The specific node to attach the comment to.
                Defaults to None.

        Returns:
            None

        Raises:
            None
        """
        if clean_format:
            comment = TSComment.clean_comment(comment)

        if self.inline_comment:
            if auto_format:
                self.inline_comment.edit_text(comment)
            else:
                self.inline_comment.edit(comment)
        else:
            if auto_format:
                comment = "  " + TSComment.generate_comment(comment, TSCommentType.DOUBLE_SLASH)
            node = node or self.ts_node
            Value(node, self.file_node_id, self.ctx, self).insert_after(comment, fix_indentation=False, newline=False)

    @property
    @reader
    def semicolon_node(self) -> Editable | None:
        """Retrieves the semicolon node associated with a TypeScript symbol.

        A semicolon node is a TreeSitter node of type ';' that appears immediately after the symbol node.

        Returns:
            Editable | None: The semicolon node wrapped as an Editable if it exists, None otherwise.
        """
        sibbling = self.ts_node.next_sibling
        if sibbling and sibbling.type == ";":
            return Value(sibbling, self.file_node_id, self.ctx, self)
        return None

    @property
    @reader
    def has_semicolon(self) -> bool:
        """Checks whether the current symbol has a semicolon at the end.

        This property determines if a semicolon is present at the end of the symbol by checking
        if the semicolon_node property exists.

        Returns:
            bool: True if the symbol has a semicolon at the end, False otherwise.
        """
        return self.semicolon_node is not None

    @noapidoc
    def _move_to_file(
        self,
        file: SourceFile,
        encountered_symbols: set[Symbol | Import],
        include_dependencies: bool = True,
        strategy: Literal["add_back_edge", "update_all_imports", "duplicate_dependencies"] = "update_all_imports",
    ) -> tuple[NodeId, NodeId]:
        # TODO: Prevent creation of import loops (!) - raise a ValueError and make the agent fix it
        # =====[ Arg checking ]=====
        if file == self.file:
            return file.file_node_id, self.node_id

        # =====[ Move over dependencies recursively ]=====
        if include_dependencies:
            try:
                for dep in self.dependencies:
                    if dep in encountered_symbols:
                        continue

                    # =====[ Symbols - move over ]=====
                    elif isinstance(dep, TSSymbol):
                        if dep.is_top_level:
                            encountered_symbols.add(dep)
                            dep._move_to_file(file, encountered_symbols=encountered_symbols, include_dependencies=True, strategy=strategy)

                    # =====[ Imports - copy over ]=====
                    elif isinstance(dep, TSImport):
                        if dep.imported_symbol:
                            file.add_import(dep.imported_symbol, alias=dep.alias.source, import_type=dep.import_type)
                        else:
                            file.add_import(dep.source)

                    else:
                        msg = f"Unknown dependency type {type(dep)}"
                        raise ValueError(msg)
            except Exception as e:
                print(f"Failed to move dependencies of {self.name}: {e}")
        else:
            try:
                for dep in self.dependencies:
                    if isinstance(dep, Assignment):
                        msg = "Assignment not implemented yet"
                        raise NotImplementedError(msg)

                    # =====[ Symbols - move over ]=====
                    elif isinstance(dep, Symbol) and dep.is_top_level:
                        file.add_import(imp=dep, alias=dep.name, import_type=ImportType.NAMED_EXPORT, is_type_import=isinstance(dep, TypeAlias))

                        if not dep.is_exported:
                            dep.file.add_export_to_symbol(dep)
                        pass

                    # =====[ Imports - copy over ]=====
                    elif isinstance(dep, TSImport):
                        if dep.imported_symbol:
                            file.add_import(dep.imported_symbol, alias=dep.alias.source, import_type=dep.import_type, is_type_import=dep.is_type_import())
                        else:
                            file.add_import(dep.source)

            except Exception as e:
                print(f"Failed to move dependencies of {self.name}: {e}")

        # =====[ Make a new symbol in the new file ]=====
        # This will update all edges etc.
        file.add_symbol(self)
        import_line = self.get_import_string(module=file.import_module_name)

        # =====[ Checks if symbol is used in original file ]=====
        # Takes into account that it's dependencies will be moved
        is_used_in_file = any(usage.file == self.file and usage.node_type == NodeType.SYMBOL and usage not in encountered_symbols for usage in self.symbol_usages)

        # ======[ Strategy: Duplicate Dependencies ]=====
        if strategy == "duplicate_dependencies":
            # If not used in the original file. or if not imported from elsewhere, we can just remove the original symbol
            if not is_used_in_file and not any(usage.kind is UsageKind.IMPORTED and usage.usage_symbol not in encountered_symbols for usage in self.usages):
                self.remove()

        # ======[ Strategy: Add Back Edge ]=====
        # Here, we will add a "back edge" to the old file importing the self
        elif strategy == "add_back_edge":
            if is_used_in_file:
                self.file.add_import(import_line)
                if self.is_exported:
                    self.file.add_import(f"export {{ {self.name} }}")
            elif self.is_exported:
                module_name = file.name
                self.file.add_import(f"export {{ {self.name} }} from '{module_name}'")
            # Delete the original symbol
            self.remove()

        # ======[ Strategy: Update All Imports ]=====
        # Update the imports in all the files which use this symbol to get it from the new file now
        elif strategy == "update_all_imports":
            for usage in self.usages:
                if isinstance(usage.usage_symbol, TSImport):
                    # Add updated import
                    if usage.usage_symbol.resolved_symbol is not None and usage.usage_symbol.resolved_symbol.node_type == NodeType.SYMBOL and usage.usage_symbol.resolved_symbol == self:
                        usage.usage_symbol.file.add_import(import_line)
                        usage.usage_symbol.remove()
                elif usage.usage_type == UsageType.CHAINED:
                    # Update all previous usages of import * to the new import name
                    if usage.match and "." + self.name in usage.match:
                        if isinstance(usage.match, FunctionCall):
                            usage.match.get_name().edit(self.name)
                        if isinstance(usage.match, ChainedAttribute):
                            usage.match.edit(self.name)
                        usage.usage_symbol.file.add_import(import_line)
            if is_used_in_file:
                self.file.add_import(import_line)
            # Delete the original symbol
            self.remove()

    def _convert_proptype_to_typescript(self, prop_type: Editable, param: Parameter | None, level: int) -> str:
        """Converts a PropType definition to its TypeScript equivalent."""
        # Handle basic types
        type_map = {"string": "string", "number": "number", "bool": "boolean", "object": "object", "array": "any[]", "func": "CallableFunction"}
        if prop_type.source in type_map:
            return type_map[prop_type.source]
        if isinstance(prop_type, ChainedAttribute):
            if prop_type.attribute.source == "node":
                return "T"
            if prop_type.attribute.source == "element":
                self.file.add_import("import React from 'react';\n")
                return "React.ReactElement"
            if prop_type.attribute.source in type_map:
                return type_map[prop_type.attribute.source]
                # if prop_type.attribute.source == "func":
                # params = []
                # if param:
                #     for usage in param.usages:
                #         call = None
                #         if isinstance(usage.match, FunctionCall):
                #             call = usage.match
                #         elif isinstance(usage.match.parent, FunctionCall):
                #             call = usage.match.parent
                #         if call:
                #             for arg in call.args:
                #                 resolved_value = arg.value.resolved_value
                #                 if resolved_value.rstrip("[]") not in ("number", "string", "boolean", "any", "object"):
                #                     resolved_value = "any"
                #                 params.append(f"{arg.name or arg.source}: {resolved_value}")
                # return f"({",".join(params)}) => void"
                return "Function"
            if prop_type.attribute.source == "isRequired":
                return self._convert_proptype_to_typescript(prop_type.object, param, level)
        if isinstance(prop_type, FunctionCall):
            if prop_type.name == "isRequired":
                return self._convert_proptype_to_typescript(prop_type.args[0].value, param, level)
            # Handle arrays
            if prop_type.name == "arrayOf":
                item = self._convert_proptype_to_typescript(prop_type.args[0].value, param, level)
                # needs_parens = isinstance(prop_type.args[0].value, FunctionCall)
                needs_parens = False
                return f"({item})[]" if needs_parens else f"{item}[]"

            # Handle oneOf
            if prop_type.name == "oneOf":
                values = [arg.source for arg in prop_type.args[0].value]
                # Add parentheses if one of the values is a function
                return " | ".join(f"({t})" if "() => void" == t else t for t in values)
            # Handle anyOf (alias for oneOf)
            if prop_type.name == "anyOf":
                values = [arg.source for arg in prop_type.args[0].value]
                # Add parentheses if one of the values is a function
                return " | ".join(f"({t})" if "() => void" == t else t for t in values)

            # Handle oneOfType
            if prop_type.name == "oneOfType":
                types = [self._convert_proptype_to_typescript(arg, param, level) for arg in prop_type.args[0].value]
                # Only add parentheses if one of the types is a function
                return " | ".join(f"({t})" if "() => void" == t else t for t in types)

            # Handle shape
            if prop_type.name == "shape":
                return self._convert_dict(prop_type.args[0].value, level)
            if prop_type.name == "objectOf":
                return self._convert_object_of(prop_type.args[0].value, level)
        return "any"

    def _convert_dict(self, value: Type, level: int) -> str:
        """Converts a dictionary of PropTypes to a TypeScript interface string."""
        result = "{\n"
        for key, value in value.items():
            is_required = isinstance(value, ChainedAttribute) and value.attribute.source == "isRequired"
            optional = "" if is_required else "?"
            indent = "    " * level
            param = next((p for p in self.parameters if p.name == key), None) if self.parameters else None
            result += f"{indent}{key}{optional}: {self._convert_proptype_to_typescript(value, param, level + 1)};\n"
        indent = "    " * (level - 1)

        result += f"{indent}}}"
        return result

    def _convert_object_of(self, value: Type, level: int) -> str:
        """Converts a dictionary of PropTypes to a TypeScript interface string."""
        indent = "    " * level
        prev_indent = "    " * (level - 1)
        type_value = self._convert_proptype_to_typescript(value, None, level + 1)
        return f"{{\n{indent}[key: string]: {type_value};\n{prev_indent}}}"

    def _get_static_prop_types(self) -> Type | None:
        """Returns a dictionary of prop types for a React component."""
        for usage in self.usages:
            if isinstance(usage.usage_symbol, Assignment) and usage.usage_symbol.name == "propTypes":
                assert isinstance(usage.usage_symbol.value, Type), usage.usage_symbol.value.__class__
                return usage.usage_symbol.value
        return None

    @noapidoc
    def convert_to_react_interface(self) -> str | None:
        if not self.is_jsx:
            return None

        component_name = self.name
        # Handle class components with static propTypes
        if proptypes := self._get_static_prop_types():
            generics = ""
            generic_name = ""
            if "PropTypes.node" in proptypes.source:
                generics = "<T extends React.ReactNode>"
                generic_name = "<React.ReactNode>"
                self.file.add_import("import React from 'react';\n")
            interface_name = f"{component_name}Props"
            # Create interface definition
            interface_def = f"interface {interface_name}{generics} {self._convert_dict(proptypes, 1)}"

            # Insert interface and update component
            self.insert_before(interface_def + "\n")

            proptypes.parent_statement.remove()
            for imp in self.file.imports:
                if imp.module.source.strip("'").strip('"') in ("react", "prop-types"):
                    imp.remove_if_unused()
            return interface_name + generic_name

    @writer
    def flag(self, **kwargs: Unpack[FlagKwargs]) -> CodeFlag[Self]:
        """Flags a TypeScript symbol by adding a flag comment and returning a CodeFlag.

        This implementation first creates the CodeFlag through the standard flagging system,
        then adds a TypeScript-specific comment to visually mark the flagged code.

        Args:
            **kwargs: Flag keyword arguments including optional 'message'

        Returns:
            CodeFlag[Self]: The code flag object for tracking purposes
        """
        # First create the standard CodeFlag through the base implementation
        code_flag = super().flag(**kwargs)

        # Add a TypeScript comment to visually mark the flag
        message = kwargs.get("message", "")
        if message:
            self.set_inline_comment(f"🚩 {message}")

        return code_flag
