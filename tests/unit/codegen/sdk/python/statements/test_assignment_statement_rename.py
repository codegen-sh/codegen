from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_rename_local_variables_exact_match_no_change(tmpdir) -> None:
    # language=python
    content = """
def helper_func_a(param_a):
    return param_a
def helper_func_b(param_a):
    return param_a
def main_func(input_id):
    var_a = input_id
    var_b = "b"
    id_a = var_a.attr_a
    result_a = helper_func_a(param_a = var_a)
    var_c = (
        helper_func_b(
            param_a=var_b
        )
    )
    config = {
            "id": var_b.attr_a if var_b else None
    }
    return var_a
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        for function in codebase.functions:
            local_vars = function.code_block.get_local_var_assignments("var", fuzzy_match=False)
            for local_var in local_vars:
                local_var.rename("renamed_var")

    assert codebase.get_file("file.py").content == content


def test_rename_local_variables_exact_match_has_change(tmpdir) -> None:
    # language=python
    content = """
def helper_func_a(param_a):
    return param_a
def helper_func_b(param_a):
    return param_a
def main_func(input_id):
    var_a = input_id
    var_b = "b"
    id_a = var_a.attr_a
    result_a = helper_func_a(param_a = var_a)
    var_c = (
        helper_func_b(
            param_a=var_b
        )
    )
    config = {
            "id": var_b.attr_a if var_b else None
    }
    return var_a
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        for function in codebase.functions:
            local_vars = function.code_block.get_local_var_assignments("var_a", fuzzy_match=False)
            for local_var in local_vars:
                local_var.rename("renamed_var_a")

    # language=python
    expected_content = """
def helper_func_a(param_a):
    return param_a
def helper_func_b(param_a):
    return param_a
def main_func(input_id):
    renamed_var_a = input_id
    var_b = "b"
    id_a = renamed_var_a.attr_a
    result_a = helper_func_a(param_a = renamed_var_a)
    var_c = (
        helper_func_b(
            param_a=var_b
        )
    )
    config = {
            "id": var_b.attr_a if var_b else None
    }
    return renamed_var_a
    """
    assert codebase.get_file("file.py").content == expected_content


def test_rename_local_variable_fuzzy_match(tmpdir) -> None:
    # language=python
    content = """
def helper_func_a(param_a):
    return param_a
def helper_func_b(param_a):
    return param_a
def main_func(input_id):
    var_a = input_id
    var_b = "b"
    id_a = var_a.attr_a
    result_a = helper_func_a(param_a = var_a)
    var_c = (
        helper_func_b(
            param_a=var_b
        )
    )
    config = {
            "id": var_b.attr_a if var_b else None
    }
    return var_a
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        for function in codebase.functions:
            local_vars = function.code_block.get_local_var_assignments("var", fuzzy_match=True)
            for local_var in local_vars:
                local_var.rename(local_var.name.replace("var", "renamed_var"))

    # language=python
    expected_content = """
def helper_func_a(param_a):
    return param_a
def helper_func_b(param_a):
    return param_a
def main_func(input_id):
    renamed_var_a = input_id
    renamed_var_b = "b"
    id_a = renamed_var_a.attr_a
    result_a = helper_func_a(param_a = renamed_var_a)
    renamed_var_c = (
        helper_func_b(
            param_a=renamed_var_b
        )
    )
    config = {
            "id": renamed_var_b.attr_a if renamed_var_b else None
    }
    return renamed_var_a
    """
    assert codebase.get_file("file.py").content == expected_content
