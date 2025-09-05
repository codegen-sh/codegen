"""Exception handling and LLM fix suggestions for autogenlib."""

import sys
import traceback
import os
from logging import getLogger
import openai
import time
import textwrap
import re

from ._cache import get_cached_code, cache_module
from ._context import set_module_context
from ._state import description, exception_handler_enabled

logger = getLogger(__name__)


def generate_fix_for_analysis_error(error_dict: dict, source_code: str) -> dict:
    """Generate a fix for an analysis error (not a runtime exception).

    This function extends autogenlib's fixing capability to handle static analysis errors
    from tools like ruff, mypy, pylint, etc.

    Args:
        error_dict: Dictionary containing error information with keys:
                   - file_path, line, column, error_type, severity, message, tool_source
        source_code: The source code of the file containing the error

    Returns:
        Dictionary with fix information: fixed_code, explanation, changes
    """
    try:
        # Set API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("Please set the OPENAI_API_KEY environment variable.")
            return {}

        base_url = os.environ.get("OPENAI_API_BASE_URL")
        model = os.environ.get("OPENAI_MODEL", "gpt-4.1")

        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        # Create a system prompt for static analysis error fixing
        system_prompt = """
        You are an expert Python developer specialized in fixing static analysis errors.
        
        You excel at:
        1. Understanding static analysis tool outputs (ruff, mypy, pylint, bandit, etc.)
        2. Identifying the root cause of style, type, security, and logic issues
        3. Providing minimal, targeted fixes that resolve the specific issue
        4. Maintaining code consistency and following Python best practices
        5. Explaining the reasoning behind each fix
        
        Your fixes should:
        1. Address the specific error without introducing new issues
        2. Maintain the original code's functionality and intent
        3. Follow PEP 8 and modern Python conventions
        4. Include type hints where appropriate
        5. Add necessary imports or remove unused ones
        
        Always provide both the fixed code and a clear explanation.
        """

        # Create a user prompt for the specific error
        user_prompt = f"""
        STATIC ANALYSIS ERROR FIXING TASK
        
        ERROR DETAILS:
        - File: {error_dict.get('file_path', 'unknown')}
        - Line: {error_dict.get('line', 0)}
        - Column: {error_dict.get('column', 0)}
        - Error Type: {error_dict.get('error_type', 'unknown')}
        - Severity: {error_dict.get('severity', 'unknown')}
        - Tool: {error_dict.get('tool_source', 'unknown')}
        - Message: {error_dict.get('message', 'No message provided')}
        
        CURRENT SOURCE CODE:
        ```python
        {source_code}
        ```
        
        TASK:
        Fix the specific error identified above. Focus on the exact line and issue mentioned.
        
        RESPONSE FORMAT (JSON):
        {{
            "explanation": "Clear explanation of what was wrong and how you fixed it",
            "changes": [
                {{
                    "line": 123,
                    "description": "What was changed on this line",
                    "original": "original code",
                    "new": "fixed code"
                }}
            ],
            "fixed_code": "Complete fixed Python code for the entire file"
        }}
        
        Remember: Make minimal changes that specifically address the reported error.
        """

        # Call the OpenAI API
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=4000,
                    temperature=0.2,  # Low temperature for consistent fixes
                    response_format={"type": "json_object"},
                )

                # Get the generated response
                content = response.choices[0].message.content.strip()

                try:
                    fix_info = json.loads(content)

                    # Validate that we have the required fields
                    if not all(
                        field in fix_info for field in ["explanation", "fixed_code"]
                    ):
                        raise ValueError("Missing required fields in response")

                    # Validate the fixed code
                    try:
                        compile(fix_info["fixed_code"], "<string>", "exec")
                        return fix_info
                    except SyntaxError as e:
                        logger.warning(f"Generated fix contains syntax errors: {e}")
                        if attempt == max_retries - 1:
                            return {}
                        time.sleep(1)

                except json.JSONDecodeError as e:
                    logger.warning(f"Error parsing LLM response as JSON: {e}")
                    if attempt == max_retries - 1:
                        return {
                            "explanation": "Error parsing LLM response",
                            "fixed_code": content,
                        }
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error generating fix: {e}")
                if attempt == max_retries - 1:
                    return {}
                time.sleep(1)

        return {}

    except Exception as e:
        logger.error(f"Error in generate_fix_for_analysis_error: {e}")
        return {}


def setup_exception_handler():
    """Set up the global exception handler."""
    # Store the original excepthook
    original_excepthook = sys.excepthook

    # Define our custom exception hook
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        if exception_handler_enabled:
            handle_exception(exc_type, exc_value, exc_traceback)
        # Call the original excepthook regardless
        original_excepthook(exc_type, exc_value, exc_traceback)

    # Set our custom excepthook as the global handler
    sys.excepthook = custom_excepthook


