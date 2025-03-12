from typing import Optional

from codegen.extensions.attribution.git_history import GitAttributionTracker
from codegen.sdk.core.codebase import Codebase


def analyze_ai_impact(codebase: Codebase, ai_authors: Optional[list[str]] = None, max_commits: Optional[int] = None) -> dict:
    """Analyze the impact of AI on a codebase.

    Args:
        codebase: The codebase to analyze
        ai_authors: List of author names/emails to track as AI contributors
                    (defaults to ['devin[bot]', 'codegen[bot]'])
        max_commits: Maximum number of commits to process (None for all)

    Returns:
        Dictionary with analysis results
    """
    tracker = GitAttributionTracker(codebase, ai_authors)
    tracker.build_history(max_commits)
    tracker.map_symbols_to_history()

    # Get basic stats
    stats = tracker.get_ai_contribution_stats()

    # Get AI-touched symbols
    ai_symbols = tracker.get_ai_touched_symbols()

    # Find high-impact AI symbols (those with many dependents)
    high_impact_symbols = []
    for symbol in ai_symbols:
        if hasattr(symbol, "usages") and len(symbol.usages) > 5:
            high_impact_symbols.append({"name": symbol.name, "filepath": symbol.filepath, "usage_count": len(symbol.usages), "last_editor": tracker.get_symbol_last_editor(symbol)})

    # Sort by usage count
    high_impact_symbols.sort(key=lambda x: x["usage_count"], reverse=True)

    # Get timeline data
    timeline = tracker.get_ai_contribution_timeline()
    timeline_data = [{"date": dt.strftime("%Y-%m"), "count": count} for dt, count in timeline]

    # Get list of all contributors with commit counts
    contributors = []
    for author_id, commits in tracker._author_contributions.items():
        contributors.append((author_id, len(commits)))

    # Sort by commit count (descending)
    contributors.sort(key=lambda x: x[1], reverse=True)

    return {
        "stats": stats,
        "ai_symbol_count": len(ai_symbols),
        "total_symbol_count": len(list(codebase.symbols)),
        "high_impact_symbols": high_impact_symbols[:20],  # Top 20
        "timeline": timeline_data,
        "contributors": contributors,
    }


def add_attribution_to_symbols(codebase: Codebase, ai_authors: Optional[list[str]] = None) -> None:
    """Add attribution information to symbols in the codebase.

    This adds the following attributes to each symbol:
    - last_editor: The name of the last person who edited the symbol
    - editor_history: List of all editors who have touched the symbol

    Args:
        codebase: The codebase to analyze
        ai_authors: List of author names/emails to track as AI contributors
    """
    tracker = GitAttributionTracker(codebase, ai_authors)
    tracker.build_history()
    tracker.map_symbols_to_history()

    # Add attribution to each symbol
    for symbol in codebase.symbols:
        history = tracker.get_symbol_history(symbol)

        # Add last editor
        if history:
            sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
            symbol.last_editor = sorted_history[0]["author"]

            # Add editor history (unique editors)
            editors = {commit["author"] for commit in history}
            symbol.editor_history = list(editors)

            # Add is_ai_authored flag
            symbol.is_ai_authored = any(editor in tracker.ai_authors for editor in symbol.editor_history)
