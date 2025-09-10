#!/usr/bin/env python3
"""
Comprehensive Graph-Sitter Analysis Module
Integrates all graph-sitter folder functionalities for complete codebase analysis
"""

import os
import logging
import math
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from collections import defaultdict, Counter

# Import all graph-sitter modules
from graph_sitter import Codebase
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.external_module import ExternalModule

# Import all analysis functions from graph-sitter modules
from graph_sitter.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Import visualization and analysis tools
from graph_sitter.view_file import (
    ViewFileObservation,
    add_line_numbers,
    view_file
)

from graph_sitter.reveal_symbol import (
    SymbolInfo,
    RevealSymbolObservation,
    get_symbol_info,
    truncate_source,
    get_extended_context,
    reveal_symbol,
    hop_through_imports
)

from graph_sitter.list_directory import (
    DirectoryInfo,
    ListDirectoryObservation,
    list_directory
)

from graph_sitter.bash import (
    RunBashCommandObservation,
    validate_command,
    run_bash_command
)

from graph_sitter.reflection import (
    ReflectionSection,
    ReflectionObservation,
    parse_reflection_response,
    perform_reflection
)

from graph_sitter.observation import Observation

from graph_sitter.tools import get_workspace_tools

from graph_sitter.tool_output_types import (
    EditFileArtifacts,
    ViewFileArtifacts,
    ListDirectoryArtifacts,
    SearchMatch,
    SearchArtifacts,
    SemanticEditArtifacts,
    RelaceEditArtifacts
)

# Import documentation generation
from graph_sitter.generate_docs_json import generate_docs_json
from graph_sitter.mdx_docs_generation import (
    render_mdx_page_for_class,
    render_mdx_page_title,
    render_mdx_inheritence_section,
    render_mdx_attributes_section,
    render_mdx_methods_section,
    render_mdx_for_attribute,
    format_parameter_for_mdx,
    format_parameters_for_mdx,
    format_return_for_mdx,
    render_mdx_for_method,
    get_mdx_route_for_class,
    format_type_string,
    resolve_type_string,
    format_builtin_type_string,
    span_type_string_by_pipe,
    parse_link
)

# Import codebase utilities
from graph_sitter.current_code_codebase import (
    get_current_code_codebase,
    get_codegen_codebase_base_path,
    get_graphsitter_repo_path,
    import_all_codegen_sdk_modules,
    get_documented_objects
)

from graph_sitter.codegen_sdk_codebase import (
    get_codegen_sdk_codebase,
    get_codegen_sdk_subdirectories
)

# Import document functions
from graph_sitter.document_functions import (
    run as document_functions_run,
    get_extended_context as doc_get_extended_context,
    hop_through_imports as doc_hop_through_imports
)

# Import visualization modules
from graph_sitter.blast_radius import (
    generate_edge_meta as blast_generate_edge_meta,
    is_http_method,
    create_blast_radius_visualization,
    run as blast_radius_run
)

from graph_sitter.call_trace import (
    generate_edge_meta as call_generate_edge_meta,
    create_downstream_call_trace,
    run as call_trace_run
)

from graph_sitter.dependency_trace import (
    create_dependencies_visualization,
    run as dependency_trace_run
)

from graph_sitter.method_relationships import (
    generate_edge_meta as method_generate_edge_meta,
    graph_class_methods,
    create_downstream_call_trace as method_create_downstream_call_trace,
    run as method_relationships_run
)

import networkx as nx

logger = logging.getLogger(__name__)


