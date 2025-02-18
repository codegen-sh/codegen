from itertools import chain
from pathlib import Path

import tomlkit
from termcolor import colored

from codegen.git.utils.file_utils import split_git_path
from codegen.sdk.code_generation.current_code_codebase import get_documented_objects
from codegen.shared.decorators.docs import DocumentedObject

EXTERNAL_IMPORTS = """
import os
import re
from pathlib import Path
import networkx as nx
import plotly
""".strip()
CODEGEN_IMPORTS = """
from codegen.git.models.codemod_context import CodemodContext
from codegen.git.models.github_named_user_context import GithubNamedUserContext
from codegen.git.models.pr_options import PROptions
from codegen.git.models.pr_part_context import PRPartContext
from codegen.git.models.pull_request_context import PullRequestContext
"""
# TODO: these should also be made public (i.e. included in the docs site)
GS_PRIVATE_IMPORTS = """
from codegen.shared.exceptions.control_flow import StopCodemodException
""".strip()

IMPORT_STRING_TEMPLATE = """
# External imports
{external_imports}

# GraphSitter imports (private)
{codegen_imports}
{gs_private_imports}

# GraphSitter imports (public)
{gs_public_imports}
""".strip()

IMPORT_FILE_TEMPLATE = (
    '''
# This file is auto-generated, do not modify manually. Edit this in src/codegen/gscli/generate/runner_imports.py.
def get_generated_imports():
    return """
{import_str}
"""
'''.strip()
    + "\n"
)


def fix_ruff_imports(objects: list[DocumentedObject]):
    root, _ = split_git_path(str(Path(__file__)))
    to_add = []
    for obj in objects:
        to_add.append(f"{obj.module}.{obj.name}")
    generics = tomlkit.array()
    for val in dict.fromkeys(to_add):
        generics.add_line(val, indent="  ")
    generics.add_line(indent="")
    config = Path(root) / "ruff.toml"
    toml_config = tomlkit.parse(config.read_text())
    toml_config["lint"]["pyflakes"]["extend-generics"] = generics
    config.write_text(tomlkit.dumps(toml_config))


def get_runner_imports(include_codegen=True, include_private_imports: bool = True) -> str:
    # get the imports from the apidoc, py_apidoc, and ts_apidoc
    gs_objects = get_documented_objects()
    gs_public_objects = list(chain(gs_objects["apidoc"], gs_objects["py_apidoc"], gs_objects["ts_apidoc"]))
    fix_ruff_imports(gs_public_objects)
    gs_public_imports = {f"from {obj.module} import {obj.name}" for obj in gs_public_objects}

    # construct import string with all imports
    ret = IMPORT_STRING_TEMPLATE.format(
        codegen_imports=CODEGEN_IMPORTS if include_codegen else "",
        external_imports=EXTERNAL_IMPORTS,
        gs_private_imports=GS_PRIVATE_IMPORTS if include_private_imports else "",
        gs_public_imports="\n".join(sorted(gs_public_imports)),
    )
    return ret


EXPORT_TEMPLATE = """
__all__ = [
    "__version__",
    "__version_tuple__",
    "StopCodemodException",
{modules}
]
""".strip()


def generate_exported_modules() -> str:
    gs_objects = get_documented_objects()
    gs_public_objects = list(chain(gs_objects["apidoc"], gs_objects["py_apidoc"], gs_objects["ts_apidoc"]))
    return EXPORT_TEMPLATE.format(modules=",\n".join(dict.fromkeys('    "' + obj.name + '"' for obj in sorted(gs_public_objects, key=lambda x: x.name))))


def _generate_runner_imports(imports_file: str) -> None:
    print(colored(f"Generating runner imports string in {imports_file}", "green"))

    import_str = get_runner_imports()
    # write the imports to the file
    with open(imports_file, "w") as f:
        f.write(IMPORT_FILE_TEMPLATE.format(import_str=import_str))
