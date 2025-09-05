from tqdm import tqdm

from codegen.sdk.code_generation.doc_utils.parse_docstring import parse_docstring
from codegen.sdk.code_generation.doc_utils.schemas import ClassDoc, GSDocs, MethodDoc
from codegen.sdk.code_generation.doc_utils.utils import create_path, extract_class_description, get_type, get_type_str, has_documentation, is_settter, replace_multiple_types
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.placeholder.placeholder_type import TypePlaceholder

ATTRIBUTES_TO_IGNORE = [
    "ctx",
    "node_id",
    "angular",
    "model_config",
    "constructor_keyword",
    "viz",
    "console",
    "items",
    "node_type",
    "ts_node",
    "file_node_id",
    "statement_type",
    "assignment_types",
]


def generate_docs_json(codebase: Codebase, head_commit: str, raise_on_missing_docstring: bool = False) -> GSDocs:
    """Update documentation table for classes, methods and attributes in the codebase.

    Args:
        codebase (Codebase): the codebase to update the docs for
        head_commit (str): the head commit hash
    Returns:
        dict[str, dict[str, Any]]: the documentation for the codebase
    """
    codegen_sdk_docs = GSDocs(classes=[])
    types_cache = {}

    def process_class_doc(cls):
        """Update or create documentation for a class."""
        description = cls.docstring.source.strip('"""') if cls.docstring else None
        parent_classes = [f"<{create_path(parent)}>" for parent in cls.superclasses if isinstance(parent, Class) and has_documentation(parent)]

        cls_doc = ClassDoc(
            title=cls.name,
            description=extract_class_description(description),
            content=" ",
            path=create_path(cls),
            inherits_from=parent_classes,
            version=str(head_commit),
            github_url=cls.github_url,
        )

        return cls_doc

    def process_method(method, cls, cls_doc, seen_methods):
        """Process a single method and update its documentation."""
        if any(dec.name == "noapidoc" for dec in method.decorators):
            return

        if method.name in seen_methods and not is_settter(method):
            return

        if not method.docstring:
            msg = f"Method {cls.name}.{method.name} does not have a docstring"
            raise ValueError(msg)

        method_path = create_path(method, cls)
        parameters = []

        parsed = parse_docstring(method.docstring.source)
        if parsed is None:
            msg = f"Method {cls.name}.{method.name} docstring does not exist or has incorrect format."
            raise ValueError(msg)

        # Update parameter types
        for param, parsed_param in zip(method.parameters[1:], parsed["arguments"]):
            if param.name == parsed_param.name:
                if isinstance(param.type, TypePlaceholder):
                    resolved_types = []
                else:
                    resolved_types = param.type.resolved_types

                parsed_param.type = replace_multiple_types(
                    codebase=codebase, input_str=parsed_param.type, resolved_types=resolved_types, parent_class=cls, parent_symbol=method, types_cache=types_cache
                )
                if param.default:
                    parsed_param.default = param.default

                parameters.append(parsed_param)
        # Update return type

        if not isinstance(method.return_type, TypePlaceholder):
            return_type = replace_multiple_types(
                codebase=codebase, input_str=method.return_type.source, resolved_types=method.return_type.resolved_types, parent_class=cls, parent_symbol=method, types_cache=types_cache
            )
        else:
            return_type = None
        parsed["return_types"] = [return_type]

        meta_data = {"parent": create_path(method.parent_class), "path": method.file.filepath}
        return MethodDoc(
            name=method.name,
            description=parsed["description"],
            parameters=parsed["arguments"],
            return_type=parsed["return_types"],
            return_description=parsed["return_description"],
            method_type=get_type(method),
            code=method.function_signature,
            path=method_path,
            raises=parsed["raises"],
            metainfo=meta_data,
            version=str(head_commit),
            github_url=method.github_url,
        )

    def process_attribute(attr, cls, cls_doc, seen_methods):
        """Process a single attribute and update its documentation."""
        if attr.name in seen_methods or attr.name in ATTRIBUTES_TO_IGNORE:
            return

        attr_path = create_path(attr, cls)

        description = attr.docstring(attr.parent_class)
        if raise_on_missing_docstring and not description:
            msg = f"Attribute {attr.parent_class.name}.{attr.name} does not have a docstring"
            raise ValueError(msg)
        attr_return_type = []
        if r_type := get_type_str(attr):
            if isinstance(r_type, TypePlaceholder):
                resolved_types = []
            else:
                resolved_types = r_type.resolved_types
            r_type_source = replace_multiple_types(codebase=codebase, input_str=r_type.source, resolved_types=resolved_types, parent_class=cls, parent_symbol=attr, types_cache=types_cache)
            attr_return_type.append(r_type_source)

        attr_info = {"description": description, "attr_return_type": attr_return_type}

        meta_data = {"parent": create_path(attr.parent_class), "path": attr.file.filepath}

        return MethodDoc(
            name=attr.name,
            description=attr_info["description"],
            parameters=[],
            return_type=attr_info["attr_return_type"],
            return_description=None,
            method_type="attribute",
            code=attr.attribute_docstring,
            path=attr_path,
            raises=[],
            metainfo=meta_data,
            version=str(head_commit),
            github_url=attr.github_url,
        )

    # Process all documented classes
    documented_classes = [cls for cls in codebase.classes if has_documentation(cls)]

    for cls in tqdm(documented_classes):
        cls_doc = process_class_doc(cls)
        codegen_sdk_docs.classes.append(cls_doc)
        seen_methods = set()

        # Process methods
        for method in cls.methods(max_depth=None, private=False, magic=False):
            method_doc = process_method(method, cls, cls_doc, seen_methods)
            if not method_doc:
                continue
            seen_methods.add(method_doc.name)
            cls_doc.methods.append(method_doc)

        # Process attributes
        for attr in cls.attributes(max_depth=None, private=False):
            if attr.name in ATTRIBUTES_TO_IGNORE:
                continue

            attr_doc = process_attribute(attr, cls, cls_doc, seen_methods)
            if not attr_doc:
                continue
            seen_methods.add(attr_doc.name)
            cls_doc.attributes.append(attr_doc)

    return codegen_sdk_docs
