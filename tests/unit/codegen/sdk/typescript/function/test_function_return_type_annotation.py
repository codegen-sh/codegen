from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_return_type_annotation(tmpdir) -> None:
    # language=typescript
    content = """
function getValue(value: number | string): number | string {
  return value;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 1
        symbol = file.get_function("getValue")
        assert symbol.return_type.source == "number | string"


def test_return_type_new_line(tmpdir) -> None:
    # language=typescript
    content = """
function func<Type, Obj>(
  val: Type,
): Array<keyof Obj> {
  return Object.keys(val) as unknown as Array<keyof Obj>
}

export function fn<T, U, V>(
  arg: T,
  arr: Array<U | V>,
): V {
  if (
    arr.length === 0 ||
    arr.every((item) => item.prop.length === 0)
  ) {
    return { ...obj }
  }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        # Iterate over all files in the codebase
        for file in codebase.files:
            # Iterate over all functions in the file
            for func in file.functions:
                # Check if the return type is of the form Array<T>
                if (return_type := func.return_type) and isinstance(return_type, GenericType) and return_type.name == "Array":
                    # Array<..> syntax only allows one type argument
                    func.set_return_type(f"({return_type.parameters[0].source})[]")

                # Process each parameter in the function
                for param in func.parameters:
                    if (param_type := param.type) and isinstance(param_type, GenericType) and param_type.name == "Array":
                        # Array<..> syntax only allows one type argument
                        param_type.edit(f"({param_type.parameters[0].source})[]")

    # language=typescript
    assert (
        file.content
        == """
function func<Type, Obj>(
  val: Type,
): (keyof Obj)[] {
  return Object.keys(val) as unknown as Array<keyof Obj>
}

export function fn<T, U, V>(
  arg: T,
  arr: (U | V)[],
): V {
  if (
    arr.length === 0 ||
    arr.every((item) => item.prop.length === 0)
  ) {
    return { ...obj }
  }
}
    """
    )
