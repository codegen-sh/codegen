import codegen
from codegen import Codebase
import re


def count_lines(source: str):
    """Count different types of lines in source code.

    Args:
        source: The source code string to analyze

    Returns:
        tuple: (LOC, LLOC, SLOC, Comments)
    """
    if not source.strip():
        return 0, 0, 0, 0

    lines = [line.strip() for line in source.splitlines()]
    loc = len(lines)
    sloc = len([line for line in lines if line])

    in_multiline = False
    comments = 0
    code_lines = []

    i = 0
    while i < len(lines):
        line = lines[i]
        code_part = line
        if not in_multiline and "#" in line:
            comment_start = line.find("#")
            if not re.search(r'["\'].*#.*["\']', line[:comment_start]):
                code_part = line[:comment_start].strip()
                if line[comment_start:].strip():
                    comments += 1

        # Handle multi-line strings/comments
        if ('"""' in line or "'''" in line) and not (line.count('"""') % 2 == 0 or line.count("'''") % 2 == 0):
            if in_multiline:
                in_multiline = False
                comments += 1
            else:
                in_multiline = True
                comments += 1
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    code_part = ""
        elif in_multiline:
            comments += 1
            code_part = ""
        elif line.strip().startswith("#"):
            comments += 1
            code_part = ""

        if code_part.strip():
            code_lines.append(code_part)

        i += 1

    lloc = 0
    continued_line = False
    for line in code_lines:
        if continued_line:
            if not any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
                continued_line = False
            continue

        lloc += len([stmt for stmt in line.split(";") if stmt.strip()])

        if any(line.rstrip().endswith(c) for c in ("\\", ",", "{", "[", "(")):
            continued_line = True

    return loc, lloc, sloc, comments


@codegen.function("line-metrics")
def run(codebase: Codebase):
    """Analyze line metrics across the codebase."""
    total_loc = 0
    total_lloc = 0
    total_sloc = 0
    total_comments = 0
    results = []

    for file in codebase.files:
        loc, lloc, sloc, comments = count_lines(file.source)

        results.append({"filepath": file.filepath, "loc": loc, "lloc": lloc, "sloc": sloc, "comments": comments})

        total_loc += loc
        total_lloc += lloc
        total_sloc += sloc
        total_comments += comments

    results.sort(key=lambda x: x["loc"], reverse=True)

    print("\n📊 Line Metrics Analysis")
    print("=" * 60)
    print("\n📈 Overall Stats:")
    print(f"  • Total Lines of Code (LOC): {total_loc}")
    print(f"  • Total Logical Lines (LLOC): {total_lloc}")
    print(f"  • Total Source Lines (SLOC): {total_sloc}")
    print(f"  • Total Comments: {total_comments}")
    print(f"  • Comment Density: {(total_comments / total_loc) * 100:.1f}%")

    print("\n📝 Top 10 Largest Files:")
    print("-" * 60)
    for result in results[:10]:
        filepath = result["filepath"]
        if len(filepath) > 40:
            filepath = "..." + filepath[-37:]

        print(f"  • {filepath}")
        print(f"    LOC: {result['loc']}, LLOC: {result['lloc']}, SLOC: {result['sloc']}, Comments: {result['comments']}")

    return results


if __name__ == "__main__":
    codebase = Codebase.from_repo("modal-labs/modal-client")
    run(codebase)
