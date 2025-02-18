from codegen.sdk.core.codebase import Codebase
from codegen.sdk.writer_decorators import canonical
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill


@skill(
    canonical=True,
    prompt="""Generate a TypeScript codemod that processes a codebase to split large files. The codemod should define constants for maximum file length (500 lines)
and maximum symbol length (50 lines). It should iterate through all files in the codebase, checking if a file exceeds the maximum length. If a file
has more than 3 symbols that exceed the maximum symbol length, create a new directory for the file (removing the .ts extension) and move each long
symbol into its own new file within that directory. Ensure to add a back edge to the original file for each moved symbol.""",
    uid="b5bbec91-5bfe-4b4b-b62e-0a1ec94089b5",
)
@canonical
class SplitLargeFiles(Codemod, Skill):
    """This codemod splits all large files."""

    language = ProgrammingLanguage.TYPESCRIPT

    @skill_impl(test_cases=[], skip_test=True, language=ProgrammingLanguage.TYPESCRIPT)
    def execute(self, codebase: Codebase):
        # Define constants for maximum lengths
        MAX_FILE_LENGTH = 500
        MAX_SYMBOL_LENGTH = 50

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Check if the file has more than the maximum file length
            if len(file.content.splitlines()) > MAX_FILE_LENGTH:
                # Count the number of symbols with more than the maximum symbol length
                long_symbols_count = sum(1 for symbol in file.symbols if len(symbol.source.splitlines()) > MAX_SYMBOL_LENGTH)
                # Proceed if there are more than 3 long symbols
                if long_symbols_count > 3:
                    # Create a new directory for the file
                    dir_name = file.filepath.replace(".ts", "")
                    codebase.create_directory(dir_name, exist_ok=True)
                    # Iterate over symbols in the file
                    for symbol in file.symbols:
                        # Skip any symbol named 'Space'
                        if len(symbol.source.splitlines()) > MAX_SYMBOL_LENGTH:
                            # Create a new file for the symbol
                            new_file = codebase.create_file(f"{dir_name}/{symbol.name}.ts", sync=False)
                            # Move the symbol to the new file
                            symbol.move_to_file(new_file)
                            # Add a back edge to the original file
                            file.add_symbol_import(symbol)
