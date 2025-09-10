#!/usr/bin/env python3
"""
Enhanced AutoGenLib AI Resolution Module
Provides comprehensive AI-driven error resolution with full context integration
"""

import os
import logging
import json
from typing import Dict, Any

import openai

from graph_sitter import Codebase

# Import autogenlib's core generation and utility functions
from autogenlib._generator import extract_python_code, validate_code

# Import enhanced context functions and EnhancedDiagnostic
from lsp_diagnostics import EnhancedDiagnostic

logger = logging.getLogger(__name__)


def resolve_diagnostic_with_ai(
    enhanced_diagnostic: EnhancedDiagnostic, codebase: Codebase
) -> Dict[str, Any]:
    """
    Generates a fix for a given LSP diagnostic using an AI model, with comprehensive context.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set.")
        return {"status": "error", "message": "OpenAI API key not configured."}

    base_url = os.environ.get("OPENAI_API_BASE_URL")
    model = os.environ.get(
        "OPENAI_MODEL", "gpt-4o"
    )  # Using gpt-4o for better code generation

    client = openai.OpenAI(api_key=api_key, base_url=base_url)

    # Prepare comprehensive context for the LLM
    diag = enhanced_diagnostic["diagnostic"]

    # Construct the system message with comprehensive instructions
    system_message = """
    You are an expert software engineer and code fixer with deep knowledge of software architecture, 
    design patterns, and best practices. Your task is to analyze code diagnostics and provide 
    precise, contextually-aware fixes.

    You have access to:
    1. LSP diagnostic information (static analysis)
    2. Runtime error context (if available)
    3. UI interaction error context (if available)
    4. Graph-Sitter codebase analysis (symbol relationships, dependencies, usages)
    5. AutoGenLib context (caller information, module context)
    6. Architectural context (file role, module structure)
    7. Visualization data (blast radius, dependency traces)
    8. Error pattern analysis (similar errors, resolution strategies)

    Follow these guidelines:
    1. Understand the diagnostic: Analyze the message, severity, and exact location
    2. Consider the full context: Use all provided context to understand the broader implications
    3. Identify root causes: Look beyond symptoms to find underlying issues
    4. Propose comprehensive fixes: Address not just the immediate error but related issues
    5. Maintain code quality: Ensure fixes follow best practices and coding standards
    6. Consider side effects: Think about how changes might affect other parts of the codebase

    Output format: Return a JSON object with:
    - 'fixed_code': The corrected code (can be a snippet, function, or entire file)
    - 'explanation': Detailed explanation of the fix and why it's necessary
    - 'confidence': Confidence level (0.0-1.0) in the fix
    - 'side_effects': Potential side effects or additional changes needed
    - 'testing_suggestions': Suggestions for testing the fix
    - 'related_changes': Other files or symbols that might need updates
    """

    # Construct comprehensive user prompt
    user_prompt = f"""
    DIAGNOSTIC INFORMATION:
    ======================
    Severity: {diag.severity.name if diag.severity else "Unknown"}
    Code: {diag.code}
    Source: {diag.source}
    Message: {diag.message}
    File: {enhanced_diagnostic["relative_file_path"]}
    Line: {diag.range.line + 1}, Character: {diag.range.character}
    End Line: {diag.range.end.line + 1}, End Character: {diag.range.end.character}

    RELEVANT CODE SNIPPET (with '>>>' markers for the diagnostic range):
    ================================================================
    ```python
    {enhanced_diagnostic["relevant_code_snippet"]}
    ```

    FULL FILE CONTENT:
    ==================
    ```python
    {enhanced_diagnostic["file_content"]}
    ```

    GRAPH-SITTER CONTEXT:
    =====================
    Codebase Overview: {enhanced_diagnostic["graph_sitter_context"].get("codebase_overview", {}).get("codebase_overview", "N/A")}
    
    Symbol Context: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("symbol_context", {}), indent=2)}
    
    File Context: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("file_context", {}), indent=2)}
    
    Architectural Context: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("architectural_context", {}), indent=2)}
    
    Resolution Context: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("resolution_context", {}), indent=2)}
    
    Visualization Data: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("visualization_data", {}), indent=2)}

    AUTOGENLIB CONTEXT:
    ===================
    {json.dumps(enhanced_diagnostic["autogenlib_context"], indent=2)}

    RUNTIME CONTEXT:
    ================
    Runtime Errors: {json.dumps(enhanced_diagnostic["runtime_context"], indent=2)}
    
    UI Interaction Context: {json.dumps(enhanced_diagnostic["ui_interaction_context"], indent=2)}

    ADDITIONAL CONTEXT:
    ===================
    Similar Patterns: {json.dumps(enhanced_diagnostic["graph_sitter_context"].get("similar_patterns", []), indent=2)}

    Your task is to provide a comprehensive fix for this diagnostic, considering all the context provided.
    Return a JSON object with the required fields: fixed_code, explanation, confidence, side_effects, testing_suggestions, related_changes.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,  # Keep it low for deterministic fixes
            max_tokens=4000,  # Increased for comprehensive responses
        )

        content = response.choices[0].message.content.strip()
        fix_info = {}
        try:
            fix_info = json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"AI response was not valid JSON: {content}")
            return {
                "status": "error",
                "message": "AI returned invalid JSON.",
                "raw_response": content,
            }

        fixed_code = fix_info.get("fixed_code", "")
        explanation = fix_info.get("explanation", "No explanation provided.")
        confidence = fix_info.get("confidence", 0.5)
        side_effects = fix_info.get("side_effects", [])
        testing_suggestions = fix_info.get("testing_suggestions", [])
        related_changes = fix_info.get("related_changes", [])

        if not fixed_code:
            return {
                "status": "error",
                "message": "AI did not provide fixed code.",
                "explanation": explanation,
            }

        # Basic validation of the fixed code
        if not validate_code(fixed_code):
            logger.warning("AI generated code that is not syntactically valid.")
            # Attempt to extract valid code if it's wrapped in markdown
            extracted_code = extract_python_code(fixed_code)
            if validate_code(extracted_code):
                fixed_code = extracted_code
            else:
                return {
                    "status": "warning",
                    "message": "AI generated code with syntax errors.",
                    "fixed_code": fixed_code,
                    "explanation": explanation,
                    "confidence": confidence
                    * 0.5,  # Reduce confidence for invalid code
                }

        return {
            "status": "success",
            "fixed_code": fixed_code,
            "explanation": explanation,
            "confidence": confidence,
            "side_effects": side_effects,
            "testing_suggestions": testing_suggestions,
            "related_changes": related_changes,
        }

    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return {"status": "error", "message": f"OpenAI API error: {e}"}
    except Exception as e:
        logger.error(f"Error resolving diagnostic with AI: {e}")
        return {"status": "error", "message": f"An unexpected error occurred: {e}"}


