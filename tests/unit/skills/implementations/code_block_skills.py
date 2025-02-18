from abc import ABC

from codegen.sdk.core.codebase import CodebaseType
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.statements.expression_statement import ExpressionStatement
from codegen.shared.enums.programming_language import ProgrammingLanguage
from tests.shared.skills.decorators import skill, skill_impl
from tests.shared.skills.skill import Skill
from tests.shared.skills.skill_test import SkillTestCase, SkillTestCasePyFile, SkillTestCaseTSFile

py_input = """
def main():
    print("This is the main function")
    # Your main program logic goes here
    x = 5
    y = 10
    result = add_numbers(x, y)
    print(f"The sum of {x} and {y} is {result}")

def add_numbers(a, b):
    with open("log.txt", "w") as f:
        return a + b

if __name__ == "__main__":
    main()
"""

ts_input = r"""
function main(): void {
    console.log("This is the main function");
    // Your main program logic goes here
    const x: number = 5;
    const y: number = 10;
    const result: number = addNumbers(x, y);
    console.log(`The sum of ${x} and ${y} is ${result}`);
}

function addNumbers(a: number, b: number): number {
    const fs = require('fs');
    fs.writeFileSync("log.txt", "");
    return a + b;
}

if (require.main === module) {
    main();
}
"""
ts_output_unwrap_function = """
console.log("This is the main function");
// Your main program logic goes here
const x: number = 5;
const y: number = 10;
const result: number = addNumbers(x, y);
console.log(`The sum of ${x} and ${y} is ${result}`);

const fs = require('fs');
fs.writeFileSync("log.txt", "");
return a + b;

if (require.main === module) {
    main();
}
"""

py_output_unwrap_function = """
print("This is the main function")
# Your main program logic goes here
x = 5
y = 10
result = add_numbers(x, y)
print(f"The sum of {x} and {y} is {result}")

with open("log.txt", "w") as f:
    return a + b

if __name__ == "__main__":
    main()
"""


@skill(eval_skill=False, prompt="Unwrap the body of all functions in the file", uid="22ce6b14-9cfa-4264-9da4-8b32d79684f4")
class UnwrapFunctionBody(Skill, ABC):
    """Unwraps the body of all functions in the codebase, transforming each function's code block into a flat structure without nested scopes."""

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCasePyFile(input=py_input, output=py_output_unwrap_function)])], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Unwraps the body of all functions in the file"""
        # iterate through all functions in the codebase
        for function in codebase.functions:
            # unwrap the body of the function
            function.code_block.unwrap()

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input, output=ts_output_unwrap_function)])], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Unwraps the body of all functions in the file"""
        # iterate through all functions in the codebase
        for function in codebase.functions:
            # unwrap the body of the function
            function.code_block.unwrap()


ts_output_unwrap_if_statement = """
function main(): void {
    console.log("This is the main function");
    // Your main program logic goes here
    const x: number = 5;
    const y: number = 10;
    const result: number = addNumbers(x, y);
    console.log(`The sum of ${x} and ${y} is ${result}`);
}

function addNumbers(a: number, b: number): number {
    const fs = require('fs');
    fs.writeFileSync("log.txt", "");
    return a + b;
}

main();
"""

py_output_unwrap_if_statement = """
def main():
    print("This is the main function")
    # Your main program logic goes here
    x = 5
    y = 10
    result = add_numbers(x, y)
    print(f"The sum of {x} and {y} is {result}")

def add_numbers(a, b):
    with open("log.txt", "w") as f:
        return a + b

main()
"""


@skill(eval_skill=False, prompt="Unwrap the body of all if statements in the file", uid="77c97447-0580-46ee-b871-7ace7f3ee727")
class UnwrapIfStatement(Skill, ABC):
    """Unwraps the body of all if statements in the file"""

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCasePyFile(input=py_input, output=py_output_unwrap_if_statement)])], language=ProgrammingLanguage.PYTHON)
    @skill_impl([SkillTestCase(files=[SkillTestCaseTSFile(input=ts_input, output=ts_output_unwrap_if_statement)])], language=ProgrammingLanguage.TYPESCRIPT)
    def skill_func(codebase: CodebaseType):
        for file in codebase.files:
            for if_block in file.code_block.if_blocks:
                if_block.consequence_block.unwrap()


py_output_unwrap_with_statement = """
def main():
    print("This is the main function")
    # Your main program logic goes here
    x = 5
    y = 10
    result = add_numbers(x, y)
    print(f"The sum of {x} and {y} is {result}")

def add_numbers(a, b):
    return a + b

if __name__ == "__main__":
    main()
"""


