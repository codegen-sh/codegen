from typing import Optional

from codegen.extensions.graph.utils import Node, NodeLabel, Relation, RelationLabel, SimpleGraph
from codegen.sdk.code_generation.doc_utils.utils import safe_get_class
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.function import Function
from codegen.sdk.python.class_definition import PyClass


def create_codebase_graph(codebase):
    """Create a SimpleGraph representing the codebase structure."""
    # Initialize graph
    graph = SimpleGraph()

    # Track existing nodes by name to prevent duplicates
    node_registry = {}  # name -> node_id mapping

    def get_or_create_node(name: str, label: NodeLabel, parent_name: Optional[str] = None, properties: dict | None = None):
        """Get existing node or create new one if it doesn't exist."""
        full_name = f"{parent_name}.{name}" if parent_name and parent_name != "Class" else name
        if full_name in node_registry:
            return graph.nodes[node_registry[full_name]]

        node = Node(name=name, full_name=full_name, label=label.value, properties=properties or {})
        node_registry[full_name] = node.id
        graph.add_node(node)
        return node

    def create_class_node(class_def):
        """Create a node for a class definition."""
        return get_or_create_node(
            name=class_def.name,
            label=NodeLabel.CLASS,
            properties={
                "filepath": class_def.filepath if hasattr(class_def, "filepath") else "",
                "source": class_def.source if hasattr(class_def, "source") else "",
                "type": "class",
            },
        )

    def create_function_node(func):
        """Create a node for a function/method."""
        class_name = None
        if func.is_method:
            class_name = func.parent_class.name

        return get_or_create_node(
            name=func.name,
            label=NodeLabel.METHOD if class_name else NodeLabel.FUNCTION,
            parent_name=class_name,
            properties={
                "filepath": func.filepath if hasattr(func, "filepath") else "",
                "is_async": func.is_async if hasattr(func, "is_async") else False,
                "source": func.source if hasattr(func, "source") else "",
                "type": "method" if class_name else "function",
            },
        )

    def create_function_call_node(func_call):
        """Create a node for a function call."""
        func_def = func_call.function_definition
        if not func_def:
            return None
        if isinstance(func_def, ExternalModule):
            parent_class = safe_get_class(codebase, func_def.name)
            if parent_class and parent_class.get_method(func_call.name):
                return create_function_node(parent_class.get_method(func_call.name))
            else:
                return None

        call_node = None
        if isinstance(func_def, Function):
            call_node = create_function_node(func_def)

        elif isinstance(func_def, Class):
            call_node = create_class_node(func_def)

        return call_node

    # Process all classes
    for class_def in codebase.classes:
        class_node = create_class_node(class_def)

        # Process methods
        methods = class_def.methods
        for method in methods:
            method_node = create_function_node(method)

            # Add DEFINES relation
            defines_relation = Relation(
                label=RelationLabel.DEFINES.value, source_id=class_node.id, target_id=method_node.id, properties={"relationship_description": "The parent class defines the method."}
            )
            graph.add_relation(defines_relation)

            for call in method.function_calls:
                call_node = create_function_call_node(call)
                if call_node and call_node != method_node:
                    call_relation = Relation(
                        label=RelationLabel.CALLS.value, source_id=method_node.id, target_id=call_node.id, properties={"relationship_description": f"The method calls the {call_node.label}."}
                    )
                    graph.add_relation(call_relation)

        # Add inheritance relations
        if class_def.parent_classes:
            for parent in class_def.parent_classes:
                if not isinstance(parent, PyClass):
                    try:
                        parent = codebase.get_class(parent.name, optional=True)
                        if not parent:
                            continue
                    except Exception as e:
                        print(f"parent not found: {e}")
                        continue
                if not hasattr(parent, "name"):
                    continue
                parent_node = create_class_node(parent)

                inherits_relation = Relation(
                    label=RelationLabel.INHERITS_FROM.value,
                    source_id=class_node.id,
                    target_id=parent_node.id,
                    properties={"relationship_description": "The child class inherits from the parent class."},
                )
                graph.add_relation(inherits_relation)

    for func in codebase.functions:
        func_node = create_function_node(func)
        for call in func.function_calls:
            call_node = create_function_call_node(call)
            if call_node and call_node != func_node:
                call_relation = Relation(
                    label=RelationLabel.CALLS.value, source_id=func_node.id, target_id=call_node.id, properties={"relationship_description": f"The function calls the {call_node.label}."}
                )
                graph.add_relation(call_relation)

    return graph
