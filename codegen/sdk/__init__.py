"""Codegen SDK - Graph-sitter integration for code analysis and manipulation.

This module provides the core SDK functionality for working with codebases,
functions, and programming language analysis.
"""

# Core exports
try:
    from codegen.sdk.core.codebase import Codebase
    from codegen.sdk.core.function import Function
except ImportError:
    # Fallback classes if dependencies are missing
    class Codebase:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Codebase(placeholder - dependencies missing)"
            
    class Function:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
        def __repr__(self):
            return "Function(placeholder - dependencies missing)"

# Enums
from codegen.sdk.shared.enums.programming_language import ProgrammingLanguage

# Configuration (mock for now)
class Config:
    tree_sitter_enabled = True
    ai_features_enabled = True

config = Config()

# Analysis functions (mock for now)
def analyze_codebase(*args, **kwargs):
    """Analyze a codebase structure and dependencies."""
    return {"status": "mock", "args": args, "kwargs": kwargs}

def parse_code(*args, **kwargs):
    """Parse code using tree-sitter."""
    return {"status": "mock", "args": args, "kwargs": kwargs}

def generate_code(*args, **kwargs):
    """Generate code based on analysis."""
    return {"status": "mock", "args": args, "kwargs": kwargs}

__all__ = [
    "Codebase",
    "Function", 
    "ProgrammingLanguage",
    "config",
    "analyze_codebase",
    "parse_code", 
    "generate_code"
]