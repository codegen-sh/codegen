"""Code generation for autogenlib using OpenAI API."""

import openai
import os
import ast
import re
from ._cache import get_all_modules, get_cached_prompt
from logging import getLogger

logger = getLogger(__name__)


def validate_code(code):
    """Validate the generated code against PEP standards."""
    try:
        # Check if the code is syntactically valid
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def get_codebase_context():
    """Get the full codebase context for all cached modules."""
    modules = get_all_modules()

    if not modules:
        return ""

    context = "Here is the existing codebase for reference:\n\n"

    for module_name, data in modules.items():
        if "code" in data:
            context += f"# Module: {module_name}\n```python\n{data['code']}\n```\n\n"

    return context


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
    if validate_code(response):
        return response

    # Try to extract code from markdown code blocks
    code_block_pattern = r"```(?:python)?(.*?)```"
    matches = re.findall(code_block_pattern, response, re.DOTALL)

    if matches:
        # Join all code blocks and check if valid
        extracted_code = "\n\n".join(match.strip() for match in matches)
        if validate_code(extracted_code):
            return extracted_code

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
    if not extracted_code or not validate_code(extracted_code):
        # Last resort: try to use the whole response if it might be valid code
        if "def " in response or "class " in response or "import " in response:
            if validate_code(response):
                return response

        # Log the issue
        logger.warning("Could not extract valid Python code from response")
        logger.debug("Response: %s", response)
        return response

    return extracted_code


