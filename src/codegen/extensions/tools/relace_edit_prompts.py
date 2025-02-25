"""Prompts for the Relace edit tool."""

RELACE_EDIT_PROMPT = """Edit a file using the Relace Instant Apply API.

The Relace Instant Apply API is a high-speed code generation engine optimized for real-time performance at 2000 tokens/second. It splits code generation into two specialized steps:

1. Hard Reasoning: Uses SOTA models like Claude for complex code understanding
2. Fast Integration: Rapidly merges edits into existing code

To use this tool, provide:
1. The path to the file you want to edit
2. An edit snippet that describes the changes you want to make

The edit snippet should:
- Include complete code blocks that will appear in the final output
- Clearly indicate which parts of the code remain unchanged with comments like "// ... rest of code ..."
- Maintain correct indentation and code structure

Example edit snippet:
```
// ... keep existing imports ...

// Add new function
function calculateDiscount(price, discountPercent) {
  return price * (discountPercent / 100);
}

// ... keep existing code ...
```

The API will merge your edit snippet with the existing code to produce the final result.
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