def resolve_runtime_error_with_ai(
    runtime_error: Dict[str, Any], codebase: Codebase
) -> Dict[str, Any]:
    """
    Resolve runtime errors using AI with full context.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "OpenAI API key not configured."}

    client = openai.OpenAI(
        api_key=api_key, base_url=os.environ.get("OPENAI_API_BASE_URL")
    )

    system_message = """
    You are an expert Python developer specializing in runtime error resolution.
    You have access to the full traceback, codebase context, and related information.
    
    Provide comprehensive fixes that:
    1. Address the immediate runtime error
    2. Add proper error handling
    3. Include defensive programming practices
    4. Consider the broader codebase impact
    
    Return JSON with: fixed_code, explanation, confidence, prevention_measures
    """

    user_prompt = f"""
    RUNTIME ERROR:
    ==============
    Error Type: {runtime_error["error_type"]}
    Message: {runtime_error["message"]}
    File: {runtime_error["file_path"]}
    Line: {runtime_error["line"]}
    Function: {runtime_error["function"]}
    
    FULL TRACEBACK:
    ===============
    {runtime_error["traceback"]}
    
    Please provide a comprehensive fix for this runtime error.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        logger.error(f"Error resolving runtime error with AI: {e}")
        return {"status": "error", "message": f"Failed to resolve runtime error: {e}"}


