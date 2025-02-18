import codegen
from codegen import Codebase


def analyze_model_fields(method) -> dict:
    """Analyze model fields from ns_conf.model definitions."""
    print(f"\n🔍 Analyzing model fields for method: {method.name}")
    schema = {}

    # Look for model definitions in doc decorators
    for decorator in method.decorators:
        if ".doc" in decorator.source:
            try:
                if "model=" in decorator.source:
                    model_def = decorator.source.split("model=")[1]
                    if "fields." in model_def:
                        # Parse the fields
                        fields_str = model_def.split("{")[1].split("}")[0]
                        for field in fields_str.split(","):
                            if ":" in field:
                                name, field_type = field.split(":", 1)
                                name = name.strip()
                                if "fields.String" in field_type:
                                    schema[name] = {"type": "string"}
                                elif "fields.Boolean" in field_type:
                                    schema[name] = {"type": "boolean"}
                                elif "fields.Integer" in field_type:
                                    schema[name] = {"type": "integer"}
                                elif "fields.Nested" in field_type:
                                    schema[name] = {"type": "object"}
                                else:
                                    schema[name] = {"type": "any"}
            except Exception as e:
                print(f"   ⚠️ Couldn't parse model fields: {str(e)}")

    return schema


def analyze_doc_responses(method) -> list[tuple]:
    """Analyze responses defined in @ns_conf.doc decorators."""
    print(f"\n🔍 Analyzing doc responses for method: {method.name}")
    responses = []

    for decorator in method.decorators:
        if ".doc" in decorator.source:
            try:
                if "responses=" in decorator.source:
                    responses_dict = decorator.source.split("responses=")[1].split("}")[0] + "}"
                    if "{" in responses_dict:
                        resp_content = responses_dict.strip("{}").split(",")
                        for resp in resp_content:
                            if ":" in resp:
                                code, desc = resp.split(":", 1)
                                code = int(code.strip())
                                desc = desc.strip().strip("'").strip('"')
                                schema = None  # Could extract from body/model if present
                                responses.append((code, desc, schema))
            except Exception as e:
                print(f"   ⚠️ Couldn't parse doc responses: {str(e)}")

    return responses


def analyze_method_returns(method) -> list[tuple]:
    """Analyze method return statements to determine response schemas."""
    print(f"\n🔍 Analyzing returns for method: {method.name}")
    responses = set()  # Using set to avoid duplicates

    # First check existing response decorators
    for decorator in method.decorators:
        if ".response" in decorator.source:
            try:
                args = decorator.source.split("(")[1].split(")")[0].split(",", 2)
                status = int(args[0].strip())
                desc = args[1].strip().strip("'").strip('"')
                schema = eval(args[2].strip()) if len(args) > 2 else None
                responses.add((status, desc, schema))
            except Exception as e:
                print(f"   ⚠️ Couldn't parse response decorator: {str(e)}")

    # Check doc responses
    doc_responses = analyze_doc_responses(method)
    for resp in doc_responses:
        responses.add(resp)

    # Handle model fields if present
    model_schema = analyze_model_fields(method)
    if model_schema:
        # Add model schema to existing 200 response or create new one
        success_responses = [r for r in responses if r[0] == 200]
        if success_responses:
            responses.remove(success_responses[0])
            responses.add((200, success_responses[0][1], model_schema))
        else:
            responses.add((200, "Success", model_schema))

    # Track http_error calls
    error_calls = [call for call in method.function_calls if call.name == "http_error"]
    for error_call in error_calls:
        if len(error_call.args) >= 2:
            try:
                status_code = error_call.args[0].value
                if hasattr(status_code, "name"):  # Handle HTTPStatus enum
                    status_code = getattr(status_code, status_code.name)
                message = error_call.args[1].value
                responses.add((int(status_code), message, None))
            except Exception as e:
                print(f"   ⚠️ Couldn't parse http_error: {str(e)}")

    # Analyze return statements
    for return_stmt in method.return_statements:
        try:
            return_value = return_stmt.value.source
            if "''" in return_value and "200" in return_value:
                responses.add((200, "Success", None))
            elif "{" in return_value:
                schema = {}
                content = return_value.strip("{}")
                for pair in content.split(","):
                    if ":" in pair:
                        key, _ = pair.split(":", 1)
                        key = key.strip().strip("'").strip('"')
                        schema[key] = {"type": "any"}
                responses.add((200, "Success", schema))
        except Exception as e:
            print(f"   ⚠️ Couldn't analyze return: {str(e)}")

    # Ensure we have at least one response
    if not responses:
        responses.add((200, "Success", None))

    return list(responses)