@skill(eval_skill=False, prompt="Unwrap the body of all with statements in the file", uid="e52ce1d7-1e96-4884-ab2f-c8c20933b299")
class UnwrapWithStatement(Skill, ABC):
    """This unwraps a `with` statement"""

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCasePyFile(input=py_input, output=py_output_unwrap_with_statement)])], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Unwraps the body of all with statements in the file"""
        # for all functions in the codebase
        for function in codebase.functions:
            # for each with statement in the function
            for with_statement in function.code_block.with_statements:
                # unwrap the with statement
                with_statement.code_block.unwrap()

    @staticmethod
    @skill_impl([], language=ProgrammingLanguage.TYPESCRIPT, ignore=True)
    def typescript_skill_func(codebase: CodebaseType):
        """With Statements are not supported in TypeScript"""
        ...


py_convert_test_assertion_input = """
def test_http_transactions(uuid, client, model):
    response = client.patch(
        f"/v1/some/path/{uuid}",
        model_id=model.id,
        json=(
            {
                "field1": 1,
            }
        ),
    )
    assert response.status_code == 400, response.data
    assert (
        response.json["error_v2"]["message"]
        == "This transaction has already been synced, cannot modify attribute"
    )

    # An unrelated test setup code block
    entity = create_entity(
        request_id="id",
        text="Suggested data for entity",
        id=uuid,
    )
    db.session.add(entity)
    db.session.commit()

    response = client.get(
        f"/v1/new/path/{uuid}",
        model_id=model.id,
        json=(
            {
                "data": [
                    {
                        "id": model.id,
                        "uuid": uuid,
                    }
                ],
            }
        ),
    )
    assert response.status_code == 200, response.data
    assert response.json["data"] == { "id": model.id, "uuid": uuid }
"""
py_convert_test_assertion_output = """
def test_http_transactions(uuid, client, model):
    response = client.patch(
        f"/v1/some/path/{uuid}",
        model_id=model.id,
        json=(
            {
                "field1": 1,
            }
        ),
        expect_status=400,
    )
    assert (
        response.json["error_v2"]["message"]
        == "This transaction has already been synced, cannot modify attribute"
    )

    # An unrelated test setup code block
    entity = create_entity(
        request_id="id",
        text="Suggested data for entity",
        id=uuid,
    )
    db.session.add(entity)
    db.session.commit()

    response = client.get(
        f"/v1/new/path/{uuid}",
        model_id=model.id,
        json=(
            {
                "data": [
                    {
                        "id": model.id,
                        "uuid": uuid,
                    }
                ],
            }
        ),
        expect_status=200,
    )
    assert response.json["data"] == { "id": model.id, "uuid": uuid }
