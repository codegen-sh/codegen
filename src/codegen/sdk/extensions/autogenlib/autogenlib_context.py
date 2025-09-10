#!/usr/bin/env python3
"""
Enhanced AutoGenLib Context Module
Provides comprehensive context enrichment for AI-driven code analysis and fixing
"""

import os
import logging
from typing import Dict, Optional, Any, List

from graph_sitter import Codebase
from solidlsp.lsp_protocol_handler.lsp_types import Diagnostic, Range

# Import LSPDiagnosticsManager's EnhancedDiagnostic
from lsp_diagnostics import EnhancedDiagnostic

# Import existing autogenlib components
from autogenlib._caller import get_caller_info
from autogenlib._generator import get_codebase_context as get_autogenlib_codebase_context
from autogenlib._context import get_module_context, extract_defined_names
from autogenlib._cache import get_all_modules, get_cached_code, get_cached_prompt

# Import GraphSitterAnalyzer for codebase overview
from graph_sitter_analysis import GraphSitterAnalyzer

logger = logging.getLogger(__name__)

def get_llm_codebase_overview(codebase: Codebase) -> Dict[str, str]:
    """
    Provides a high-level summary of the entire codebase for the LLM.
    """
    analyzer = GraphSitterAnalyzer(codebase)
    overview = analyzer.get_codebase_overview()
    return {"codebase_overview": overview.get("summary", "No specific codebase overview available.")}

