import os

import codegen
from codegen.sdk.code_generation.current_code_codebase import get_graphsitter_repo_path
from codegen.sdk.core.codebase import Codebase


def test_codegen_imports():
    # Test decorated function
    @codegen.function(name="sample_codemod")
    def run(codebase):
        pass

    # Test class
    cls = codegen.Function
    assert cls is not None
    os.chdir(get_graphsitter_repo_path())  # TODO: CG-10643
    codebase = Codebase("./")
    assert codebase is not None
