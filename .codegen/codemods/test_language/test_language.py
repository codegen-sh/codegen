import codegen
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


@codegen.function("test-language", subdirectories=["src/codegen/cli"], language=ProgrammingLanguage.PYTHON)
def run(codebase: Codebase):
    file = codebase.get_file("src/codegen/cli/errors.py")
    print(f"File: {file.path}")
    for s in file.symbols:
        print(s.name)


if __name__ == "__main__":
    print("Parsing codebase...")
    codebase = Codebase("./")

    print("Running...")
    run(codebase)
