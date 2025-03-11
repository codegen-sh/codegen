import os
import sys

from codegen import Codebase
from codegen.extensions.attribution.cli import run
from codegen.extensions.attribution.main import add_attribution_to_symbols
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig
from codegen.shared.enums.programming_language import ProgrammingLanguage


def print_symbol_attribution(codebase):
    """Print attribution information for symbols in the codebase."""
    print("\n🔍 Symbol Attribution Examples:")

    # First, make sure attribution information is added to symbols
    ai_authors = ["devin[bot]", "codegen[bot]", "github-actions[bot]"]
    add_attribution_to_symbols(codebase, ai_authors)

    # Get some interesting symbols to examine
    # Let's look at classes and functions with the most usages
    symbols_with_usages = []
    for symbol in codebase.symbols:
        if hasattr(symbol, "usages") and len(symbol.usages) > 0:
            symbols_with_usages.append((symbol, len(symbol.usages)))

    # Sort by usage count (most used first)
    symbols_with_usages.sort(key=lambda x: x[1], reverse=True)

    # Print attribution for top symbols
    count = 0
    for symbol, usage_count in symbols_with_usages[:10]:  # Look at top 10 most used symbols
        count += 1
        print(f"\n📊 Symbol #{count}: {symbol.name} ({type(symbol).__name__})")
        print(f"  • File: {symbol.filepath}")
        print(f"  • Usages: {usage_count}")

        # Print attribution information
        if hasattr(symbol, "last_editor"):
            print(f"  • Last editor: {symbol.last_editor}")
        else:
            print("  • Last editor: Not available")

        if hasattr(symbol, "editor_history") and symbol.editor_history:
            print(f"  • Editor history: {', '.join(symbol.editor_history[:5])}" + (f" and {len(symbol.editor_history) - 5} more..." if len(symbol.editor_history) > 5 else ""))
        else:
            print("  • Editor history: Not available")

        if hasattr(symbol, "is_ai_authored"):
            print(f"  • AI authored: {'Yes' if symbol.is_ai_authored else 'No'}")
        else:
            print("  • AI authored: Not available")


if __name__ == "__main__":
    try:
        print("Initializing codebase...")

        # Use current directory if it's a git repository
        if os.path.exists(".git"):
            print("Using current directory as repository...")
            repo_path = os.getcwd()
            repo_config = RepoConfig.from_repo_path(repo_path)
            repo_operator = RepoOperator(repo_config=repo_config)

            project = ProjectConfig.from_repo_operator(repo_operator=repo_operator, programming_language=ProgrammingLanguage.PYTHON)
            codebase = Codebase(projects=[project])
        else:
            # Use from_repo method for a well-known repository
            print("Using a sample repository...")
            codebase = Codebase.from_repo(
                repo_full_name="codegen-sh/codegen",
                # commit="",  # Using a specific commit for consistency
                language="python",
            )

        print(f"Codebase loaded with {len(codebase.files)} files and {len(codebase.symbols)} symbols")

        # First run the analysis to gather attribution data
        print("\n🔍 Running AI impact analysis...")
        run(codebase)

        # Then show examples of accessing attribution information
        print_symbol_attribution(codebase)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
