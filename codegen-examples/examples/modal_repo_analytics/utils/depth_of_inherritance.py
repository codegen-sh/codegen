import codegen
from codegen import Codebase


def calculate_doi(cls):
    """Calculate the depth of inheritance for a given class."""
    return len(cls.superclasses)


@codegen.function("depth-of-inheritance")
def run(codebase: Codebase):
    """Analyze depth of inheritance for all classes in the codebase."""
    results = []
    total_doi = 0

    for cls in codebase.classes:
        doi = calculate_doi(cls)
        results.append({"name": cls.name, "doi": doi})
        total_doi += doi

    if results:
        max_doi = max(result["doi"] for result in results)
        print(f"Highest Depth of Inheritance (DOI): {max_doi}")
        print("\nClasses with highest DOI:")
        for result in results:
            if result["doi"] == max_doi:
                print(f"- {result['name']}")
    else:
        print("❌ No classes found in the codebase to analyze.")


if __name__ == "__main__":
    codebase = Codebase.from_repo("posthog/posthog")
    run(codebase)