def analyze_method_params(method) -> dict:
    """Analyze method parameters and request parsing to determine expect schema."""
    print(f"\n🔍 Analyzing parameters for method: {method.name}")
    schema = {}

    # First check ns_conf.expect decorators
    for decorator in method.decorators:
        if ".expect" in decorator.source:
            try:
                expect_dict = decorator.source.split("expect(")[1].split(")")[0]
                if "{" in expect_dict:
                    dict_content = expect_dict.strip("{}")
                    for entry in dict_content.split(","):
                        if ":" in entry and "'" in entry:
                            key = entry.split(":")[0].strip().strip("'").strip('"')
                            schema[key] = {"type": "any", "required": False}  # Default to not required
            except Exception as e:
                print(f"   ⚠️ Couldn't parse expect decorator: {str(e)}")

    # Look for request.json usage if no schema found
    if not schema:
        for call in method.function_calls:
            if "request.json" in call.source:
                try:
                    if "get(" in call.source:
                        key = call.source.split(".get(")[1].split(",")[0].strip("'\"")
                        schema[key] = {"type": "any", "required": False}
                    else:
                        key = call.source.split("request.json")[1].strip("[].'\"")
                        schema[key] = {"type": "any", "required": True}
                except Exception as e:
                    print(f"   ⚠️ Couldn't analyze request.json: {str(e)}")

    print(f"   📝 Found expected params: {schema}")
    return schema


@codegen.function("add-openapi-decorators")
def run(codebase: Codebase):
    """Add OpenAPI decorators (@response and @expect) to API endpoints."""
    analytics = {}

    for cls in codebase.classes:
        if cls.is_subclass_of("Resource"):
            file_analytics = []

            ns_decorator = next((d for d in cls.decorators if ".route" in d.source), None)
            if not ns_decorator:
                continue

            ns_name = ns_decorator.source.split("@")[1].split(".")[0]
            print(f"      📌 Found namespace: {ns_name}")

            for method in cls.methods:
                print(f"\n      ⚡ Checking method: {method.name}")

                if method.name not in ("get", "post", "put", "patch", "delete"):
                    print("         ⏩ Skipping - not an HTTP method")
                    continue

                # Check existing decorators
                existing_decorators = [d.source for d in method.decorators]
                print(f"         📝 Existing decorators: {existing_decorators}")

                # Check for missing decorators
                missing_response = not any(".response" in d for d in existing_decorators)
                missing_expect = not any(".expect" in d for d in existing_decorators)

                if not (missing_response or missing_expect):
                    print("         ✅ All decorators present")
                    continue

                print(f"         🔧 Missing decorators - response: {missing_response}, expect: {missing_expect}")

                missing_info = {"class": cls.name, "method": method.name, "missing_response": missing_response, "missing_expect": missing_expect}
                file_analytics.append(missing_info)

                try:
                    response_schemas = analyze_method_returns(method)
                    expect_schema = analyze_method_params(method) if method.name in ("post", "put", "patch") else {}

                    # Add missing expect decorator
                    if missing_expect and method.name in ("post", "put", "patch") and expect_schema:
                        schema_str = "{\n"
                        for key, value in expect_schema.items():
                            schema_str += f"    '{key}': {value},\n"
                        schema_str += "}"
                        print(f"         ➕ Adding expect decorator with schema: {schema_str}")
                        method.insert_before(f"@{ns_name}.expect({schema_str})", fix_indentation=True)

                    # Add missing response decorators
                    if missing_response:
                        print(f"         ➕ Adding {len(response_schemas)} response decorators")
                        for code, desc, schema in reversed(response_schemas):
                            if schema:
                                schema_str = "{\n"
                                for key, value in schema.items():
                                    schema_str += f"    '{key}': {value},\n"
                                schema_str += "}"
                                print(f"         Adding response {code} with schema")
                                method.insert_before(f"@{ns_name}.response({code}, '{desc}', {schema_str})", fix_indentation=True)
                            else:
                                print(f"         Adding response {code} without schema")
                                method.insert_before(f"@{ns_name}.response({code}, '{desc}')", fix_indentation=True)
                except Exception as e:
                    print(f"         ❌ Error adding decorators: {str(e)}")
                    continue

            if file_analytics:
                analytics[cls.file.filepath] = file_analytics

    print("\n📊 Analytics: Missing OpenAPI Decorators")
    print("================================================================")

    for file_path, missing_decorators in analytics.items():
        print(f"\nFile: {file_path}")
        for info in missing_decorators:
            print(f"  Class: {info['class']}, Method: {info['method']}")
            if info["missing_response"]:
                print("    ❌ Missing @response decorator")
            if info["missing_expect"]:
                print("    ❌ Missing @expect decorator")

    print("\n✅ OpenAPI decorators added!")
    codebase.commit()


if __name__ == "__main__":
    print("🎯 Starting OpenAPI decorators addition...")
    codebase = Codebase.from_repo("mindsdb/mindsdb", commit="4b76c44bfaec789289e15fbdff7397e866009f94", language="python")
    run(codebase)
    print("✅ Done! OpenAPI decorators added to all API endpoints!")
