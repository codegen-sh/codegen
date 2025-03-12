import codegen
from codegen import Codebase

# Initialize codebase

# Define the target directory
TARGET_DIR = "input_repo/tests"


def remove_unittest_inheritance(file):
    """Removes inheritance from unittest.TestCase for classes in a file"""
    print(f"🔍 Checking file: {file.filepath}")
    # Iterate through all classes in the file
    for cls in file.classes:
        # Check if the class inherits from unittest.TestCase
        if any(base.source == "unittest.TestCase" for base in cls.parent_class_names):
            # Remove the inheritance
            cls.parent_class_names[0].remove()
            print(f"🔧 Removed unittest.TestCase inheritance from: {cls.name}")


def convert_to_pytest_fixtures(file):
    """Converts unittest setUp methods to pytest fixtures and updates test methods"""
    print(f"🔍 Processing file: {file.filepath}")

    if not any(imp.name == "pytest" for imp in file.imports):
        file.add_import("import pytest")
        print(f"➕ Added pytest import to {file.filepath}")

    for cls in file.classes:
        setup_method = cls.get_method("setUp")
        if setup_method:
            fixture_name = f"setup_{cls.name.lower()}"
            fixture_body = "\n".join([line.replace("self.", "") for line in setup_method.body.split("\n")])
            fixture_code = f"""
@pytest.fixture
def {fixture_name}():
{fixture_body.strip()}
"""

            model_class = "Character" if "Character" in cls.name else "Castle"

            for method in cls.methods:
                if method.name == "setUp":
                    method.insert_before(fixture_code)
                    print(f"🔧 Created fixture {fixture_name} for class {cls.name}")
                elif method.name.startswith("test_"):
                    new_signature = f"def {method.name}({fixture_name}, {model_class}):"
                    method_body = "\n".join([line.replace("self.", "") for line in method.source.split("\n")[1:]])
                    method.edit(f"{new_signature}\n{method_body}")
                    print(f"🔄 Updated test method {method.name} signature and removed self references")
            setup_method.remove()
            print(f"🗑️ Removed setUp method from class {cls.name}")


@codegen.function("unittest-to-pytest")
def run(codebase: Codebase):
    """Main function to run the unittest to pytest conversion"""
    print("🚀 Starting unittest to pytest conversion...")

    # Step 1: Remove unittest.TestCase inheritance
    print("\n📝 Step 1: Removing unittest.TestCase inheritance...")
    for file in codebase.files:
        if TARGET_DIR in file.filepath:
            remove_unittest_inheritance(file)

    # Step 2: Convert setUp methods to pytest fixtures
    print("\n📝 Step 2: Converting setUp methods to pytest fixtures...")
    for file in codebase.files:
        if TARGET_DIR in file.filepath:
            convert_to_pytest_fixtures(file)

    # Commit changes
    print("\n💾 Committing changes...")
    codebase.commit()
    print("✅ Conversion completed successfully!")


if __name__ == "__main__":
    codebase = Codebase("./")
    run(codebase)
