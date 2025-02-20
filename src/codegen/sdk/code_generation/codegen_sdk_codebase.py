import os.path

from codegen.sdk.code_generation.current_code_codebase import get_codegen_codebase_base_path, get_current_code_codebase
from codegen.sdk.core.codebase import Codebase
from codegen.shared.configs.models.codebase import DefaultCodebaseConfig


def get_codegen_sdk_subdirectories() -> list[str]:
    base = get_codegen_codebase_base_path()
    return [os.path.join(base, "codegen/sdk"), os.path.join(base, "codemods")]


def get_codegen_sdk_codebase() -> Codebase:
    """Grabs a Codebase w/ GraphSitter content. Responsible for figuring out where it is, e.g. in Modal or local"""
    codebase = get_current_code_codebase(DefaultCodebaseConfig, subdirectories=get_codegen_sdk_subdirectories())
    return codebase
