"""Dynamic tool registration for the Codegen MCP server."""

import json
from typing import Annotated

from fastmcp import FastMCP

from .executor import execute_tool_via_api


def register_dynamic_tools(mcp: FastMCP, available_tools: list):
    """Register all available tools from the API as individual MCP tools."""
    import inspect

    for i, tool_info in enumerate(available_tools):
        # Skip None or invalid tool entries
        if not tool_info or not isinstance(tool_info, dict):
            print(f"⚠️ Skipping invalid tool entry at index {i}: {tool_info}")
            continue

        try:
            tool_name = tool_info.get("name", "unknown_tool")
            tool_description = tool_info.get("description", "No description available").replace("'", '"').replace('"', '\\"')
            tool_parameters = tool_info.get("parameters", {})

            # Parse the parameter schema
            if tool_parameters is None:
                tool_parameters = {}
            properties = tool_parameters.get("properties", {})
            required = tool_parameters.get("required", [])
        except Exception as e:
            print(f"❌ Error processing tool at index {i}: {e}")
            print(f"Tool data: {tool_info}")
            continue

        def make_tool_function(name: str, description: str, props: dict, req: list):
            # Create function dynamically with proper parameters
            def create_dynamic_function():
                # Build parameter list for the function
                param_list = []
                param_annotations = {}

                # Collect required and optional parameters separately
                required_params = []
                optional_params = []

                # Add other parameters from schema
                for param_name, param_info in props.items():
                    param_type = param_info.get("type", "string")
                    param_desc = param_info.get("description", f"Parameter {param_name}").replace("'", '"').replace('"', '\\"')
                    is_required = param_name in req

                    # Special handling for tool_call_id - always make it optional
                    if param_name == "tool_call_id":
                        optional_params.append("tool_call_id: Annotated[str, 'Unique identifier for this tool call'] = 'mcp_call'")
                        continue

                    # Convert JSON schema types to Python types
                    if param_type == "string":
                        py_type = "str"
                    elif param_type == "integer":
                        py_type = "int"
                    elif param_type == "number":
                        py_type = "float"
                    elif param_type == "boolean":
                        py_type = "bool"
                    elif param_type == "array":
                        items_type = param_info.get("items", {}).get("type", "string")
                        if items_type == "string":
                            py_type = "list[str]"
                        else:
                            py_type = "list"
                    else:
                        py_type = "str"  # Default fallback

                    # Handle optional parameters (anyOf with null)
                    if "anyOf" in param_info:
                        py_type = f"{py_type} | None"
                        if not is_required:
                            default_val = param_info.get("default", "None")
                            if isinstance(default_val, str) and default_val != "None":
                                default_val = f'"{default_val}"'
                            optional_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}'] = {default_val}")
                        else:
                            required_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}']")
                    elif is_required:
                        required_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}']")
                    else:
                        # Optional parameter with default
                        default_val = param_info.get("default", "None")
                        if isinstance(default_val, str) and default_val not in ["None", "null"]:
                            default_val = f'"{default_val}"'
                        elif isinstance(default_val, bool):
                            default_val = str(default_val)
                        elif default_val is None or default_val == "null":
                            default_val = "None"
                        optional_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}'] = {default_val}")

                # Only add tool_call_id if it wasn't already in the schema
                tool_call_id_found = any("tool_call_id" in param for param in optional_params)
                if not tool_call_id_found:
                    optional_params.append("tool_call_id: Annotated[str, 'Unique identifier for this tool call'] = 'mcp_call'")

                # Combine required params first, then optional params
                param_list = required_params + optional_params

                # Create the function code
                params_str = ", ".join(param_list)

                # Create a list of parameter names for the function
                param_names = []
                for param in param_list:
                    # Extract parameter name from the type annotation
                    param_name = param.split(":")[0].strip()
                    param_names.append(param_name)

                param_names_str = repr(param_names)

                func_code = f"""
def tool_function({params_str}) -> str:
    '''Dynamically created tool function: {description}'''
    # Collect all parameters by name to avoid circular references
    param_names = {param_names_str}
    arguments = {{}}

    # Get the current frame's local variables
    import inspect
    frame = inspect.currentframe()
    try:
        locals_dict = frame.f_locals
        for param_name in param_names:
            if param_name in locals_dict:
                value = locals_dict[param_name]
                # Handle None values and ensure JSON serializable
                if value is not None:
                    arguments[param_name] = value
    finally:
        del frame

    # Execute the tool via API
    result = execute_tool_via_api('{name}', arguments)

    # Return formatted result
    return json.dumps(result, indent=2)
"""

                # Execute the function code to create the function
                namespace = {"Annotated": Annotated, "json": json, "execute_tool_via_api": execute_tool_via_api, "inspect": inspect}
                try:
                    exec(func_code, namespace)
                    func = namespace["tool_function"]
                except SyntaxError as e:
                    print(f"❌ Syntax error in tool {name}:")
                    print(f"Error: {e}")
                    print("Generated code:")
                    for i, line in enumerate(func_code.split("\n"), 1):
                        print(f"{i:3}: {line}")
                    raise

                # Set metadata
                func.__name__ = name.replace("-", "_")
                func.__doc__ = description

                return func

            return create_dynamic_function()

        # Create the tool function
        tool_func = make_tool_function(tool_name, tool_description, properties, required)

        # Register with FastMCP using the decorator
        decorated_func = mcp.tool()(tool_func)

        print(f"✅ Registered dynamic tool: {tool_name}")