def get_comprehensive_symbol_context(codebase: Codebase, symbol_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
    """Get comprehensive context for a symbol using all available Graph-Sitter APIs."""
    analyzer = GraphSitterAnalyzer(codebase)
    
    # Get symbol details
    symbol_details = analyzer.get_symbol_details(symbol_name, filepath)
    
    # Get extended context using reveal_symbol
    reveal_info = analyzer.reveal_symbol_relationships(symbol_name, filepath=filepath, max_depth=3, max_tokens=2000)
    
    # Get function-specific details if it's a function
    function_details = None
    if symbol_details.get("error") is None and symbol_details.get("symbol_type") == "Function":
        function_details = analyzer.get_function_details(symbol_name, filepath)
    
    # Get class-specific details if it's a class
    class_details = None
    if symbol_details.get("error") is None and symbol_details.get("symbol_type") == "Class":
        class_details = analyzer.get_class_details(symbol_name, filepath)
    
    return {
        "symbol_details": symbol_details,
        "reveal_info": reveal_info,
        "function_details": function_details,
        "class_details": class_details,
        "extended_dependencies": reveal_info.dependencies if reveal_info.dependencies else [],
        "extended_usages": reveal_info.usages if reveal_info.usages else []
    }

def get_file_context(codebase: Codebase, filepath: str) -> Dict[str, Any]:
    """Get comprehensive context for a file."""
    analyzer = GraphSitterAnalyzer(codebase)
    
    # Get file details
    file_details = analyzer.get_file_details(filepath)
    
    # Get import relationships
    import_analysis = analyzer.analyze_import_relationships(filepath)
    
    # Get directory listing for context
    directory_path = os.path.dirname(filepath) or "./"
    directory_info = analyzer.list_directory_contents(directory_path, depth=1)
    
    # View file content with line numbers
    file_view = analyzer.view_file_content(filepath, line_numbers=True, max_lines=100)
    
    return {
        "file_details": file_details,
        "import_analysis": import_analysis,
        "directory_context": directory_info,
        "file_preview": file_view,
        "related_files": [
            imp["imported_by"] for imp in import_analysis.get("inbound_imports", [])
        ] if import_analysis.get("error") is None else []
    }

def get_autogenlib_enhanced_context(enhanced_diagnostic: EnhancedDiagnostic) -> Dict[str, Any]:
    """Get enhanced context using AutoGenLib's context retrieval capabilities."""
    
    # Get caller context from AutoGenLib
    caller_info = get_caller_info()
    
    # Get module context if available
    module_name = enhanced_diagnostic["relative_file_path"].replace("/", ".").replace(".py", "")
    module_context = get_module_context(module_name)
    
    # Get AutoGenLib's internal codebase context
    autogenlib_codebase_context = get_autogenlib_codebase_context()
    
    # Get all cached modules for broader context
    all_cached_modules = get_all_modules()
    
    # Extract defined names from the file
    defined_names = extract_defined_names(enhanced_diagnostic["file_content"])
    
    # Get cached code and prompts
    cached_code = get_cached_code(module_name)
    cached_prompt = get_cached_prompt(module_name)
    
    return {
        "caller_info": {
            "filename": caller_info.get("filename", "unknown"),
            "code": caller_info.get("code", ""),
            "code_length": len(caller_info.get("code", "")),
            "relevant_snippets": _extract_relevant_code_snippets(caller_info.get("code", ""), enhanced_diagnostic)
        },
        "module_context": {
            "module_name": module_name,
            "defined_names": list(defined_names),
            "cached_code": cached_code or "",
            "cached_prompt": cached_prompt or "",
            "has_cached_context": bool(module_context),
            "module_dependencies": _analyze_module_dependencies(module_name, all_cached_modules)
        },
        "autogenlib_codebase_context": autogenlib_codebase_context,
        "cached_modules_overview": {
            "total_modules": len(all_cached_modules),
            "module_names": list(all_cached_modules.keys()),
            "related_modules": _find_related_modules(module_name, all_cached_modules)
        },
        "file_analysis": {
            "defined_names_count": len(defined_names),
            "file_size": len(enhanced_diagnostic["file_content"]),
            "line_count": len(enhanced_diagnostic["file_content"].splitlines()),
            "import_statements": _count_import_statements(enhanced_diagnostic["file_content"]),
            "function_definitions": _count_function_definitions(enhanced_diagnostic["file_content"]),
            "class_definitions": _count_class_definitions(enhanced_diagnostic["file_content"])
        }
    }

def get_ai_fix_context(enhanced_diagnostic: EnhancedDiagnostic, codebase: Codebase) -> EnhancedDiagnostic:
    """
    Aggregates all relevant context for the AI to resolve a diagnostic.
    This is the central context aggregation function.
    """
    
    # 1. Get Graph-Sitter context
    diag = enhanced_diagnostic["diagnostic"]
    
    # Find symbol at diagnostic location
    symbol_at_error = None
    try:
        file_obj = codebase.get_file(enhanced_diagnostic["relative_file_path"])
        
        # Try to find function containing the error
        for func in file_obj.functions:
            if (hasattr(func, 'start_point') and hasattr(func, 'end_point') and
                func.start_point.line <= diag.range.line <= func.end_point.line):
                symbol_at_error = func
                break
        
        # Try to find class containing the error if no function found
        if not symbol_at_error:
            for cls in file_obj.classes:
                if (hasattr(cls, 'start_point') and hasattr(cls, 'end_point') and
                    cls.start_point.line <= diag.range.line <= cls.end_point.line):
                    symbol_at_error = cls
                    break
                    
    except Exception as e:
        logger.warning(f"Could not find symbol at error location: {e}")

    # Get comprehensive symbol context if found
    symbol_context = {}
    if symbol_at_error:
        symbol_context = get_comprehensive_symbol_context(
            codebase, 
            symbol_at_error.name, 
            enhanced_diagnostic["relative_file_path"]
        )
    
    # Get file context
    file_context = get_file_context(codebase, enhanced_diagnostic["relative_file_path"])
    
    # Get codebase overview
    codebase_overview = get_llm_codebase_overview(codebase)
    
    # 2. Get AutoGenLib enhanced context
    autogenlib_context = get_autogenlib_enhanced_context(enhanced_diagnostic)
    
    # 3. Analyze related patterns using Graph-Sitter
    analyzer = GraphSitterAnalyzer(codebase)
    
    # Find similar errors in the codebase
    similar_patterns = []
    if diag.code:
        # Look for other diagnostics with the same code
        for other_file in codebase.files:
            if other_file.filepath != enhanced_diagnostic["relative_file_path"]:
                # This is a simplified pattern matching - in practice, you'd want more sophisticated analysis
                if diag.code.lower() in other_file.source.lower():
                    similar_patterns.append({
                        "file": other_file.filepath,
                        "pattern": diag.code,
                        "confidence": 0.6,
                        "line_count": len(other_file.source.splitlines())
                    })
    
    # 4. Get architectural context
    architectural_context = {
        "file_role": _determine_file_role(enhanced_diagnostic["relative_file_path"]),
        "module_dependencies": len(file_context.get("import_analysis", {}).get("imports_analysis", [])),
        "is_test_file": "test" in enhanced_diagnostic["relative_file_path"].lower(),
        "is_main_file": enhanced_diagnostic["relative_file_path"].endswith("main.py") or enhanced_diagnostic["relative_file_path"].endswith("__main__.py"),
        "directory_depth": len(enhanced_diagnostic["relative_file_path"].split(os.sep)) - 1,
        "related_symbols": _find_related_symbols_in_file(codebase, enhanced_diagnostic["relative_file_path"], diag.range.line)
    }
    
    # 5. Get error resolution context
    resolution_context = {
        "error_category": _categorize_error(diag),
        "common_fixes": _get_common_fixes_for_error(diag),
        "resolution_confidence": _estimate_resolution_confidence(diag, symbol_context),
        "requires_manual_review": _requires_manual_review(diag),
        "automated_fix_available": _has_automated_fix(diag)
    }
    
    # 6. Aggregate all context
    enhanced_diagnostic["graph_sitter_context"] = {
        "symbol_context": symbol_context,
        "file_context": file_context,
        "codebase_overview": codebase_overview,
        "similar_patterns": similar_patterns,
        "architectural_context": architectural_context,
        "resolution_context": resolution_context,
        "visualization_data": _get_visualization_context(analyzer, symbol_at_error) if symbol_at_error else {}
    }
    
    enhanced_diagnostic["autogenlib_context"] = autogenlib_context
    
    return enhanced_diagnostic

def _extract_relevant_code_snippets(caller_code: str, enhanced_diagnostic: EnhancedDiagnostic) -> List[str]:
    """Extract relevant code snippets from caller code."""
    if not caller_code:
        return []
    
    snippets = []
    lines = caller_code.split('\n')
    
    # Look for imports related to the diagnostic file
    file_name = os.path.basename(enhanced_diagnostic["relative_file_path"]).replace('.py', '')
    for i, line in enumerate(lines):
        if 'import' in line and file_name in line:
            # Include surrounding context
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            snippets.append('\n'.join(lines[start:end]))
    
    # Look for function calls that might be related to the error
    diag_message = enhanced_diagnostic["diagnostic"].message.lower()
    for i, line in enumerate(lines):
        if any(word in line.lower() for word in diag_message.split() if len(word) > 3):
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            snippets.append('\n'.join(lines[start:end]))
    
    return snippets[:5]  # Limit to 5 most relevant snippets

def _analyze_module_dependencies(module_name: str, all_cached_modules: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze dependencies between cached modules."""
    dependencies = {
        "direct_dependencies": [],
        "dependent_modules": [],
        "circular_dependencies": []
    }
    
    if module_name not in all_cached_modules:
        return dependencies
    
    module_code = all_cached_modules[module_name].get("code", "")
    
    # Find direct dependencies
    for other_module, other_data in all_cached_modules.items():
        if other_module != module_name:
            if f"from {other_module}" in module_code or f"import {other_module}" in module_code:
                dependencies["direct_dependencies"].append(other_module)
            
            other_code = other_data.get("code", "")
            if f"from {module_name}" in other_code or f"import {module_name}" in other_code:
                dependencies["dependent_modules"].append(other_module)
    
    # Check for circular dependencies
    for dep in dependencies["direct_dependencies"]:
        if module_name in dependencies["dependent_modules"] and dep in dependencies["dependent_modules"]:
            dependencies["circular_dependencies"].append(dep)
    
    return dependencies

def _find_related_modules(module_name: str, all_cached_modules: Dict[str, Any]) -> List[str]:
    """Find modules related to the given module."""
    related = []
    
    # Find modules with similar names
    base_name = module_name.split('.')[-1]
    for other_module in all_cached_modules.keys():
        other_base = other_module.split('.')[-1]
        if base_name in other_base or other_base in base_name:
            if other_module != module_name:
                related.append(other_module)
    
    return related[:10]  # Limit to 10 most related

def _count_import_statements(file_content: str) -> int:
    """Count import statements in file content."""
    lines = file_content.split('\n')
    return sum(1 for line in lines if line.strip().startswith(('import ', 'from ')))

def _count_function_definitions(file_content: str) -> int:
    """Count function definitions in file content."""
    return len(re.findall(r'^\s*def\s+\w+', file_content, re.MULTILINE))

def _count_class_definitions(file_content: str) -> int:
    """Count class definitions in file content."""
    return len(re.findall(r'^\s*class\s+\w+', file_content, re.MULTILINE))

def _determine_file_role(filepath: str) -> str:
    """Determine the role of a file in the codebase architecture."""
    filepath_lower = filepath.lower()
    
    if "test" in filepath_lower:
        return "test"
    elif "main" in filepath_lower or "__main__" in filepath_lower:
        return "entry_point"
    elif "config" in filepath_lower or "settings" in filepath_lower:
        return "configuration"
    elif "model" in filepath_lower or "schema" in filepath_lower:
        return "data_model"
    elif "view" in filepath_lower or "template" in filepath_lower:
        return "presentation"
    elif "controller" in filepath_lower or "handler" in filepath_lower:
        return "controller"
    elif "service" in filepath_lower or "business" in filepath_lower:
        return "business_logic"
    elif "util" in filepath_lower or "helper" in filepath_lower:
        return "utility"
    elif "api" in filepath_lower or "endpoint" in filepath_lower:
        return "api"
    elif "__init__" in filepath_lower:
        return "module_init"
    else:
        return "general"

def _find_related_symbols_in_file(codebase: Codebase, filepath: str, error_line: int) -> List[Dict[str, Any]]:
    """Find symbols related to the error location."""
    try:
        file_obj = codebase.get_file(filepath)
        related_symbols = []
        
        # Find symbols near the error line
        for func in file_obj.functions:
            if hasattr(func, 'start_point') and hasattr(func, 'end_point'):
                if func.start_point.line <= error_line <= func.end_point.line:
                    related_symbols.append({
                        "name": func.name,
                        "type": "function",
                        "distance": 0,  # Contains the error
                        "complexity": _calculate_simple_complexity(func)
                    })
                elif abs(func.start_point.line - error_line) <= 10:
                    related_symbols.append({
                        "name": func.name,
                        "type": "function", 
                        "distance": abs(func.start_point.line - error_line),
                        "complexity": _calculate_simple_complexity(func)
                    })
        
        # Find classes near the error line
        for cls in file_obj.classes:
            if hasattr(cls, 'start_point') and hasattr(cls, 'end_point'):
                if cls.start_point.line <= error_line <= cls.end_point.line:
                    related_symbols.append({
                        "name": cls.name,
                        "type": "class",
                        "distance": 0,
                        "methods_count": len(cls.methods)
                    })
        
        return sorted(related_symbols, key=lambda x: x["distance"])[:5]
        
    except Exception as e:
        logger.warning(f"Error finding related symbols: {e}")
        return []

def _calculate_simple_complexity(func) -> int:
    """Calculate simple complexity metric."""
    if hasattr(func, "source") and func.source:
        return func.source.count("if ") + func.source.count("for ") + func.source.count("while ") + 1
    return 1

def _categorize_error(diagnostic: Diagnostic) -> str:
    """Categorize error based on diagnostic information."""
    message = diagnostic.message.lower()
    code = str(diagnostic.code).lower() if diagnostic.code else ""
    
    if any(keyword in message for keyword in ["import", "module", "not found"]):
        return "import_error"
    elif any(keyword in message for keyword in ["type", "annotation", "expected"]):
        return "type_error"
    elif any(keyword in message for keyword in ["syntax", "invalid", "unexpected"]):
        return "syntax_error"
    elif any(keyword in message for keyword in ["unused", "defined", "never used"]):
        return "unused_code"
    elif any(keyword in message for keyword in ["missing", "required", "undefined"]):
        return "missing_definition"
    elif "circular" in message or "cycle" in message:
        return "circular_dependency"
    else:
        return "general_error"

def _get_common_fixes_for_error(diagnostic: Diagnostic) -> List[str]:
    """Get common fixes for an error category."""
    category = _categorize_error(diagnostic)
    
    fixes_map = {
        "import_error": [
            "Add missing import statement",
            "Fix import path",
            "Install missing package",
            "Check module availability"
        ],
        "type_error": [
            "Add type annotations",
            "Fix type mismatch",
            "Import missing types",
            "Update function signature"
        ],
        "syntax_error": [
            "Fix syntax issues",
            "Check parentheses/brackets",
            "Fix indentation",
            "Remove invalid characters"
        ],
        "unused_code": [
            "Remove unused imports",
            "Remove unused variables",
            "Add underscore prefix for intentionally unused",
            "Use the variable or remove it"
        ],
        "missing_definition": [
            "Define missing variable/function",
            "Add missing import",
            "Check spelling",
            "Add default value"
        ],
        "circular_dependency": [
            "Refactor to break circular imports",
            "Move shared code to separate module",
            "Use dependency injection",
            "Reorganize module structure"
        ]
    }
    
    return fixes_map.get(category, ["Manual review required"])

def _estimate_resolution_confidence(diagnostic: Diagnostic, symbol_context: Dict[str, Any]) -> float:
    """Estimate confidence in automated resolution."""
    confidence = 0.5  # Base confidence
    
    # Higher confidence for well-understood error types
    category = _categorize_error(diagnostic)
    category_confidence = {
        "import_error": 0.8,
        "unused_code": 0.9,
        "type_error": 0.7,
        "syntax_error": 0.6,
        "missing_definition": 0.5,
        "circular_dependency": 0.3
    }
    
    confidence = category_confidence.get(category, 0.5)
    
    # Adjust based on symbol context availability
    if symbol_context and symbol_context.get("symbol_details", {}).get("error") is None:
        confidence += 0.1
    
    # Adjust based on error message clarity
    if len(diagnostic.message) > 50:  # Detailed error messages
        confidence += 0.1
    
    return min(1.0, confidence)

def _requires_manual_review(diagnostic: Diagnostic) -> bool:
    """Check if error requires manual review."""
    category = _categorize_error(diagnostic)
    manual_review_categories = ["circular_dependency", "missing_definition"]
    
    return (
        category in manual_review_categories or
        "todo" in diagnostic.message.lower() or
        "fixme" in diagnostic.message.lower() or
        diagnostic.severity and diagnostic.severity.value == 1  # Critical errors
    )

def _has_automated_fix(diagnostic: Diagnostic) -> bool:
    """Check if error has available automated fix."""
    category = _categorize_error(diagnostic)
    automated_categories = ["unused_code", "import_error", "type_error"]
    
    return category in automated_categories

def _get_visualization_context(analyzer: GraphSitterAnalyzer, symbol) -> Dict[str, Any]:
    """Get visualization context for a symbol."""
    if not symbol:
        return {}
    
    try:
        # Create blast radius visualization
        blast_radius = analyzer.create_blast_radius_visualization(symbol.name)
        
        # Create dependency trace if it's a function
        dependency_trace = {}
        if hasattr(symbol, 'function_calls'):  # It's a function
            dependency_trace = analyzer.create_dependency_trace_visualization(symbol.name)
        
        return {
            "blast_radius": blast_radius,
            "dependency_trace": dependency_trace,
            "symbol_relationships": {
                "usages_count": len(symbol.usages),
                "dependencies_count": len(symbol.dependencies),
                "complexity": analyzer._calculate_cyclomatic_complexity(symbol) if hasattr(symbol, 'source') else 0
            }
        }
    except Exception as e:
        logger.warning(f"Error creating visualization context: {e}")
        return {}

def get_error_pattern_context(codebase: Codebase, error_category: str, max_examples: int = 5) -> Dict[str, Any]:
    """Get context about similar error patterns in the codebase."""
    analyzer = GraphSitterAnalyzer(codebase)
    
    pattern_context = {
        "category": error_category,
        "common_causes": _get_common_causes_for_error_category(error_category),
        "resolution_strategies": _get_resolution_strategies_for_error_category(error_category),
        "related_files": [],
        "similar_errors_count": 0,
        "pattern_analysis": {}
    }
    
    # Search for similar patterns in the codebase
    search_terms = _get_search_terms_for_error_category(error_category)
    for term in search_terms:
        for file_obj in codebase.files:
            if hasattr(file_obj, "source") and term.lower() in file_obj.source.lower():
                pattern_context["related_files"].append({
                    "filepath": file_obj.filepath,
                    "matches": file_obj.source.lower().count(term.lower()),
                    "file_role": _determine_file_role(file_obj.filepath)
                })
                pattern_context["similar_errors_count"] += 1
                
                if len(pattern_context["related_files"]) >= max_examples:
                    break
    
    # Analyze patterns
    if pattern_context["related_files"]:
        file_roles = [f["file_role"] for f in pattern_context["related_files"]]
        pattern_context["pattern_analysis"] = {
            "most_affected_role": max(set(file_roles), key=file_roles.count),
            "role_distribution": {role: file_roles.count(role) for role in set(file_roles)},
            "average_matches_per_file": sum(f["matches"] for f in pattern_context["related_files"]) / len(pattern_context["related_files"])
        }
    
    return pattern_context

def _get_common_causes_for_error_category(category: str) -> List[str]:
    """Get common causes for an error category."""
    causes_map = {
        "import_error": [
            "Missing package installation",
            "Incorrect import path",
            "Module not in PYTHONPATH",
            "Circular import dependencies"
        ],
        "type_error": [
            "Missing type annotations",
            "Incorrect type usage",
            "Type mismatch in function calls",
            "Generic type parameter issues"
        ],
        "syntax_error": [
            "Missing parentheses or brackets",
            "Incorrect indentation",
            "Invalid character usage",
            "Incomplete statements"
        ],
        "unused_code": [
            "Imports added but never used",
            "Variables defined but not referenced",
            "Functions created but not called",
            "Refactoring artifacts"
        ],
        "missing_definition": [
            "Variable used before definition",
            "Function called but not defined",
            "Missing import for used symbol",
            "Typo in variable/function name"
        ],
        "circular_dependency": [
            "Mutual dependencies between modules",
            "Poor module organization",
            "Shared state between modules",
            "Tight coupling between components"
        ]
    }
    return causes_map.get(category, ["Unknown causes"])

def _get_resolution_strategies_for_error_category(category: str) -> List[str]:
    """Get resolution strategies for an error category."""
    strategies_map = {
        "import_error": [
            "Fix import paths and module names",
            "Install missing dependencies",
            "Add modules to PYTHONPATH",
            "Reorganize module structure"
        ],
        "type_error": [
            "Add explicit type annotations",
            "Fix type mismatches",
            "Import missing type definitions",
            "Update function signatures"
        ],
        "syntax_error": [
            "Fix syntax issues automatically",
            "Use code formatter",
            "Check language syntax rules",
            "Validate with linter"
        ],
        "unused_code": [
            "Remove unused imports and variables",
            "Use import optimization tools",
            "Add underscore prefix for intentional unused",
            "Refactor to eliminate dead code"
        ],
        "missing_definition": [
            "Define missing variables and functions",
            "Add missing imports",
            "Fix typos in names",
            "Add default values where appropriate"
        ],
        "circular_dependency": [
            "Refactor shared code to separate module",
            "Use dependency injection patterns",
            "Reorganize module hierarchy",
            "Break tight coupling between modules"
        ]
    }
    return strategies_map.get(category, ["Manual review and correction required"])

def _get_search_terms_for_error_category(category: str) -> List[str]:
    """Get search terms to find similar patterns for an error category."""
    terms_map = {
        "import_error": ["import ", "from ", "ImportError", "ModuleNotFoundError"],
        "type_error": ["TypeError", "def ", "class ", "->", ":"],
        "syntax_error": ["SyntaxError", "def ", "class ", "if ", "for "],
        "unused_code": ["import ", "from ", "def ", "="],
        "missing_definition": ["NameError", "UnboundLocalError", "def ", "="],
        "circular_dependency": ["import ", "from "]
    }
    return terms_map.get(category, [])