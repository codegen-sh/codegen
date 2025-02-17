import codegen
from codegen import Codebase
from codegen.sdk.enums import ProgrammingLanguage
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
    for file in codebase.files:
        for _class in file.classes:
            for method in _class.methods:
                if method.name in ["each", "setPromiseCallback"]:
                    print("skipping method", method.name, "\n")
                    continue

                # Only process methods containing operationPromise
                if not method.find("operationPromise"):
                    continue

                # Find the first promise chain with then blocks
                promise_chain = None
                promise_statement = None
                for func in method.function_calls:
                    chain = func.get_promise_chain
                    if chain and len(chain.then_chain) > 0:  # Check if chain exists first
                        promise_chain = chain
                        promise_statement = chain.parent_statement
                        print(f"converting {method.name} promise chain to async await...")
                        break

                if not promise_chain:
                    continue

                custom_var_name = "operation"

                # ---------- CONVERT PROMISE CHAIN TO ASYNC AWAIT ----------
                async_await_code = promise_chain.convert_to_async_await(custom_var_name=custom_var_name, inplace_edit=False)

                new_code = f"""\
                    try {{
                        {async_await_code}

                        if (callback) {{
                            callback(null, {custom_var_name});
                        }}

                        return {custom_var_name};
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

    codebase.commit()


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase("/Users/tawsifkamal/Documents/codegen-repos/twilio-node", programming_language=ProgrammingLanguage.TYPESCRIPT)
    print("Running codemod...")
    run(codebase)
