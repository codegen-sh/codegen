#!/usr/bin/env python3
"""
Demo script showing Codegen + SDK integration working together.

This demonstrates:
1. Codegen agent imports and basic functionality
2. SDK graph-sitter contexts and analysis
3. Both packages working in harmony
"""

def demo_codegen_imports():
    """Demonstrate codegen package imports"""
    print("🔧 Testing Codegen Package Imports:")
    
    # Import from main exports
    from codegen.exports import Agent, Codebase, Function, ProgrammingLanguage
    print(f"  ✅ Agent: {Agent}")
    print(f"  ✅ Codebase: {Codebase}")
    print(f"  ✅ Function: {Function}")
    print(f"  ✅ ProgrammingLanguage: {ProgrammingLanguage}")
    
    # Test programming language enum
    python_lang = ProgrammingLanguage.PYTHON
    print(f"  ✅ Python language: {python_lang}")
    
    return True

def demo_sdk_functionality():
    """Demonstrate SDK functionality"""
    print("\n🌳 Testing SDK Graph-Sitter Functionality:")
    
    # Import SDK components
    from codegen.sdk import Codebase, Function, ProgrammingLanguage, config
    print(f"  ✅ SDK Codebase: {Codebase}")
    print(f"  ✅ SDK Function: {Function}")
    print(f"  ✅ SDK ProgrammingLanguage: {ProgrammingLanguage}")
    
    # Test configuration
    print(f"  ✅ Tree-sitter enabled: {config.tree_sitter_enabled}")
    print(f"  ✅ AI features enabled: {config.ai_features_enabled}")
    
    # Test lazy imports
    from codegen.sdk import analyze_codebase, parse_code, generate_code
    print(f"  ✅ Analysis functions available: analyze_codebase, parse_code, generate_code")
    
    return True

def demo_compiled_modules():
    """Demonstrate compiled modules (fallback implementations)"""
    print("\n⚙️ Testing Compiled Modules:")
    
    # Test resolution module
    from codegen.sdk.compiled.resolution import UsageKind, ResolutionStack, Resolution
    print(f"  ✅ UsageKind enum: {UsageKind}")
    print(f"  ✅ ResolutionStack: {ResolutionStack}")
    
    # Create a resolution example
    resolution = Resolution("test_function", UsageKind.CALL)
    print(f"  ✅ Resolution example: {resolution}")
    
    # Test resolution stack
    stack = ResolutionStack()
    stack.push("item1")
    stack.push("item2")
    print(f"  ✅ Stack length: {len(stack)}")
    print(f"  ✅ Stack peek: {stack.peek()}")
    
    return True

def demo_tree_sitter_parsers():
    """Demonstrate tree-sitter parser availability"""
    print("\n🌲 Testing Tree-sitter Language Parsers:")
    
    parsers = [
        'tree_sitter_python',
        'tree_sitter_javascript', 
        'tree_sitter_typescript',
        'tree_sitter_java',
        'tree_sitter_go',
        'tree_sitter_rust',
        'tree_sitter_cpp',
        'tree_sitter_c',
    ]
    
    available_parsers = []
    for parser in parsers:
        try:
            __import__(parser)
            available_parsers.append(parser)
            print(f"  ✅ {parser}")
        except ImportError:
            print(f"  ❌ {parser} (not available)")
    
    print(f"  📊 Available parsers: {len(available_parsers)}/{len(parsers)}")
    return len(available_parsers) > 0

def demo_integration():
    """Demonstrate integration between codegen and SDK"""
    print("\n🔗 Testing Codegen + SDK Integration:")
    
    # Import from both packages
    from codegen.exports import Codebase as CodegenCodebase
    from codegen.sdk.core.codebase import Codebase as SDKCodebase
    
    # Check if they're the same class (they should be)
    same_class = CodegenCodebase is SDKCodebase
    print(f"  ✅ Same Codebase class: {same_class}")
    
    # Test that both import paths work
    from codegen.exports import ProgrammingLanguage as CodegenPL
    from codegen.sdk import ProgrammingLanguage as SDKPL
    
    same_enum = CodegenPL is SDKPL
    print(f"  ✅ Same ProgrammingLanguage enum: {same_enum}")
    
    return same_class and same_enum

def main():
    """Run all demonstrations"""
    print("🚀 Codegen + SDK Integration Demo")
    print("=" * 50)
    
    tests = [
        ("Codegen Imports", demo_codegen_imports),
        ("SDK Functionality", demo_sdk_functionality),
        ("Compiled Modules", demo_compiled_modules),
        ("Tree-sitter Parsers", demo_tree_sitter_parsers),
        ("Integration", demo_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"⚠️ {test_name}: PARTIAL")
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Demo Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All demos passed! Integration is working perfectly!")
        print("\n🔧 Available CLI commands:")
        print("  • codegen        - Main codegen CLI")
        print("  • codegen-sdk    - SDK CLI")
        print("  • gs             - SDK CLI (short alias)")
        print("  • graph-sitter   - SDK CLI (full name)")
        
        print("\n📚 Usage examples:")
        print("  codegen-sdk version")
        print("  codegen-sdk test")
        print("  gs analyze /path/to/code")
        print("  graph-sitter parse file.py")
        
        return True
    else:
        print("⚠️ Some demos failed. Check the output above.")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
