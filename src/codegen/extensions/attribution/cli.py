import json
import os

import pygit2

import codegen
from codegen import Codebase
from codegen.extensions.attribution.main import add_attribution_to_symbols, analyze_ai_impact


def diagnose_repository(codebase):
    """Print diagnostic information about the repository."""
    try:
        repo_path = codebase.ctx.projects[0].repo_operator.repo_path
        print("\n🔍 Repository Diagnostics:")
        print(f"Repository path: {repo_path}")

        # Check if it's a git repository
        if not os.path.exists(os.path.join(repo_path, ".git")):
            print("⚠️ No .git directory found. This might not be a git repository.")
            return

        try:
            repo = pygit2.Repository(repo_path)

            # Check if repository has commits
            try:
                head = repo.head
                head_commit = repo.get(head.target)
                print(f"Repository has a HEAD commit: {head_commit.id}")
                print(f"HEAD commit author: {head_commit.author.name} <{head_commit.author.email}>")
                print(f"HEAD commit message (first 5 lines only): {'\n'.join(head_commit.message.strip().split('\n')[:5])}")
                print("...")
                # Check if it's a shallow clone
                if os.path.exists(os.path.join(repo_path, ".git", "shallow")):
                    print("⚠️ This appears to be a shallow clone, which may have limited history.")

                # Try to count commits
                commit_count = 0
                for _ in repo.walk(head.target, pygit2.GIT_SORT_TIME):
                    commit_count += 1
                    if commit_count >= 10:  # Just check first 10
                        break

                if commit_count == 0:
                    print("⚠️ No commits found in the repository.")
                else:
                    print(f"Found at least {commit_count} commits in the repository.")

            except (pygit2.GitError, KeyError) as e:
                print(f"⚠️ Error accessing HEAD: {e}")
                print("This repository might be empty or corrupted.")

        except Exception as e:
            print(f"⚠️ Error opening repository with pygit2: {e}")

    except Exception as e:
        print(f"⚠️ Error during repository diagnosis: {e}")


@codegen.function("analyze-ai-impact")
def run(codebase: Codebase):
    """Analyze the impact of AI on the codebase.

    This function:
    1. Analyzes git history to identify AI contributions
    2. Identifies which parts of the codebase were written by AI
    3. Determines the impact of AI-written code
    4. Generates a report with statistics and visualizations

    Run the analysis using the codegen CLI:
    codegen analyze-ai-impact

    Or from script:
    from codegen.extensions.attribution.cli import run
    codebase = Codebase....
    run(codebase)
    """
    print("🤖 Analyzing AI impact on codebase...")

    # Run repository diagnostics first
    diagnose_repository(codebase)

    # Default AI authors to track (and ci bots)
    ai_authors = ["renovate[bot]", "dependabot[bot]", "github-actions[bot]", "devin-ai-integration[bot]"]

    # Run the analysis
    results = analyze_ai_impact(codebase, ai_authors)

    # Print list of all contributors
    print("\n👥 All Contributors:")
    contributors = results.get("contributors", [])
    if contributors:
        # Sort by commit count (descending)
        for author, count in contributors:
            is_ai = any(ai_name in author for ai_name in ai_authors)
            ai_indicator = "🤖" if is_ai else "👤"
            print(f"  {ai_indicator} {author}: {count} commits")
    else:
        print("  No contributors found.")

    # Print summary statistics
    stats = results["stats"]
    print("\n📊 AI Contribution Summary:")
    print(f"Total commits: {stats['total_commits']}")
    print(f"AI commits: {stats['ai_commits']} ({stats['ai_percentage']:.1f}%)")

    if stats["total_file_count"] > 0:
        ai_file_percentage = stats["ai_file_count"] / stats["total_file_count"] * 100
    else:
        ai_file_percentage = 0.0
    print(f"Files with >50% AI contribution: {stats['ai_file_count']} of {stats['total_file_count']} ({ai_file_percentage:.1f}%)")

    if results["total_symbol_count"] > 0:
        ai_symbol_percentage = results["ai_symbol_count"] / results["total_symbol_count"] * 100
    else:
        ai_symbol_percentage = 0.0
    print(f"AI-touched symbols: {results['ai_symbol_count']} of {results['total_symbol_count']} ({ai_symbol_percentage:.1f}%)")

    # Print high-impact AI symbols
    print("\n🔍 High-Impact AI-Written Code:")
    if results["high_impact_symbols"]:
        for symbol in results["high_impact_symbols"][:10]:  # Show top 10
            print(f"  • {symbol['name']} ({symbol['filepath']})")
            print(f"    - Used by {symbol['usage_count']} other symbols")
            print(f"    - Last edited by: {symbol['last_editor']}")
    else:
        print("  No high-impact AI-written code found.")

    # Print top AI files
    print("\n📁 Top Files by AI Contribution:")
    if stats["top_ai_files"]:
        for file_path, percentage in stats["top_ai_files"][:10]:  # Show top 10
            print(f"  • {file_path}: {percentage:.1f}% AI contribution")
    else:
        print("  No files with AI contributions found.")

    # Save detailed results to file
    output_path = "ai_impact_analysis.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Detailed analysis saved to {output_path}")

    # Add attribution to symbols
    print("\n🏷️ Adding attribution information to symbols...")
    add_attribution_to_symbols(codebase, ai_authors)
    print("✅ Attribution information added to symbols")

    print("\nYou can now access attribution information on symbols:")
    print("  • symbol.last_editor - The last person who edited the symbol")
    print("  • symbol.editor_history - List of all editors who have touched the symbol")
    print("  • symbol.is_ai_authored - Whether the symbol was authored by AI")
