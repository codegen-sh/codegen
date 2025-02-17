from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.expressions import Name
from codegen.sdk.core.statements.statement import StatementType

if TYPE_CHECKING:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.statements.statement import Statement
    from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
    from codegen.sdk.typescript.function import TSFunction


class TSPromiseChain:
    """A class representing a TypeScript Promise chain.

    This class parses and handles Promise chains in TypeScript code, including .then(), .catch(), and .finally() chains.
    It provides functionality to convert Promise chains to async/await syntax.
    """

    base_chain: list[FunctionCall | Name]
    then_chain: list[FunctionCall]
    catch_call: FunctionCall | None
    finally_call: FunctionCall | None
    after_promise_chain: list[FunctionCall | Name]
    base_attribute: Name
    parent_statement: Statement
    parent_function: FunctionCall
    parent_class: Class
    declared_vars: set[str]
    base_indent: str
    name: str | None
    log_statements: list[str] = ["console.error", "console.warn", "console.log"]

    def __init__(self, attribute_chain: list[FunctionCall | Name]) -> None:
        """Initialize a TSPromiseChain instance.

        Args:
            attribute_chain: A list of function calls or a Name object representing the Promise chain
        """
        # Parse the chain and assign all attributes
        (self.base_chain, self.then_chain, self.catch_call, self.finally_call, self.after_promise_chain) = self._parse_chain(attribute_chain)

        self.base_attribute = self.base_chain[-1].parent.object
        self.parent_statement = self.base_chain[0].parent_statement
        self.parent_function = self.parent_statement.parent_function
        self.parent_class = self.parent_statement.parent_class
        self.declared_vars = set()
        self.base_indent = " " * self.parent_statement._get_indent()
        self.name = self.base_chain[0].source if isinstance(self.base_chain[0], Name) else self.base_chain[0].name

    @reader
    def _parse_chain(self, attribute_chain: list[FunctionCall | Name]) -> tuple[list[FunctionCall], list[FunctionCall], FunctionCall | None, FunctionCall | None, list[FunctionCall | Name]]:
        """Parse the Promise chain into its component parts.

        Args:
            attribute_chain: The chain of function calls to parse

        Returns:
            A tuple containing:
                - base_chain: Initial function calls
                - then_chain: .then() calls
                - catch_call: .catch() call if present
                - finally_call: .finally() call if present
                - after_promise_chain: Calls after the Promise chain
        """
        base_chain: list[FunctionCall | Name] = []
        then_chain: list[FunctionCall] = []
        catch_call: FunctionCall | None = None
        finally_call: FunctionCall | None = None
        after_promise_chain: list[FunctionCall | Name] = []

        in_then_chain: bool = False
        promise_chain_ended: bool = False

        for attribute in attribute_chain:
            if not isinstance(attribute, Name):
                if attribute.name == "then":
                    in_then_chain = True
                    then_chain.append(attribute)
                elif attribute.name == "catch":
                    catch_call = attribute
                    in_then_chain = False
                elif attribute.name == "finally":
                    finally_call = attribute
                    in_then_chain = False
                    promise_chain_ended = True
                else:
                    if promise_chain_ended:
                        after_promise_chain.append(attribute)
                    elif in_then_chain:
                        then_chain.append(attribute)
                    else:
                        base_chain.append(attribute)
            else:
                if promise_chain_ended:
                    after_promise_chain.append(attribute)
                elif in_then_chain:
                    then_chain.append(attribute)
                else:
                    base_chain.append(attribute)

        return base_chain, then_chain, catch_call, finally_call, after_promise_chain

    @property
    @reader
    def is_return_statement(self) -> bool:
        """Check if the parent statement is a return statement.

        Returns:
            bool: True if the parent statement is a return statement
        """
        return self.parent_statement.statement_type == StatementType.RETURN_STATEMENT

    @property
    @reader
    def assigned_var(self) -> str | None:
        """Get the variable being assigned to in an assignment statement.

        Returns:
            Optional[str]: The name of the variable being assigned to, or None if not an assignment
        """
        if self.parent_statement.statement_type == StatementType.ASSIGNMENT:
            return self.parent_statement.left

    @reader
    def get_next_call_params(self, call: FunctionCall | None) -> list[str]:
        from codegen.sdk.typescript.function import TSFunction

        """Get parameters from the next then/catch/finally call.

        Args:
            call: The function call to extract parameters from

        Returns:
            List[str]: List of parameter names from the call
        """
        # handling the .then in parameter function
        if call and len(call.args) > 0 and isinstance(call.args[0].value, TSFunction):
            return [p.source for p in call.args[0].value.parameters]

        return []

    @reader
    def _needs_anonymous_function(self, arrow_fn: TSFunction) -> bool:
        """Determine if we need to use an anonymous function wrapper.

        Returns True if:
        1. There are multiple return statements
        2. The code block has complex control flow (if/else, loops, etc)

        Args:
            arrow_fn: The arrow function to analyze

        Returns:
            bool: True if an anonymous function wrapper is needed
        """
        statements = arrow_fn.code_block.get_statements()
        return_count = sum(1 for stmt in statements if stmt.statement_type == StatementType.RETURN_STATEMENT)
        return return_count > 1

    @reader
    def format_param_assignment(self, params: list[str], base_expr: str, declare: bool = True) -> str:
        """Format parameter assignment with proper let declaration if needed.

        Args:
            params: List of parameter names to assign
            base_expr: The base expression to assign from
            declare: Whether to declare new variables with 'let'

        Returns:
            str: Formatted parameter assignment string
        """
        if not params:
            return base_expr

        if len(params) > 1:
            param_str = ", ".join(params)
            if declare and not any(p in self.declared_vars for p in params):
                self.declared_vars.update(params)
                return f"let [{param_str}] = {base_expr}"
            return f"[{param_str}] = {base_expr}"
        else:
            param = params[0]
            if declare and param not in self.declared_vars:
                self.declared_vars.add(param)
                return f"let {param} = {base_expr}"
            return f"{param} = {base_expr}"

    @reader
    def handle_base_call(self) -> str:
        """Format the base promise call.

        Returns:
            str: Formatted base call string
        """
        new_handle = None
        if "await" not in self.base_attribute.extended_source:
            new_handle = f"await {self.base_attribute.extended_source};"
        else:
            new_handle = f"{self.base_attribute.extended_source};"

        next_params = self.get_next_call_params(self.then_chain[0])
        if next_params:
            new_handle = self.format_param_assignment(next_params, new_handle)
        return new_handle

    @reader
    def handle_then_block(self, call: FunctionCall, next_call: FunctionCall | None = None) -> str:
        from codegen.sdk.typescript.function import TSFunction

        """Format a then block in the promise chain.

        Args:
            call: The then call to format
            next_call: The next function call in the chain, if any

        Returns:
            str: Formatted then block code
        """
        # a then block must have a callback handler
        if not call or call.name != "then" or len(call.args) != 1:
            msg = "Invalid then call provided"
            raise Exception(msg)

        arrow_fn = call.args[0].value
        if not isinstance(arrow_fn, TSFunction):
            msg = "callback function not provided in the argument"
            raise Exception(msg)

        statements = arrow_fn.code_block.statements

        formatted_statements = []

        # adds anonymous function if then block handler has ambiguous returns
        if self._needs_anonymous_function(arrow_fn):
            anon_block = self._format_anonymous_function(arrow_fn, next_call)
            formatted_statements.append(f"{self.base_indent}{anon_block}")

        elif self._is_implicit_return(arrow_fn):
            implicit_block = self._handle_last_block_implicit_return(statements, is_catch=False)
            formatted_statements.append(f"{self.base_indent}{implicit_block}")
        else:
            for stmt in statements:
                if stmt.statement_type == StatementType.RETURN_STATEMENT:
                    return_value = stmt.source[7:].strip()
                    next_params = self.get_next_call_params(next_call)
                    await_expression = f"await {return_value}"
                    if next_params:
                        formatted_statements.append(f"{self.base_indent}{self.format_param_assignment(next_params, await_expression, declare=True)}")
                    else:
                        formatted_statements.append(f"{self.base_indent}{await_expression}")
                else:
                    formatted_statements.append(f"{self.base_indent}{stmt.source.strip()}")

        return "\n".join(formatted_statements)

    @reader
    def parse_last_then_block(self, call: FunctionCall, assignment_variable_name: str | None = None) -> str:
        from codegen.sdk.typescript.function import TSFunction

        """Parse the last .then() block in the chain.

        Args:
            call: The last .then() call to parse
            assignment_variable_name: Optional custom variable name for assignment

        Returns:
            str: Formatted code for the last .then() block
        """
        arrow_fn = call.args[0].value

        if not isinstance(arrow_fn, TSFunction):
            msg = "callback function not provided in the argument"
            raise Exception(msg)

        statements = arrow_fn.code_block.statements

        if self._needs_anonymous_function(arrow_fn):
            return self._format_anonymous_function(arrow_fn, assignment_variable_name=assignment_variable_name)

        if self._is_implicit_return(arrow_fn):
            return self._handle_last_block_implicit_return(statements, assignment_variable_name=assignment_variable_name)
        else:
            formatted_statements = []
            for stmt in statements:
                if stmt.statement_type == StatementType.RETURN_STATEMENT:
                    return_value = self._handle_last_block_normal_return(stmt, assignment_variable_name=assignment_variable_name)
                    formatted_statements.append(return_value)
                else:
                    formatted_statements.append(stmt.source.strip())
            return "\n".join(formatted_statements)

    @reader
    def _handle_last_block_normal_return(self, stmt: Statement, is_catch: bool = False, assignment_variable_name: str | None = None) -> str:
        """Handle a normal return statement in the last block of a Promise chain.

        Args:
            stmt: The return statement to handle
            is_catch: Whether this is in a catch block
            assignment_variable_name: Optional custom variable name for assignment

        Returns:
            str: Formatted return statement code
        """
        return_value = stmt.source[7:].strip()  # Remove 'return ' prefix

        var_name = assignment_variable_name if assignment_variable_name else self.assigned_var
        if var_name:
            return self.format_param_assignment([var_name], return_value)
        elif self.is_return_statement:
            if is_catch:
                return f"throw {return_value}"
            else:
                return f"return {return_value}"
        else:
            if is_catch:
                return f"throw {return_value}"
            else:
                return f"await {return_value}"

    @reader
    def _handle_last_block_implicit_return(self, statements: MultiLineCollection[Statement], is_catch: bool = False, assignment_variable_name: str | None = None) -> str:
        """Handle an implicit return in the last block of a Promise chain.

        Args:
            statements: The statements in the block
            is_catch: Whether this is in a catch block
            assignment_variable_name: Optional custom variable name for assignment

        Returns:
            str: Formatted implicit return code
        """
        stmt_source = statements[0].source.strip()
        var_name = assignment_variable_name if assignment_variable_name else self.assigned_var

        if any(stmt_source.startswith(console_method) for console_method in self.log_statements):
            return stmt_source + ";"
        elif is_catch:
            return "throw " + stmt_source + ";"
        elif var_name:
            return self.format_param_assignment([var_name], stmt_source)
        elif self.is_return_statement:
            return "return " + stmt_source + ";"
        else:
            return "await " + stmt_source + ";"

    @reader
    def handle_catch_block(self, call: FunctionCall, assignment_variable_name: str | None = None) -> str:
        """Handle catch block in the promise chain.

        Args:
            call: The catch function call to handle
            assignment_variable_name: Optional custom variable name for assignment

        Returns:
            str: Formatted catch block code
        """
        # a catch block must have a callback handler
        if not call or call.name != "catch" or len(call.args) != 1:
            msg = "Invalid catch call provided"
            raise Exception(msg)

        arrow_fn = call.args[0].value
        statements = arrow_fn.code_block.statements
        if len(arrow_fn.parameters) > 0:
            error_param = arrow_fn.parameters[0].source
        else:
            error_param = ""

        formatted_statements = [f"{self.base_indent}}} catch({error_param}: any) {{"]

        # adds annonymous function if catch block handler has ambiguous returns
        if self._needs_anonymous_function(arrow_fn):
            anon_block = self._format_anonymous_function(arrow_fn, assignment_variable_name=assignment_variable_name)
            formatted_statements.append(f"{self.base_indent}{anon_block}")

        elif self._is_implicit_return(arrow_fn):
            implicit_block = self._handle_last_block_implicit_return(statements, is_catch=True, assignment_variable_name=assignment_variable_name)
            formatted_statements.append(f"{self.base_indent}{implicit_block}")
        else:
            for stmt in statements:
                if stmt.statement_type == StatementType.RETURN_STATEMENT:
                    return_block = self._handle_last_block_normal_return(stmt, is_catch=True, assignment_variable_name=assignment_variable_name)
                    formatted_statements.append(f"{self.base_indent}{return_block}")
                else:
                    formatted_statements.append(f"{self.base_indent}{stmt.source.strip()}")

        return "\n".join(formatted_statements)

    @reader
    def handle_finally_block(self, call: FunctionCall) -> str:
        """Handle finally block in the promise chain.

        Args:
            call: The finally function call to handle

        Returns:
            str: Formatted finally block code
        """
        if not call or call.name != "finally":
            msg = "Invalid finally call provided"
            raise Exception(msg)

        arrow_fn = call.args[0].value
        statements = arrow_fn.code_block.statements

        formatted_statements = [f"{self.base_indent}}} finally {{"]

        for stmt in statements:
            formatted_statements.append(f"{self.base_indent}{stmt.source.strip()}")

        return "\n".join(formatted_statements)

    @writer
    def convert_to_async_await(self, assignment_variable_name: str | None = None, inplace_edit: bool = True) -> str | None:
        """Convert the promise chain to async/await syntax.

        Args:
            assignment_variable_name: Optional custom variable name for assignment
            inplace_edit: If set to true, will call statement.edit(); else will return a string of the new code

        Returns:
            Optional[str]: The converted async/await code
        """
        # check if promise expression needs to be wrapped in a try/catch/finally block
        needs_wrapping = self.has_catch_call or self.has_finally_call
        formatted_blocks = []

        if needs_wrapping:
            formatted_blocks.append(f"\n{self.base_indent}try {{")

        base_call = self.handle_base_call()
        formatted_blocks.append(f"{self.base_indent}{base_call}")

        for idx, then_call in enumerate(self.then_chain):
            is_last_then = idx == len(self.then_chain) - 1

            # if it's the last then block, then parse differently
            if is_last_then:
                formatted_block = self.parse_last_then_block(then_call, assignment_variable_name=assignment_variable_name)
            else:
                next_call = self.then_chain[idx + 1] if idx + 1 < len(self.then_chain) else None
                formatted_block = self.handle_then_block(then_call, next_call)
            formatted_blocks.append(f"{self.base_indent}{formatted_block}")

        if self.catch_call:
            catch_block = self.handle_catch_block(self.catch_call, assignment_variable_name=assignment_variable_name)
            formatted_blocks.append(catch_block)

        if self.finally_call:
            finally_block = self.handle_finally_block(self.finally_call)
            formatted_blocks.append(finally_block)

        if needs_wrapping:
            formatted_blocks.append(f"{self.base_indent}}}")

        if self.parent_statement.parent_function:
            self.parent_statement.parent_function.asyncify()

        diff_changes = "\n".join(formatted_blocks)
        if inplace_edit:
            self.parent_statement.edit(diff_changes)
        else:
            return diff_changes

    @reader
    def _is_implicit_return(self, arrow_fn: TSFunction) -> bool:
        """Check if an arrow function has an implicit return.

        An implicit return occurs when:
        1. The function has exactly one statement
        2. The statement is not a comment
        3. The function body is not wrapped in curly braces

        Args:
            arrow_fn: The arrow function to check

        Returns:
            bool: True if the function has an implicit return
        """
        statements = arrow_fn.code_block.statements
        if len(statements) != 1:
            return False

        stmt = statements[0]
        return not stmt.statement_type == StatementType.COMMENT and not arrow_fn.code_block.source.strip().startswith("{")

    @reader
    def _format_anonymous_function(self, arrow_fn: TSFunction, next_call: FunctionCall | None = None, assignment_variable_name: str | None = None) -> str:
        """Format an arrow function as an anonymous async function.

        Args:
            arrow_fn: The arrow function to format
            next_call: The next function call in the chain, if any
            assignment_variable_name: Optional custom variable name for assignment

        Returns:
            str: Formatted anonymous function code
        """
        params = arrow_fn.parameters
        params_str = ", ".join(p.source for p in params) if params else ""
        lines = []

        var_name = assignment_variable_name if assignment_variable_name else self.assigned_var

        if next_call and next_call.name == "then":
            next_params = self.get_next_call_params(next_call)
            if next_params:
                lines.append(f"{self.base_indent}{self.format_param_assignment(next_params, f'await (async ({params_str}) => {{', declare=True)}")
        else:
            prefix = ""
            if self.is_return_statement:
                prefix = "return "
            elif var_name:
                prefix = f"{var_name} = "
            lines.append(f"{self.base_indent}{prefix}await (async ({params_str}) => {{")

        code_block = arrow_fn.code_block
        block_content = code_block.source.strip()
        if block_content.startswith("{"):
            block_content = block_content[1:]
        if block_content.endswith("}"):
            block_content = block_content[:-1]

        block_lines = block_content.split("\n")
        for line in block_lines:
            if line.strip():
                lines.append(f"{self.base_indent}    {line.strip()}")

        if params_str:
            lines.append(f"{self.base_indent}}})({params_str});")
        else:
            lines.append(f"{self.base_indent}}})();")

        return "\n".join(lines)

    @property
    @reader
    def has_catch_call(self) -> bool:
        """Check if the Promise chain has a catch call.

        Returns:
            bool: True if there is a catch call
        """
        return self.catch_call is not None

    @property
    @reader
    def has_finally_call(self) -> bool:
        """Check if the Promise chain has a finally call.

        Returns:
            bool: True if there is a finally call
        """
        return self.finally_call is not None
