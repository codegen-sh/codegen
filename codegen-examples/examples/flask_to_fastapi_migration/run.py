import codebase
from codegen import Codebase

# Initialize codebase

# Define the target directory
TARGET_DIR = "repo-before"


def update_flask_imports_and_init(file):
    """Update Flask imports and initialization to FastAPI"""
    print(f"🔍 Processing file: {file.filepath}")

    # Update imports
    for imp in file.imports:
        if imp.name == "Flask":
            print("  📦 Updating import: Flask -> FastAPI")
            imp.set_name("FastAPI")
        elif imp.symbol_name == "flask":
            print("  📦 Updating import module: flask -> fastapi")
            imp.set_import_module("fastapi")

    # Update Flask initialization and remove __name__
    for call in file.function_calls:
        if call.name == "Flask":
            print("  🔧 Updating function call: Flask -> FastAPI")
            call.set_name("FastAPI")
            if len(call.args) > 0 and call.args[0].value == "__name__":
                print("  🗑️ Removing __name__ argument from FastAPI initialization")
                call.args[0].remove()


def update_route_decorators(file):
    """Convert Flask route decorators to FastAPI style"""
    print(f"\n📁 Processing file: {file.filepath}")

    for function in file.functions:
        for decorator in function.decorators:
            if "@app.route" in decorator.source:
                route = decorator.source.split('"')[1]
                method = "get"
                if "methods=" in decorator.source:
                    methods = decorator.source.split("methods=")[1].split("]")[0].strip().lower().replace("'", "").replace('"', "")
                    if "post" in methods:
                        method = "post"
                    elif "put" in methods:
                        method = "put"
                    elif "delete" in methods:
                        method = "delete"
                new_decorator = f'@app.{method}("{route}")'
                decorator.edit(new_decorator)
                print(f"🔄 Updated decorator for function '{function.name}': {new_decorator}")


def setup_static_files(file):
    """Add static file handling for FastAPI"""
    print(f"📁 Processing file: {file.filepath}")

    # Add import for StaticFiles
    file.add_import("from fastapi.staticfiles import StaticFiles")
    print("✅ Added import: from fastapi.staticfiles import StaticFiles")

    # Add app.mount for static file handling
    file.add_symbol_from_source('app.mount("/static", StaticFiles(directory="static"), name="static")')
    print("✅ Added app.mount for static file handling")


def update_jinja2_syntax(file):
    """Update Jinja2 template handling for FastAPI"""
    print(f"\n📁 Processing: {file.filepath}")

    # Update url_for calls
    for func_call in file.function_calls:
        if func_call.name == "url_for" and func_call.args:
            arg_value = func_call.args[0].value
            if arg_value and arg_value[0] != "'" and arg_value[0] != '"':
                func_call.args[0].set_value(f"'{arg_value}'")

    # Update extends and include statements
    for tag in ["extends", "include"]:
        for statement in file.search(f"{{% {tag} "):
            source = statement.source.strip()
            if source[-1] != "'":
                if source[-1] == '"':
                    source = source[:-1] + "'"
                else:
                    source += "'"
                new_source = f"{{% {tag} '{source[len(f'{{% {tag} ') :]}"
                statement.edit(new_source)

    # Update render_template calls
    for func_call in file.function_calls:
        if func_call.name == "render_template":
            func_call.set_name("Jinja2Templates(directory='templates').TemplateResponse")
            if len(func_call.args) > 1:
                context_arg = ", ".join(f"{arg.name}={arg.value}" for arg in func_call.args[1:])
                func_call.set_kwarg("context", f"{'{'}{context_arg}{'}'}")
            func_call.set_kwarg("request", "request")


@codebase.function("flask_to_fastapi_migration")
def run():
    """Main function to run the Flask to FastAPI migration"""
    print("🚀 Starting Flask to FastAPI migration...\n")

    # Process each file in the target directory
    for file in codebase.files:
        if TARGET_DIR in file.filepath:
            # Step 1: Update Flask imports and initialization
            print("\n📝 Step 1: Updating Flask imports and initialization...")
            update_flask_imports_and_init(file)

            # Step 2: Update route decorators
            print("\n📝 Step 2: Converting route decorators...")
            update_route_decorators(file)

            # Step 3: Setup static file handling
            print("\n📝 Step 3: Setting up static file handling...")
            setup_static_files(file)

            # Step 4: Update Jinja2 template handling
            print("\n📝 Step 4: Updating Jinja2 template handling...")
            update_jinja2_syntax(file)

    # Commit all changes
    print("\n💾 Committing changes...")
    codebase.commit()
    print("✅ Flask to FastAPI migration completed successfully!")


if __name__ == "__main__":
    codebase = Codebase("./")

    run()
