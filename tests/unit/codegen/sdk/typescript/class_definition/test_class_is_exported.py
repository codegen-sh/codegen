from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_export_function_is_exported(tmpdir) -> None:
    file = """
export class ExportedClass {
  greeting: string;

  constructor(message: string) {
    this.greeting = message;
  }

  greet() {
    return "Hello, " + this.greeting;
  }
}

class NotExportedClass {
  greeting: string;

  constructor(message: string) {
    this.greeting = message;
  }

  greet() {
    return "Hello, " + this.greeting;
  }
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        exported_class = file.get_symbol("ExportedClass")
        assert exported_class.is_exported

        not_exported_class = file.get_symbol("NotExportedClass")
        assert not not_exported_class.is_exported
