# Transform promise.then statements to async/await

This example demonstrates how to use Codegen to automatically transform `promise.then` statements to `async/await`.

> Here is an [open pull request](https://github.com/twilio/twilio-node/pull/1072) created in the [_official_ twilio node.js](https://www.twilio.com/docs/messaging/quickstart/node) repository using the promise to async/await transformation using Codegen.

## How the Migration Script Works

The script automates the entire migration process in a few key steps:

1. **Promise Detection**

   ```python
   # Get all promise chains in the codebase
   promise_chains = []
   for file in codebase.files:
       promise_chains = promise_chains + file.promise_chains
   ```

   ```python
   # Or get all promise chains in the current function
   function = codebase.get_function("function_name")
   promise_chains = function.promise_chains
   ```

   ```python
   # Or get the promise chain for the current function call
   function_call = codebase.get_function("function_name").function_calls[0]
   promise_chain = function_call.promise_chain
   ```

   - Automatically identifies all promise chains in each file, function, or function call in the codebase
   - Uses Codegen's intelligent code analysis engine

1. **Transformation**

   ```python
   # Transform a promise chain to async/await (inplace)
   promise_chain.convert_to_async_await()
   codebase.commit()
   ```

   ```python
   # Or return the transformed code + clean up additonal business logic from .then blocks
   promise_statement = promise_chain.parent_statement
   new_code = promise_chain.convert_to_async_await(inplace_edit=False)

   promise_statement.edit(
       f"""
    {new_code}

    # handle additional business logic here
    """
   )
   ```

   - Replaces the promise chain with the async/await version
   - Handles function calls and function bodies automatically
   - Handles top-level varable assignments and return statements
   - Deals with ambiguous return blocks by adding annonymous functions where necessary
   - Carries over try/catch/finally blocks
   - Acknowledges implicit returns

# Examples

## Running the Migration on the [Official Twilio Node.js](https://github.com/twilio/twilio-node) Client Libary

_1. Follow step by step in the [convert_promises_twilio_repository.ipynb](./convert_promises_twilio_repository.ipynb) notebook_

_Or run codemod script directly:_

```bash
# Install Codegen
pip install codegen

# Run the promise to async/await migration
python run.py
```

The script will:

1. Initialize the codebase
1. Find _all 592_ instances of `promise.then` statements with the base call called `operationPromise`
1. Convert those to async/await style calls

_IMPORTANT: ensure to run `npx prettier --write .` after the migration to fix indentation + linting_

## Explore All The Covered Cases for the Conversion

_Checkout the [promise_to_async_await.ipynb](./promise_to_async_await.ipynb) notebook_

Currently, the `promise_chain.convert_to_async_await()` method handles the following cases:

- `promise.then()` statements of any length
- `promise.then().catch()` statements of any length
- `promise.then().catch().finally()` statements of any length
- Implicit returns -> `return promise.then()`
- Top level variable assignments -> `let assigned_var = promise.then()`
- Top level variable assignments -> `let assigned_var = promise.then()`
- Ambiguous/conditional return blocks

**IMPORTANT:**

_There will be cases that the current `promise_chain.convert_to_async_await()` cannot handle. In those cases, either right your own transformation logic using the codegen-sdk or open an issue on the [Codegen](https://github.com/codegen-sh/codegen-sdk) repository._

## Contributing

Feel free to submit issues and any enhancement requests!
