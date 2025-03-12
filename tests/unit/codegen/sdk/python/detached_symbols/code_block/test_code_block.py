import re
from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.python import PyFile


def test_code_block(tmpdir) -> None:
    # language=python
    content = """
GLOBAL_VAR = 1

def sum_even_numbers(numbers, threshold=10):
    '''
    Calculates the sum of even numbers in an array.

    :param numbers: The array of numbers.
    :type numbers: list[int]
    :param threshold: The optional threshold value. Default is 10.
    :type threshold: int
    :return: The sum of even numbers or -1 if the sum exceeds the threshold.
    :rtype: int
    '''
    # Variable declarations
    sum_val = 0
    is_threshold_reached = lambda: sum_val > threshold

    is_threshold_reached()

    # For loop
    for num in numbers:
        # Nested comment
        print(f"Skipping odd number: {num}")
        if num % 2 == 0:
            return sum_val

    # While loop
    while sum_val < threshold:
        sum_val += 1

    if is_threshold_reached():
        return sum_val
    return 0

sum_even_numbers([1, 2, 3, 4, 5])
        """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        statements = file.get_function("sum_even_numbers").code_block.get_statements()

        assert len(statements) == 17
        statement_types = [(x.index, x.statement_type, x.parent.level) for x in statements]
        assert statement_types == [
            (0, StatementType.COMMENT, 1),
            (1, StatementType.COMMENT, 1),
            (2, StatementType.ASSIGNMENT, 1),
            (3, StatementType.ASSIGNMENT, 1),
            (4, StatementType.EXPRESSION_STATEMENT, 1),
            (5, StatementType.COMMENT, 1),
            (6, StatementType.FOR_LOOP_STATEMENT, 1),
            (0, StatementType.COMMENT, 2),
            (1, StatementType.EXPRESSION_STATEMENT, 2),
            (2, StatementType.IF_BLOCK_STATEMENT, 2),
            (0, StatementType.RETURN_STATEMENT, 3),
            (7, StatementType.COMMENT, 1),
            (8, StatementType.WHILE_STATEMENT, 1),
            (0, StatementType.ASSIGNMENT, 2),
            (9, StatementType.IF_BLOCK_STATEMENT, 1),
            (0, StatementType.RETURN_STATEMENT, 2),
            (10, StatementType.RETURN_STATEMENT, 1),
        ]


def test_code_block_local_vars(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
class MyClass:
    attr1: str
    attr2: str

def foo(x: int, y: str) -> MyClass:
    z = str(x) + y
    obj = MyClass()
    obj.attr1 = z
    if a_condition := True:
        a = a_condition
    else:
        a_else = a_condition | False
    for i in range(10):
        b = 2
    while obj.attr2 == "some random string" + z:
        c = 3
    try:
        d = 1
    except:
        e = 1
    return obj
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={file_name: content},
    ) as codebase:
        file = codebase.get_file(file_name)
        local_var_assignments = file.get_function("foo").code_block.local_var_assignments

        assert len(local_var_assignments) == 8
        assert [v.name for v in local_var_assignments] == [
            "z",
            "obj",
            "a",
            "a_else",
            "b",
            "c",
            "d",
            "e",
        ]


