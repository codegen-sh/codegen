import codegen
from codegen import Codebase


@codegen.function("dict-to-pydantic-schema")
def run(codebase: Codebase):
    """Convert dictionary literals to Pydantic models in a Python codebase.

    This codemod:
    1. Finds all dictionary literals in global variables and class attributes
    2. Creates corresponding Pydantic models
    3. Updates the assignments to use the new models
    4. Adds necessary Pydantic imports
    """
    # Track statistics
    files_modified = 0
    models_created = 0

    # Iterate through all files in the codebase
    for file in codebase.files:
        needs_imports = False
        file_modified = False

        # Look for dictionary assignments in global variables
        for global_var in file.global_vars:
            try:
                if "{" in global_var.source and "}" in global_var.source:
                    dict_content = global_var.value.source.strip("{}")
                    if not dict_content.strip():
                        continue

                    # Convert dict to Pydantic model
                    class_name = global_var.name.title() + "Schema"
                    model_def = f"""class {class_name}(BaseModel):
    {dict_content.replace(",", "\n    ")}"""

                    print(f"\nConverting '{global_var.name}' to schema")
                    print("\nOriginal code:")
                    print(global_var.source)
                    print("\nNew code:")
                    print(model_def)
                    print(f"{class_name}(**{global_var.value.source})")
                    print("-" * 50)

                    # Insert model and update assignment
                    global_var.insert_before(model_def + "\n\n")
                    global_var.set_value(f"{class_name}(**{global_var.value.source})")
                    needs_imports = True
                    models_created += 1
                    file_modified = True
            except Exception as e:
                print(f"Error processing global variable {global_var.name}: {str(e)}")

        # Look for dictionary assignments in class attributes
        for cls in file.classes:
            for attr in cls.attributes:
                try:
                    if "{" in attr.source and "}" in attr.source:
                        dict_content = attr.value.source.strip("{}")
                        if not dict_content.strip():
                            continue

                        # Convert dict to Pydantic model
                        class_name = attr.name.title() + "Schema"
                        model_def = f"""class {class_name}(BaseModel):
    {dict_content.replace(",", "\n    ")}"""

                        print(f"\nConverting'{attr.name}' to schema")
                        print("\nOriginal code:")
                        print(attr.source)
                        print("\nNew code:")
                        print(model_def)
                        print(f"{class_name}(**{attr.value.source})")
                        print("-" * 50)

                        # Insert model and update attribute
                        cls.insert_before(model_def + "\n\n")
                        attr.set_value(f"{class_name}(**{attr.value.source})")
                        needs_imports = True
                        models_created += 1
                        file_modified = True
                except Exception as e:
                    print(f"Error processing attribute {attr.name} in class {cls.name}: {str(e)}")

        # Add imports if needed
        if needs_imports:
            file.add_import_from_import_string("from pydantic import BaseModel")

        if file_modified:
            files_modified += 1

    print("\nModification complete:")
    print(f"Files modified: {files_modified}")
    print(f"Schemas created: {models_created}")


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("modal-labs/modal-client", commit="81941c24897889a2ff2f627c693fa734967e693c", language="python")

    print("Running codemod...")
    run(codebase)