"""

ts_convert_test_assertion_input = """
function testHttpTransactions(uuid: string, client: Client, model: Model, db: DB): void {
  let response = client.patch(
    `/v1/some/path/${uuid}`,
    {
      model_id: model.id,
      json: {
        field1: 1,
      },
    }
  );

  expect(response.status).toBe(400);
  expect(response.data).toBeDefined();
  expect(response.json().error_v2.message)
    .toBe("This transaction has already been synced, cannot modify attribute");

  // An unrelated test setup code block
  const entity = createEntity({
    request_id: "id",
    text: "Suggested data for entity",
    id: uuid,
  });
  db.session.add(entity);
  db.session.commit();

  response = client.get(
    `/v1/new/path/${uuid}`,
    {
      model_id: model.id,
      json: {
        data: [
          {
            id: model.id,
            uuid: uuid,
          }
        ],
      },
    }
  );

  expect(response.status).toBe(200);
  expect(response.data).toBeDefined();
  expect(response.json().data).toEqual({ id: model.id, uuid: uuid });
}
"""
ts_convert_test_assertion_output = """
function testHttpTransactions(uuid: string, client: Client, model: Model, db: DB): void {
  let response = client.patch(
    `/v1/some/path/${uuid}`,
    {
      model_id: model.id,
      json: {
        field1: 1,
      },
    },
    expect_status=400
  );
  expect(response.data).toBeDefined();
  expect(response.json().error_v2.message)
    .toBe("This transaction has already been synced, cannot modify attribute");

  // An unrelated test setup code block
  const entity = createEntity({
    request_id: "id",
    text: "Suggested data for entity",
    id: uuid,
  });
  db.session.add(entity);
  db.session.commit();

  response = client.get(
    `/v1/new/path/${uuid}`,
    {
      model_id: model.id,
      json: {
        data: [
          {
            id: model.id,
            uuid: uuid,
          }
        ],
      },
    },
    expect_status=200
  );
  expect(response.data).toBeDefined();
  expect(response.json().data).toEqual({ id: model.id, uuid: uuid });
}
"""


@skill(eval_skill=False, prompt="Convert test assertion to an argument a call to test function.", uid="a4f2c5dc-46a0-45b8-960b-826c8238239c")
class ConvertStatementToArgument(Skill, ABC):
    """Converts http status code assertion statements into an `expect_status` argument
    for test functions that make a call to a http method.
    """

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCasePyFile(input=py_convert_test_assertion_input, output=py_convert_test_assertion_output)])], language=ProgrammingLanguage.PYTHON)
    def python_skill_func(codebase: CodebaseType):
        """Transform test assertion statements into an argument to test functions that make a call to a http method."""
        methods = ["post", "get", "put", "delete", "patch"]
        client_name = "client"

        test_function = codebase.get_function("test_http_transactions")
        code_block = test_function.code_block

        # Search for all assignments of http calls
        test_call_assignments = []
        for assignment_var in code_block.local_var_assignments:
            assignment_value = assignment_var.value
            if not isinstance(assignment_value, FunctionCall):
                continue
            name = assignment_value.get_name()
            if isinstance(name, ChainedAttribute) and name.object == client_name and name.attribute.source in methods:
                test_call_assignments.append(assignment_var)

        for i, test_call_assignment in enumerate(test_call_assignments):
            # Search for the closest subsequent statement that uses the response variable in an assert statement
            search_start = test_call_assignment.index + 1
            search_end = len(code_block.statements) if i == len(test_call_assignments) - 1 else test_call_assignments[i + 1].index

            for statement in code_block.statements[search_start:search_end]:
                # Found the assertion statement using the response variable
                if f"assert {test_call_assignment.left.source}.status_code ==" in statement.source:
                    # Add the expect_error argument to the function call
                    assertion_value = statement.source.split("==")[-1].strip()
                    expected_status_code = assertion_value.split(",")[0].strip()
                    last_arg = test_call_assignment.value.args[-1]
                    last_arg.insert_after(",", newline=False)
                    last_arg.insert_after(f"expect_status={expected_status_code}", fix_indentation=True)

                    # Remove the assertion statement
                    statement.remove()

    @staticmethod
    @skill_impl([SkillTestCase(files=[SkillTestCaseTSFile(input=ts_convert_test_assertion_input, output=ts_convert_test_assertion_output)])], language=ProgrammingLanguage.TYPESCRIPT)
    def typescript_skill_func(codebase: CodebaseType):
        """Transform test assertion statements into an argument to test functions that make a call to a http method."""
        methods = ["post", "get", "put", "delete", "patch"]
        client_name = "client"

        test_function = codebase.get_function("testHttpTransactions")
        code_block = test_function.code_block

        # Search for all assignments of http calls
        test_call_assignments = []
        for assignment_var in code_block.local_var_assignments:
            assignment_value = assignment_var.value
            if not isinstance(assignment_value, FunctionCall):
                continue
            name = assignment_value.get_name()
            if isinstance(name, ChainedAttribute) and name.object == client_name and name.attribute.source in methods:
                test_call_assignments.append(assignment_var)

        for i, test_call_assignment in enumerate(test_call_assignments):
            # Search for the closest subsequent statement that uses the response variable in an assert statement
            search_start = test_call_assignment.index + 1
            search_end = len(code_block.statements) if i == len(test_call_assignments) - 1 else test_call_assignments[i + 1].index

            for statement in code_block.statements[search_start:search_end]:
                if not isinstance(statement, ExpressionStatement) or not isinstance(statement.value, FunctionCall):
                    continue

                # Found the assertion statement using the response variable
                if f"expect({test_call_assignment.left.source}.status)" in statement.extended_source:
                    # Add the expect_error argument to the function call
                    expected_status_code = statement.source.split(".")[-1].lstrip("toBe(").rstrip(");")
                    last_arg = test_call_assignment.value.args[-1]
                    last_arg.insert_after(",", newline=False)
                    last_arg.insert_after(f"expect_status={expected_status_code}", fix_indentation=True)

                    # Remove the assertion statement
                    statement.remove()
