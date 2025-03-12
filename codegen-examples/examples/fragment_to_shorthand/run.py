import codegen
from codegen import Codebase


@codegen.function("fragment_to_shorthand")
def run(codebase: Codebase):
    print("🔍 Starting Fragment syntax conversion...")

    for file in codebase.files:
        print(f"📁 Processing: {file.filepath}")

        fragments_found = False

        # Convert Fragment components to shorthand
        for element in file.jsx_elements:
            if element.name == "Fragment":
                print(f"🔄 Converting Fragment in {file.filepath}")
                element.set_name("")  # Convert to <> syntax
                fragments_found = True

        # Clean up Fragment imports if we found and converted any
        if fragments_found:
            for import_stmt in file.import_statements:
                for imp in import_stmt.imports:
                    if imp.name == "Fragment":
                        print(f"🧹 Removing Fragment import from {file.filepath}")
                        imp.remove()

        if fragments_found:
            print(f"✨ Completed conversion in {file.filepath}")
            codebase.commit()


if __name__ == "__main__":
    print("🎯 Starting Fragment to shorthand conversion...")
    codebase = Codebase.from_repo("RocketChat/Rocket.Chat", commit="a4f2102af1c2e875c60cafebd0163105bdaca678", language="typescript")
    run(codebase)
    print("✅ Done! All Fragments converted to shorthand syntax!")
