import codegen
from codegen import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute


@codegen.function("sqlalchemy-1.4-to-2.0")
def run(codebase: Codebase):
    """
    Convert SQLAlchemy 1.4 codebases to 2.0.
    """
    files_modified = 0
    functions_modified = 0

    print("\nStarting SQLAlchemy 1.4 to 2.0 migration...")

    for file in codebase.files:
        file_modified = False
        print(f"\nProcessing file: {file.path}")

        # Step 1: Convert Query to Select
        for call in file.function_calls:
            if call.name == "query":
                chain = call
                while chain.parent and isinstance(chain.parent, ChainedAttribute):
                    chain = chain.parent

                original_code = chain.source
                new_query = chain.source.replace("query(", "select(")
                if "filter(" in new_query:
                    new_query = new_query.replace(".filter(", ".where(")
                if "filter_by(" in new_query:
                    model = call.args[0].value
                    conditions = chain.source.split("filter_by(")[1].split(")")[0]
                    new_conditions = [f"{model}.{cond.strip().replace('=', ' == ')}" for cond in conditions.split(",")]
                    new_query = f".where({' & '.join(new_conditions)})"
                if "execute" not in chain.parent.source:
                    new_query = f"execute({new_query}).scalars()"

                print(f"\nConverting query in {file.path}:\n")
                print("Original code:")
                print(original_code)
                print("\nNew code:")
                print(new_query)
                print("-" * 50)

                chain.edit(new_query)
                file_modified = True
                functions_modified += 1

        # Step 2: Modernize ORM Relationships
        for cls in file.classes:
            for attr in cls.attributes:
                if isinstance(attr.value, FunctionCall) and attr.value.name == "relationship":
                    if "lazy=" not in attr.value.source:
                        original_rel = attr.value.source
                        new_rel = original_rel + ', lazy="select"'
                        if "backref" in new_rel:
                            new_rel = new_rel.replace("backref", "back_populates")

                        print(f"\nUpdating relationship in class {cls.name}:\n")
                        print("Original code:")
                        print(original_rel)
                        print("\nNew code:")
                        print(new_rel)
                        print("-" * 50)

                        attr.value.edit(new_rel)
                        file_modified = True
                        functions_modified += 1

        # Step 3: Convert Column Definitions to Type Annotations
        for cls in file.classes:
            for attr in cls.attributes:
                if "Column(" in attr.source:
                    original_attr = attr.source
                    new_attr = original_attr.replace("Column", "mapped_column")
                    type_hint = "Mapped" + original_attr.split("= Column")[1]
                    new_attr = f"{attr.name}: {type_hint}"

                    print(f"\nUpdating column definition in class {cls.name}:\n")
                    print("Original code:")
                    print(original_attr)
                    print("\nNew code:")
                    print(new_attr)
                    print("-" * 50)

                    attr.edit(new_attr)
                    file_modified = True
                    functions_modified += 1

        if file_modified:
            files_modified += 1

    print("\nMigration complete:")
    print(f"Files modified: {files_modified}")
    print(f"Functions modified: {functions_modified}")


if __name__ == "__main__":
    repo_path = "./input_repo"
    print("Initializing codebase...")
    codebase = Codebase(repo_path)
    print("Running SQLAlchemy 1.4 to 2.0 codemod...")
    run(codebase)
