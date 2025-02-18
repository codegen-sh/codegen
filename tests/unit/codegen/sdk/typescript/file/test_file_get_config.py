from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


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
    { "path": "./shared/app/src" }
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
        parent_file: TSFile = codebase.get_file(parent_file_name)
        child_file: TSFile = codebase.get_file(child_file_name)
        sibling_file: TSFile = codebase.get_file(sibling_file_name)

        assert parent_file.get_config().config_file.name == codebase.get_file(root_config_name).name
        assert child_file.get_config().config_file.name == codebase.get_file(config_name).name
        assert sibling_file.get_config().config_file.name == codebase.get_file(root_config_name).name
