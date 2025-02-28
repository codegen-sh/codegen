import re
import textwrap

from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.function import Function
from codegen.sdk.core.interfaces.callable import Callable
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.python.statements.attribute import PyAttribute
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

# These are the classes that are not language specific, but have language specific subclasses with different names
SPECIAL_BASE_CLASSES = {"SourceFile": "File"}


def sanitize_docstring_for_markdown(docstring: str | None) -> str:
    """Sanitize the docstring for MDX"""
    if docstring is None:
        return ""
    docstring_lines = docstring.splitlines()
    if len(docstring_lines) > 1:
        docstring_lines[1:] = [textwrap.dedent(line) for line in docstring_lines[1:]]
    docstring = "\n".join(docstring_lines)
    if docstring.startswith('"""'):
        docstring = docstring[3:]
    if docstring.endswith('"""'):
        docstring = docstring[:-3]
    return docstring


def sanitize_mdx_mintlify_description(content: str) -> str:
    """Mintlify description field needs to have string escaped, which content doesn't need.
    the must be parsing the description differently or something
    """
    content = sanitize_docstring_for_markdown(content)
    # make sure all `< />` components are properly escaped with a `` inline-block
    # if the string already has the single-quote then this is a no-op
    content = re.sub(r"(?<!`)(<[^>]+>)(?!`)", r"`\1`", content)

    # escape double quote characters
    if re.search(r'\\"', content):
        return content  # No-op if already escaped
    return re.sub(r'(")', r"\\\1", content)


def sanitize_html_for_mdx(html_string: str) -> str:
    """Sanitize HTML string for MDX by escaping double quotes in attribute values.

    Args:
        html_string (str): The input HTML string to sanitize

    Returns:
        str: The sanitized HTML string with escaped quotes
    """
    # Replace double quotes with &quot; but only in HTML attributes
    return re.sub(r'"', "&quot;", html_string)


def get_type_str(parent, curr_depth=0, max_depth=5):
    """Returns the type node for an attribute."""
    if curr_depth >= max_depth:
        return None
    if isinstance(parent, Type):
        return parent
    for child in parent.children:
        if attr_type := get_type_str(child, curr_depth=curr_depth + 1):
            return attr_type
    return None


def is_language_base_class(cls_obj: Class):
    """Returns true if `cls_obj` is a direct parent of a language specific class.

    For example, `Symbol` which is a direct parent of `PySymbol` and `TsSymbol` is a language base class
    and `Editable` is not.

    Args:
        cls_obj (Class): the class object to check

    Returns:
        bool: if `cls_obj` is a language base class
    """
    if cls_obj.name in SPECIAL_BASE_CLASSES:
        return True

    sub_classes = cls_obj.subclasses(max_depth=1)
    base_name = cls_obj.name.lower()
    return any(sub_class.name.lower() in [f"py{base_name}", f"ts{base_name}"] for sub_class in sub_classes)


def get_section(symbol: Symbol, parent_class: Class | None = None):
    if parent_class:
        doc_section = parent_class.filepath.split("/")[1]
    else:
        doc_section = symbol.filepath.split("/")[1]
    return doc_section


def get_language(symbol: Class | Function | PyAttribute) -> str:
    """Gets the language of which the symbol is an abstract representation.

    Args:
        symbol (Class | Function | PyAttribute): the symbol to get the langauge of
    Returns:
        str: the language of the symbol
    """
    if ProgrammingLanguage.PYTHON.value.lower() in symbol.filepath:
        return ProgrammingLanguage.PYTHON.value
    elif ProgrammingLanguage.TYPESCRIPT.value.lower() in symbol.filepath:
        return ProgrammingLanguage.TYPESCRIPT.value
    elif isinstance(symbol, Class) and is_language_base_class(symbol):
        return "NONE"
    elif isinstance(symbol.parent_class, Class) and is_language_base_class(symbol.parent_class):
        return "NONE"
    else:
        return "ALL"


def get_type(method: Function):
    """Return the type of method.

    Args:
        method (Function): the method to check the type of.

    Returns:
        str: `property` if the method is a property, `method` otherwise.
    """
    if method.is_property:
        return "property"
    else:
        return "method"


def is_settter(m: Function):
    """Checks if `m` is a setter method
    Args:
        m (Function): the function (method) to check
    Returns:
        bool: `True` if `m` is a setter method, `False` otherwise
    """
    return any([dec.name == f"{m.name}.setter" for dec in m.decorators])


