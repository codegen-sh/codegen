from typing import Annotated, Any

from mcp.server.fastmcp import Context, FastMCP

from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS

# Initialize FastMCP server

mcp = FastMCP("codegen-mcp", instructions="MCP server for the Codegen SDK. Use the tools and resources to setup codegen in your environment and to create and improve your Codegen Codemods.")

# ----- RESOURCES -----


@mcp.resource("system://agent_prompt", description="Provides all the information the agent needs to know about Codegen SDK", mime_type="text/plain")
def get_docs() -> str:
    """Get the sdk doc url."""
    return SYSTEM_PROMPT


@mcp.resource("system://setup_instructions", description="Provides all the instructions to setup the environment for the agent", mime_type="text/plain")
def get_setup_instructions() -> str:
    """Get the setup instructions."""
    return SETUP_INSTRUCTIONS


@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict[str, Any]:
    """Get the service config."""
    return {
        "name": "mcp-codegen",
        "version": "0.1.0",
        "description": "The MCP server for assisting with creating/writing/improving codegen codemods.",
    }


# ----- TOOLS -----


@mcp.tool()
def ask_codegen_sdk(query: Annotated[str, "Ask a question about the Codegen SDK, CLI, or codemod development"]):
    """Provide guidance on Codegen SDK usage and best practices."""
    
    query_lower = query.lower()
    
    # Basic responses for common SDK questions
    if "codebase" in query_lower:
        return """The Codebase class is the main entry point for analyzing code repositories. Here's how to use it:

```python
from codegen.sdk.core.codebase import Codebase

# Initialize a codebase
codebase = Codebase("/path/to/your/project")

# Analyze files
files = codebase.get_files()
for file in files:
    print(f"File: {file.path}")
    print(f"Language: {file.language}")
```

Key methods:
- `get_files()`: Get all files in the codebase
- `get_files_by_extension()`: Filter files by extension
- `analyze()`: Perform deep analysis of the codebase
"""
    
    elif "codemod" in query_lower:
        return """To create codemods with Codegen:

1. **Using the CLI:**
```bash
codegen create my-codemod -d "Description of transformation"
```

2. **Using the SDK:**
```python
from codegen.sdk.core.codemod import Codemod

# Create a new codemod
codemod = Codemod(
    name="my-transformation",
    description="Transform specific patterns"
)

# Define transformation rules
@codemod.rule
def transform_function(node):
    # Your transformation logic here
    return modified_node

# Apply to codebase
codemod.apply_to_codebase(codebase)
```
"""
    
    elif "typescript" in query_lower or "javascript" in query_lower:
        return """For TypeScript/JavaScript analysis:

```python
from codegen.sdk.core.codebase import Codebase

# Initialize with TypeScript focus
codebase = Codebase("/path/to/ts/project")
ts_files = codebase.get_files_by_extension(['.ts', '.tsx', '.js', '.jsx'])

# Common TypeScript transformations:
# - Add type annotations
# - Convert JavaScript to TypeScript
# - Update import/export statements
# - Migrate to newer syntax
```
"""
    
    elif "python" in query_lower:
        return """For Python analysis and transformation:

```python
from codegen.sdk.core.codebase import Codebase

# Focus on Python files
codebase = Codebase("/path/to/python/project")
py_files = codebase.get_files_by_extension(['.py'])

# Common Python transformations:
# - Update imports
# - Modernize syntax (f-strings, type hints)
# - Refactor function signatures
# - Add error handling
```
"""
    
    else:
        return f"""I can help you with Codegen! Here are some common topics:

**Getting Started:**
- Install: `pip install codegen`
- Login: `codegen login`
- Create codemod: `codegen create my-codemod`

**Codebase Analysis:**
- Use `Codebase` class to analyze repositories
- Filter files by language or extension
- Perform structural analysis

**Codemod Development:**
- Create transformation rules
- Apply systematic changes
- Test and iterate on transformations

**Language Support:**
- TypeScript/JavaScript
- Python
- Multi-language codebases

For your question: "{query}"

Visit our documentation for more details: https://docs.codegen.com

What specific aspect would you like to know more about?
"""


@mcp.tool()
def generate_codemod(
    title: Annotated[str, "The title of the codemod (hyphenated)"],
    task: Annotated[str, "The task to which the codemod should implement to solve"],
    codebase_path: Annotated[str, "The absolute path to the codebase directory"],
    ctx: Context,
) -> str:
    """Generate a codemod for the given task and codebase."""
    return f'''
    Use the codegen cli to generate a codemod. If you need to intall the cli the command to do so is `uv tool install codegen`. Once installed, run the following command to generate the codemod:

    codegen create {title} -d "{task}"
    '''


@mcp.tool()
def improve_codemod(
    codemod_source: Annotated[str, "The source code of the codemod to improve"],
    task: Annotated[str, "The task to which the codemod should implement to solve"],
    concerns: Annotated[list[str], "A list of issues that were discovered with the current codemod that need to be considered in the next iteration"],
    context: Annotated[dict[str, Any], "Additional context for the codemod this can be a list of files that are related, additional information about the task, etc."],
    language: Annotated[str, "The language of the codebase (e.g., 'python', 'typescript', 'javascript')"],
    ctx: Context,
) -> str:
    """Provide suggestions for improving a codemod based on identified issues."""
    
    concerns_text = "\n".join(f"- {concern}" for concern in concerns)
    context_text = "\n".join(f"- {key}: {value}" for key, value in context.items())
    
    return f"""## Codemod Improvement Analysis

**Original Task:** {task}
**Language:** {language}

**Identified Issues:**
{concerns_text}

**Additional Context:**
{context_text}

**Improvement Suggestions:**

1. **Code Review:** Analyze the current codemod for common issues:
   - Edge case handling
   - Error handling and validation
   - Performance considerations
   - Code style and readability

2. **Testing:** Ensure comprehensive test coverage:
   - Unit tests for transformation logic
   - Integration tests with sample codebases
   - Edge case testing

3. **Common Fixes Based on Language:**

   **For {language.upper()}:**
   - Ensure proper AST node handling
   - Handle different syntax variations
   - Consider language-specific edge cases
   - Validate import/export transformations

4. **Recommended Next Steps:**
   - Review the codemod against the identified concerns
   - Add error handling for edge cases
   - Test with diverse code samples
   - Consider using Codegen's built-in validation tools

**Current Codemod Analysis:**
```{language}
{codemod_source[:500]}{'...' if len(codemod_source) > 500 else ''}
```

Would you like me to provide more specific guidance for any of these areas?
"""


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    mcp.run(transport="stdio")