def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle an exception by sending it to the LLM for fix suggestions."""
    # Extract the traceback information
    tb_frames = traceback.extract_tb(exc_traceback)
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Determine the source of the exception
    is_autogenlib_exception = False
    module_name = None
    source_code = None
    source_file = None

    # Try to find the frame where the exception originated
    for frame in tb_frames:
        filename = frame.filename
        lineno = frame.lineno

        # Check if this file is from an autogenlib module
        if "<string>" not in filename and filename != "<stdin>":
            # This is a real file
            if filename.endswith(".py"):
                source_file = filename
                module_name_from_frame = None

                # Try to get the module name from the frame
                frame_module = None
                if hasattr(frame, "frame") and hasattr(frame.frame, "f_globals"):
                    module_name_from_frame = frame.frame.f_globals.get("__name__")
                elif len(frame) > 3 and hasattr(frame[0], "f_globals"):
                    module_name_from_frame = frame[0].f_globals.get("__name__")

                if (
                    module_name_from_frame
                    and module_name_from_frame.startswith("autogenlib.")
                    and module_name_from_frame != "autogenlib"
                ):
                    # This is an autogenlib module
                    is_autogenlib_exception = True
                    module_name = module_name_from_frame

                    # Get code from cache if it's an autogenlib module
                    if module_name.count(".") > 1:
                        module_name = ".".join(module_name.split(".")[:2])
                    source_code = get_cached_code(module_name)
                    break

                # For non-autogenlib modules, try to read the source file
                try:
                    with open(filename, "r") as f:
                        source_code = f.read()
                    module_name = module_name_from_frame or os.path.basename(
                        filename
                    ).replace(".py", "")
                    break
                except:
                    pass

    # If we couldn't determine the source from the traceback, use the last frame
    if not source_code and tb_frames:
        last_frame = tb_frames[-1]
        if hasattr(last_frame, "filename") and last_frame.filename:
            filename = last_frame.filename
            if (
                "<string>" not in filename
                and filename != "<stdin>"
                and filename.endswith(".py")
            ):
                try:
                    with open(filename, "r") as f:
                        source_code = f.read()
                    module_name = os.path.basename(filename).replace(".py", "")
                except:
                    pass

    # If we still don't have source code but have a module name from an autogenlib module
    if not source_code and module_name and module_name.startswith("autogenlib."):
        source_code = get_cached_code(module_name)
        is_autogenlib_exception = True

    # Check all loaded modules if we still don't have source code
    if not source_code:
        for loaded_module_name, loaded_module in list(sys.modules.items()):
            if (
                loaded_module_name.startswith("autogenlib.")
                and loaded_module_name != "autogenlib"
            ):
                try:
                    # Try to see if this module might be related to the exception
                    if (
                        exc_type.__module__ == loaded_module_name
                        or loaded_module_name in tb_str
                    ):
                        module_name = loaded_module_name
                        if module_name.count(".") > 1:
                            module_name = ".".join(module_name.split(".")[:2])
                        source_code = get_cached_code(module_name)
                        is_autogenlib_exception = True
                        break
                except:
                    continue

    # If we still don't have any source code, try to extract it from any file mentioned in the traceback
    if not source_code:
        for line in tb_str.split("\n"):
            if 'File "' in line and '.py"' in line:
                try:
                    file_path = line.split('File "')[1].split('"')[0]
                    if os.path.exists(file_path) and file_path.endswith(".py"):
                        with open(file_path, "r") as f:
                            source_code = f.read()
                        module_name = os.path.basename(file_path).replace(".py", "")
                        source_file = file_path
                        break
                except:
                    continue

    # If we still don't have source code, we'll just use the traceback
    if not source_code:
        source_code = "# Source code could not be determined"
        module_name = "unknown"

    # Generate fix using LLM
    fix_info = generate_fix(
        module_name,
        source_code,
        exc_type,
        exc_value,
        tb_str,
        is_autogenlib_exception,
        source_file,
    )

    if fix_info and is_autogenlib_exception:
        # For autogenlib modules, we can try to reload them automatically
        fixed_code = fix_info.get("fixed_code")
        if fixed_code:
            # Cache the fixed code
            cache_module(module_name, fixed_code, description)

            # Update the module context
            set_module_context(module_name, fixed_code)

            # Reload the module with the fixed code
            try:
                if module_name in sys.modules:
                    # Execute the new code in the module's namespace
                    exec(fixed_code, sys.modules[module_name].__dict__)
                    logger.info(f"Module {module_name} has been fixed and reloaded")

                    # Output a helpful message to the user
                    print("\n" + "=" * 80)
                    print(f"AutoGenLib fixed an error in module {module_name}")
                    print("The module has been reloaded with the fix.")
                    print("Please retry your operation.")
                    print("=" * 80 + "\n")
            except Exception as e:
                logger.error(f"Error reloading fixed module: {e}")
                print("\n" + "=" * 80)
                print(f"AutoGenLib attempted to fix an error in module {module_name}")
                print(f"But encountered an error while reloading: {e}")
                print("Please restart your application to apply the fix.")
                print("=" * 80 + "\n")
    elif fix_info:
        # For external code, just display the fix suggestions
        print("\n" + "=" * 80)
        print(f"AutoGenLib detected an error in {module_name}")
        if source_file:
            print(f"File: {source_file}")
        print(f"Error: {exc_type.__name__}: {exc_value}")

        # Display the fix suggestions
        print("\nFix Suggestions:")
        print("-" * 40)
        if "explanation" in fix_info:
            explanation = textwrap.fill(fix_info["explanation"], width=78)
            print(explanation)
            print("-" * 40)

        if "fixed_code" in fix_info:
            print("Suggested fixed code:")
            print("-" * 40)
            if source_file:
                print(f"# Apply this fix to {source_file}")

            # If we have specific changes, display them in a more readable format
            if "changes" in fix_info:
                for change in fix_info["changes"]:
                    print(
                        f"Line {change.get('line', '?')}: {change.get('description', '')}"
                    )
                    if "original" in change and "new" in change:
                        print(f"Original: {change['original']}")
                        print(f"New:      {change['new']}")
                        print()
            else:
                # Otherwise just print a snippet of the fixed code (first 20 lines)
                fixed_code_lines = fix_info["fixed_code"].split("\n")
                if len(fixed_code_lines) > 20:
                    print("\n".join(fixed_code_lines[:20]))
                    print("... (truncated for readability)")
                else:
                    print(fix_info["fixed_code"])

        print("=" * 80 + "\n")


def extract_python_code(response):
    """
    Extract Python code from LLM response more robustly.

    Handles various ways code might be formatted in the response:
    - Code blocks with ```python or ``` markers
    - Multiple code blocks
    - Indented code blocks
    - Code without any markers

    Returns the cleaned Python code.
    """
    # Check if response is already clean code (no markdown)
    try:
        compile(response, "<string>", "exec")
        return response
    except SyntaxError:
        pass

    # Try to extract code from markdown code blocks
    code_block_pattern = r"```(?:python)?(.*?)```"
    matches = re.findall(code_block_pattern, response, re.DOTALL)

    if matches:
        # Join all code blocks and check if valid
        extracted_code = "\n\n".join(match.strip() for match in matches)
        try:
            compile(extracted_code, "<string>", "exec")
            return extracted_code
        except SyntaxError:
            pass

    # If we get here, no valid code blocks were found
    # Try to identify the largest Python-like chunk in the text
    lines = response.split("\n")
    code_lines = []
    current_code_chunk = []

    for line in lines:
        # Skip obvious non-code lines
        if re.match(
            r"^(#|Here's|I've|This|Note:|Remember:|Explanation:)", line.strip()
        ):
            # If we were collecting code, save the chunk
            if current_code_chunk:
                code_lines.extend(current_code_chunk)
                current_code_chunk = []
            continue

        # Lines that likely indicate code
        if re.match(
            r"^(import|from|def|class|if|for|while|return|try|with|@|\s{4}|    )", line
        ):
            current_code_chunk.append(line)
        elif line.strip() == "" and current_code_chunk:
            # Empty lines within code blocks are kept
            current_code_chunk.append(line)
        elif current_code_chunk:
            # If we have a non-empty line that doesn't look like code but follows code
            # we keep it in the current chunk (might be a variable assignment, etc.)
            current_code_chunk.append(line)

    # Add any remaining code chunk
    if current_code_chunk:
        code_lines.extend(current_code_chunk)

    # Join all identified code lines
    extracted_code = "\n".join(code_lines)

    # If we couldn't extract anything or it's invalid, return the original
    # but the validator will likely reject it
    if not extracted_code:
        return response

    try:
        compile(extracted_code, "<string>", "exec")
        return extracted_code
    except SyntaxError:
        # Last resort: try to use the whole response if it might be valid code
        if "def " in response or "class " in response or "import " in response:
            try:
                compile(response, "<string>", "exec")
                return response
            except SyntaxError:
                pass

        # Log the issue
        logger.warning("Could not extract valid Python code from response")
        return response


def generate_fix(
    module_name,
    current_code,
    exc_type,
    exc_value,
    traceback_str,
    is_autogenlib=False,
    source_file=None,
):
    """Generate a fix for the exception using the LLM.

    Args:
        module_name: Name of the module where the exception occurred
        current_code: Current source code of the module
        exc_type: Exception type
        exc_value: Exception value
        traceback_str: Formatted traceback string
        is_autogenlib: Whether this is an autogenlib-generated module
        source_file: Path to the source file (for non-autogenlib modules)

    Returns:
        Dictionary containing fix information:
        - fixed_code: The fixed code (if available)
        - explanation: Explanation of the issue and fix
        - changes: List of specific changes made (if available)
    """
    try:
        # Set API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("Please set the OPENAI_API_KEY environment variable.")
            return None

        base_url = os.environ.get("OPENAI_API_BASE_URL")
        model = os.environ.get("OPENAI_MODEL", "gpt-4.1")

        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        # Create a system prompt for the LLM
        system_prompt = """
        You are an expert Python developer and debugger specialized in fixing code errors.
        
        You meticulously analyze errors by:
        1. Tracing the execution flow to the exact point of failure
        2. Understanding the root cause, not just the symptoms
        3. Identifying edge cases that may have triggered the exception
        4. Looking for similar issues elsewhere in the code
        
        When creating fixes, you:
        1. Make the minimal changes necessary to resolve the issue
        2. Maintain consistency with the existing code style
        3. Add appropriate defensive programming
        4. Ensure type consistency and proper error handling
        5. Add brief comments explaining non-obvious fixes
        
        Your responses must be precise, direct, and immediately applicable.
        """

        # Create a user prompt for the LLM
        user_prompt = f"""
        DEBUGGING TASK: Fix a Python error in {module_name}
        
        MODULE DETAILS:
        {"AUTO-GENERATED MODULE" if is_autogenlib else "USER CODE"}
        {f"Source file: {source_file}" if source_file else ""}
        
        CURRENT CODE:
        ```python
        {current_code}
        ```
        
        ERROR DETAILS:
        Type: {exc_type.__name__}
        Message: {exc_value}
        
        TRACEBACK:
        {traceback_str}
        
        {"REQUIRED RESPONSE FORMAT: Return ONLY complete fixed Python code. No explanations, comments, or markdown." if is_autogenlib else 'REQUIRED RESPONSE FORMAT: JSON with "explanation", "changes" (line-by-line fixes), and "fixed_code" fields.'}
        
        {"Remember: The module will be executed directly so your response must be valid Python code only." if is_autogenlib else "Remember: Be specific about what changes and why. Include line numbers for easy reference."}
        """

        # Call the OpenAI API
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=5000,
                    temperature=0.3,  # Lower temperature for more deterministic results
                    response_format={"type": "json_object"}
                    if not is_autogenlib
                    else None,
                )

                # Get the generated response
                content = response.choices[0].message.content.strip()

                if is_autogenlib:
                    # For autogenlib modules, we expect just the fixed code
                    fixed_code = extract_python_code(content)

                    # Validate the fixed code
                    try:
                        compile(fixed_code, "<string>", "exec")
                        return {"fixed_code": fixed_code}
                    except Exception as e:
                        logger.warning(f"Generated fix contains syntax errors: {e}")
                        if attempt == max_retries - 1:
                            return None
                        time.sleep(1)  # Wait before retry
                else:
                    # For regular code, we expect a JSON response
                    try:
                        import json

                        fix_info = json.loads(content)

                        # Validate that we have at least some of the expected fields
                        if not any(
                            field in fix_info
                            for field in ["explanation", "changes", "fixed_code"]
                        ):
                            raise ValueError("Missing required fields in response")

                        # If we have fixed code, validate it
                        if "fixed_code" in fix_info:
                            try:
                                compile(fix_info["fixed_code"], "<string>", "exec")
                            except Exception as e:
                                logger.warning(
                                    f"Generated fix contains syntax errors: {e}"
                                )
                                # We'll still return it for user information, even if it has syntax errors

                        return fix_info
                    except Exception as e:
                        logger.warning(f"Error parsing LLM response as JSON: {e}")
                        if attempt == max_retries - 1:
                            # If all attempts failed to parse as JSON, return a simplified response
                            return {
                                "explanation": "Error analyzing the code. Here's the raw LLM output:",
                                "fixed_code": content,
                            }
                        time.sleep(1)  # Wait before retry

            except Exception as e:
                logger.error(f"Error generating fix: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(1)  # Wait before retry

        return None
    except Exception as e:
        logger.error(f"Error in generate_fix: {e}")
        return None