def create_path(symbol: Class | Function | PyAttribute, parent_class: Class | None = None) -> str:
    """Creates a route path for `symbol` that will be used in the frontend

    Args:
        symbol (Class | Function | PyAttribute): the object for which a path should be created
        parent_class (Class | None): optional parent class of the method
    Returns:
        str: route path of `symbol`
    """
    name = symbol.name
    language = get_language(symbol)

    if language == ProgrammingLanguage.PYTHON.value:
        doc_section = ProgrammingLanguage.PYTHON.value.lower()
    elif language == ProgrammingLanguage.TYPESCRIPT.value:
        doc_section = ProgrammingLanguage.TYPESCRIPT.value.lower()
    else:
        doc_section = "core"

    if isinstance(symbol, Class):
        return f"api-reference/{doc_section}/{name}"

    if parent_class:
        parent_name = parent_class.name
    else:
        parent_name = symbol.parent_class.name

    if isinstance(symbol, Function) and is_settter(symbol):
        return f"api-reference/{doc_section}/{parent_name}/set_{name}"

    return f"api-reference/{doc_section}/{parent_name}/{name}"


def has_documentation(c: Class):
    """If the class c is meant to be documented.

    Args:
        c (Class): the class to check
    Returns:
        bool: `True` if the class is meant to be documented, `False` otherwise
    """
    return any([dec.name == "ts_apidoc" or dec.name == "py_apidoc" or dec.name == "apidoc" for dec in c.decorators])


def safe_get_class(codebase: Codebase, class_name: str, language: str | None = None) -> Class | None:
    """Find the class in the codebase.

    Args:
        codebase (Codebase): the codebase to search in
        class_name (str): the name of the class to resolve
        language (str | None): the language of the class to resolve
    Returns:
        Class | None: the class if found, None otherwise
    """
    if '"' in class_name:
        class_name = class_name.strip('"')
    if "'" in class_name:
        class_name = class_name.strip("'")

    symbols = []
    try:
        class_obj = codebase.get_class(class_name, optional=True)
        if not class_obj:
            return None

    except Exception:
        symbols = codebase.get_symbols(class_name)
        possible_classes = [s for s in symbols if isinstance(s, Class) and has_documentation(s)]
        if not possible_classes:
            return None
        if len(possible_classes) > 1:
            msg = f"Found {len(possible_classes)} classes with name {class_name}"
            raise ValueError(msg)
        class_obj = possible_classes[0]

    if language and is_language_base_class(class_obj):
        sub_classes = class_obj.subclasses(max_depth=1)

        if class_name in SPECIAL_BASE_CLASSES:
            class_name = SPECIAL_BASE_CLASSES[class_name]

        if language == ProgrammingLanguage.PYTHON.value:
            sub_classes = [s for s in sub_classes if s.name == f"Py{class_name}"]
        elif language == ProgrammingLanguage.TYPESCRIPT.value:
            sub_classes = [s for s in sub_classes if s.name == f"TS{class_name}"]
        if len(sub_classes) == 1:
            class_obj = sub_classes[0]
    return class_obj


def resolve_type_symbol(codebase: Codebase, symbol_name: str, resolved_types: list[Type], parent_class: Class, parent_symbol: Symbol, types_cache: dict):
    """Find the symbol in the codebase.

    Args:
        codebase (Codebase): the codebase to search in
        symbol_name (str): the name of the symbol to resolve
        resolved_types (list[Type]): the resolved types of the symbol
        parent_class (Class): the parent class of the symbol
        types_cache (dict): the cache to store the results in
    Returns:
        str: the route path of the symbol
    """
    if symbol_name in ["list", "tuple", "int", "str", "dict", "set", "None", "bool", "optional", "Union"]:
        return symbol_name
    if symbol_name.lower() == "self":
        return f"<{create_path(parent_class)}>"

    language = get_language(parent_class)
    if (symbol_name, language) in types_cache:
        return types_cache[(symbol_name, language)]

    trgt_symbol = None
    cls_obj = safe_get_class(codebase=codebase, class_name=symbol_name, language=language)
    if cls_obj:
        trgt_symbol = cls_obj

    if not trgt_symbol:
        if symbol := parent_symbol.file.get_symbol(symbol_name):
            for resolved_type in symbol.resolved_types:
                if isinstance(resolved_type, FunctionCall) and len(resolved_type.args) >= 2:
                    bound_arg = resolved_type.args[1]
                    bound_name = bound_arg.value.source
                    if cls_obj := safe_get_class(codebase, bound_name, language=get_language(parent_class)):
                        trgt_symbol = cls_obj
                        break

        elif symbol := codebase.get_symbol(symbol_name, optional=True):
            if len(symbol.resolved_types) == 1:
                trgt_symbol = symbol.resolved_types[0]

    if trgt_symbol and isinstance(trgt_symbol, Callable) and has_documentation(trgt_symbol):
        trgt_path = f"<{create_path(trgt_symbol)}>"
        types_cache[(symbol_name, language)] = trgt_path
        return trgt_path

    return symbol_name