def test_code_block_get_local_var(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
class MyClass:
    attr1: str
    attr2: str

def foo(x: int, y: str) -> MyClass:
    z = str(x) + y
    obj = MyClass()
    obj.attr1 = z
    return obj
    """
    with get_codebase_session(tmpdir=tmpdir, files={file_name: content}) as mock_codebase:
        file = mock_codebase.get_file(file_name)
        func = file.get_function("foo")

        z = func.code_block.get_local_var_assignment("z")
        assert z.name == "z"
        obj = func.code_block.get_local_var_assignment("obj")
        assert obj.name == "obj"


def test_code_block_get_variable_usages_in_assignments(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
class MyClass:
    attr1: str
    attr2: str

def foo(x: int, y: str) -> MyClass:
    z = str(x) + y
    obj = MyClass()
    random = "i'm an unused var!"
    obj.attr1 = z.obj
    return obj
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={file_name: content},
    ) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        z = code_block.get_local_var_assignment("z")
        z_name = z.name
        obj = code_block.get_local_var_assignment("obj")
        obj_name = obj.name
        obj_usage_statement = code_block.statements[3]
        assert obj_usage_statement.source == "obj.attr1 = z.obj"

        z_usages = obj_usage_statement.get_variable_usages(z.name)
        assert len(z_usages) == 1
        assert z_usages[0].source == "z"
        z_usages[0].edit("renamed_attribute")
    assert "obj.attr1 = renamed_attribute.obj" in file.content

    code_block = file.get_function("foo").code_block
    obj_usage_statement = code_block.statements[3]
    obj_usages = obj_usage_statement.get_variable_usages(obj_name)
    assert len(obj_usages) == 1
    assert obj_usages[0].source == "obj"
    obj_usages[0].edit("renamed_obj")
    codebase.ctx.commit_transactions()
    assert "renamed_obj.attr1 = renamed_attribute.obj" in file.content

    random = code_block.get_local_var_assignment("random")
    assert len(random.get_variable_usages(obj_name)) == 0
    assert len(random.get_variable_usages(z_name)) == 0


def test_code_block_get_variable_usages_in_statements(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
class MyClass:
    attr1: str
    attr2: str

def foo(x: int, y: str) -> MyClass:
    z = str(x) + y
    obj = MyClass()
    if z == "some random string":
        obj.attr1 = z
    for i in range(10):
        obj.attr2 += str(i)
    while obj.attr2 == "some random string" + z:
        obj.z += z
    return obj
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={file_name: content},
    ) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        z = code_block.get_local_var_assignment("z")
        z_name = z.name
        obj = code_block.get_local_var_assignment("obj")
        if_statement = code_block.statements[2]

        z_usages = if_statement.get_variable_usages(z.name)
        obj_usages = if_statement.get_variable_usages(obj.name)
        assert len(z_usages) == 2
        assert len(obj_usages) == 1
        z_usages[0].edit("new_z")
        z_usages[1].edit("new_z")
        obj_usages[0].edit("new_obj")
        all_z_usages = code_block.get_variable_usages(z_name)
        assert len(all_z_usages) == 4
    assert 'if new_z == "some random string":\n        new_obj.attr1 = new_z' in file.content


def test_code_block_get_variable_usage_func_call(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
def bar(x: int, y: int, z: int) -> int:
    return x + y + z

def foo(x: int, y: str) -> MyClass:
    z = str(x) + y
    obj = MyClass()
    obj.attr1 = bar(x=3, y=int(y), z=z)
    if True:
        a = 1
    for i in range(10):
        b = 2
    while obj.attr2 == "some random string" + z:
        c = 3
    return obj
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.PYTHON,
        files={file_name: content},
    ) as codebase:
        file = codebase.get_file(file_name)
        func = file.get_function("foo")
        code_block = func.code_block

        x_usages = code_block.get_variable_usages("x")
        y_usages = code_block.get_variable_usages("y")
        z_usages = code_block.get_variable_usages("z")
        assert len(x_usages) == 1
        assert len(y_usages) == 2
        assert len(z_usages) == 2

        for x_usage in x_usages:
            x_usage.edit("new_x")
        for y_usage in y_usages:
            y_usage.edit("new_y")
        code_block.get_local_var_assignment("z").rename("new_z")

    # language=python
    expected_content = """
def bar(x: int, y: int, z: int) -> int:
    return x + y + z

def foo(x: int, y: str) -> MyClass:
    new_z = str(new_x) + new_y
    obj = MyClass()
    obj.attr1 = bar(x=3, y=int(new_y), z=new_z)
    if True:
        a = 1
    for i in range(10):
        b = 2
    while obj.attr2 == "some random string" + new_z:
        c = 3
    return obj
    """
    assert file.content == expected_content


def test_get_local_variable_usages(tmpdir) -> None:
    file_name = "test.py"
    # language=python
    content = """
    def bar(x: int, y: int, z: int) -> int:
        return x + y + z

    def foo(x: int, y: str) -> MyClass:
        z = str(x) + y
        obj = MyClass()
        obj.attr1 = bar(x=3, y=int(y), z=z)
        if True:
            a = 1
        for i in range(10):
            b = 2
        while obj.attr2 == "some random string" + z:
            c = 3
        return obj
        """
    with get_codebase_session(tmpdir=tmpdir, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)

        foo = file.get_function("foo")
        z = foo.code_block.get_local_var_assignment("z")
        z_usages = z.local_usages
        for z_usage in reversed(z_usages):
            z_usage.edit("new_z")
        assert len(z_usages) == 2


def test_code_block_get_comment(tmpdir) -> None:
    # language=python
    content = """
def example_function(param1: str, param2: int) -> None:
    x = 1  # comment to remove
    y = 2
    z = x + y
    for i in range(10):
        print(i)
    """
    comment_text = "# comment to remove"
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        func = file.get_function("example_function")

        # Test comment removal
        comment = func.code_block.get_comment(comment_text)
        comment.remove()

        # Test finding variable usages
        x_usages = func.code_block.find("x")
        assert len(x_usages) == 2

        # Test regex search for whole word matches
        whole_word_x = func.code_block.search(r"\b(?<!\.)\bx\b(?!\.)")
        assert len(whole_word_x) == 2

    assert comment_text not in file.content


def test_reduce_proxy_variable(tmpdir) -> None:
    # language=python
    content = """
def my_db_query(
    parent: Parent, to_record: Record
) -> None:
    from_record = (
        parent.proxy
    )  # added by Codegen
    from_logs: list[Log] = (
        db.session.execute(
            select(Log).where(
                Log.proxy_id == from_record.id
            )
        )
    )
    x = from_record
    y = from_record.parent
    for log in from_logs:
        log.proxy_id = to_record.id
    """
    WRAP_REDUCE_MIGRATION_STRING_IDENTIFIER = "# added by Codegen"
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        func = file.get_function("my_db_query")
        code_block = func.code_block

        # Step 2: Remove the proxy variable declaration + comment
        codegen_comment = code_block.get_comment(WRAP_REDUCE_MIGRATION_STRING_IDENTIFIER)
        comment_index = code_block.statements.index(codegen_comment)
        proxy_var = code_block.statements[comment_index - 1]
        codegen_comment.remove()
        proxy_var.remove()

        # Step 3: Replace "parent.proxy.<field>" with "parent.<field>"
        proxy_var_usages = code_block.find(f"{proxy_var.left}.")
        for usage in proxy_var_usages:
            # Case 1: <proxy_var>.parent -> parent
            if usage.source == f"{proxy_var.left}.parent":
                usage.edit("parent")
            else:
                # Case 2: <proxy_var>.<field> -> parent.<field>
                usage.replace(f"{proxy_var.left}.", "parent.")

        # Case 3: <proxy_var> -> parent.proxy
        proxy_var_whole_word_usages = code_block.search(rf"\b(?<!\.){proxy_var.left}(?!\.)\b")
        for usage in proxy_var_whole_word_usages[1:]:
            usage.edit("parent.proxy")

        # Step 4: Replace "<Record>.proxy_id" with "<Record>.parent_id"
        proxy_id_usages = code_block.find(".proxy_id")
        for usage in proxy_id_usages:
            usage.replace(".proxy_id", ".parent_id")

    # language=python
    assert re.sub(r"\s+", "", file.content) == re.sub(
        r"\s+",
        "",
        """
def my_db_query(
    parent: Parent, to_record: Record
) -> None:

    from_logs: list[Log] = (
        db.session.execute(
            select(Log).where(
                Log.parent_id == parent.id
            )
        )
    )
    x = parent.proxy
    y = parent
    for log in from_logs:
        log.parent_id = to_record.id
    """,
    )


def test_if_else_statements(tmpdir) -> None:
    # language=python
    content = """
def foo():
    if a:
        log(a)
    elif b:
        print(b)
        if c:
            print(c)
        if d:
            print(d)
        else:
            return
    elif c:
        if d:
            print(d)
        else:
            return
        print(c)
    else:
        return
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file: PyFile = codebase.get_file("test.py")
        function = file.get_function("foo")
        if_blocks = function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT)
        assert len(if_blocks) == 4
        assert len(function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT, function.code_block.level)) == 1
        assert len(function.code_block.get_statements(StatementType.IF_BLOCK_STATEMENT, function.code_block.level + 1)) == 4
        statements = function.code_block.get_statements()
        assert len(statements) == 13
        statement_types = [(x.statement_type, x.parent.level) for x in statements]
        assert statement_types == [
            (StatementType.IF_BLOCK_STATEMENT, 1),
            (StatementType.EXPRESSION_STATEMENT, 2),
            (StatementType.EXPRESSION_STATEMENT, 2),
            (StatementType.IF_BLOCK_STATEMENT, 2),
            (StatementType.EXPRESSION_STATEMENT, 3),
            (StatementType.IF_BLOCK_STATEMENT, 2),
            (StatementType.EXPRESSION_STATEMENT, 3),
            (StatementType.RETURN_STATEMENT, 3),
            (StatementType.IF_BLOCK_STATEMENT, 2),
            (StatementType.EXPRESSION_STATEMENT, 3),
            (StatementType.RETURN_STATEMENT, 3),
            (StatementType.EXPRESSION_STATEMENT, 2),
            (StatementType.RETURN_STATEMENT, 2),
        ]
