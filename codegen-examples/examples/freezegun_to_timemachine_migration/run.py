import codegen
from codegen import Codebase


@codegen.function("freezegun-to-timemachine")
def run(codebase: Codebase):
    """Convert FreezeGun usage to TimeMachine in test files.

    This script:
    1. Identifies test files using FreezeGun.
    2. Updates imports from FreezeGun to TimeMachine.
    3. Modifies function calls to include necessary parameters.
    """
    print("🚀 Starting FreezeGun to TimeMachine conversion...")

    for file in codebase.files:
        if "tests" not in file.filepath:
            continue
        print(f"📝 Processing: {file.filepath}")

        # Update imports
        for imp in file.imports:
            if imp.symbol_name and "freezegun" in imp.source:
                if imp.name == "freeze_time":
                    # required due to Codegen limitations
                    imp.edit("from time_machine import travel")
                else:
                    imp.set_import_module("time_machine")

        # Find all function calls in the file
        for fcall in file.function_calls:
            # Skip if not a freeze_time call
            if "freeze_time" not in fcall.source:
                continue

            # Get original source and prepare new source
            new_source = fcall.source

            # Add tick parameter if not present
            if not fcall.get_arg_by_parameter_name("tick"):
                if new_source.endswith(")"):
                    new_source = new_source[:-1]
                    if not new_source.endswith("("):
                        new_source += ","
                    new_source += " tick=False)"

            # Replace freeze_time with travel
            if "." in new_source:
                new_source = new_source.replace("freeze_time", "travel").replace("freezegun", "time_machine")
            else:
                new_source = "travel" + new_source[len("freeze_time") :]

            # Make single edit with complete changes
            fcall.edit(new_source)

    codebase.commit()
    print("✅ FreezeGun to TimeMachine conversion completed successfully!")


if __name__ == "__main__":
    codebase = Codebase.from_repo("getmoto/moto", commit="786a8ada7ed0c7f9d8b04d49f24596865e4b7901", language="python")
    run(codebase)
