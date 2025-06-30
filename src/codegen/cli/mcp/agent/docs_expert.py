"""
Simple docs expert agent for the MCP server.
This provides basic SDK documentation assistance.
"""

from typing import Any, Dict
from codegen.sdk.core.codebase import Codebase


class SimpleSDKExpert:
    """A simple SDK expert that provides basic documentation assistance."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
    
    def invoke(self, input_data: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a query about the Codegen SDK.
        
        Args:
            input_data: Dictionary containing the user's query
            config: Configuration options (unused in this simple implementation)
            
        Returns:
            Dictionary with response messages
        """
        query = input_data.get("input", "")
        
        # Simple response based on common SDK questions
        response = self._generate_response(query)
        
        return {
            "messages": [
                type('Message', (), {
                    'content': response
                })()
            ]
        }
    
    def _generate_response(self, query: str) -> str:
        """Generate a response based on the query."""
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
        
        elif "fileanalyzer" in query_lower or "file analyzer" in query_lower:
            return """The FileAnalyzer class helps analyze individual files. Example usage:

```python
from codegen.sdk.core.file_analyzer import FileAnalyzer

# Analyze a specific file
analyzer = FileAnalyzer("/path/to/file.py")
analysis = analyzer.analyze()

# Get imports, functions, classes
imports = analysis.imports
functions = analysis.functions
classes = analysis.classes
```

Common use cases:
- Detecting unused imports
- Finding function definitions
- Analyzing class structures
- Extracting dependencies
"""
        
        elif "codemod" in query_lower:
            return """To create codemods with the Codegen SDK:

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

Use `codegen create` CLI command to generate codemod templates.
"""
        
        elif "typescript" in query_lower or "ts" in query_lower:
            return """For TypeScript analysis:

```python
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Initialize with TypeScript focus
codebase = Codebase("/path/to/ts/project")
ts_files = codebase.get_files_by_language(ProgrammingLanguage.TYPESCRIPT)

# Analyze TypeScript-specific patterns
for file in ts_files:
    if file.path.endswith('.ts') or file.path.endswith('.tsx'):
        # Process TypeScript files
        pass
```
"""
        
        elif "python" in query_lower:
            return """For Python analysis:

```python
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Focus on Python files
codebase = Codebase("/path/to/python/project")
py_files = codebase.get_files_by_language(ProgrammingLanguage.PYTHON)

# Common Python analysis tasks
for file in py_files:
    # Analyze imports, functions, classes
    analysis = file.analyze()
    unused_imports = analysis.get_unused_imports()
```
"""
        
        else:
            return f"""I can help you with the Codegen SDK! Here are some common topics:

**Codebase Analysis:**
- Use `Codebase` class to analyze entire repositories
- Filter files by language or extension
- Perform deep structural analysis

**File Analysis:**
- Use `FileAnalyzer` for individual file analysis
- Extract imports, functions, classes
- Detect unused code and dependencies

**Codemod Creation:**
- Create transformation rules with the `Codemod` class
- Apply systematic changes across codebases
- Use CLI tools for codemod generation

**Language Support:**
- TypeScript/JavaScript analysis
- Python code transformation
- Multi-language codebase handling

For your specific question: "{query}"

Could you provide more details about what you're trying to accomplish? I can give you more targeted guidance based on your specific use case.

For comprehensive documentation, visit: https://docs.codegen.com/introduction/api
"""


def create_sdk_expert_agent(codebase: Codebase) -> SimpleSDKExpert:
    """Create a simple SDK expert agent."""
    return SimpleSDKExpert(codebase)