def replace_multiple_types(codebase: Codebase, input_str: str, resolved_types: list[Type], parent_class: Class, parent_symbol: Symbol, types_cache: dict) -> str:
    """Replace multiple types in a string.

    Args:
        codebase (Codebase): the codebase to search in
        input_str (str): the string to replace the types in
        parent_class (Class): the parent class of the symbol
        types_cache (dict): the cache to store the results in
    Returns:
        str: the string with the types replaced
    """
    # Remove outer quotes if present
    input_str = input_str.replace('"', "")

    def process_parts(content):
        # Handle nested brackets recursively
        stack = []
        current = ""
        parts = []
        separators = []
        in_quotes = False
        quote_char = None

        i = 0
        while i < len(content):
            char = content[i]

            # Handle quotes
            if char in "\"'":
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                current += char
            # Only process special characters if we're not in quotes
            elif not in_quotes:
                if char == "[":
                    stack.append("[")
                    current += char
                elif char == "]":
                    if stack:
                        stack.pop()
                    current += char
                elif (char in ",|") and not stack:  # Only split when not inside brackets
                    if current.strip():
                        parts.append(current.strip())
                        separators.append(char)
                    current = ""
                else:
                    current += char
            else:
                current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        # Process each part
        processed_parts = []
        for part in parts:
            # Check if the part is quoted
            if part.startswith('"') and part.endswith('"'):
                processed_parts.append(part)  # Keep quoted parts as-is
                continue

            # Check if the part itself contains brackets
            if "[" in part:
                base_type = part[: part.index("[")]
                bracket_content = part[part.index("[") :].strip("[]")
                processed_bracket = process_parts(bracket_content)
                replacement = resolve_type_symbol(
                    codebase=codebase, symbol_name=base_type, resolved_types=resolved_types, parent_class=parent_class, parent_symbol=parent_symbol, types_cache=types_cache
                )
                processed_part = replacement + "[" + processed_bracket + "]"
            else:
                replacement = resolve_type_symbol(codebase=codebase, symbol_name=part, resolved_types=resolved_types, parent_class=parent_class, parent_symbol=parent_symbol, types_cache=types_cache)
                processed_part = replacement
            processed_parts.append(processed_part)

        # Reconstruct with original separators
        result = processed_parts[0]
        for i in range(len(separators)):
            result += f"{separators[i]} {processed_parts[i + 1]}"

        return result

    # Check if the input contains any separators
    if any(sep in input_str for sep in ",|"):
        return process_parts(input_str)
    # Handle bracketed input
    elif "[" in input_str:
        base_type = input_str[: input_str.index("[")]
        bracket_content = input_str[input_str.index("[") :].strip("[]")
        processed_content = process_parts(bracket_content)
        replacement = resolve_type_symbol(codebase=codebase, symbol_name=base_type, resolved_types=resolved_types, parent_class=parent_class, parent_symbol=parent_symbol, types_cache=types_cache)
        return replacement + "[" + processed_content + "]"
    # Handle simple input
    else:
        replacement = resolve_type_symbol(codebase=codebase, symbol_name=input_str, resolved_types=resolved_types, parent_class=parent_class, parent_symbol=parent_symbol, types_cache=types_cache)
        return replacement


def extract_class_description(docstring):
    """Extract the class description from a docstring, excluding the attributes section.

    Args:
        docstring (str): The class docstring to parse

    Returns:
        str: The class description with whitespace normalized
    """
    if not docstring:
        return ""

    # Split by "Attributes:" and take only the first part
    parts = docstring.split("Attributes:")
    description = parts[0]

    # Normalize whitespace
    lines = [line.strip() for line in description.strip().splitlines()]
    return " ".join(filter(None, lines))
