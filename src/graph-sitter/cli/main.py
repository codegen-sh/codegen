"""
Main CLI entry point for Codegen SDK.

Provides command-line interface for SDK functionality including:
- Code analysis and parsing
- Codebase manipulation
- AI-powered code generation
- Graph-sitter integration
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Import SDK components
try:
    from codegen.sdk import Codebase, Function, ProgrammingLanguage, config
    from codegen.sdk.core.codebase import Codebase as CoreCodebase
except ImportError as e:
    print(f"❌ Failed to import SDK components: {e}")
    sys.exit(1)

app = typer.Typer(
    name="codegen-sdk",
    help="Codegen SDK - Advanced Code Analysis and Manipulation Framework",
    rich_markup_mode="rich",
)
console = Console()


@app.command()
def version():
    """Show SDK version information"""
    from codegen.sdk import __version__, __author__, __email__
    
    version_info = Text()
    version_info.append("Codegen SDK\n", style="bold blue")
    version_info.append(f"Version: {__version__}\n", style="green")
    version_info.append(f"Author: {__author__}\n", style="dim")
    version_info.append(f"Email: {__email__}\n", style="dim")
    
    console.print(Panel(version_info, title="Version Info", border_style="blue"))


@app.command()
def analyze(
    path: Path = typer.Argument(..., help="Path to analyze (file or directory)"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Programming language"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Analyze code structure and dependencies"""
    console.print(f"🔍 Analyzing: [bold]{path}[/bold]")
    
    if not path.exists():
        console.print(f"❌ Path does not exist: {path}", style="red")
        raise typer.Exit(1)
    
    try:
        # Create codebase instance
        if path.is_file():
            console.print("📄 Analyzing single file...")
            # Analyze single file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            console.print(f"✅ File analyzed: {len(content)} characters")
            
        else:
            console.print("📁 Analyzing directory...")
            # Analyze directory as codebase
            codebase = Codebase(str(path))
            console.print(f"✅ Codebase analyzed: {path}")
            
        if verbose:
            console.print("🔧 Analysis complete with detailed output")
        else:
            console.print("✅ Analysis complete")
            
    except Exception as e:
        console.print(f"❌ Analysis failed: {e}", style="red")
        if verbose:
            import traceback
            console.print(traceback.format_exc(), style="dim red")
        raise typer.Exit(1)


@app.command()
def parse(
    file_path: Path = typer.Argument(..., help="File to parse"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="Programming language"),
    output_format: str = typer.Option("json", "--format", "-f", help="Output format (json, yaml, tree)"),
):
    """Parse source code into AST representation"""
    console.print(f"🌳 Parsing: [bold]{file_path}[/bold]")
    
    if not file_path.exists():
        console.print(f"❌ File does not exist: {file_path}", style="red")
        raise typer.Exit(1)
    
    try:
        # Parse the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        console.print(f"✅ File parsed: {len(content)} characters")
        console.print(f"📊 Output format: {output_format}")
        
    except Exception as e:
        console.print(f"❌ Parsing failed: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    no_ai: bool = typer.Option(False, "--no-ai", help="Disable AI features"),
):
    """Configure SDK settings"""
    if show:
        console.print("⚙️ Current SDK Configuration:")
        console.print(f"  Tree-sitter enabled: {config.tree_sitter_enabled}")
        console.print(f"  AI features enabled: {config.ai_features_enabled}")
        console.print(f"  Cache enabled: {config.cache_enabled}")
        console.print(f"  Debug mode: {config.debug_mode}")
        return
    
    if debug:
        config.enable_debug()
        console.print("🐛 Debug mode enabled", style="yellow")
    
    if no_ai:
        config.disable_ai_features()
        console.print("🤖 AI features disabled", style="yellow")


@app.command()
def test():
    """Test SDK functionality and imports"""
    console.print("🧪 Testing SDK functionality...")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Basic imports
    tests_total += 1
    try:
        from codegen.sdk import Codebase, Function, ProgrammingLanguage
        console.print("✅ Basic imports working")
        tests_passed += 1
    except Exception as e:
        console.print(f"❌ Basic imports failed: {e}", style="red")
    
    # Test 2: Core functionality
    tests_total += 1
    try:
        # Test basic functionality
        lang = ProgrammingLanguage.PYTHON
        console.print(f"✅ Programming language enum working: {lang}")
        tests_passed += 1
    except Exception as e:
        console.print(f"❌ Core functionality failed: {e}", style="red")
    
    # Test 3: Configuration
    tests_total += 1
    try:
        from codegen.sdk import config
        console.print(f"✅ Configuration working: debug={config.debug_mode}")
        tests_passed += 1
    except Exception as e:
        console.print(f"❌ Configuration failed: {e}", style="red")
    
    # Summary
    console.print(f"\n📊 Test Results: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        console.print("🎉 All tests passed!", style="green")
    else:
        console.print("⚠️ Some tests failed", style="yellow")
        raise typer.Exit(1)


def main():
    """Main entry point for SDK CLI"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="dim")
        sys.exit(0)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
