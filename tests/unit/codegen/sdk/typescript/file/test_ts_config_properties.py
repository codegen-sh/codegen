from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.ts_config import TSConfig


def test_file_get_config(tmpdir) -> None:
    parent_file_name = "shared/app/src/test.ts"
    child_file_name = "modules/app/src/test.ts"
    sibling_file_name = "modules/tests/src/test.ts"

    root_config_name = "tsconfig.json"
    # language=typescript
    root_config_content = """
{
  "extends": "./tsconfig.base.json",
}
    """

    parent_config_name = "tsconfig.base.json"
    # language=typescript
    parent_config_content = """
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@shared/*": ["./shared/*"],
      "@utils/*": ["./utils/*"],
      "@models/*": ["./models/*"]
    }
  },
  "exclude": ["node_modules", "dist"],
  "references": [
    { "path": "./shared/app" }
  ]
}
    """
    config_name = "modules/app/tsconfig.json"
    # language=typescript
    config_content = """
{
  "extends": "../../tsconfig.base",
  "compilerOptions": {
    "outDir": "dist",
    "paths": {
      "@codegen/test/*": ["../*"]
    }
  },
  "include": ["src/**/*", "testHelpers"],
  "references": [
    { "path": "../tests" },
    { "path": "../../shared/app" }
  ]
}
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={parent_file_name: "", child_file_name: "", sibling_file_name: "", config_name: config_content, root_config_name: root_config_content, parent_config_name: parent_config_content},
        commit=True,
    ) as codebase:
        config: TSConfig = codebase.ctx.config_parser.get_config(config_name)
        root_config: TSConfig = codebase.ctx.config_parser.get_config(root_config_name)
        parent_config: TSConfig = codebase.ctx.config_parser.get_config(parent_config_name)

        assert config is not None
        assert config.config_file.filepath == config_name
        assert root_config is not None
        assert root_config.config_file.filepath == root_config_name
        assert parent_config is not None
        assert parent_config.config_file.filepath == parent_config_name

        assert config.base_config.config_file.filepath == parent_config_name
        assert root_config.base_config.config_file.filepath == parent_config_name
        assert parent_config.base_config is None

        assert config.paths == {
            "@codegen/test/*": ["../*"],
            "@shared/*": ["./shared/*"],
            "@utils/*": ["./utils/*"],
            "@models/*": ["./models/*"],
        }
        assert set(config.references) == {
            ("../tests", codebase.get_directory("modules/tests")),
            ("../../shared/app", codebase.get_directory("shared/app")),
        }
        assert config.path_import_aliases == {
            "@codegen/test": ["modules"],
            "@shared": ["shared"],
            "@utils": ["utils"],
            "@models": ["models"],
        }
        assert config.reference_import_aliases == {
            "tests": ["modules/tests"],
            "shared/app": ["shared/app"],
            "app": ["shared/app"],
        }
        assert root_config.paths == {
            "@shared/*": ["./shared/*"],
            "@utils/*": ["./utils/*"],
            "@models/*": ["./models/*"],
        }
        assert set(root_config.references) == set()
        assert root_config.path_import_aliases == {
            "@shared": ["shared"],
            "@utils": ["utils"],
            "@models": ["models"],
        }
        assert root_config.reference_import_aliases == {
            "app": ["shared/app"],
            "shared/app": ["shared/app"],
        }
        assert parent_config.paths == {
            "@shared/*": ["./shared/*"],
            "@utils/*": ["./utils/*"],
            "@models/*": ["./models/*"],
        }
        assert set(parent_config.references) == {
            ("./shared/app", codebase.get_directory("shared/app")),
        }
        assert parent_config.path_import_aliases == {
            "@shared": ["shared"],
            "@utils": ["utils"],
            "@models": ["models"],
        }
        assert parent_config.reference_import_aliases == {
            "app": ["shared/app"],
            "shared/app": ["shared/app"],
        }
