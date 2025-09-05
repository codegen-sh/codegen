"""Context management for autogenlib modules."""

import ast

# Store the context of each module
module_contexts = {}


def get_module_context(fullname):
    """Get the context of a module."""
    return module_contexts.get(fullname, {})


def set_module_context(fullname, code):
    """Update the context of a module."""
    module_contexts[fullname] = {
        "code": code,
        "defined_names": extract_defined_names(code),
    }


def extract_defined_names(code):
    """Extract all defined names (functions, classes, variables) from the code."""
    try:
        tree = ast.parse(code)
        names = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)

        return names
    except SyntaxError:
        return set()


def is_name_defined(fullname):
    """Check if a name is defined in its module."""
    if "." not in fullname:
        return False

    module_path, name = fullname.rsplit(".", 1)
    context = get_module_context(module_path)

    if not context:
        # Module doesn't exist yet
        return False

    return name in context.get("defined_names", set())
