import codegen
from codegen import Codebase
from codegen.sdk.core.statements.statement import StatementType


@codegen.function("promises-to-async-await")
def run(codebase: Codebase):
    """Convert a repeated use of a promise chain to async await in the official twilio js client library twilio/twilio-node repository.

    This codemod:
    1. Finds all methods containing operationPromise.then chains
    2. Converts the promise chain to use async await
    3. Gets rid of the callback handler by adding try catch directly in the function body
    """

    # loop through all files -> classes -> methods to find promise the operationPromise chains
    i = 0

    for file in codebase.files:  # pyright: ignore
        for _class in file.classes:
            for method in _class.methods:
                if method.name in ["each", "setPromiseCallback"]:
                    print("skipping method", method.name, "...")
                    continue

                # Only process methods containing operationPromise
                if not method.find("operationPromise"):
                    continue

                # Find the first promise chain with then blocks
                for promise_chain in method.promise_chains:
                    promise_statement = promise_chain.parent_statement
                    i += 1
                    if i < 10:
                        print(f"Found operation promise in the {method.name} method in {method.file.filepath} file.")

                    # ---------- CONVERT PROMISE CHAIN TO ASYNC AWAIT ----------
                    assignment_variable_name = "operation"
                    async_await_code = promise_chain.convert_to_async_await(assignment_variable_name=assignment_variable_name, inplace_edit=False)

                    new_code = f"""\
                        try {{
                            {async_await_code}

                            if (callback) {{
                                callback(null, {assignment_variable_name});
                            }}

                            return {assignment_variable_name};
                        }} catch(err: any) {{
                            if (callback) {{
                                callback(err);
                            }}
                            throw err;
                        }}"""

                    promise_statement.edit(new_code)

                    # Cleanup callback handler assignment and subsequent return statement
                    statements = promise_statement.parent.get_statements()
                    return_stmt = next((stmt for stmt in statements if stmt.statement_type == StatementType.RETURN_STATEMENT), None)
                    assign_stmt = next((stmt for stmt in reversed(statements) if stmt.statement_type == StatementType.ASSIGNMENT), None)

                    if return_stmt:
                        return_stmt.remove()
                    if assign_stmt:
                        assign_stmt.remove()
    print(f"Found {i + 1} operationPromise chains!")
    print("Converting to async/await...")
    print("Done!")

    codebase.commit()


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase("twilio/twilio-node", language="typescript")
    print("Running codemod...")
    run(codebase)
