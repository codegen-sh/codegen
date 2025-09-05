#!/usr/bin/env python3
"""
Comprehensive test script for Codegen with SDK integration.

This script tests both:
1. Codegen agent functionality 
2. Graph-sitter SDK contexts and capabilities

Run this after `pip install -e .` to validate the complete integration.
"""

import sys
import traceback
from pathlib import Path
from typing import Dict, Any

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_test(name: str, success: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {name}")
    if details:
        print(f"    {details}")

def test_basic_imports() -> Dict[str, Any]:
    """Test basic package imports"""
    print_section("BASIC IMPORTS TEST")
    results = {}
    
    # Test codegen main package
    try:
        import codegen
        print_test("Codegen main package", True, f"Version: {getattr(codegen, '__version__', 'unknown')}")
        results['codegen_main'] = True
    except Exception as e:
        print_test("Codegen main package", False, str(e))
        results['codegen_main'] = False
    
    # Test codegen.exports
    try:
        from codegen.exports import Agent, Codebase, Function, ProgrammingLanguage
        print_test("Codegen exports", True, f"Agent: {Agent}, Codebase: {Codebase}")
        results['codegen_exports'] = True
    except Exception as e:
        print_test("Codegen exports", False, str(e))
        results['codegen_exports'] = False
    
    # Test SDK package
    try:
        import codegen.sdk
        print_test("SDK package", True, f"Version: {getattr(codegen.sdk, '__version__', 'unknown')}")
        results['sdk_main'] = True
    except Exception as e:
        print_test("SDK package", False, str(e))
        results['sdk_main'] = False
    
    # Test SDK core components
    try:
        from codegen.sdk.core.codebase import Codebase as SDKCodebase
        from codegen.sdk.core.function import Function as SDKFunction
        print_test("SDK core components", True, f"SDKCodebase: {SDKCodebase}")
        results['sdk_core'] = True
    except Exception as e:
        print_test("SDK core components", False, str(e))
        results['sdk_core'] = False
    
    return results

def test_codegen_agent_functionality() -> Dict[str, Any]:
    """Test codegen agent functionality"""
    print_section("CODEGEN AGENT FUNCTIONALITY")
    results = {}
    
    # Test Agent class
    try:
        from codegen.agents.agent import Agent
        agent = Agent()
        print_test("Agent instantiation", True, f"Agent type: {type(agent)}")
        results['agent_creation'] = True
    except Exception as e:
        print_test("Agent instantiation", False, str(e))
        results['agent_creation'] = False
    
    # Test programming language enum
    try:
        from codegen.shared.enums.programming_language import ProgrammingLanguage
        python_lang = ProgrammingLanguage.PYTHON
        print_test("Programming language enum", True, f"Python: {python_lang}")
        results['programming_language'] = True
    except Exception as e:
        print_test("Programming language enum", False, str(e))
        results['programming_language'] = False
    
    return results

def test_sdk_graph_sitter_functionality() -> Dict[str, Any]:
    """Test SDK graph-sitter functionality"""
    print_section("SDK GRAPH-SITTER FUNCTIONALITY")
    results = {}
    
    # Test SDK configuration
    try:
        from codegen.sdk import config
        print_test("SDK configuration", True, f"Tree-sitter: {config.tree_sitter_enabled}")
        results['sdk_config'] = True
    except Exception as e:
        print_test("SDK configuration", False, str(e))
        results['sdk_config'] = False
    
    # Test compiled modules (fallback implementations)
    try:
        from codegen.sdk.compiled import utils, resolution, autocommit, sort
        print_test("Compiled modules", True, "All fallback modules loaded")
        results['compiled_modules'] = True
    except Exception as e:
        print_test("Compiled modules", False, str(e))
        results['compiled_modules'] = False
    
    # Test tree-sitter parser
    try:
        from codegen.sdk.tree_sitter_parser import get_parser_by_filepath_or_extension
        # This might fail due to missing language parsers, but should import
        print_test("Tree-sitter parser import", True, "Parser module loaded")
        results['tree_sitter_parser'] = True
    except Exception as e:
        print_test("Tree-sitter parser import", False, str(e))
        results['tree_sitter_parser'] = False
    
    # Test SDK lazy imports
    try:
        from codegen.sdk import analyze_codebase, parse_code, generate_code
        print_test("SDK lazy imports", True, "Analysis functions available")
        results['sdk_lazy_imports'] = True
    except Exception as e:
        print_test("SDK lazy imports", False, str(e))
        results['sdk_lazy_imports'] = False
    
    return results

def test_codebase_integration() -> Dict[str, Any]:
    """Test codebase integration between codegen and SDK"""
    print_section("CODEBASE INTEGRATION TEST")
    results = {}
    
    # Test that both Codebase classes are available
    try:
        from codegen.exports import Codebase as ExportCodebase
        from codegen.sdk.core.codebase import Codebase as SDKCodebase
        
        # Verify they are the same class (should be due to imports)
        same_class = ExportCodebase is SDKCodebase
        print_test("Codebase class identity", same_class, f"Same class: {same_class}")
        results['codebase_identity'] = same_class
    except Exception as e:
        print_test("Codebase class identity", False, str(e))
        results['codebase_identity'] = False
    
    # Test basic codebase functionality
    try:
        from codegen.sdk.core.codebase import Codebase
        # Try to create a codebase instance (may fail due to missing args)
        print_test("Codebase class available", True, "Codebase class imported successfully")
        results['codebase_available'] = True
    except Exception as e:
        print_test("Codebase class available", False, str(e))
        results['codebase_available'] = False
    
    return results

def test_cli_entry_points() -> Dict[str, Any]:
    """Test CLI entry points"""
    print_section("CLI ENTRY POINTS TEST")
    results = {}
    
    # Test main codegen CLI
    try:
        from codegen.cli.cli import main as codegen_main
        print_test("Codegen CLI entry point", True, "Main CLI function available")
        results['codegen_cli'] = True
    except Exception as e:
        print_test("Codegen CLI entry point", False, str(e))
        results['codegen_cli'] = False
    
    # Test SDK CLI
    try:
        from codegen.sdk.cli.main import main as sdk_main
        print_test("SDK CLI entry point", True, "SDK CLI function available")
        results['sdk_cli'] = True
    except Exception as e:
        print_test("SDK CLI entry point", False, str(e))
        results['sdk_cli'] = False
    
    return results

def test_dependencies() -> Dict[str, Any]:
    """Test critical dependencies"""
    print_section("DEPENDENCIES TEST")
    results = {}
    
    critical_deps = [
        ('tree_sitter', 'Tree-sitter core'),
        ('rustworkx', 'RustworkX graph library'),
        ('networkx', 'NetworkX'),
        ('plotly', 'Plotly visualization'),
        ('dicttoxml', 'Dict to XML conversion'),
        ('xmltodict', 'XML to dict conversion'),
        ('dataclasses_json', 'Dataclasses JSON'),
        ('tabulate', 'Table formatting'),
    ]
    
    for module_name, description in critical_deps:
        try:
            __import__(module_name)
            print_test(description, True, f"Module: {module_name}")
            results[module_name] = True
        except ImportError as e:
            print_test(description, False, f"Missing: {module_name} - {e}")
            results[module_name] = False
    
    return results

def test_system_wide_accessibility() -> Dict[str, Any]:
    """Test system-wide accessibility after pip install -e ."""
    print_section("SYSTEM-WIDE ACCESSIBILITY TEST")
    results = {}
    
    # Test that packages are accessible from any location
    try:
        import codegen
        import codegen.sdk
        from codegen.exports import Codebase, Function, Agent
        from codegen.sdk import analyze_codebase, config
        
        print_test("System-wide imports", True, "All packages accessible globally")
        results['system_wide'] = True
    except Exception as e:
        print_test("System-wide imports", False, str(e))
        results['system_wide'] = False
    
    # Test entry points would be available
    try:
        # These should be available as console scripts after pip install -e .
        from codegen.cli.cli import main
        from codegen.sdk.cli.main import main as sdk_main
        print_test("Console script entry points", True, "CLI entry points available")
        results['console_scripts'] = True
    except Exception as e:
        print_test("Console script entry points", False, str(e))
        results['console_scripts'] = False
    
    return results

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🚀 Starting Comprehensive Codegen + SDK Integration Test")
    print(f"Python version: {sys.version}")
    print(f"Test script location: {Path(__file__).absolute()}")
    
    all_results = {}
    
    # Run all test suites
    test_suites = [
        ("Basic Imports", test_basic_imports),
        ("Codegen Agent", test_codegen_agent_functionality),
        ("SDK Graph-Sitter", test_sdk_graph_sitter_functionality),
        ("Codebase Integration", test_codebase_integration),
        ("CLI Entry Points", test_cli_entry_points),
        ("Dependencies", test_dependencies),
        ("System-Wide Access", test_system_wide_accessibility),
    ]
    
    for suite_name, test_func in test_suites:
        try:
            results = test_func()
            all_results[suite_name] = results
        except Exception as e:
            print(f"❌ Test suite '{suite_name}' failed with exception: {e}")
            traceback.print_exc()
            all_results[suite_name] = {'error': str(e)}
    
    # Print comprehensive summary
    print_section("COMPREHENSIVE TEST SUMMARY")
    
    total_tests = 0
    passed_tests = 0
    
    for suite_name, results in all_results.items():
        if 'error' in results:
            print(f"❌ {suite_name}: SUITE ERROR")
            continue
            
        suite_total = len(results)
        suite_passed = sum(1 for v in results.values() if v is True)
        total_tests += suite_total
        passed_tests += suite_passed
        
        status = "✅" if suite_passed == suite_total else "⚠️"
        print(f"{status} {suite_name}: {suite_passed}/{suite_total} tests passed")
    
    print(f"\n📊 OVERALL RESULTS: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Integration is successful!")
        return True
    else:
        print("⚠️ Some tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)
