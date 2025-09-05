import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def update_init_file(file: Path) -> None:
    path = Path(__file__).parent.parent
    sys.path.append(str(path))
    from codegen.sdk.gscli.generate.runner_imports import generate_exported_modules, get_runner_imports

    content = file.read_text()
    content = get_runner_imports(include_codegen=False) + "\n" + content + "\n" + generate_exported_modules()
    file.write_text(content)


class SpecialBuildHook(BuildHookInterface):
    PLUGIN_NAME = "codegen_build"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        file = Path(self.root) / "src" / "graph_sitter" / "__init__.py"
        update_init_file(file)
        build_data["artifacts"].append(f"/{file}")
