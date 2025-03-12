from codegen.sdk.code_generation.enums import DocumentationDecorators
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.enums import NodeType
from codegen.sdk.python.class_definition import PyClass
from codegen.shared.enums.programming_language import ProgrammingLanguage


def get_decorator_for_language(
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
) -> DocumentationDecorators:
    if language == ProgrammingLanguage.PYTHON:
        return DocumentationDecorators.PYTHON
    elif language == ProgrammingLanguage.TYPESCRIPT:
        return DocumentationDecorators.TYPESCRIPT


def get_api_classes_by_decorator(
    codebase: Codebase,
    language: ProgrammingLanguage = ProgrammingLanguage.PYTHON,
) -> dict[str, PyClass]:
    """Returns all classes in a directory that have a specific decorator."""
    classes = {}
    language_specific_decorator = get_decorator_for_language(language).value
    general_decorator = DocumentationDecorators.GENERAL_API.value
    # get language specific classes
    for cls in codebase.classes:
        class_decorators = [decorator.name for decorator in cls.decorators]
        if language_specific_decorator in class_decorators:
            classes[cls.name] = cls
    for cls in codebase.classes:
        class_decorators = [decorator.name for decorator in cls.decorators]
        if general_decorator in class_decorators and cls.name not in classes.keys():
            classes[cls.name] = cls
    return classes


def format_python_codeblock(source: str) -> str:
    """A python codeblock in markdown format."""
    # USE 4 backticks instead of 3 so backticks inside the codeblock are handled properly
    cb = f"````python\n{source}\n````"
    return cb


def set_indent(string: str, indent: int) -> str:
    """Sets the indentation of a string."""
    tab = "\t"
    return "\n".join([f"{tab * indent}{line}" for line in string.split("\n")])


def get_codegen_sdk_class_docstring(cls: PyClass, codebase: Codebase) -> str:
    """Get the documentation for a single GraphSitter class and its methods."""
    # =====[ Parent classes ]=====
    parent_classes = cls.parent_class_names
    parent_class_names = [parent.source for parent in parent_classes if parent.source not in ("Generic", "ABC", "Expression")]
    superclasses = ", ".join([name for name in parent_class_names])
    if len(superclasses) > 0:
        superclasses = f"({superclasses})"

    # =====[ Name + docstring ]=====
    source = f"class {cls.name}{superclasses}:"
    if cls.docstring is not None:
        source += set_indent(string=f'\n"""{cls.docstring.text}"""', indent=1)
    source += "\n"

    # =====[ Attributes ]=====
    if cls.is_subclass_of("Enum"):
        for attribute in cls.attributes:
            source += set_indent(f"\n{attribute.source}", 1)
    else:
        for attribute in cls.attributes(private=False, max_depth=None):
            # Only document attributes which have docstrings
            if docstring := attribute.docstring(cls):
                source += set_indent(f"\n{attribute.attribute_docstring}", 1)
                source += set_indent(string=f'\n"""{docstring}"""', indent=2)
                source += set_indent("\n...\n", 2)

    # =====[ Get inherited method ]=====
    def get_inherited_method(superclasses, method):
        """Returns True if the method is inherited"""
        for s in superclasses:
            for m in s.methods:
                if m.name == method.name:
                    if m.docstring == method.docstring or method.docstring is None:
                        return m
        return None

    # =====[ Get superclasses ]=====
    superclasses = cls.superclasses
    superclasses = list({s.name: s for s in superclasses}.values())
    superclasses = [x for x in superclasses if x.node_type != NodeType.EXTERNAL]

    # TODO use new filter_methods_list function here
    # =====[ Get methods to be documented ]=====
    doc_methods = cls.methods
    doc_methods = [m for m in doc_methods if not m.name.startswith("_")]
    doc_methods = [m for m in doc_methods if not any("noapidoc" in d.name for d in m.decorators)]
    doc_methods = [m for m in doc_methods if get_inherited_method(superclasses, m) is None]

    # =====[ Methods ]=====
    for method in doc_methods:
        if "property" in [decorator.name for decorator in method.decorators]:
            source += set_indent(f"\n@property\n{method.function_signature}", 1)
        else:
            source += set_indent(f"\n{method.function_signature}", 1)
        if method.docstring is not None:
            source += set_indent(string=f'\n"""{method.docstring.text}"""', indent=2)
        source += set_indent("\n...\n", 2)

    # =====[ Format markdown ]=====
    return f"""### {cls.name}\n\n{format_python_codeblock(source)}"""