def resolve_ui_error_with_ai(
    ui_error: Dict[str, Any], codebase: Codebase
) -> Dict[str, Any]:
    """
    Resolve UI interaction errors using AI with full context.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "OpenAI API key not configured."}

    client = openai.OpenAI(
        api_key=api_key, base_url=os.environ.get("OPENAI_API_BASE_URL")
    )

    system_message = """
    You are an expert frontend developer specializing in React/JavaScript error resolution.
    You understand component lifecycles, state management, and user interaction patterns.
    
    Provide fixes that:
    1. Resolve the immediate UI error
    2. Improve user experience
    3. Add proper error boundaries
    4. Follow React best practices
    
    Return JSON with: fixed_code, explanation, confidence, user_impact
    """

    user_prompt = f"""
    UI INTERACTION ERROR:
    ====================
    Error Type: {ui_error["error_type"]}
    Message: {ui_error["message"]}
    File: {ui_error["file_path"]}
    Line: {ui_error["line"]}
    Component: {ui_error.get("component", "Unknown")}
    
    Please provide a comprehensive fix for this UI error.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()
        return json.loads(content)

    except Exception as e:
        logger.error(f"Error resolving UI error with AI: {e}")
        return {"status": "error", "message": f"Failed to resolve UI error: {e}"}


def resolve_multiple_errors_with_ai(
    enhanced_diagnostics: List[EnhancedDiagnostic],
    codebase: Codebase,
    max_fixes: int = 10,
) -> Dict[str, Any]:
    """
    Resolve multiple errors in batch using AI with pattern recognition.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "OpenAI API key not configured."}

    client = openai.OpenAI(
        api_key=api_key, base_url=os.environ.get("OPENAI_API_BASE_URL")
    )

    # Group errors by category and file
    error_groups = {}
    for enhanced_diag in enhanced_diagnostics[:max_fixes]:
        diag = enhanced_diag["diagnostic"]
        file_path = enhanced_diag["relative_file_path"]
        error_category = (
            enhanced_diag["graph_sitter_context"]
            .get("resolution_context", {})
            .get("error_category", "general")
        )

        key = f"{error_category}:{file_path}"
        if key not in error_groups:
            error_groups[key] = []
        error_groups[key].append(enhanced_diag)

    batch_results = []

    for group_key, group_diagnostics in error_groups.items():
        error_category, file_path = group_key.split(":", 1)

        # Create batch prompt for similar errors
        system_message = f"""
        You are an expert software engineer specializing in batch error resolution.
        You are fixing {len(group_diagnostics)} {error_category} errors in {file_path}.
        
        Provide a comprehensive fix that addresses all related errors efficiently.
        Consider patterns and commonalities between the errors.
        
        Return JSON with: fixes (array of individual fixes), batch_explanation, overall_confidence
        """

        diagnostics_summary = []
        for enhanced_diag in group_diagnostics:
            diag = enhanced_diag["diagnostic"]
            diagnostics_summary.append(
                {
                    "line": diag.range.line + 1,
                    "message": diag.message,
                    "code": diag.code,
                    "snippet": enhanced_diag["relevant_code_snippet"],
                }
            )

        user_prompt = f"""
        BATCH ERROR RESOLUTION:
        ======================
        Error Category: {error_category}
        File: {file_path}
        Number of Errors: {len(group_diagnostics)}
        
        ERRORS TO FIX:
        ==============
        {json.dumps(diagnostics_summary, indent=2)}
        
        FULL FILE CONTENT:
        ==================
        ```python
        {group_diagnostics[0]["file_content"]}
        ```
        
        CONTEXT SUMMARY:
        ================
        Graph-Sitter Context: {json.dumps(group_diagnostics[0]["graph_sitter_context"], indent=2)}
        AutoGenLib Context: {json.dumps(group_diagnostics[0]["autogenlib_context"], indent=2)}
        
        Please provide a batch fix for all these related errors.
        """

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=5000,
            )

            content = response.choices[0].message.content.strip()
            batch_result = json.loads(content)
            batch_result["group_key"] = group_key
            batch_result["errors_count"] = len(group_diagnostics)
            batch_results.append(batch_result)

        except Exception as e:
            logger.error(f"Error in batch resolution for {group_key}: {e}")
            batch_results.append(
                {
                    "group_key": group_key,
                    "status": "error",
                    "message": f"Batch resolution failed: {e}",
                    "errors_count": len(group_diagnostics),
                }
            )

    return {
        "status": "success",
        "batch_results": batch_results,
        "total_groups": len(error_groups),
        "total_errors": sum(len(group) for group in error_groups.values()),
    }


def generate_comprehensive_fix_strategy(
    codebase: Codebase, error_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a comprehensive fix strategy for all errors in the codebase.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "OpenAI API key not configured."}

    client = openai.OpenAI(
        api_key=api_key, base_url=os.environ.get("OPENAI_API_BASE_URL")
    )

    system_message = """
    You are a senior software architect and code quality expert.
    Analyze the comprehensive error analysis and create a strategic plan for fixing all issues.
    
    Consider:
    1. Error priorities and dependencies
    2. Optimal fixing order to minimize conflicts
    3. Architectural improvements needed
    4. Preventive measures for future errors
    5. Testing and validation strategies
    
    Return JSON with: strategy, phases, priorities, estimated_effort, risk_assessment
    """

    user_prompt = f"""
    COMPREHENSIVE ERROR ANALYSIS:
    ============================
    Total Errors: {error_analysis.get("total", 0)}
    Critical: {error_analysis.get("critical", 0)}
    Major: {error_analysis.get("major", 0)}
    Minor: {error_analysis.get("minor", 0)}
    
    ERROR CATEGORIES:
    =================
    {json.dumps(error_analysis.get("by_category", {}), indent=2)}
    
    ERROR PATTERNS:
    ===============
    {json.dumps(error_analysis.get("error_patterns", []), indent=2)}
    
    RESOLUTION RECOMMENDATIONS:
    ===========================
    {json.dumps(error_analysis.get("resolution_recommendations", []), indent=2)}
    
    Please create a comprehensive strategy for resolving all these errors efficiently.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=3000,
        )

        content = response.choices[0].message.content.strip()
        strategy = json.loads(content)

        return {"status": "success", "strategy": strategy, "generated_at": time.time()}

    except Exception as e:
        logger.error(f"Error generating fix strategy: {e}")
        return {"status": "error", "message": f"Failed to generate strategy: {e}"}


