import codegen
from codegen import Codebase

# Initialize codebase

# Define the target directory
TARGET_DIR = "input_repo"


def convert_print_statements(file):
    """Convert Python 2 print statements to Python 3 function calls"""
    print(f"📁 Processing file: {file.filepath}")
    lines = file.content.split("\n")
    new_content = []
    updates = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("print "):
            indent = line[: len(line) - len(line.lstrip())]
            args = stripped[6:].strip()
            new_content.append(f"{indent}print({args})")
            updates += 1
            print(f"  🔄 Converting: {stripped} -> print({args})")
        else:
            new_content.append(line)

    if updates > 0:
        file.edit("\n".join(new_content))
        print(f"✅ Updated {updates} print statements\n")


def update_unicode_to_str(file):
    """Convert Unicode-related code to str for Python 3"""
    print(f"🔎 Processing file: {file.filepath}")

    # Update imports from 'unicode' to 'str'
    for imp in file.imports:
        if imp.name == "unicode":
            print(f"📦 Updating import in {file.filepath}")
            imp.set_name("str")

    # Update function calls from Unicode to str
    for func_call in file.function_calls:
        if func_call.name == "unicode":
            print("🔧 Converting Unicode() call to str()")
            func_call.set_name("str")

        # Check function arguments for Unicode references
        for arg in func_call.args:
            if arg.value == "unicode":
                print("📝 Updating argument from unicode to str")
                arg.set_value("str")

    # Find and update Unicode string literals (u"...")
    for string_literal in file.find('u"'):
        if string_literal.source.startswith('u"') or string_literal.source.startswith("u'"):
            print("🔤 Converting Unicode string literal to regular string")
            new_string = string_literal.source[1:]  # Remove the 'u' prefix
            string_literal.edit(new_string)


def convert_raw_input(file):
    """Convert raw_input() calls to input()"""
    print(f"\n📁 Processing file: {file.filepath}")
    for call in file.function_calls:
        if call.name == "raw_input":
            print(f"  🔄 Found raw_input: {call.source}")
            print(f"  ✨ Converting to: input{call.source[len('raw_input') :]}")
            call.edit(f"input{call.source[len('raw_input') :]}")


def update_exception_syntax(file):
    """Update Python 2 exception handling to Python 3 syntax"""
    try:
        print(f"🔍 Processing {file.filepath}")
        for editable in file.find("except "):
            try:
                if editable.source.lstrip().startswith("except") and ", " in editable.source and " as " not in editable.source:
                    print(f"🔄 Found Python 2 style exception: {editable.source.strip()}")
                    parts = editable.source.split(",", 1)
                    new_source = f"{parts[0]} as{parts[1]}"
                    print(f"✨ Converting to: {new_source.strip()}")
                    editable.edit(new_source)
            except Exception as e:
                print(f"⚠️ Error processing except clause: {e!s}")
    except Exception as e:
        print(f"❌ Error processing file {file.filepath}: {e!s}")


def update_iterators(file):
    """Update iterator methods from Python 2 to Python 3"""
    print(f"\n📁 Processing file: {file.filepath}")

    for cls in file.classes:
        next_method = cls.get_method("next")
        if next_method:
            print(f"  ⚙️ Found iterator class: {cls.name}")
            print("    📝 Converting next() to __next__()")

            # Create new __next__ method with same content
            new_method_source = next_method.source.replace("def next", "def __next__")
            cls.add_source(new_method_source)

            print("    🗑️ Removing old next() method")
            next_method.remove()

            # Update print statements
            print("    🔄 Updating print statements to Python3 syntax")
            for stmt in cls.code_block.statements:
                if 'print "' in stmt.source or "print '" in stmt.source:
                    new_stmt = stmt.source.replace('print "', 'print("').replace("print '", "print('")
                    if not new_stmt.strip().endswith(")"):
                        new_stmt = new_stmt.rstrip() + ")"
                    stmt.edit(new_stmt)


@codegen.function("python2-to-python3")
def run():
    """Main function to run the Python 2 to 3 conversion"""
    print("🚀 Starting Python 2 to 3 conversion...\n")

    # Process each file in the target directory
    for file in codebase.files:
        if TARGET_DIR in file.filepath:
            # Step 1: Convert print statements
            print("\n📝 Step 1: Converting print statements...")
            convert_print_statements(file)

            # Step 2: Update Unicode to str
            print("\n📝 Step 2: Converting Unicode to str...")
            update_unicode_to_str(file)

            # Step 3: Convert raw_input to input
            print("\n📝 Step 3: Converting raw_input to input...")
            convert_raw_input(file)

            # Step 4: Update exception handling syntax
            print("\n📝 Step 4: Updating exception handling...")
            update_exception_syntax(file)

            # Step 5: Update iterator methods
            print("\n📝 Step 5: Updating iterator methods...")
            update_iterators(file)

    # Commit all changes
    print("\n💾 Committing changes...")
    codebase.commit()
    print("✅ Python 2 to 3 conversion completed successfully!")


if __name__ == "__main__":
    codebase = Codebase("./")

    run(codebase)
