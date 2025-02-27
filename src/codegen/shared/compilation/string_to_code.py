import linecache
import sys
import traceback
from collections.abc import Callable
from typing import Any

from codegen.shared.compilation.codeblock_validation import check_for_dangerous_operations
from codegen.shared.compilation.exception_utils import get_local_frame, get_offset_traceback
from codegen.shared.compilation.function_compilation import safe_compile_function_string
from codegen.shared.compilation.function_construction import create_function_str_from_codeblock, get_imports_string
from codegen.shared.exceptions.control_flow import StopCodemodException
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def create_execute_function_from_codeblock(codeblock: str, custom_scope: dict | None = None, func_name: str = "execute") -> Callable:
    """Convert a user code string into a Callable that takes in a Codebase.

    Steps:
    1. Check for any dangerous operations in the codeblock. Will raise DangerousUserCodeException if any dangerous operations are found.
    2. Create a function string from the codeblock. Ex: "def execute(codebase: Codebase): ..."
    3. Compile the function string into a Callable that takes in a Codebase. Will raise InvalidUserCodeException if there are any code errors (ex: IndentationErrors)
    4. Wrap the function in another function (that also takes in a Codebase) that handles calling the function and safely handling any exceptions occur during execution.

    Args:
        codeblock (str): The user code to construct the Callable with (usually CodemodVersionModel.source)
        custom_scope (dict | None, optional): Custom scope to be used during compilation. Defaults to None.
        func_name (str, optional): Name of the function to be created. Defaults to "execute".

    Returns:
        Callable: def <func_name>(codebase: Codebase) -> any | dict

    Raises:
        UnsafeUserCodeException: If the user's code contains dangerous operations.
        InvalidUserCodeException: If there are syntax errors in the provided code.
    """
    # =====[ Set up custom scope ]=====
    custom_scope = custom_scope or {}
    logger.info(f"create_execute_function custom_scope: {custom_scope.keys()}")

    # =====[ Check for dangerous operations in the codeblock ]=====
    check_for_dangerous_operations(codeblock)
    # =====[ Create function string from codeblock ]=====
    func_str = create_function_str_from_codeblock(codeblock, func_name)
    # =====[ Compile the function string into a function  ]=====
    func = safe_compile_function_string(custom_scope=custom_scope, func_name=func_name, func_str=func_str)

    # =====[ Compute line offset of func_str  ]=====
    # This is to generate the a traceback with the correct line window
    len_imports = len(get_imports_string().split("\n"))
    len_func_str = 1
    line_offset = len_imports + len_func_str

    # =====[ Create closure function to enclose outer scope variables]=====
    def closure_func() -> Callable[[Any], None]:
        """Wrap user code in a closure to capture the outer scope variables and format errors."""
        _func_str = func_str
        _line_offset = line_offset

        # Wrap the func for better tracing
        def wrapped_func(*args, **kwargs):
            """Wraps the user code to capture and format exceptions + grab locals"""
            try:
                linecache.cache["<string>"] = (len(_func_str), None, _func_str.splitlines(True), "<string>")
                func(*args, **kwargs)

            # =====[ Grab locals during `StopCodemodException` ]=====
            except StopCodemodException as e:
                logger.info(f"Stopping codemod due to {e.__class__.__name__}: {e}")
                raise e

            except Exception as e:
                # =====[ Get offset, filtered traceback message ]=====
                tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
                error_message = get_offset_traceback(tb_lines, _line_offset, filenameFilter="<string>")

                # =====[ Find frame in user's code ]=====
                exc_type, exc_value, exc_traceback = sys.exc_info()
                frame = get_local_frame(exc_type, exc_value, exc_traceback)
                # TODO: handle frame is None
                line_num = frame.f_lineno

                # =====[ Get context lines ]=====
                context_start = max(0, line_num - 3)
                context_end = min(len(func_str.split("\n")), line_num + 2)
                context_lines = func_str.split("\n")[context_start:context_end]

                # =====[ Format error message with context ]=====
                error_lines = []
                for i, line in enumerate(context_lines, start=context_start + 1):
                    marker = ">" if i == line_num else " "
                    error_lines.append(f"{marker} {i - _line_offset}: {line.rstrip()}")
                error_context = "\n".join(error_lines)

                # =====[ Format error message ]=====
                error_message = (
                    error_message
                    + f"""

Code context:
{error_context}
"""
                )
                raise RuntimeError(error_message) from e

        return wrapped_func

    return closure_func()