class GraphSitterAnalyzer:
    """
    Comprehensive analysis engine using all Graph-Sitter capabilities.
    Provides unified access to all graph-sitter folder functionalities.
    """
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.analysis_cache = {}
        self.visualization_cache = {}
        
    # ============================================================================
    # CORE ANALYSIS FUNCTIONS (from codebase_analysis.py)
    # ============================================================================
    
    def get_codebase_overview(self) -> Dict[str, Any]:
        """Provides a high-level overview of the codebase structure."""
        if "codebase_overview" in self.analysis_cache:
            return self.analysis_cache["codebase_overview"]
            
        summary_str = get_codebase_summary(self.codebase)
        
        # Parse summary into structured data
        overview = {
            "summary": summary_str,
            "files_count": len(list(self.codebase.files)),
            "functions_count": len(list(self.codebase.functions)),
            "classes_count": len(list(self.codebase.classes)),
            "symbols_count": len(list(self.codebase.symbols)),
            "imports_count": len(list(self.codebase.imports)),
            "external_modules_count": len(list(self.codebase.external_modules)),
            "entrypoints": self._identify_entrypoints(),
            "dead_code_summary": self._get_dead_code_summary(),
            "complexity_overview": self._get_complexity_overview()
        }
        
        self.analysis_cache["codebase_overview"] = overview
        return overview

    def get_file_details(self, filepath: str) -> Dict[str, Any]:
        """Retrieves detailed information about a specific file."""
        cache_key = f"file_details_{filepath}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        try:
            file_obj = self.codebase.get_file(filepath)
            summary_str = get_file_summary(file_obj)
            
            details = {
                "filepath": filepath,
                "summary": summary_str,
                "functions": [self._get_function_summary(f) for f in file_obj.functions],
                "classes": [self._get_class_summary(c) for c in file_obj.classes],
                "imports": [self._get_import_summary(i) for i in file_obj.imports],
                "symbols": [self._get_symbol_summary(s) for s in getattr(file_obj, "symbols", [])],
                "metrics": {
                    "lines_of_code": len(file_obj.source.splitlines()) if hasattr(file_obj, "source") else 0,
                    "complexity_score": self._calculate_file_complexity(file_obj),
                    "maintainability_index": self._calculate_maintainability_index(file_obj),
                    "documentation_coverage": self._calculate_file_doc_coverage(file_obj)
                }
            }
            
            self.analysis_cache[cache_key] = details
            return details
        except ValueError:
            return {"filepath": filepath, "error": "File not found in codebase."}

    def get_function_details(self, function_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves comprehensive information about a function."""
        cache_key = f"function_details_{function_name}_{filepath}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        try:
            symbols = self.codebase.get_symbols(symbol_name=function_name)
            if not symbols:
                return {"function_name": function_name, "error": "Function not found."}

            target_symbol = self._resolve_symbol_with_filepath(symbols, filepath, Function)
            if not target_symbol:
                return {"function_name": function_name, "filepath": filepath, "error": "Function not found at specified path or is not a function."}

            summary_str = get_function_summary(target_symbol)
            reveal_info = reveal_symbol(
                codebase=self.codebase,
                symbol_name=function_name,
                filepath=filepath,
                max_depth=3,
                max_tokens=5000
            )

            details = {
                "function_name": function_name,
                "filepath": target_symbol.file.filepath if target_symbol.file else "N/A",
                "summary": summary_str,
                "parameters": self._get_function_parameters_details(target_symbol),
                "return_type": self._get_function_return_type_details(target_symbol),
                "local_variables": self._get_function_local_variables_details(target_symbol),
                "dependencies": [self._symbol_to_dict(s) for s in reveal_info.dependencies] if reveal_info.dependencies else [],
                "usages": [self._symbol_to_dict(s) for s in reveal_info.usages] if reveal_info.usages else [],
                "call_sites": [self._call_site_to_dict(cs) for cs in target_symbol.call_sites],
                "function_calls": [self._function_call_to_dict(fc) for fc in target_symbol.function_calls],
                "complexity_metrics": self._calculate_function_complexity_metrics(target_symbol),
                "quality_metrics": self._calculate_function_quality_metrics(target_symbol)
            }
            
            self.analysis_cache[cache_key] = details
            return details
        except Exception as e:
            return {"function_name": function_name, "error": f"Error retrieving function details: {e}"}

    def get_class_details(self, class_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves comprehensive information about a class."""
        cache_key = f"class_details_{class_name}_{filepath}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        try:
            symbols = self.codebase.get_symbols(symbol_name=class_name)
            if not symbols:
                return {"class_name": class_name, "error": "Class not found."}

            target_symbol = self._resolve_symbol_with_filepath(symbols, filepath, Class)
            if not target_symbol:
                return {"class_name": class_name, "filepath": filepath, "error": "Class not found at specified path or is not a class."}

            summary_str = get_class_summary(target_symbol)
            reveal_info = reveal_symbol(
                codebase=self.codebase,
                symbol_name=class_name,
                filepath=filepath,
                max_depth=3,
                max_tokens=5000
            )

            details = {
                "class_name": class_name,
                "filepath": target_symbol.file.filepath if target_symbol.file else "N/A",
                "summary": summary_str,
                "methods": [self._get_method_summary(m) for m in target_symbol.methods],
                "attributes": [self._get_attribute_summary(a) for a in target_symbol.attributes],
                "superclasses": [self._class_to_dict(sc) for sc in target_symbol.superclasses],
                "subclasses": [self._class_to_dict(sc) for sc in target_symbol.subclasses],
                "dependencies": [self._symbol_to_dict(s) for s in reveal_info.dependencies] if reveal_info.dependencies else [],
                "usages": [self._symbol_to_dict(s) for s in reveal_info.usages] if reveal_info.usages else [],
                "inheritance_metrics": self._calculate_inheritance_metrics(target_symbol),
                "complexity_metrics": self._calculate_class_complexity_metrics(target_symbol)
            }
            
            self.analysis_cache[cache_key] = details
            return details
        except Exception as e:
            return {"class_name": class_name, "error": f"Error retrieving class details: {e}"}

    def get_symbol_details(self, symbol_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves comprehensive information about any symbol."""
        cache_key = f"symbol_details_{symbol_name}_{filepath}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
            
        try:
            symbols = self.codebase.get_symbols(symbol_name=symbol_name)
            if not symbols:
                return {"symbol_name": symbol_name, "error": "Symbol not found."}

            target_symbol = self._resolve_symbol_with_filepath(symbols, filepath, Symbol)
            if not target_symbol:
                return {"symbol_name": symbol_name, "filepath": filepath, "error": "Symbol not found at specified path."}

            summary_str = get_symbol_summary(target_symbol)
            reveal_info = reveal_symbol(
                codebase=self.codebase,
                symbol_name=symbol_name,
                filepath=filepath,
                max_depth=3,
                max_tokens=5000
            )

            details = {
                "symbol_name": symbol_name,
                "symbol_type": type(target_symbol).__name__,
                "filepath": target_symbol.file.filepath if target_symbol.file else "N/A",
                "summary": summary_str,
                "dependencies": [self._symbol_to_dict(s) for s in reveal_info.dependencies] if reveal_info.dependencies else [],
                "usages": [self._symbol_to_dict(s) for s in reveal_info.usages] if reveal_info.usages else [],
                "context": self._get_symbol_context(target_symbol)
            }
            
            self.analysis_cache[cache_key] = details
            return details
        except Exception as e:
            return {"symbol_name": symbol_name, "error": f"Error retrieving symbol details: {e}"}

    # ============================================================================
    # VISUALIZATION FUNCTIONS (from blast_radius.py, call_trace.py, etc.)
    # ============================================================================
    
    def create_blast_radius_visualization(self, symbol_name: str, filepath: Optional[str] = None, max_depth: int = 5) -> Dict[str, Any]:
        """Creates blast radius visualization showing impact of changes."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=symbol_name)
            if not symbols:
                return {"error": f"Symbol '{symbol_name}' not found"}
            
            target_symbol = self._resolve_symbol_with_filepath(symbols, filepath, Symbol)
            if not target_symbol:
                return {"error": f"Symbol '{symbol_name}' not found at specified path"}

            # Create NetworkX graph for blast radius
            G = nx.DiGraph()
            
            # Use the blast radius logic
            self._build_blast_radius_graph(G, target_symbol, max_depth)
            
            return {
                "nodes": [{"id": str(node), "label": str(node), "type": type(node).__name__} for node in G.nodes()],
                "edges": [{"source": str(source), "target": str(target)} for source, target in G.edges()],
                "metadata": {
                    "target_symbol": symbol_name,
                    "visualization_type": "blast_radius",
                    "node_count": len(G.nodes()),
                    "edge_count": len(G.edges()),
                    "max_depth": max_depth
                }
            }
        except Exception as e:
            return {"error": f"Failed to create blast radius visualization: {e}"}

    def create_call_trace_visualization(self, function_name: str, filepath: Optional[str] = None, max_depth: int = 10) -> Dict[str, Any]:
        """Creates call trace visualization showing function call relationships."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=function_name)
            if not symbols:
                return {"error": f"Function '{function_name}' not found"}
            
            target_function = self._resolve_symbol_with_filepath(symbols, filepath, Function)
            if not target_function:
                return {"error": f"Function '{function_name}' not found at specified path or is not a function"}

            # Create NetworkX graph for call trace
            G = nx.DiGraph()
            
            # Use the call trace logic
            self._build_call_trace_graph(G, target_function, max_depth)
            
            return {
                "nodes": [{"id": str(node), "label": str(node), "type": type(node).__name__} for node in G.nodes()],
                "edges": [{"source": str(source), "target": str(target)} for source, target in G.edges()],
                "metadata": {
                    "target_function": function_name,
                    "visualization_type": "call_trace",
                    "node_count": len(G.nodes()),
                    "edge_count": len(G.edges()),
                    "max_depth": max_depth
                }
            }
        except Exception as e:
            return {"error": f"Failed to create call trace visualization: {e}"}

    def create_dependency_trace_visualization(self, symbol_name: str, filepath: Optional[str] = None, max_depth: int = 5) -> Dict[str, Any]:
        """Creates dependency trace visualization."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=symbol_name)
            if not symbols:
                return {"error": f"Symbol '{symbol_name}' not found"}
            
            target_symbol = self._resolve_symbol_with_filepath(symbols, filepath, Symbol)
            if not target_symbol:
                return {"error": f"Symbol '{symbol_name}' not found at specified path"}

            # Create NetworkX graph for dependency trace
            G = nx.DiGraph()
            
            # Use the dependency trace logic
            self._build_dependency_trace_graph(G, target_symbol, max_depth)
            
            return {
                "nodes": [{"id": str(node), "label": str(node), "type": type(node).__name__} for node in G.nodes()],
                "edges": [{"source": str(source), "target": str(target)} for source, target in G.edges()],
                "metadata": {
                    "target_symbol": symbol_name,
                    "visualization_type": "dependency_trace",
                    "node_count": len(G.nodes()),
                    "edge_count": len(G.edges()),
                    "max_depth": max_depth
                }
            }
        except Exception as e:
            return {"error": f"Failed to create dependency trace visualization: {e}"}

    def create_method_relationships_visualization(self, class_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Creates method relationships visualization within a class."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=class_name)
            if not symbols:
                return {"error": f"Class '{class_name}' not found"}
            
            target_class = self._resolve_symbol_with_filepath(symbols, filepath, Class)
            if not target_class:
                return {"error": f"Class '{class_name}' not found at specified path or is not a class"}

            # Create NetworkX graph for method relationships
            G = nx.DiGraph()
            
            # Use the method relationships logic
            self._build_method_relationships_graph(G, target_class)
            
            return {
                "nodes": [{"id": str(node), "label": str(node), "type": type(node).__name__} for node in G.nodes()],
                "edges": [{"source": str(source), "target": str(target)} for source, target in G.edges()],
                "metadata": {
                    "target_class": class_name,
                    "visualization_type": "method_relationships",
                    "node_count": len(G.nodes()),
                    "edge_count": len(G.edges())
                }
            }
        except Exception as e:
            return {"error": f"Failed to create method relationships visualization: {e}"}

    # ============================================================================
    # FILE AND DIRECTORY OPERATIONS (from view_file.py, list_directory.py)
    # ============================================================================
    
    def view_file_content(self, filepath: str, line_numbers: bool = True, start_line: Optional[int] = None, 
                         end_line: Optional[int] = None, max_lines: int = 500) -> ViewFileObservation:
        """Views file content with optional line numbers and pagination."""
        return view_file(
            codebase=self.codebase,
            filepath=filepath,
            line_numbers=line_numbers,
            start_line=start_line,
            end_line=end_line,
            max_lines=max_lines
        )

    def list_directory_contents(self, path: str = "./", depth: int = 2) -> ListDirectoryObservation:
        """Lists directory contents with specified depth."""
        return list_directory(codebase=self.codebase, path=path, depth=depth)

    def add_line_numbers_to_content(self, content: str) -> str:
        """Adds line numbers to content."""
        return add_line_numbers(content)

    # ============================================================================
    # SYMBOL REVELATION AND ANALYSIS (from reveal_symbol.py)
    # ============================================================================
    
    def reveal_symbol_relationships(self, symbol_name: str, filepath: Optional[str] = None, 
                                  max_depth: int = 2, max_tokens: Optional[int] = None,
                                  collect_dependencies: bool = True, collect_usages: bool = True) -> RevealSymbolObservation:
        """Reveals comprehensive symbol relationships."""
        return reveal_symbol(
            codebase=self.codebase,
            symbol_name=symbol_name,
            filepath=filepath,
            max_depth=max_depth,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages
        )

    def get_symbol_info_detailed(self, symbol: Symbol, max_tokens: Optional[int] = None) -> SymbolInfo:
        """Gets detailed information about a symbol."""
        return get_symbol_info(symbol, max_tokens)

    def get_extended_symbol_context(self, symbol: Symbol, degree: int, max_tokens: Optional[int] = None,
                                  collect_dependencies: bool = True, collect_usages: bool = True) -> Tuple[List[SymbolInfo], List[SymbolInfo], int]:
        """Gets extended context for a symbol."""
        return get_extended_context(
            symbol=symbol,
            degree=degree,
            max_tokens=max_tokens,
            collect_dependencies=collect_dependencies,
            collect_usages=collect_usages
        )

    # ============================================================================
    # DOCUMENTATION GENERATION (from document_functions.py, generate_docs_json.py, mdx_docs_generation.py)
    # ============================================================================
    
    def generate_docstrings_for_undocumented(self) -> Dict[str, Any]:
        """Generates docstrings for undocumented functions using AI."""
        try:
            logger.info("Generating docstrings for undocumented functions...")
            
            # Count undocumented functions before
            undocumented_before = len([f for f in self.codebase.functions if not getattr(f, 'docstring', None)])
            
            # Run the document functions process
            document_functions_run(self.codebase)
            
            # Count undocumented functions after
            undocumented_after = len([f for f in self.codebase.functions if not getattr(f, 'docstring', None)])
            
            return {
                "status": "success",
                "undocumented_before": undocumented_before,
                "undocumented_after": undocumented_after,
                "docstrings_generated": undocumented_before - undocumented_after,
                "message": "Docstring generation complete. Remember to commit changes."
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to generate docstrings: {e}"}

    def generate_structured_docs(self, head_commit: str = "latest", raise_on_missing_docstring: bool = False) -> Any:
        """Generates structured JSON documentation."""
        return generate_docs_json(self.codebase, head_commit, raise_on_missing_docstring)

    def generate_mdx_documentation(self, target_classes: Optional[List[str]] = None, output_dir: str = "docs") -> Dict[str, Any]:
        """Generates MDX documentation pages."""
        try:
            # Generate structured docs first
            structured_docs = self.generate_structured_docs()
            
            # Filter classes if specified
            if target_classes:
                classes_to_document = [cls_doc for cls_doc in structured_docs.classes if cls_doc.title in target_classes]
            else:
                classes_to_document = structured_docs.classes
            
            generated_files = []
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            for cls_doc in classes_to_document:
                try:
                    mdx_content = render_mdx_page_for_class(cls_doc)
                    mdx_route = get_mdx_route_for_class(cls_doc)
                    
                    # Create file path
                    file_path = output_path / f"{mdx_route}.mdx"
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write MDX content
                    file_path.write_text(mdx_content)
                    generated_files.append(str(file_path))
                    
                except Exception as e:
                    logger.warning(f"Failed to generate MDX for {cls_doc.title}: {e}")
            
            return {
                "status": "success",
                "generated_files": generated_files,
                "classes_documented": len(generated_files),
                "output_directory": output_dir
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to generate MDX documentation: {e}"}

    # ============================================================================
    # DEAD CODE ANALYSIS
    # ============================================================================
    
    def find_dead_code(self) -> Dict[str, Any]:
        """Identifies dead code using graph traversal from entry points."""
        if "dead_code" in self.analysis_cache:
            return self.analysis_cache["dead_code"]
            
        dead_code = {
            "total": 0,
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "variables": 0,
            "detailed_items": [],
            "recommendations": [],
            "entry_point_analysis": {}
        }

        # Find entry points
        entry_points = self._identify_entrypoints()
        
        # Perform graph traversal from entry points
        visited = set()
        
        def traverse_from_entry_point(symbol):
            if symbol in visited or isinstance(symbol, ExternalModule):
                return
            visited.add(symbol)

            # Traverse function calls
            if hasattr(symbol, "function_calls"):
                for call in symbol.function_calls:
                    if hasattr(call, "function_definition") and call.function_definition:
                        traverse_from_entry_point(call.function_definition)

            # Traverse usages
            if hasattr(symbol, "usages"):
                for usage in symbol.usages:
                    if hasattr(usage, "usage_symbol"):
                        traverse_from_entry_point(usage.usage_symbol)

            # Traverse dependencies
            if hasattr(symbol, "dependencies"):
                for dep in symbol.dependencies:
                    if hasattr(dep, "resolved_symbol") and dep.resolved_symbol:
                        traverse_from_entry_point(dep.resolved_symbol)
                    elif isinstance(dep, Symbol):
                        traverse_from_entry_point(dep)

        # Start traversal from all entry points
        for entry_point in entry_points["functions"] + entry_points["classes"]:
            if "symbol_obj" in entry_point:
                traverse_from_entry_point(entry_point["symbol_obj"])

        # Find dead functions
        for func in self.codebase.functions:
            if (func not in visited and 
                not self._is_test_function(func) and 
                not self._is_special_function(func)):
                
                dead_code["functions"] += 1
                dead_code["detailed_items"].append({
                    "type": "function",
                    "name": func.name,
                    "file": func.filepath,
                    "line": func.start_point.line + 1 if hasattr(func, 'start_point') else 0,
                    "reason": "No usage found from entry points",
                    "confidence": 0.8,
                    "complexity": self._calculate_function_complexity(func),
                    "loc": len(func.source.splitlines()) if hasattr(func, 'source') else 0
                })

        # Find dead classes
        for cls in self.codebase.classes:
            if cls not in visited and not self._is_test_class(cls):
                dead_code["classes"] += 1
                dead_code["detailed_items"].append({
                    "type": "class",
                    "name": cls.name,
                    "file": cls.filepath,
                    "line": cls.start_point.line + 1 if hasattr(cls, 'start_point') else 0,
                    "reason": "No usage found from entry points",
                    "confidence": 0.7,
                    "methods_count": len(cls.methods),
                    "inheritance_depth": len(cls.superclasses)
                })

        # Find dead imports
        for file_obj in self.codebase.files:
            for imp in file_obj.imports:
                if not hasattr(imp, 'usages') or len(imp.usages) == 0:
                    dead_code["imports"] += 1
                    dead_code["detailed_items"].append({
                        "type": "import",
                        "name": imp.name,
                        "file": file_obj.filepath,
                        "line": imp.start_point.line + 1 if hasattr(imp, 'start_point') else 0,
                        "reason": "Import not used in file",
                        "confidence": 0.9,
                        "module": getattr(imp, 'module', 'unknown')
                    })

        dead_code["total"] = (
            dead_code["functions"] + dead_code["classes"] + 
            dead_code["imports"] + dead_code["variables"]
        )

        # Generate recommendations
        dead_code["recommendations"] = [
            "Review dead code items before removal",
            "Check if functions are used in tests or configuration",
            "Consider if classes are used for inheritance only",
            "Verify imports are not used in string literals or dynamic imports",
            f"Found {len(entry_points['functions'])} entry point functions",
            f"Found {len(entry_points['classes'])} entry point classes"
        ]
        
        dead_code["entry_point_analysis"] = entry_points
        
        self.analysis_cache["dead_code"] = dead_code
        return dead_code

    # ============================================================================
    # BASH COMMAND EXECUTION (from bash.py)
    # ============================================================================
    
    def validate_bash_command(self, command: str) -> Tuple[bool, str]:
        """Validates if a bash command is safe to execute."""
        return validate_command(command)

    def run_bash_command(self, command: str, is_background: bool = False) -> RunBashCommandObservation:
        """Runs a bash command and returns the result."""
        return run_bash_command(command, is_background)

    # ============================================================================
    # REFLECTION AND PLANNING (from reflection.py)
    # ============================================================================
    
    def perform_reflection(self, context_summary: str, findings_so_far: str, 
                         current_challenges: str = "", reflection_focus: Optional[str] = None) -> ReflectionObservation:
        """Performs agent reflection for strategic planning."""
        return perform_reflection(
            context_summary=context_summary,
            findings_so_far=findings_so_far,
            current_challenges=current_challenges,
            reflection_focus=reflection_focus,
            codebase=self.codebase
        )

    def parse_reflection_response(self, response: str) -> List[ReflectionSection]:
        """Parses reflection response into structured sections."""
        return parse_reflection_response(response)

    # ============================================================================
    # WORKSPACE TOOLS (from tools.py)
    # ============================================================================
    
    def get_workspace_tools(self):
        """Gets all workspace tools initialized with the codebase."""
        return get_workspace_tools(self.codebase)

    # ============================================================================
    # CODEBASE UTILITIES (from current_code_codebase.py, codegen_sdk_codebase.py)
    # ============================================================================
    
    def get_current_code_codebase(self, config=None, secrets=None, subdirectories=None):
        """Gets codebase for currently running code."""
        return get_current_code_codebase(config, secrets, subdirectories)

    def get_codegen_sdk_codebase(self):
        """Gets the codegen SDK codebase."""
        return get_codegen_sdk_codebase()

    def import_all_sdk_modules(self):
        """Imports all codegen SDK modules."""
        import_all_codegen_sdk_modules()

    def get_documented_objects(self):
        """Gets all documented objects."""
        return get_documented_objects()

    # ============================================================================
    # ADVANCED ANALYSIS FUNCTIONS
    # ============================================================================
    
    def analyze_function_complexity(self, function_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes complexity metrics for a specific function."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=function_name)
            if not symbols:
                return {"function_name": function_name, "error": "Function not found."}
            
            target_function = self._resolve_symbol_with_filepath(symbols, filepath, Function)
            if not target_function:
                return {"function_name": function_name, "error": "Function not found at specified path or is not a function."}

            # Calculate various complexity metrics
            cyclomatic_complexity = self._calculate_cyclomatic_complexity(target_function)
            halstead_metrics = self._calculate_halstead_metrics(target_function)
            
            return {
                "function_name": function_name,
                "filepath": target_function.file.filepath if target_function.file else "N/A",
                "cyclomatic_complexity": cyclomatic_complexity,
                "complexity_rank": self._get_complexity_rank(cyclomatic_complexity),
                "halstead_metrics": halstead_metrics,
                "parameters_count": len(target_function.parameters),
                "return_statements_count": len(getattr(target_function, "return_statements", [])),
                "function_calls_count": len(target_function.function_calls),
                "lines_of_code": len(target_function.source.splitlines()) if hasattr(target_function, "source") else 0,
                "maintainability_score": self._calculate_function_maintainability(target_function)
            }
        except Exception as e:
            return {"function_name": function_name, "error": f"Error analyzing function complexity: {e}"}

    def analyze_class_structure(self, class_name: str, filepath: Optional[str] = None) -> Dict[str, Any]:
        """Analyzes structural metrics for a specific class."""
        try:
            symbols = self.codebase.get_symbols(symbol_name=class_name)
            if not symbols:
                return {"class_name": class_name, "error": "Class not found."}
            
            target_class = self._resolve_symbol_with_filepath(symbols, filepath, Class)
            if not target_class:
                return {"class_name": class_name, "error": "Class not found at specified path or is not a class."}

            # Analyze class structure
            methods_analysis = []
            for method in target_class.methods:
                methods_analysis.append({
                    "name": method.name,
                    "complexity": self._calculate_cyclomatic_complexity(method),
                    "parameters_count": len(method.parameters),
                    "is_public": not method.name.startswith("_"),
                    "is_property": self._is_property_method(method),
                    "lines_of_code": len(method.source.splitlines()) if hasattr(method, "source") else 0,
                    "has_docstring": bool(getattr(method, "docstring", None))
                })

            attributes_analysis = []
            for attr in target_class.attributes:
                attributes_analysis.append({
                    "name": attr.name,
                    "is_public": not attr.name.startswith("_"),
                    "has_type_annotation": hasattr(attr, "type") and attr.type is not None,
                    "usages_count": len(attr.usages) if hasattr(attr, "usages") else 0
                })

            return {
                "class_name": class_name,
                "filepath": target_class.file.filepath if target_class.file else "N/A",
                "methods_count": len(target_class.methods),
                "attributes_count": len(target_class.attributes),
                "inheritance_depth": len(target_class.superclasses),
                "subclasses_count": len(target_class.subclasses),
                "methods_analysis": methods_analysis,
                "attributes_analysis": attributes_analysis,
                "complexity_score": sum(m["complexity"] for m in methods_analysis) / max(1, len(methods_analysis)),
                "public_methods_ratio": len([m for m in methods_analysis if m["is_public"]]) / max(1, len(methods_analysis)),
                "documented_methods_ratio": len([m for m in methods_analysis if m["has_docstring"]]) / max(1, len(methods_analysis)),
                "cohesion_metrics": self._calculate_class_cohesion(target_class)
            }
        except Exception as e:
            return {"class_name": class_name, "error": f"Error analyzing class structure: {e}"}

    def analyze_import_relationships(self, filepath: str) -> Dict[str, Any]:
        """Analyzes import relationships for a specific file."""
        try:
            file_obj = self.codebase.get_file(filepath)
            
            imports_analysis = []
            for imp in file_obj.imports:
                imports_analysis.append({
                    "name": imp.name,
                    "module": getattr(imp, "module", "unknown"),
                    "is_external": isinstance(getattr(imp, "resolved_symbol", None), ExternalModule),
                    "usages_count": len(imp.usages) if hasattr(imp, "usages") else 0,
                    "is_unused": len(imp.usages) == 0 if hasattr(imp, "usages") else True,
                    "line": imp.start_point.line + 1 if hasattr(imp, "start_point") else 0,
                    "resolved": bool(getattr(imp, "resolved_symbol", None))
                })

            inbound_imports = []
            for symbol in getattr(file_obj, "symbols", []):
                for usage in symbol.usages:
                    if hasattr(usage, "file") and usage.file != file_obj:
                        inbound_imports.append({
                            "symbol": symbol.name,
                            "imported_by": usage.file.filepath,
                            "usage_type": type(usage).__name__
                        })

            return {
                "filepath": filepath,
                "imports_count": len(file_obj.imports),
                "external_imports_count": len([i for i in imports_analysis if i["is_external"]]),
                "unused_imports_count": len([i for i in imports_analysis if i["is_unused"]]),
                "unresolved_imports_count": len([i for i in imports_analysis if not i["resolved"]]),
                "imports_analysis": imports_analysis,
                "inbound_imports": inbound_imports,
                "inbound_imports_count": len(inbound_imports),
                "circular_dependencies": self._detect_circular_imports(file_obj)
            }
        except ValueError:
            return {"filepath": filepath, "error": "File not found in codebase."}
        except Exception as e:
            return {"filepath": filepath, "error": f"Error analyzing import relationships: {e}"}

    # ============================================================================
    # HELPER FUNCTIONS
    # ============================================================================
    
    def _resolve_symbol_with_filepath(self, symbols: List[Symbol], filepath: Optional[str], expected_type: type) -> Optional[Symbol]:
        """Helper to resolve an ambiguous symbol by filepath and type."""
        if filepath:
            for s in symbols:
                if s.file and s.file.filepath == filepath and isinstance(s, expected_type):
                    return s
        elif symbols and isinstance(symbols[0], expected_type):
            return symbols[0]
        return None

    def _identify_entrypoints(self) -> Dict[str, List[Dict[str, Any]]]:
        """Identifies entry points in the codebase."""
        entrypoints = {
            "functions": [],
            "classes": [],
            "files": []
        }
        
        # Function entry points
        for func in self.codebase.functions:
            if self._is_entrypoint_function(func):
                entrypoints["functions"].append({
                    "name": func.name,
                    "file": func.filepath,
                    "type": "function",
                    "score": self._calculate_entrypoint_score(func),
                    "symbol_obj": func
                })
        
        # Class entry points
        for cls in self.codebase.classes:
            if self._is_entrypoint_class(cls):
                entrypoints["classes"].append({
                    "name": cls.name,
                    "file": cls.filepath,
                    "type": "class",
                    "score": self._calculate_class_entrypoint_score(cls),
                    "symbol_obj": cls
                })
        
        # File entry points
        for file_obj in self.codebase.files:
            if self._is_entrypoint_file(file_obj):
                entrypoints["files"].append({
                    "name": file_obj.name,
                    "path": file_obj.filepath,
                    "type": "file"
                })
        
        return entrypoints

    def _get_dead_code_summary(self) -> Dict[str, Any]:
        """Gets a summary of dead code analysis."""
        dead_code = self.find_dead_code()
        return {
            "total_dead_items": dead_code["total"],
            "dead_functions": dead_code["functions"],
            "dead_classes": dead_code["classes"],
            "dead_imports": dead_code["imports"]
        }

    def _get_complexity_overview(self) -> Dict[str, Any]:
        """Gets complexity overview of the codebase."""
        complexities = [self._calculate_function_complexity(f) for f in self.codebase.functions]
        if not complexities:
            return {"average": 0, "max": 0, "distribution": {}}
            
        return {
            "average_complexity": sum(complexities) / len(complexities),
            "max_complexity": max(complexities),
            "min_complexity": min(complexities),
            "distribution": {
                "low": len([c for c in complexities if c <= 5]),
                "medium": len([c for c in complexities if 5 < c <= 10]),
                "high": len([c for c in complexities if c > 10])
            }
        }

    def _get_function_parameters_details(self, func: Function) -> List[Dict[str, Any]]:
        """Extracts detailed information about function parameters."""
        params_details = []
        for param in func.parameters:
            param_type_source = getattr(param.type, 'source', 'Any') if hasattr(param, 'type') and param.type else 'Any'
            resolved_types = []
            
            if hasattr(param, 'type') and param.type and hasattr(param.type, 'resolved_value') and param.type.resolved_value:
                resolved_symbols = param.type.resolved_value
                if not isinstance(resolved_symbols, list):
                    resolved_symbols = [resolved_symbols]
                    
                for res_sym in resolved_symbols:
                    if isinstance(res_sym, Symbol):
                        resolved_types.append({
                            "name": res_sym.name,
                            "type": type(res_sym).__name__,
                            "filepath": res_sym.filepath if hasattr(res_sym, 'filepath') else None
                        })
                    elif isinstance(res_sym, ExternalModule):
                        resolved_types.append({
                            "name": res_sym.name,
                            "type": "ExternalModule"
                        })
                    else:
                        resolved_types.append({"name": str(res_sym), "type": "Unknown"})

            params_details.append({
                "name": param.name,
                "type_annotation": param_type_source,
                "resolved_types": resolved_types,
                "has_default": getattr(param, "has_default", False),
                "is_keyword_only": getattr(param, "is_keyword_only", False),
                "is_positional_only": getattr(param, "is_positional_only", False),
                "is_var_arg": getattr(param, "is_var_arg", False),
                "is_var_kw": getattr(param, "is_var_kw", False)
            })
        return params_details

    def _get_function_return_type_details(self, func: Function) -> Dict[str, Any]:
        """Extracts detailed information about function return type."""
        return_type_source = getattr(func.return_type, 'source', 'Any') if hasattr(func, 'return_type') and func.return_type else 'Any'
        resolved_types = []
        
        if hasattr(func, 'return_type') and func.return_type and hasattr(func.return_type, 'resolved_value') and func.return_type.resolved_value:
            resolved_symbols = func.return_type.resolved_value
            if not isinstance(resolved_symbols, list):
                resolved_symbols = [resolved_symbols]
                
            for res_sym in resolved_symbols:
                if isinstance(res_sym, Symbol):
                    resolved_types.append({
                        "name": res_sym.name,
                        "type": type(res_sym).__name__,
                        "filepath": res_sym.filepath if hasattr(res_sym, 'filepath') else None
                    })
                elif isinstance(res_sym, ExternalModule):
                    resolved_types.append({
                        "name": res_sym.name,
                        "type": "ExternalModule"
                    })
                else:
                    resolved_types.append({"name": str(res_sym), "type": "Unknown"})
                    
        return {
            "type_annotation": return_type_source,
            "resolved_types": resolved_types
        }

    def _get_function_local_variables_details(self, func: Function) -> List[Dict[str, Any]]:
        """Extracts details about local variables defined within a function."""
        local_vars = []
        if hasattr(func, 'code_block') and hasattr(func.code_block, 'local_var_assignments'):
            for assignment in func.code_block.local_var_assignments:
                var_type_source = getattr(assignment.type, 'source', 'Any') if hasattr(assignment, 'type') and assignment.type else 'Any'
                local_vars.append({
                    "name": assignment.name,
                    "type_annotation": var_type_source,
                    "line": assignment.start_point.line + 1 if hasattr(assignment, 'start_point') else None,
                    "value_snippet": assignment.source if hasattr(assignment, 'source') else None
                })
        return local_vars

    def _symbol_to_dict(self, symbol_info: SymbolInfo) -> Dict[str, Any]:
        """Converts SymbolInfo to dictionary."""
        return {
            "name": symbol_info.name,
            "filepath": symbol_info.filepath,
            "source": symbol_info.source
        }

    def _call_site_to_dict(self, call_site) -> Dict[str, Any]:
        """Converts call site to dictionary."""
        return {
            "name": getattr(call_site, "name", "unknown"),
            "file": getattr(call_site, "file", {}).get("filepath", "unknown") if hasattr(call_site, "file") else "unknown",
            "line": getattr(call_site, "start_point", {}).get("line", 0) if hasattr(call_site, "start_point") else 0
        }

    def _function_call_to_dict(self, function_call) -> Dict[str, Any]:
        """Converts function call to dictionary."""
        return {
            "name": getattr(function_call, "name", "unknown"),
            "args_count": len(getattr(function_call, "args", [])),
            "line": getattr(function_call, "start_point", {}).get("line", 0) if hasattr(function_call, "start_point") else 0
        }

    def _class_to_dict(self, cls: Class) -> Dict[str, Any]:
        """Converts class to dictionary."""
        return {
            "name": cls.name,
            "filepath": cls.filepath,
            "methods_count": len(cls.methods),
            "attributes_count": len(cls.attributes)
        }

    # ============================================================================
    # COMPLEXITY AND QUALITY METRICS
    # ============================================================================
    
    def _calculate_function_complexity(self, func: Function) -> int:
        """Calculates cyclomatic complexity for a function."""
        return self._calculate_cyclomatic_complexity(func)

    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """Calculate cyclomatic complexity for a function."""
        try:
            complexity = 1  # Base complexity

            if hasattr(func, "source") and func.source:
                source = func.source.lower()
                # Count decision points
                complexity += source.count("if ")
                complexity += source.count("elif ")
                complexity += source.count("for ")
                complexity += source.count("while ")
                complexity += source.count("except ")
                complexity += source.count("and ")
                complexity += source.count("or ")
                complexity += source.count("try:")
                complexity += source.count("with ")

            return complexity
        except Exception:
            return 1

    def _calculate_halstead_metrics(self, func: Function) -> Dict[str, float]:
        """Calculate Halstead metrics for a function."""
        try:
            if not hasattr(func, "source") or not func.source:
                return {"volume": 0.0, "difficulty": 0.0, "effort": 0.0}

            operators, operands = get_operators_and_operands(func)
            volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
            
            N = N1 + N2  # Program length
            n = n1 + n2  # Program vocabulary

            if n > 0 and n2 > 0:
                difficulty = (n1 / 2) * (N2 / n2)
                effort = difficulty * volume
            else:
                difficulty = effort = 0

            return {
                "volume": volume,
                "difficulty": difficulty,
                "effort": effort,
                "length": N,
                "vocabulary": n,
                "unique_operators": n1,
                "unique_operands": n2
            }
        except Exception:
            return {"volume": 0.0, "difficulty": 0.0, "effort": 0.0}

    def _get_complexity_rank(self, complexity: int) -> str:
        """Get complexity rank based on cyclomatic complexity."""
        if complexity <= 5:
            return "A"
        elif complexity <= 10:
            return "B"
        elif complexity <= 20:
            return "C"
        elif complexity <= 30:
            return "D"
        elif complexity <= 40:
            return "E"
        else:
            return "F"

    def _calculate_function_complexity_metrics(self, func: Function) -> Dict[str, Any]:
        """Calculate comprehensive complexity metrics for a function."""
        return {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(func),
            "halstead_metrics": self._calculate_halstead_metrics(func),
            "lines_of_code": len(func.source.splitlines()) if hasattr(func, "source") else 0,
            "parameters_count": len(func.parameters),
            "nesting_depth": self._calculate_nesting_depth(func)
        }

    def _calculate_function_quality_metrics(self, func: Function) -> Dict[str, Any]:
        """Calculate quality metrics for a function."""
        return {
            "has_docstring": bool(getattr(func, "docstring", None)),
            "has_return_type": bool(getattr(func, "return_type", None)),
            "typed_parameters_ratio": self._calculate_typed_parameters_ratio(func),
            "maintainability_score": self._calculate_function_maintainability(func)
        }

    def _calculate_class_complexity_metrics(self, cls: Class) -> Dict[str, Any]:
        """Calculate complexity metrics for a class."""
        method_complexities = [self._calculate_cyclomatic_complexity(m) for m in cls.methods]
        return {
            "average_method_complexity": sum(method_complexities) / max(1, len(method_complexities)),
            "max_method_complexity": max(method_complexities) if method_complexities else 0,
            "methods_count": len(cls.methods),
            "attributes_count": len(cls.attributes),
            "inheritance_depth": len(cls.superclasses),
            "weighted_methods_per_class": sum(method_complexities)
        }

    def _calculate_inheritance_metrics(self, cls: Class) -> Dict[str, Any]:
        """Calculate inheritance-related metrics."""
        return {
            "depth_of_inheritance": len(cls.superclasses),
            "number_of_children": len(cls.subclasses),
            "coupling_between_objects": len([dep for dep in cls.dependencies if isinstance(dep, Class)]),
            "response_for_class": len(cls.methods) + len([m for sc in cls.superclasses for m in sc.methods])
        }

    def _calculate_class_cohesion(self, cls: Class) -> Dict[str, Any]:
        """Calculate class cohesion metrics."""
        # Simplified LCOM (Lack of Cohesion of Methods) calculation
        methods = list(cls.methods)
        attributes = list(cls.attributes)
        
        if not methods or not attributes:
            return {"lcom": 0, "cohesion_score": 1.0}
        
        # Count method pairs that don't share attributes
        non_cohesive_pairs = 0
        total_pairs = 0
        
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                total_pairs += 1
                # Check if methods share any attributes
                method1_attrs = set(getattr(method1, "variable_usages", []))
                method2_attrs = set(getattr(method2, "variable_usages", []))
                
                if not method1_attrs.intersection(method2_attrs):
                    non_cohesive_pairs += 1
        
        lcom = non_cohesive_pairs / max(1, total_pairs)
        cohesion_score = 1.0 - lcom
        
        return {
            "lcom": lcom,
            "cohesion_score": cohesion_score,
            "methods_count": len(methods),
            "attributes_count": len(attributes)
        }

    # ============================================================================
    # GRAPH BUILDING FUNCTIONS
    # ============================================================================
    
    def _build_blast_radius_graph(self, graph: nx.DiGraph, symbol: Symbol, max_depth: int, depth: int = 0):
        """Build blast radius graph recursively."""
        if depth >= max_depth or symbol in graph.nodes:
            return

        graph.add_node(symbol, name=symbol.name, type=type(symbol).__name__, depth=depth)

        # Add all usages (things that would be affected by changes)
        for usage in symbol.usages:
            if hasattr(usage, "usage_symbol"):
                affected_symbol = usage.usage_symbol
                if affected_symbol not in graph.nodes:
                    graph.add_node(affected_symbol, name=affected_symbol.name, 
                                 type=type(affected_symbol).__name__, depth=depth + 1)
                graph.add_edge(symbol, affected_symbol, relationship="impacts")
                
                if depth + 1 < max_depth:
                    self._build_blast_radius_graph(graph, affected_symbol, max_depth, depth + 1)

    def _build_call_trace_graph(self, graph: nx.DiGraph, func: Function, max_depth: int, depth: int = 0):
        """Build call trace graph recursively."""
        if depth >= max_depth or func in graph.nodes:
            return

        graph.add_node(func, name=func.name, type="function", depth=depth)

        # Add function calls
        for call in func.function_calls:
            if hasattr(call, "function_definition") and call.function_definition:
                called_func = call.function_definition
                if not isinstance(called_func, ExternalModule) and called_func not in graph.nodes:
                    graph.add_node(called_func, name=called_func.name, type="function", depth=depth + 1)
                    graph.add_edge(func, called_func, relationship="calls")
                    
                    if depth + 1 < max_depth:
                        self._build_call_trace_graph(graph, called_func, max_depth, depth + 1)

    def _build_dependency_trace_graph(self, graph: nx.DiGraph, symbol: Symbol, max_depth: int, depth: int = 0):
        """Build dependency trace graph recursively."""
        if depth >= max_depth or symbol in graph.nodes:
            return

        graph.add_node(symbol, name=symbol.name, type=type(symbol).__name__, depth=depth)

        # Add dependencies
        for dep in symbol.dependencies:
            if isinstance(dep, Import):
                dep = hop_through_imports(dep)
            
            if isinstance(dep, Symbol) and not isinstance(dep, ExternalModule) and dep not in graph.nodes:
                graph.add_node(dep, name=dep.name, type=type(dep).__name__, depth=depth + 1)
                graph.add_edge(symbol, dep, relationship="depends_on")
                
                if depth + 1 < max_depth:
                    self._build_dependency_trace_graph(graph, dep, max_depth, depth + 1)

    def _build_method_relationships_graph(self, graph: nx.DiGraph, cls: Class):
        """Build method relationships graph for a class."""
        graph.add_node(cls, name=cls.name, type="class")

        # Add all methods
        for method in cls.methods:
            graph.add_node(method, name=f"{cls.name}.{method.name}", type="method")
            graph.add_edge(cls, method, relationship="contains")
            
            # Add method call relationships
            for call in method.function_calls:
                if hasattr(call, "function_definition") and call.function_definition:
                    called_func = call.function_definition
                    if called_func in cls.methods:  # Internal method call
                        graph.add_edge(method, called_func, relationship="calls")

    # ============================================================================
    # UTILITY FUNCTIONS
    # ============================================================================
    
    def _is_entrypoint_function(self, func: Function) -> bool:
        """Check if a function is an entrypoint."""
        entrypoint_patterns = ["main", "run", "start", "execute", "cli", "app", "serve"]
        return (
            any(pattern in func.name.lower() for pattern in entrypoint_patterns) or
            func.name == "__main__" or
            self._has_entrypoint_decorators(func) or
            self._is_called_from_main_block(func)
        )

    def _is_entrypoint_class(self, cls: Class) -> bool:
        """Check if a class is an entrypoint."""
        entrypoint_patterns = ["app", "application", "server", "client", "main", "runner", "service"]
        return (
            any(pattern in cls.name.lower() for pattern in entrypoint_patterns) or
            self._has_framework_inheritance(cls) or
            self._has_singleton_pattern(cls)
        )

    def _is_entrypoint_file(self, file_obj: SourceFile) -> bool:
        """Check if a file is an entrypoint."""
        entrypoint_patterns = ["main.py", "__main__.py", "app.py", "server.py", "run.py", "cli.py"]
        return any(pattern in file_obj.filepath for pattern in entrypoint_patterns)

    def _is_test_function(self, func: Function) -> bool:
        """Check if a function is a test function."""
        return (
            func.name.startswith("test_") or 
            "test" in func.filepath or
            self._has_test_decorators(func)
        )

    def _is_test_class(self, cls: Class) -> bool:
        """Check if a class is a test class."""
        return cls.name.startswith("Test") or "test" in cls.filepath

    def _is_special_function(self, func: Function) -> bool:
        """Check if a function is special (shouldn't be considered dead code)."""
        special_patterns = ["__init__", "__str__", "__repr__", "__call__", "setUp", "tearDown"]
        return any(pattern in func.name for pattern in special_patterns)

    def _calculate_entrypoint_score(self, func: Function) -> float:
        """Calculate entrypoint score for a function."""
        score = 1.0  # Base score
        
        # Name-based scoring
        entrypoint_names = ["main", "run", "start", "execute", "app", "serve", "launch"]
        if any(name in func.name.lower() for name in entrypoint_names):
            score += 2.0
        
        # Usage-based scoring
        if len(func.usages) == 0:
            score += 1.0
        elif len(func.usages) < 3:
            score += 0.5
        
        # Complexity-based scoring
        complexity = self._calculate_cyclomatic_complexity(func)
        if 5 <= complexity <= 15:
            score += 1.0
        elif complexity > 15:
            score += 0.5
        
        # Call-based scoring
        if len(func.function_calls) > 5:
            score += 1.0
        elif len(func.function_calls) > 2:
            score += 0.5
        
        return score

    def _calculate_class_entrypoint_score(self, cls: Class) -> float:
        """Calculate entrypoint score for a class."""
        score = 1.0  # Base score
        
        # Name-based scoring
        entrypoint_names = ["app", "application", "server", "client", "main", "service"]
        if any(name in cls.name.lower() for name in entrypoint_names):
            score += 2.0
        
        # Size-based scoring
        if len(cls.methods) > 10:
            score += 1.0
        
        # Inheritance-based scoring
        if len(cls.superclasses) > 0:
            for superclass in cls.superclasses:
                if any(pattern in superclass.name.lower() for pattern in ["application", "service", "handler"]):
                    score += 1.5
        
        return score

    def _has_entrypoint_decorators(self, func: Function) -> bool:
        """Check if function has entrypoint decorators."""
        if not hasattr(func, "decorators"):
            return False
        
        for decorator in func.decorators:
            decorator_source = getattr(decorator, "source", "")
            if any(pattern in decorator_source.lower() for pattern in ["@app.", "@click.", "@typer.", "@fastapi."]):
                return True
        return False

    def _has_framework_inheritance(self, cls: Class) -> bool:
        """Check if class inherits from framework classes."""
        for superclass in cls.superclasses:
            if any(pattern in superclass.name.lower() for pattern in ["application", "app", "service", "handler"]):
                return True
        return False

    def _has_singleton_pattern(self, cls: Class) -> bool:
        """Check if class implements singleton pattern."""
        return any("instance" in method.name.lower() or "singleton" in method.name.lower() for method in cls.methods)

    def _has_test_decorators(self, func: Function) -> bool:
        """Check if function has test decorators."""
        if not hasattr(func, "decorators"):
            return False
        
        for decorator in func.decorators:
            decorator_source = getattr(decorator, "source", "")
            if any(pattern in decorator_source.lower() for pattern in ["@pytest.", "@unittest.", "@test"]):
                return True
        return False

    def _is_called_from_main_block(self, func: Function) -> bool:
        """Check if function is called from if __name__ == '__main__' block."""
        for usage in func.usages:
            if hasattr(usage, "parent_statement"):
                parent = usage.parent_statement
                if hasattr(parent, "condition") and "__name__" in getattr(parent.condition, "source", ""):
                    return True
        return False

    def _is_property_method(self, method: Function) -> bool:
        """Check if method is a property."""
        if not hasattr(method, "decorators"):
            return False
        
        for decorator in method.decorators:
            if "@property" in getattr(decorator, "source", ""):
                return True
        return False

    def _calculate_nesting_depth(self, func: Function) -> int:
        """Calculate maximum nesting depth in a function."""
        if not hasattr(func, "source") or not func.source:
            return 0
        
        lines = func.source.split('\n')
        max_depth = 0
        current_depth = 0
        
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['if ', 'for ', 'while ', 'try:', 'with ']):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif stripped in ['else:', 'elif ', 'except:', 'finally:']:
                continue
            elif stripped == '' or stripped.startswith('#'):
                continue
            else:
                # Check for dedentation
                indent_level = len(line) - len(line.lstrip())
                if indent_level == 0:
                    current_depth = 0
        
        return max_depth

    def _calculate_typed_parameters_ratio(self, func: Function) -> float:
        """Calculate ratio of typed parameters."""
        if not func.parameters:
            return 1.0
        
        typed_count = sum(1 for p in func.parameters if hasattr(p, 'type') and p.type)
        return typed_count / len(func.parameters)

    def _calculate_function_maintainability(self, func: Function) -> float:
        """Calculate function maintainability score."""
        complexity = self._calculate_cyclomatic_complexity(func)
        loc = len(func.source.splitlines()) if hasattr(func, "source") else 0
        has_docstring = bool(getattr(func, "docstring", None))
        
        # Simplified maintainability calculation
        base_score = 100
        complexity_penalty = complexity * 2
        loc_penalty = max(0, (loc - 20) * 0.5)
        doc_bonus = 10 if has_docstring else 0
        
        return max(0, base_score - complexity_penalty - loc_penalty + doc_bonus)

    def _calculate_file_complexity(self, file_obj: SourceFile) -> float:
        """Calculate complexity score for a file."""
        try:
            if not hasattr(file_obj, "functions"):
                return 0.0

            function_complexities = [self._calculate_cyclomatic_complexity(func) for func in file_obj.functions]
            return sum(function_complexities) / max(1, len(function_complexities))
        except Exception:
            return 0.0

    def _calculate_maintainability_index(self, file_obj: SourceFile) -> float:
        """Calculate maintainability index for a file."""
        try:
            if not hasattr(file_obj, "source"):
                return 0.0

            loc = len(file_obj.source.splitlines())
            complexity = self._calculate_file_complexity(file_obj)

            if loc > 0:
                return max(0, (171 - 5.2 * math.log(loc) - 0.23 * complexity - 16.2 * math.log(loc)) * 100 / 171)
            return 0.0
        except Exception:
            return 0.0

    def _calculate_file_doc_coverage(self, file_obj: SourceFile) -> float:
        """Calculate documentation coverage for a file."""
        total_symbols = len(file_obj.functions) + len(file_obj.classes)
        if total_symbols == 0:
            return 1.0
        
        documented = sum(1 for f in file_obj.functions if getattr(f, 'docstring', None))
        documented += sum(1 for c in file_obj.classes if getattr(c, 'docstring', None))
        
        return documented / total_symbols

    def _detect_circular_imports(self, file_obj: SourceFile) -> List[List[str]]:
        """Detect circular import dependencies for a file."""
        import_graph = nx.DiGraph()
        
        # Build import graph starting from this file
        def add_file_imports(current_file, visited=None):
            if visited is None:
                visited = set()
            if current_file.filepath in visited:
                return
            visited.add(current_file.filepath)
            
            import_graph.add_node(current_file.filepath)
            for imp in current_file.imports:
                if hasattr(imp, "from_file") and imp.from_file:
                    import_graph.add_edge(current_file.filepath, imp.from_file.filepath)
                    add_file_imports(imp.from_file, visited)
        
        add_file_imports(file_obj)
        
        # Find cycles involving this file
        cycles = list(nx.simple_cycles(import_graph))
        return [cycle for cycle in cycles if file_obj.filepath in cycle]

    # ============================================================================
    # SUMMARY HELPER FUNCTIONS
    # ============================================================================
    
    def _get_function_summary(self, func: Function) -> Dict[str, Any]:
        """Get summary information for a function."""
        return {
            "name": func.name,
            "line": func.start_point.line + 1 if hasattr(func, 'start_point') else 0,
            "complexity": self._calculate_cyclomatic_complexity(func),
            "parameters_count": len(func.parameters),
            "has_docstring": bool(getattr(func, "docstring", None)),
            "is_async": getattr(func, "is_async", False),
            "usages_count": len(func.usages)
        }

    def _get_class_summary(self, cls: Class) -> Dict[str, Any]:
        """Get summary information for a class."""
        return {
            "name": cls.name,
            "line": cls.start_point.line + 1 if hasattr(cls, 'start_point') else 0,
            "methods_count": len(cls.methods),
            "attributes_count": len(cls.attributes),
            "inheritance_depth": len(cls.superclasses),
            "has_docstring": bool(getattr(cls, "docstring", None)),
            "usages_count": len(cls.usages)
        }

    def _get_import_summary(self, imp: Import) -> Dict[str, Any]:
        """Get summary information for an import."""
        return {
            "name": imp.name,
            "module": getattr(imp, "module", "unknown"),
            "line": imp.start_point.line + 1 if hasattr(imp, 'start_point') else 0,
            "is_external": isinstance(getattr(imp, "resolved_symbol", None), ExternalModule),
            "usages_count": len(imp.usages) if hasattr(imp, "usages") else 0,
            "is_resolved": bool(getattr(imp, "resolved_symbol", None))
        }

    def _get_symbol_summary(self, symbol: Symbol) -> Dict[str, Any]:
        """Get summary information for a symbol."""
        return {
            "name": symbol.name,
            "type": type(symbol).__name__,
            "line": symbol.start_point.line + 1 if hasattr(symbol, 'start_point') else 0,
            "usages_count": len(symbol.usages),
            "dependencies_count": len(symbol.dependencies)
        }

    def _get_method_summary(self, method: Function) -> Dict[str, Any]:
        """Get summary information for a method."""
        return {
            "name": method.name,
            "line": method.start_point.line + 1 if hasattr(method, 'start_point') else 0,
            "complexity": self._calculate_cyclomatic_complexity(method),
            "parameters_count": len(method.parameters),
            "is_public": not method.name.startswith("_"),
            "is_property": self._is_property_method(method),
            "has_docstring": bool(getattr(method, "docstring", None))
        }

    def _get_attribute_summary(self, attr) -> Dict[str, Any]:
        """Get summary information for an attribute."""
        return {
            "name": attr.name,
            "line": attr.start_point.line + 1 if hasattr(attr, 'start_point') else 0,
            "is_public": not attr.name.startswith("_"),
            "has_type_annotation": hasattr(attr, "type") and attr.type is not None,
            "usages_count": len(attr.usages) if hasattr(attr, "usages") else 0
        }

    def _get_symbol_context(self, symbol: Symbol) -> Dict[str, Any]:
        """Get contextual information about a symbol."""
        return {
            "parent_class": symbol.parent_class.name if getattr(symbol, "parent_class", None) else None,
            "parent_function": symbol.parent_function.name if getattr(symbol, "parent_function", None) else None,
            "file": symbol.file.filepath if symbol.file else None,
            "is_public": not symbol.name.startswith("_"),
            "symbol_type": getattr(symbol, "symbol_type", type(symbol).__name__)
        }