def generate_code(description, fullname, existing_code=None, caller_info=None):
    """Generate code using the OpenAI API."""
    parts = fullname.split(".")
    if len(parts) < 2:
        return None

    module_name = parts[1]
    function_name = parts[2] if len(parts) > 2 else None

    # Get the cached prompt or use the provided description
    module_to_check = ".".join(fullname.split(".")[:2])  # e.g., 'autogenlib.totp'
    cached_prompt = get_cached_prompt(module_to_check)
    current_description = cached_prompt or description

    # Get the full codebase context
    codebase_context = get_codebase_context()

    # Add caller code context if available
    caller_context = ""
    if caller_info and caller_info.get("code"):
        code = caller_info.get("code", "")
        # Extract the most relevant parts of the code if possible
        # Try to focus on the sections that use the requested module/function
        relevant_parts = []
        module_parts = fullname.split(".")

        if len(module_parts) >= 2:
            # Look for imports of this module
            module_prefix = f"from {module_parts[0]}.{module_parts[1]}"
            import_lines = [line for line in code.split("\n") if module_prefix in line]
            if import_lines:
                relevant_parts.extend(import_lines)

            # Look for usages of the imported functions
            if len(module_parts) >= 3:
                func_name = module_parts[2]
                func_usage_lines = [
                    line
                    for line in code.split("\n")
                    if func_name in line and not line.startswith(("import ", "from "))
                ]
                if func_usage_lines:
                    relevant_parts.extend(func_usage_lines)

        # Include relevant parts if found, otherwise use the whole code
        if relevant_parts:
            caller_context = f"""
            Here is the code that is importing and using this module/function:
            ```python
            # File: {caller_info.get("filename", "unknown")}
            # --- Relevant snippets ---
            {"\n".join(relevant_parts)}
            ```
            
            And here is the full context:
            ```python
            {code}
            ```
            
            Pay special attention to how the requested functionality will be used in the code snippets above.
            """
        else:
            caller_context = f"""
            Here is the code that is importing this module/function:
            ```python
            # File: {caller_info.get("filename", "unknown")}
            {code}
            ```
            
            Pay special attention to how the requested functionality will be used in this code.
            """

        logger.debug(f"Including caller context from {caller_info.get('filename')}")

    # Create a prompt for the OpenAI API
    system_message = """
    You are an expert Python developer tasked with generating high-quality, production-ready Python modules.
    
    Follow these guidelines precisely:
    
    1. CODE QUALITY:
       - Write clean, efficient, and well-documented code with docstrings
       - Follow PEP 8 style guidelines strictly
       - Include type hints where appropriate (Python 3.12+ compatible)
       - Add comprehensive error handling for edge cases
       - Create descriptive variable names that clearly convey their purpose
    
    2. UNDERSTANDING CONTEXT:
       - Carefully analyze existing code to maintain consistency
       - Match the naming conventions and patterns in related modules
       - Ensure your implementation will work with the exact data structures shown in caller code
       - Make reasonable assumptions when information is missing, but document those assumptions
    
    3. RESPONSE FORMAT:
       - ONLY provide clean Python code with no explanations outside of code comments
       - Do NOT include markdown formatting, explanations, or any text outside the code
       - Do NOT include ```python or ``` markers around your code
       - Your entire response should be valid Python code that can be executed directly
    
    4. IMPORTS:
       - Use only Python standard library modules unless explicitly told otherwise
       - If you need to import from within the library (autogenlib), do so as if those modules exist
       - Format imports according to PEP 8 (stdlib, third-party, local)
    
    The code you generate will be directly executed by the Python interpreter, so it must be syntactically perfect.
    """

    if function_name and existing_code:
        prompt = f"""
        TASK: Extend an existing Python module named '{module_name}' with a new function/class.
        
        LIBRARY PURPOSE:
        {current_description}
        
        EXISTING MODULE CODE:
        ```python
        {existing_code}
        ```
        
        CODEBASE CONTEXT:
        {codebase_context}
        
        CALLER CONTEXT:
        {caller_context}
        
        REQUIREMENTS:
        Add a new {"class" if function_name[0].isupper() else "function"} named '{function_name}' that implements:
        {description}
        
        IMPORTANT INSTRUCTIONS:
        1. Keep all existing functions and classes intact
        2. Follow the existing coding style for consistency
        3. Add comprehensive docstrings and comments where needed
        4. Include proper type hints and error handling
        5. Return ONLY the complete Python code for the entire module
        6. Do NOT include any explanations or markdown formatting in your response
        """
    elif function_name:
        prompt = f"""
        TASK: Create a new Python module named '{module_name}' with a specific function/class.
        
        LIBRARY PURPOSE:
        {current_description}
        
        CODEBASE CONTEXT:
        {codebase_context}
        
        CALLER CONTEXT:
        {caller_context}
        
        REQUIREMENTS:
        Create a module that contains a {"class" if function_name[0].isupper() else "function"} named '{function_name}' that implements:
        {description}
        
        IMPORTANT INSTRUCTIONS:
        1. Start with an appropriate module docstring summarizing the purpose
        2. Include comprehensive docstrings for all functions/classes
        3. Add proper type hints and error handling
        4. Return ONLY the complete Python code for the module
        5. Do NOT include any explanations or markdown formatting in your response
        """
    else:
        prompt = f"""
        TASK: Create a new Python package module named '{module_name}'.
        
        LIBRARY PURPOSE:
        {current_description}
        
        CODEBASE CONTEXT:
        {codebase_context}
        
        CALLER CONTEXT:
        {caller_context}
        
        REQUIREMENTS:
        Implement functionality for:
        {description}
        
        IMPORTANT INSTRUCTIONS:
        1. Create a well-structured module with appropriate functions and classes
        2. Start with a comprehensive module docstring
        3. Include proper docstrings, type hints, and error handling
        4. Return ONLY the complete Python code without any explanations
        5. Do NOT include file paths or any markdown formatting in your response
        """

    try:
        # Set API key from environment variable
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable.")

        base_url = os.environ.get("OPENAI_API_BASE_URL")
        model = os.environ.get("OPENAI_MODEL", "gpt-4.1")

        # Initialize the OpenAI client
        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        logger.debug("Prompt: %s", prompt)

        # Call the OpenAI API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )

        # Get the generated code
        raw_response = response.choices[0].message.content.strip()

        logger.debug("Raw response: %s", raw_response)

        # Extract and clean the Python code from the response
        code = extract_python_code(raw_response)

        logger.debug("Extracted code: %s", code)

        # Validate the code
        if validate_code(code):
            return code
        else:
            logger.error("Generated code is not valid. Attempting to fix...")

            # Try to clean up common issues
            # Remove any additional text before or after code blocks
            clean_code = re.sub(r'^.*?(?=(?:"""|\'\'\'))', "", code, flags=re.DOTALL)

            if validate_code(clean_code):
                logger.info("Fixed code validation issues")
                return clean_code

            logger.error("Generated code is not valid and could not be fixed")
            return None
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return None