def validate_fix_with_context(
    fixed_code: str, enhanced_diagnostic: EnhancedDiagnostic, codebase: Codebase
) -> Dict[str, Any]:
    """
    Validate a fix using comprehensive context analysis.
    """
    validation_results = {
        "syntax_valid": False,
        "context_compatible": False,
        "dependencies_satisfied": False,
        "style_consistent": False,
        "warnings": [],
        "suggestions": [],
    }

    # 1. Syntax validation
    try:
        validate_code(fixed_code)
        validation_results["syntax_valid"] = True
    except Exception as e:
        validation_results["warnings"].append(f"Syntax error: {e}")

    # 2. Context compatibility validation
    symbol_context = enhanced_diagnostic["graph_sitter_context"].get(
        "symbol_context", {}
    )
    if symbol_context and symbol_context.get("symbol_details", {}).get("error") is None:
        # Check if fix maintains expected function signature
        if "function_details" in symbol_context:
            func_details = symbol_context["function_details"]
            if "def " in fixed_code:
                validation_results["context_compatible"] = True
            else:
                validation_results["warnings"].append(
                    "Fix doesn't appear to maintain function structure"
                )

    # 3. Dependencies validation
    file_context = enhanced_diagnostic["graph_sitter_context"].get("file_context", {})
    if file_context and "import_analysis" in file_context:
        import_analysis = file_context["import_analysis"]
        # Check if fix introduces new dependencies
        for imp in import_analysis.get("imports_analysis", []):
            if imp["name"] in fixed_code and not imp["is_external"]:
                validation_results["dependencies_satisfied"] = True
                break

    # 4. Style consistency validation
    original_style = _analyze_code_style(enhanced_diagnostic["file_content"])
    fixed_style = _analyze_code_style(fixed_code)

    if _styles_compatible(original_style, fixed_style):
        validation_results["style_consistent"] = True
    else:
        validation_results["suggestions"].append(
            "Consider adjusting code style to match existing patterns"
        )

    return validation_results


def _analyze_code_style(code: str) -> Dict[str, Any]:
    """Analyze code style patterns."""
    return {
        "indentation": "spaces" if "    " in code else "tabs",
        "quote_style": "double" if code.count('"') > code.count("'") else "single",
        "line_length": max(len(line) for line in code.split("\n")) if code else 0,
        "has_type_hints": "->" in code or ": " in code,
    }


def _styles_compatible(style1: Dict[str, Any], style2: Dict[str, Any]) -> bool:
    """Check if two code styles are compatible."""
    return style1.get("indentation") == style2.get("indentation") and style1.get(
        "quote_style"
    ) == style2.get("quote_style")


import time
