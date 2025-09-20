DEFAULT_CODEMOD = '''import codegen
from codegen.sdk.core.codebase import Codebase


@codegen.function("{name}")
def run(codebase: Codebase):
    """Add a description of what this codemod does."""
    # Add your code here
    print('Total files: ', len(codebase.files))
    print('Total functions: ', len(codebase.functions))
    print('Total imports: ', len(codebase.imports))


if __name__ == "__main__":
    print('Parsing codebase...')
    codebase = Codebase("./")

    print('Running...')
    run(codebase)
'''
