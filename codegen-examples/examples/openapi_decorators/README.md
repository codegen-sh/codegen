# Add OpenAPI Decorators to Flask-RESTx Endpoints

This example demonstrates how to use Codegen to automatically add OpenAPI decorators (`@response` and `@expect`) to Flask-RESTx API endpoints. The migration script analyzes existing code patterns and adds appropriate decorators to improve API documentation.

> [!NOTE]
> This codemod helps maintain consistent API documentation by automatically analyzing endpoint behavior and adding appropriate OpenAPI decorators.

## How the Migration Script Works

The script automates the documentation process in several key steps:

1. **Resource Class Detection**

   ```python
   for cls in codebase.classes:
       if cls.is_subclass_of("Resource"):
           # Process Flask-RESTx resource classes
   ```

   - Identifies Flask-RESTx resource classes
   - Analyzes HTTP method handlers (get, post, put, patch, delete)
   - Determines which decorators are missing

1. **Response Analysis**

   ```python
   response_schemas = analyze_method_returns(method)
   ```

   - Analyzes return statements
   - Extracts response codes and schemas
   - Handles error responses from `http_error` calls
   - Processes existing `@doc` decorators

1. **Parameter Analysis**

   ```python
   expect_schema = analyze_method_params(method)
   ```

   - Analyzes request parameter usage
   - Detects JSON request body schemas
   - Processes existing `@expect` decorators

## Why This Makes Documentation Easy

1. **Automated Analysis**

   - Automatically detects API patterns
   - Infers response and request schemas
   - No manual documentation required

1. **Consistent Documentation**

   - Ensures all endpoints are documented
   - Maintains consistent decorator usage
   - Preserves existing decorators

1. **Intelligent Schema Detection**

   - Analyzes model fields
   - Detects request parameter types
   - Handles nested objects

## Common Documentation Patterns

### Response Decorators

```python
# Before
@ns.route("/endpoint")
class MyResource(Resource):
    def get(self):
        return {"data": result}


# After
@ns.route("/endpoint")
class MyResource(Resource):
    @ns.response(200, "Success", {"data": {"type": "any"}})
    def get(self):
        return {"data": result}
```

### Request Expect Decorators

```python
# Before
@ns.route("/endpoint")
class MyResource(Resource):
    def post(self):
        data = request.json["name"]
        return {"status": "success"}


# After
@ns.route("/endpoint")
class MyResource(Resource):
    @ns.expect({"name": {"type": "any", "required": True}})
    @ns.response(200, "Success", {"status": {"type": "any"}})
    def post(self):
        data = request.json["name"]
        return {"status": "success"}
```

## Key Benefits to Note

1. **Better API Documentation**

   - Clear response schemas
   - Documented request parameters
   - Improved API explorer experience

1. **Consistent Error Handling**

   - Documented error responses
   - Clear status codes
   - Better client integration

1. **Time Savings**

   - Automated decorator generation
   - Reduced manual documentation work
   - Easier maintenance

## Running the Migration

```bash
# Install Codegen
pip install codegen

# Run the migration
python run.py
```

The script will:

1. Initialize the codebase
1. Find Flask-RESTx resource classes
1. Analyze methods and add decorators
1. Print detailed analytics about missing decorators

## Learn More

- [Flask-RESTx Documentation](https://flask-restx.readthedocs.io/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
