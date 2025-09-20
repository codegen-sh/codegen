import linecache
import sys
import traceback
from collections.abc import Callable

from codegen.shared.exceptions.compilation import InvalidUserCodeException
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def get_compilation_error_context(filename: str, line_number: int, window_size: int = 2):
    """Get lines of context around SyntaxError + Exceptions that occur when compiling functions."""
    start = max(1, line_number - window_size)
    end = line_number + window_size + 1
    lines = []
    for i in range(start, end):
        line = linecache.getline(filename, i).rstrip()
        if line:
            lines.append((i, line))
    return lines


def safe_compile_function_string(custom_scope: dict, func_name: str, func_str: str) -> Callable:
    # =====[ Add function string to linecache ]=====
    # (This is necessary for the traceback to work correctly)
    linecache.cache["<string>"] = (len(func_str), None, func_str.splitlines(True), "<string>")

    # =====[ Compile & exec the code ]=====
    # This will throw errors if there is invalid syntax
    try:
        # First, try to compile the code to catch syntax errors
        logger.info(f"Compiling function: {func_name} ...")
        compiled_code = compile(func_str, "<string>", "exec")
        # If compilation succeeds, try to execute the code
        logger.info(f"Compilation succeeded. exec-ing function: {func_name} ...")
        exec(compiled_code, custom_scope, custom_scope)

    # =====[ Catch SyntaxErrors ]=====
    except SyntaxError as e:
        error_class = e.__class__.__name__
        detail = e.args[0]
        line_number = e.lineno
        context_lines = get_compilation_error_context("<string>", line_number)
        context_str = "\n".join(f"{'>' if i == line_number else ' '} {i}: {line}" for i, line in context_lines)
        error_line = linecache.getline("<string>", line_number).strip()
        caret_line = " " * (e.offset - 1) + "^" * (len(error_line) - e.offset + 1)
        error_message = f"{error_class} at line {line_number}: {detail}\n    {error_line}\n    {caret_line}\n{context_str}"
        raise InvalidUserCodeException(error_message) from e

    # =====[ All other Exceptions ]=====
    except Exception as e:
        error_class = e.__class__.__name__
        detail = str(e)
        _, _, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1].lineno
        context_lines = get_compilation_error_context("<string>", line_number)
        context_str = "\n".join(f"{'>' if i == line_number else ' '} {i}: {line}" for i, line in context_lines)
        error_line = linecache.getline("<string>", line_number).strip()
        error_message = f"{error_class} at line {line_number}: {detail}\n    {error_line}\n{context_str}"
        raise InvalidUserCodeException(error_message) from e

    finally:
        # Clear the cache to free up memory
        linecache.clearcache()

    return custom_scope.get(func_name)
