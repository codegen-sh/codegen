from github.Comparison import Comparison


def format_comparison(comparison: Comparison, show_commits: bool = True) -> str:
    diff_str_list = []

    for file in comparison.files:
        # Header for each file
        diff_str_list.append(f"File: {file.filename}, Status: {file.status}")
        diff_str_list.append(f"+++ {file.filename if file.status != 'removed' else '/dev/null'}")
        diff_str_list.append(f"--- {file.filename if file.status != 'added' else '/dev/null'}")

        # Parsing the patch for each file
        if file.patch:
            for line in file.patch.split("\n"):
                if line.startswith("+") or line.startswith("-"):
                    diff_str_list.append(line)

    if show_commits:
        for commit in comparison.commits:
            # Commit information
            diff_str_list.append(f"Commit: {commit.sha}, Author: {commit.commit.author.name}, Message: {commit.commit.message}")

    return "\n".join(diff_str_list)
