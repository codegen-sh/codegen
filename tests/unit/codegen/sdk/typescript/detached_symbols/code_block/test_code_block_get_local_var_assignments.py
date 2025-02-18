from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_and_rename_get_local_var_assignments(tmpdir) -> None:
    # language=typescript
    content = """
function funcC(varA: any): any {
    return varA;
}

function funcB(varA: any): any {
    return varA;
}

function funcA(paramId: any): any {
    const varA = paramId;
    const varB = "b";
    const idA = varA.propA;
    const returnA = funcC(varA);
    const varC = funcB(varB);
    const someObject = {
        id: varB.propA ? varB.propA : null,
        status: "OPEN",
    };
    return varA;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        for function in codebase.functions:
            matching_vars = function.code_block.get_local_var_assignments("var", fuzzy_match=True)
            for local_var in matching_vars:
                local_var.rename("newVar")

    assert len(list(codebase.symbols)) > 0
    file = codebase.get_file("test.ts")
    assert "newVar" in file.content
