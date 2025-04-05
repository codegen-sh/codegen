"""Prompts for the Relace edit tool."""

RELACE_EDIT_PROMPT = """Edit a file using the Relace Instant Apply API.

⚠️ IMPORTANT: The 'edit_snippet' parameter must be provided as a direct string, NOT as a dictionary or JSON object.
For example, use: edit_snippet="// ... code here ..." NOT edit_snippet={"code": "// ... code here ..."}
DO NOT pass the edit_snippet as a dictionary or JSON object or dictionary with a 'code' key .

The Relace Instant Apply API is a high-speed code generation engine optimized for real-time performance at 2000 tokens/second. It splits code generation into two specialized steps:

1. Hard Reasoning: Uses SOTA models like Claude for complex code understanding
2. Fast Integration: Rapidly merges edits into existing code

To use this tool effectively, provide:
1. The path to the file you want to edit (filepath)
2. An edit snippet that describes the changes you want to make (edit_snippet)

The edit snippet is crucial for successful merging and should follow these guidelines:
- Include complete code blocks that will appear in the final output
- Clearly indicate which parts of the code remain unchanged with descriptive comments like:
  * "// ... keep existing imports ..."
  * "// ... rest of the class definition ..."
  * "// ... existing function implementations ..."
- Maintain correct indentation and code structure exactly as it should appear in the final code
- Use comments to indicate the purpose of your changes (e.g., "// Add new function")
- For removing sections, provide sufficient context so it's clear what should be removed
- Focus only on the modifications, not other aspects of the code
- Preserve language-specific syntax (comment style may vary by language)
- Include more context than just the minimal changes - surrounding code helps the API understand where and how to apply the edit

Example edit snippet:
```
// ... keep existing imports ...

// Add new function
function calculateDiscount(price, discountPercent) {
  return price * (discountPercent / 100);
}

// ... keep existing code ...
```

Another example (Python):
```
# ... existing imports ...

# Add new helper function
def validate_input(data):
    '''Validates the input data structure.'''
    if not isinstance(data, dict):
        raise TypeError("Input must be a dictionary")
    if "id" not in data:
        raise ValueError("Input must contain an 'id' field")
    return True

# ... rest of the file ...
```

The API will merge your edit snippet with the existing code to produce the final result.
The API key will be automatically retrieved from the RELACE_API environment variable.

Common pitfalls to avoid:
- Not providing enough context around changes
- Providing too little surrounding code (include more than just the changed lines)
- Incorrect indentation in the edit snippet
- Forgetting to indicate unchanged sections with comments
- Using inconsistent comment styles
- Being too vague about where changes should be applied
- Passing the edit_snippet as a dictionary or JSON object instead of a direct string
"""

RELACE_EDIT_SYSTEM_PROMPT = """You are an expert at creating edit snippets for the Relace Instant Apply API.

Your job is to create an edit snippet that describes how to modify the provided existing code according to user specifications.

Follow these guidelines:
1. Focus only on the MODIFICATION REQUEST, not other aspects of the code
2. Abbreviate unchanged sections with "// ... rest of headers/sections/code ..." (be descriptive in the comment)
3. Indicate the location and nature of modifications with comments and ellipses
4. Preserve indentation and code structure exactly as it should appear in the final code
5. Do not output lines that will not be in the final code after merging
6. If removing a section, provide relevant context so it's clear what should be removed

Do NOT provide commentary or explanations - only the code with a focus on the modifications.
"""

RELACE_EDIT_USER_PROMPT = """EXISTING CODE:
{initial_code}

MODIFICATION REQUEST:
{user_instructions}

Create an edit snippet that can be used with the Relace Instant Apply API to implement these changes.
"""
